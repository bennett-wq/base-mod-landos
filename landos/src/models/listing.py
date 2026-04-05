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
    address_raw: Optional[str] = None
    parcel_number_raw: Optional[str] = None
    subdivision_name_raw: Optional[str] = None
    remarks_raw: Optional[str] = None
    remarks_classified: Optional[dict[str, Any]] = None
    remarks_classified_confidence: Optional[float] = None
    listing_agent_name: Optional[str] = None
    listing_agent_id: Optional[str] = None
    listing_office_name: Optional[str] = None
    listing_office_id: Optional[str] = None
    seller_name_raw: Optional[str] = None
    owner_name_raw: Optional[str] = None
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

    # BBO — Listing Behavior (Signal Family 2)
    previous_list_price: Optional[float] = None
    original_entry_timestamp: Optional[datetime] = None
    status_change_timestamp: Optional[datetime] = None
    price_change_timestamp: Optional[datetime] = None
    back_on_market_date: Optional[date] = None

    # BBO — Developer Exit (Signal Family 1)
    off_market_date: Optional[date] = None
    withdrawal_date: Optional[date] = None
    cancellation_date: Optional[date] = None
    major_change_timestamp: Optional[datetime] = None
    major_change_type: Optional[str] = None

    # BBO — Language Intelligence (Signal Family 3)
    private_remarks: Optional[str] = None
    showing_instructions: Optional[str] = None

    # BBO — Agent/Office Clustering (Signal Family 4)
    list_agent_key: Optional[str] = None
    co_list_agent_key: Optional[str] = None
    co_list_office_key: Optional[str] = None
    buyer_agent_key: Optional[str] = None
    buyer_office_key: Optional[str] = None

    # BBO — Subdivision Remnant (Signal Family 5)
    legal_description: Optional[str] = None
    tax_legal_description: Optional[str] = None
    lot_dimensions: Optional[str] = None
    frontage_length: Optional[float] = None
    possible_use: Optional[str] = None
    number_of_lots: Optional[int] = None

    # BBO — Land Detail
    zoning: Optional[str] = None
    zoning_description: Optional[str] = None
    lot_features: Optional[str] = None
    road_frontage_type: Optional[str] = None
    road_surface_type: Optional[str] = None
    utilities: Optional[str] = None
    sewer: Optional[str] = None
    water_source: Optional[str] = None
    current_use: Optional[str] = None

    # BBO — Market Velocity (Signal Family 6)
    purchase_contract_date: Optional[date] = None

    # BBO — Agent-only remarks (separate from PrivateRemarks)
    agent_only_remarks: Optional[str] = None
    legal_remarks: Optional[str] = None

    # BBO — Additional parcels
    additional_parcels_yn: Optional[str] = None
    additional_parcels_description: Optional[str] = None

    # BBO — Development status
    development_status: Optional[str] = None

    # BBO — Contract / Pending timestamps
    contract_status_change_date: Optional[date] = None
    pending_timestamp: Optional[datetime] = None

    # BBO — Concessions
    concessions: Optional[str] = None
    concessions_comments: Optional[str] = None

    # BBO — Township
    township_name: Optional[str] = None

    # BBO — Document / media counts
    documents_count: Optional[int] = None
    photos_count: Optional[int] = None
