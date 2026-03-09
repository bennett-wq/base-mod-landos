"""TriggerEngine — the routing brain of the LandOS event mesh.

Receives an EventEnvelope, evaluates all registered TriggerRules,
and returns a RoutingResult with WakeInstructions for rules that fired
and SuppressedRules for rules that did not.

Evaluation order per rule (stops at first suppression):
  1. Phase gate      — rule.phase vs context.active_phase via phase_allows()
  2. Depth cap       — event.generation_depth >= context.generation_depth_cap
                       Short-circuits ALL remaining rules if triggered.
  3. Condition       — rule.condition(event, context)
  4. Cooldown        — rule.cooldown_seconds + cooldown_key_builder
                       Bypassed only if event is RAW AND rule.raw_event_bypasses_cooldown.
  5. Materiality     — rule.materiality_threshold vs context.score_delta
  6. Fire            — produce WakeInstruction, record cooldown wake

Time handling:
  All timestamps in this evaluation — RoutingResult.evaluated_at,
  WakeInstruction.created_at, and all cooldown reads/writes — use
  context.current_timestamp. No wall-clock calls are made inside this module.

Anti-loop note (one-direction causality):
  Layer 2 of the trigger matrix's anti-loop defense is NOT implemented
  at the engine level. It is enforced per-rule via condition lambdas.
  Rule authors must add causality guards to their condition functions
  when wiring rules in Steps 4–8.

Recursion limit note:
  When the depth cap fires, the engine records DEPTH_CAP_REACHED in
  suppressed_rules. It does NOT emit a recursion_limit_reached EventEnvelope
  — that would create a circular dependency. Event emission for recursion
  limits belongs in the agent orchestration layer (Step 4+).
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID, uuid4

from src.events.envelope import EventEnvelope
from src.events.enums import EventClass
from src.triggers.context import TriggerContext
from src.triggers.cooldown import CooldownTracker
from src.triggers.enums import TriggerOutcome, phase_allows
from src.triggers.result import RoutingResult, SuppressedRule
from src.triggers.rule import TriggerRule
from src.triggers.wake import WakeInstruction

logger = logging.getLogger(__name__)


class TriggerEngine:
    """Evaluates trigger rules against incoming EventEnvelopes."""

    def __init__(
        self,
        rules: list[TriggerRule],
        cooldown_tracker: CooldownTracker,
    ) -> None:
        self._rules = rules
        self._cooldown = cooldown_tracker
        self._validate_rules()

    def _validate_rules(self) -> None:
        """Ensure cooldown_seconds and cooldown_key_builder are always paired."""
        for rule in self._rules:
            has_seconds = rule.cooldown_seconds is not None
            has_builder = rule.cooldown_key_builder is not None
            if has_seconds != has_builder:
                raise ValueError(
                    f"Rule '{rule.rule_id}': cooldown_seconds and cooldown_key_builder "
                    f"must both be set or both be None."
                )

    def evaluate(
        self,
        event: EventEnvelope,
        context: TriggerContext | None = None,
    ) -> RoutingResult:
        """Evaluate all rules against the event and return a RoutingResult."""
        if context is None:
            context = TriggerContext()

        now: datetime = context.current_timestamp

        result = RoutingResult(
            event_id=event.event_id,
            event_type=event.event_type,
            evaluated_at=now,
        )

        # Resolve causal_chain_id once for all WakeInstructions from this event.
        causal_chain_id: UUID = event.causal_chain_id or uuid4()

        # Check depth cap before evaluating any individual rule.
        # If triggered, all matching rules are suppressed and we return immediately.
        if event.generation_depth >= context.generation_depth_cap:
            logger.warning(
                "generation_depth %d >= cap %d for event %s (%s). "
                "All rules suppressed. Emit recursion_limit_reached via orchestration layer.",
                event.generation_depth,
                context.generation_depth_cap,
                event.event_id,
                event.event_type,
            )
            for rule in self._rules:
                if self._event_matches_rule(event, rule):
                    result.suppressed_rules.append(
                        SuppressedRule(
                            rule_id=rule.rule_id,
                            outcome=TriggerOutcome.DEPTH_CAP_REACHED,
                            detail=(
                                f"generation_depth {event.generation_depth} "
                                f">= cap {context.generation_depth_cap}"
                            ),
                        )
                    )
            return result

        for rule in self._rules:
            if not self._event_matches_rule(event, rule):
                continue

            # 1. Phase gate — always use phase_allows(), never compare PhaseGate directly.
            if not phase_allows(rule.phase, context.active_phase):
                result.suppressed_rules.append(
                    SuppressedRule(
                        rule_id=rule.rule_id,
                        outcome=TriggerOutcome.PHASE_GATED,
                        detail=(
                            f"rule phase {rule.phase} not active "
                            f"(active: {context.active_phase})"
                        ),
                    )
                )
                continue

            # 2. Condition
            try:
                condition_met = rule.condition(event, context)
            except Exception as exc:
                logger.error(
                    "Rule '%s' condition raised an exception: %s", rule.rule_id, exc
                )
                condition_met = False

            if not condition_met:
                result.suppressed_rules.append(
                    SuppressedRule(
                        rule_id=rule.rule_id,
                        outcome=TriggerOutcome.CONDITION_NOT_MET,
                    )
                )
                continue

            # 3. Cooldown
            if rule.cooldown_seconds is not None and rule.cooldown_key_builder is not None:
                cooldown_suppressed = self._check_cooldown(rule, event, context, now)
                if cooldown_suppressed is not None:
                    result.suppressed_rules.append(cooldown_suppressed)
                    continue

            # 4. Materiality
            materiality_suppressed = self._check_materiality(rule, event, context)
            if materiality_suppressed is not None:
                result.suppressed_rules.append(materiality_suppressed)
                continue

            # All checks passed — fire the rule.
            wake = self._build_wake_instruction(rule, event, causal_chain_id, now)
            result.fired_rules.append(rule.rule_id)
            result.wake_instructions.append(wake)

            # Record cooldown wake after firing.
            if rule.cooldown_seconds is not None and rule.cooldown_key_builder is not None:
                cooldown_key = rule.cooldown_key_builder(event, context)
                if cooldown_key is not None:
                    self._cooldown.record_wake(cooldown_key, rule.rule_id, now)

        return result

    # ── Private helpers ───────────────────────────────────────────────

    def _event_matches_rule(self, event: EventEnvelope, rule: TriggerRule) -> bool:
        return rule.event_type == "*" or rule.event_type == event.event_type

    def _check_cooldown(
        self,
        rule: TriggerRule,
        event: EventEnvelope,
        context: TriggerContext,
        now: datetime,
    ) -> SuppressedRule | None:
        """Return a SuppressedRule if cooldown blocks, else None."""
        # Raw-event bypass: only when the rule explicitly opts in.
        if rule.raw_event_bypasses_cooldown and event.event_class == EventClass.RAW:
            return None

        cooldown_key = rule.cooldown_key_builder(event, context)  # type: ignore[misc]
        if cooldown_key is None:
            # Key builder returned None — no scoping for this event; skip cooldown.
            return None

        if self._cooldown.is_cooling_down(
            cooldown_key, rule.rule_id, rule.cooldown_seconds, now  # type: ignore[arg-type]
        ):
            return SuppressedRule(
                rule_id=rule.rule_id,
                outcome=TriggerOutcome.COOLDOWN_BLOCKED,
                detail=f"cooldown key '{cooldown_key}' active for {rule.cooldown_seconds}s",
            )
        return None

    def _check_materiality(
        self,
        rule: TriggerRule,
        event: EventEnvelope,
        context: TriggerContext,
    ) -> SuppressedRule | None:
        """Return a SuppressedRule if materiality gate blocks, else None."""
        if rule.materiality_threshold is None:
            return None
        if event.event_class == EventClass.RAW:
            return None  # Raw events always bypass materiality.
        if context.score_delta is None:
            # Scoring engine not yet available; pass the gate with a warning.
            logger.warning(
                "Rule '%s' has materiality_threshold %.3f but context.score_delta is None. "
                "Gate passes (scoring engine not yet wired).",
                rule.rule_id,
                rule.materiality_threshold,
            )
            return None
        if context.score_delta < rule.materiality_threshold:
            return SuppressedRule(
                rule_id=rule.rule_id,
                outcome=TriggerOutcome.MATERIALITY_NOT_MET,
                detail=(
                    f"score_delta {context.score_delta:.4f} "
                    f"< threshold {rule.materiality_threshold:.4f}"
                ),
            )
        return None

    def _build_wake_instruction(
        self,
        rule: TriggerRule,
        event: EventEnvelope,
        causal_chain_id: UUID,
        now: datetime,
    ) -> WakeInstruction:
        return WakeInstruction(
            rule_id=rule.rule_id,
            source_event_id=event.event_id,
            wake_target=rule.wake_target,
            wake_type=rule.wake_type,
            priority=rule.priority,
            routing_class=rule.routing_class,
            entity_refs=event.entity_refs,
            generation_depth=event.generation_depth + 1,
            causal_chain_id=causal_chain_id,
            created_at=now,
        )
