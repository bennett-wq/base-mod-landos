"""Step 6 acceptance tests — Cluster Detection.

Coverage:
  InMemoryClusterStore        (2 tests)
  Owner cluster detection     (4 tests)
  Owner cluster events        (3 tests)
  Agent cluster detection     (4 tests)
  Office cluster detection    (4 tests)
  Cluster trigger integration (4 tests)
  Deterministic identity      (2 tests)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


from src.adapters.cluster.detector import (
    AGENT_THRESHOLD,
    CLUSTER_SIZE_THRESHOLD,
    OFFICE_THRESHOLD,
    OWNER_CLUSTER_EMIT,
    ClusterDetector,
    _deterministic_cluster_id,
)
from src.adapters.cluster.store import InMemoryClusterStore
from src.models.enums import ClusterType, StandardStatus
from src.models.listing import Listing
from src.triggers.context import TriggerContext
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.engine import TriggerEngine
from src.triggers.enums import PhaseGate
from src.triggers.rules import ALL_RULES

_FIXED_TS = datetime(2026, 3, 9, 14, 0, 0, tzinfo=timezone.utc)


# ── Shared helpers ─────────────────────────────────────────────────────────

def _listing(**kwargs) -> Listing:
    base = dict(
        source_system="cluster_detector",
        listing_key="CL-001",
        standard_status=StandardStatus.ACTIVE,
        list_price=85000,
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


def _detector(engine=None, ctx=None, store=None) -> ClusterDetector:
    return ClusterDetector(
        engine=engine if engine is not None else _engine(),
        context=ctx if ctx is not None else _ctx(),
        cluster_store=store if store is not None else InMemoryClusterStore(),
    )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: InMemoryClusterStore
# ═══════════════════════════════════════════════════════════════════════════

class TestInMemoryClusterStore:

    def test_upsert_and_get(self):
        from src.models.owner import OwnerCluster
        store = InMemoryClusterStore()
        cid = _deterministic_cluster_id(ClusterType.SAME_OWNER, "owner-key-test")
        cluster = OwnerCluster(
            cluster_id=cid,
            cluster_type=ClusterType.SAME_OWNER,
            detection_method="owner_id_match",
            member_count=2,
        )
        store.upsert(cluster)
        result = store.get(cid)
        assert result is not None
        assert result.cluster_id == cid
        assert result.member_count == 2

    def test_all_returns_all_clusters(self):
        from src.models.owner import OwnerCluster
        store = InMemoryClusterStore()
        ids = [
            _deterministic_cluster_id(ClusterType.SAME_OWNER, f"k-{i}")
            for i in range(3)
        ]
        for i, cid in enumerate(ids):
            store.upsert(OwnerCluster(
                cluster_id=cid,
                cluster_type=ClusterType.SAME_OWNER,
                detection_method="owner_id_match",
                member_count=i + 2,
            ))
        assert len(store.all()) == 3
        assert len(store) == 3


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: Owner cluster detection
# ═══════════════════════════════════════════════════════════════════════════

class TestOwnerClusterDetection:

    def test_two_listings_same_owner_id_form_cluster(self):
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(2)
        ]
        store = InMemoryClusterStore()
        det = _detector(store=store)
        det.scan_listings(listings, now=_FIXED_TS)
        assert len(store) == 1
        cluster = store.all()[0]
        assert cluster.cluster_type == ClusterType.SAME_OWNER
        assert cluster.member_count == 2
        assert cluster.detection_method == "owner_id_match"

    def test_seller_name_normalization_groups_same_owner(self):
        """Different capitalizations of same name are grouped together."""
        listings = [
            _listing(listing_key="L-0", seller_name_raw="John Smith"),
            _listing(listing_key="L-1", seller_name_raw="  JOHN  SMITH  "),
        ]
        store = InMemoryClusterStore()
        det = _detector(store=store)
        det.scan_listings(listings, now=_FIXED_TS)
        assert len(store) == 1
        cluster = store.all()[0]
        assert cluster.detection_method == "name_normalized_match"
        assert cluster.member_count == 2

    def test_single_listing_no_cluster(self):
        owner_id = uuid4()
        listings = [_listing(listing_key="L-0", owner_id=owner_id)]
        store = InMemoryClusterStore()
        det = _detector(store=store)
        det.scan_listings(listings, now=_FIXED_TS)
        assert len(store) == 0

    def test_none_owner_no_seller_name_no_cluster(self):
        listings = [_listing(listing_key=f"L-{i}") for i in range(3)]
        store = InMemoryClusterStore()
        det = _detector(store=store)
        det.scan_listings(listings, now=_FIXED_TS)
        assert len(store) == 0


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: Owner cluster events
# ═══════════════════════════════════════════════════════════════════════════

class TestOwnerClusterEvents:

    def test_same_owner_listing_detected_event_emitted(self):
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(2)
        ]
        results = _detector().scan_listings(listings, now=_FIXED_TS)
        event_types = [r.event_type for r in results]
        assert "same_owner_listing_detected" in event_types

    def test_owner_cluster_detected_emitted_at_threshold_3(self):
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(OWNER_CLUSTER_EMIT)  # exactly 3
        ]
        results = _detector().scan_listings(listings, now=_FIXED_TS)
        event_types = [r.event_type for r in results]
        assert "owner_cluster_detected" in event_types

    def test_cluster_size_threshold_crossed_at_5(self):
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(CLUSTER_SIZE_THRESHOLD)  # exactly 5
        ]
        results = _detector().scan_listings(listings, now=_FIXED_TS)
        event_types = [r.event_type for r in results]
        assert "owner_cluster_size_threshold_crossed" in event_types

    def test_two_listings_does_not_emit_owner_cluster_detected(self):
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(2)
        ]
        results = _detector().scan_listings(listings, now=_FIXED_TS)
        event_types = [r.event_type for r in results]
        assert "owner_cluster_detected" not in event_types
        assert "owner_cluster_size_threshold_crossed" not in event_types


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: Agent cluster detection
# ═══════════════════════════════════════════════════════════════════════════

class TestAgentClusterDetection:

    def test_three_listings_same_agent_detected(self):
        listings = [
            _listing(listing_key=f"L-{i}", list_agent_key="AGT-CLUSTER-01")
            for i in range(AGENT_THRESHOLD)
        ]
        store = InMemoryClusterStore()
        det = _detector(store=store)
        det.scan_listings(listings, now=_FIXED_TS)
        assert len(store) == 1
        cluster = store.all()[0]
        assert cluster.cluster_type == ClusterType.SAME_AGENT
        assert cluster.agent_program_flag is True

    def test_two_listings_same_agent_below_threshold(self):
        listings = [
            _listing(listing_key=f"L-{i}", list_agent_key="AGT-CLUSTER-02")
            for i in range(2)
        ]
        store = InMemoryClusterStore()
        det = _detector(store=store)
        det.scan_listings(listings, now=_FIXED_TS)
        # SAME_AGENT requires 3 — nothing stored
        agent_clusters = [c for c in store.all() if c.cluster_type == ClusterType.SAME_AGENT]
        assert len(agent_clusters) == 0

    def test_none_list_agent_key_not_detected(self):
        listings = [_listing(listing_key=f"L-{i}", list_agent_key=None) for i in range(5)]
        store = InMemoryClusterStore()
        _detector(store=store).scan_listings(listings, now=_FIXED_TS)
        assert len(store) == 0

    def test_agent_subdivision_program_event_emitted(self):
        listings = [
            _listing(listing_key=f"L-{i}", list_agent_key="AGT-EVENT-01")
            for i in range(AGENT_THRESHOLD)
        ]
        results = _detector().scan_listings(listings, now=_FIXED_TS)
        event_types = [r.event_type for r in results]
        assert "agent_subdivision_program_detected" in event_types


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: Office cluster detection
# ═══════════════════════════════════════════════════════════════════════════

class TestOfficeClusterDetection:

    def test_five_listings_same_office_detected(self):
        listings = [
            _listing(listing_key=f"L-{i}", listing_office_id="OFF-CLUSTER-01")
            for i in range(OFFICE_THRESHOLD)
        ]
        store = InMemoryClusterStore()
        det = _detector(store=store)
        det.scan_listings(listings, now=_FIXED_TS)
        assert len(store) == 1
        cluster = store.all()[0]
        assert cluster.cluster_type == ClusterType.SAME_OFFICE
        assert cluster.office_program_flag is True

    def test_four_listings_same_office_below_threshold(self):
        listings = [
            _listing(listing_key=f"L-{i}", listing_office_id="OFF-CLUSTER-02")
            for i in range(4)
        ]
        store = InMemoryClusterStore()
        _detector(store=store).scan_listings(listings, now=_FIXED_TS)
        office_clusters = [c for c in store.all() if c.cluster_type == ClusterType.SAME_OFFICE]
        assert len(office_clusters) == 0

    def test_none_listing_office_id_not_detected(self):
        listings = [_listing(listing_key=f"L-{i}", listing_office_id=None) for i in range(6)]
        store = InMemoryClusterStore()
        _detector(store=store).scan_listings(listings, now=_FIXED_TS)
        assert len(store) == 0

    def test_office_inventory_program_event_emitted(self):
        listings = [
            _listing(listing_key=f"L-{i}", listing_office_id="OFF-EVENT-01")
            for i in range(OFFICE_THRESHOLD)
        ]
        results = _detector().scan_listings(listings, now=_FIXED_TS)
        event_types = [r.event_type for r in results]
        assert "office_inventory_program_detected" in event_types


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: Cluster trigger integration
# ═══════════════════════════════════════════════════════════════════════════

class TestClusterTriggerIntegration:

    def _wake_targets(self, results, event_type: str) -> list[str]:
        """Collect wake_targets from all wake instructions for a given event_type."""
        targets = []
        for r in results:
            if r.event_type == event_type:
                targets.extend(w.wake_target for w in r.wake_instructions)
        return targets

    def test_rc_fires_on_owner_cluster_detected_size_3(self):
        """RC: owner_cluster_detected (cluster_size >= 3) → municipal_intelligence_team."""
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(OWNER_CLUSTER_EMIT)  # 3
        ]
        results = _detector().scan_listings(listings, now=_FIXED_TS)
        targets = self._wake_targets(results, "owner_cluster_detected")
        assert "municipal_intelligence_team" in targets

    def test_ro_fires_on_owner_cluster_detected(self):
        """RO: owner_cluster_detected → spark_signal_agent."""
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(OWNER_CLUSTER_EMIT)  # 3
        ]
        results = _detector().scan_listings(listings, now=_FIXED_TS)
        targets = self._wake_targets(results, "owner_cluster_detected")
        assert "spark_signal_agent" in targets

    def test_rp_fires_on_same_owner_listing_detected(self):
        """RP: same_owner_listing_detected → spark_signal_agent."""
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(2)
        ]
        results = _detector().scan_listings(listings, now=_FIXED_TS)
        targets = self._wake_targets(results, "same_owner_listing_detected")
        assert "spark_signal_agent" in targets

    def test_ru_fires_on_cluster_size_threshold_crossed(self):
        """RU1/RU2: owner_cluster_size_threshold_crossed → opportunity_creation_agent + municipal_agent."""
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(CLUSTER_SIZE_THRESHOLD)  # 5
        ]
        results = _detector().scan_listings(listings, now=_FIXED_TS)
        targets = self._wake_targets(results, "owner_cluster_size_threshold_crossed")
        assert "opportunity_creation_agent" in targets
        assert "municipal_agent" in targets


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: Deterministic cluster identity
# ═══════════════════════════════════════════════════════════════════════════

class TestDeterministicClusterIdentity:

    def test_repeated_scan_same_group_reuses_same_cluster_id(self):
        """Two scans of the same logical owner group produce the same cluster_id."""
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(2)
        ]
        store = InMemoryClusterStore()
        det = _detector(store=store)

        det.scan_listings(listings, now=_FIXED_TS)
        first_id = store.all()[0].cluster_id

        # Second scan — fresh engine/cooldown so events route again, but same store
        det2 = ClusterDetector(
            engine=_engine(),
            context=_ctx(),
            cluster_store=store,
        )
        det2.scan_listings(listings, now=_FIXED_TS)
        second_id = store.all()[0].cluster_id

        assert first_id == second_id

    def test_store_length_does_not_increase_on_identical_rescan(self):
        """Re-scanning the same logical groups does not grow the store."""
        owner_id = uuid4()
        listings = [
            _listing(listing_key=f"L-{i}", owner_id=owner_id)
            for i in range(3)
        ]
        store = InMemoryClusterStore()
        det = _detector(store=store)

        det.scan_listings(listings, now=_FIXED_TS)
        count_after_first = len(store)

        det2 = ClusterDetector(
            engine=_engine(),
            context=_ctx(),
            cluster_store=store,
        )
        det2.scan_listings(listings, now=_FIXED_TS)
        count_after_second = len(store)

        assert count_after_first == count_after_second
