"""Step 4 acceptance tests — Spark MLS listing ingestion path.

Coverage:
  Normalizer (6 tests)     — raw dict → Listing; SkipRecord cases; coercions
  Event factory (8 tests)  — state diffs → correct event types/payloads
  Integration (7 tests)    — process_batch → TriggerEngine routing results

All tests use deterministic timestamps and explicit TriggerContext to avoid
wall-clock non-determinism (same pattern as test_trigger_engine.py).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest

from src.adapters.spark.event_factory import (
    build_listing_added,
    build_listing_expired,
    build_listing_price_reduced,
    build_listing_relisted,
    build_listing_status_changed,
)
from src.adapters.spark.ingestion import InMemoryListingStore, SparkIngestionAdapter
from src.adapters.spark.normalizer import SkipRecord, normalize
from src.models.enums import StandardStatus
from src.models.listing import Listing
from src.triggers.context import TriggerContext
from src.triggers.engine import TriggerEngine
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.enums import PhaseGate
from src.triggers.rules import ALL_RULES, RA, RB, RE

# ── Shared test fixtures ───────────────────────────────────────────────────

_FIXED_TS = datetime(2026, 3, 9, 12, 0, 0, tzinfo=timezone.utc)


def _ctx() -> TriggerContext:
    return TriggerContext(
        active_phase=PhaseGate.PHASE_1,
        current_timestamp=_FIXED_TS,
    )


def _engine() -> tuple[TriggerEngine, InMemoryCooldownTracker]:
    tracker = InMemoryCooldownTracker()
    engine = TriggerEngine(rules=ALL_RULES, cooldown_tracker=tracker)
    return engine, tracker


def _land_record(**overrides) -> dict:
    """Minimal valid Spark land record."""
    base = {
        "ListingKey": "SPARK-001",
        "StandardStatus": "Active",
        "ListPrice": "95000",
        "PropertyType": "Land",
        "LotSizeAcres": "2.5",
        "ListAgentMlsId": "AGT-99",
        "ListAgentFullName": "Jane Smith",
        "ListOfficeMlsId": "OFF-42",
        "ListOfficeName": "ReMax Land",
        "PublicRemarks": "Great buildable lot near river.",
        "ListingContractDate": "2026-01-15",
        "ExpirationDate": "2026-07-15",
    }
    base.update(overrides)
    return base


def _listing_from_record(**overrides) -> Listing:
    return normalize(_land_record(**overrides), now=_FIXED_TS)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: Normalizer tests
# ═══════════════════════════════════════════════════════════════════════════

class TestNormalizer:

    def test_valid_land_record_produces_listing(self):
        listing = normalize(_land_record(), now=_FIXED_TS)
        assert isinstance(listing, Listing)
        assert listing.listing_key == "SPARK-001"
        assert listing.source_system == "spark_rets"
        assert listing.list_price == 95000
        assert listing.standard_status == StandardStatus.ACTIVE
        assert listing.property_type == "Land"
        assert listing.lot_size_acres == 2.5
        assert listing.listing_agent_id == "AGT-99"
        assert listing.listing_office_id == "OFF-42"
        assert listing.remarks_raw == "Great buildable lot near river."
        assert listing.created_at == _FIXED_TS
        assert listing.updated_at == _FIXED_TS

    def test_non_land_property_type_raises_skip_record(self):
        with pytest.raises(SkipRecord):
            normalize(_land_record(PropertyType="Residential"), now=_FIXED_TS)

    def test_missing_optional_fields_produce_none(self):
        record = {
            "ListingKey": "SPARK-002",
            "StandardStatus": "Active",
            "ListPrice": "50000",
            "PropertyType": "Vacant Land",
        }
        listing = normalize(record, now=_FIXED_TS)
        assert listing.lot_size_acres is None
        assert listing.latitude is None
        assert listing.longitude is None
        assert listing.dom is None
        assert listing.cdom is None
        assert listing.remarks_raw is None
        assert listing.listing_agent_id is None
        assert listing.listing_office_id is None
        assert listing.list_date is None
        assert listing.expiration_date is None

    def test_status_string_normalizes_to_enum(self):
        listing = normalize(_land_record(StandardStatus="Expired"), now=_FIXED_TS)
        assert listing.standard_status == StandardStatus.EXPIRED

        listing2 = normalize(_land_record(StandardStatus="Pending"), now=_FIXED_TS)
        assert listing2.standard_status == StandardStatus.PENDING

    def test_lot_size_acres_coerced_from_string(self):
        listing = normalize(_land_record(LotSizeAcres="12.75"), now=_FIXED_TS)
        assert listing.lot_size_acres == 12.75
        assert isinstance(listing.lot_size_acres, float)

    def test_list_price_coerced_from_string(self):
        listing = normalize(_land_record(ListPrice="125000"), now=_FIXED_TS)
        assert listing.list_price == 125000
        assert isinstance(listing.list_price, int)

    def test_owner_name_maps_when_seller_name_missing(self):
        listing = normalize(
            _land_record(
                SellerName=None,
                OwnerName="Cook Jennifer L",
            ),
            now=_FIXED_TS,
        )
        assert listing.seller_name_raw is None
        assert listing.owner_name_raw == "Cook Jennifer L"


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: Event factory / diff tests
# ═══════════════════════════════════════════════════════════════════════════

class TestEventFactory:

    def test_listing_added_payload_complete(self):
        listing = _listing_from_record()
        event = build_listing_added(listing, now=_FIXED_TS)

        assert event.event_type == "listing_added"
        assert event.event_class.value == "raw"
        assert event.event_family.value == "listing"
        assert event.source_system == "spark_rets"
        assert event.source_record_id == "SPARK-001"
        assert event.entity_refs.listing_id == listing.listing_id
        assert event.payload["listing_key"] == "SPARK-001"
        assert event.payload["list_price"] == 95000
        assert event.payload["property_type"] == "Land"
        assert event.payload["acreage"] == 2.5
        assert event.payload["listing_agent_id"] == "AGT-99"
        assert event.payload["listing_office_id"] == "OFF-42"
        assert event.generation_depth == 0

    def test_no_changes_produces_no_events(self):
        """Same listing ingested twice → no events on second pass."""
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        record = _land_record()
        adapter.process_batch([record], now=_FIXED_TS)
        results = adapter.process_batch([record], now=_FIXED_TS)
        assert results == []

    def test_status_change_emits_listing_status_changed(self):
        old = _listing_from_record(StandardStatus="Active")
        new = _listing_from_record(StandardStatus="Pending")
        event = build_listing_status_changed(old, new, now=_FIXED_TS)

        assert event.event_type == "listing_status_changed"
        assert event.payload["old_status"] == "active"
        assert event.payload["new_status"] == "pending"
        assert event.payload["close_price"] is None
        assert event.payload["close_date"] is None
        assert event.source_record_id == "SPARK-001"

    def test_expired_transition_emits_both_status_changed_and_expired(self):
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        adapter.process_batch([_land_record(StandardStatus="Active")], now=_FIXED_TS)
        results = adapter.process_batch(
            [_land_record(StandardStatus="Expired")], now=_FIXED_TS
        )

        event_types = [r.event_type for r in results]
        assert "listing_status_changed" in event_types
        assert "listing_expired" in event_types
        assert len(results) == 2

    def test_relist_emits_both_status_changed_and_relisted(self):
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        adapter.process_batch([_land_record(StandardStatus="Expired")], now=_FIXED_TS)
        results = adapter.process_batch(
            [_land_record(StandardStatus="Active", ListingContractDate="2026-08-01")],
            now=_FIXED_TS,
        )

        event_types = [r.event_type for r in results]
        assert "listing_status_changed" in event_types
        assert "listing_relisted" in event_types
        assert len(results) == 2

    def test_price_decrease_emits_price_reduced_with_correct_percent(self):
        old = _listing_from_record(ListPrice="100000")
        new = _listing_from_record(ListPrice="90000")
        event = build_listing_price_reduced(old, new, reduction_count=1, now=_FIXED_TS)

        assert event.event_type == "listing_price_reduced"
        assert event.payload["old_price"] == 100000
        assert event.payload["new_price"] == 90000
        assert event.payload["percent_change"] == pytest.approx(-10.0, abs=0.01)
        assert event.payload["reduction_count"] == 1
        assert event.source_record_id == "SPARK-001"

    def test_price_increase_does_not_emit_price_reduced(self):
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        adapter.process_batch([_land_record(ListPrice="80000")], now=_FIXED_TS)
        results = adapter.process_batch([_land_record(ListPrice="95000")], now=_FIXED_TS)

        event_types = [r.event_type for r in results]
        assert "listing_price_reduced" not in event_types

    def test_gap_days_none_when_dates_unavailable(self):
        """gap_days is None when expiration_date and list_date are both absent."""
        old = normalize(
            {
                "ListingKey": "SPARK-003",
                "StandardStatus": "Expired",
                "ListPrice": "75000",
                "PropertyType": "Land",
                # No ExpirationDate, no ListingContractDate
            },
            now=_FIXED_TS,
        )
        new = normalize(
            {
                "ListingKey": "SPARK-003",
                "StandardStatus": "Active",
                "ListPrice": "75000",
                "PropertyType": "Land",
                # No ListingContractDate on new either
            },
            now=_FIXED_TS,
        )
        event = build_listing_relisted(old, new, now=_FIXED_TS)
        assert event.payload["gap_days"] is None


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: Integration / trigger wiring tests
# ═══════════════════════════════════════════════════════════════════════════

class TestIntegration:

    def test_listing_added_large_acreage_fires_ra_and_rb(self):
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        results = adapter.process_batch(
            [_land_record(LotSizeAcres="7.0")], now=_FIXED_TS
        )
        assert len(results) == 1
        result = results[0]
        assert RA.rule_id in result.fired_rules
        assert RB.rule_id in result.fired_rules

    def test_listing_added_small_acreage_fires_ra_suppresses_rb(self):
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        results = adapter.process_batch(
            [_land_record(LotSizeAcres="1.0")], now=_FIXED_TS
        )
        assert len(results) == 1
        result = results[0]
        assert RA.rule_id in result.fired_rules
        assert RB.rule_id not in result.fired_rules
        suppressed_ids = [s.rule_id for s in result.suppressed_rules]
        assert RB.rule_id in suppressed_ids

    def test_listing_expired_fires_re(self):
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        adapter.process_batch([_land_record(StandardStatus="Active")], now=_FIXED_TS)
        results = adapter.process_batch(
            [_land_record(StandardStatus="Expired")], now=_FIXED_TS
        )

        expired_result = next(r for r in results if r.event_type == "listing_expired")
        assert RE.rule_id in expired_result.fired_rules

    def test_re_wake_instruction_target(self):
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        adapter.process_batch([_land_record(StandardStatus="Active")], now=_FIXED_TS)
        results = adapter.process_batch(
            [_land_record(StandardStatus="Expired")], now=_FIXED_TS
        )

        expired_result = next(r for r in results if r.event_type == "listing_expired")
        re_wake = next(w for w in expired_result.wake_instructions if w.rule_id == RE.rule_id)
        assert re_wake.wake_target == "supply_intelligence_team"

    def test_non_land_record_produces_no_events(self):
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        results = adapter.process_batch(
            [_land_record(PropertyType="Residential")], now=_FIXED_TS
        )
        assert results == []

    def test_mixed_batch_correct_result_count(self):
        """Batch with 1 land record + 1 non-land → 1 RoutingResult."""
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        records = [
            _land_record(ListingKey="LAND-1"),
            _land_record(ListingKey="SKIP-1", PropertyType="Residential"),
        ]
        results = adapter.process_batch(records, now=_FIXED_TS)
        assert len(results) == 1
        assert results[0].event_type == "listing_added"

    def test_reduction_count_cumulative_does_not_reset_on_increase(self):
        """reduction_count increments on decrease; price increase does not reset it."""
        engine, _ = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)

        # Ingest initial listing at 100k
        adapter.process_batch([_land_record(ListPrice="100000")], now=_FIXED_TS)
        # Price drop 1: 100k → 90k
        adapter.process_batch([_land_record(ListPrice="90000")], now=_FIXED_TS)
        # Price rise: 90k → 95k (no listing_price_reduced, count stays at 1)
        adapter.process_batch([_land_record(ListPrice="95000")], now=_FIXED_TS)
        # Price drop 2: 95k → 85k
        results = adapter.process_batch([_land_record(ListPrice="85000")], now=_FIXED_TS)

        reduction_result = next(r for r in results if r.event_type == "listing_price_reduced")
        wake = reduction_result.wake_instructions  # no rules for price_reduced yet
        # Check via the payload via a direct event rebuild
        assert store.get_reduction_count("SPARK-001") == 2
