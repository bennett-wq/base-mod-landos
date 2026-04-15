"""engine.recommendation — GO / NO-GO / NEGOTIATE verdict.

Spec reference: §6 recommendation.py, §13 q5.
"""

from __future__ import annotations

from src.models.opportunity import Verdict


def recommendation(
    base_margin_pct: float,
    negotiate_floor_pct: float,
    base_land: float,
    go_threshold_pct: float = 15.0,
) -> tuple[Verdict, float | None]:
    """Return (verdict, negotiate_target_land_price).

    Decision tree:
      base_margin_pct >= go_threshold_pct (15.0)      → GO, None
      base_margin_pct >= negotiate_floor_pct (8.0)    → NEGOTIATE, base_land (current)
      base_margin_pct >= -30.0 (aggressive reduction)  → NEGOTIATE, base_land * 0.5
      else                                             → NO_GO, None
    """
    if base_margin_pct >= go_threshold_pct:
        return Verdict.GO, None

    if base_margin_pct >= negotiate_floor_pct:
        return Verdict.NEGOTIATE, base_land

    if base_margin_pct >= -30.0:
        return Verdict.NEGOTIATE, round(base_land * 0.5, 2)

    return Verdict.NO_GO, None
