"""TriggerRule — the atomic unit of the LandOS trigger engine.

A TriggerRule combines an event type, a condition, a wake target, and
guardrail configuration. The same event type can have multiple rules with
different conditions and targets.

Per LANDOS_TRIGGER_MATRIX.md design principle: priority attaches to the
trigger rule, not just the event type.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from src.events.enums import RoutingClass
from src.triggers.enums import PhaseGate, WakeType

if TYPE_CHECKING:
    from src.events.envelope import EventEnvelope
    from src.triggers.context import TriggerContext


@dataclass(frozen=True)
class TriggerRule:
    """Atomic routing rule for the trigger engine.

    Invariant: cooldown_seconds and cooldown_key_builder must both be set
    or both be None. The engine validates this at startup.
    """

    rule_id: str
    """Unique human-readable slug, e.g. 'RA__listing_added__link_to_parcel'."""

    event_type: str
    """Exact event_type string to match, e.g. 'listing_added'. Use '*' for any."""

    wake_target: str
    """Agent type or team to wake, e.g. 'supply_intelligence_team'."""

    wake_type: WakeType

    phase: PhaseGate
    """Minimum system phase required. Always check via phase_allows()."""

    priority: int
    """1–10, matching LANDOS_TRIGGER_MATRIX.md. Lower = higher priority."""

    routing_class: RoutingClass
    """Processing urgency. Static — does not vary by payload in Step 3."""

    condition: Callable[[EventEnvelope, TriggerContext], bool]
    """Predicate evaluated against the event. Use lambda e, ctx: True if unconditional."""

    cooldown_seconds: int | None
    """None = no cooldown for this rule."""

    cooldown_key_builder: Callable[[EventEnvelope, TriggerContext], str | None] | None
    """Required when cooldown_seconds is set. Returns the scoping key
    (e.g. 'cluster:{uuid}') or None to skip cooldown for this invocation.
    Must be None when cooldown_seconds is None."""

    raw_event_bypasses_cooldown: bool = field(default=False)
    """Set True only for rules where LANDOS_TRIGGER_MATRIX.md explicitly documents
    raw-event cooldown override. The engine bypasses cooldown only when this is
    True AND event.event_class == RAW."""

    materiality_threshold: float | None = field(default=None)
    """Minimum score delta required to fire. None = no gate.
    Enforcement requires TriggerContext.score_delta, which is populated
    by the scoring engine (Step 4+). In Step 3, gates with no score_delta pass."""

    max_fan_out: int | None = field(default=None)
    """Blast-radius limit from the trigger matrix. Documented here for fidelity;
    enforcement belongs in the agent orchestration layer (Step 4+)."""

    description: str = field(default="")
