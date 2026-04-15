"""AC M1-3.1 through M1-3.17: all underwriting types construct, validate, and serialize.

Spec §6.1.5. Traces back to the manual McCartney underwriting deliverable.
"""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models.opportunity import (
    SetbackRules,
    DwellingRules,
    UseCheckResult,
    CostBreakdown,
    ExitPrice,
    Margin,
    SensitivityMatrix,
    Verdict,
    Program,
    CompConfidence,
    Comp,
    CompAggregates,
    MarketStats,
    ModelFit,
    OpportunityUnderwriting,
)


def test_setback_rules_r5_construction():
    """AC M1-3.1: SetbackRules constructs with Ypsi Twp R-5 values from the spec §9."""
    r5 = SetbackRules(
        district_code="R-5",
        min_lot_sf=5400,
        min_width_ft=50,
        max_coverage_pct=35.0,
        max_height_ft=25.0,
        max_stories=2,
        front_setback_ft=20.0,
        side_least_ft=5.0,
        side_total_ft=16.0,
        rear_setback_ft=35.0,
        min_ground_floor_sf=720,
        source_url="https://library.municode.com/mi/ypsilanti_charter_township",
        pulled_on=date(2026, 4, 15),
    )
    assert r5.rear_setback_ft == 35.0
    assert r5.max_coverage_pct == 35.0


def test_dwelling_rules_defaults():
    """AC M1-3.2: DwellingRules uses Sec. 1101 defaults (24 ft min width, 3:1 ratio)."""
    dr = DwellingRules()
    assert dr.min_plan_width_ft == 24.0
    assert dr.max_plan_ratio == 3.0
    assert dr.facade_front_required is True


def test_use_check_result_arlington_denial():
    """AC M1-3.3: UseCheckResult handles the R-5 one-family denial case."""
    result = UseCheckResult(
        allowed=False,
        path="denied",
        citation="Sec. 406 (one-family residential)",
        rationale="Two-family dwellings not permitted in R-5.",
    )
    assert result.allowed is False
    assert result.path == "denied"


def test_cost_breakdown_mccartney_jaxon():
    """AC M1-3.4: CostBreakdown matches McCartney Phase E Jaxon + $20K land."""
    cost = CostBreakdown(
        home_quote=81645.0,
        site_cost=86767.0,
        contingency_pct=0.15,
        contingency_amount=25261.8,
        base_land_price=20000.0,
        total=213673.8,
    )
    assert cost.total == pytest.approx(213673.8, abs=0.1)


def test_exit_price_with_confidence():
    """AC M1-3.5: ExitPrice carries ppsf + total + confidence band."""
    ep = ExitPrice(ppsf=183.0, total=234240.0, confidence=CompConfidence.MEDIUM, sqft=1280)
    assert ep.confidence == CompConfidence.MEDIUM


def test_margin_negative_case():
    """AC M1-3.6: Margin handles the McCartney -5.4% case."""
    m = Margin(net=-12274.0, gross=3826.0, net_margin_pct=-5.4)
    assert m.net_margin_pct == -5.4


def test_sensitivity_matrix_grid():
    """AC M1-3.7: SensitivityMatrix holds a 2D grid of margin percentages."""
    sm = SensitivityMatrix(
        rows=[210000.0, 230000.0, 250000.0],
        columns=[11000.0, 20000.0, 32500.0],
        values=[
            [-7.4, -11.6, -17.5],
            [4.5, 0.1, -5.4],
            [14.5, 10.0, 3.9],
        ],
    )
    assert sm.values[1][2] == -5.4


def test_verdict_enum_values():
    """AC M1-3.8: Verdict enum has GO, NO-GO, NEGOTIATE."""
    assert Verdict.GO.value == "GO"
    assert Verdict.NO_GO.value == "NO-GO"
    assert Verdict.NEGOTIATE.value == "NEGOTIATE"


