"""Step 4.5 BBO signal trigger rules — bidirectional event mesh wiring.

Forward rules (BBO signals → cluster / supply intelligence):
  RI  — listing_bbo_cdom_threshold_crossed    → RESCAN cluster_detection_agent
  RJ  — listing_private_remarks_signal_detected (package_language) → CLASSIFY supply_intelligence_team
  RK  — listing_private_remarks_signal_detected (fatigue_language) → RESCORE supply_intelligence_team
  RL  — agent_land_accumulation_detected       → RESCAN cluster_detection_agent
  RM  — office_land_program_detected           → RESCAN cluster_detection_agent
  RN1 — developer_exit_signal_detected         → RESCAN cluster_detection_agent
  RN2 — developer_exit_signal_detected         → RESCORE supply_intelligence_team

Reverse rules (cluster + parcel → spark_signal_agent):
  RO  — owner_cluster_detected                 → RESCAN spark_signal_agent
  RP  — same_owner_listing_detected            → RESCAN spark_signal_agent
  RQ  — parcel_score_updated (≥0.70)           → RESCAN spark_signal_agent
  RR  — parcel_owner_resolved                  → RESCAN spark_signal_agent

Opportunity routing rules:
  RS  — developer_exit_signal_detected         → RESCAN opportunity_creation_agent
  RT  — subdivision_remnant_detected           → RESCAN opportunity_creation_agent
  RU1 — owner_cluster_size_threshold_crossed   → RESCAN opportunity_creation_agent
  RU2 — owner_cluster_size_threshold_crossed   → RESCAN municipal_agent
"""

from __future__ import annotations

from datetime import timedelta

from src.events.enums import RoutingClass
from src.triggers.enums import PhaseGate, WakeType
from src.triggers.rule import TriggerRule

_CDOM_COOLDOWN = int(timedelta(hours=24).total_seconds())
_REMARKS_PACKAGE_COOLDOWN = int(timedelta(days=7).total_seconds())
_REMARKS_FATIGUE_COOLDOWN = int(timedelta(hours=24).total_seconds())
_AGENT_COOLDOWN = int(timedelta(hours=12).total_seconds())
_OFFICE_COOLDOWN = int(timedelta(hours=12).total_seconds())
_DEV_EXIT_COOLDOWN = int(timedelta(hours=48).total_seconds())
_CLUSTER_REVERSE_COOLDOWN = int(timedelta(hours=12).total_seconds())
_SAME_OWNER_COOLDOWN = int(timedelta(hours=6).total_seconds())
_PARCEL_SCORE_REVERSE_COOLDOWN = int(timedelta(hours=24).total_seconds())
_PARCEL_OWNER_REVERSE_COOLDOWN = int(timedelta(hours=48).total_seconds())
_OPPORTUNITY_COOLDOWN = int(timedelta(hours=48).total_seconds())
_SUBDIVISION_COOLDOWN = int(timedelta(hours=72).total_seconds())
_CLUSTER_THRESHOLD_COOLDOWN = int(timedelta(hours=72).total_seconds())
_RELIST_COOLDOWN = int(timedelta(hours=24).total_seconds())
_FAILED_EXIT_COOLDOWN = int(timedelta(hours=24).total_seconds())
_DISTRESS_COOLDOWN = int(timedelta(days=7).total_seconds())


# ── RI — CDOM threshold → cluster rescan ──────────────────────────────────

RI = TriggerRule(
    rule_id="RI__listing_bbo_cdom_threshold_crossed__cluster_rescan",
    event_type="listing_bbo_cdom_threshold_crossed",
    wake_target="cluster_detection_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_CDOM_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"cdom_threshold:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "listing_bbo_cdom_threshold_crossed → RESCAN cluster_detection_agent. "
        "24-hour cooldown per listing. Step 4.5 forward rule."
    ),
)

# ── RJ — package language → CLASSIFY supply_intelligence_team ─────────────

RJ = TriggerRule(
    rule_id="RJ__private_remarks_package_language__classify",
    event_type="listing_private_remarks_signal_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.CLASSIFY,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: "package_language" in (e.payload.get("detected_categories") or []),
    cooldown_seconds=_REMARKS_PACKAGE_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"remarks_package:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "listing_private_remarks_signal_detected with package_language → "
        "CLASSIFY supply_intelligence_team. 7-day cooldown per listing."
    ),
)

# ── RK — fatigue language → RESCORE supply_intelligence_team ──────────────

RK = TriggerRule(
    rule_id="RK__private_remarks_fatigue_language__rescore",
    event_type="listing_private_remarks_signal_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.RESCORE,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: "fatigue_language" in (e.payload.get("detected_categories") or []),
    cooldown_seconds=_REMARKS_FATIGUE_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"remarks_fatigue:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "listing_private_remarks_signal_detected with fatigue_language → "
        "RESCORE supply_intelligence_team. 24-hour cooldown per listing."
    ),
)

