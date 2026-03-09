"""Phase 1 cluster-family trigger rules.

Rule C is the first slice of owner_cluster_detected → full downstream chain.
It models the municipal rescan leg only. The separate cluster_municipal_scan_required
rule (distinct event type, 30-day per-municipality cooldown) is a PLANNED_RULE.

Routing upgrade note (deferred):
  The trigger matrix documents that 5+ member clusters upgrade routing from
  STANDARD to IMMEDIATE. The current rule model treats routing_class as static.
  This upgrade is deferred until the rule model supports dynamic routing-class
  resolution, or until Rule C is split into separate rules (Step 6).
"""

from __future__ import annotations

from src.events.enums import RoutingClass
from src.triggers.enums import PhaseGate, WakeType
from src.triggers.rule import TriggerRule

RC = TriggerRule(
    rule_id="RC__owner_cluster_detected__rescan_municipality",
    event_type="owner_cluster_detected",
    wake_target="municipal_intelligence_team",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: int(e.payload.get("cluster_size", 0)) >= 3,
    cooldown_seconds=43200,  # 12 hours per-cluster, per trigger matrix
    cooldown_key_builder=lambda e, ctx: (
        f"cluster:{e.entity_refs.cluster_id}"
        if e.entity_refs.cluster_id is not None
        else None
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "owner_cluster_detected (cluster_size >= 3) → RESCAN wake to municipal_intelligence_team. "
        "First slice of owner_cluster_detected → full downstream chain. "
        "12-hour per-cluster cooldown per trigger matrix. "
        "Routing upgrade for 5+ members deferred to Step 6."
    ),
)
