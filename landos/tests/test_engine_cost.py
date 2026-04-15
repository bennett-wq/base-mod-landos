"""AC M1-7: cost_stack reproduces McCartney Phase E for the Jaxon model."""

import pytest

from src.engine.cost import cost_stack, incentive_adjust
from src.models.opportunity import CostBreakdown, Program


def test_cost_stack_mccartney_jaxon_asking():
    """AC M1-7.1: Jaxon ($81,645) + $86,767 site + 15% contingency + $32,500 land
    = $226,174 total. Source: McCartney Phase E 'Asking ($130K/4)' row.
    """
    result = cost_stack(
        home_quote=81645.0,
        site_cost=86767.0,
        contingency_pct=0.15,
        land=32500.0,
    )
    assert isinstance(result, CostBreakdown)
    assert result.home_quote == 81645.0
    assert result.site_cost == 86767.0
    assert result.contingency_amount == pytest.approx(25261.8, abs=0.5)
    assert result.total == pytest.approx(226173.8, abs=0.5)


def test_cost_stack_mccartney_jaxon_aggressive():
    """AC M1-7.2: Jaxon + $20K land → $213,674 total (Phase E 'Aggressive' row)."""
    result = cost_stack(
        home_quote=81645.0,
        site_cost=86767.0,
        contingency_pct=0.15,
        land=20000.0,
    )
    assert result.total == pytest.approx(213673.8, abs=0.5)


def test_incentive_adjust_noop():
    """AC M1-7.3: Empty program list returns the base cost unchanged."""
    base = CostBreakdown(
        home_quote=81645.0,
        site_cost=86767.0,
        contingency_pct=0.15,
        contingency_amount=25261.8,
        base_land_price=20000.0,
        total=213673.8,
    )
    adjusted = incentive_adjust(base, programs=[])
    assert adjusted.total == pytest.approx(base.total)


def test_incentive_adjust_applies_program_deltas():
    """AC M1-7.4: Two programs reduce total cost by sum of value_to_deal."""
    base = CostBreakdown(
        home_quote=81645.0,
        site_cost=86767.0,
        contingency_pct=0.15,
        contingency_amount=25261.8,
        base_land_price=20000.0,
        total=213673.8,
    )
    programs = [
        Program(
            name="IFT Class 7b",
            authority_type="township",
            scope="industrial-zoned",
            dates_active="active",
            stacking_notes="stacks with NEZ",
            applies_to_parcel=True,
            source_citation="Ypsi Twp resolution 2024-14",
            value_to_deal=5000.0,
        ),
        Program(
            name="MI 10K DPA",
            authority_type="state",
            scope="MSHDA",
            dates_active="active",
            stacking_notes="buyer-side",
            applies_to_parcel=True,
            source_citation="MSHDA DPA guidelines",
            value_to_deal=10000.0,
        ),
    ]
    adjusted = incentive_adjust(base, programs=programs)
    assert adjusted.total == pytest.approx(213673.8 - 15000.0, abs=0.5)
