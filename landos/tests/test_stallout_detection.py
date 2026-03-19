"""Step 8 — Historical Stallout Detection tests.

Covers all 17 acceptance criteria (AC-1 through AC-17):

AC-1:  test_stall_assessment_strong_stall (Willow Creek)
AC-2:  test_stall_assessment_no_stall (Oak Ridge)
AC-3:  test_emit_historical_plat_stall
AC-4:  test_emit_historical_subdivision_stall
AC-5:  test_emit_roads_installed_majority_vacant
AC-6:  test_emit_permits_pulled_majority_vacant
AC-7:  test_emit_approved_no_vertical_progress
AC-8:  test_emit_bond_posted_no_progress
AC-9:  test_emit_partial_buildout_stagnation (Maple Estates)
AC-10: test_opportunity_created_on_stall
AC-11: test_no_opportunity_low_confidence
AC-12: test_trigger_routing_stallout_events (parametrized × 7 rules)
AC-13: test_cooldown_blocks_duplicate_stall
AC-14: test_subdivision_object_updated
AC-15: test_stores_crud
AC-16: Verified by running full test suite (289 existing tests)
AC-17: Verified by file existence (this file)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from src.adapters.municipal.store import InMemoryMunicipalEventStore
from src.adapters.stallout.detector import StallAssessment, detect_stall
from src.adapters.stallout.event_factory import build_stallout_events
from src.adapters.stallout.ingestion import scan_subdivisions_for_stalls
from src.adapters.stallout.opportunity_factory import create_stall_opportunity
from src.adapters.stallout.store import (
    InMemoryOpportunityStore,
    InMemorySubdivisionStore,
)
from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily, RoutingClass
from src.models.development import Subdivision
from src.models.enums import (
    InfrastructureStatus,
    MunicipalEventType,
    MunicipalityType,
    OpportunityStatus,
    OpportunityType,
    VacancyStatus,
)
from src.models.municipality import Municipality, MunicipalEvent
from src.models.opportunity import Opportunity
from src.models.parcel import Parcel
from src.triggers.context import TriggerContext
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.engine import TriggerEngine
from src.triggers.rules import ALL_RULES


# ── Constants ──────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 3, 19, 12, 0, 0, tzinfo=timezone.utc)
_MUNI_ID = uuid4()


# ── Fixture helpers ────────────────────────────────────────────────────────────

def _make_parcel(
    subdivision_id: UUID,
    municipality_id: UUID = _MUNI_ID,
    vacancy_status: VacancyStatus = VacancyStatus.VACANT,
) -> Parcel:
    """Create a minimal Parcel for testing."""
    return Parcel(
        source_system_ids={"regrid_id": str(uuid4())},
        jurisdiction_state="MI",
        county="Washtenaw",
        municipality_id=municipality_id,
        apn_or_parcel_number=f"APN-{uuid4().hex[:8]}",
        acreage=0.25,
        vacancy_status=vacancy_status,
        subdivision_id=subdivision_id,
    )


def _make_municipal_event(
    event_type: MunicipalEventType,
    occurred_at: date | datetime,
    municipality_id: UUID = _MUNI_ID,
    subdivision_id: UUID | None = None,
    details: dict | None = None,
) -> MunicipalEvent:
    """Create a MunicipalEvent for testing."""
    occ = occurred_at
    if isinstance(occ, date) and not isinstance(occ, datetime):
        occ = datetime(occ.year, occ.month, occ.day, tzinfo=timezone.utc)
    return MunicipalEvent(
        municipality_id=municipality_id,
        event_type=event_type,
        occurred_at=occ,
        source_system="planning_commission_minutes",
        subdivision_id=subdivision_id,
        details=details,
    )


def _willow_creek() -> tuple[Subdivision, list[MunicipalEvent], list[Parcel]]:
    """Classic stall: plat 2018, 40 lots, 28 vacant (0.70), roads 2019,
    bond 2018, no activity after 2019. Expected: is_stalled=True, confidence >= 0.75."""
    sub_id = uuid4()
    subdivision = Subdivision(
        subdivision_id=sub_id,
        name="Willow Creek",
        municipality_id=_MUNI_ID,
        county="Washtenaw",
        state="MI",
        plat_date=date(2018, 6, 15),
        total_lots=40,
        vacant_lots=28,
        improved_lots=12,
    )

    events = [
        _make_municipal_event(
            MunicipalEventType.PLAT_RECORDED,
            date(2018, 6, 15),
            subdivision_id=sub_id,
            details={"plat_name": "Willow Creek", "total_lots": 40},
        ),
        _make_municipal_event(
            MunicipalEventType.BOND_POSTED,
            date(2018, 8, 1),
            subdivision_id=sub_id,
            details={"bond_amount": 250000, "bond_type": "performance"},
        ),
        _make_municipal_event(
            MunicipalEventType.ROADS_INSTALLED,
            date(2019, 5, 20),
            subdivision_id=sub_id,
            details={"road_names": ["Willow Creek Dr", "Oak Ln"]},
        ),
    ]

    parcels = (
        [_make_parcel(sub_id, vacancy_status=VacancyStatus.VACANT) for _ in range(28)]
        + [_make_parcel(sub_id, vacancy_status=VacancyStatus.IMPROVED) for _ in range(12)]
    )

    return subdivision, events, parcels


def _oak_ridge() -> tuple[Subdivision, list[MunicipalEvent], list[Parcel]]:
    """Healthy subdivision: plat 2024, 30 lots, 4 vacant (0.13), 26 improved.
    Expected: is_stalled=False."""
    sub_id = uuid4()
    subdivision = Subdivision(
        subdivision_id=sub_id,
        name="Oak Ridge",
        municipality_id=_MUNI_ID,
        county="Washtenaw",
        state="MI",
        plat_date=date(2024, 3, 1),
        total_lots=30,
        vacant_lots=4,
        improved_lots=26,
    )

    events = [
        _make_municipal_event(
            MunicipalEventType.PLAT_RECORDED,
            date(2024, 3, 1),
            subdivision_id=sub_id,
        ),
        _make_municipal_event(
            MunicipalEventType.ROADS_INSTALLED,
            date(2024, 6, 1),
            subdivision_id=sub_id,
        ),
        _make_municipal_event(
            MunicipalEventType.PERMIT_PULLED,
            date(2025, 12, 1),
            subdivision_id=sub_id,
        ),
    ]

    parcels = (
        [_make_parcel(sub_id, vacancy_status=VacancyStatus.VACANT) for _ in range(4)]
        + [_make_parcel(sub_id, vacancy_status=VacancyStatus.IMPROVED) for _ in range(26)]
    )

    return subdivision, events, parcels


def _maple_estates() -> tuple[Subdivision, list[MunicipalEvent], list[Parcel]]:
    """Partial buildout stall: plat 2020, 20 lots, 8 improved, 12 vacant,
    last permit 2022. Expected: partial_buildout_stagnation_detected emitted."""
    sub_id = uuid4()
    subdivision = Subdivision(
        subdivision_id=sub_id,
        name="Maple Estates",
        municipality_id=_MUNI_ID,
        county="Washtenaw",
        state="MI",
        plat_date=date(2020, 4, 10),
        total_lots=20,
        vacant_lots=12,
        improved_lots=8,
    )

    events = [
        _make_municipal_event(
            MunicipalEventType.PLAT_RECORDED,
            date(2020, 4, 10),
            subdivision_id=sub_id,
        ),
        _make_municipal_event(
            MunicipalEventType.ROADS_INSTALLED,
            date(2020, 9, 15),
            subdivision_id=sub_id,
        ),
        _make_municipal_event(
            MunicipalEventType.PERMIT_PULLED,
            date(2022, 2, 1),
            subdivision_id=sub_id,
        ),
    ]

    parcels = (
        [_make_parcel(sub_id, vacancy_status=VacancyStatus.VACANT) for _ in range(12)]
        + [_make_parcel(sub_id, vacancy_status=VacancyStatus.IMPROVED) for _ in range(8)]
    )

    return subdivision, events, parcels


def _engine_and_context(
    ts: datetime = _NOW,
) -> tuple[TriggerEngine, TriggerContext]:
    """Create TriggerEngine with ALL_RULES and a TriggerContext."""
    engine = TriggerEngine(
        rules=ALL_RULES,
        cooldown_tracker=InMemoryCooldownTracker(),
    )
    context = TriggerContext(current_timestamp=ts)
    return engine, context


# ── AC-1: StallAssessment computation (Willow Creek) ──────────────────────────


class TestStallAssessmentStrongStall:
    """AC-1: Willow Creek → is_stalled=True, confidence >= 0.75, correct signals."""

    def test_stall_assessment_strong_stall(self):
        subdivision, events, parcels = _willow_creek()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)

        assert assessment.is_stalled is True
        assert assessment.stall_confidence >= 0.75
        assert "plat_age" in assessment.stall_signals
        assert "high_vacancy" in assessment.stall_signals
        assert "roads_installed" in assessment.stall_signals
        assert "no_recent_activity" in assessment.stall_signals
        assert assessment.vacancy_ratio == pytest.approx(0.70, abs=0.01)
        assert assessment.infrastructure_invested is True
        assert assessment.years_since_plat is not None
        assert assessment.years_since_plat >= 7.0

    def test_bonds_posted_signal_present(self):
        subdivision, events, parcels = _willow_creek()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        assert "bonds_posted" in assessment.stall_signals

    def test_confidence_matches_weight_sum(self):
        """Confidence should equal the sum of weights for present signals."""
        subdivision, events, parcels = _willow_creek()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        # Willow Creek has: plat_age(0.20) + high_vacancy(0.25) + roads_installed(0.20)
        # + bonds_posted(0.10) + no_recent_activity(0.15) = 0.90
        assert assessment.stall_confidence == pytest.approx(0.90, abs=0.01)


# ── AC-2: Stall negative case (Oak Ridge) ─────────────────────────────────────


class TestStallAssessmentNoStall:
    """AC-2: Oak Ridge → is_stalled=False."""

    def test_stall_assessment_no_stall(self):
        subdivision, events, parcels = _oak_ridge()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)

        assert assessment.is_stalled is False
        assert assessment.vacancy_ratio == pytest.approx(0.133, abs=0.01)

    def test_low_vacancy_blocks_stall(self):
        """Even with roads + plat, low vacancy means no stall."""
        subdivision, events, parcels = _oak_ridge()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        assert "high_vacancy" not in assessment.stall_signals


# ── AC-3: Historical plat stall event ─────────────────────────────────────────


class TestEmitHistoricalPlatStall:
    """AC-3: plat >= 5 years + vacancy >= 0.4 → historical_plat_stall_detected."""

    def test_emit_historical_plat_stall(self):
        subdivision, events, parcels = _willow_creek()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)

        plat_events = [e for e in emitted if e.event_type == "historical_plat_stall_detected"]
        assert len(plat_events) == 1

        ev = plat_events[0]
        assert ev.event_class == EventClass.DERIVED
        assert ev.event_family == EventFamily.HISTORICAL_STALL
        assert ev.generation_depth == 1
        assert ev.emitted_by_agent_run_id is not None
        assert ev.derived_from_event_ids is not None
        assert len(ev.derived_from_event_ids) > 0
        assert ev.entity_refs.subdivision_id == subdivision.subdivision_id
        assert ev.entity_refs.municipality_id == subdivision.municipality_id

        # Verify payload per Event Library
        p = ev.payload
        assert p["plat_name"] == "Willow Creek"
        assert p["total_lots"] == 40
        assert p["vacant_lots"] == 28
        assert p["vacancy_ratio"] == pytest.approx(0.70, abs=0.01)
        assert p["years_since_plat"] >= 7.0

    def test_no_plat_stall_when_young(self):
        """Oak Ridge plat is 2 years old — no plat stall event."""
        subdivision, events, parcels = _oak_ridge()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)
        plat_events = [e for e in emitted if e.event_type == "historical_plat_stall_detected"]
        assert len(plat_events) == 0


# ── AC-4: Historical subdivision stall event ──────────────────────────────────


class TestEmitHistoricalSubdivisionStall:
    """AC-4: is_stalled=True → historical_subdivision_stall_detected."""

    def test_emit_historical_subdivision_stall(self):
        subdivision, events, parcels = _willow_creek()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)

        stall_events = [e for e in emitted if e.event_type == "historical_subdivision_stall_detected"]
        assert len(stall_events) == 1

        ev = stall_events[0]
        assert ev.event_class == EventClass.DERIVED
        assert ev.event_family == EventFamily.HISTORICAL_STALL
        p = ev.payload
        assert "stall_signals" in p
        assert "stall_confidence" in p
        assert p["stall_confidence"] >= 0.75

    def test_no_stall_event_when_not_stalled(self):
        subdivision, events, parcels = _oak_ridge()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)
        stall_events = [e for e in emitted if e.event_type == "historical_subdivision_stall_detected"]
        assert len(stall_events) == 0


# ── AC-5: Roads installed majority vacant event ──────────────────────────────


class TestEmitRoadsInstalledMajorityVacant:
    """AC-5: roads_installed + vacancy >= 0.5 → roads_installed_majority_vacant_detected."""

    def test_emit_roads_installed_majority_vacant(self):
        subdivision, events, parcels = _willow_creek()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)

        road_events = [e for e in emitted if e.event_type == "roads_installed_majority_vacant_detected"]
        assert len(road_events) == 1

        ev = road_events[0]
        assert ev.event_class == EventClass.DERIVED
        assert ev.event_family == EventFamily.MUNICIPAL_PROCESS
        p = ev.payload
        assert p["vacancy_ratio"] >= 0.5
        assert p["road_installation_date"] is not None

    def test_no_road_event_low_vacancy(self):
        """Oak Ridge has roads but vacancy is 0.13 — no road stall event."""
        subdivision, events, parcels = _oak_ridge()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)
        road_events = [e for e in emitted if e.event_type == "roads_installed_majority_vacant_detected"]
        assert len(road_events) == 0


# ── AC-6: Permits pulled majority vacant event ────────────────────────────────


class TestEmitPermitsPulledMajorityVacant:
    """AC-6: permit_pulled + vacancy >= 0.5 → permits_pulled_majority_vacant_detected."""

    def test_emit_permits_pulled_majority_vacant(self):
        """Create a subdivision with permits and high vacancy."""
        sub_id = uuid4()
        subdivision = Subdivision(
            subdivision_id=sub_id,
            name="Permit Stall Sub",
            municipality_id=_MUNI_ID,
            county="Washtenaw",
            state="MI",
            plat_date=date(2018, 1, 1),
            total_lots=20,
            vacant_lots=12,
            improved_lots=8,
        )
        events = [
            _make_municipal_event(MunicipalEventType.PLAT_RECORDED, date(2018, 1, 1), subdivision_id=sub_id),
            _make_municipal_event(MunicipalEventType.PERMIT_PULLED, date(2019, 3, 1), subdivision_id=sub_id),
            _make_municipal_event(MunicipalEventType.PERMIT_PULLED, date(2019, 6, 1), subdivision_id=sub_id),
        ]
        parcels = (
            [_make_parcel(sub_id, vacancy_status=VacancyStatus.VACANT) for _ in range(12)]
            + [_make_parcel(sub_id, vacancy_status=VacancyStatus.IMPROVED) for _ in range(8)]
        )

        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)

        permit_events = [e for e in emitted if e.event_type == "permits_pulled_majority_vacant_detected"]
        assert len(permit_events) == 1
        assert permit_events[0].payload["vacancy_ratio"] >= 0.5
        assert permit_events[0].payload["permitted_lots"] == 2


# ── AC-7: Approved no vertical progress event ─────────────────────────────────


class TestEmitApprovedNoVerticalProgress:
    """AC-7: approval event + no permits + years >= 3.0 → approved_no_vertical_progress_detected."""

    def test_emit_approved_no_vertical_progress(self):
        sub_id = uuid4()
        subdivision = Subdivision(
            subdivision_id=sub_id,
            name="Approval Only Sub",
            municipality_id=_MUNI_ID,
            county="Washtenaw",
            state="MI",
            plat_date=date(2020, 1, 1),
            total_lots=25,
            vacant_lots=20,
            improved_lots=0,
        )
        events = [
            _make_municipal_event(MunicipalEventType.SITE_PLAN_APPROVED, date(2020, 3, 1), subdivision_id=sub_id),
            _make_municipal_event(MunicipalEventType.ENGINEERING_APPROVED, date(2020, 6, 1), subdivision_id=sub_id),
        ]
        parcels = [_make_parcel(sub_id) for _ in range(25)]

        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)

        approved_events = [e for e in emitted if e.event_type == "approved_no_vertical_progress_detected"]
        assert len(approved_events) == 1

        ev = approved_events[0]
        assert ev.event_class == EventClass.DERIVED
        assert ev.event_family == EventFamily.MUNICIPAL_PROCESS
        assert ev.payload["years_since_approval"] >= 3.0
        assert ev.payload["vertical_progress_detected"] is False


# ── AC-8: Bond posted no progress event ───────────────────────────────────────


class TestEmitBondPostedNoProgress:
    """AC-8: bond_posted + no progress + years >= 3.0 → bond_posted_no_progress_detected."""

    def test_emit_bond_posted_no_progress(self):
        subdivision, events, parcels = _willow_creek()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)

        bond_events = [e for e in emitted if e.event_type == "bond_posted_no_progress_detected"]
        assert len(bond_events) == 1

        ev = bond_events[0]
        assert ev.event_class == EventClass.DERIVED
        assert ev.event_family == EventFamily.MUNICIPAL_PROCESS
        assert ev.payload["years_since_bond"] >= 3.0
        assert ev.payload["progress_indicators"] == []


# ── AC-9: Partial buildout stagnation event (Maple Estates) ───────────────────


class TestEmitPartialBuildoutStagnation:
    """AC-9: improved_lots > 0 AND vacant_lots > 0 AND years_since_last_build >= 3.0
    → partial_buildout_stagnation_detected (Maple Estates)."""

    def test_emit_partial_buildout_stagnation(self):
        subdivision, events, parcels = _maple_estates()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)

        stagnation_events = [e for e in emitted if e.event_type == "partial_buildout_stagnation_detected"]
        assert len(stagnation_events) == 1

        ev = stagnation_events[0]
        assert ev.event_class == EventClass.DERIVED
        assert ev.event_family == EventFamily.HISTORICAL_STALL
        p = ev.payload
        assert p["built_lots"] == 8
        assert p["vacant_lots"] == 12
        assert p["years_since_last_build"] >= 3.0

    def test_no_stagnation_when_recent_activity(self):
        """Oak Ridge has recent permits — no stagnation."""
        subdivision, events, parcels = _oak_ridge()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)
        stagnation_events = [e for e in emitted if e.event_type == "partial_buildout_stagnation_detected"]
        assert len(stagnation_events) == 0


# ── AC-10: Opportunity creation ───────────────────────────────────────────────


class TestOpportunityCreatedOnStall:
    """AC-10: stall_confidence >= 0.45 → Opportunity created."""

    def test_opportunity_created_on_stall(self):
        subdivision, events, parcels = _willow_creek()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)
        event_ids = [ev.event_id for ev in emitted]

        opp = create_stall_opportunity(assessment, subdivision, event_ids)

        assert opp is not None
        assert opp.opportunity_type == OpportunityType.STALLED_SUBDIVISION
        assert opp.municipality_id == subdivision.municipality_id
        assert opp.subdivision_id == subdivision.subdivision_id
        assert opp.status == OpportunityStatus.DETECTED
        assert opp.source_event_ids == event_ids
        assert opp.opportunity_score == pytest.approx(
            assessment.stall_confidence * 0.8, abs=0.01
        )

    def test_opportunity_has_parcel_ids(self):
        subdivision, events, parcels = _willow_creek()
        subdivision.parcel_ids = [p.parcel_id for p in parcels]
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        opp = create_stall_opportunity(assessment, subdivision, [uuid4()])
        assert opp is not None
        assert len(opp.parcel_ids) == 40


# ── AC-11: Opportunity not created for low confidence ─────────────────────────


class TestNoOpportunityLowConfidence:
    """AC-11: stall_confidence < 0.45 → no Opportunity."""

    def test_no_opportunity_low_confidence(self):
        subdivision, events, parcels = _oak_ridge()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)

        opp = create_stall_opportunity(assessment, subdivision, [uuid4()])
        assert opp is None

    def test_borderline_no_opportunity(self):
        """Test with confidence just below 0.45."""
        assessment = StallAssessment(
            is_stalled=False,
            stall_signals=["plat_age", "high_vacancy"],
            stall_confidence=0.44,
            vacancy_ratio=0.5,
            years_since_plat=6.0,
            years_since_last_activity=2.0,
            infrastructure_invested=False,
        )
        sub = Subdivision(
            name="Borderline Sub",
            municipality_id=_MUNI_ID,
            county="Washtenaw",
            state="MI",
        )
        opp = create_stall_opportunity(assessment, sub, [uuid4()])
        assert opp is None


# ── AC-12: Trigger routing — stallout events ──────────────────────────────────


class TestTriggerRoutingStalloutEvents:
    """AC-12: All 7 stallout events route correctly through trigger rules STA–STG."""

    @pytest.mark.parametrize(
        "event_type,expected_rule_prefix,payload_overrides",
        [
            (
                "historical_plat_stall_detected",
                "STA",
                {"vacancy_ratio": 0.7, "years_since_plat": 8.0},
            ),
            (
                "historical_subdivision_stall_detected",
                "STB",
                {"stall_confidence": 0.8},
            ),
            (
                "roads_installed_majority_vacant_detected",
                "STC",
                {"vacancy_ratio": 0.7},
            ),
            (
                "permits_pulled_majority_vacant_detected",
                "STD",
                {"vacancy_ratio": 0.6},
            ),
            (
                "approved_no_vertical_progress_detected",
                "STE",
                {"years_since_approval": 5.0},
            ),
            (
                "bond_posted_no_progress_detected",
                "STF",
                {"years_since_bond": 4.0},
            ),
            (
                "partial_buildout_stagnation_detected",
                "STG",
                {"years_since_last_build": 4.0},
            ),
        ],
    )
    def test_trigger_routing_stallout_events(
        self,
        event_type: str,
        expected_rule_prefix: str,
        payload_overrides: dict,
    ):
        engine, context = _engine_and_context()
        sub_id = uuid4()

        # Determine the event family
        if event_type in (
            "historical_plat_stall_detected",
            "historical_subdivision_stall_detected",
            "partial_buildout_stagnation_detected",
        ):
            event_family = EventFamily.HISTORICAL_STALL
        else:
            event_family = EventFamily.MUNICIPAL_PROCESS

        event = EventEnvelope(
            event_type=event_type,
            event_family=event_family,
            event_class=EventClass.DERIVED,
            occurred_at=_NOW,
            observed_at=_NOW,
            source_system="stallout_detection_agent",
            source_confidence=0.8,
            entity_refs=EntityRefs(
                subdivision_id=sub_id,
                municipality_id=_MUNI_ID,
            ),
            derived_from_event_ids=[uuid4()],
            emitted_by_agent_run_id=uuid4(),
            generation_depth=1,
            payload={
                "subdivision_id": str(sub_id),
                **payload_overrides,
            },
        )

        result = engine.evaluate(event, context)
        matched_rules = [
            r for r in result.fired_rules if r.startswith(expected_rule_prefix)
        ]
        assert len(matched_rules) >= 1, (
            f"Expected rule {expected_rule_prefix} to fire for {event_type}, "
            f"but fired_rules={result.fired_rules}"
        )


# ── AC-13: Cooldown enforcement ───────────────────────────────────────────────


class TestCooldownBlocksDuplicateStall:
    """AC-13: Second stall event for same subdivision within 30 days is blocked."""

    def test_cooldown_blocks_duplicate_stall(self):
        engine, context = _engine_and_context()
        sub_id = uuid4()

        def _make_stall_event():
            return EventEnvelope(
                event_type="historical_subdivision_stall_detected",
                event_family=EventFamily.HISTORICAL_STALL,
                event_class=EventClass.DERIVED,
                occurred_at=_NOW,
                observed_at=_NOW,
                source_system="stallout_detection_agent",
                source_confidence=0.8,
                entity_refs=EntityRefs(
                    subdivision_id=sub_id,
                    municipality_id=_MUNI_ID,
                ),
                derived_from_event_ids=[uuid4()],
                emitted_by_agent_run_id=uuid4(),
                generation_depth=1,
                payload={
                    "subdivision_id": str(sub_id),
                    "stall_confidence": 0.8,
                },
            )

        # First evaluation should fire
        result1 = engine.evaluate(_make_stall_event(), context)
        stb_fired_1 = [r for r in result1.fired_rules if r.startswith("STB")]
        assert len(stb_fired_1) == 1

        # Second evaluation within cooldown window should be blocked
        result2 = engine.evaluate(_make_stall_event(), context)
        stb_fired_2 = [r for r in result2.fired_rules if r.startswith("STB")]
        assert len(stb_fired_2) == 0

        # Verify it was suppressed by cooldown
        stb_suppressed = [
            s for s in result2.suppressed_rules if s.rule_id.startswith("STB")
        ]
        assert len(stb_suppressed) == 1
        assert stb_suppressed[0].outcome.value == "cooldown_blocked"


# ── AC-14: Subdivision object updated ─────────────────────────────────────────


class TestSubdivisionObjectUpdated:
    """AC-14: After scanning, Subdivision fields are updated."""

    def test_subdivision_object_updated(self):
        subdivision, events, parcels = _willow_creek()
        store = InMemoryMunicipalEventStore()
        for ev in events:
            store.save(ev)

        engine, context = _engine_and_context()
        parcels_map = {subdivision.subdivision_id: parcels}

        scan_subdivisions_for_stalls(
            [subdivision], store, parcels_map, engine, context, now=_NOW
        )

        assert subdivision.stall_flag is True
        assert subdivision.stall_score is not None
        assert subdivision.stall_score >= 0.75
        assert subdivision.vacancy_ratio == pytest.approx(0.70, abs=0.01)
        assert subdivision.infrastructure_status == InfrastructureStatus.ROADS_INSTALLED
        assert subdivision.years_since_plat is not None
        assert subdivision.years_since_plat >= 7.0
        assert subdivision.updated_at == _NOW

    def test_stall_detected_at_set_on_new_detection(self):
        subdivision, events, parcels = _willow_creek()
        assert subdivision.stall_detected_at is None

        store = InMemoryMunicipalEventStore()
        for ev in events:
            store.save(ev)

        engine, context = _engine_and_context()
        parcels_map = {subdivision.subdivision_id: parcels}

        scan_subdivisions_for_stalls(
            [subdivision], store, parcels_map, engine, context, now=_NOW
        )

        assert subdivision.stall_detected_at == _NOW

    def test_healthy_subdivision_not_flagged(self):
        subdivision, events, parcels = _oak_ridge()
        store = InMemoryMunicipalEventStore()
        for ev in events:
            store.save(ev)

        engine, context = _engine_and_context()
        parcels_map = {subdivision.subdivision_id: parcels}

        scan_subdivisions_for_stalls(
            [subdivision], store, parcels_map, engine, context, now=_NOW
        )

        assert subdivision.stall_flag is False
        assert subdivision.stall_score is not None
        assert subdivision.stall_score < 0.45


# ── AC-15: InMemory stores work ───────────────────────────────────────────────


class TestStoresCrud:
    """AC-15: SubdivisionStore and OpportunityStore CRUD operations."""

    def test_subdivision_store_save_and_get(self):
        store = InMemorySubdivisionStore()
        sub = Subdivision(
            name="Test Sub",
            municipality_id=_MUNI_ID,
            county="Washtenaw",
            state="MI",
        )
        store.save(sub)
        assert store.get(sub.subdivision_id) is not None
        assert store.get(sub.subdivision_id).name == "Test Sub"

    def test_subdivision_store_get_by_municipality(self):
        store = InMemorySubdivisionStore()
        muni1 = uuid4()
        muni2 = uuid4()
        s1 = Subdivision(name="Sub1", municipality_id=muni1, county="W", state="MI")
        s2 = Subdivision(name="Sub2", municipality_id=muni1, county="W", state="MI")
        s3 = Subdivision(name="Sub3", municipality_id=muni2, county="W", state="MI")
        store.save(s1)
        store.save(s2)
        store.save(s3)

        results = store.get_by_municipality(muni1)
        assert len(results) == 2
        assert all(s.municipality_id == muni1 for s in results)

    def test_subdivision_store_all_and_len(self):
        store = InMemorySubdivisionStore()
        for i in range(3):
            store.save(Subdivision(
                name=f"Sub{i}", municipality_id=_MUNI_ID, county="W", state="MI"
            ))
        assert len(store) == 3
        assert len(store.all()) == 3

    def test_subdivision_store_get_missing_returns_none(self):
        store = InMemorySubdivisionStore()
        assert store.get(uuid4()) is None

    def test_opportunity_store_save_and_get(self):
        store = InMemoryOpportunityStore()
        opp = Opportunity(
            opportunity_type=OpportunityType.STALLED_SUBDIVISION,
            parcel_ids=[uuid4()],
            municipality_id=_MUNI_ID,
            status=OpportunityStatus.DETECTED,
        )
        store.save(opp)
        assert store.get(opp.opportunity_id) is not None

    def test_opportunity_store_get_by_subdivision(self):
        store = InMemoryOpportunityStore()
        sub_id = uuid4()
        opp1 = Opportunity(
            opportunity_type=OpportunityType.STALLED_SUBDIVISION,
            parcel_ids=[uuid4()],
            municipality_id=_MUNI_ID,
            subdivision_id=sub_id,
            status=OpportunityStatus.DETECTED,
        )
        opp2 = Opportunity(
            opportunity_type=OpportunityType.STALLED_SUBDIVISION,
            parcel_ids=[uuid4()],
            municipality_id=_MUNI_ID,
            subdivision_id=uuid4(),
            status=OpportunityStatus.DETECTED,
        )
        store.save(opp1)
        store.save(opp2)

        results = store.get_by_subdivision(sub_id)
        assert len(results) == 1
        assert results[0].opportunity_id == opp1.opportunity_id

    def test_opportunity_store_get_by_municipality(self):
        store = InMemoryOpportunityStore()
        muni1 = uuid4()
        muni2 = uuid4()
        opp1 = Opportunity(
            opportunity_type=OpportunityType.STALLED_SUBDIVISION,
            parcel_ids=[uuid4()],
            municipality_id=muni1,
            status=OpportunityStatus.DETECTED,
        )
        opp2 = Opportunity(
            opportunity_type=OpportunityType.STALLED_SUBDIVISION,
            parcel_ids=[uuid4()],
            municipality_id=muni2,
            status=OpportunityStatus.DETECTED,
        )
        store.save(opp1)
        store.save(opp2)

        results = store.get_by_municipality(muni1)
        assert len(results) == 1

    def test_opportunity_store_all_and_len(self):
        store = InMemoryOpportunityStore()
        for _ in range(3):
            store.save(Opportunity(
                opportunity_type=OpportunityType.STALLED_SUBDIVISION,
                parcel_ids=[uuid4()],
                municipality_id=_MUNI_ID,
                status=OpportunityStatus.DETECTED,
            ))
        assert len(store) == 3
        assert len(store.all()) == 3

    def test_opportunity_store_get_missing_returns_none(self):
        store = InMemoryOpportunityStore()
        assert store.get(uuid4()) is None


# ── AC-12 (additional): Full integration — scan returns events + opportunity ──


class TestScanIntegration:
    """Integration test: scan_subdivisions_for_stalls produces correct results."""

    def test_scan_willow_creek_produces_events_and_opportunity(self):
        subdivision, events, parcels = _willow_creek()
        store = InMemoryMunicipalEventStore()
        for ev in events:
            store.save(ev)

        engine, context = _engine_and_context()
        parcels_map = {subdivision.subdivision_id: parcels}

        results = scan_subdivisions_for_stalls(
            [subdivision], store, parcels_map, engine, context, now=_NOW
        )

        assert len(results) == 1
        assessment, emitted_events, opportunity = results[0]

        assert assessment.is_stalled is True
        assert len(emitted_events) > 0
        assert opportunity is not None
        assert opportunity.opportunity_type == OpportunityType.STALLED_SUBDIVISION

    def test_scan_oak_ridge_no_opportunity(self):
        subdivision, events, parcels = _oak_ridge()
        store = InMemoryMunicipalEventStore()
        for ev in events:
            store.save(ev)

        engine, context = _engine_and_context()
        parcels_map = {subdivision.subdivision_id: parcels}

        results = scan_subdivisions_for_stalls(
            [subdivision], store, parcels_map, engine, context, now=_NOW
        )

        assert len(results) == 1
        assessment, emitted_events, opportunity = results[0]

        assert assessment.is_stalled is False
        assert opportunity is None

    def test_scan_multiple_subdivisions(self):
        wc_sub, wc_events, wc_parcels = _willow_creek()
        or_sub, or_events, or_parcels = _oak_ridge()

        store = InMemoryMunicipalEventStore()
        for ev in wc_events + or_events:
            store.save(ev)

        engine, context = _engine_and_context()
        parcels_map = {
            wc_sub.subdivision_id: wc_parcels,
            or_sub.subdivision_id: or_parcels,
        }

        results = scan_subdivisions_for_stalls(
            [wc_sub, or_sub], store, parcels_map, engine, context, now=_NOW
        )

        assert len(results) == 2
        # First result (Willow Creek) should be stalled
        assert results[0][0].is_stalled is True
        assert results[0][2] is not None  # opportunity
        # Second result (Oak Ridge) should not be stalled
        assert results[1][0].is_stalled is False
        assert results[1][2] is None  # no opportunity

    def test_scan_maple_estates_partial_buildout(self):
        subdivision, events, parcels = _maple_estates()
        store = InMemoryMunicipalEventStore()
        for ev in events:
            store.save(ev)

        engine, context = _engine_and_context()
        parcels_map = {subdivision.subdivision_id: parcels}

        results = scan_subdivisions_for_stalls(
            [subdivision], store, parcels_map, engine, context, now=_NOW
        )

        assert len(results) == 1
        assessment, emitted_events, opportunity = results[0]

        # Maple Estates should emit partial_buildout_stagnation_detected
        stagnation = [
            e for e in emitted_events
            if e.event_type == "partial_buildout_stagnation_detected"
        ]
        assert len(stagnation) == 1


# ── Additional edge cases ─────────────────────────────────────────────────────


class TestEdgeCases:
    """Additional edge cases for robustness."""

    def test_empty_events_list(self):
        """Subdivision with no municipal events."""
        sub = Subdivision(
            name="Empty Sub",
            municipality_id=_MUNI_ID,
            county="Washtenaw",
            state="MI",
            plat_date=date(2015, 1, 1),
            total_lots=10,
            vacant_lots=8,
        )
        assessment = detect_stall(sub, [], [], now=_NOW)
        # Should detect plat_age + high_vacancy + no_recent_activity
        assert "plat_age" in assessment.stall_signals
        assert "high_vacancy" in assessment.stall_signals
        assert "no_recent_activity" in assessment.stall_signals
        assert assessment.is_stalled is True

    def test_no_plat_date(self):
        """Subdivision without plat_date — plat_age signal should not fire."""
        sub = Subdivision(
            name="No Plat Sub",
            municipality_id=_MUNI_ID,
            county="Washtenaw",
            state="MI",
            total_lots=10,
            vacant_lots=8,
        )
        assessment = detect_stall(sub, [], [], now=_NOW)
        assert "plat_age" not in assessment.stall_signals

    def test_vacancy_from_parcels_when_subdivision_fields_missing(self):
        """When subdivision lacks total_lots/vacant_lots, use parcel list."""
        sub_id = uuid4()
        sub = Subdivision(
            subdivision_id=sub_id,
            name="Parcel Count Sub",
            municipality_id=_MUNI_ID,
            county="Washtenaw",
            state="MI",
        )
        parcels = (
            [_make_parcel(sub_id, vacancy_status=VacancyStatus.VACANT) for _ in range(7)]
            + [_make_parcel(sub_id, vacancy_status=VacancyStatus.IMPROVED) for _ in range(3)]
        )
        assessment = detect_stall(sub, [], parcels, now=_NOW)
        assert assessment.vacancy_ratio == pytest.approx(0.70, abs=0.01)

    def test_all_events_have_required_derived_fields(self):
        """Every emitted event must have DERIVED class requirements."""
        subdivision, events, parcels = _willow_creek()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)

        assert len(emitted) > 0
        for ev in emitted:
            assert ev.event_class == EventClass.DERIVED
            assert ev.generation_depth == 1
            assert ev.emitted_by_agent_run_id is not None
            assert ev.derived_from_event_ids is not None
            assert len(ev.derived_from_event_ids) > 0
            assert ev.source_confidence is not None
            assert 0.0 <= ev.source_confidence <= 1.0
            assert ev.entity_refs.subdivision_id is not None
            assert ev.entity_refs.municipality_id is not None

    def test_all_events_share_same_agent_run_id(self):
        """All events from a single build_stallout_events call share one agent_run_id."""
        subdivision, events, parcels = _willow_creek()
        assessment = detect_stall(subdivision, events, parcels, now=_NOW)
        emitted = build_stallout_events(assessment, subdivision, events, now=_NOW)

        assert len(emitted) > 1
        run_ids = {ev.emitted_by_agent_run_id for ev in emitted}
        assert len(run_ids) == 1, f"Expected 1 agent_run_id, got {len(run_ids)}"
