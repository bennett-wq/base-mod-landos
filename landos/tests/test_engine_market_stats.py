"""AC M1-11: market_stats reproduces McCartney 22-month inventory claim."""

import json
from pathlib import Path
import pytest

from src.engine.market_stats import months_of_inventory, cdom_distribution, compile_market_stats

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mccartney"


def test_months_of_inventory_48198_land():
    """AC M1-11.1: 48198 land → 22 months of inventory (deep buyer's market).
    Source: McCartney Phase H recommendation 'Why PASS' item 4.
    """
    active = json.loads((FIXTURE_DIR / "spark_48198_land_active.json").read_text())
    closed = json.loads((FIXTURE_DIR / "spark_48198_land_closed_30d.json").read_text())

    moi = months_of_inventory(active_count=len(active), closed_last_30d=len(closed))
    assert moi == pytest.approx(22.0, abs=2.0)


def test_cdom_distribution_returns_three_percentiles():
    """AC M1-11.2: CDOM distribution returns (median, p75, p90)."""
    cdoms = [30, 60, 90, 120, 180, 240, 365, 500, 700, 900]
    median, p75, p90 = cdom_distribution(cdoms)
    assert median > 0
    assert p75 >= median
    assert p90 >= p75
