"""Phase 1 listing-family trigger rules.

Rules:
  RA — listing_added → LINK wake (unconditional)
  RB — listing_added → CLASSIFY wake (acreage >= 5.0)
  RE — listing_expired → RESCORE wake (unconditional, activated Step 4)
       Promoted from PLANNED__listing_expired__cluster_reassessment.
       Full cluster-reassessment condition wired in Step 6.
"""

from __future__ import annotations

from src.events.enums import RoutingClass
from src.triggers.enums import PhaseGate, WakeType
from src.triggers.rule import TriggerRule

RA = TriggerRule(
    rule_id="RA__listing_added__link_to_parcel",
    event_type="listing_added",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.LINK,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=None,
    cooldown_key_builder=None,
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "listing_added → LINK wake to supply_intelligence_team. "
        "Unconditional. No cooldown. First leg of listing → parcel linkage chain."
    ),
)

RB = TriggerRule(
    rule_id="RB__listing_added__classify_large_acreage",
    event_type="listing_added",
    wake_target="listing_analysis_agent",
    wake_type=WakeType.CLASSIFY,
    phase=PhaseGate.PHASE_1,
    priority=6,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: float(e.payload.get("acreage", 0) or 0) >= 5.0,
    cooldown_seconds=None,
    cooldown_key_builder=None,
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "listing_added with acreage >= 5.0 → CLASSIFY wake to listing_analysis_agent. "
        "Per trigger matrix: large-acreage listings require dedicated classification. "
        "No cooldown."
    ),
)

RE = TriggerRule(
    rule_id="RE__listing_expired__wake_supply_intelligence",
    event_type="listing_expired",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.RESCORE,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=None,
    cooldown_key_builder=None,
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "listing_expired → RESCORE wake to supply_intelligence_team. "
        "Unconditional. Activated from PLANNED in Step 4. "
        "Full cluster reassessment wiring deferred to Step 6."
    ),
)
