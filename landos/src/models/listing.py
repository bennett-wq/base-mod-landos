"""Listing object model — a property offered for sale on the market.

Fields per LANDOS_OBJECT_MODEL.md.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.models.enums import StandardStatus


class Listing(BaseModel):
    # ── Required fields ──────────────────────────────────────────────
    listing_id: UUID = Field(default_factory=uuid4)
    source_system: str
    listing_key: str
    standard_status: StandardStatus
    list_price: int
    property_type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Optional fields ──────────────────────────────────────────────
    original_list_price: Optional[int] = None
    parcel_id: Optional[UUID] = None
    municipality_id: Optional[UUID] = None
    subdivision_name_raw: Optional[str] = None
    remarks_raw: Optional[str] = None
    remarks_classified: Optional[dict[str, Any]] = None
    remarks_classified_confidence: Optional[float] = None
    listing_agent_name: Optional[str] = None
    listing_agent_id: Optional[str] = None
    listing_office_name: Optional[str] = None
    listing_office_id: Optional[str] = None
    seller_name_raw: Optional[str] = None
    owner_id: Optional[UUID] = None
    lot_size_acres: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    dom: Optional[int] = None
    cdom: Optional[int] = None
    price_per_acre: Optional[float] = None
    close_price: Optional[int] = None
    close_date: Optional[date] = None
    list_date: Optional[date] = None
    expiration_date: Optional[date] = None
