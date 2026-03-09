"""TriggerContext — immutable per-evaluation state for the trigger engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.triggers.enums import PhaseGate


@dataclass(frozen=True)
class TriggerContext:
    """Read-only state passed to every rule evaluation.

    Callers construct this before calling TriggerEngine.evaluate().
    score_delta is populated by the scoring engine (Step 4+); if None,
    materiality gates pass by default.
    """

    active_phase: PhaseGate = PhaseGate.PHASE_1
    generation_depth_cap: int = 5
    current_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    score_delta: float | None = None
