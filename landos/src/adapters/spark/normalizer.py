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

from src.adapters.spark.field_map import BBO_TO_LISTING, LAND_PROPERTY_TYPES, STATUS_MAP
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
    address_raw = _to_str_optional(record.get("UnparsedAddress"))
    parcel_number_raw = _to_str_optional(record.get("ParcelNumber"))

    # ── price_per_acre derived field ───────────────────────────────────
    price_per_acre: float | None = None
    if lot_size_acres and lot_size_acres > 0 and list_price:
        price_per_acre = round(list_price / lot_size_acres, 2)

    # ── BBO field mapping (all optional, missing keys are silently ignored) ─
    bbo_kwargs: dict = _map_bbo_fields(record)

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
        close_price=close_price,
        close_date=close_date,
        list_date=list_date,
        expiration_date=expiration_date,
        subdivision_name_raw=subdivision_name_raw,
        seller_name_raw=seller_name_raw,
        address_raw=address_raw,
        parcel_number_raw=parcel_number_raw,
        price_per_acre=price_per_acre,
        created_at=now,
        updated_at=now,
        **bbo_kwargs,
    )


# ── BBO field mapper ──────────────────────────────────────────────────────

# Fields that need integer coercion
_BBO_INT_FIELDS = {"cdom", "number_of_lots", "documents_count", "photos_count"}
# Fields that need float coercion
_BBO_FLOAT_FIELDS = {"previous_list_price", "frontage_length"}
# Fields that need date coercion
_BBO_DATE_FIELDS = {
    "back_on_market_date", "off_market_date", "withdrawal_date",
    "cancellation_date", "purchase_contract_date", "contract_status_change_date",
}
# Fields that need datetime coercion (ISO 8601 with time component)
_BBO_DATETIME_FIELDS = {
    "original_entry_timestamp", "status_change_timestamp",
    "price_change_timestamp", "major_change_timestamp", "pending_timestamp",
}


def _map_bbo_fields(record: dict) -> dict:
    """Map BBO source fields from record into Listing field kwargs.

    All fields are optional. Missing or unparseable values are silently
    omitted from the returned dict (Listing defaults them to None).
    """
    kwargs: dict = {}
    for src_key, dest_field in BBO_TO_LISTING.items():
        raw = record.get(src_key)
        if raw is None or raw == "":
            continue
        try:
            if dest_field in _BBO_INT_FIELDS:
                kwargs[dest_field] = _to_int_optional(raw)
            elif dest_field in _BBO_FLOAT_FIELDS:
                kwargs[dest_field] = _to_float_optional(raw)
            elif dest_field in _BBO_DATE_FIELDS:
                kwargs[dest_field] = _to_date_optional(raw)
            elif dest_field in _BBO_DATETIME_FIELDS:
                kwargs[dest_field] = _to_datetime_optional(raw)
            else:
                # String fields
                val = _to_str_optional(raw)
                if val is not None:
                    kwargs[dest_field] = val
        except Exception:
            # Defensive: never let a BBO field crash normalization
            logger.warning("BBO coercion failed for %s=%r", src_key, raw)
    return kwargs


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
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    # Accept ISO 8601 date strings: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS...
    s = str(value).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        logger.warning("Cannot parse date value: %r", value)
        return None


def _to_datetime_optional(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    s = str(value).strip()
    if not s:
        return None
    try:
        # Python 3.9 fromisoformat doesn't handle trailing 'Z'; replace with +00:00
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        logger.warning("Cannot parse datetime value: %r", value)
        return None
