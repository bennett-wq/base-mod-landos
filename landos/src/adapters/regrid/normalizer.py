"""Regrid bulk parcel record normalizer — raw dict → Parcel object.

Raises SkipRecord for any record that should not enter the system:
  - Missing required fields (ll_uuid, parcelnumb, state2, county)
  - Acreage not determinable (both acreage and ll_gisacre absent or zero)

Vacancy inference (Regrid has no direct vacancy flag):
  improvval == 0 or improvcode in VACANT_IMPROV_CODES → VACANT
  improvval > 0                                        → IMPROVED
  neither determinable                                 → UNKNOWN

Municipality linkage:
  Parcel.municipality_id cannot be derived from Regrid directly.
  Callers must supply a default_municipality_id (e.g., the Washtenaw County
  sentinel UUID for the bulk load) or a municipality_lookup dict keyed on
  lowercase city/township name. Records with no resolvable municipality
  raise SkipRecord when strict=True (default) or are skipped silently.

All type coercions are contained here. No external calls.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from src.adapters.regrid.field_map import (
    REQUIRED_REGRID_FIELDS,
    VACANT_IMPROV_CODES,
)
from src.models.enums import VacancyStatus
from src.models.parcel import Parcel

logger = logging.getLogger(__name__)


class SkipRecord(Exception):
    """Raised when a Regrid record should not produce a Parcel object."""


def normalize(
    record: dict,
    default_municipality_id: UUID | None = None,
    municipality_lookup: dict[str, UUID] | None = None,
    now: datetime | None = None,
) -> Parcel:
    """Normalize a raw Regrid bulk-export record dict into a Parcel object.

    Args:
        record:                  Raw field dict from Regrid bulk export.
        default_municipality_id: Fallback municipality UUID when lookup fails.
                                 Required when municipality_lookup is None.
        municipality_lookup:     Optional dict keyed on lowercase city/township
                                 name → municipality UUID.
        now:                     Timestamp for created_at / updated_at.
                                 Defaults to UTC now.

    Returns:
        A Parcel with all mappable fields populated.

    Raises:
        SkipRecord: If the record should be excluded from the system.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # ── Required-field presence check ─────────────────────────────────
    for field in REQUIRED_REGRID_FIELDS:
        if not record.get(field):
            raise SkipRecord(f"Missing required field: {field}")

    # ── Acreage — try acreage, fall back to ll_gisacre ────────────────
    acreage = _to_float_optional(record.get("acreage"))
    if not acreage or acreage <= 0:
        acreage = _to_float_optional(record.get("ll_gisacre"))
    if not acreage or acreage <= 0:
        raise SkipRecord(
            f"No usable acreage for parcel {record.get('parcelnumb')!r}"
        )

    # ── Municipality resolution ────────────────────────────────────────
    municipality_id = _resolve_municipality(
        record, municipality_lookup, default_municipality_id
    )
    if municipality_id is None:
        raise SkipRecord(
            f"Cannot resolve municipality for parcel {record.get('parcelnumb')!r}"
        )

    # ── Vacancy inference ──────────────────────────────────────────────
    vacancy_status = _infer_vacancy(record)

    # ── Source system IDs ──────────────────────────────────────────────
    source_system_ids: dict[str, str] = {
        "regrid_id": str(record["ll_uuid"]).strip(),
    }
    raw_pin = _to_str_optional(record.get("parcelnumb_no_formatting"))
    if raw_pin:
        source_system_ids["county_pin"] = raw_pin

    # ── Scalar field mapping ──────────────────────────────────────────
    apn = str(record["parcelnumb"]).strip()
    jurisdiction_state = str(record["state2"]).strip().upper()
    county = str(record["county"]).strip()

    owner_name_raw = _to_str_optional(record.get("owner"))
    address_raw = _to_str_optional(record.get("address") or record.get("saddress"))
    zoning_code = _to_str_optional(record.get("zoning"))
    land_use_class = _to_str_optional(record.get("usedesc")) or _to_str_optional(record.get("usecode"))
    legal_description_raw = _to_str_optional(record.get("legaldesc"))
    frontage_feet = _to_float_optional(record.get("frontage"))
    depth_feet = _to_float_optional(record.get("depth"))
    flood_zone = _to_str_optional(record.get("floodzone"))
    tax_status = _to_str_optional(record.get("taxstatus"))

    # assessed_value — use taxyear + taxamt or fallback to assessedval
    assessed_value = _to_int_optional(record.get("assessedval"))
    if assessed_value is None:
        assessed_value = _to_int_optional(record.get("taxamt"))

    # ── Geometry ──────────────────────────────────────────────────────
    geometry: dict[str, Any] | None = _extract_geometry(record)
    centroid: dict[str, Any] | None = _build_centroid(record)

    return Parcel(
        source_system_ids=source_system_ids,
        jurisdiction_state=jurisdiction_state,
        county=county,
        municipality_id=municipality_id,
        apn_or_parcel_number=apn,
        acreage=acreage,
        vacancy_status=vacancy_status,
        owner_name_raw=owner_name_raw,
        address_raw=address_raw,
        zoning_code=zoning_code,
        land_use_class=land_use_class,
        legal_description_raw=legal_description_raw,
        frontage_feet=frontage_feet,
        depth_feet=depth_feet,
        flood_zone=flood_zone,
        tax_status=tax_status,
        assessed_value=assessed_value,
        geometry=geometry,
        centroid=centroid,
        created_at=now,
        updated_at=now,
    )


