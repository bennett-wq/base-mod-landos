"""Step 4.5 acceptance tests — Spark BBO Signal Intelligence.

Coverage:
  CDOM detection         (3 tests)
  Developer exit         (3 tests)
  Private remarks        (6 tests)
  Remarks excerpt safety (2 tests)
  Agent accumulation     (3 tests)
  Subdivision remnant    (4 tests)
  Reverse rules wired    (2 tests)
  Full integration       (3 tests)
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from src.adapters.spark.bbo_signals import (
    CDOM_THRESHOLD_DEFAULT,
    detect_agent_land_accumulation,
    detect_cdom_threshold,
    detect_developer_exit,
    detect_office_land_program,
    detect_private_remarks_signals,
    detect_subdivision_remnant,
)
from src.adapters.spark.event_factory import build_listing_private_remarks_signal_detected
from src.adapters.spark.ingestion import InMemoryListingStore, SparkIngestionAdapter
from src.adapters.spark.normalizer import normalize
from src.models.enums import StandardStatus
from src.models.listing import Listing
from src.triggers.context import TriggerContext
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.engine import TriggerEngine
from src.triggers.enums import PhaseGate
from src.triggers.rules import ALL_RULES, RO, RP, RQ, RR

_FIXED_TS = datetime(2026, 3, 9, 12, 0, 0, tzinfo=timezone.utc)


def _listing(**kwargs) -> Listing:
    base = dict(
        source_system="spark_rets",
        listing_key="TEST-001",
        standard_status=StandardStatus.ACTIVE,
        list_price=75000,
        property_type="Land",
    )
    base.update(kwargs)
    return Listing(**base)


def _engine() -> TriggerEngine:
    return TriggerEngine(rules=ALL_RULES, cooldown_tracker=InMemoryCooldownTracker())


def _ctx() -> TriggerContext:
    return TriggerContext(
        active_phase=PhaseGate.PHASE_1,
        current_timestamp=_FIXED_TS,
    )


def _land_record(**overrides) -> dict:
    base = {
        "ListingKey": "SPARK-BBO-001",
        "StandardStatus": "Active",
        "ListPrice": "95000",
        "PropertyType": "Land",
        "LotSizeAcres": "2.5",
        "ListAgentMlsId": "AGT-99",
        "ListAgentFullName": "Jane Smith",
        "ListOfficeMlsId": "OFF-42",
        "ListOfficeName": "ReMax Land",
    }
    base.update(overrides)
    return base


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: CDOM detection
# ═══════════════════════════════════════════════════════════════════════════

class TestCdomDetection:

    def test_cdom_above_threshold_detected(self):
        listing = _listing(cdom=91)
        assert detect_cdom_threshold(listing, threshold=90) is True

    def test_cdom_at_threshold_detected(self):
        listing = _listing(cdom=90)
        assert detect_cdom_threshold(listing, threshold=90) is True

    def test_cdom_below_threshold_not_detected(self):
        listing = _listing(cdom=89)
        assert detect_cdom_threshold(listing, threshold=90) is False

    def test_cdom_none_not_detected(self):
        listing = _listing(cdom=None)
        assert detect_cdom_threshold(listing, threshold=90) is False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: Developer exit detection
# ═══════════════════════════════════════════════════════════════════════════

class TestDeveloperExitDetection:

    def test_off_market_date_on_active_listing_detected(self):
        listing = _listing(
            off_market_date=date(2026, 2, 1),
            standard_status=StandardStatus.ACTIVE,
        )
        detected, reason = detect_developer_exit(listing)
        assert detected is True
        assert "off_market_date" in reason

    def test_cancellation_date_with_high_cdom_detected(self):
        listing = _listing(
            cancellation_date=date(2026, 2, 15),
            cdom=75,
        )
        detected, reason = detect_developer_exit(listing)
        assert detected is True
        assert "cancellation" in reason

    def test_no_exit_signals_not_detected(self):
        listing = _listing(cdom=30)
        detected, reason = detect_developer_exit(listing)
        assert detected is False
        assert reason == ""

    def test_major_change_type_withdrawn_detected(self):
        listing = _listing(major_change_type="Withdrawn")
        detected, reason = detect_developer_exit(listing)
        assert detected is True
        assert "Withdrawn" in reason

    def test_withdrawal_with_low_cdom_not_detected(self):
        """Withdrawal requires cdom >= 120."""
        listing = _listing(
            withdrawal_date=date(2026, 2, 1),
            cdom=90,
        )
        detected, reason = detect_developer_exit(listing)
        assert detected is False

    def test_withdrawal_with_high_cdom_detected(self):
        listing = _listing(
            withdrawal_date=date(2026, 2, 1),
            cdom=120,
        )
        detected, reason = detect_developer_exit(listing)
        assert detected is True
        assert "withdrawal" in reason


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: Private remarks signal detection — each category
# ═══════════════════════════════════════════════════════════════════════════

class TestPrivateRemarksSignals:

    def test_fatigue_language_detected(self):
        listing = _listing(private_remarks="bring any offer, motivated seller")
        categories = detect_private_remarks_signals(listing)
        assert "fatigue_language" in categories

    def test_package_and_bulk_language_detected(self):
        listing = _listing(private_remarks="package deal, all remaining lots available")
        categories = detect_private_remarks_signals(listing)
        assert "package_language" in categories
        assert "bulk_language" in categories

    def test_restriction_language_detected(self):
        listing = _listing(private_remarks="no subdivision per deed restriction")
        categories = detect_private_remarks_signals(listing)
        assert "restriction_language" in categories

    def test_utility_language_detected(self):
        listing = _listing(private_remarks="sewer available at street")
        categories = detect_private_remarks_signals(listing)
        assert "utility_language" in categories

    def test_none_remarks_returns_empty_list(self):
        listing = _listing(private_remarks=None)
        categories = detect_private_remarks_signals(listing)
        assert categories == []

    def test_empty_remarks_returns_empty_list(self):
        listing = _listing(private_remarks="")
        categories = detect_private_remarks_signals(listing)
        assert categories == []

    def test_no_signal_keywords_returns_empty_list(self):
        listing = _listing(private_remarks="Nice lot near the park. Call for details.")
        categories = detect_private_remarks_signals(listing)
        assert categories == []


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: Remarks excerpt safety
# ═══════════════════════════════════════════════════════════════════════════

class TestRemarksExcerptSafety:

    def test_long_remarks_truncated_to_200_chars(self):
        long_remarks = "bring any offer " + "X" * 500
        listing = _listing(private_remarks=long_remarks)
        event = build_listing_private_remarks_signal_detected(
            listing,
            detected_categories=["fatigue_language"],
            remarks_excerpt=long_remarks[:200],
            now=_FIXED_TS,
        )
        assert len(event.payload["remarks_excerpt"]) <= 200

    def test_full_remarks_never_in_payload(self):
        long_remarks = "bring any offer " + "S" * 500
        listing = _listing(private_remarks=long_remarks)
        categories = detect_private_remarks_signals(listing)
        event = build_listing_private_remarks_signal_detected(
            listing,
            detected_categories=categories,
            remarks_excerpt=(listing.private_remarks or "")[:200],
            now=_FIXED_TS,
        )
        # The full 500-char tail of X's should NOT appear in remarks_excerpt
        assert "S" * 201 not in event.payload["remarks_excerpt"]
        assert len(event.payload["remarks_excerpt"]) <= 200


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: Agent land accumulation detection
# ═══════════════════════════════════════════════════════════════════════════

class TestAgentAccumulationDetection:

    def test_five_listings_same_agent_detected(self):
        listings = [
            _listing(listing_key=f"L-{i}", list_agent_key="AGT-001")
            for i in range(5)
        ]
        trigger_listing = listings[0]
        detected, count = detect_agent_land_accumulation(trigger_listing, listings, threshold=3)
        assert detected is True
        assert count == 5

    def test_two_listings_below_threshold_not_detected(self):
        listings = [
            _listing(listing_key=f"L-{i}", list_agent_key="AGT-001")
            for i in range(2)
        ]
        detected, count = detect_agent_land_accumulation(listings[0], listings, threshold=3)
        assert detected is False
        assert count == 2

    def test_none_list_agent_key_not_detected(self):
        listing = _listing(list_agent_key=None)
        detected, count = detect_agent_land_accumulation(listing, [listing], threshold=1)
        assert detected is False
        assert count == 0


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5B: Office land program detection
# ═══════════════════════════════════════════════════════════════════════════

class TestOfficeDetection:

    def test_five_listings_same_office_detected(self):
        listings = [
            _listing(listing_key=f"L-{i}", listing_office_id="OFF-001")
            for i in range(5)
        ]
        detected, count = detect_office_land_program(listings[0], listings, threshold=5)
        assert detected is True
        assert count == 5

    def test_four_listings_below_threshold_not_detected(self):
        listings = [
            _listing(listing_key=f"L-{i}", listing_office_id="OFF-001")
            for i in range(4)
        ]
        detected, count = detect_office_land_program(listings[0], listings, threshold=5)
        assert detected is False
        assert count == 4

    def test_none_listing_office_id_not_detected(self):
        listing = _listing(listing_office_id=None)
        detected, count = detect_office_land_program(listing, [listing], threshold=1)
        assert detected is False
        assert count == 0


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: Subdivision remnant detection
# ═══════════════════════════════════════════════════════════════════════════

class TestSubdivisionRemnantDetection:

    def test_number_of_lots_above_one_detected(self):
        listing = _listing(number_of_lots=3)
        detected, reason = detect_subdivision_remnant(listing)
        assert detected is True
        assert "number_of_lots=3" in reason

    def test_legal_description_lot_block_plat_detected(self):
        listing = _listing(legal_description="Lot 14 of Block 7, Oak Hills Plat")
        detected, reason = detect_subdivision_remnant(listing)
        assert detected is True
        assert "Lot/Block/Plat" in reason

    def test_subdivision_name_with_high_cdom_detected(self):
        listing = _listing(subdivision_name_raw="Sunbrook Estates", cdom=200)
        detected, reason = detect_subdivision_remnant(listing)
        assert detected is True
        assert "subdivision_name_raw" in reason

    def test_no_signals_not_detected(self):
        listing = _listing(cdom=50)
        detected, reason = detect_subdivision_remnant(listing)
        assert detected is False
        assert reason == ""

    def test_number_of_lots_one_not_detected(self):
        listing = _listing(number_of_lots=1)
        detected, reason = detect_subdivision_remnant(listing)
        assert detected is False

    def test_subdivision_name_with_low_cdom_not_detected(self):
        """subdivision_name_raw alone without cdom >= 180 doesn't trigger."""
        listing = _listing(subdivision_name_raw="Oak Park Sub", cdom=100)
        detected, reason = detect_subdivision_remnant(listing)
        assert detected is False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: Reverse rules wired in ALL_RULES
