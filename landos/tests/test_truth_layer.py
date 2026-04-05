"""Tests for the truth layer fixes:
  - Subdivision canonicalization
  - Subdivision total-lot aggregation
  - Stall assessment persistence
  - Rerun stability (deterministic IDs)
  - Stats API truth
"""

from __future__ import annotations

import sqlite3
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from src.utils.subdivision_canon import canonicalize_subdivision
from src.adapters.cluster.parcel_cluster_detector import _extract_subdivision
from src.stores.sqlite_store import SQLiteStore
from src.models.development import Subdivision
from src.models.enums import InfrastructureStatus, StandardStatus
from src.models.listing import Listing


# ── Canonicalization tests ────────────────────────────────────────────────

class TestSubdivisionCanonicalization:
    def test_basic_lowercasing(self):
        assert canonicalize_subdivision("Smith Acres") == "smith acres"

    def test_whitespace_collapse(self):
        assert canonicalize_subdivision("  smith   acres  ") == "smith acres"

    def test_trailing_punctuation(self):
        assert canonicalize_subdivision("smith acres.") == "smith acres"
        assert canonicalize_subdivision("smith acres,") == "smith acres"

    def test_possessive_variants_collapse(self):
        # "co.'s" → "co"
        assert canonicalize_subdivision("lincoln realty co.'s horseshoe lake") == "lincoln realty co horseshoe lake"
        # "co's" → "co"
        assert canonicalize_subdivision("lincoln realty co's horseshoe lake") == "lincoln realty co horseshoe lake"
        # "co.," → "co"
        assert canonicalize_subdivision("lincoln realty co., horseshoe lake") == "lincoln realty co horseshoe lake"

    def test_summerhomes_variant(self):
        assert canonicalize_subdivision("whitmore lake summerhomes") == "whitmore lake summer homes"
        assert canonicalize_subdivision("whitmore lake summer homes") == "whitmore lake summer homes"

    def test_trailing_sub_stripped(self):
        assert canonicalize_subdivision("smith acres sub") == "smith acres"
        assert canonicalize_subdivision("smith acres subdivision") == "smith acres"

    def test_municipality_false_positive_rejected(self):
        assert canonicalize_subdivision("ann arbor") is None
        assert canonicalize_subdivision("Ann Arbor") is None
        assert canonicalize_subdivision("ypsilanti") is None
        assert canonicalize_subdivision("saline") is None
        assert canonicalize_subdivision("chelsea") is None

    def test_municipality_with_qualifier_allowed(self):
        # "ann arbor hills" is a real subdivision, not a bare municipality name
        assert canonicalize_subdivision("ann arbor hills") == "ann arbor hills"

    def test_too_short_rejected(self):
        assert canonicalize_subdivision("ab") is None
        assert canonicalize_subdivision("") is None

    def test_none_input(self):
        assert canonicalize_subdivision(None) is None


class TestExtractSubdivisionCanonicalized:
    """Ensure _extract_subdivision uses shared canonicalization."""

    def test_basic_extraction(self):
        result = _extract_subdivision("LOT 5 SMITH ACRES SUB")
        assert result == "smith acres"

    def test_plat_of_pattern(self):
        result = _extract_subdivision("PLAT OF DEVONSHIRE LOT 10")
        assert result == "devonshire"

    def test_municipality_false_positive(self):
        # A bare city name should be rejected
        result = _extract_subdivision("LOT 5 ANN ARBOR SUB")
        assert result is None

    def test_variant_collapse(self):
        r1 = _extract_subdivision("LOT 5 LINCOLN REALTY CO.'S HORSESHOE LAKE SUB")
        r2 = _extract_subdivision("LOT 3 LINCOLN REALTY CO'S HORSESHOE LAKE SUBDIVISION")
        assert r1 == r2
        assert r1 is not None


# ── Stall persistence tests ──────────────────────────────────────────────

