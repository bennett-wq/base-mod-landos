"""Tests for listing history signal analysis — the seller-intent evidence engine.

Covers:
  - Partial release detection (few listed out of many owned)
  - Failed exit detection (expired/withdrawn history)
  - Relist cycle detection
  - Public + private remarks scanning
  - New pattern categories (distress, infrastructure, development)
  - Composite score computation
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.models.enums import StandardStatus
from src.models.listing import Listing
from src.scoring.listing_history_signals import (
    ListingHistoryEvidence,
    analyze_cluster_listing_history,
)

_FIXED_TS = datetime(2026, 4, 4, 12, 0, 0, tzinfo=timezone.utc)


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


class TestPartialRelease:
    def test_few_listed_out_of_many_detected(self):
        """2 listings out of 10 lots = partial release."""
        active = [_listing(listing_key="L-1"), _listing(listing_key="L-2")]
        ev = analyze_cluster_listing_history(active, [], total_cluster_lots=10)
        assert ev.partial_release_detected is True
        assert ev.partial_release_ratio == pytest.approx(0.2)

    def test_many_listed_out_of_few_not_detected(self):
        """4 listings out of 5 lots = NOT partial release."""
        active = [_listing(listing_key=f"L-{i}") for i in range(4)]
        ev = analyze_cluster_listing_history(active, [], total_cluster_lots=5)
        assert ev.partial_release_detected is False

    def test_small_cluster_not_detected(self):
        """Under 5 lots, partial release is not flagged."""
        active = [_listing(listing_key="L-1")]
        ev = analyze_cluster_listing_history(active, [], total_cluster_lots=4)
        assert ev.partial_release_detected is False


class TestFailedExitDetection:
    def test_expired_history_detected(self):
        hist = [_listing(listing_key="L-1", standard_status=StandardStatus.EXPIRED)]
        ev = analyze_cluster_listing_history([], hist, total_cluster_lots=5)
        assert ev.has_expired_history is True
        assert ev.expired_listings == 1

    def test_withdrawn_history_detected(self):
        hist = [_listing(listing_key="L-1", standard_status=StandardStatus.WITHDRAWN)]
        ev = analyze_cluster_listing_history([], hist, total_cluster_lots=5)
        assert ev.has_withdrawn_history is True
        assert ev.withdrawn_listings == 1


class TestRelistCycles:
    def test_same_key_different_statuses_detected(self):
        """Same listing_key with active + expired = relist cycle."""
        active = [_listing(listing_key="L-1", standard_status=StandardStatus.ACTIVE)]
        hist = [_listing(listing_key="L-1", standard_status=StandardStatus.EXPIRED)]
        ev = analyze_cluster_listing_history(active, hist, total_cluster_lots=5)
        assert ev.has_relist_cycle is True
        assert ev.repeated_listing_cycles >= 1


class TestRemarksScanning:
    def test_public_remarks_scanned(self):
        """remarks_raw (public) should be scanned for signals."""
        active = [_listing(
            listing_key="L-1",
            remarks_raw="package deal, all remaining lots available",
        )]
        ev = analyze_cluster_listing_history(active, [], total_cluster_lots=5)
        assert ev.package_language_detected is True

    def test_distress_language_detected(self):
        active = [_listing(
            listing_key="L-1",
            private_remarks="estate sale, selling as-is",
        )]
        ev = analyze_cluster_listing_history(active, [], total_cluster_lots=5)
        assert ev.distress_language_detected is True

    def test_infrastructure_ready_detected(self):
        active = [_listing(
            listing_key="L-1",
            remarks_raw="paved road, city water and city sewer",
        )]
        ev = analyze_cluster_listing_history(active, [], total_cluster_lots=5)
        assert ev.infrastructure_ready_detected is True

    def test_development_ready_detected(self):
        active = [_listing(
            listing_key="L-1",
            remarks_raw="site plan approved, ready to build",
        )]
        ev = analyze_cluster_listing_history(active, [], total_cluster_lots=5)
        assert ev.development_ready_detected is True


class TestCompositeScore:
    def test_empty_evidence_scores_zero(self):
        ev = analyze_cluster_listing_history([], [], total_cluster_lots=5)
        assert ev.history_signal_score == 0.0

    def test_multiple_signals_compound(self):
        """Partial release + expired history + distress = high score."""
        active = [_listing(listing_key="L-1")]
        hist = [
            _listing(listing_key="L-2", standard_status=StandardStatus.EXPIRED,
                     private_remarks="estate sale, must close"),
        ]
        ev = analyze_cluster_listing_history(active, hist, total_cluster_lots=10)
        # partial_release(0.20) + expired(0.18) + distress(0.15) + fatigue(0.10) = 0.63
        assert ev.history_signal_score >= 0.5

    def test_score_capped_at_one(self):
        """Score should never exceed 1.0 even with all signals."""
        active = [_listing(listing_key="L-1", cdom=365,
                           remarks_raw="package deal, paved road, site plan approved")]
        hist = [
            _listing(listing_key="L-1", standard_status=StandardStatus.EXPIRED,
                     private_remarks="estate sale as-is, must sell, price reduced",
                     previous_list_price=100000, list_price=75000),
        ]
        ev = analyze_cluster_listing_history(active, hist, total_cluster_lots=20)
        assert ev.history_signal_score <= 1.0
