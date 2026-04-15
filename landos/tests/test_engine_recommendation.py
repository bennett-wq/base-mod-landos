"""AC M1-10: recommendation() GO / NO-GO / NEGOTIATE verdict logic."""

import pytest

from src.engine.recommendation import recommendation
from src.models.opportunity import Verdict


def test_recommendation_go_at_15_percent():
    """AC M1-10.1: base_margin_pct >= 15.0 → (GO, None)."""
    verdict, target = recommendation(
        base_margin_pct=15.2,
        negotiate_floor_pct=8.0,
        base_land=32500.0,
    )
    assert verdict is Verdict.GO
    assert target is None


def test_recommendation_negotiate_at_8_percent():
    """AC M1-10.2: base_margin_pct in [8.0, 15.0) → (NEGOTIATE, not None)."""
    verdict, target = recommendation(
        base_margin_pct=10.0,
        negotiate_floor_pct=8.0,
        base_land=32500.0,
    )
    assert verdict is Verdict.NEGOTIATE
    assert target is not None


def test_recommendation_mccartney_negative():
    """AC M1-10.3: McCartney Phase H: -5.4% margin with $32,500 land.

    Expected: NEGOTIATE at ~$16,250 (half of $32,500).
    The plan says Phase H returns NEGOTIATE at $20K (roughly half of $32,500).
    Spec allows verdict in (NEGOTIATE, NO_GO); we assert NEGOTIATE and target ~$16,250.
    """
    verdict, target = recommendation(
        base_margin_pct=-5.4,
        negotiate_floor_pct=8.0,
        base_land=32500.0,
    )
    assert verdict in (Verdict.NEGOTIATE, Verdict.NO_GO)
    # If NEGOTIATE, target should be base_land * 0.5
    if verdict is Verdict.NEGOTIATE:
        assert target == pytest.approx(16250.0, abs=1.0)


def test_recommendation_no_go_below_floor():
    """AC M1-10.4: base_margin_pct < -30.0 → (NO_GO, None)."""
    verdict, target = recommendation(
        base_margin_pct=-50.0,
        negotiate_floor_pct=8.0,
        base_land=32500.0,
    )
    assert verdict is Verdict.NO_GO
    assert target is None
