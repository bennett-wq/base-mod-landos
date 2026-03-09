"""Tests for the canonical event envelope — Step 1 acceptance criteria.

Proves:
1. A valid raw event can be created and serialized.
2. A valid derived event can be created and serialized.
3. Invalid enum values fail validation.
4. Missing required fields fail validation.
5. Entity_refs must have at least one reference.
6. source_confidence range is enforced.
7. wake_priority range is enforced.
8. Fingerprint computation is deterministic.
9. Conditional derived/compound field requirements are enforced.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily, EventStatus, RoutingClass


# ── Helpers ──────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _raw_listing_event(**overrides) -> EventEnvelope:
    """Minimal valid raw listing event."""
    defaults = dict(
        event_type="listing_added",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=_now(),
        observed_at=_now(),
        source_system="spark_rets",
        entity_refs=EntityRefs(listing_id=uuid4()),
        payload={
            "listing_key": "MLS-12345",
            "list_price": 85000,
            "property_type": "Vacant Land",
            "acreage": 0.45,
            "address_raw": "123 Main St, Ypsilanti, MI",
            "listing_agent_id": "AGT-001",
            "listing_office_id": "OFC-001",
        },
    )
    defaults.update(overrides)
    return EventEnvelope(**defaults)


def _derived_cluster_event(**overrides) -> EventEnvelope:
    """Minimal valid derived cluster event."""
    source_event_id = uuid4()
    defaults = dict(
        event_type="owner_cluster_detected",
        event_family=EventFamily.CLUSTER_OWNER,
        event_class=EventClass.DERIVED,
        occurred_at=_now(),
        observed_at=_now(),
        source_system="scoring_engine",
        entity_refs=EntityRefs(cluster_id=uuid4(), owner_id=uuid4()),
        payload={
            "cluster_size": 4,
            "cluster_type": "same_owner",
            "member_listing_ids": [str(uuid4()) for _ in range(4)],
        },
        source_confidence=0.85,
        derived_from_event_ids=[source_event_id],
        causal_chain_id=uuid4(),
        generation_depth=1,
        emitted_by_agent_run_id=uuid4(),
    )
    defaults.update(overrides)
    return EventEnvelope(**defaults)


def _compound_event(**overrides) -> EventEnvelope:
    """Minimal valid compound event."""
    defaults = dict(
        event_type="split_ready_parcel",
        event_family=EventFamily.PARCEL_STATE,
        event_class=EventClass.COMPOUND,
        occurred_at=_now(),
        observed_at=_now(),
        source_system="trigger_engine",
        entity_refs=EntityRefs(parcel_id=uuid4(), municipality_id=uuid4()),
        payload={
            "adequate_frontage": True,
            "adequate_acreage": True,
            "favorable_split_posture": True,
        },
        source_confidence=0.72,
        derived_from_event_ids=[uuid4(), uuid4()],
        causal_chain_id=uuid4(),
        generation_depth=2,
    )
    defaults.update(overrides)
    return EventEnvelope(**defaults)


# ── 1. Valid raw event creation ──────────────────────────────────────

class TestRawEventCreation:
    def test_create_raw_event(self):
        evt = _raw_listing_event()
        assert evt.event_type == "listing_added"
        assert evt.event_family == EventFamily.LISTING
        assert evt.event_class == EventClass.RAW
        assert evt.status == EventStatus.PENDING
        assert evt.schema_version == "1.0"
        assert evt.generation_depth == 0
        assert evt.wake_priority == 5
        assert evt.routing_class == RoutingClass.STANDARD
        assert evt.ttl == 86400

    def test_raw_event_has_auto_id(self):
        evt = _raw_listing_event()
        assert evt.event_id is not None

    def test_raw_event_has_created_at(self):
        evt = _raw_listing_event()
        assert evt.created_at is not None

    def test_raw_event_serializes_to_dict(self):
        evt = _raw_listing_event()
        d = evt.to_dict()
        assert isinstance(d, dict)
        assert d["event_type"] == "listing_added"
        assert d["event_family"] == "listing"
        assert d["event_class"] == "raw"
        assert d["status"] == "pending"
        assert isinstance(d["payload"], dict)
        assert d["payload"]["listing_key"] == "MLS-12345"

    def test_raw_event_serializes_to_json(self):
        evt = _raw_listing_event()
        j = evt.to_json()
        assert isinstance(j, str)
        assert '"listing_added"' in j


# ── 2. Valid derived event creation ──────────────────────────────────

class TestDerivedEventCreation:
    def test_create_derived_event(self):
        evt = _derived_cluster_event()
        assert evt.event_type == "owner_cluster_detected"
        assert evt.event_family == EventFamily.CLUSTER_OWNER
        assert evt.event_class == EventClass.DERIVED
        assert evt.generation_depth == 1
        assert evt.source_confidence == 0.85
        assert len(evt.derived_from_event_ids) == 1

    def test_derived_event_serializes_to_dict(self):
        evt = _derived_cluster_event()
        d = evt.to_dict()
        assert d["event_class"] == "derived"
        assert d["generation_depth"] == 1
        assert len(d["derived_from_event_ids"]) == 1

    def test_derived_event_serializes_to_json(self):
        evt = _derived_cluster_event()
        j = evt.to_json()
        assert '"owner_cluster_detected"' in j


# ── 3. Invalid enum values fail ─────────────────────────────────────

class TestInvalidEnums:
    def test_invalid_event_family(self):
        with pytest.raises(ValidationError, match="event_family"):
            _raw_listing_event(event_family="nonexistent_family")

    def test_invalid_event_class(self):
        with pytest.raises(ValidationError, match="event_class"):
            _raw_listing_event(event_class="imaginary")

    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="status"):
            _raw_listing_event(status="bogus_status")

    def test_invalid_routing_class(self):
        with pytest.raises(ValidationError, match="routing_class"):
            _raw_listing_event(routing_class="turbo")


# ── 4. Missing required fields fail ─────────────────────────────────

class TestMissingRequired:
    def test_missing_event_type(self):
        with pytest.raises(ValidationError, match="event_type"):
            EventEnvelope(
                event_family=EventFamily.LISTING,
                event_class=EventClass.RAW,
                occurred_at=_now(),
                observed_at=_now(),
                source_system="spark_rets",
                entity_refs=EntityRefs(listing_id=uuid4()),
                payload={"listing_key": "X"},
            )

    def test_missing_source_system(self):
        with pytest.raises(ValidationError, match="source_system"):
            EventEnvelope(
                event_type="listing_added",
                event_family=EventFamily.LISTING,
                event_class=EventClass.RAW,
                occurred_at=_now(),
                observed_at=_now(),
                entity_refs=EntityRefs(listing_id=uuid4()),
                payload={"listing_key": "X"},
            )

    def test_missing_payload(self):
        with pytest.raises(ValidationError, match="payload"):
            EventEnvelope(
                event_type="listing_added",
                event_family=EventFamily.LISTING,
                event_class=EventClass.RAW,
                occurred_at=_now(),
                observed_at=_now(),
                source_system="spark_rets",
                entity_refs=EntityRefs(listing_id=uuid4()),
            )

    def test_missing_entity_refs(self):
        with pytest.raises(ValidationError, match="entity_refs"):
            EventEnvelope(
                event_type="listing_added",
                event_family=EventFamily.LISTING,
                event_class=EventClass.RAW,
                occurred_at=_now(),
                observed_at=_now(),
                source_system="spark_rets",
                payload={"listing_key": "X"},
            )


# ── 5. Entity refs must have at least one ref ───────────────────────

class TestEntityRefs:
    def test_empty_entity_refs_fail(self):
        with pytest.raises(ValidationError, match="at least one reference"):
            EntityRefs()

    def test_single_ref_ok(self):
        refs = EntityRefs(parcel_id=uuid4())
        assert refs.parcel_id is not None

    def test_multiple_refs_ok(self):
        refs = EntityRefs(listing_id=uuid4(), municipality_id=uuid4())
        assert refs.listing_id is not None
        assert refs.municipality_id is not None


# ── 6. Source confidence range ───────────────────────────────────────

class TestSourceConfidence:
    def test_confidence_below_zero(self):
        with pytest.raises(ValidationError, match="source_confidence"):
            _raw_listing_event(source_confidence=-0.1)

    def test_confidence_above_one(self):
        with pytest.raises(ValidationError, match="source_confidence"):
            _raw_listing_event(source_confidence=1.1)

    def test_confidence_at_bounds(self):
        evt_lo = _raw_listing_event(source_confidence=0.0)
        evt_hi = _raw_listing_event(source_confidence=1.0)
        assert evt_lo.source_confidence == 0.0
        assert evt_hi.source_confidence == 1.0


# ── 7. Wake priority range ──────────────────────────────────────────

class TestWakePriority:
    def test_priority_below_one(self):
        with pytest.raises(ValidationError, match="wake_priority"):
            _raw_listing_event(wake_priority=0)

    def test_priority_above_ten(self):
        with pytest.raises(ValidationError, match="wake_priority"):
            _raw_listing_event(wake_priority=11)

    def test_priority_at_bounds(self):
        evt_lo = _raw_listing_event(wake_priority=1)
        evt_hi = _raw_listing_event(wake_priority=10)
        assert evt_lo.wake_priority == 1
        assert evt_hi.wake_priority == 10


# ── 8. Fingerprint computation ───────────────────────────────────────

class TestFingerprint:
    def test_fingerprint_deterministic(self):
        evt = _raw_listing_event()
        assert evt.compute_fingerprint() == evt.compute_fingerprint()

    def test_same_payload_same_fingerprint(self):
        payload = {"a": 1, "b": "two"}
        evt1 = _raw_listing_event(payload=payload)
        evt2 = _raw_listing_event(payload=payload)
        assert evt1.compute_fingerprint() == evt2.compute_fingerprint()

    def test_different_payload_different_fingerprint(self):
        evt1 = _raw_listing_event(payload={"x": 1})
        evt2 = _raw_listing_event(payload={"x": 2})
        assert evt1.compute_fingerprint() != evt2.compute_fingerprint()


# ── 9. Conditional derived/compound field requirements ───────────────

class TestDerivedConditionalRequirements:
    """Per LANDOS_EVENT_LIBRARY.md:
    - source_confidence: required for derived and compound events.
    - derived_from_event_ids: required for derived and compound events.
    - emitted_by_agent_run_id: required for derived events.
    """

    def test_derived_missing_source_confidence_fails(self):
        with pytest.raises(ValidationError, match="source_confidence.*required"):
            _derived_cluster_event(source_confidence=None)

    def test_derived_missing_derived_from_event_ids_fails(self):
        with pytest.raises(ValidationError, match="derived_from_event_ids.*required"):
            _derived_cluster_event(derived_from_event_ids=None)

    def test_derived_empty_derived_from_event_ids_fails(self):
        with pytest.raises(ValidationError, match="derived_from_event_ids.*required"):
            _derived_cluster_event(derived_from_event_ids=[])

    def test_derived_missing_emitted_by_agent_run_id_fails(self):
        with pytest.raises(ValidationError, match="emitted_by_agent_run_id.*required"):
            _derived_cluster_event(emitted_by_agent_run_id=None)

    def test_raw_event_allows_absent_derived_fields(self):
        """Raw events must NOT require source_confidence, derived_from_event_ids,
        or emitted_by_agent_run_id."""
        evt = _raw_listing_event()
        assert evt.source_confidence is None
        assert evt.derived_from_event_ids is None
        assert evt.emitted_by_agent_run_id is None


class TestCompoundConditionalRequirements:
    def test_compound_event_valid(self):
        evt = _compound_event()
        assert evt.event_class == EventClass.COMPOUND
        assert evt.source_confidence == 0.72
        assert len(evt.derived_from_event_ids) == 2

    def test_compound_missing_source_confidence_fails(self):
        with pytest.raises(ValidationError, match="source_confidence.*required"):
            _compound_event(source_confidence=None)

    def test_compound_missing_derived_from_event_ids_fails(self):
        with pytest.raises(ValidationError, match="derived_from_event_ids.*required"):
            _compound_event(derived_from_event_ids=None)

    def test_compound_does_not_require_emitted_by_agent_run_id(self):
        """Compound events do not require emitted_by_agent_run_id (only derived do)."""
        evt = _compound_event(emitted_by_agent_run_id=None)
        assert evt.emitted_by_agent_run_id is None
