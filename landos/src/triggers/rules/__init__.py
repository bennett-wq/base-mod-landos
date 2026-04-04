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
from src.triggers.rules.bbo_rules import (
    RI, RJ, RK, RL, RM, RN1, RN2, RO, RP, RQ, RR, RS, RT, RU1, RU2,
    RY, RZ1, RZ2, RZ3,
)
from src.triggers.rules.cluster_rules import RC
from src.triggers.rules.listing_rules import RA, RB, RE
from src.triggers.rules.municipal_rules import RV, RW, RX
from src.triggers.rules.parcel_rules import RF, RG, RH
from src.triggers.rules.phase2_placeholders import RD
from src.triggers.rules.stallout_rules import STA, STB, STC, STD, STE, STF, STG

# ── Executable registry ───────────────────────────────────────────────
# Only fully wired, tested rules belong here. The engine is constructed
# with ALL_RULES and will evaluate every entry against every event.
# RF, RG, RH activated from PLANNED in Step 5.
# RI-RU activated in Step 4.5 (BBO signal intelligence).

ALL_RULES: list[TriggerRule] = [
    RA, RB, RC, RD, RE, RF, RG, RH,
    # Step 4.5 — BBO forward rules
    RI, RJ, RK, RL, RM, RN1, RN2,
    # Step 4.5 — reverse rules
    RO, RP, RQ, RR,
    # Step 4.5 — opportunity routing
    RS, RT, RU1, RU2,
    # Seller-intent + expansion rules
    RY, RZ1, RZ2, RZ3,
    # Step 7 — municipal scan rules
    RV, RW, RX,
    # Step 8 — stallout detection rules
    STA, STB, STC, STD, STE, STF, STG,
]

# ── Planning catalog (not active) ─────────────────────────────────────
# condition=lambda e, ctx: False ensures these never produce a wake
# accidentally if referenced. Activate by moving to ALL_RULES in the
# relevant step (6–8) once the condition is properly wired.
# Note: PLANNED__listing_expired__cluster_reassessment was activated as RE in Step 4.
# Note: PLANNED__parcel_linked_to_listing__rescore was activated as RF in Step 5.
# Note: PLANNED__municipality_rule_now_supports_split__rescore_parcels activated as RX in Step 7.

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
        description="PLANNED — wire owner linkage wake in Step 6 (cluster detection).",
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
]

# ── Startup safety: reject duplicate rule_ids ─────────────────────────
_all_ids = [r.rule_id for r in ALL_RULES]
_dupes = [rid for rid in _all_ids if _all_ids.count(rid) > 1]
if _dupes:
    raise RuntimeError(f"Duplicate rule_id(s) in ALL_RULES: {sorted(set(_dupes))}")
del _all_ids, _dupes

__all__ = [
    "ALL_RULES", "PLANNED_RULES",
    "RA", "RB", "RC", "RD", "RE", "RF", "RG", "RH",
    "RI", "RJ", "RK", "RL", "RM", "RN1", "RN2",
    "RO", "RP", "RQ", "RR",
    "RS", "RT", "RU1", "RU2",
    "RY", "RZ1", "RZ2", "RZ3",
    "RV", "RW", "RX",
    "STA", "STB", "STC", "STD", "STE", "STF", "STG",
]
