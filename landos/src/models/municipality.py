"""Municipality and MunicipalEvent object models.

Fields per LANDOS_OBJECT_MODEL.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.enums import (
    ApprovalAuthorityType,
    LandDivisionPosture,
    MunicipalEventType,
    MunicipalityType,
    OccurredAtPrecision,
    SB23Posture,
    Section108_6Posture,
    SewerServiceType,
    WaterServiceType,
)


class Municipality(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    municipality_id: UUID = Field(default_factory=uuid4)
    name: str
    municipality_type: MunicipalityType
    state: str
    county: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    fips_code: Optional[str] = None
    geometry: Optional[dict[str, Any]] = None  # GeoJSON
    population: Optional[int] = None
    approval_authority_type: Optional[ApprovalAuthorityType] = None
    land_division_posture: Optional[LandDivisionPosture] = None
    land_division_posture_confidence: Optional[float] = None
    sb_23_posture: Optional[SB23Posture] = None
    section_108_6_posture: Optional[Section108_6Posture] = None
    minimum_lot_size_sf: Optional[int] = None
    minimum_frontage_feet: Optional[float] = None
    sewer_service_type: Optional[SewerServiceType] = None
    water_service_type: Optional[WaterServiceType] = None
    zoning_ordinance_url: Optional[str] = None
    master_plan_url: Optional[str] = None
    incentive_density_score: Optional[float] = None
    market_wake_score: Optional[float] = None
    market_wake_score_version: Optional[str] = None
    last_municipal_event_at: Optional[datetime] = None
    notes: Optional[str] = None
    notes_confidence: Optional[float] = None


class MunicipalEvent(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    municipal_event_id: UUID = Field(default_factory=uuid4)
    municipality_id: UUID
    event_type: MunicipalEventType
    occurred_at: datetime  # may be approximate for historical records
    source_system: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    source_document_ref: Optional[str] = None
    occurred_at_precision: Optional[OccurredAtPrecision] = None
    parcel_ids: Optional[list[UUID]] = None
    subdivision_id: Optional[UUID] = None
    site_condo_project_id: Optional[UUID] = None
    developer_entity_id: Optional[UUID] = None
    details: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    notes_confidence: Optional[float] = None
    detection_method: Optional[str] = None
    updated_at: Optional[datetime] = None
