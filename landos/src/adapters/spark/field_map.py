"""Spark RETS/RESO field mapping constants for LandOS listing ingestion.

This module defines:
  - RESO_TO_LISTING: mapping from RESO standard field names to Listing model fields.
  - STATUS_MAP: normalization of RESO StandardStatus strings to StandardStatus enum values.
  - LAND_PROPERTY_TYPES: set of RESO PropertyType values treated as Michigan land/lot listings.

Phase 1 scope note:
  This mapping covers the standard public RESO surface only.
  Spark/BBO private remarks, custom fields, listing documents, and
  metadata-driven fields are NOT mapped here — see BBO depth follow-up
  requirements in the Step 4 session report.
"""

from __future__ import annotations

# ── RESO standard field → Listing model field ─────────────────────────────

RESO_TO_LISTING: dict[str, str] = {
    "ListingKey": "listing_key",
    "ListPrice": "list_price",
    "OriginalListPrice": "original_list_price",
    "PropertyType": "property_type",
    "LotSizeAcres": "lot_size_acres",
    "PublicRemarks": "remarks_raw",
    "ListAgentMlsId": "listing_agent_id",
    "ListAgentFullName": "listing_agent_name",
    "ListOfficeMlsId": "listing_office_id",
    "ListOfficeName": "listing_office_name",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "DaysOnMarket": "dom",
    "CumulativeDaysOnMarket": "cdom",
    "ClosePrice": "close_price",
    "CloseDate": "close_date",
    "ListingContractDate": "list_date",
    "ExpirationDate": "expiration_date",
    "SubdivisionName": "subdivision_name_raw",
    # SellerName is non-standard across RETS providers; map defensively
    "SellerName": "seller_name_raw",
}

# ── RESO StandardStatus → StandardStatus enum value ───────────────────────

STATUS_MAP: dict[str, str] = {
    "Active": "active",
    "ActiveUnderContract": "pending",
    "Pending": "pending",
    "Closed": "closed",
    "Withdrawn": "withdrawn",
    "Expired": "expired",
    "Canceled": "canceled",
    "Cancelled": "canceled",  # alternate spelling seen in some feeds
    "Hold": "withdrawn",      # treat Hold as withdrawn for Phase 1
}

# ── Land property type filter ──────────────────────────────────────────────
# Only records with a PropertyType in this set pass normalization.
# Phase 1: Michigan land/lot listings only.
# Extend this set (with care) when adding property sub-types in future steps.

LAND_PROPERTY_TYPES: frozenset[str] = frozenset({
    "Land",
    "Vacant Land",
    "Lots And Land",
})
