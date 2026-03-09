"""Subdivision, SiteCondoProject, and DeveloperEntity object models.

Fields per LANDOS_OBJECT_MODEL.md.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.enums import (
    BondStatus,
    ConnectionStatus,
    DeveloperEntityType,
    InfrastructureStatus,
)


class Subdivision(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    subdivision_id: UUID = Field(default_factory=uuid4)
    name: str
    municipality_id: UUID
    county: str
    state: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    plat_date: Optional[date] = None
    plat_municipal_event_id: Optional[UUID] = None
    total_lots: Optional[int] = None
    vacant_lots: Optional[int] = None
    improved_lots: Optional[int] = None
    vacancy_ratio: Optional[float] = None
    infrastructure_status: Optional[InfrastructureStatus] = None
    sewer_status: Optional[ConnectionStatus] = None
    water_status: Optional[ConnectionStatus] = None
    hoa_exists: Optional[bool] = None
    developer_entity_id: Optional[UUID] = None
    developer_control_active: Optional[bool] = None
    stall_flag: Optional[bool] = None
    stall_score: Optional[float] = None
    stall_score_version: Optional[str] = None
    stall_detected_at: Optional[datetime] = None
    years_since_plat: Optional[float] = None
    bond_status: Optional[BondStatus] = None
    parcel_ids: Optional[list[UUID]] = None
    active_listing_count: Optional[int] = None
    geometry: Optional[dict[str, Any]] = None  # GeoJSON


class SiteCondoProject(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    site_condo_project_id: UUID = Field(default_factory=uuid4)
    name: str
    municipality_id: UUID
    county: str
    state: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    master_deed_date: Optional[date] = None
    master_deed_municipal_event_id: Optional[UUID] = None
    total_units: Optional[int] = None
    vacant_units: Optional[int] = None
    improved_units: Optional[int] = None
    vacancy_ratio: Optional[float] = None
    infrastructure_status: Optional[InfrastructureStatus] = None
    sewer_status: Optional[ConnectionStatus] = None
    water_status: Optional[ConnectionStatus] = None
    hoa_exists: Optional[bool] = None
    developer_entity_id: Optional[UUID] = None
    developer_control_active: Optional[bool] = None
    stall_flag: Optional[bool] = None
    stall_score: Optional[float] = None
    stall_score_version: Optional[str] = None
    years_since_master_deed: Optional[float] = None
    detection_method: Optional[str] = None
    detection_confidence: Optional[float] = None
    parcel_ids: Optional[list[UUID]] = None
    active_listing_count: Optional[int] = None
    geometry: Optional[dict[str, Any]] = None  # GeoJSON


class DeveloperEntity(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    developer_entity_id: UUID = Field(default_factory=uuid4)
    name: str
    entity_type: DeveloperEntityType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    alternate_names: Optional[list[str]] = None
    owner_ids: Optional[list[UUID]] = None
    subdivision_ids: Optional[list[UUID]] = None
    site_condo_project_ids: Optional[list[UUID]] = None
    active_listing_count: Optional[int] = None
    total_parcel_count: Optional[int] = None
    total_vacant_parcel_count: Optional[int] = None
    geographic_focus: Optional[str] = None
    fatigue_score: Optional[float] = None
    fatigue_score_version: Optional[str] = None
    fatigue_signals: Optional[dict[str, Any]] = None
    fatigue_score_confidence: Optional[float] = None
    exit_window_flag: Optional[bool] = None
    last_activity_at: Optional[datetime] = None
    detection_method: Optional[str] = None
