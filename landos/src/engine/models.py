"""Engine models filter — pure-math BaseMod catalog fit against a buildable envelope.

Spec §6 models.py. Uses the spec §9 item 8 Sec. 1101 rules:
min 24 ft dwelling width, max 3:1 plan ratio, perimeter frost-depth
foundation, front-facing facade.

Dimension check uses *total footprint* (box + garage + porch) against the
buildable envelope, not the raw box dimensions. The Sec. 1101 plan-width
and ratio checks operate on the box dimensions (the structure itself).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.engine.envelope import EnvelopeResult
from src.models.opportunity import DwellingRules, ModelFit


@dataclass
class HomeModelSpec:
    """Dimensions + price for one BaseMod home model from the catalog."""

    model_id: UUID
    name: str
    # box_width / box_depth: the structure footprint (no garage, no porch)
    # May be None if the catalog row omits them; filter logic falls back
    # to total_width / total_depth in that case for Sec. 1101 ratio check.
    box_width_ft: Optional[float]
    box_depth_ft: Optional[float]
    # total_width / total_depth: full footprint including garage + porch
    # These are the values checked against the buildable envelope.
    total_width_ft: Optional[float]
    total_depth_ft: Optional[float]
    living_sf: int
    bedrooms: int
    bathrooms: float
    base_price: float
    dwelling_type: str  # "SFR" | "duplex" | "triplex"


def filter_models(
    envelope: EnvelopeResult,
    catalog: list[HomeModelSpec],
    sec1101: DwellingRules,
) -> list[ModelFit]:
    """Filter catalog against envelope + Sec. 1101 plan rules.

    Checks (in order):
    1. Total footprint width ≤ buildable width
    2. Total footprint depth ≤ buildable depth
    3. Box width ≥ Sec. 1101 minimum plan width
    4. Box depth:width ratio ≤ Sec. 1101 maximum plan ratio
    5. Total footprint area ≤ coverage cap

    Returns one ModelFit per catalog entry; fits=True for models that
    pass every check.
    """
    results: list[ModelFit] = []

    for m in catalog:
        reasons: list[str] = []

        # Total footprint dimension check — must fit within buildable envelope
        if m.total_width_ft is not None and m.total_width_ft > envelope.buildable_width_ft:
            reasons.append(
                f"total width {m.total_width_ft} ft > buildable width "
                f"{envelope.buildable_width_ft} ft"
            )
        if m.total_depth_ft is not None and m.total_depth_ft > envelope.buildable_depth_ft:
            reasons.append(
                f"total depth {m.total_depth_ft} ft > buildable depth "
                f"{envelope.buildable_depth_ft} ft"
            )

        # Sec. 1101 minimum plan width — use box_width; fall back to total_width
        effective_width = m.box_width_ft if m.box_width_ft is not None else m.total_width_ft
        if effective_width is not None and effective_width < sec1101.min_plan_width_ft:
            reasons.append(
                f"plan width {effective_width} ft < Sec. 1101 min "
                f"{sec1101.min_plan_width_ft} ft"
            )

        # Sec. 1101 max plan ratio (depth:width) — use box dims; fall back to total dims
        effective_depth = m.box_depth_ft if m.box_depth_ft is not None else m.total_depth_ft
        if effective_width and effective_depth and effective_width > 0:
            ratio = effective_depth / effective_width
            if ratio > sec1101.max_plan_ratio:
                reasons.append(
                    f"plan ratio {ratio:.2f}:1 > Sec. 1101 max "
                    f"{sec1101.max_plan_ratio}:1"
                )

        # Coverage cap: total footprint area must not exceed coverage cap
        if m.total_width_ft is not None and m.total_depth_ft is not None:
            footprint_area = m.total_width_ft * m.total_depth_ft
            if footprint_area > envelope.coverage_cap_sf:
                reasons.append(
                    f"footprint area {footprint_area:.0f} sf > "
                    f"coverage cap {envelope.coverage_cap_sf:.0f} sf"
                )

        results.append(
            ModelFit(
                model_id=m.model_id,
                model_name=m.name,
                fits=len(reasons) == 0,
                reason=(
                    "; ".join(reasons) if reasons
                    else "fits buildable envelope + Sec. 1101"
                ),
            )
        )

    return results
