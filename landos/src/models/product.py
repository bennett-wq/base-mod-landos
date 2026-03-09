"""HomeProduct and SiteFit object models.

Fields per LANDOS_OBJECT_MODEL.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from src.models.enums import (
    AccessType,
    FitResult,
    FoundationType,
    GarageType,
    SewerAvailable,
    SetbackFitResult,
    UtilityOverallStatus,
    WaterAvailable,
)


class HomeProduct(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    home_product_id: UUID = Field(default_factory=uuid4)
    model_name: str
    footprint_width_feet: float
    footprint_depth_feet: float
    stories: int
    square_footage: int
    base_price: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    garage_type: Optional[GarageType] = None
    foundation_type: Optional[FoundationType] = None
    min_lot_width_feet: Optional[float] = None
    min_lot_depth_feet: Optional[float] = None
    min_lot_acres: Optional[float] = None
    utility_requirements: Optional[dict[str, Any]] = None
    product_line: Optional[str] = None
    active: Optional[bool] = None
    image_url: Optional[str] = None
    spec_sheet_url: Optional[str] = None


class SiteFit(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    site_fit_id: UUID = Field(default_factory=uuid4)
    parcel_id: UUID
    home_product_id: UUID
    fit_result: FitResult
    fit_confidence: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("fit_confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("fit_confidence must be between 0.0 and 1.0")
        return v

    # ── Setback analysis fields ──────────────────────────────────────
    front_setback_required_feet: Optional[float] = None
    side_setback_required_feet: Optional[float] = None
    rear_setback_required_feet: Optional[float] = None
    front_setback_available_feet: Optional[float] = None
    side_setback_available_feet: Optional[float] = None
    rear_setback_available_feet: Optional[float] = None
    setback_fit_result: Optional[SetbackFitResult] = None
    setback_source: Optional[str] = None

    # ── Utility analysis fields ──────────────────────────────────────
    sewer_available: Optional[SewerAvailable] = None
    sewer_connection_cost_estimate: Optional[int] = None
    water_available: Optional[WaterAvailable] = None
    water_connection_cost_estimate: Optional[int] = None
    electric_available: Optional[bool] = None
    gas_available: Optional[bool] = None
    utility_overall_status: Optional[UtilityOverallStatus] = None
    utility_confidence: Optional[float] = None

    # ── General site feasibility fields ──────────────────────────────
    access_type: Optional[AccessType] = None
    slope_concern: Optional[bool] = None
    flood_concern: Optional[bool] = None
    wetland_concern: Optional[bool] = None
    environmental_flag: Optional[bool] = None
    notes: Optional[str] = None
    notes_confidence: Optional[float] = None
    requires_human_review: Optional[bool] = None
