"""Engine cost — cost stack and incentive adjustment. Pure math, no I/O."""

from __future__ import annotations

from src.models.opportunity import CostBreakdown, Program


def cost_stack(
    home_quote: float,
    site_cost: float,
    contingency_pct: float,
    land: float,
) -> CostBreakdown:
    """Bennett-specified formula: quote + site + contingency*(quote+site) + land.

    Spec §6 cost.py. Contingency is applied to quote + site, not to land.
    """
    contingency_base = home_quote + site_cost
    contingency_amount = contingency_base * contingency_pct
    total = home_quote + site_cost + contingency_amount + land
    return CostBreakdown(
        home_quote=home_quote,
        site_cost=site_cost,
        contingency_pct=contingency_pct,
        contingency_amount=round(contingency_amount, 2),
        base_land_price=land,
        total=round(total, 2),
    )


def incentive_adjust(base: CostBreakdown, programs: list[Program]) -> CostBreakdown:
    """Apply program deltas to the cost stack. Each applicable program's
    value_to_deal is subtracted from the total (a positive value_to_deal
    represents money saved / tax abated / grant received).

    Spec §4.4 — only programs where applies_to_parcel=True count.
    """
    net_delta = sum(p.value_to_deal for p in programs if p.applies_to_parcel)
    return CostBreakdown(
        home_quote=base.home_quote,
        site_cost=base.site_cost,
        contingency_pct=base.contingency_pct,
        contingency_amount=base.contingency_amount,
        base_land_price=base.base_land_price,
        total=round(base.total - net_delta, 2),
    )
