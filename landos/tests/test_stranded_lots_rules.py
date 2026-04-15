"""Stranded-lots trigger rules — acceptance tests.

Covers all 9 acceptance criteria for Task M2-2:

AC-1:  All 4 SL rules appear in ALL_RULES (registry wired)
AC-2:  SL1 condition fires for any parcel_discovered event
AC-3:  SL2 condition fires for any zoning_resolved event
AC-4:  SL3 condition fires for parcel_underwritten with verdict "GO"
AC-5:  SL3 condition fires for parcel_underwritten with verdict "NEGOTIATE"
AC-6:  SL3 condition does NOT fire for parcel_underwritten with verdict "NO-GO"
AC-7:  SL4 condition fires for any area_favorable event
AC-8:  Cooldown key builders produce expected key strings
AC-9:  No duplicate rule_ids (import succeeds; safety check in __init__.py)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.events.envelope import EntityRefs, EventEnvelope
from src.events.enums import EventClass, EventFamily
from src.triggers.context import TriggerContext
from src.triggers.cooldown import InMemoryCooldownTracker
from src.triggers.engine import TriggerEngine
from src.triggers.enums import PhaseGate
from src.triggers.rules import ALL_RULES
from src.triggers.rules.stranded_lots_rules import (
    ALL_STRANDED_LOTS_RULES,
    SL1,
    SL2,
    SL3,
    SL4,
)

# ── Constants ──────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)
_MUNI_ID = uuid4()
_PARCEL_ID = uuid4()


# ── Fixture helpers ────────────────────────────────────────────────────────────

def _engine() -> TriggerEngine:
    return TriggerEngine(rules=ALL_RULES, cooldown_tracker=InMemoryCooldownTracker())


def _ctx(phase: PhaseGate = PhaseGate.PHASE_1) -> TriggerContext:
    return TriggerContext(
        active_phase=phase,
        current_timestamp=_NOW,
    )


def _make_raw_event(
    event_type: str,
    event_family: EventFamily,
    payload: dict,
) -> EventEnvelope:
    """Build a minimal RAW EventEnvelope for trigger tests."""
    return EventEnvelope(
        event_type=event_type,
        event_family=event_family,
        event_class=EventClass.RAW,
        occurred_at=_NOW,
        observed_at=_NOW,
        source_system="test_harness",
        entity_refs=EntityRefs(parcel_id=_PARCEL_ID),
        payload=payload,
    )


# ── AC-1: Registry wiring ──────────────────────────────────────────────────────


class TestRegistryWiring:
    """AC-1: All 4 SL rules must appear in ALL_RULES."""

    def test_all_stranded_lots_rules_in_all_rules(self):
        rule_ids = {r.rule_id for r in ALL_RULES}
        for rule in ALL_STRANDED_LOTS_RULES:
            assert rule.rule_id in rule_ids, (
                f"{rule.rule_id} missing from ALL_RULES"
            )

    def test_sl1_in_all_rules(self):
        assert SL1 in ALL_RULES

    def test_sl2_in_all_rules(self):
        assert SL2 in ALL_RULES

    def test_sl3_in_all_rules(self):
        assert SL3 in ALL_RULES

    def test_sl4_in_all_rules(self):
        assert SL4 in ALL_RULES

    def test_all_stranded_lots_rules_has_four_entries(self):
        assert len(ALL_STRANDED_LOTS_RULES) == 4


# ── AC-2: SL1 condition ───────────────────────────────────────────────────────


class TestSL1Condition:
    """AC-2: SL1 fires for any parcel_discovered event."""

    def test_sl1_condition_fires(self):
        event = _make_raw_event(
            "parcel_discovered",
            EventFamily.PARCEL_STATE,
            {"parcel_apn": "14-02-100-001"},
        )
        ctx = _ctx()
        assert SL1.condition(event, ctx) is True

    def test_sl1_engine_fires(self):
        engine = _engine()
        ctx = _ctx()
        event = _make_raw_event(
            "parcel_discovered",
            EventFamily.PARCEL_STATE,
            {"parcel_apn": "14-02-100-001"},
        )
        result = engine.evaluate(event, ctx)
        matched = [r for r in result.fired_rules if r.startswith("SL1")]
        assert len(matched) >= 1


# ── AC-3: SL2 condition ───────────────────────────────────────────────────────


class TestSL2Condition:
    """AC-3: SL2 fires for any zoning_resolved event."""

    def test_sl2_condition_fires(self):
        event = _make_raw_event(
            "zoning_resolved",
            EventFamily.MUNICIPAL_PROCESS,
            {"municipality_id": str(_MUNI_ID), "district_code": "R-1"},
        )
        ctx = _ctx()
        assert SL2.condition(event, ctx) is True

    def test_sl2_engine_fires(self):
        engine = _engine()
        ctx = _ctx()
        event = _make_raw_event(
            "zoning_resolved",
            EventFamily.MUNICIPAL_PROCESS,
            {"municipality_id": str(_MUNI_ID), "district_code": "R-1"},
        )
        result = engine.evaluate(event, ctx)
        matched = [r for r in result.fired_rules if r.startswith("SL2")]
        assert len(matched) >= 1


# ── AC-4 / AC-5 / AC-6: SL3 condition ────────────────────────────────────────


class TestSL3Condition:
    """AC-4/5: SL3 fires for GO and NEGOTIATE; AC-6: does NOT fire for NO-GO."""

    @pytest.mark.parametrize("verdict", ["GO", "NEGOTIATE"])
    def test_sl3_condition_fires_for_go_and_negotiate(self, verdict: str):
        event = _make_raw_event(
            "parcel_underwritten",
            EventFamily.PARCEL_STATE,
            {"parcel_apn": "14-02-100-001", "verdict": verdict},
        )
        ctx = _ctx(PhaseGate.PHASE_2)
        assert SL3.condition(event, ctx) is True

    def test_sl3_condition_does_not_fire_for_no_go(self):
        event = _make_raw_event(
            "parcel_underwritten",
            EventFamily.PARCEL_STATE,
            {"parcel_apn": "14-02-100-001", "verdict": "NO-GO"},
        )
        ctx = _ctx(PhaseGate.PHASE_2)
        assert SL3.condition(event, ctx) is False

    def test_sl3_engine_fires_for_go(self):
        engine = _engine()
        ctx = _ctx(PhaseGate.PHASE_2)
        event = _make_raw_event(
            "parcel_underwritten",
            EventFamily.PARCEL_STATE,
            {"parcel_apn": "14-02-100-001", "verdict": "GO"},
        )
        result = engine.evaluate(event, ctx)
        matched = [r for r in result.fired_rules if r.startswith("SL3")]
        assert len(matched) >= 1

    def test_sl3_engine_does_not_fire_for_no_go(self):
        engine = _engine()
        ctx = _ctx(PhaseGate.PHASE_2)
        event = _make_raw_event(
            "parcel_underwritten",
            EventFamily.PARCEL_STATE,
            {"parcel_apn": "14-02-100-001", "verdict": "NO-GO"},
        )
        result = engine.evaluate(event, ctx)
        matched = [r for r in result.fired_rules if r.startswith("SL3")]
        assert len(matched) == 0

    def test_sl3_phase_gated_in_phase1(self):
        """SL3 is PHASE_2; should not fire when active phase is PHASE_1."""
        engine = _engine()
        ctx = _ctx(PhaseGate.PHASE_1)
        event = _make_raw_event(
            "parcel_underwritten",
            EventFamily.PARCEL_STATE,
            {"parcel_apn": "14-02-100-001", "verdict": "GO"},
        )
        result = engine.evaluate(event, ctx)
        matched = [r for r in result.fired_rules if r.startswith("SL3")]
        assert len(matched) == 0


# ── AC-7: SL4 condition ───────────────────────────────────────────────────────


class TestSL4Condition:
    """AC-7: SL4 fires for any area_favorable event."""

    def test_sl4_condition_fires(self):
        event = _make_raw_event(
            "area_favorable",
            EventFamily.PARCEL_STATE,
            {"scope_type": "municipality", "scope_value": "ann_arbor"},
        )
        ctx = _ctx()
        assert SL4.condition(event, ctx) is True

    def test_sl4_engine_fires(self):
        engine = _engine()
        ctx = _ctx()
        event = _make_raw_event(
            "area_favorable",
            EventFamily.PARCEL_STATE,
            {"scope_type": "municipality", "scope_value": "ann_arbor"},
        )
        result = engine.evaluate(event, ctx)
        matched = [r for r in result.fired_rules if r.startswith("SL4")]
        assert len(matched) >= 1


# ── AC-8: Cooldown key builders ───────────────────────────────────────────────


class TestCooldownKeyBuilders:
    """AC-8: cooldown_key_builder lambdas produce expected key strings."""

    def _fake_ctx(self) -> TriggerContext:
        return _ctx()

    def test_sl1_key_builder(self):
        event = _make_raw_event(
            "parcel_discovered",
            EventFamily.PARCEL_STATE,
            {"parcel_apn": "14-02-100-001"},
        )
        key = SL1.cooldown_key_builder(event, self._fake_ctx())
        assert key == "parcel_discovered:14-02-100-001"

    def test_sl1_key_builder_missing_apn(self):
        """Empty APN produces a stable key (no crash)."""
        event = _make_raw_event("parcel_discovered", EventFamily.PARCEL_STATE, {})
        key = SL1.cooldown_key_builder(event, self._fake_ctx())
        assert key == "parcel_discovered:"

    def test_sl2_key_builder(self):
        event = _make_raw_event(
            "zoning_resolved",
            EventFamily.MUNICIPAL_PROCESS,
            {"municipality_id": "muni-001", "district_code": "R-2"},
        )
        key = SL2.cooldown_key_builder(event, self._fake_ctx())
        assert key == "zoning_resolved:muni-001:R-2"

    def test_sl2_key_builder_partial(self):
        event = _make_raw_event(
            "zoning_resolved",
            EventFamily.MUNICIPAL_PROCESS,
            {"municipality_id": "muni-001"},
        )
        key = SL2.cooldown_key_builder(event, self._fake_ctx())
        assert key == "zoning_resolved:muni-001:"

    def test_sl3_key_builder(self):
        event = _make_raw_event(
            "parcel_underwritten",
            EventFamily.PARCEL_STATE,
            {"parcel_apn": "14-02-100-002", "verdict": "GO"},
        )
        key = SL3.cooldown_key_builder(event, self._fake_ctx())
        assert key == "parcel_underwritten:14-02-100-002"

    def test_sl4_key_builder(self):
        event = _make_raw_event(
            "area_favorable",
            EventFamily.PARCEL_STATE,
            {"scope_type": "zip", "scope_value": "48103"},
        )
        key = SL4.cooldown_key_builder(event, self._fake_ctx())
        assert key == "area_favorable:zip:48103"

    def test_sl4_key_builder_missing_fields(self):
        event = _make_raw_event("area_favorable", EventFamily.PARCEL_STATE, {})
        key = SL4.cooldown_key_builder(event, self._fake_ctx())
        assert key == "area_favorable::"


# ── AC-9: No duplicate rule_ids ───────────────────────────────────────────────


class TestNoDuplicateRuleIds:
    """AC-9: import succeeds — the __init__.py safety check catches dupes at import time."""

    def test_import_succeeds_no_duplicate_ids(self):
        """If import succeeded (file loaded), no duplicates exist."""
        from src.triggers.rules import ALL_RULES as _rules  # noqa: F401
        # The duplicate check in __init__.py raises RuntimeError at import time.
        # Reaching this line means it passed.
        all_ids = [r.rule_id for r in _rules]
        assert len(all_ids) == len(set(all_ids)), "Duplicate rule_ids detected"

    def test_sl_rule_ids_are_unique_within_group(self):
        sl_ids = [r.rule_id for r in ALL_STRANDED_LOTS_RULES]
        assert len(sl_ids) == len(set(sl_ids))