# ── RL — agent land accumulation → cluster rescan ─────────────────────────

RL = TriggerRule(
    rule_id="RL__agent_land_accumulation_detected__cluster_rescan",
    event_type="agent_land_accumulation_detected",
    wake_target="cluster_detection_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_AGENT_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"agent_accumulation:{e.payload.get('list_agent_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "agent_land_accumulation_detected → RESCAN cluster_detection_agent. "
        "12-hour cooldown per agent key. Step 4.5 forward rule."
    ),
)

# ── RM — office land program → cluster rescan ─────────────────────────────

RM = TriggerRule(
    rule_id="RM__office_land_program_detected__cluster_rescan",
    event_type="office_land_program_detected",
    wake_target="cluster_detection_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_OFFICE_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"office_program:{e.payload.get('listing_office_id', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "office_land_program_detected → RESCAN cluster_detection_agent. "
        "12-hour cooldown per office id. Step 4.5 forward rule."
    ),
)

# ── RN1 — developer exit → cluster rescan ─────────────────────────────────

RN1 = TriggerRule(
    rule_id="RN1__developer_exit_signal_detected__cluster_rescan",
    event_type="developer_exit_signal_detected",
    wake_target="cluster_detection_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_DEV_EXIT_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"dev_exit_cluster:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "developer_exit_signal_detected → RESCAN cluster_detection_agent. "
        "48-hour cooldown per listing. Step 4.5 forward rule (RN fan-out leg 1)."
    ),
)

# ── RN2 — developer exit → supply intelligence rescore ───────────────────

RN2 = TriggerRule(
    rule_id="RN2__developer_exit_signal_detected__rescore_supply",
    event_type="developer_exit_signal_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.RESCORE,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_DEV_EXIT_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"dev_exit_supply:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "developer_exit_signal_detected → RESCORE supply_intelligence_team. "
        "48-hour cooldown per listing. Step 4.5 forward rule (RN fan-out leg 2)."
    ),
)

# ── RO — owner cluster detected → spark_signal_agent ─────────────────────

RO = TriggerRule(
    rule_id="RO__owner_cluster_detected__spark_signal_rescan",
    event_type="owner_cluster_detected",
    wake_target="spark_signal_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_CLUSTER_REVERSE_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"cluster_reverse:{e.payload.get('owner_key') or e.payload.get('cluster_id', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "owner_cluster_detected → RESCAN spark_signal_agent. "
        "Reverse routing: cluster signals wake BBO signal deepening. "
        "12-hour cooldown per owner/cluster. Step 4.5 reverse rule."
    ),
)

# ── RP — same owner listing detected → spark_signal_agent ─────────────────

RP = TriggerRule(
    rule_id="RP__same_owner_listing_detected__spark_signal_rescan",
    event_type="same_owner_listing_detected",
    wake_target="spark_signal_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_SAME_OWNER_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"same_owner_reverse:{e.payload.get('owner_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "same_owner_listing_detected → RESCAN spark_signal_agent. "
        "Reverse routing: same-owner signal deepens BBO analysis. "
        "6-hour cooldown per owner key. Step 4.5 reverse rule."
    ),
)

# ── RQ — parcel score high → spark_signal_agent ───────────────────────────

RQ = TriggerRule(
    rule_id="RQ__parcel_score_updated_high__spark_signal_rescan",
    event_type="parcel_score_updated",
    wake_target="spark_signal_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: float(e.payload.get("new_score", 0) or 0) >= 0.70,
    cooldown_seconds=_PARCEL_SCORE_REVERSE_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"parcel_score_high:{e.payload.get('regrid_id', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "parcel_score_updated with new_score >= 0.70 → RESCAN spark_signal_agent. "
        "Reverse routing: high-scoring parcels trigger deeper BBO scan. "
        "24-hour cooldown per parcel. Step 4.5 reverse rule."
    ),
)

# ── RR — parcel owner resolved → spark_signal_agent ──────────────────────

RR = TriggerRule(
    rule_id="RR__parcel_owner_resolved__spark_signal_rescan",
    event_type="parcel_owner_resolved",
    wake_target="spark_signal_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=5,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_PARCEL_OWNER_REVERSE_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"parcel_owner_reverse:{e.payload.get('regrid_id', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "parcel_owner_resolved → RESCAN spark_signal_agent. "
        "Reverse routing: owner resolution triggers BBO signal scan on related listings. "
        "48-hour cooldown per parcel. Step 4.5 reverse rule."
    ),
)

# ── RS — developer exit → opportunity_creation_agent ─────────────────────

RS = TriggerRule(
    rule_id="RS__developer_exit_signal_detected__opportunity_rescan",
    event_type="developer_exit_signal_detected",
    wake_target="opportunity_creation_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_OPPORTUNITY_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"dev_exit_opportunity:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "developer_exit_signal_detected → RESCAN opportunity_creation_agent. "
        "48-hour cooldown per listing. Opportunity routing rule RS."
    ),
)

# ── RT — subdivision remnant → opportunity_creation_agent ─────────────────

RT = TriggerRule(
    rule_id="RT__subdivision_remnant_detected__opportunity_rescan",
    event_type="subdivision_remnant_detected",
    wake_target="opportunity_creation_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_SUBDIVISION_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"subdivision_opportunity:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "subdivision_remnant_detected → RESCAN opportunity_creation_agent. "
        "72-hour cooldown per listing. Opportunity routing rule RT."
    ),
)

