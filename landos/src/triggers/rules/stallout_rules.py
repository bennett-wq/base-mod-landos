"""Step 8 stallout trigger rules.

STA — historical_plat_stall_detected → create Opportunity.
      Priority 4, standard, 30d cooldown per subdivision.

STB — historical_subdivision_stall_detected → create Opportunity + link DeveloperEntity.
      Priority 4, standard, 30d cooldown per subdivision.

STC — roads_installed_majority_vacant_detected → stallout flag + create Opportunity.
      Priority 2, immediate, 30d cooldown per subdivision.

STD — permits_pulled_majority_vacant_detected → create Opportunity if vacancy > 0.5.
      Priority 3, standard, 30d cooldown per subdivision.

STE — approved_no_vertical_progress_detected → rescore + create if high vacancy.
      Priority 5, standard, 30d cooldown per subdivision.

STF — bond_posted_no_progress_detected → create if warranted.
      Priority 5, standard, 30d cooldown per subdivision.

STG — partial_buildout_stagnation_detected → create Opportunity.
      Priority 5, standard, 30d cooldown per subdivision.
"""

from __future__ import annotations

from datetime import timedelta

from src.events.enums import RoutingClass
from src.triggers.enums import PhaseGate, WakeType
from src.triggers.rule import TriggerRule

_STALLOUT_COOLDOWN = int(timedelta(days=30).total_seconds())


def _stallout_cooldown_key(e, ctx) -> str:
    """Build cooldown key scoped to subdivision."""
    return f"stallout:{e.entity_refs.subdivision_id}"


# ── STA — historical_plat_stall_detected ──────────────────────────────────────

STA = TriggerRule(
    rule_id="STA__historical_plat_stall_detected__create_opportunity",
    event_type="historical_plat_stall_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.CREATE,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: (
        (e.payload or {}).get("vacancy_ratio", 0) >= 0.4
        and (e.payload or {}).get("years_since_plat", 0) >= 5.0
    ),
    cooldown_seconds=_STALLOUT_COOLDOWN,
    cooldown_key_builder=_stallout_cooldown_key,
    description=(
        "historical_plat_stall_detected → create Opportunity. "
        "Priority 4, standard, 30d cooldown per subdivision."
    ),
)


# ── STB — historical_subdivision_stall_detected ───────────────────────────────

STB = TriggerRule(
    rule_id="STB__historical_subdivision_stall_detected__create_opportunity",
    event_type="historical_subdivision_stall_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.CREATE,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: (
        (e.payload or {}).get("stall_confidence", 0) >= 0.6
    ),
    cooldown_seconds=_STALLOUT_COOLDOWN,
    cooldown_key_builder=_stallout_cooldown_key,
    description=(
        "historical_subdivision_stall_detected → create Opportunity + link DeveloperEntity. "
        "Priority 4, standard, 30d cooldown per subdivision."
    ),
)


# ── STC — roads_installed_majority_vacant_detected ────────────────────────────

STC = TriggerRule(
    rule_id="STC__roads_installed_majority_vacant_detected__create_opportunity",
    event_type="roads_installed_majority_vacant_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.CREATE,
    phase=PhaseGate.PHASE_1,
    priority=2,
    routing_class=RoutingClass.IMMEDIATE,
    condition=lambda e, ctx: True,
    cooldown_seconds=_STALLOUT_COOLDOWN,
    cooldown_key_builder=_stallout_cooldown_key,
    description=(
        "roads_installed_majority_vacant_detected → stallout flag + create Opportunity. "
        "Priority 2, immediate, 30d cooldown per subdivision."
    ),
)


# ── STD — permits_pulled_majority_vacant_detected ─────────────────────────────

STD = TriggerRule(
    rule_id="STD__permits_pulled_majority_vacant_detected__create_opportunity",
    event_type="permits_pulled_majority_vacant_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.CREATE,
    phase=PhaseGate.PHASE_1,
    priority=3,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_STALLOUT_COOLDOWN,
    cooldown_key_builder=_stallout_cooldown_key,
    description=(
        "permits_pulled_majority_vacant_detected → create Opportunity if vacancy > 0.5. "
        "Priority 3, standard, 30d cooldown per subdivision."
    ),
)


# ── STE — approved_no_vertical_progress_detected ──────────────────────────────

STE = TriggerRule(
    rule_id="STE__approved_no_vertical_progress_detected__create_opportunity",
    event_type="approved_no_vertical_progress_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.CREATE,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: (
        (e.payload or {}).get("years_since_approval", 0) >= 3.0
    ),
    cooldown_seconds=_STALLOUT_COOLDOWN,
    cooldown_key_builder=_stallout_cooldown_key,
    description=(
        "approved_no_vertical_progress_detected → rescore + create if high vacancy. "
        "Priority 5, standard, 30d cooldown per subdivision."
    ),
)


# ── STF — bond_posted_no_progress_detected ────────────────────────────────────

STF = TriggerRule(
    rule_id="STF__bond_posted_no_progress_detected__create_opportunity",
    event_type="bond_posted_no_progress_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.CREATE,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_STALLOUT_COOLDOWN,
    cooldown_key_builder=_stallout_cooldown_key,
    description=(
        "bond_posted_no_progress_detected → create if warranted. "
        "Priority 5, standard, 30d cooldown per subdivision."
    ),
)


# ── STG — partial_buildout_stagnation_detected ────────────────────────────────

STG = TriggerRule(
    rule_id="STG__partial_buildout_stagnation_detected__create_opportunity",
    event_type="partial_buildout_stagnation_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.CREATE,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: (
        (e.payload or {}).get("years_since_last_build", 0) >= 3.0
    ),
    cooldown_seconds=_STALLOUT_COOLDOWN,
    cooldown_key_builder=_stallout_cooldown_key,
    description=(
        "partial_buildout_stagnation_detected → create Opportunity. "
        "Priority 5, standard, 30d cooldown per subdivision."
    ),
)
