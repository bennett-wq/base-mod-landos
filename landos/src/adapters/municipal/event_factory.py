"""Event factory for municipal process detection events.

Maps each MunicipalEvent object to its corresponding detection event(s)
in the event mesh per the Event Library spec.

Detection events (7A.2):
  - All use event_class=RAW, event_family=MUNICIPAL_PROCESS
  - source_system from MunicipalEvent.source_system
  - entity_refs includes municipality_id
  - payload includes municipal_event_id

Derived event (7B):
  - evaluate_split_impact() produces municipality_rule_now_supports_split
  - event_class=DERIVED, generation_depth=1
  - Pattern matching only (Phase 1, no LLM)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily
from src.models.enums import MunicipalEventType
from src.models.municipality import MunicipalEvent


# ── MunicipalEvent.event_type → emitted event_type mapping ─────────────────

_EVENT_TYPE_MAP: dict[MunicipalEventType, str] = {
    MunicipalEventType.SITE_PLAN_APPROVED: "site_plan_approved_detected",
    MunicipalEventType.PLAT_RECORDED: "plat_recorded_detected",
    MunicipalEventType.ENGINEERING_APPROVED: "engineering_approved_detected",
    MunicipalEventType.PERMIT_PULLED: "permit_pulled_detected",
    MunicipalEventType.ROADS_INSTALLED: "roads_installed_detected",
    MunicipalEventType.ROADS_ACCEPTED: "roads_accepted_detected",
    MunicipalEventType.SEWER_EXTENDED: "public_sewer_extension_detected",
    MunicipalEventType.WATER_EXTENDED: "water_extension_detected",
    MunicipalEventType.BOND_POSTED: "bond_posted_detected",
    MunicipalEventType.BOND_EXTENDED: "bond_extension_detected",
    MunicipalEventType.BOND_RELEASED: "bond_released_detected",
    MunicipalEventType.HOA_CREATED: "hoa_created_detected",
    MunicipalEventType.MASTER_DEED_RECORDED: "master_deed_recorded_detected",
    MunicipalEventType.RULE_CHANGE: "municipality_rule_change_detected",
    MunicipalEventType.INCENTIVE_CREATED: "incentive_detected",
}

# ── Payload builders per event type ─────────────────────────────────────────

def _base_payload(me: MunicipalEvent) -> dict:
    """Common payload fields: municipal_event_id is always present."""
    return {"municipal_event_id": str(me.municipal_event_id)}


def _payload_site_plan_approved(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "project_name": d.get("project_name"),
        "approval_body": d.get("approval_body"),
        "lot_count": d.get("lot_count"),
    }


def _payload_plat_recorded(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "plat_name": d.get("plat_name"),
        "total_lots": d.get("total_lots"),
        "recording_date": d.get("recording_date"),
    }


def _payload_engineering_approved(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "project_name": d.get("project_name"),
    }


def _payload_permit_pulled(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "permit_number": d.get("permit_number"),
        "permit_type": d.get("permit_type"),
        "valuation": d.get("valuation"),
    }


def _payload_roads_installed(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "road_names": d.get("road_names"),
        "linear_feet": d.get("linear_feet"),
    }


def _payload_roads_accepted(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "acceptance_date": d.get("acceptance_date"),
    }


def _payload_sewer_extended(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "extension_area": d.get("extension_area"),
    }


def _payload_water_extended(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "extension_area": d.get("extension_area"),
    }


def _payload_bond_posted(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "bond_amount": d.get("bond_amount"),
        "bond_type": d.get("bond_type"),
        "expiration_date": d.get("expiration_date"),
    }


def _payload_bond_extended(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "original_expiration": d.get("original_expiration"),
        "new_expiration": d.get("new_expiration"),
        "extension_count": d.get("extension_count"),
    }


def _payload_bond_released(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "release_date": d.get("release_date"),
        "conditions_met": d.get("conditions_met"),
    }


def _payload_hoa_created(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "hoa_name": d.get("hoa_name"),
        "developer_control_flag": d.get("developer_control_flag"),
    }


def _payload_master_deed_recorded(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "project_name": d.get("project_name"),
        "total_units": d.get("total_units"),
        "recording_date": d.get("recording_date"),
    }


def _payload_rule_change(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "rule_type": d.get("rule_type"),
        "old_value": d.get("old_value"),
        "new_value": d.get("new_value"),
        "effective_date": d.get("effective_date"),
    }


def _payload_incentive_created(me: MunicipalEvent) -> dict:
    d = me.details or {}
    return {
        **_base_payload(me),
        "program_name": d.get("program_name"),
        "program_type": d.get("program_type"),
        "eligibility_summary": d.get("eligibility_summary"),
    }


_PAYLOAD_BUILDERS: dict[MunicipalEventType, callable] = {
    MunicipalEventType.SITE_PLAN_APPROVED: _payload_site_plan_approved,
    MunicipalEventType.PLAT_RECORDED: _payload_plat_recorded,
    MunicipalEventType.ENGINEERING_APPROVED: _payload_engineering_approved,
    MunicipalEventType.PERMIT_PULLED: _payload_permit_pulled,
    MunicipalEventType.ROADS_INSTALLED: _payload_roads_installed,
    MunicipalEventType.ROADS_ACCEPTED: _payload_roads_accepted,
    MunicipalEventType.SEWER_EXTENDED: _payload_sewer_extended,
    MunicipalEventType.WATER_EXTENDED: _payload_water_extended,
    MunicipalEventType.BOND_POSTED: _payload_bond_posted,
    MunicipalEventType.BOND_EXTENDED: _payload_bond_extended,
    MunicipalEventType.BOND_RELEASED: _payload_bond_released,
    MunicipalEventType.HOA_CREATED: _payload_hoa_created,
    MunicipalEventType.MASTER_DEED_RECORDED: _payload_master_deed_recorded,
    MunicipalEventType.RULE_CHANGE: _payload_rule_change,
    MunicipalEventType.INCENTIVE_CREATED: _payload_incentive_created,
}


# ── Public API ──────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def build_detection_event(
    me: MunicipalEvent,
    now: datetime | None = None,
) -> EventEnvelope:
    """Build a raw detection event for a MunicipalEvent.

    Maps MunicipalEvent.event_type to the corresponding detection event
    per the Event Library spec (e.g., plat_recorded → plat_recorded_detected).

    Every emitted event:
      - event_class: RAW
      - event_family: MUNICIPAL_PROCESS
      - source_system: from MunicipalEvent.source_system
      - entity_refs includes municipality_id
      - payload includes municipal_event_id
    """
    if now is None:
        now = _now_utc()

    event_type = _EVENT_TYPE_MAP.get(me.event_type)
    if event_type is None:
        raise ValueError(f"No detection event mapping for event_type: {me.event_type}")

    payload_builder = _PAYLOAD_BUILDERS.get(me.event_type, _base_payload)
    payload = payload_builder(me)

    return EventEnvelope(
        event_type=event_type,
        event_family=EventFamily.MUNICIPAL_PROCESS,
        event_class=EventClass.RAW,
        occurred_at=me.occurred_at,
        observed_at=now,
        source_system=me.source_system,
        entity_refs=EntityRefs(municipality_id=me.municipality_id),
        payload=payload,
    )


# ── 7B: Derived event — municipality_rule_now_supports_split ────────────────

# Rule types that can indicate increased split permissiveness
_SPLIT_RELEVANT_RULE_TYPES = frozenset({
    "zoning_amendment",
    "ordinance_change",
    "section_108_6_authorization",
})

# Keywords in new_value that suggest increased permissiveness
_SPLIT_POSITIVE_PATTERN = re.compile(
    r"(?:reduced|decreased|removed\s+restriction|authorized|"
    r"lowered|eliminated|relaxed|expanded|increased\s+density|"
    r"permitted|allowed|enabled)",
    re.IGNORECASE,
)


def evaluate_split_impact(
    rule_change_event: EventEnvelope,
    now: datetime | None = None,
) -> Optional[EventEnvelope]:
    """Evaluate whether a municipality_rule_change_detected event indicates
    increased split permissiveness.

    Phase 1 logic: simple pattern matching (not LLM).
      - rule_type must be in SPLIT_RELEVANT_RULE_TYPES
      - new_value must contain permissiveness keywords

    Returns:
      - EventEnvelope for municipality_rule_now_supports_split if positive
      - None if the rule change does not indicate split support (AC-4)
    """
    if now is None:
        now = _now_utc()

    payload = rule_change_event.payload or {}
    rule_type = payload.get("rule_type", "")
    new_value = payload.get("new_value", "")

    # Check rule_type relevance
    if rule_type not in _SPLIT_RELEVANT_RULE_TYPES:
        return None

    # Check new_value for permissiveness keywords
    if not new_value or not _SPLIT_POSITIVE_PATTERN.search(str(new_value)):
        return None

    # Positive: emit derived event
    return EventEnvelope(
        event_type="municipality_rule_now_supports_split",
        event_family=EventFamily.MUNICIPAL_PROCESS,
        event_class=EventClass.DERIVED,
        occurred_at=rule_change_event.occurred_at,
        observed_at=now,
        source_system="municipal_intelligence_agent",
        source_confidence=0.7,
        entity_refs=EntityRefs(
            municipality_id=rule_change_event.entity_refs.municipality_id,
        ),
        derived_from_event_ids=[rule_change_event.event_id],
        emitted_by_agent_run_id=uuid4(),
        generation_depth=1,
        payload={
            "rule_type": rule_type,
            "old_posture": payload.get("old_value"),
            "new_posture": new_value,
            "effective_date": payload.get("effective_date"),
            "affected_parcel_estimate": None,
        },
    )