# ── Private helpers ────────────────────────────────────────────────────────

def _resolve_municipality(
    record: dict,
    lookup: dict[str, UUID] | None,
    default: UUID | None,
) -> UUID | None:
    if lookup:
        city_raw = _to_str_optional(record.get("city") or record.get("scity"))
        if city_raw:
            matched = lookup.get(city_raw.lower().strip())
            if matched:
                return matched
    return default


def _infer_vacancy(record: dict) -> VacancyStatus:
    """Infer VacancyStatus from improvement value, improvement code, or usedesc.

    Priority order:
      1. improvval > 0          → IMPROVED
      2. improvval == 0         → VACANT (unless improvcode contradicts)
      3. improvcode in VACANT   → VACANT
      4. usedesc contains VACANT → VACANT
      5. usedesc present (no VACANT) → IMPROVED
      6. nothing determinable   → UNKNOWN
    """
    improv_val = _to_float_optional(record.get("improvval"))
    if improv_val is not None:
        if improv_val > 0:
            return VacancyStatus.IMPROVED
        if improv_val == 0:
            improv_code = _to_str_optional(record.get("improvcode"))
            if improv_code and improv_code.upper() not in VACANT_IMPROV_CODES:
                return VacancyStatus.UNKNOWN
            return VacancyStatus.VACANT

    # No improvval — check improvcode alone
    improv_code = _to_str_optional(record.get("improvcode"))
    if improv_code:
        if improv_code.upper() in VACANT_IMPROV_CODES:
            return VacancyStatus.VACANT
        return VacancyStatus.IMPROVED

    # No improvval or improvcode — check usedesc for VACANT keyword
    usedesc = _to_str_optional(record.get("usedesc"))
    if usedesc:
        if "VACANT" in usedesc.upper():
            return VacancyStatus.VACANT
        # Has a use description but no vacancy indicator — likely improved
        return VacancyStatus.IMPROVED

    return VacancyStatus.UNKNOWN


def _extract_geometry(record: dict) -> dict[str, Any] | None:
    """Return GeoJSON geometry dict from the record, if present."""
    raw = record.get("geojson") or record.get("geometry")
    if isinstance(raw, dict) and raw.get("type"):
        return raw
    return None


def _build_centroid(record: dict) -> dict[str, Any] | None:
    """Build a GeoJSON Point centroid from lat/lon fields."""
    lat = _to_float_optional(record.get("lat") or record.get("latitude"))
    lon = _to_float_optional(record.get("lon") or record.get("longitude"))
    if lat is not None and lon is not None:
        return {"type": "Point", "coordinates": [lon, lat]}
    return None


def _to_float_optional(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return None


def _to_int_optional(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None


def _to_str_optional(value: object) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None
