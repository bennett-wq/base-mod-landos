"""Enums for the LandOS trigger engine.

Values match LANDOS_TRIGGER_MATRIX.md exactly. Do not add values
without updating the architecture doc first.
"""

from enum import Enum


class WakeType(str, Enum):
    """What kind of work the woken agent should perform."""

    RESCORE = "rescore"
    RESCAN = "rescan"
    CREATE = "create"
    LINK = "link"
    CLASSIFY = "classify"
    FIT = "fit"
    NOTIFY = "notify"
    SUPPRESS = "suppress"
    ESCALATE = "escalate"


class PhaseGate(str, Enum):
    """Minimum system phase required for a trigger rule to fire.

    Use phase_allows(rule_phase, active_phase) for comparisons — never
    compare PhaseGate values directly in the engine or rules.
    """

    PHASE_1 = "phase_1"
    PHASE_2 = "phase_2"
    PHASE_3_PLUS = "phase_3_plus"


# Integer ordering for phase comparison. Lower = earlier phase.
_PHASE_ORDER: dict[PhaseGate, int] = {
    PhaseGate.PHASE_1: 1,
    PhaseGate.PHASE_2: 2,
    PhaseGate.PHASE_3_PLUS: 3,
}


def phase_allows(rule_phase: PhaseGate, active_phase: PhaseGate) -> bool:
    """Return True if the active phase is at or beyond the rule's required phase."""
    return _PHASE_ORDER[active_phase] >= _PHASE_ORDER[rule_phase]


class TriggerOutcome(str, Enum):
    """Why a trigger rule was suppressed or fired."""

    FIRED = "fired"
    PHASE_GATED = "phase_gated"
    COOLDOWN_BLOCKED = "cooldown_blocked"
    MATERIALITY_NOT_MET = "materiality_not_met"
    DEPTH_CAP_REACHED = "depth_cap_reached"
    CONDITION_NOT_MET = "condition_not_met"
