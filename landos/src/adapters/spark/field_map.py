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
    "ClosePrice": "close_price",
    "CloseDate": "close_date",
    "ListingContractDate": "list_date",
    "ExpirationDate": "expiration_date",
    "SubdivisionName": "subdivision_name_raw",
    # SellerName is non-standard across RETS providers; map defensively
    "SellerName": "seller_name_raw",
    # Address — UnparsedAddress is the RESO standard composite field
    "UnparsedAddress": "address_raw",
    # ParcelNumber — needed for parcel-to-listing linkage in Step 5
    "ParcelNumber": "parcel_number_raw",
}

# ── BBO private-role field → Listing model field ──────────────────────────

BBO_TO_LISTING: dict[str, str] = {
    # Family 1 — Developer Exit
    "OffMarketDate":         "off_market_date",
    "WithdrawalDate":        "withdrawal_date",
    "CancellationDate":      "cancellation_date",
    "MajorChangeTimestamp":  "major_change_timestamp",
    "MajorChangeType":       "major_change_type",

    # Family 2 — Listing Behavior
    "CumulativeDaysOnMarket":  "cdom",
    "PreviousListPrice":       "previous_list_price",
    "OriginalEntryTimestamp":  "original_entry_timestamp",
    "StatusChangeTimestamp":   "status_change_timestamp",
    "PriceChangeTimestamp":    "price_change_timestamp",
    "BackOnMarketDate":        "back_on_market_date",

    # Family 3 — Language Intelligence
    "PrivateRemarks":        "private_remarks",
    "ShowingInstructions":   "showing_instructions",

    # Family 4 — Agent/Office Clustering
    "ListAgentKey":          "list_agent_key",
    "CoListAgentKey":        "co_list_agent_key",
    "CoListOfficeKey":       "co_list_office_key",
    "BuyerAgentKey":         "buyer_agent_key",
    "BuyerOfficeKey":        "buyer_office_key",

    # Family 5 — Subdivision Remnant
    "LegalDescription":      "legal_description",
    "TaxLegalDescription":   "tax_legal_description",
    "LotDimensions":         "lot_dimensions",
    "FrontageLength":        "frontage_length",
    "PossibleUse":           "possible_use",
    "NumberOfLots":          "number_of_lots",

    # Family 6 — Market Velocity
    "PurchaseContractDate":  "purchase_contract_date",

    # Agent-only remarks (separate from PrivateRemarks)
    "Remarks_sp_Misc_co_Agent_sp_Only_sp_Remarks2": "agent_only_remarks",

    # Additional parcels
    "AdditionalParcelsYN": "additional_parcels_yn",
    "AdditionalParcelsDescription": "additional_parcels_description",

    # Development status
    "DevelopmentStatus": "development_status",

    # Contract/pending dates
    "ContractStatusChangeDate": "contract_status_change_date",
    "PendingTimestamp": "pending_timestamp",

    # Concessions
    "Concessions": "concessions",
    "ConcessionsComments": "concessions_comments",

    # Township (separate from municipality)
    "Township": "township_name",

    # Legal description (Spark uses different field names)
    "Remarks_sp_Misc_co_Legal3": "legal_remarks",

    # Document/media counts
    "DocumentsCount":        "documents_count",
    "PhotosCount":           "photos_count",

    # Land detail
    "Zoning":                "zoning",
    "ZoningDescription":     "zoning_description",
    "LotFeatures":           "lot_features",
    "RoadFrontageType":      "road_frontage_type",
    "RoadSurfaceType":       "road_surface_type",
    "Utilities":             "utilities",
    "Sewer":                 "sewer",
    "WaterSource":           "water_source",
    "CurrentUse":            "current_use",

    # ── Discovery batch (2026-04-08) — high-value unmapped fields ────────

    # Spark internal listing ID — needed for native API calls (genealogy)
    "ListingId":             "listing_id_spark",

    # On-market date — more precise than ListingContractDate
    "OnMarketDate":          "on_market_date",

    # Tax / economics (100% populated in Washtenaw)
    "TaxAnnualAmount":       "tax_annual_amount",
    "TaxAssessedValue":      "tax_assessed_value",
    "TaxYear":               "tax_year",
    "Tax_sp_Info_co_SEV":    "state_equalized_value",
    "Tax_sp_Info_co_Taxable_sp_Value": "taxable_value",

    # Agent contact (for broker outreach)
    "ListAgentEmail":        "listing_agent_email",
    "ListAgentMobilePhone":  "listing_agent_mobile",
    "ListAgentStateLicense": "listing_agent_license",

    # Office contact
    "ListOfficePhone":       "listing_office_phone",
    "ListOfficeEmail":       "listing_office_email",

    # Property classification
    "PropertySubType":       "property_sub_type",
    "Ownership":             "ownership_type",

    # Pre-computed price/acre from API (100% populated)
    "OfficeContract_sp_Info_co_List_sp_PriceAcre": "api_price_per_acre",

    # Road frontage in feet (93% populated)
    "General_sp_Property_sp_Info_co_Road_sp_Frontage": "road_frontage_feet",

    # Municipality name from API (100% populated)
    "Location_sp_Property_sp_Info_co_Municipality": "municipality_name",

    # School district (100% populated)
    "HighSchoolDistrict":    "school_district",

    # Cross street for location context (93%)
    "CrossStreet":           "cross_street",

    # Listing/financing terms
    "ListingTerms":          "listing_terms",

    # Freshness signals
    "PhotosChangeTimestamp":     "photos_change_timestamp",
    "DocumentsChangeTimestamp":  "documents_change_timestamp",
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
