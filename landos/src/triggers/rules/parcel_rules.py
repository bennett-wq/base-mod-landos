"""Phase 1 parcel-state trigger rules.

Rules:
  RF — parcel_linked_to_listing → RESCORE wake (unconditional, activated Step 5)
       Promoted from PLANNED__parcel_linked_to_listing__rescore.
  RG — parcel_owner_resolved    → RESCAN wake  (unconditional, activated Step 5)
       New in Step 5. Wakes cluster detection agent to check if owner matches
       an existing cluster or known developer entity.
  RH — parcel_score_updated     → RESCORE wake (score_delta materiality gate, activated Step 5)
       New in Step 5. Wakes supply intelligence team when a parcel's score
       changes materially (abs(score_delta) >= 0.05).
"""

from __future__ import annotations

from src.events.enums import RoutingClass
from src.triggers.enums import PhaseGate, WakeType
from src.triggers.rule import TriggerRule

RF = TriggerRule(
    rule_id="RF__parcel_linked_to_listing__rescore",
    event_type="parcel_linked_to_listing",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.RESCORE,
    phase=PhaseGate.PHASE_1,
    priority=6,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=None,
    cooldown_key_builder=None,
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "parcel_linked_to_listing → RESCORE wake to supply_intelligence_team. "
        "Unconditional. Activated from PLANNED in Step 5. "
        "Per trigger matrix: new linkage always warrants rescore with listing data."
    ),
)

RG = TriggerRule(
    rule_id="RG__parcel_owner_resolved__cluster_rescan",
    event_type="parcel_owner_resolved",
    wake_target="cluster_detection_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=6,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=None,
    cooldown_key_builder=None,
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "parcel_owner_resolved → RESCAN wake to cluster_detection_agent. "
        "Unconditional. Activated in Step 5. "
        "Per trigger matrix: check if owner matches an existing cluster or known developer."
    ),
)

RH = TriggerRule(
    rule_id="RH__parcel_score_updated__rescore_opportunity",
    event_type="parcel_score_updated",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.RESCORE,
    phase=PhaseGate.PHASE_1,
    priority=6,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: abs(float(e.payload.get("score_delta", 0) or 0)) >= 0.05,
    cooldown_seconds=None,
    cooldown_key_builder=None,
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "parcel_score_updated → RESCORE wake to supply_intelligence_team. "
        "Condition: abs(score_delta) >= 0.05 (materiality gate per trigger matrix). "
        "Activated in Step 5."
    ),
)
