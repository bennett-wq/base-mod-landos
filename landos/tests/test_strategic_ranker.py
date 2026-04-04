"""Tests for StrategicOpportunityRanker — the product feature.

Covers:
  - Basic ranking from parcel clusters
  - group_key-based stall assessment matching (the pipeline bridge)
  - Score computation with real stall evidence
  - Infrastructure flag propagation
  - min_lots filtering
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

import pytest

from src.adapters.stallout.detector import StallAssessment
from src.models.development import Subdivision
from src.models.enums import VacancyStatus
from src.models.parcel import Parcel
from src.scoring.strategic_ranker import (
    StrategicOpportunity,
    rank_from_pipeline,
    score_opportunity,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

MUNI_ID = uuid4()


@dataclass
class FakeParcelClusterResult:
    """Minimal ParcelClusterResult for testing."""
    cluster_type: str
    group_key: str
    parcels: list = field(default_factory=list)
    matched_listings: list = field(default_factory=list)
    total_acreage: float = 0.0

    @property
    def parcel_count(self) -> int:
        return len(self.parcels)


def _make_parcel(vacancy: VacancyStatus = VacancyStatus.VACANT, acreage: float = 0.5) -> Parcel:
    return Parcel(
        source_system_ids={"regrid_id": str(uuid4())},
        jurisdiction_state="MI",
        apn_or_parcel_number=f"APN-{uuid4().hex[:8]}",
        municipality_id=MUNI_ID,
        county="Washtenaw",
        state="MI",
        vacancy_status=vacancy,
        acreage=acreage,
    )


def _make_subdivision_cluster(
    name: str, total: int, vacant: int, acreage: float = 10.0
) -> FakeParcelClusterResult:
    parcels = []
    for i in range(total):
        status = VacancyStatus.VACANT if i < vacant else VacancyStatus.IMPROVED
        parcels.append(_make_parcel(status, acreage / total))
    return FakeParcelClusterResult(
        cluster_type="subdivision",
        group_key=name,
        parcels=parcels,
        total_acreage=acreage,
    )


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestScoreComputation:
    def test_score_with_all_zeros(self):
        opp = StrategicOpportunity(
            opportunity_id="test-1",
            name="Empty",
            opportunity_type="owner_cluster",
        )
        score_opportunity(opp)
        # lot_count=0 → 0.1 * 0.14 = 0.014
        assert opp.composite_score == pytest.approx(0.014, abs=0.01)

    def test_score_with_infrastructure_and_vacancy(self):
        opp = StrategicOpportunity(
            opportunity_id="test-2",
            name="Good target",
            opportunity_type="stalled_subdivision",
            lot_count=10,
            infrastructure_invested=True,
            vacancy_ratio=0.8,
            stall_confidence=0.6,
            has_active_listings=True,
        )
        score_opportunity(opp)
        # Should be a decent score even without seller intent
        assert opp.composite_score > 0.35
        assert opp.score_breakdown["infrastructure"] == 1.0
        assert opp.score_breakdown["stall_confidence"] == 0.6
        assert opp.score_breakdown["listing_activity"] == 1.0

    def test_seller_intent_boosts_score(self):
        """Distress + fatigue + relist = strong seller intent signal."""
        opp = StrategicOpportunity(
            opportunity_id="test-3",
            name="Motivated seller",
            opportunity_type="stalled_subdivision",
            lot_count=10,
            infrastructure_invested=True,
            vacancy_ratio=0.8,
            stall_confidence=0.6,
            has_active_listings=True,
            distress_language_detected=True,
            fatigue_language_detected=True,
            has_relist_cycle=True,
            expired_listing_count=2,
        )
        score_opportunity(opp)
        # Seller intent should push this above 0.5
        assert opp.composite_score > 0.5
        assert opp.score_breakdown["seller_intent"] > 0.6

    def test_infrastructure_ready_from_remarks(self):
        """Infrastructure mentioned in remarks (not from plat) gives partial score."""
        opp = StrategicOpportunity(
            opportunity_id="test-4",
            name="Infra in remarks",
            opportunity_type="owner_cluster",
            lot_count=5,
            infrastructure_invested=False,
            infrastructure_ready_detected=True,
        )
        score_opportunity(opp)
        assert opp.score_breakdown["infrastructure"] == 0.4  # remarks-only, no structured BBO data


class TestRankFromPipeline:
    def test_empty_clusters(self):
        result = rank_from_pipeline([], {}, {})
        assert result == []

    def test_min_lots_filter(self):
        cluster = _make_subdivision_cluster("small sub", total=3, vacant=3)
        result = rank_from_pipeline([cluster], {}, {}, min_lots=5)
        assert len(result) == 0

        result = rank_from_pipeline([cluster], {}, {}, min_lots=1)
        assert len(result) == 1

    def test_basic_ranking_without_stall(self):
        c1 = _make_subdivision_cluster("big", total=20, vacant=18, acreage=50.0)
        c2 = _make_subdivision_cluster("small", total=5, vacant=3, acreage=5.0)
        result = rank_from_pipeline([c1, c2], {}, {})
        assert len(result) == 2
        # Bigger cluster with more vacancy should score higher
        assert result[0].name == "big"
        assert result[0].lot_count == 20
        assert result[0].composite_score > result[1].composite_score


class TestGroupKeyStallMatching:
    """Tests the critical bridge: matching stall assessments to clusters by group_key."""

    def test_stall_assessment_applied_via_group_key(self):
        cluster = _make_subdivision_cluster("willow creek", total=10, vacant=8)
        stall = StallAssessment(
            is_stalled=True,
            stall_signals=["high_vacancy", "roads_installed", "no_recent_activity"],
            stall_confidence=0.60,
            vacancy_ratio=0.80,
            infrastructure_invested=True,
        )
        sub = Subdivision(
            name="willow creek",
            municipality_id=MUNI_ID,
            county="Washtenaw",
            state="MI",
            total_lots=10,
            vacant_lots=8,
        )

        result = rank_from_pipeline(
            parcel_clusters=[cluster],
            stall_assessments={},
            subdivisions={},
            stall_by_group_key={"willow creek": stall},
            subdivisions_by_group_key={"willow creek": sub},
        )

        assert len(result) == 1
        opp = result[0]
        assert opp.opportunity_type == "stalled_subdivision"
        assert opp.infrastructure_invested is True
        assert opp.stall_confidence == 0.60
        assert opp.stall_signals == ["high_vacancy", "roads_installed", "no_recent_activity"]
        assert opp.composite_score > 0.35  # Strong without seller intent; seller intent pushes higher

    def test_infrastructure_flag_flows_to_api_model(self):
        """Verify infrastructure_invested=True makes it through asdict() for SQLite."""
        from dataclasses import asdict

        cluster = _make_subdivision_cluster("oak ridge", total=6, vacant=5)
        stall = StallAssessment(
            is_stalled=True,
            stall_signals=["high_vacancy", "roads_installed", "no_recent_activity"],
            stall_confidence=0.60,
            vacancy_ratio=0.83,
            infrastructure_invested=True,
        )

        result = rank_from_pipeline(
            parcel_clusters=[cluster],
            stall_assessments={},
            subdivisions={},
            stall_by_group_key={"oak ridge": stall},
            subdivisions_by_group_key={},
        )

        d = asdict(result[0])
        assert d["infrastructure_invested"] is True
        assert d["stall_confidence"] == 0.60
        assert d["stall_signals"] == ["high_vacancy", "roads_installed", "no_recent_activity"]
        assert d["composite_score"] > 0

    def test_no_stall_assessment_gives_zero_stall(self):
        """Clusters without stall data should still rank, just with stall=0."""
        cluster = FakeParcelClusterResult(
            cluster_type="owner",
            group_key="john smith",
            parcels=[_make_parcel() for _ in range(7)],
            total_acreage=15.0,
        )

        result = rank_from_pipeline([cluster], {}, {})
        assert len(result) == 1
        opp = result[0]
        assert opp.infrastructure_invested is False
        assert opp.stall_confidence == 0.0
        assert opp.stall_signals == []
        assert opp.composite_score > 0  # Still ranked on other signals

    def test_subdivision_id_matching_takes_precedence(self):
        """If parcel.subdivision_id matches, use that over group_key."""
        sub_id = uuid4()
        parcels = [_make_parcel() for _ in range(5)]
        for p in parcels:
            p.subdivision_id = sub_id

        cluster = FakeParcelClusterResult(
            cluster_type="subdivision",
            group_key="maple estates",
            parcels=parcels,
            total_acreage=10.0,
        )

        # stall via subdivision_id (higher confidence)
        stall_by_id = StallAssessment(
            is_stalled=True,
            stall_signals=["high_vacancy", "roads_installed", "no_recent_activity", "plat_age"],
            stall_confidence=0.80,
            vacancy_ratio=1.0,
            infrastructure_invested=True,
        )
        sub_by_id = Subdivision(
            subdivision_id=sub_id,
            name="Maple Estates",
            municipality_id=MUNI_ID,
            county="Washtenaw",
            state="MI",
        )

        # stall via group_key (lower confidence)
        stall_by_gk = StallAssessment(
            is_stalled=False,
            stall_signals=["high_vacancy"],
            stall_confidence=0.25,
            vacancy_ratio=1.0,
            infrastructure_invested=False,
        )

        result = rank_from_pipeline(
            parcel_clusters=[cluster],
            stall_assessments={str(sub_id): stall_by_id},
            subdivisions={str(sub_id): sub_by_id},
            stall_by_group_key={"maple estates": stall_by_gk},
            subdivisions_by_group_key={},
        )

        assert len(result) == 1
        opp = result[0]
        # Should use the subdivision_id match (0.80), not group_key (0.25)
        assert opp.stall_confidence == 0.80
        assert opp.infrastructure_invested is True
