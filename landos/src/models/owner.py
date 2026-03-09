"""Owner and OwnerCluster object models.

Fields per LANDOS_OBJECT_MODEL.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.enums import ClusterType, OwnerEntityType


class Owner(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    owner_id: UUID = Field(default_factory=uuid4)
    owner_name_normalized: str
    entity_type: OwnerEntityType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    owner_name_raw: Optional[str] = None
    source_system: Optional[str] = None
    mailing_address: Optional[str] = None
    parcel_count: Optional[int] = None
    total_acreage_owned: Optional[float] = None
    linked_entity_names: Optional[list[str]] = None
    developer_entity_id: Optional[UUID] = None
    entity_type_confidence: Optional[float] = None


class OwnerCluster(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    cluster_id: UUID = Field(default_factory=uuid4)
    cluster_type: ClusterType
    detection_method: str
    member_count: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    owner_ids: Optional[list[UUID]] = None
    parcel_ids: Optional[list[UUID]] = None
    listing_ids: Optional[list[UUID]] = None
    municipality_id: Optional[UUID] = None
    subdivision_id: Optional[UUID] = None
    site_condo_project_id: Optional[UUID] = None
    developer_entity_id: Optional[UUID] = None
    geographic_centroid: Optional[dict[str, Any]] = None  # GeoJSON point
    geographic_radius_miles: Optional[float] = None
    total_acreage: Optional[float] = None
    total_list_value: Optional[int] = None
    agent_program_flag: Optional[bool] = None
    office_program_flag: Optional[bool] = None
    fatigue_score: Optional[float] = None
    fatigue_score_confidence: Optional[float] = None
