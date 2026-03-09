"""RoutingResult — what the trigger engine returns for one event evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.triggers.enums import TriggerOutcome
from src.triggers.wake import WakeInstruction


@dataclass
class SuppressedRule:
    """Records why a trigger rule did not fire for an event."""

    rule_id: str
    outcome: TriggerOutcome
    detail: str | None = None


@dataclass
class RoutingResult:
    """Complete result of evaluating all rules against one event.

    evaluated_at is provided by TriggerEngine from context.current_timestamp —
    no wall-clock calls inside this class.
    """

    event_id: UUID
    event_type: str
    evaluated_at: datetime                        # provided by TriggerEngine from context.current_timestamp
    fired_rules: list[str] = field(default_factory=list)
    suppressed_rules: list[SuppressedRule] = field(default_factory=list)
    wake_instructions: list[WakeInstruction] = field(default_factory=list)
