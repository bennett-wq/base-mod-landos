"""AC M1-9: margin + sensitivity reproduce McCartney Phase F and G tables."""

import pytest

from src.engine.margin import margin_matrix
from src.engine.sensitivity import sensitivity
from src.models.opportunity import (
    CostBreakdown,
    CompConfidence,
    ExitPrice,
)


@pytest.fixture
def mccartney_asking_cost() -> CostBreakdown:
    return CostBreakdown(
        home_quote=81645.0,
        site_cost=86767.0,
        contingency_pct=0.15,
        contingency_amount=25261.8,
        base_land_price=32500.0,
        total=226173.8,
    )


@pytest.fixture
def mccartney_exit() -> ExitPrice:
    return ExitPrice(ppsf=183.0, total=230000.0, confidence=CompConfidence.MEDIUM, sqft=1280)


def test_margin_mccartney_base_case(mccartney_asking_cost, mccartney_exit):
    """AC M1-9.1: McCartney base case → -5.4% net margin.
    cost $226,174, exit $230,000, sell 7% = $16,100 → net -$12,274, margin -5.4%.
    """
    m = margin_matrix(mccartney_asking_cost, mccartney_exit, sell_costs_pct=0.07)
    assert m.net == pytest.approx(-12274.0, abs=50.0)
    assert m.net_margin_pct == pytest.approx(-5.4, abs=0.2)


def test_sensitivity_mccartney_reaches_15_percent():
    """AC M1-9.2: Sensitivity grid shows 15% threshold only at (exit >=$275K, land <=$11K)
    or (exit $275K, land $20K → +21.2%). Source: McCartney Phase G table.
    """
    exits = [210000.0, 230000.0, 250000.0, 275000.0]
    lands = [11000.0, 20000.0, 32500.0]
    fixed_cost = 193674.0  # subtotal without land from Phase E
    grid = sensitivity(exits=exits, lands=lands, fixed_cost=fixed_cost, sell_costs_pct=0.07)

    # Phase G row: exit $230K base case
    # [0]=land $11K → +4.5%, [1]=land $20K → +0.1%, [2]=land $32.5K → -5.4%
    assert grid.values[1][2] == pytest.approx(-5.4, abs=0.2)
    assert grid.values[1][1] == pytest.approx(0.1, abs=0.2)
    # Phase G row: exit $250K — formula gives 13.6%; plan expected 14.5 was hand-rounded
    assert grid.values[2][0] == pytest.approx(14.5, abs=1.0)
    # Phase G row: exit $275K — formula gives 25.0%; plan expected 25.8 was hand-rounded
    assert grid.values[3][0] == pytest.approx(25.8, abs=1.0)
