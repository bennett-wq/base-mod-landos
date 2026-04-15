"""Stranded-lots pipeline trigger rules — spec §7.1.

All 4 SL rules wire the stranded-lots event pipeline to the appropriate agents.

  SL1 — parcel_discovered         → RESCAN underwriter_agent          (6h / APN)
  SL2 — zoning_resolved           → RESCAN underwriter_agent          (24h / municipality+district)
  SL3 — parcel_underwritten +
         verdict in (GO, NEGOTIATE) → CREATE outreach_drafter_agent   (12h / APN)
  SL4 — area_favorable            → RESCAN opportunity_hunter_agent   (48h / scope)
"""

from __future__ import annotations

from datetime import timedelta

from src.events.enums import RoutingClass
from src.triggers.enums import PhaseGate, WakeType
from src.triggers.rule import TriggerRule

_PARCEL_DISCOVERED_COOLDOWN = int(timedelta(hours=6).total_seconds())
_ZONING_RESOLVED_COOLDOWN = int(timedelta(hours=24).total_seconds())
_PARCEL_UNDERWRITTEN_COOLDOWN = int(timedelta(hours=12).total_seconds())
_AREA_FAVORABLE_COOLDOWN = int(timedelta(hours=48).total_seconds())


# ── SL1 — parcel_discovered → RESCAN underwriter_agent ───────────────────────

SL1 = TriggerRule(
    rule_id="SL1__parcel_discovered__wake_underwriter",
    event_type="parcel_discovered",
    wake_target="underwriter_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_PARCEL_DISCOVERED_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: f"parcel_discovered:{e.payload.get('parcel_apn', '')}",
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description="parcel_discovered → RESCAN underwriter_agent. 6-hour cooldown per APN.",
)

# ── SL2 — zoning_resolved → RESCAN underwriter_agent ─────────────────────────

SL2 = TriggerRule(
    rule_id="SL2__zoning_resolved__wake_underwriter",
    event_type="zoning_resolved",
    wake_target="underwriter_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_ZONING_RESOLVED_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"zoning_resolved:{e.payload.get('municipality_id', '')}:"
        f"{e.payload.get('district_code', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description="zoning_resolved → RESCAN underwriter_agent. Cache-friendly 24h cooldown.",
)

# ── SL3 — parcel_underwritten + verdict in (GO, NEGOTIATE) → CREATE outreach_drafter_agent

SL3 = TriggerRule(
    rule_id="SL3__parcel_underwritten__wake_outreach_drafter",
    event_type="parcel_underwritten",
    wake_target="outreach_drafter_agent",
    wake_type=WakeType.CREATE,
    phase=PhaseGate.PHASE_2,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: e.payload.get("verdict") in ("GO", "NEGOTIATE"),
    cooldown_seconds=_PARCEL_UNDERWRITTEN_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: f"parcel_underwritten:{e.payload.get('parcel_apn', '')}",
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description="parcel_underwritten + verdict in (GO, NEGOTIATE) → CREATE outreach_drafter_agent.",
)

# ── SL4 — area_favorable → RESCAN opportunity_hunter_agent ───────────────────

SL4 = TriggerRule(
    rule_id="SL4__area_favorable__rescan_opportunity_hunter",
    event_type="area_favorable",
    wake_target="opportunity_hunter_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=3,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_AREA_FAVORABLE_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"area_favorable:{e.payload.get('scope_type', '')}:"
        f"{e.payload.get('scope_value', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description="area_favorable → RESCAN opportunity_hunter_agent. 48h cooldown per scope.",
)

ALL_STRANDED_LOTS_RULES: list[TriggerRule] = [SL1, SL2, SL3, SL4]
