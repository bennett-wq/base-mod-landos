"""Parcel object model — the atomic unit of land.

Fields per LANDOS_OBJECT_MODEL.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.enums import VacancyStatus


class Parcel(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    parcel_id: UUID = Field(default_factory=uuid4)
    source_system_ids: dict[str, str]  # e.g. {"regrid_id": "...", "county_pin": "..."}
    jurisdiction_state: str
    county: str
    municipality_id: UUID
    apn_or_parcel_number: str
    acreage: float
    vacancy_status: VacancyStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    address_raw: Optional[str] = None
    legal_description_raw: Optional[str] = None
    geometry: Optional[dict[str, Any]] = None  # GeoJSON
    centroid: Optional[dict[str, Any]] = None  # GeoJSON point
    current_owner_id: Optional[UUID] = None
    owner_name_raw: Optional[str] = None
    land_use_class: Optional[str] = None
    zoning_code: Optional[str] = None
    frontage_feet: Optional[float] = None
    depth_feet: Optional[float] = None
    flood_zone: Optional[str] = None
    topography_summary: Optional[str] = None
    topography_confidence: Optional[float] = None
    subdivision_id: Optional[UUID] = None
    site_condo_project_id: Optional[UUID] = None
    assessed_value: Optional[int] = None
    tax_status: Optional[str] = None
    opportunity_score: Optional[float] = None
    opportunity_score_version: Optional[str] = None
    split_candidate_flag: Optional[bool] = None
    split_candidate_confidence: Optional[float] = None