class TestStallPersistence:
    def _make_store(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        return SQLiteStore(db_path=tmp.name)

    def test_stall_flag_persisted(self):
        store = self._make_store()
        sub = Subdivision(
            subdivision_id=UUID("12345678-1234-1234-1234-123456789abc"),
            name="test acres",
            municipality_id=UUID("00000000-0000-0000-0000-000000000001"),
            county="Washtenaw",
            state="MI",
            total_lots=20,
            vacant_lots=15,
            vacancy_ratio=0.75,
            infrastructure_status=InfrastructureStatus.ROADS_INSTALLED,
            stall_flag=True,
            stall_score=0.6,
            stall_score_version="v1_plat_inference",
            stall_detected_at=datetime(2026, 4, 4, tzinfo=timezone.utc),
        )
        store.save_subdivisions_batch([sub])

        # Query back
        row = store._conn.execute(
            "SELECT stall_flag, stall_score, vacancy_ratio FROM subdivisions WHERE subdivision_id = ?",
            (str(sub.subdivision_id),),
        ).fetchone()
        assert row["stall_flag"] == 1
        assert row["stall_score"] == 0.6
        assert row["vacancy_ratio"] == 0.75

    def test_not_stalled_flag_persisted(self):
        store = self._make_store()
        sub = Subdivision(
            subdivision_id=UUID("12345678-1234-1234-1234-123456789abc"),
            name="healthy acres",
            municipality_id=UUID("00000000-0000-0000-0000-000000000001"),
            county="Washtenaw",
            state="MI",
            total_lots=50,
            vacant_lots=5,
            vacancy_ratio=0.1,
            infrastructure_status=InfrastructureStatus.ROADS_INSTALLED,
            stall_flag=False,
            stall_score=0.2,
        )
        store.save_subdivisions_batch([sub])

        row = store._conn.execute(
            "SELECT stall_flag, stall_score, vacancy_ratio FROM subdivisions WHERE subdivision_id = ?",
            (str(sub.subdivision_id),),
        ).fetchone()
        assert row["stall_flag"] == 0
        assert row["stall_score"] == 0.2
        assert row["vacancy_ratio"] == 0.1


# ── Pipeline reset tests ─────────────────────────────────────────────────

class TestPipelineReset:
    def _make_store(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        return SQLiteStore(db_path=tmp.name)

    def test_reset_clears_current_state(self):
        store = self._make_store()
        # Insert some data
        store._conn.execute(
            "INSERT INTO pipeline_stats (stat_key, stat_value, updated_at) VALUES ('test', '1', '2026-01-01')"
        )
        store._conn.execute(
            "INSERT INTO strategic_opportunities (opportunity_id, name, data_json, updated_at) VALUES ('opp1', 'test', '{}', '2026-01-01')"
        )
        store._conn.commit()

        assert store._conn.execute("SELECT COUNT(*) FROM pipeline_stats").fetchone()[0] == 1
        assert store._conn.execute("SELECT COUNT(*) FROM strategic_opportunities").fetchone()[0] == 1

        store.reset_current_state()

        assert store._conn.execute("SELECT COUNT(*) FROM pipeline_stats").fetchone()[0] == 0
        assert store._conn.execute("SELECT COUNT(*) FROM strategic_opportunities").fetchone()[0] == 0

    def test_reset_preserves_listing_history(self):
        store = self._make_store()
        store._conn.execute(
            "INSERT INTO listing_history (listing_key, snapshot_status, data_json, ingested_at) VALUES ('lk1', 'Active', '{}', '2026-01-01')"
        )
        store._conn.commit()

        store.reset_current_state()

        count = store._conn.execute("SELECT COUNT(*) FROM listing_history").fetchone()[0]
        assert count == 1, "listing_history must survive reset"

    def test_listing_history_dedupes_within_run_only(self):
        store = self._make_store()
        listing = Listing(
            source_system="spark_rets",
            listing_key="lk1",
            standard_status=StandardStatus.EXPIRED,
            list_price=100000,
            property_type="Land",
        )

        store.save_listing_history_batch([listing, listing], run_id="run-1")
        count = store._conn.execute("SELECT COUNT(*) FROM listing_history").fetchone()[0]
        assert count == 1

        store.save_listing_history_batch([listing], run_id="run-2")
        count = store._conn.execute("SELECT COUNT(*) FROM listing_history").fetchone()[0]
        assert count == 2

    def test_listing_history_persists_owner_name_raw(self):
        store = self._make_store()
        listing = Listing(
            source_system="spark_rets",
            listing_key="lk-owner",
            standard_status=StandardStatus.EXPIRED,
            list_price=120000,
            property_type="Land",
            owner_name_raw="Cook Jennifer L",
        )

        store.save_listing_history(listing, run_id="run-owner")
        row = store._conn.execute(
            "SELECT owner_name_raw FROM listing_history WHERE listing_key = ?",
            ("lk-owner",),
        ).fetchone()
        assert row["owner_name_raw"] == "Cook Jennifer L"


# ── Rerun stability tests ────────────────────────────────────────────────

class TestRerunStability:
    def test_deterministic_subdivision_id(self):
        """Same canonical name should always produce the same UUID."""
        ns = uuid.UUID("b2c3d4e5-f6a7-8901-bcde-f12345678901")
        id1 = uuid.uuid5(ns, "devonshire")
        id2 = uuid.uuid5(ns, "devonshire")
        assert id1 == id2

    def test_different_names_different_ids(self):
        ns = uuid.UUID("b2c3d4e5-f6a7-8901-bcde-f12345678901")
        id1 = uuid.uuid5(ns, "devonshire")
        id2 = uuid.uuid5(ns, "watsonia park")
        assert id1 != id2

    def test_canonicalization_produces_stable_ids(self):
        """Variant names should canonicalize to the same key → same ID."""
        ns = uuid.UUID("b2c3d4e5-f6a7-8901-bcde-f12345678901")
        k1 = canonicalize_subdivision("WHITMORE LAKE SUMMERHOMES")
        k2 = canonicalize_subdivision("whitmore lake summer homes")
        assert k1 == k2
        assert uuid.uuid5(ns, k1) == uuid.uuid5(ns, k2)


# ── Stats truth tests ────────────────────────────────────────────────────

class TestStatsTruth:
    def test_strategic_opportunity_count(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        store = SQLiteStore(db_path=tmp.name)

        # Insert strategic opportunities
        for i in range(5):
            store.save_strategic_opportunity({
                "opportunity_id": f"opp-{i}",
                "name": f"test-{i}",
                "data_json": "{}",
            })
        store.commit()

        assert store.get_strategic_opportunity_count() == 5
        # The old get_opportunity_count should be 0 (nothing in opportunities table)
        assert store.get_opportunity_count() == 0

    def test_strategic_query_orders_tier_before_score(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        store = SQLiteStore(db_path=tmp.name)

        store.save_strategic_opportunity({
            "opportunity_id": "tier-4-high",
            "name": "tier-4-high",
            "precedence_tier": 4,
            "composite_score": 0.99,
        })
        store.save_strategic_opportunity({
            "opportunity_id": "tier-1-mid",
            "name": "tier-1-mid",
            "precedence_tier": 1,
            "composite_score": 0.40,
        })

        opps = store.get_strategic_opportunities(limit=10)
        assert opps[0]["opportunity_id"] == "tier-1-mid"
