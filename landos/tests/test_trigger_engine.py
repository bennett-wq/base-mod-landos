"""Tests for the Step 3 trigger engine scaffold.

Proves all Step 3 acceptance criteria:
1. Matching rule fires.
2. Non-matching rule does not fire.
3. Cooldown blocks a duplicate.
4. Generation-depth hard cap stops recursion.
5. Phase gating prevents Phase 2+ rules from firing in Phase 1 context.

Also covers:
- phase_allows() ordering helper
- Cross-family routing (cluster event → municipal wake)
- RoutingResult structure (event_id, causal_chain_id inheritance, timestamps)
- raw_event_bypasses_cooldown per-rule opt-in semantics
- Engine startup validation (mismatched cooldown fields)
- Deterministic time: cooldown expiry controlled via context.current_timestamp
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily, RoutingClass
from src.triggers.context import TriggerContext
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.engine import TriggerEngine
from src.triggers.enums import PhaseGate, TriggerOutcome, WakeType, phase_allows
from src.triggers.rule import TriggerRule
from src.triggers.rules import ALL_RULES, RA, RB, RC, RD


# ── Helpers ───────────────────────────────────────────────────────────

_FIXED_TS = datetime(2026, 3, 9, 12, 0, 0, tzinfo=timezone.utc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ctx(
    phase: PhaseGate = PhaseGate.PHASE_1,
    depth_cap: int = 5,
    now: datetime | None = None,
) -> TriggerContext:
    return TriggerContext(
        active_phase=phase,
        generation_depth_cap=depth_cap,
        current_timestamp=now or _FIXED_TS,
    )


def _engine(rules=None) -> tuple[TriggerEngine, InMemoryCooldownTracker]:
    tracker = InMemoryCooldownTracker()
    engine = TriggerEngine(
        rules=rules if rules is not None else ALL_RULES,
        cooldown_tracker=tracker,
    )
    return engine, tracker


def _listing_added(
    acreage: float = 0.5,
    listing_id: UUID | None = None,
    generation_depth: int = 0,
    causal_chain_id: UUID | None = None,
) -> EventEnvelope:
    """listing_added is always EventClass.RAW — comes from MLS feed."""
    return EventEnvelope(
        event_type="listing_added",
        event_family=EventFamily.LISTING,
        event_class=EventClass.RAW,
        occurred_at=_now(),
        observed_at=_now(),
        source_system="spark_rets",
        entity_refs=EntityRefs(listing_id=listing_id or uuid4()),
        payload={"listing_key": "MLS-1", "list_price": 80000, "acreage": acreage},
        generation_depth=generation_depth,
        causal_chain_id=causal_chain_id,
    )


def _cluster_detected(
    cluster_id: UUID | None = None,
    cluster_size: int = 4,
) -> EventEnvelope:
    """owner_cluster_detected is always EventClass.DERIVED."""
    return EventEnvelope(
        event_type="owner_cluster_detected",
        event_family=EventFamily.CLUSTER_OWNER,
        event_class=EventClass.DERIVED,
        occurred_at=_now(),
        observed_at=_now(),
        source_system="scoring_engine",
        entity_refs=EntityRefs(cluster_id=cluster_id or uuid4()),
        payload={"cluster_size": cluster_size, "cluster_type": "same_owner"},
        source_confidence=0.85,
        derived_from_event_ids=[uuid4()],
        emitted_by_agent_run_id=uuid4(),
        generation_depth=1,
    )


def _incentive_detected() -> EventEnvelope:
    """incentive_detected is Class: raw per LANDOS_EVENT_LIBRARY.md."""
    return EventEnvelope(
        event_type="incentive_detected",
        event_family=EventFamily.INCENTIVE,
        event_class=EventClass.RAW,
        occurred_at=_now(),
        observed_at=_now(),
        source_system="municipal_intelligence_team",
        entity_refs=EntityRefs(municipality_id=uuid4()),
        payload={"incentive_name": "Tax Abatement", "jurisdiction": "Ypsilanti Township"},
    )


def _parcel_score_updated() -> EventEnvelope:
    return EventEnvelope(
        event_type="parcel_score_updated",
        event_family=EventFamily.PARCEL_STATE,
        event_class=EventClass.DERIVED,
        occurred_at=_now(),
        observed_at=_now(),
        source_system="scoring_engine",
        entity_refs=EntityRefs(parcel_id=uuid4()),
        payload={"opportunity_score": 0.72, "delta": 0.08},
        source_confidence=0.90,
        derived_from_event_ids=[uuid4()],
        emitted_by_agent_run_id=uuid4(),
        generation_depth=1,
    )


# ── Phase ordering helper ─────────────────────────────────────────────


class TestPhaseAllows:
    def test_phase1_allows_phase1(self):
        assert phase_allows(PhaseGate.PHASE_1, PhaseGate.PHASE_1) is True

    def test_phase1_allowed_in_phase2(self):
        assert phase_allows(PhaseGate.PHASE_1, PhaseGate.PHASE_2) is True

    def test_phase2_not_allowed_in_phase1(self):
        assert phase_allows(PhaseGate.PHASE_2, PhaseGate.PHASE_1) is False

    def test_phase3_not_allowed_in_phase2(self):
        assert phase_allows(PhaseGate.PHASE_3_PLUS, PhaseGate.PHASE_2) is False

    def test_phase3_allowed_in_phase3(self):
        assert phase_allows(PhaseGate.PHASE_3_PLUS, PhaseGate.PHASE_3_PLUS) is True


# ── 1. Matching rule fires ────────────────────────────────────────────


class TestMatchingRuleFires:
    def test_listing_added_fires_rule_ra(self):
        engine, _ = _engine()
        evt = _listing_added(acreage=0.5)
        result = engine.evaluate(evt, _ctx())
        assert RA.rule_id in result.fired_rules
        wake = next(w for w in result.wake_instructions if w.rule_id == RA.rule_id)
        assert wake.wake_target == "supply_intelligence_team"
        assert wake.wake_type == WakeType.LINK

    def test_two_rules_match_same_event_both_fire(self):
        engine, _ = _engine()
        evt = _listing_added(acreage=6.0)
        result = engine.evaluate(evt, _ctx())
        assert RA.rule_id in result.fired_rules
        assert RB.rule_id in result.fired_rules
        assert len(result.wake_instructions) == 2


# ── 2. Non-matching rule does not fire ───────────────────────────────


class TestNonMatchingRuleDoesNotFire:
    def test_wrong_event_type_no_match(self):
        engine, _ = _engine()
        evt = _parcel_score_updated()
        result = engine.evaluate(evt, _ctx())
        assert result.fired_rules == []
        assert result.wake_instructions == []

    def test_condition_not_met_suppresses_rb(self):
        engine, _ = _engine()
        evt = _listing_added(acreage=1.0)
        result = engine.evaluate(evt, _ctx())
        assert RB.rule_id not in result.fired_rules
        suppressed_ids = [s.rule_id for s in result.suppressed_rules]
        assert RB.rule_id in suppressed_ids
        rb_sup = next(s for s in result.suppressed_rules if s.rule_id == RB.rule_id)
        assert rb_sup.outcome == TriggerOutcome.CONDITION_NOT_MET
        # RA still fires
        assert RA.rule_id in result.fired_rules

    def test_condition_not_met_suppresses_rc(self):
        engine, _ = _engine()
        evt = _cluster_detected(cluster_size=2)
        result = engine.evaluate(evt, _ctx())
        assert RC.rule_id not in result.fired_rules
        suppressed_ids = [s.rule_id for s in result.suppressed_rules]
        assert RC.rule_id in suppressed_ids
        rc_sup = next(s for s in result.suppressed_rules if s.rule_id == RC.rule_id)
        assert rc_sup.outcome == TriggerOutcome.CONDITION_NOT_MET


# ── 3. Cooldown blocks duplicate ─────────────────────────────────────


class TestCooldownBlocksDuplicate:
    def test_cooldown_blocks_second_fire_same_cluster(self):
        engine, _ = _engine()
        cluster_id = uuid4()
        evt = _cluster_detected(cluster_id=cluster_id, cluster_size=4)

        # First call at _FIXED_TS: should fire
        result1 = engine.evaluate(evt, _ctx())
        assert RC.rule_id in result1.fired_rules

        # Second call at same timestamp: still within cooldown window
        result2 = engine.evaluate(evt, _ctx())
        suppressed_ids = [s.rule_id for s in result2.suppressed_rules]
        assert RC.rule_id in suppressed_ids
        rc_sup = next(s for s in result2.suppressed_rules if s.rule_id == RC.rule_id)
        assert rc_sup.outcome == TriggerOutcome.COOLDOWN_BLOCKED

    def test_cooldown_expires_after_window(self):
        engine, _ = _engine()
        cluster_id = uuid4()
        evt = _cluster_detected(cluster_id=cluster_id, cluster_size=4)

        # Fire at _FIXED_TS — sets cooldown
        engine.evaluate(evt, _ctx(now=_FIXED_TS))

        # Evaluate at _FIXED_TS + cooldown + 1s — cooldown has expired
        t_after = _FIXED_TS + timedelta(seconds=RC.cooldown_seconds + 1)  # type: ignore[operator]
        result = engine.evaluate(evt, _ctx(now=t_after))
        assert RC.rule_id in result.fired_rules

    def test_different_cluster_not_affected_by_cooldown(self):
        engine, _ = _engine()
        evt_a = _cluster_detected(cluster_id=uuid4(), cluster_size=4)
        evt_b = _cluster_detected(cluster_id=uuid4(), cluster_size=4)
        result_a = engine.evaluate(evt_a, _ctx())
        result_b = engine.evaluate(evt_b, _ctx())
        assert RC.rule_id in result_a.fired_rules
        assert RC.rule_id in result_b.fired_rules

    def test_raw_event_bypasses_cooldown_when_rule_opts_in(self):
        """listing_added is naturally RAW. A rule with raw_event_bypasses_cooldown=True
        should fire again for the same listing even within the cooldown window."""
        listing_id = uuid4()
        bypass_rule = TriggerRule(
            rule_id="TEST__bypass_listing_rule",
            event_type="listing_added",
            wake_target="supply_intelligence_team",
            wake_type=WakeType.LINK,
            phase=PhaseGate.PHASE_1,
            priority=5,
            routing_class=RoutingClass.STANDARD,
            condition=lambda e, ctx: True,
            cooldown_seconds=3600,
            cooldown_key_builder=lambda e, ctx: f"listing:{e.entity_refs.listing_id}",
            raw_event_bypasses_cooldown=True,
        )
        engine = TriggerEngine(
            rules=[bypass_rule], cooldown_tracker=InMemoryCooldownTracker()
        )
        evt = _listing_added(listing_id=listing_id)

        # First fire — sets cooldown
        r1 = engine.evaluate(evt, _ctx())
        assert bypass_rule.rule_id in r1.fired_rules

        # Second fire at same timestamp — should fire again because RAW + rule opts in
        r2 = engine.evaluate(evt, _ctx())
        assert bypass_rule.rule_id in r2.fired_rules

    def test_raw_event_does_not_bypass_cooldown_when_rule_does_not_opt_in(self):
        """listing_added is naturally RAW. A rule with raw_event_bypasses_cooldown=False
        should still be blocked by cooldown even though the event is raw."""
        listing_id = uuid4()
        no_bypass_rule = TriggerRule(
            rule_id="TEST__no_bypass_listing_rule",
            event_type="listing_added",
            wake_target="supply_intelligence_team",
            wake_type=WakeType.LINK,
            phase=PhaseGate.PHASE_1,
            priority=5,
            routing_class=RoutingClass.STANDARD,
            condition=lambda e, ctx: True,
            cooldown_seconds=3600,
            cooldown_key_builder=lambda e, ctx: f"listing:{e.entity_refs.listing_id}",
            raw_event_bypasses_cooldown=False,
        )
        engine = TriggerEngine(
            rules=[no_bypass_rule], cooldown_tracker=InMemoryCooldownTracker()
        )
        evt = _listing_added(listing_id=listing_id)

        # First fire — sets cooldown
        r1 = engine.evaluate(evt, _ctx())
        assert no_bypass_rule.rule_id in r1.fired_rules

        # Second fire at same timestamp — blocked despite being RAW, rule does not opt in
        r2 = engine.evaluate(evt, _ctx())
        suppressed_ids = [s.rule_id for s in r2.suppressed_rules]
        assert no_bypass_rule.rule_id in suppressed_ids
        sup = next(s for s in r2.suppressed_rules if s.rule_id == no_bypass_rule.rule_id)
        assert sup.outcome == TriggerOutcome.COOLDOWN_BLOCKED


# ── 4. Generation depth cap ───────────────────────────────────────────


class TestGenerationDepthCap:
    def test_depth_at_cap_blocks_all_rules(self):
        engine, _ = _engine()
        evt = _listing_added(acreage=6.0, generation_depth=5)
        result = engine.evaluate(evt, _ctx())
        assert result.fired_rules == []
        assert result.wake_instructions == []
        suppressed_ids = [s.rule_id for s in result.suppressed_rules]
        assert RA.rule_id in suppressed_ids
        assert RB.rule_id in suppressed_ids
        for s in result.suppressed_rules:
            assert s.outcome == TriggerOutcome.DEPTH_CAP_REACHED

    def test_depth_below_cap_fires_normally(self):
        engine, _ = _engine()
        evt = _listing_added(acreage=0.5, generation_depth=4)
        result = engine.evaluate(evt, _ctx())
        assert RA.rule_id in result.fired_rules

    def test_wake_instruction_depth_is_incremented(self):
        engine, _ = _engine()
        evt = _listing_added(acreage=0.5, generation_depth=2)
        result = engine.evaluate(evt, _ctx())
        wake = next(w for w in result.wake_instructions if w.rule_id == RA.rule_id)
        assert wake.generation_depth == 3


# ── 5. Phase gating ───────────────────────────────────────────────────


class TestPhaseGating:
    def test_phase_2_rule_suppressed_in_phase_1_context(self):
        engine, _ = _engine()
        evt = _incentive_detected()
        result = engine.evaluate(evt, _ctx(phase=PhaseGate.PHASE_1))
        assert RD.rule_id not in result.fired_rules
        suppressed_ids = [s.rule_id for s in result.suppressed_rules]
        assert RD.rule_id in suppressed_ids
        rd_sup = next(s for s in result.suppressed_rules if s.rule_id == RD.rule_id)
        assert rd_sup.outcome == TriggerOutcome.PHASE_GATED

    def test_phase_2_rule_fires_in_phase_2_context(self):
        engine, _ = _engine()
        evt = _incentive_detected()
        result = engine.evaluate(evt, _ctx(phase=PhaseGate.PHASE_2))
        assert RD.rule_id in result.fired_rules

    def test_phase_1_rule_fires_in_phase_2_context(self):
        engine, _ = _engine()
        evt = _listing_added(acreage=6.0)
        result = engine.evaluate(evt, _ctx(phase=PhaseGate.PHASE_2))
        assert RA.rule_id in result.fired_rules
        assert RB.rule_id in result.fired_rules


# ── 6. RoutingResult structure ────────────────────────────────────────


class TestRoutingResult:
    def test_routing_result_has_correct_event_id(self):
        engine, _ = _engine()
        evt = _listing_added()
        result = engine.evaluate(evt, _ctx())
        assert result.event_id == evt.event_id

    def test_evaluated_at_matches_context_timestamp(self):
        engine, _ = _engine()
        evt = _listing_added()
        result = engine.evaluate(evt, _ctx(now=_FIXED_TS))
        assert result.evaluated_at == _FIXED_TS

    def test_wake_instruction_created_at_matches_context_timestamp(self):
        engine, _ = _engine()
        evt = _listing_added()
        result = engine.evaluate(evt, _ctx(now=_FIXED_TS))
        for wake in result.wake_instructions:
            assert wake.created_at == _FIXED_TS

    def test_causal_chain_id_inherited(self):
        engine, _ = _engine()
        chain_id = uuid4()
        evt = _listing_added(causal_chain_id=chain_id)
        result = engine.evaluate(evt, _ctx())
        for wake in result.wake_instructions:
            assert wake.causal_chain_id == chain_id

    def test_causal_chain_id_assigned_when_absent(self):
        """Raw event with no causal_chain_id: engine assigns a new UUID.
        All wake instructions for the same event share that same new UUID."""
        engine, _ = _engine()
        evt = _listing_added(acreage=6.0)  # triggers RA and RB
        assert evt.causal_chain_id is None
        result = engine.evaluate(evt, _ctx())
        assert len(result.wake_instructions) == 2
        chain_ids = {w.causal_chain_id for w in result.wake_instructions}
        assert len(chain_ids) == 1  # all share the same newly assigned UUID
        assert isinstance(chain_ids.pop(), UUID)


# ── 7. Cross-family routing ───────────────────────────────────────────


class TestCrossFamilyRouting:
    def test_cluster_event_wakes_municipal_team(self):
        """owner_cluster_detected (cluster_owner family) → municipal_intelligence_team wake.
        Proves event-mesh cross-family routing."""
        engine, _ = _engine()
        evt = _cluster_detected(cluster_size=4)
        result = engine.evaluate(evt, _ctx())
        assert RC.rule_id in result.fired_rules
        wake = next(w for w in result.wake_instructions if w.rule_id == RC.rule_id)
        assert wake.wake_target == "municipal_intelligence_team"
        assert wake.wake_type == WakeType.RESCAN


# ── 8. Engine startup validation ─────────────────────────────────────


class TestEngineStartupValidation:
    def test_rule_with_cooldown_seconds_but_no_builder_raises(self):
        bad_rule = TriggerRule(
            rule_id="BAD__no_builder",
            event_type="listing_added",
            wake_target="test",
            wake_type=WakeType.LINK,
            phase=PhaseGate.PHASE_1,
            priority=5,
            routing_class=RoutingClass.STANDARD,
            condition=lambda e, ctx: True,
            cooldown_seconds=3600,
            cooldown_key_builder=None,  # missing — should raise
        )
        with pytest.raises(ValueError, match="cooldown_seconds and cooldown_key_builder"):
            TriggerEngine(rules=[bad_rule], cooldown_tracker=InMemoryCooldownTracker())

    def test_rule_with_builder_but_no_cooldown_seconds_raises(self):
        bad_rule = TriggerRule(
            rule_id="BAD__no_seconds",
            event_type="listing_added",
            wake_target="test",
            wake_type=WakeType.LINK,
            phase=PhaseGate.PHASE_1,
            priority=5,
            routing_class=RoutingClass.STANDARD,
            condition=lambda e, ctx: True,
            cooldown_seconds=None,
            cooldown_key_builder=lambda e, ctx: "some_key",  # orphaned — should raise
        )
        with pytest.raises(ValueError, match="cooldown_seconds and cooldown_key_builder"):
            TriggerEngine(rules=[bad_rule], cooldown_tracker=InMemoryCooldownTracker())


# ── 9. Package imports ────────────────────────────────────────────────


class TestPackageImports:
    def test_triggers_package_exports(self):
        from src.triggers import TriggerEngine, TriggerRule, WakeInstruction, RoutingResult
        assert TriggerEngine is not None
        assert TriggerRule is not None
        assert WakeInstruction is not None
        assert RoutingResult is not None
