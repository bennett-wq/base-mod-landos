"""Phase 2 trigger rules — included in executable registry to prove phase gating.

These rules exist in ALL_RULES but do not fire in a PHASE_1 context.
Their presence in the registry is intentional: it proves the engine's
phase gate blocks them correctly during Phase 1 operation.
"""

from __future__ import annotations

from src.events.enums import RoutingClass
from src.triggers.enums import PhaseGate, WakeType
from src.triggers.rule import TriggerRule

RD = TriggerRule(
    rule_id="RD__incentive_detected__wake_incentive_team",
    event_type="incentive_detected",
    wake_target="incentives_policy_team",
    wake_type=WakeType.CREATE,
    phase=PhaseGate.PHASE_2,
    priority=7,
    routing_class=RoutingClass.BATCH,
    condition=lambda e, ctx: True,
    cooldown_seconds=None,
    cooldown_key_builder=None,
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "incentive_detected → CREATE wake to incentives_policy_team. "
        "Phase 2 gate: does not fire in Phase 1 context. "
        "Proves phase gating in Step 3 tests."
    ),
)
