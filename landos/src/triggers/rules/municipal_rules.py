"""Step 7 municipal trigger rules.

RV  — Common municipal detection routing: any municipal_process family
      raw event → update Municipality (last_municipal_event_at).
      Priority 6, batch, 24h cooldown per municipality.

RW  — municipality_rule_change_detected → evaluate split impact.
      Priority 3, immediate, no cooldown (rule changes always processed).

RX  — municipality_rule_now_supports_split → rescore qualifying parcels.
      Activated from PLANNED_RULES. Priority 4, immediate,
      24h cooldown per municipality. Max fan-out: 500.
"""

from __future__ import annotations

from datetime import timedelta

from src.events.enums import EventFamily, RoutingClass
from src.triggers.enums import PhaseGate, WakeType
from src.triggers.rule import TriggerRule

_MUNICIPAL_COOLDOWN = int(timedelta(hours=24).total_seconds())


# ── RV — Common municipal detection routing ──────────────────────────────────

RV = TriggerRule(
    rule_id="RV__municipal_process_detected__update_municipality",
    event_type="*",  # matches all event types
    wake_target="municipal_agent",
    wake_type=WakeType.RESCORE,
    phase=PhaseGate.PHASE_1,
    priority=6,
    routing_class=RoutingClass.BATCH,
    condition=lambda e, ctx: (
        e.event_family == EventFamily.MUNICIPAL_PROCESS
        and e.event_type != "municipality_rule_now_supports_split"
    ),
    cooldown_seconds=_MUNICIPAL_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"municipal_detection:{e.entity_refs.municipality_id}"
    ),
    raw_event_bypasses_cooldown=True,
    description=(
        "Common municipal detection routing — any municipal_process family "
        "raw event updates Municipality.last_municipal_event_at. "
        "24h cooldown per municipality, bypassed by raw events."
    ),
)


# ── RW — rule_change_detected → evaluate split impact ────────────────────────

RW = TriggerRule(
    rule_id="RW__municipality_rule_change_detected__evaluate_split",
    event_type="municipality_rule_change_detected",
    wake_target="municipal_intelligence_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=3,
    routing_class=RoutingClass.IMMEDIATE,
    condition=lambda e, ctx: True,
    cooldown_seconds=None,
    cooldown_key_builder=None,
    description=(
        "municipality_rule_change_detected → evaluate split impact. "
        "Priority 3, immediate, no cooldown — rule changes always processed."
    ),
)


# ── RX — municipality_rule_now_supports_split → rescore parcels ──────────────
# Activated from PLANNED__municipality_rule_now_supports_split__rescore_parcels

RX = TriggerRule(
    rule_id="RX__municipality_rule_now_supports_split__rescore_parcels",
    event_type="municipality_rule_now_supports_split",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.RESCORE,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.IMMEDIATE,
    condition=lambda e, ctx: True,
    cooldown_seconds=_MUNICIPAL_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"split_rescore:{e.entity_refs.municipality_id}"
    ),
    max_fan_out=500,
    description=(
        "municipality_rule_now_supports_split → jurisdiction-wide parcel rescore. "
        "Activated from PLANNED rule. Priority 4, immediate, "
        "24h cooldown per municipality. Max fan-out: 500 parcels/batch."
    ),
)
