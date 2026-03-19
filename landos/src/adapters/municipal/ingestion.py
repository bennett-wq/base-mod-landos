"""Municipal scan ingestion — Step 7.

process_municipal_records() takes a list of raw municipal record dicts,
normalizes each into a MunicipalEvent, persists to InMemory store,
emits detection events, evaluates through the trigger engine, and
returns routing results.

Municipality object update (7E):
  - Updates last_municipal_event_at on the Municipality object
  - Updates land_division_posture if a rule_change triggers split support
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from src.adapters.municipal.event_factory import (
    build_detection_event,
    evaluate_split_impact,
)
from src.adapters.municipal.normalizer import normalize_municipal_record
from src.adapters.municipal.store import InMemoryMunicipalEventStore
from src.models.enums import LandDivisionPosture, MunicipalEventType
from src.models.municipality import Municipality, MunicipalEvent
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.result import RoutingResult


def _update_municipality(
    municipality: Municipality,
    me: MunicipalEvent,
) -> None:
    """Update Municipality object after ingesting a municipal event (7E).

    - last_municipal_event_at = max(current, new event's occurred_at)
    """
    if municipality.last_municipal_event_at is None:
        municipality.last_municipal_event_at = me.occurred_at
    else:
        municipality.last_municipal_event_at = max(
            municipality.last_municipal_event_at,
            me.occurred_at,
        )
    municipality.updated_at = datetime.now(timezone.utc)


def _update_municipality_split_posture(
    municipality: Municipality,
    new_posture_str: str,
) -> None:
    """Update land_division_posture if a rule change supports splits."""
    try:
        municipality.land_division_posture = LandDivisionPosture(new_posture_str)
    except ValueError:
        # If new_posture doesn't map to an enum, set to PERMISSIVE
        # since the derived event confirmed it supports splits
        municipality.land_division_posture = LandDivisionPosture.PERMISSIVE
    municipality.updated_at = datetime.now(timezone.utc)


def process_municipal_records(
    raw_records: list[dict[str, Any]],
    engine: TriggerEngine,
    context: TriggerContext,
    store: InMemoryMunicipalEventStore,
    municipality: Optional[Municipality] = None,
    now: datetime | None = None,
) -> list[RoutingResult]:
    """Ingest a batch of raw municipal records.

    For each raw record:
      1. Normalize into a MunicipalEvent
      2. Save to InMemory store
      3. Update Municipality object (7E)
      4. Build detection event
      5. Evaluate through trigger engine
      6. If rule_change: evaluate split impact and route derived event

    Returns list of RoutingResult from all events processed.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    results: list[RoutingResult] = []

    for raw in raw_records:
        # 1. Normalize
        me = normalize_municipal_record(raw, now=now)

        # 2. Save to store
        store.save(me)

        # 3. Update Municipality object (7E)
        if municipality is not None:
            _update_municipality(municipality, me)

        # 4. Build detection event
        detection_event = build_detection_event(me, now=now)

        # 5. Evaluate through trigger engine
        result = engine.evaluate(detection_event, context)
        results.append(result)

        # 6. If rule_change: evaluate split impact
        if me.event_type == MunicipalEventType.RULE_CHANGE:
            derived = evaluate_split_impact(detection_event, now=now)
            if derived is not None:
                # Route the derived event through the engine
                derived_result = engine.evaluate(derived, context)
                results.append(derived_result)

                # Update municipality posture (7E)
                if municipality is not None:
                    new_posture = (derived.payload or {}).get("new_posture", "")
                    _update_municipality_split_posture(municipality, new_posture)

    return results
