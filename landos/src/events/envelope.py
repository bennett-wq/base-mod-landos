"""Canonical event envelope for the LandOS event mesh.

Implements the envelope schema defined in LANDOS_EVENT_LIBRARY.md.
This is a data-structure and serialization contract only — no runtime
trigger logic, no database wiring.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from src.events.enums import EventClass, EventFamily, EventStatus, RoutingClass


class EntityRefs(BaseModel):
    """Map of entity type to ID(s) that an event is about.

    At least one reference must be present.
    """

    parcel_id: Optional[UUID] = None
    parcel_ids: Optional[list[UUID]] = None
    listing_id: Optional[UUID] = None
    municipality_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    cluster_id: Optional[UUID] = None
    subdivision_id: Optional[UUID] = None
    site_condo_project_id: Optional[UUID] = None
    developer_entity_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    home_product_id: Optional[UUID] = None

    @model_validator(mode="after")
    def at_least_one_ref(self) -> EntityRefs:
        if not any(v is not None for v in self.model_dump().values()):
            raise ValueError("entity_refs must contain at least one reference")
        return self


class EventEnvelope(BaseModel):
    """Canonical event envelope — every event in LandOS rides inside this structure.

    Required and optional fields match LANDOS_EVENT_LIBRARY.md exactly.
    """

    # ── Required fields ──────────────────────────────────────────────
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    event_family: EventFamily
    event_class: EventClass
    occurred_at: datetime
    observed_at: datetime
    source_system: str
    entity_refs: EntityRefs
    payload: dict[str, Any]
    schema_version: str = "1.0"
    status: EventStatus = EventStatus.PENDING

    # ── Optional fields ──────────────────────────────────────────────
    source_record_id: Optional[str] = None
    source_confidence: Optional[float] = None
    derived_from_event_ids: Optional[list[UUID]] = None
    causal_chain_id: Optional[UUID] = None
    generation_depth: int = 0
    wake_priority: int = 5
    routing_class: RoutingClass = RoutingClass.STANDARD
    dedupe_key: Optional[str] = None
    fingerprint_hash: Optional[str] = None
    emitted_by_agent_run_id: Optional[UUID] = None
    ttl: int = 86400
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Validators ───────────────────────────────────────────────────

    @field_validator("source_confidence")
    @classmethod
    def confidence_in_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("source_confidence must be between 0.0 and 1.0")
        return v

    @field_validator("wake_priority")
    @classmethod
    def priority_in_range(cls, v: int) -> int:
        if not (1 <= v <= 10):
            raise ValueError("wake_priority must be between 1 and 10")
        return v

    @field_validator("generation_depth")
    @classmethod
    def depth_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("generation_depth must be >= 0")
        return v

    @model_validator(mode="after")
    def class_conditional_requirements(self) -> EventEnvelope:
        """Enforce fields that are conditionally required by event_class.

        Per LANDOS_EVENT_LIBRARY.md:
        - source_confidence: required for derived and compound events.
        - derived_from_event_ids: required for derived and compound events.
        - emitted_by_agent_run_id: required for derived events.
        Raw events may omit all of these.
        """
        if self.event_class in (EventClass.DERIVED, EventClass.COMPOUND):
            if self.source_confidence is None:
                raise ValueError(
                    f"source_confidence is required for {self.event_class.value} events"
                )
            if not self.derived_from_event_ids:
                raise ValueError(
                    f"derived_from_event_ids is required for {self.event_class.value} events"
                )
        if self.event_class == EventClass.DERIVED:
            if self.emitted_by_agent_run_id is None:
                raise ValueError(
                    "emitted_by_agent_run_id is required for derived events"
                )
        return self

    # ── Serialization helpers ────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict with JSON-safe types."""
        return json.loads(self.model_dump_json())

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return self.model_dump_json(indent=2)

    # ── Fingerprinting helper ────────────────────────────────────────

    def compute_fingerprint(self) -> str:
        """SHA-256 of the canonicalized (sorted-keys, whitespace-stripped) payload JSON.

        Per LANDOS_EVENT_LIBRARY.md: two events with different dedupe_keys
        but the same fingerprint_hash should be evaluated for merge.
        """
        canonical = json.dumps(self.payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()
