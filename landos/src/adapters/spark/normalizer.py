"""Spark RETS/RESO record normalizer — raw dict → Listing object.

Raises SkipRecord for any record that should not enter the system:
  - PropertyType not in LAND_PROPERTY_TYPES
  - Missing required fields (ListingKey, ListPrice, StandardStatus, PropertyType)

All type coercions happen here (strings → int, float, date).
No external calls; fully deterministic given the input dict and now timestamp.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from src.adapters.spark.field_map import LAND_PROPERTY_TYPES, STATUS_MAP
from src.models.enums import StandardStatus
from src.models.listing import Listing

logger = logging.getLogger(__name__)


class SkipRecord(Exception):
    """Raised when a Spark record should not produce a Listing object."""


_REQUIRED_FIELDS = ("ListingKey", "ListPrice", "StandardStatus", "PropertyType")


def normalize(record: dict, now: datetime | None = None) -> Listing:
    """Normalize a raw Spark RETS/RESO record dict into a Listing object.

    Args:
        record: Raw field dict from Spark feed (RESO field names).
        now:    Timestamp to use for created_at / updated_at.
                Defaults to UTC now if not provided.

    Returns:
        A Listing with all mappable fields populated.

    Raises:
        SkipRecord: If the record should be excluded from the system.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # ── Required-field presence check ─────────────────────────────────
    for field in _REQUIRED_FIELDS:
        if record.get(field) is None:
            raise SkipRecord(f"Missing required field: {field}")

    # ── Property type filter ───────────────────────────────────────────
    property_type: str = str(record["PropertyType"]).strip()
    if property_type not in LAND_PROPERTY_TYPES:
        raise SkipRecord(
            f"PropertyType '{property_type}' not in LAND_PROPERTY_TYPES"
        )

    # ── Status normalization ───────────────────────────────────────────
    raw_status: str = str(record["StandardStatus"]).strip()
    normalized_status = STATUS_MAP.get(raw_status)
    if normalized_status is None:
        raise SkipRecord(f"Unknown StandardStatus: '{raw_status}'")
    standard_status = StandardStatus(normalized_status)

    # ── Price coercion ─────────────────────────────────────────────────
    list_price = _to_int(record["ListPrice"], "ListPrice")
    original_list_price = _to_int_optional(record.get("OriginalListPrice"))

    # ── Optional scalar fields ─────────────────────────────────────────
    lot_size_acres = _to_float_optional(record.get("LotSizeAcres"))
    latitude = _to_float_optional(record.get("Latitude"))
    longitude = _to_float_optional(record.get("Longitude"))
    dom = _to_int_optional(record.get("DaysOnMarket"))
    cdom = _to_int_optional(record.get("CumulativeDaysOnMarket"))
    close_price = _to_int_optional(record.get("ClosePrice"))

    # ── Date fields ────────────────────────────────────────────────────
    close_date = _to_date_optional(record.get("CloseDate"))
    list_date = _to_date_optional(record.get("ListingContractDate"))
    expiration_date = _to_date_optional(record.get("ExpirationDate"))

    # ── String fields (no transformation beyond stripping) ────────────
    listing_key = str(record["ListingKey"]).strip()
    remarks_raw = _to_str_optional(record.get("PublicRemarks"))
    listing_agent_id = _to_str_optional(record.get("ListAgentMlsId"))
    listing_agent_name = _to_str_optional(record.get("ListAgentFullName"))
    listing_office_id = _to_str_optional(record.get("ListOfficeMlsId"))
    listing_office_name = _to_str_optional(record.get("ListOfficeName"))
    subdivision_name_raw = _to_str_optional(record.get("SubdivisionName"))
    seller_name_raw = _to_str_optional(record.get("SellerName"))

    # ── price_per_acre derived field ───────────────────────────────────
    price_per_acre: float | None = None
    if lot_size_acres and lot_size_acres > 0 and list_price:
        price_per_acre = round(list_price / lot_size_acres, 2)

    return Listing(
        source_system="spark_rets",
        listing_key=listing_key,
        standard_status=standard_status,
        list_price=list_price,
        property_type=property_type,
        original_list_price=original_list_price,
        lot_size_acres=lot_size_acres,
        remarks_raw=remarks_raw,
        listing_agent_id=listing_agent_id,
        listing_agent_name=listing_agent_name,
        listing_office_id=listing_office_id,
        listing_office_name=listing_office_name,
        latitude=latitude,
        longitude=longitude,
        dom=dom,
        cdom=cdom,
        close_price=close_price,
        close_date=close_date,
        list_date=list_date,
        expiration_date=expiration_date,
        subdivision_name_raw=subdivision_name_raw,
        seller_name_raw=seller_name_raw,
        price_per_acre=price_per_acre,
        created_at=now,
        updated_at=now,
    )


# ── Private coercion helpers ───────────────────────────────────────────────

def _to_int(value: object, field_name: str) -> int:
    try:
        return int(float(str(value)))
    except (ValueError, TypeError) as exc:
        raise SkipRecord(f"Cannot coerce {field_name}={value!r} to int") from exc


def _to_int_optional(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None


def _to_float_optional(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return None


def _to_str_optional(value: object) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _to_date_optional(value: object) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    # Accept ISO 8601 date strings: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS...
    s = str(value).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        logger.warning("Cannot parse date value: %r", value)
        return None
