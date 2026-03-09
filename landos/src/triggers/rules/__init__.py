"""Trigger rule registry for the LandOS event mesh.

ALL_RULES: executable registry — loaded into TriggerEngine. Every rule
    here is fully wired and will be evaluated against incoming events.

PLANNED_RULES: non-active catalog — documented but NOT loaded into any
    TriggerEngine instance. Each entry has condition=lambda e, ctx: False
    so it cannot produce a wake accidentally. These exist as pre-scaffolding
    for Steps 5–8.
"""

from __future__ import annotations

from src.events.enums import RoutingClass
from src.triggers.enums import PhaseGate, WakeType
from src.triggers.rule import TriggerRule
from src.triggers.rules.cluster_rules import RC
from src.triggers.rules.listing_rules import RA, RB, RE
from src.triggers.rules.phase2_placeholders import RD

# ── Executable registry ───────────────────────────────────────────────
# Only fully wired, tested rules belong here. The engine is constructed
# with ALL_RULES and will evaluate every entry against every event.

ALL_RULES: list[TriggerRule] = [RA, RB, RC, RD, RE]

# ── Planning catalog (not active) ─────────────────────────────────────
# condition=lambda e, ctx: False ensures these never produce a wake
# accidentally if referenced. Activate by moving to ALL_RULES in the
# relevant step (5–8) once the condition is properly wired.
# Note: PLANNED__listing_expired__cluster_reassessment was activated as RE in Step 4.

PLANNED_RULES: list[TriggerRule] = [
    TriggerRule(
        rule_id="PLANNED__listing_added__owner_linkage",
        event_type="listing_added",
        wake_target="supply_intelligence_team",
        wake_type=WakeType.LINK,
        phase=PhaseGate.PHASE_1,
        priority=5,
        routing_class=RoutingClass.STANDARD,
        condition=lambda e, ctx: False,
        cooldown_seconds=None,
        cooldown_key_builder=None,
        description="PLANNED — wire owner linkage wake in Step 5 (parcel linkage).",
    ),
    TriggerRule(
        rule_id="PLANNED__listing_added__cluster_scan_required",
        event_type="listing_added",
        wake_target="supply_intelligence_team",
        wake_type=WakeType.RESCAN,
        phase=PhaseGate.PHASE_1,
        priority=5,
        routing_class=RoutingClass.STANDARD,
        condition=lambda e, ctx: False,
        cooldown_seconds=None,
        cooldown_key_builder=None,
        description="PLANNED — wire cluster scan required wake in Step 6 (cluster detection).",
    ),
    TriggerRule(
        rule_id="PLANNED__parcel_linked_to_listing__rescore",
        event_type="parcel_linked_to_listing",
        wake_target="supply_intelligence_team",
        wake_type=WakeType.RESCORE,
        phase=PhaseGate.PHASE_1,
        priority=5,
        routing_class=RoutingClass.BATCH,
        condition=lambda e, ctx: False,
        cooldown_seconds=None,
        cooldown_key_builder=None,
        description="PLANNED — wire parcel rescore on linkage in Step 5.",
    ),
    TriggerRule(
        rule_id="PLANNED__municipality_rule_now_supports_split__rescore_parcels",
        event_type="municipality_rule_now_supports_split",
        wake_target="supply_intelligence_team",
        wake_type=WakeType.RESCORE,
        phase=PhaseGate.PHASE_1,
        priority=4,
        routing_class=RoutingClass.IMMEDIATE,
        condition=lambda e, ctx: False,
        cooldown_seconds=None,
        cooldown_key_builder=None,
        max_fan_out=500,
        description=(
            "PLANNED — wire municipality rule-change → jurisdiction-wide parcel rescore in Step 7. "
            "Max fan-out: 500 parcels/batch per trigger matrix."
        ),
    ),
]

__all__ = ["ALL_RULES", "PLANNED_RULES", "RA", "RB", "RC", "RD", "RE"]