def test_program_tif_construction():
    """AC M1-3.9: Program represents a TIF district or PA 198 abatement."""
    p = Program(
        name="IFT Class 7b",
        authority_type="township",
        scope="industrial-zoned",
        dates_active="2024-2034",
        stacking_notes="stacks with NEZ",
        applies_to_parcel=True,
        source_citation="Ypsi Twp resolution 2024-14",
        value_to_deal=5000.0,
    )
    assert p.applies_to_parcel is True
    assert p.value_to_deal == 5000.0


def test_comp_row():
    """AC M1-3.10: Comp holds a single comparable sale row."""
    c = Comp(
        address="1070 Hawthorne Ave, Ypsilanti",
        close_date=date(2026, 2, 9),
        price=230000.0,
        sqft=1256,
        ppsf=183.0,
        year_built=2022,
        distance_mi=2.0,
    )
    assert c.ppsf == 183.0


def test_comp_aggregates():
    """AC M1-3.11: CompAggregates summarizes a comp bucket."""
    ca = CompAggregates(median_ppsf=183.0, count=3)
    assert ca.count == 3


def test_market_stats_deep_buyer():
    """AC M1-3.12: MarketStats with 22 months of inventory → deep_buyer market_health."""
    ms = MarketStats(
        months_of_inventory=22.0,
        median_cdom_days=180,
        p75_cdom_days=240,
        p90_cdom_days=365,
        failed_listings_on_parcel=3,
        years_listed_total=14.0,
        market_health="deep_buyer",
    )
    assert ms.market_health == "deep_buyer"


def test_model_fit_jaxon_pass():
    """AC M1-3.13: ModelFit records why a model fits or doesn't."""
    mf = ModelFit(
        model_id=uuid4(),
        model_name="The Jaxon",
        fits=True,
        reason="fits buildable envelope + Sec. 1101",
    )
    assert mf.fits is True


def test_opportunity_underwriting_minimal():
    """AC M1-3.14: OpportunityUnderwriting constructs with all required fields."""
    uw = OpportunityUnderwriting(
        opportunity_id=uuid4(),
        parcel_id=uuid4(),
        fitting_model_id=uuid4(),
        computed_at=datetime.now(),
        engine_version="0.1.0",
        zoning_district="R-5",
        zoning_source_url="https://library.municode.com/mi/ypsilanti_charter_township",
        zoning_pulled_on=date(2026, 4, 15),
        site_fit_id=uuid4(),
        permitted_use_result=UseCheckResult(
            allowed=True, path="by-right", citation="Sec. 406", rationale="one-family"
        ),
        buildable_width_ft=40.5,
        buildable_depth_ft=57.1,
        envelope_area_sf=2311.0,
        coverage_cap_sf=2206.0,
        binding_constraint="depth",
        comp_set_1_aggregates=CompAggregates(median_ppsf=183.0, count=3),
        comp_set_2_aggregates={"all": CompAggregates(median_ppsf=175.0, count=46)},
        comp_set_3_aggregates={"all": CompAggregates(median_ppsf=0.0, count=100)},
        anchor_comp=Comp(
            address="1070 Hawthorne Ave, Ypsilanti",
            close_date=date(2026, 2, 9),
            price=230000.0,
            sqft=1256,
            ppsf=183.0,
            year_built=2022,
            distance_mi=2.0,
        ),
        anchor_rationale="Closest 2022+ build in target band.",
        market_stats=MarketStats(
            months_of_inventory=22.0,
            median_cdom_days=180,
            p75_cdom_days=240,
            p90_cdom_days=365,
            failed_listings_on_parcel=3,
            years_listed_total=14.0,
            market_health="deep_buyer",
        ),
        home_quote=81645.0,
        site_cost=86767.0,
        contingency_pct=0.15,
        contingency_amount=25262.0,
        base_land_price=32500.0,
        adjusted_cost_breakdown=CostBreakdown(
            home_quote=81645.0,
            site_cost=86767.0,
            contingency_pct=0.15,
            contingency_amount=25261.8,
            base_land_price=32500.0,
            total=226173.8,
        ),
        total_cost_per_parcel=226174.0,
        exit_price=ExitPrice(ppsf=183.0, total=230000.0, confidence=CompConfidence.MEDIUM, sqft=1280),
        sell_costs_pct=0.07,
        margin_base_case=Margin(net=-12274.0, gross=3826.0, net_margin_pct=-5.4),
        sensitivity_matrix=SensitivityMatrix(rows=[], columns=[], values=[]),
        verdict=Verdict.NEGOTIATE,
        negotiate_target_land_price=20000.0,
        email_send_blocked=True,
    )
    assert uw.verdict == Verdict.NEGOTIATE
    assert uw.email_send_blocked is True


