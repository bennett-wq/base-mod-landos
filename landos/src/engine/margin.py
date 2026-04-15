"""Engine margin — net margin computation."""

from __future__ import annotations

from src.models.opportunity import CostBreakdown, ExitPrice, Margin


def margin_matrix(cost: CostBreakdown, exit_price: ExitPrice, sell_costs_pct: float) -> Margin:
    """Spec §6 margin.py. net = exit - sell_costs - cost; margin % = net / cost."""
    sell_costs = exit_price.total * sell_costs_pct
    net = exit_price.total - sell_costs - cost.total
    gross = exit_price.total - cost.total
    net_margin_pct = (net / cost.total) * 100 if cost.total > 0 else 0.0
    return Margin(
        net=round(net, 2),
        gross=round(gross, 2),
        net_margin_pct=round(net_margin_pct, 2),
    )
