"""Event factory for stallout detection events — Step 8A.2.

Builds DERIVED events from stallout detection conclusions.
Events span two families:
  - historical_stall: historical_plat_stall_detected,
      historical_subdivision_stall_detected,
      partial_buildout_stagnation_detected
  - municipal_process: roads_installed_majority_vacant_detected,
      permits_pulled_majority_vacant_detected,
      approved_no_vertical_progress_detected,
      bond_posted_no_progress_detected

Every emitted event:
  - event_class: DERIVED
  - generation_depth: 1
  - emitted_by_agent_run_id: sentinel UUID
  - derived_from_event_ids: relevant MunicipalEvent IDs
  - source_confidence: from StallAssessment.stall_confidence
  - entity_refs: subdivision_id + municipality_id
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from src.adapters.stallout.detector import StallAssessment
from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily
from src.models.development import Subdivision
from src.models.enums import MunicipalEventType
from src.models.municipality import MunicipalEvent


# ── Approval event types (used for "approved no vertical progress") ───────────

_APPROVAL_EVENT_TYPES = frozenset({
    MunicipalEventType.SITE_PLAN_APPROVED,
    MunicipalEventType.ENGINEERING_APPROVED,
    MunicipalEventType.PLAT_RECORDED,
})


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _years_between(target_date: date, now: datetime) -> float:
    return (now.date() - target_date).days / 365.25


def _event_date(me: MunicipalEvent) -> date:
    """Extract date from MunicipalEvent.occurred_at."""
    if isinstance(me.occurred_at, datetime):
        return me.occurred_at.date()
    return me.occurred_at


def _make_entity_refs(subdivision: Subdivision) -> EntityRefs:
    """Build entity_refs with subdivision_id and municipality_id."""
    return EntityRefs(
        subdivision_id=subdivision.subdivision_id,
        municipality_id=subdivision.municipality_id,
    )


def _base_envelope(
    event_type: str,
    event_family: EventFamily,
    subdivision: Subdivision,
    derived_from_event_ids: list,
    source_confidence: float,
    payload: dict,
    now: datetime,
    agent_run_id: UUID,
) -> EventEnvelope:
    """Build a DERIVED event envelope with stallout common fields."""
    return EventEnvelope(
        event_type=event_type,
        event_family=event_family,
        event_class=EventClass.DERIVED,
        occurred_at=now,
        observed_at=now,
        source_system="stallout_detection_agent",
        source_confidence=source_confidence,
        entity_refs=_make_entity_refs(subdivision),
        derived_from_event_ids=derived_from_event_ids,
        emitted_by_agent_run_id=agent_run_id,
        generation_depth=1,
        payload=payload,
    )


def build_stallout_events(
    assessment: StallAssessment,
    subdivision: Subdivision,
    municipal_events: list[MunicipalEvent],
    now: datetime | None = None,
) -> list[EventEnvelope]:
    """Build stallout-related events from a StallAssessment.

    Returns a list of EventEnvelopes for each condition that is met.
    Multiple events can be emitted for the same subdivision.

    Args:
        assessment: The StallAssessment from detect_stall().
        subdivision: The Subdivision being assessed.
        municipal_events: MunicipalEvents associated with this subdivision.
        now: Current timestamp (for testability).

    Returns:
        List of DERIVED EventEnvelopes to route through the trigger engine.
    """
    if now is None:
        now = _now_utc()

    events: list[EventEnvelope] = []
    agent_run_id = uuid4()
    all_event_ids = [me.municipal_event_id for me in municipal_events]

    # ── 1. historical_subdivision_stall_detected ──────────────────────────
    # Condition: is_stalled = True
    if assessment.is_stalled:
        events.append(_base_envelope(
            event_type="historical_subdivision_stall_detected",
            event_family=EventFamily.HISTORICAL_STALL,
            subdivision=subdivision,
            derived_from_event_ids=all_event_ids,
            source_confidence=assessment.stall_confidence,
            payload={
                "subdivision_id": str(subdivision.subdivision_id),
                "stall_signals": assessment.stall_signals,
                "vacancy_ratio": assessment.vacancy_ratio,
                "years_since_activity": assessment.years_since_last_activity,
                "stall_confidence": assessment.stall_confidence,
            },
            now=now,
            agent_run_id=agent_run_id,
        ))

    # ── 2. historical_plat_stall_detected ─────────────────────────────────
    # Condition: plat_date >= 5 years AND vacancy_ratio >= 0.4
    if (
        assessment.years_since_plat is not None
        and assessment.years_since_plat >= 5.0
        and assessment.vacancy_ratio >= 0.4
    ):
        events.append(_base_envelope(
            event_type="historical_plat_stall_detected",
            event_family=EventFamily.HISTORICAL_STALL,
            subdivision=subdivision,
            derived_from_event_ids=all_event_ids,
            source_confidence=assessment.stall_confidence,
            payload={
                "subdivision_id": str(subdivision.subdivision_id),
                "plat_name": subdivision.name,
                "plat_recording_date": (
                    subdivision.plat_date.isoformat()
                    if subdivision.plat_date is not None
                    else None
                ),
                "total_lots": subdivision.total_lots,
                "vacant_lots": subdivision.vacant_lots,
                "vacancy_ratio": assessment.vacancy_ratio,
                "years_since_plat": assessment.years_since_plat,
            },
            now=now,
            agent_run_id=agent_run_id,
        ))

    # ── 3. roads_installed_majority_vacant_detected ───────────────────────
    # Condition: roads_installed event AND vacancy_ratio >= 0.5
    roads_events = [
        me for me in municipal_events
        if me.event_type in (
            MunicipalEventType.ROADS_INSTALLED,
            MunicipalEventType.ROADS_ACCEPTED,
        )
    ]
    if roads_events and assessment.vacancy_ratio >= 0.5:
        road_event_ids = [me.municipal_event_id for me in roads_events]
        # Find earliest road installation date
        road_date = min(_event_date(me) for me in roads_events)
        events.append(_base_envelope(
            event_type="roads_installed_majority_vacant_detected",
            event_family=EventFamily.MUNICIPAL_PROCESS,
            subdivision=subdivision,
            derived_from_event_ids=road_event_ids,
            source_confidence=assessment.stall_confidence,
            payload={
                "subdivision_id": str(subdivision.subdivision_id),
                "site_condo_project_id": None,
                "total_lots": subdivision.total_lots,
                "vacant_lots": subdivision.vacant_lots,
                "vacancy_ratio": assessment.vacancy_ratio,
                "road_installation_date": road_date.isoformat(),
            },
            now=now,
            agent_run_id=agent_run_id,
        ))

    # ── 4. permits_pulled_majority_vacant_detected ────────────────────────
    # Condition: permit_pulled event AND vacancy_ratio >= 0.5
    permit_events = [
        me for me in municipal_events
        if me.event_type == MunicipalEventType.PERMIT_PULLED
    ]
    if permit_events and assessment.vacancy_ratio >= 0.5:
        permit_event_ids = [me.municipal_event_id for me in permit_events]
        events.append(_base_envelope(
            event_type="permits_pulled_majority_vacant_detected",
            event_family=EventFamily.MUNICIPAL_PROCESS,
            subdivision=subdivision,
            derived_from_event_ids=permit_event_ids,
            source_confidence=assessment.stall_confidence,
            payload={
                "subdivision_id": str(subdivision.subdivision_id),
                "site_condo_project_id": None,
                "total_lots": subdivision.total_lots,
                "permitted_lots": len(permit_events),
                "vacant_lots": subdivision.vacant_lots,
                "vacancy_ratio": assessment.vacancy_ratio,
            },
            now=now,
            agent_run_id=agent_run_id,
        ))

    # ── 5. approved_no_vertical_progress_detected ─────────────────────────
    # Condition: approval event + no permit_pulled events + years >= 3.0
    approval_events = [
        me for me in municipal_events
        if me.event_type in _APPROVAL_EVENT_TYPES
    ]
    if approval_events and not permit_events:
        latest_approval = max(approval_events, key=lambda me: me.occurred_at)
        approval_date = _event_date(latest_approval)
        years_since_approval = _years_between(approval_date, now)
        if years_since_approval >= 3.0:
            approval_event_ids = [me.municipal_event_id for me in approval_events]
            events.append(_base_envelope(
                event_type="approved_no_vertical_progress_detected",
                event_family=EventFamily.MUNICIPAL_PROCESS,
                subdivision=subdivision,
                derived_from_event_ids=approval_event_ids,
                source_confidence=assessment.stall_confidence,
                payload={
                    "approval_type": latest_approval.event_type.value,
                    "approval_date": approval_date.isoformat(),
                    "years_since_approval": years_since_approval,
                    "vertical_progress_detected": False,
                },
                now=now,
                agent_run_id=agent_run_id,
            ))

    # ── 6. bond_posted_no_progress_detected ───────────────────────────────
    # Condition: bond_posted event + no progress + years >= 3.0
    bond_events = [
        me for me in municipal_events
        if me.event_type == MunicipalEventType.BOND_POSTED
    ]
    if bond_events:
        latest_bond = max(bond_events, key=lambda me: me.occurred_at)
        bond_date = _event_date(latest_bond)
        years_since_bond = _years_between(bond_date, now)
        # "No progress" = no permit_pulled events after bond posting
        permits_after_bond = [
            me for me in permit_events
            if me.occurred_at > latest_bond.occurred_at
        ]
        if years_since_bond >= 3.0 and not permits_after_bond:
            bond_event_ids = [me.municipal_event_id for me in bond_events]
            bond_details = latest_bond.details or {}
            events.append(_base_envelope(
                event_type="bond_posted_no_progress_detected",
                event_family=EventFamily.MUNICIPAL_PROCESS,
                subdivision=subdivision,
                derived_from_event_ids=bond_event_ids,
                source_confidence=assessment.stall_confidence,
                payload={
                    "bond_amount": bond_details.get("bond_amount"),
                    "bond_date": bond_date.isoformat(),
                    "years_since_bond": years_since_bond,
                    "progress_indicators": [],
                },
                now=now,
                agent_run_id=agent_run_id,
            ))

    # ── 7. partial_buildout_stagnation_detected ───────────────────────────
    # Condition: improved_lots > 0 AND vacant_lots > 0 AND years_since_last_build >= 3.0
    improved_lots = subdivision.improved_lots or 0
    vacant_lots = subdivision.vacant_lots or 0
    if improved_lots > 0 and vacant_lots > 0:
        # years_since_last_build = time since last permit_pulled
        if permit_events:
            latest_permit = max(permit_events, key=lambda me: me.occurred_at)
            last_build_date = _event_date(latest_permit)
        elif last_event_date := _most_recent_event_date(municipal_events):
            last_build_date = last_event_date
        else:
            last_build_date = None

        if last_build_date is not None:
            years_since_last_build = _years_between(last_build_date, now)
            if years_since_last_build >= 3.0:
                events.append(_base_envelope(
                    event_type="partial_buildout_stagnation_detected",
                    event_family=EventFamily.HISTORICAL_STALL,
                    subdivision=subdivision,
                    derived_from_event_ids=all_event_ids,
                    source_confidence=assessment.stall_confidence,
                    payload={
                        "subdivision_id": str(subdivision.subdivision_id),
                        "site_condo_project_id": None,
                        "total_lots": subdivision.total_lots,
                        "built_lots": improved_lots,
                        "vacant_lots": vacant_lots,
                        "years_since_last_build": years_since_last_build,
                    },
                    now=now,
                    agent_run_id=agent_run_id,
                ))

    return events


def _most_recent_event_date(events: list[MunicipalEvent]) -> Optional[date]:
    """Return the most recent occurred_at date from events."""
    if not events:
        return None
    latest = max(events, key=lambda me: me.occurred_at)
    if isinstance(latest.occurred_at, datetime):
        return latest.occurred_at.date()
    return latest.occurred_at