# ── RU1 — cluster threshold → opportunity_creation_agent ──────────────────

RU1 = TriggerRule(
    rule_id="RU1__owner_cluster_size_threshold_crossed__opportunity_rescan",
    event_type="owner_cluster_size_threshold_crossed",
    wake_target="opportunity_creation_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=3,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_CLUSTER_THRESHOLD_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"cluster_threshold_opportunity:{e.payload.get('owner_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "owner_cluster_size_threshold_crossed → RESCAN opportunity_creation_agent. "
        "72-hour cooldown per owner key. Opportunity routing rule RU (leg 1)."
    ),
)

# ── RU2 — cluster threshold → municipal_agent ─────────────────────────────

RU2 = TriggerRule(
    rule_id="RU2__owner_cluster_size_threshold_crossed__municipal_rescan",
    event_type="owner_cluster_size_threshold_crossed",
    wake_target="municipal_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=3,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_CLUSTER_THRESHOLD_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"cluster_threshold_municipal:{e.payload.get('owner_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "owner_cluster_size_threshold_crossed → RESCAN municipal_agent. "
        "72-hour cooldown per owner key. Opportunity routing rule RU (leg 2)."
    ),
)

# ── RY — listing_relisted → cluster rescan + seller intent rescore ────────
# A relist is one of the strongest seller-intent signals: the owner tried
# to sell, failed (expired/withdrawn/canceled), and is trying again.

RY = TriggerRule(
    rule_id="RY__listing_relisted__seller_intent_rescore",
    event_type="listing_relisted",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.RESCORE,
    phase=PhaseGate.PHASE_1,
    priority=3,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_RELIST_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"relist_rescore:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "listing_relisted → RESCORE supply_intelligence_team. "
        "Strong seller-intent signal: owner tried to exit, failed, relisted. "
        "24-hour cooldown per listing."
    ),
)

# ── RZ1 — listing_relisted → cluster expansion ──────────────────────────
# A relist should also trigger cluster expansion: find more lots from the
# same owner or subdivision.

RZ1 = TriggerRule(
    rule_id="RZ1__listing_relisted__cluster_expansion",
    event_type="listing_relisted",
    wake_target="cluster_detection_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: True,
    cooldown_seconds=_RELIST_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"relist_cluster:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "listing_relisted → RESCAN cluster_detection_agent. "
        "Owner re-entering market triggers cluster expansion search. "
        "24-hour cooldown per listing."
    ),
)

# ── RZ2 — distress language → opportunity rescore ────────────────────────

RZ2 = TriggerRule(
    rule_id="RZ2__private_remarks_distress_language__rescore",
    event_type="listing_private_remarks_signal_detected",
    wake_target="supply_intelligence_team",
    wake_type=WakeType.RESCORE,
    phase=PhaseGate.PHASE_1,
    priority=3,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: "distress_language" in (e.payload.get("detected_categories") or []),
    cooldown_seconds=_DISTRESS_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"remarks_distress:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "listing_private_remarks_signal_detected with distress_language → "
        "RESCORE supply_intelligence_team. 7-day cooldown per listing. "
        "As-is, estate sale, foreclosure, below market = high urgency."
    ),
)

# ── RZ3 — infrastructure/development ready → opportunity rescan ──────────

RZ3 = TriggerRule(
    rule_id="RZ3__remarks_infrastructure_ready__opportunity_rescan",
    event_type="listing_private_remarks_signal_detected",
    wake_target="opportunity_creation_agent",
    wake_type=WakeType.RESCAN,
    phase=PhaseGate.PHASE_1,
    priority=4,
    routing_class=RoutingClass.STANDARD,
    condition=lambda e, ctx: bool(
        {"infrastructure_ready", "development_ready"} & set(e.payload.get("detected_categories") or [])
    ),
    cooldown_seconds=_DISTRESS_COOLDOWN,
    cooldown_key_builder=lambda e, ctx: (
        f"remarks_infra:{e.payload.get('listing_key', '')}"
    ),
    raw_event_bypasses_cooldown=False,
    materiality_threshold=None,
    description=(
        "listing_private_remarks_signal_detected with infrastructure_ready or "
        "development_ready → RESCAN opportunity_creation_agent. "
        "7-day cooldown per listing. Confirmed infrastructure = actionable lot."
    ),
)