# ═══════════════════════════════════════════════════════════════════════════

class TestReverseRulesWired:

    def test_ro_in_all_rules_targets_spark_signal_agent(self):
        rule_ids = [r.rule_id for r in ALL_RULES]
        assert RO.rule_id in rule_ids
        assert RO.wake_target == "spark_signal_agent"

    def test_rq_in_all_rules_targets_spark_signal_agent(self):
        rule_ids = [r.rule_id for r in ALL_RULES]
        assert RQ.rule_id in rule_ids
        assert RQ.wake_target == "spark_signal_agent"

    def test_rp_in_all_rules_targets_spark_signal_agent(self):
        rule_ids = [r.rule_id for r in ALL_RULES]
        assert RP.rule_id in rule_ids
        assert RP.wake_target == "spark_signal_agent"

    def test_rr_in_all_rules_targets_spark_signal_agent(self):
        rule_ids = [r.rule_id for r in ALL_RULES]
        assert RR.rule_id in rule_ids
        assert RR.wake_target == "spark_signal_agent"

    def test_all_bbo_forward_rules_present(self):
        """RI through RN2 all present in ALL_RULES."""
        from src.triggers.rules import RI, RJ, RK, RL, RM, RN1, RN2
        rule_ids = [r.rule_id for r in ALL_RULES]
        for rule in (RI, RJ, RK, RL, RM, RN1, RN2):
            assert rule.rule_id in rule_ids, f"{rule.rule_id} missing from ALL_RULES"

    def test_opportunity_routing_rules_present(self):
        """RS, RT, RU1, RU2 all present in ALL_RULES."""
        from src.triggers.rules import RS, RT, RU1, RU2
        rule_ids = [r.rule_id for r in ALL_RULES]
        for rule in (RS, RT, RU1, RU2):
            assert rule.rule_id in rule_ids, f"{rule.rule_id} missing from ALL_RULES"


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: Full integration tests
# ═══════════════════════════════════════════════════════════════════════════

