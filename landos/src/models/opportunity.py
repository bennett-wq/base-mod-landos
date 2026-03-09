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
