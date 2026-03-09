"""CooldownTracker — interface and in-memory implementation.

The tracker stores (cooldown_key, rule_id) -> last_wake_timestamp pairs.
cooldown_key is produced by each TriggerRule's cooldown_key_builder.

All time-sensitive operations accept an explicit `now: datetime` parameter.
The engine always passes `context.current_timestamp` as `now`, making
cooldown behavior fully deterministic and testable without wall-clock calls.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Protocol

logger = logging.getLogger(__name__)


class CooldownTracker(Protocol):
    """Interface for cooldown state storage.

    Both methods accept `now` explicitly — callers must provide the evaluation
    timestamp rather than relying on internal wall-clock calls.

    The in-memory implementation is sufficient for Step 3.
    Replace with a Redis- or PostgreSQL-backed implementation in Step 4+.
    """

    def is_cooling_down(
        self,
        cooldown_key: str,
        rule_id: str,
        cooldown_seconds: int,
        now: datetime,
    ) -> bool:
        """Return True if a wake for (cooldown_key, rule_id) is still within its cooldown window."""
        ...

    def record_wake(
        self,
        cooldown_key: str,
        rule_id: str,
        now: datetime,
    ) -> None:
        """Record that a wake fired for (cooldown_key, rule_id) at the given time."""
        ...


class InMemoryCooldownTracker:
    """Dict-based in-memory cooldown tracker.

    Uses the caller-provided `now` for all time comparisons and writes.
    No internal wall-clock calls. No database dependency.
    Suitable for the Step 3 scaffold and all unit tests.
    """

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], datetime] = {}

    def is_cooling_down(
        self,
        cooldown_key: str,
        rule_id: str,
        cooldown_seconds: int,
        now: datetime,
    ) -> bool:
        key = (cooldown_key, rule_id)
        last_wake = self._store.get(key)
        if last_wake is None:
            return False
        elapsed = now - last_wake
        return elapsed < timedelta(seconds=cooldown_seconds)

    def record_wake(
        self,
        cooldown_key: str,
        rule_id: str,
        now: datetime,
    ) -> None:
        self._store[(cooldown_key, rule_id)] = now