class TestBboIntegration:

    def _make_adapter(self, threshold: int = CDOM_THRESHOLD_DEFAULT) -> SparkIngestionAdapter:
        engine = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)
        adapter._bbo_cdom_threshold = threshold  # allow override for test
        return adapter

    def test_cdom_threshold_event_emitted(self):
        """Listing with cdom=120 (>= default 90) emits RI event."""
        engine = _engine()
        store = InMemoryListingStore()

        class _TestAdapter(SparkIngestionAdapter):
            def _detect_and_build_bbo_events(self, listing, now, cdom_threshold=90):
                return super()._detect_and_build_bbo_events(listing, now, cdom_threshold=90)

        adapter = _TestAdapter(engine=engine, context=_ctx(), store=store)
        record = _land_record(CumulativeDaysOnMarket="120")
        results = adapter.process_batch([record], now=_FIXED_TS)

        event_types = [r.event_type for r in results]
        assert "listing_bbo_cdom_threshold_crossed" in event_types

    def test_private_remarks_event_emitted(self):
        """Listing with package language in private_remarks emits remarks event."""
        engine = _engine()
        store = InMemoryListingStore()
        adapter = SparkIngestionAdapter(engine=engine, context=_ctx(), store=store)
        record = _land_record(PrivateRemarks="package deal, all remaining lots available")
        results = adapter.process_batch([record], now=_FIXED_TS)

        event_types = [r.event_type for r in results]
        assert "listing_private_remarks_signal_detected" in event_types

    def test_agent_accumulation_event_emitted_at_threshold(self):
        """When 2+ listings share same ListAgentKey, RL event fires with threshold=2."""
        engine = _engine()
        store = InMemoryListingStore()

        class _ThresholdAdapter(SparkIngestionAdapter):
            def _detect_and_build_bbo_events(self, listing, now, cdom_threshold=CDOM_THRESHOLD_DEFAULT):
                from src.adapters.spark.bbo_signals import (
                    detect_agent_land_accumulation,
                    detect_cdom_threshold,
                    detect_developer_exit,
                    detect_office_land_program,
                    detect_private_remarks_signals,
                    detect_subdivision_remnant,
                )
                from src.adapters.spark.event_factory import (
                    build_agent_land_accumulation_detected,
                    build_developer_exit_signal_detected,
                    build_listing_bbo_cdom_threshold_crossed,
                    build_listing_private_remarks_signal_detected,
                    build_office_land_program_detected,
                    build_subdivision_remnant_detected,
                )
                bbo_events = []
                all_listings = self.store_listings
                if detect_cdom_threshold(listing, threshold=cdom_threshold):
                    bbo_events.append(
                        build_listing_bbo_cdom_threshold_crossed(
                            listing, cdom=listing.cdom, threshold=cdom_threshold, now=now
                        )
                    )
                remarks_categories = detect_private_remarks_signals(listing)
                if remarks_categories:
                    bbo_events.append(
                        build_listing_private_remarks_signal_detected(
                            listing,
                            detected_categories=remarks_categories,
                            remarks_excerpt=(listing.private_remarks or "")[:200],
                            now=now,
                        )
                    )
                # Use threshold=2 for this test
                agent_detected, agent_count = detect_agent_land_accumulation(listing, all_listings, threshold=2)
                if agent_detected:
                    bbo_events.append(
                        build_agent_land_accumulation_detected(listing, agent_listing_count=agent_count, now=now)
                    )
                office_detected, office_count = detect_office_land_program(listing, all_listings)
                if office_detected:
                    bbo_events.append(
                        build_office_land_program_detected(listing, office_listing_count=office_count, now=now)
                    )
                exit_detected, exit_reason = detect_developer_exit(listing)
                if exit_detected:
                    bbo_events.append(
                        build_developer_exit_signal_detected(listing, reason=exit_reason, now=now)
                    )
                remnant_detected, remnant_reason = detect_subdivision_remnant(listing)
                if remnant_detected:
                    bbo_events.append(
                        build_subdivision_remnant_detected(listing, reason=remnant_reason, now=now)
                    )
                return bbo_events

        adapter = _ThresholdAdapter(engine=engine, context=_ctx(), store=store)

        # Ingest 2 listings with same ListAgentKey
        records = [
            _land_record(ListingKey="L-1", ListAgentKey="AGT-001"),
            _land_record(ListingKey="L-2", ListAgentKey="AGT-001"),
        ]
        results = adapter.process_batch(records, now=_FIXED_TS)

        event_types = [r.event_type for r in results]
        assert "agent_land_accumulation_detected" in event_types

    def test_bbo_fields_mapped_from_spark_record(self):
        """BBO fields in the Spark record are correctly normalized into the Listing."""
        record = _land_record(
            CumulativeDaysOnMarket="150",
            PrivateRemarks="bring any offer",
            ListAgentKey="AGT-UUID-001",
            LegalDescription="Lot 5 of Block 2, Oak Hills Plat",
            NumberOfLots="3",
        )
        listing = normalize(record, now=_FIXED_TS)
        assert listing.cdom == 150
        assert listing.private_remarks == "bring any offer"
        assert listing.list_agent_key == "AGT-UUID-001"
        assert listing.legal_description == "Lot 5 of Block 2, Oak Hills Plat"
        assert listing.number_of_lots == 3

    def test_missing_bbo_fields_do_not_raise(self):
        """A record with no BBO fields normalizes successfully."""
        record = _land_record()  # no BBO fields
        listing = normalize(record, now=_FIXED_TS)
        assert listing.cdom is None
        assert listing.private_remarks is None
        assert listing.list_agent_key is None
        assert listing.legal_description is None
