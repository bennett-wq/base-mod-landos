"""Stallout detection engine — Step 8A.1.

Given a Subdivision and its associated MunicipalEvents + Parcels,
assess whether the subdivision is stalled.

Detection logic:
  - 6 weighted signals → stall_confidence (0.0–1.0)
  - is_stalled = (stall_confidence >= 0.45 AND vacancy_ratio >= 0.4)

Phase 1: rule-based only, no LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from src.models.development import Subdivision
from src.models.enums import MunicipalEventType, VacancyStatus
from src.models.municipality import MunicipalEvent
from src.models.parcel import Parcel


# ── Signal weights per spec ───────────────────────────────────────────────────

_SIGNAL_WEIGHTS: dict[str, float] = {
    "plat_age": 0.20,
    "high_vacancy": 0.25,
    "roads_installed": 0.20,
    "bonds_posted": 0.10,
    "permits_with_vacancy": 0.10,
    "no_recent_activity": 0.15,
}

# ── Thresholds ────────────────────────────────────────────────────────────────

_PLAT_AGE_THRESHOLD_YEARS = 5.0
_HIGH_VACANCY_THRESHOLD = 0.4
_PERMITS_VACANCY_THRESHOLD = 0.5
_NO_ACTIVITY_YEARS = 3.0
_STALL_CONFIDENCE_THRESHOLD = 0.45
_STALL_VACANCY_THRESHOLD = 0.4


@dataclass
class StallAssessment:
    """Result of stallout detection for a single subdivision."""

    is_stalled: bool
    stall_signals: list[str] = field(default_factory=list)
    stall_confidence: float = 0.0
    vacancy_ratio: float = 0.0
    years_since_plat: Optional[float] = None
    years_since_last_activity: float = 0.0
    infrastructure_invested: bool = False


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _years_between(target_date: date, now: datetime) -> float:
    """Calculate years between a date and a datetime."""
    return (now.date() - target_date).days / 365.25


def _event_date(me: MunicipalEvent) -> date:
    """Extract date from MunicipalEvent.occurred_at, normalizing datetime → date."""
    if isinstance(me.occurred_at, datetime):
        return me.occurred_at.date()
    return me.occurred_at


def _compute_vacancy_ratio(
    subdivision: Subdivision,
    parcels: list[Parcel],
) -> float:
    """Compute vacancy ratio from subdivision fields or parcel list."""
    # Prefer subdivision-level fields if set
    if (
        subdivision.total_lots is not None
        and subdivision.vacant_lots is not None
        and subdivision.total_lots > 0
    ):
        return subdivision.vacant_lots / subdivision.total_lots

    # Fall back to parcel list
    if not parcels:
        return 0.0

    total = len(parcels)
    vacant = sum(
        1 for p in parcels
        if p.vacancy_status == VacancyStatus.VACANT
    )
    return vacant / total if total > 0 else 0.0


def _has_event_type(
    events: list[MunicipalEvent],
    *event_types: MunicipalEventType,
) -> bool:
    """Check if any event matches one of the given types."""
    type_set = set(event_types)
    return any(me.event_type in type_set for me in events)


def _most_recent_event_date(events: list[MunicipalEvent]) -> Optional[date]:
    """Return the most recent occurred_at date from events."""
    if not events:
        return None
    latest = max(events, key=lambda me: _event_date(me))
    return _event_date(latest)


def detect_stall(
    subdivision: Subdivision,
    municipal_events: list[MunicipalEvent],
    parcels: list[Parcel],
    now: datetime | None = None,
) -> StallAssessment:
    """Assess whether a subdivision is stalled.

    Args:
        subdivision: The Subdivision object to assess.
        municipal_events: MunicipalEvents associated with this subdivision.
        parcels: Parcels within this subdivision.
        now: Current timestamp (for testability). Defaults to UTC now.

    Returns:
        StallAssessment with stall determination, signals, and confidence.
    """
    if now is None:
        now = _now_utc()

    signals: list[str] = []

    # ── Compute base metrics ──────────────────────────────────────────────

    vacancy_ratio = _compute_vacancy_ratio(subdivision, parcels)

    years_since_plat: Optional[float] = None
    if subdivision.plat_date is not None:
        years_since_plat = _years_between(subdivision.plat_date, now)

    last_event_date = _most_recent_event_date(municipal_events)
    if last_event_date is not None:
        years_since_last_activity = _years_between(last_event_date, now)
    else:
        # No events at all — treat as very inactive
        years_since_last_activity = 999.0

    infrastructure_invested = _has_event_type(
        municipal_events,
        MunicipalEventType.ROADS_INSTALLED,
        MunicipalEventType.ROADS_ACCEPTED,
    )

    # ── Evaluate 6 signal rules ───────────────────────────────────────────

    # Signal 1: plat_age
    if years_since_plat is not None and years_since_plat >= _PLAT_AGE_THRESHOLD_YEARS:
        signals.append("plat_age")

    # Signal 2: high_vacancy
    if vacancy_ratio >= _HIGH_VACANCY_THRESHOLD:
        signals.append("high_vacancy")

    # Signal 3: roads_installed
    if infrastructure_invested:
        signals.append("roads_installed")

    # Signal 4: bonds_posted
    if _has_event_type(municipal_events, MunicipalEventType.BOND_POSTED):
        signals.append("bonds_posted")

    # Signal 5: permits_with_vacancy
    if (
        _has_event_type(municipal_events, MunicipalEventType.PERMIT_PULLED)
        and vacancy_ratio >= _PERMITS_VACANCY_THRESHOLD
    ):
        signals.append("permits_with_vacancy")

    # Signal 6: no_recent_activity
    if years_since_last_activity >= _NO_ACTIVITY_YEARS:
        signals.append("no_recent_activity")

    # ── Compute confidence and stall determination ────────────────────────

    stall_confidence = sum(_SIGNAL_WEIGHTS[s] for s in signals)
    is_stalled = (
        stall_confidence >= _STALL_CONFIDENCE_THRESHOLD
        and vacancy_ratio >= _STALL_VACANCY_THRESHOLD
    )

    return StallAssessment(
        is_stalled=is_stalled,
        stall_signals=signals,
        stall_confidence=stall_confidence,
        vacancy_ratio=vacancy_ratio,
        years_since_plat=years_since_plat,
        years_since_last_activity=years_since_last_activity,
        infrastructure_invested=infrastructure_invested,
    )
