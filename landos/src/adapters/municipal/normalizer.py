"""Normalizer for municipal records → MunicipalEvent objects.

Takes raw municipal record data (from any source format) and normalizes
it into a MunicipalEvent model instance. Handles all 15 MunicipalEventType
values defined in the Object Model.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from src.models.enums import MunicipalEventType, OccurredAtPrecision
from src.models.municipality import MunicipalEvent


def _parse_datetime(value: Any) -> datetime:
    """Parse a datetime from string or return as-is if already datetime.

    Handles trailing 'Z' for Python 3.9 compatibility.
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Python 3.9: fromisoformat does not support trailing Z
        cleaned = value.replace("Z", "+00:00") if value.endswith("Z") else value
        return datetime.fromisoformat(cleaned)
    raise ValueError(f"Cannot parse datetime from {type(value).__name__}: {value!r}")


def _parse_uuid(value: Any) -> UUID:
    """Parse a UUID from string or return as-is if already UUID."""
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _parse_uuid_list(value: Any) -> Optional[list[UUID]]:
    """Parse a list of UUIDs, or return None if empty/absent."""
    if value is None:
        return None
    if isinstance(value, list):
        return [_parse_uuid(v) for v in value] if value else None
    return None


def normalize_municipal_record(
    raw: dict[str, Any],
    now: datetime | None = None,
) -> MunicipalEvent:
    """Normalize a raw municipal record dict into a MunicipalEvent.

    Required raw fields:
      - municipality_id: UUID or string
      - event_type: string matching MunicipalEventType values
      - occurred_at: ISO 8601 datetime string or datetime
      - source_system: string

    Optional raw fields:
      - municipal_event_id: UUID (auto-generated if absent)
      - source_document_ref: string
      - occurred_at_precision: string matching OccurredAtPrecision
      - parcel_ids: list of UUID strings
      - subdivision_id: UUID string
      - site_condo_project_id: UUID string
      - developer_entity_id: UUID string
      - details: dict
      - notes: string
      - notes_confidence: float
      - detection_method: string

    Raises ValueError on missing required fields or invalid event_type.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # ── Validate required fields ──────────────────────────────────────
    for field in ("municipality_id", "event_type", "occurred_at", "source_system"):
        if field not in raw or raw[field] is None:
            raise ValueError(f"Missing required field: {field}")

    # ── Parse event_type ──────────────────────────────────────────────
    raw_event_type = raw["event_type"]
    try:
        event_type = MunicipalEventType(raw_event_type)
    except ValueError:
        valid = [e.value for e in MunicipalEventType]
        raise ValueError(
            f"Invalid event_type '{raw_event_type}'. "
            f"Must be one of: {valid}"
        )

    # ── Parse occurred_at_precision ───────────────────────────────────
    precision = None
    if raw.get("occurred_at_precision") is not None:
        try:
            precision = OccurredAtPrecision(raw["occurred_at_precision"])
        except ValueError:
            pass  # Silently ignore invalid precision values

    return MunicipalEvent(
        municipal_event_id=(
            _parse_uuid(raw["municipal_event_id"])
            if raw.get("municipal_event_id") is not None
            else uuid4()
        ),
        municipality_id=_parse_uuid(raw["municipality_id"]),
        event_type=event_type,
        occurred_at=_parse_datetime(raw["occurred_at"]),
        source_system=raw["source_system"],
        created_at=now,
        # ── Optional fields ───────────────────────────────────────────
        source_document_ref=raw.get("source_document_ref"),
        occurred_at_precision=precision,
        parcel_ids=_parse_uuid_list(raw.get("parcel_ids")),
        subdivision_id=(
            _parse_uuid(raw["subdivision_id"])
            if raw.get("subdivision_id") is not None
            else None
        ),
        site_condo_project_id=(
            _parse_uuid(raw["site_condo_project_id"])
            if raw.get("site_condo_project_id") is not None
            else None
        ),
        developer_entity_id=(
            _parse_uuid(raw["developer_entity_id"])
            if raw.get("developer_entity_id") is not None
            else None
        ),
        details=raw.get("details"),
        notes=raw.get("notes"),
        notes_confidence=raw.get("notes_confidence"),
        detection_method=raw.get("detection_method"),
    )
