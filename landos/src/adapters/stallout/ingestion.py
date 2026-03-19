"""Stallout scanning ingestion — Step 8A.5.

scan_subdivisions_for_stalls() takes a list of Subdivisions,
gathers MunicipalEvents and Parcels for each, runs stallout
detection, emits events, routes through trigger engine, creates
Opportunities, and updates Subdivision objects.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.adapters.municipal.store import InMemoryMunicipalEventStore
from src.adapters.stallout.detector import StallAssessment, detect_stall
from src.adapters.stallout.event_factory import build_stallout_events
from src.adapters.stallout.opportunity_factory import create_stall_opportunity
from src.events.envelope import EventEnvelope
from src.models.development import Subdivision
from src.models.enums import InfrastructureStatus, MunicipalEventType
from src.models.municipality import MunicipalEvent
from src.models.opportunity import Opportunity
from src.models.parcel import Parcel
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.result import RoutingResult


def _derive_infrastructure_status(
    events: list[MunicipalEvent],
) -> Optional[InfrastructureStatus]:
    """Derive infrastructure status from MunicipalEvents."""
    has_roads_accepted = any(
        me.event_type == MunicipalEventType.ROADS_ACCEPTED for me in events
    )
    has_roads_installed = any(
        me.event_type == MunicipalEventType.ROADS_INSTALLED for me in events
    )

    if has_roads_accepted:
        return InfrastructureStatus.ROADS_ACCEPTED
    elif has_roads_installed:
        return InfrastructureStatus.ROADS_INSTALLED
    return None


def _update_subdivision(
    subdivision: Subdivision,
    assessment: StallAssessment,
    events: list[MunicipalEvent],
    now: datetime,
) -> None:
    """Update Subdivision object fields after stallout detection (8D).

    Updates: stall_flag, stall_score, stall_detected_at, vacancy_ratio,
    infrastructure_status, years_since_plat, updated_at.
    """
    # Only set stall_detected_at if newly detected (was not previously stalled)
    if assessment.is_stalled and subdivision.stall_flag is not True:
        subdivision.stall_detected_at = now

    subdivision.stall_flag = assessment.is_stalled
    subdivision.stall_score = assessment.stall_confidence
    subdivision.vacancy_ratio = assessment.vacancy_ratio
    subdivision.years_since_plat = assessment.years_since_plat
    subdivision.updated_at = now

    infra = _derive_infrastructure_status(events)
    if infra is not None:
        subdivision.infrastructure_status = infra


ScanResult = tuple[StallAssessment, list[EventEnvelope], Optional[Opportunity]]


def scan_subdivisions_for_stalls(
    subdivisions: list[Subdivision],
    municipal_event_store: InMemoryMunicipalEventStore,
    parcels_by_subdivision: dict[UUID, list[Parcel]],
    engine: TriggerEngine,
    context: TriggerContext,
    now: datetime | None = None,
) -> list[ScanResult]:
    """Scan subdivisions for stall conditions.

    For each subdivision:
      1. Gather MunicipalEvents from the store
      2. Gather Parcels from the lookup dict
      3. Run detect_stall()
      4. If stalled: emit events and route through trigger engine
      5. If confidence >= 0.45: create Opportunity
      6. Update Subdivision fields (8D)

    Args:
        subdivisions: List of Subdivisions to scan.
        municipal_event_store: Store to look up MunicipalEvents.
        parcels_by_subdivision: Dict mapping subdivision_id → list of Parcels.
        engine: TriggerEngine to route events through.
        context: TriggerContext for engine evaluation.
        now: Current timestamp (for testability).

    Returns:
        List of (StallAssessment, emitted_events, Opportunity | None) tuples.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    results: list[ScanResult] = []

    for subdivision in subdivisions:
        # 1. Gather MunicipalEvents for this subdivision's municipality
        all_muni_events = municipal_event_store.get_by_municipality(
            subdivision.municipality_id
        )
        # Filter to events that reference this subdivision (or have no subdivision filter)
        subdivision_events = [
            me for me in all_muni_events
            if me.subdivision_id is None or me.subdivision_id == subdivision.subdivision_id
        ]

        # 2. Gather Parcels
        parcels = parcels_by_subdivision.get(subdivision.subdivision_id, [])

        # 3. Run detection
        assessment = detect_stall(subdivision, subdivision_events, parcels, now=now)

        # 4. Emit events if stalled
        emitted_events: list[EventEnvelope] = []
        if assessment.is_stalled or assessment.stall_confidence > 0:
            emitted_events = build_stallout_events(
                assessment, subdivision, subdivision_events, now=now
            )
            # Route each event through trigger engine
            for event in emitted_events:
                engine.evaluate(event, context)

        # 5. Create Opportunity if confidence threshold met
        event_ids = [ev.event_id for ev in emitted_events]
        opportunity = create_stall_opportunity(assessment, subdivision, event_ids)

        # 6. Update Subdivision fields (8D)
        _update_subdivision(subdivision, assessment, subdivision_events, now)

        results.append((assessment, emitted_events, opportunity))

    return results
