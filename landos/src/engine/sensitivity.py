"""Engine sensitivity — 2D grid of net margin % over exit × land prices."""

from __future__ import annotations

from src.models.opportunity import SensitivityMatrix


def sensitivity(
    exits: list[float],
    lands: list[float],
    fixed_cost: float,
    sell_costs_pct: float,
) -> SensitivityMatrix:
    """Spec §6. Build a 2D grid: rows=exits, columns=lands, cell = net_margin_pct.

    fixed_cost is the cost stack subtotal WITHOUT land — e.g., McCartney's $193,674
    (quote $81,645 + site $86,767 + contingency $25,262).
    """
    values: list[list[float]] = []
    for exit_val in exits:
        row = []
        for land in lands:
            total_cost = fixed_cost + land
            sell_costs = exit_val * sell_costs_pct
            net = exit_val - sell_costs - total_cost
            margin_pct = (net / total_cost) * 100 if total_cost > 0 else 0.0
            row.append(round(margin_pct, 1))
        values.append(row)
    return SensitivityMatrix(rows=exits, columns=lands, values=values)