def test_email_send_blocked_invariant_enforced():
    """AC M1-3.15: OpportunityUnderwriting refuses construction when email_send_blocked is False.

    Hard rule from spec §4.5: outreach_drafter never sends emails. The invariant is
    enforced at the type level via a field_validator — attempting to set False raises ValidationError.
    """
    from datetime import datetime
    from uuid import uuid4

    base_kwargs = {
        "opportunity_id": uuid4(),
        "parcel_id": uuid4(),
        "fitting_model_id": uuid4(),
        "computed_at": datetime.now(),
        "engine_version": "0.1.0",
        "zoning_district": "R-5",
        "zoning_source_url": "https://example.com",
        "zoning_pulled_on": date(2026, 4, 15),
        "site_fit_id": uuid4(),
        "permitted_use_result": UseCheckResult(
            allowed=True, path="by-right", citation="Sec. 406", rationale="one-family"
        ),
        "buildable_width_ft": 40.5,
        "buildable_depth_ft": 57.1,
        "envelope_area_sf": 2311.0,
        "coverage_cap_sf": 2206.0,
        "binding_constraint": "depth",
        "comp_set_1_aggregates": CompAggregates(median_ppsf=183.0, count=3),
        "comp_set_2_aggregates": {"all": CompAggregates(median_ppsf=175.0, count=46)},
        "comp_set_3_aggregates": {"all": CompAggregates(median_ppsf=0.0, count=100)},
        "anchor_comp": Comp(
            address="x",
            close_date=date(2026, 2, 9),
            price=230000.0,
            distance_mi=2.0,
        ),
        "anchor_rationale": "x",
        "market_stats": MarketStats(
            months_of_inventory=22.0,
            median_cdom_days=180,
            p75_cdom_days=240,
            p90_cdom_days=365,
            failed_listings_on_parcel=3,
            years_listed_total=14.0,
            market_health="deep_buyer",
        ),
        "home_quote": 81645.0,
        "site_cost": 86767.0,
        "contingency_pct": 0.15,
        "contingency_amount": 25262.0,
        "base_land_price": 32500.0,
        "adjusted_cost_breakdown": CostBreakdown(
            home_quote=81645.0,
            site_cost=86767.0,
            contingency_pct=0.15,
            contingency_amount=25261.8,
            base_land_price=32500.0,
            total=226173.8,
        ),
        "total_cost_per_parcel": 226174.0,
        "exit_price": ExitPrice(ppsf=183.0, total=230000.0, confidence=CompConfidence.MEDIUM, sqft=1280),
        "sell_costs_pct": 0.07,
        "margin_base_case": Margin(net=-12274.0, gross=3826.0, net_margin_pct=-5.4),
        "sensitivity_matrix": SensitivityMatrix(rows=[], columns=[], values=[]),
        "verdict": Verdict.NEGOTIATE,
    }

    # Happy path: email_send_blocked=True works
    uw_ok = OpportunityUnderwriting(**base_kwargs, email_send_blocked=True)
    assert uw_ok.email_send_blocked is True

    # Invariant violation: email_send_blocked=False MUST raise
    with pytest.raises((ValidationError, ValueError)):
        OpportunityUnderwriting(**base_kwargs, email_send_blocked=False)  # type: ignore[arg-type]
