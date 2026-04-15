"""Opportunity object model — the convergence object.

Fields per LANDOS_OBJECT_MODEL.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.enums import OpportunityStatus, OpportunityType, PackagingReadiness


class Opportunity(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    opportunity_id: UUID = Field(default_factory=uuid4)
    opportunity_type: OpportunityType
    parcel_ids: list[UUID]
    municipality_id: UUID
    status: OpportunityStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    subdivision_id: Optional[UUID] = None
    site_condo_project_id: Optional[UUID] = None
    developer_entity_id: Optional[UUID] = None
    owner_cluster_id: Optional[UUID] = None
    listing_ids: Optional[list[UUID]] = None
    source_event_ids: Optional[list[UUID]] = None
    opportunity_score: Optional[float] = None
    opportunity_score_version: Optional[str] = None
    opportunity_score_confidence: Optional[float] = None
    score_factors: Optional[dict[str, Any]] = None
    packaging_readiness: Optional[PackagingReadiness] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    notes_confidence: Optional[float] = None


# ── Added 2026-04-15: stranded-lots underwriting types ────────────────────────
# Spec reference: §6.1.5 OpportunityUnderwriting model
# These types are Pydantic v2 BaseModel subclasses that the engine (M1-5 through
# M1-11) and agents (M2-3 through M2-10) will return. They coexist with the
# existing Opportunity class above — parallel companion, no replacement.

from datetime import date  # noqa: E402 — `datetime` already imported above
from enum import Enum
from typing import Literal
from uuid import uuid4 as _uuid4  # noqa: E402 — uuid4 already imported above

from pydantic import field_validator  # noqa: E402 — pydantic already imported above


class Verdict(str, Enum):
    """Underwriting outcome. See spec §6.1.5 recommendation section."""

    GO = "GO"
    NO_GO = "NO-GO"
    NEGOTIATE = "NEGOTIATE"


class CompConfidence(str, Enum):
    """Confidence tier for exit-price estimate. See spec §4.3 comp_narrator."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SetbackRules(BaseModel):
    """Dimensional standards for one zoning district.

    Populated by zoning_extractor agent from the municipality's Tier 1 vault
    note. See spec §4.1 and §9 (R-5 values).
    """

    district_code: str
    min_lot_sf: int
    min_width_ft: float
    max_coverage_pct: float
    max_height_ft: float
    max_stories: int
    front_setback_ft: float
    side_least_ft: float
    side_total_ft: float
    rear_setback_ft: float
    min_ground_floor_sf: int
    source_url: str
    pulled_on: date


class DwellingRules(BaseModel):
    """Sec. 1101-style dwelling compatibility rules.

    Min plan width, max plan ratio, foundation type, facade requirements.
    See spec §9 item 8.
    """

    min_plan_width_ft: float = 24.0
    max_plan_ratio: float = 3.0
    foundation_type: str = "perimeter-frost-depth"
    facade_front_required: bool = True
    entry_porch_required: bool = False
    source_section: str = "Sec. 1101"


class UseCheckResult(BaseModel):
    """permitted_use_checker agent output. See spec §4.2."""

    allowed: bool
    path: Literal["by-right", "conditional", "denied"]
    citation: str
    rationale: str


class CostBreakdown(BaseModel):
    """Cost stack from cost_stack(). See spec §6 cost.py."""

    home_quote: float
    site_cost: float
    contingency_pct: float
    contingency_amount: float
    base_land_price: float
    total: float


class ExitPrice(BaseModel):
    """exit_price() output. See spec §6 pricing.py."""

    ppsf: float
    total: float
    confidence: CompConfidence
    sqft: Optional[int] = None


class Margin(BaseModel):
    """margin_matrix() row. See spec §6 margin.py."""

    net: float
    gross: float
    net_margin_pct: float


class SensitivityMatrix(BaseModel):
    """sensitivity() output — 2D grid over exit × land prices. See spec §6."""

    rows: list[float] = Field(default_factory=list)      # exit prices
    columns: list[float] = Field(default_factory=list)   # land prices
    values: list[list[float]] = Field(default_factory=list)  # net_margin_pct grid


class Program(BaseModel):
    """TIF / PA 198 / NEZ / IFT / DPA / PILOT / etc. See spec §4.4 incentive_researcher."""

    name: str
    authority_type: str
    scope: str
    dates_active: str
    stacking_notes: str
    applies_to_parcel: bool
    source_citation: str
    value_to_deal: float


class Comp(BaseModel):
    """Single comparable sale row. See spec §4.3 comp_narrator."""

    address: str
    close_date: date
    price: float
    sqft: Optional[int] = None
    ppsf: Optional[float] = None
    year_built: Optional[int] = None
    distance_mi: float
    subdivision: Optional[str] = None
    cdom: Optional[int] = None


class CompAggregates(BaseModel):
    """Aggregate stats for one comp set bucket. See spec §4.3."""

    median_ppsf: float
    count: int
    median_price: Optional[float] = None
    date_range_days: Optional[int] = None


class MarketStats(BaseModel):
    """market_stats engine output. See spec §6 market_stats.py."""

    months_of_inventory: float
    median_cdom_days: int
    p75_cdom_days: int
    p90_cdom_days: int
    failed_listings_on_parcel: int
    years_listed_total: float
    market_health: Literal["hot", "balanced", "soft", "deep_buyer", "frozen"]


class ModelFit(BaseModel):
    """One row of the filter_models() result. See spec §6 models.py (engine)."""

    model_id: UUID
    model_name: str
    fits: bool
    reason: str
    per_parcel_ok: dict[str, bool] = Field(default_factory=dict)


class OpportunityUnderwriting(BaseModel):
    """Full underwriting result for a parcel or parcel package.

    Parallel companion to Opportunity (same relationship as SiteFit to Parcel).
    This is the single source of truth that serializes to three surfaces:
    vault markdown via src.adapters.obsidian.writer, JSON via
    api.routes.strategic, and Obsidian .base dashboards via frontmatter.

    Every field in the McCartney manual deliverable has a home here.
    See spec §6.1.5 for the field-by-field mapping.
    """

    # identity + provenance
    underwriting_id: UUID = Field(default_factory=_uuid4)
    opportunity_id: UUID
    parcel_id: UUID
    package_parcel_ids: list[UUID] = Field(default_factory=list)
    fitting_model_id: UUID
    computed_at: datetime
    engine_version: str
    codex_review_status: Literal["pending", "approved", "drift_detected"] = "pending"

    # zoning (from zoning_extractor + permitted_use_checker agents)
    zoning_district: str
    zoning_source_url: str
    zoning_pulled_on: date
    site_fit_id: UUID = Field(default_factory=_uuid4)  # FK to SiteFit in src/models/product.py
    permitted_use_result: UseCheckResult

    # envelope (populated on SiteFit by engine.envelope + engine.models)
    buildable_width_ft: float
    buildable_depth_ft: float
    envelope_area_sf: float
    coverage_cap_sf: float
    binding_constraint: Literal["depth", "width", "coverage"]

    # model fit (from engine.models.filter_models)
    fitting_models: list[ModelFit] = Field(default_factory=list)

    # comps (from comp_narrator — McCartney Phase D fidelity)
    comp_set_1_tight_sfr: list[Comp] = Field(default_factory=list)
    comp_set_1_aggregates: CompAggregates
    comp_set_2_broad_sfr: list[Comp] = Field(default_factory=list)
    comp_set_2_aggregates: dict[str, CompAggregates] = Field(default_factory=dict)
    comp_set_3_land: list[Comp] = Field(default_factory=list)
    comp_set_3_aggregates: dict[str, CompAggregates] = Field(default_factory=dict)
    anchor_comp: Comp
    anchor_rationale: str

    # market stats (from engine.market_stats)
    market_stats: MarketStats

    # incentives (from incentive_researcher agent)
    applicable_programs: list[Program] = Field(default_factory=list)
    net_incentive_delta: float = 0.0

    # cost + pricing + margin (from engine.cost + pricing + margin)
    home_quote: float
    site_cost: float
    contingency_pct: float
    contingency_amount: float
    base_land_price: float
    adjusted_cost_breakdown: CostBreakdown
    total_cost_per_parcel: float
    exit_price: ExitPrice
    sell_costs_pct: float
    margin_base_case: Margin
    sensitivity_matrix: SensitivityMatrix
    site_cost_overrun_sensitivity: list[tuple[float, float]] = Field(default_factory=list)

    # recommendation (from engine.recommendation)
    verdict: Verdict
    negotiate_target_land_price: Optional[float] = None
    rationale_bullets: list[str] = Field(default_factory=list)
    what_would_change_analysis: list[str] = Field(default_factory=list)
    suggested_offer_terms: Optional[str] = None

    # hard-rule enforcement
    has_offer_draft: bool = False
    email_send_blocked: Literal[True] = True  # INVARIANT — never False; see spec §4.5

    @field_validator("email_send_blocked")
    @classmethod
    def _enforce_email_blocked(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError(
                "email_send_blocked MUST be True — outreach_drafter invariant, see spec §4.5"
            )
        return v
