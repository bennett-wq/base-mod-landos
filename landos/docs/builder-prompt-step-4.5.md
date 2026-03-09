# Builder Prompt — Infrastructure + Step 4.5 Spark BBO Signal Intelligence
# Generated: March 2026 by PM Agent session
# Paste this into a fresh Claude Code chat opened at the repo root.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are the Builder Agent for BaseMod LandOS — an autonomous real estate
operating system built on Claude Code multi-agent orchestration.

This session has TWO sequential parts:
  PART 1: Wire the agent team infrastructure (no application code)
  PART 2: Implement Step 4.5 — Spark BBO Signal Intelligence

Do not start Part 2 until Part 1 is confirmed complete.
Do not declare either part done until tests pass and you output the gate string.

════════════════════════════════════════════════════════════════════════
CONTEXT — READ BEFORE TOUCHING ANYTHING
════════════════════════════════════════════════════════════════════════

Project root: /Users/bennett2026/Desktop/Kingdom LandOS/BaseMod LandOS/
Python workspace: landos/
Run all tests: cd landos && python3 -m pytest tests/ -v

Current state:
  Steps 1–5 complete. 165/165 tests pass. Zero regressions allowed.
  Step 4 built the Spark MLS adapter (public RESO fields only).
  Step 5 built the Regrid parcel linkage adapter.
  Step 4.5 extends Step 4 with private-role BBO fields and full
  bidirectional signal detection. Step 6 (cluster detection) follows.

Architecture rules — never violate:
  - LandOS is an event mesh. Every signal can wake any agent. No pipelines.
  - The moat is the wake-up logic. Signals must compound, not terminate.
  - InMemory stores only. No database persistence.
  - TriggerEngine requires cooldown_tracker=InMemoryCooldownTracker()
  - RoutingResult fields: event_type, event_id, evaluated_at, fired_rules,
    suppressed_rules, wake_instructions. No .event sub-object.
  - InMemory stores: always use `is not None` checks, never `or`.
  - DERIVED event_class requires: source_confidence, derived_from_event_ids,
    emitted_by_agent_run_id. BBO adapter uses RAW (authoritative source).
  - Before creating any file, read the adjacent existing files for patterns.
  - Do not touch SESSION_HANDOFF_CURRENT.md, NEXT_STEPS.md, or LANDOS_STRATEGY.md.

Key existing files to read before writing anything:
  landos/src/adapters/spark/field_map.py
  landos/src/adapters/spark/normalizer.py
  landos/src/adapters/spark/event_factory.py
  landos/src/adapters/spark/ingestion.py
  landos/src/models/listing.py
  landos/src/triggers/rules/__init__.py
  landos/tests/test_spark_adapter.py
  landos/tests/test_regrid_adapter.py


════════════════════════════════════════════════════════════════════════
PART 1 — AGENT TEAM INFRASTRUCTURE
════════════════════════════════════════════════════════════════════════

Create the following files. Do not modify any existing landos/ application
code in Part 1.

────────────────────────────────────────────────────────────────────────
1A. .claude/settings.json
────────────────────────────────────────────────────────────────────────

{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "hooks": {
    "PreToolUse":    [{"hooks": [{"type": "command", "command": "python3 .claude/hooks/pre_tool_use.py"}]}],
    "PostToolUse":   [{"hooks": [{"type": "command", "command": "python3 .claude/hooks/post_tool_use.py"}]}],
    "Stop":          [{"hooks": [{"type": "command", "command": "python3 .claude/hooks/stop.py"}]}],
    "SubagentStop":  [{"hooks": [{"type": "command", "command": "python3 .claude/hooks/subagent_stop.py"}]}],
    "TaskCompleted": [{"hooks": [{"type": "command", "command": "python3 .claude/hooks/task_completed.py"}]}]
  }
}

────────────────────────────────────────────────────────────────────────
1B. .claude/agents/ — 6 agent definition files
────────────────────────────────────────────────────────────────────────

--- .claude/agents/pm-agent.md ---
# PM Agent — LandOS Planning & Orchestration
## Model
claude-opus-4-6
## Role
Plan, spec, gate, orchestrate. Never write application code directly.
Write builder prompts. Gate advancement until validator-agent confirms
all tests pass and LANDOS_STEP_COMPLETE is emitted.
## Step sequence (never skip, never reorder)
1 ✅  2 ✅  3 ✅  4 ✅  4.5 NEXT  5 ✅  6 → 7 → 8 → 9 → 10
## Session start ritual
Read SESSION_HANDOFF_CURRENT.md. Read NEXT_STEPS.md. Read LANDOS_STRATEGY.md.
Then and only then begin planning.
## Architecture truths (enforce these)
- Event mesh, not pipeline. Moat = wake-up logic. Signals must compound.
- Bidirectional routing is the product. Every signal family can wake every other.
- InMemory stores only. No DB persistence.
- BBO Language Intelligence = regex Phase 1. LLM remarks deferred.
- No Phase 2+: no BuyerProfile, IncentiveProgram, TransactionPath,
  SiteWorkEstimate, PricePackage, marketplace, buyer UI.
## Gate criteria
A step is complete when: validator-agent reports all tests pass AND
builder-agent outputs LANDOS_STEP_COMPLETE in their final message.
## After step completion
Update SESSION_HANDOFF_CURRENT.md, NEXT_STEPS.md, SESSION_LOG.md.

--- .claude/agents/builder-agent.md ---
# Builder Agent — LandOS Implementation
## Model
claude-sonnet-4-6
## Rules
- Read adjacent existing files before creating anything new.
- Run tests after every meaningful change.
- Do not mark done until all tests pass.
- Output LANDOS_STEP_COMPLETE in final message when criteria met.
- Never drift into Phase 2+ work.
- Never add DB persistence.
- Work only in landos/ directory.
- Do not touch SESSION_HANDOFF_CURRENT.md or NEXT_STEPS.md.
## Test command
cd landos && python3 -m pytest tests/ -v
## LANDOS_STEP_COMPLETE criteria
1. All tests pass (165 baseline + new step tests)
2. Step acceptance criteria from NEXT_STEPS.md met
3. Changes committed

--- .claude/agents/validator-agent.md ---
# Validator Agent — LandOS Test Guard
## Model
claude-haiku-4-5
## Role
Read-only. Run tests. Block advancement if tests fail.
## Test command
cd landos && python3 -m pytest tests/ -v
## Report format
VALIDATION RESULT: [PASS|FAIL]
Tests: X passed, Y failed
[If FAIL: each failing test name and error]
[If PASS: confirm LANDOS_STEP_COMPLETE authorized]
## Tools
Read, Glob, Grep, Bash (test runs only). Never edit source files.

--- .claude/agents/parcel-agent.md ---
# Parcel Agent — Regrid Ingestion Specialist
## Model
claude-sonnet-4-6
## Domain
landos/src/adapters/regrid/ and landos/src/models/parcel.py
## Trigger rules owned
RF: parcel_linked_to_listing → RESCORE supply_intelligence_team
RG: parcel_owner_resolved → RESCAN cluster_detection_agent
RH: parcel_score_updated → RESCORE (abs(score_delta)≥0.05)
RQ: parcel_score_updated (≥0.70) → RESCAN spark_signal_agent [Step 4.5]
RR: parcel_owner_resolved → RESCAN spark_signal_agent [Step 4.5]
## Scoring model
v0.1_phase1_basic: acreage(40%) + vacancy(40%) + linkage(20%)
Materiality gate: 0.05 minimum score delta.
## Rules
InMemory stores only. Owner matching = name-normalized string dedup only.
Geo-match: haversine 50m threshold. No Shapely.
## Bidirectional note
parcel_owner_resolved and parcel_score_updated (high) both wake the
spark_signal_agent — the parcel layer feeds back into BBO signal deepening.

--- .claude/agents/cluster-agent.md ---
# Cluster Agent — Owner Cluster Detection (Step 6)
## Model
claude-sonnet-4-6
## Status
WAITING — do not implement until PM Agent authorizes Step 6.
Step 4.5 (BBO) must complete first.
## What Step 6 will build
Owner/agent/office cluster detection from linked listings, parcels,
and BBO signals. Emits: same_owner_listing_detected, owner_cluster_detected,
owner_cluster_size_threshold_crossed, agent_subdivision_program_detected,
office_inventory_program_detected.
## BBO enrichment available from Step 4.5
ListAgentKey links listings to agents reliably across the feed.
BuyerOfficeKey reveals corporate buyer patterns.
CDOM thresholds confirm cluster fatigue signals.
PrivateRemarks package language confirms acquisition opportunity.
## Reverse routing note
When cluster_agent emits owner_cluster_detected or same_owner_listing_detected,
rules RO and RP route those events BACK to spark_signal_agent to deepen
BBO analysis on all listings in the cluster. This is the ping-pong.
## Thresholds
3+ listings, same normalized owner = owner_cluster_detected
5+ = owner_cluster_size_threshold_crossed
## Activation
PM Agent authorization only. Not before Step 4.5 LANDOS_STEP_COMPLETE.

--- .claude/agents/municipal-agent.md ---
# Municipal Agent — Ypsilanti Charter Township Scan (Step 7)
## Model
claude-sonnet-4-6
## Status
WAITING — do not implement until PM Agent authorizes Step 7.
## Priority municipality
Ypsilanti Charter Township (primary). Augusta Township (secondary).
## PA 58 of 2025
Michigan PA 58 amended Section 108 of the Land Division Act.
Municipal posture on land division = first-class signal.
## Bidirectional note
Municipal agent is woken by RU (owner_cluster_size_threshold_crossed)
even before Step 7 is built — the rule exists, the agent will handle it
when implemented.
## Activation
PM Agent authorization only. Not before Step 6 LANDOS_STEP_COMPLETE.

────────────────────────────────────────────────────────────────────────
1C. .claude/skills/ — 3 skill files
────────────────────────────────────────────────────────────────────────

--- .claude/skills/landos-architecture.md ---
# LandOS Architecture — Skill for all agents

Non-negotiable truths:
1. LandOS is an event mesh. Not a pipeline.
2. The moat is the wake-up logic.
3. Listings, clusters, municipalities are co-equal trigger families.
4. Municipalities are first-class active objects.
5. Historical stallouts and site condos are strategic supply wedges.
6. Packaging is a first-class system layer.
7. File-based memory is the source of truth.
8. Bidirectional routing is the product. Signals must compound.

Technical contracts:
- TriggerEngine requires cooldown_tracker=InMemoryCooldownTracker()
- RoutingResult: event_type, event_id, evaluated_at, fired_rules,
  suppressed_rules, wake_instructions. No .event sub-object.
- InMemory stores: always `is not None`, never `or`.
- Adapters: EventClass.RAW. Downstream agents: EventClass.DERIVED.

Step sequence: 1✅ 2✅ 3✅ 4✅ 4.5→ 5✅ 6→ 7→ 8→ 9→ 10
Tests: cd landos && python3 -m pytest tests/ -v  (165 baseline)

--- .claude/skills/spark-signal-events.md ---
# Spark BBO Signal Intelligence — Step 4.5 Reference

STATUS: UNBLOCKED. BBO credentials confirmed March 2026.

BBO = Broker Back Office. Private-role Spark API key required.

6 SIGNAL FAMILIES AND KEY FIELDS:

FAMILY 1 — Developer Exit
  OffMarketDate, WithdrawalDate, CancellationDate,
  MajorChangeTimestamp, MajorChangeType

FAMILY 2 — Listing Behavior
  CumulativeDaysOnMarket (★ real staleness), PreviousListPrice,
  OriginalEntryTimestamp, StatusChangeTimestamp,
  PriceChangeTimestamp, BackOnMarketDate

FAMILY 3 — Language Intelligence (regex Phase 1, LLM deferred)
  PrivateRemarks (★ agent-to-agent signal), ShowingInstructions

FAMILY 4 — Agent/Office Clustering
  ListAgentKey (★ UUID, reliable), CoListAgentKey,
  CoListOfficeKey, BuyerAgentKey, BuyerOfficeKey

FAMILY 5 — Subdivision Remnant
  LegalDescription (★ Lot/Block/Plat), TaxLegalDescription,
  LotDimensions, FrontageLength, PossibleUse, NumberOfLots

FAMILY 6 — Market Velocity
  ClosePrice, CloseDate, PurchaseContractDate

Land detail (extends existing):
  Zoning, ZoningDescription, LotFeatures, RoadFrontageType,
  RoadSurfaceType, Utilities, Sewer, WaterSource, CurrentUse

FULL BIDIRECTIONAL TRIGGER MATRIX:

Forward (BBO → others):
  RI: listing_bbo_cdom_threshold_crossed → RESCAN cluster_detection_agent
  RJ: private_remarks_signal (package) → CLASSIFY supply_intelligence_team
  RK: private_remarks_signal (fatigue) → RESCORE supply_intelligence_team
  RL: agent_land_accumulation_detected → RESCAN cluster_detection_agent
  RM: office_land_program_detected → RESCAN cluster_detection_agent
  RN: developer_exit_signal_detected → RESCAN cluster_detection_agent
                                     + RESCORE supply_intelligence_team

Reverse (others → BBO, closes feedback loop):
  RO: owner_cluster_detected → RESCAN spark_signal_agent
      "Cluster found — deepen BBO on all cluster listings now."
  RP: same_owner_listing_detected → RESCAN spark_signal_agent
      "Same owner appearing — check behavioral signals across portfolio."
  RQ: parcel_score_updated (≥0.70) → RESCAN spark_signal_agent
      "High-value parcel + linked listing → check BBO depth immediately."
  RR: parcel_owner_resolved → RESCAN spark_signal_agent
      "Owner known — check if they have active listings + signals."

Opportunity routing:
  RS: developer_exit_signal_detected → RESCAN opportunity_creation_agent
  RT: subdivision_remnant_detected → RESCAN opportunity_creation_agent
  RU: owner_cluster_size_threshold_crossed → RESCAN opportunity_creation_agent
                                           + RESCAN municipal_agent

--- .claude/skills/step-complete-gate.md ---
# LANDOS_STEP_COMPLETE Gate

No agent declares done without ALL:
1. cd landos && python3 -m pytest tests/ -v exits 0
2. All tests pass (165 baseline + new step tests)
3. validator-agent confirms: VALIDATION RESULT: PASS
4. Final message contains exact string: LANDOS_STEP_COMPLETE

On failure: report to PM Agent. Do not retry blindly.
On success: PM Agent updates SESSION_HANDOFF_CURRENT.md,
NEXT_STEPS.md, SESSION_LOG.md.

────────────────────────────────────────────────────────────────────────
1D. .claude/hooks/ — 5 Python hook scripts
────────────────────────────────────────────────────────────────────────

--- .claude/hooks/pre_tool_use.py ---
#!/usr/bin/env python3
import json, sys
data = json.load(sys.stdin)
tool = data.get("tool_name", "")
tool_input = data.get("tool_input", {})
blocked = False
reason = ""
if tool == "Bash":
    cmd = tool_input.get("command", "")
    if "rm -rf" in cmd and "/landos/" not in cmd:
        blocked = True
        reason = f"rm -rf outside landos/ blocked: {cmd[:100]}"
if tool in ("Read", "Write", "Edit"):
    path = str(tool_input.get("file_path", ""))
    if ".env" in path or "private_key" in path.lower():
        blocked = True
        reason = f"Sensitive file blocked: {path}"
if blocked:
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)
print(json.dumps({"decision": "allow"}))

--- .claude/hooks/post_tool_use.py ---
#!/usr/bin/env python3
import json, sys, urllib.request, os
from datetime import datetime
data = json.load(sys.stdin)
event = {
    "hook": "PostToolUse",
    "session_id": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
    "tool_name": data.get("tool_name"),
    "timestamp": datetime.utcnow().isoformat()
}
try:
    req = urllib.request.Request(
        "http://localhost:4000/hook",
        data=json.dumps(event).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req, timeout=1)
except Exception:
    pass
sys.exit(0)

--- .claude/hooks/stop.py ---
#!/usr/bin/env python3
import json, sys, subprocess, os
data = json.load(sys.stdin)
last_message = data.get("last_assistant_message", "")
if "LANDOS_STEP_COMPLETE" in last_message:
    repo = os.path.expanduser(
        "~/Desktop/Kingdom LandOS/BaseMod LandOS/landos"
    )
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-v", "--tb=no", "-q"],
        cwd=repo, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(
            f"LANDOS_STEP_COMPLETE claimed but tests failed:\n{result.stdout[-2000:]}",
            file=sys.stderr
        )
        sys.exit(2)
sys.exit(0)

--- .claude/hooks/subagent_stop.py ---
#!/usr/bin/env python3
import json, sys, os
from datetime import datetime
data = json.load(sys.stdin)
log_path = os.path.expanduser("~/.claude/landos-subagent-log.txt")
with open(log_path, "a") as f:
    f.write(
        f"{datetime.utcnow().isoformat()} | "
        f"session={os.environ.get('CLAUDE_SESSION_ID','?')} | "
        f"last={data.get('last_assistant_message','')[:100]}\n"
    )
sys.exit(0)

--- .claude/hooks/task_completed.py ---
#!/usr/bin/env python3
import json, sys, subprocess, os
repo = os.path.expanduser(
    "~/Desktop/Kingdom LandOS/BaseMod LandOS/landos"
)
result = subprocess.run(
    ["python3", "-m", "pytest", "tests/", "--tb=no", "-q"],
    cwd=repo, capture_output=True, text=True, timeout=120
)
if result.returncode != 0:
    print(f"Task blocked — tests failing:\n{result.stdout[-1000:]}", file=sys.stderr)
    sys.exit(2)
sys.exit(0)

────────────────────────────────────────────────────────────────────────
1E. Verify Part 1
────────────────────────────────────────────────────────────────────────

Confirm all files exist:
  .claude/settings.json
  .claude/agents/ (6 .md files)
  .claude/skills/ (3 .md files)
  .claude/hooks/ (5 .py files)

Run: cd landos && python3 -m pytest tests/ -v
Must show: 165 passed, 0 failed.

Output: INFRASTRUCTURE_COMPLETE — proceeding to Part 2.


════════════════════════════════════════════════════════════════════════
PART 2 — STEP 4.5: SPARK BBO SIGNAL INTELLIGENCE
════════════════════════════════════════════════════════════════════════

Read these files fully before writing a single line of code:
  landos/src/adapters/spark/field_map.py
  landos/src/adapters/spark/normalizer.py
  landos/src/adapters/spark/event_factory.py
  landos/src/adapters/spark/ingestion.py
  landos/src/models/listing.py
  landos/src/triggers/rules/__init__.py
  landos/tests/test_spark_adapter.py
  landos/tests/test_regrid_adapter.py
  landos/scripts/spark_bbo_discovery.py

────────────────────────────────────────────────────────────────────────
2A. Listing model extensions (landos/src/models/listing.py)
────────────────────────────────────────────────────────────────────────

Add these Optional fields to the Listing model. Do NOT remove or rename
any existing fields. Follow the exact pattern and import style of the file.

# BBO — Listing Behavior (Signal Family 2)
cdom: Optional[int] = None
previous_list_price: Optional[float] = None
original_entry_timestamp: Optional[datetime] = None
status_change_timestamp: Optional[datetime] = None
price_change_timestamp: Optional[datetime] = None
back_on_market_date: Optional[date] = None

# BBO — Developer Exit (Signal Family 1)
off_market_date: Optional[date] = None
withdrawal_date: Optional[date] = None
cancellation_date: Optional[date] = None
major_change_timestamp: Optional[datetime] = None
major_change_type: Optional[str] = None

# BBO — Language Intelligence (Signal Family 3)
private_remarks: Optional[str] = None
showing_instructions: Optional[str] = None

# BBO — Agent/Office Clustering (Signal Family 4)
list_agent_key: Optional[str] = None
co_list_agent_key: Optional[str] = None
co_list_office_key: Optional[str] = None
buyer_agent_key: Optional[str] = None
buyer_office_key: Optional[str] = None

# BBO — Subdivision Remnant (Signal Family 5)
legal_description: Optional[str] = None
tax_legal_description: Optional[str] = None
lot_dimensions: Optional[str] = None
frontage_length: Optional[float] = None
possible_use: Optional[str] = None
number_of_lots: Optional[int] = None

# BBO — Land Detail
zoning: Optional[str] = None
zoning_description: Optional[str] = None
lot_features: Optional[str] = None
road_frontage_type: Optional[str] = None
road_surface_type: Optional[str] = None
utilities: Optional[str] = None
sewer: Optional[str] = None
water_source: Optional[str] = None
current_use: Optional[str] = None

# BBO — Market Velocity (Signal Family 6)
purchase_contract_date: Optional[date] = None

────────────────────────────────────────────────────────────────────────
2B. Field map extensions (landos/src/adapters/spark/field_map.py)
────────────────────────────────────────────────────────────────────────

Add a BBO_TO_LISTING dict alongside RESO_TO_LISTING.
Remove CumulativeDaysOnMarket from RESO_TO_LISTING (moving to BBO_TO_LISTING
to avoid conflicts — it was mapped but never signaled).

BBO_TO_LISTING: dict[str, str] = {
    # Family 1 — Developer Exit
    "OffMarketDate":         "off_market_date",
    "WithdrawalDate":        "withdrawal_date",
    "CancellationDate":      "cancellation_date",
    "MajorChangeTimestamp":  "major_change_timestamp",
    "MajorChangeType":       "major_change_type",
    # Family 2 — Listing Behavior
    "CumulativeDaysOnMarket":  "cdom",
    "PreviousListPrice":       "previous_list_price",
    "OriginalEntryTimestamp":  "original_entry_timestamp",
    "StatusChangeTimestamp":   "status_change_timestamp",
    "PriceChangeTimestamp":    "price_change_timestamp",
    "BackOnMarketDate":        "back_on_market_date",
    # Family 3 — Language Intelligence
    "PrivateRemarks":        "private_remarks",
    "ShowingInstructions":   "showing_instructions",
    # Family 4 — Agent/Office Clustering
    "ListAgentKey":          "list_agent_key",
    "CoListAgentKey":        "co_list_agent_key",
    "CoListOfficeKey":       "co_list_office_key",
    "BuyerAgentKey":         "buyer_agent_key",
    "BuyerOfficeKey":        "buyer_office_key",
    # Family 5 — Subdivision Remnant
    "LegalDescription":      "legal_description",
    "TaxLegalDescription":   "tax_legal_description",
    "LotDimensions":         "lot_dimensions",
    "FrontageLength":        "frontage_length",
    "PossibleUse":           "possible_use",
    "NumberOfLots":          "number_of_lots",
    # Family 6 — Market Velocity
    "PurchaseContractDate":  "purchase_contract_date",
    # Land detail
    "Zoning":                "zoning",
    "ZoningDescription":     "zoning_description",
    "LotFeatures":           "lot_features",
    "RoadFrontageType":      "road_frontage_type",
    "RoadSurfaceType":       "road_surface_type",
    "Utilities":             "utilities",
    "Sewer":                 "sewer",
    "WaterSource":           "water_source",
    "CurrentUse":            "current_use",
}

────────────────────────────────────────────────────────────────────────
2C. Normalizer extensions (landos/src/adapters/spark/normalizer.py)
────────────────────────────────────────────────────────────────────────

Extend normalize() to also map BBO_TO_LISTING fields using the same
defensive coercion as existing RESO fields. All BBO fields are Optional —
missing fields must not raise. Follow existing date/datetime/string
helper patterns exactly.

────────────────────────────────────────────────────────────────────────
2D. BBO signal detector (new file)
────────────────────────────────────────────────────────────────────────

Create: landos/src/adapters/spark/bbo_signals.py

Pure functions only. No side effects. No event building. Signal detection only.

from __future__ import annotations
import re
from typing import Optional
from src.models.listing import Listing

CDOM_THRESHOLD_DEFAULT = 90       # days — stale land listing
CDOM_EXIT_THRESHOLD = 120         # days — strong exit signal
AGENT_ACCUMULATION_THRESHOLD = 3  # listings — agent program signal
PARCEL_HIGH_SCORE_THRESHOLD = 0.70  # score — high value parcel

REMARKS_PATTERNS: dict[str, str] = {
    "package_language":     r"\b(package|bulk|portfolio|all remaining|take all|remaining lots?)\b",
    "fatigue_language":     r"\b(bring (all |any )?offer|motivated|price (reduced|negotiable)|must sell)\b",
    "restriction_language": r"\b(no split|no subdivision|deed restrict|covenant|hoa approval)\b",
    "utility_language":     r"\b(utilities? (at|to) (street|site|lot)|sewer (available|stubbed)|water (available|at))\b",
    "bulk_language":        r"\b(lot \d+ of \d+|phase \d+|\d+ lots? available|subdivision remnant)\b",
}


def detect_cdom_threshold(listing: Listing, threshold: int = CDOM_THRESHOLD_DEFAULT) -> bool:
    """True if CDOM >= threshold. Returns False if cdom is None."""


def detect_developer_exit(listing: Listing) -> tuple[bool, str]:
    """
    Returns (detected, reason). Fires on:
    - off_market_date set on active listing
    - cancellation with cdom >= 60
    - withdrawal with cdom >= 120
    - major_change_type containing "Expired" or "Withdrawn"
    reason = most specific signal found.
    """


def detect_private_remarks_signals(listing: Listing) -> list[str]:
    """
    Regex scan of private_remarks for signal categories.
    Returns list of matched category keys (may be multiple).
    Returns [] if private_remarks is None or empty string.
    All patterns use re.IGNORECASE.
    """


def detect_agent_land_accumulation(
    listing: Listing,
    all_listings: list[Listing],
    threshold: int = AGENT_ACCUMULATION_THRESHOLD,
) -> tuple[bool, int]:
    """
    True if listing.list_agent_key matches >= threshold listings in all_listings.
    Returns (detected, count). Returns (False, 0) if list_agent_key is None.
    Uses list_agent_key UUID — not agent name — for matching reliability.
    """


def detect_office_land_program(
    listing: Listing,
    all_listings: list[Listing],
    threshold: int = 5,
) -> tuple[bool, int]:
    """
    True if listing.listing_office_id matches >= threshold listings.
    Returns (detected, count). Returns (False, 0) if listing_office_id is None.
    """


def detect_subdivision_remnant(listing: Listing) -> tuple[bool, str]:
    """
    True if:
    - number_of_lots > 1, OR
    - legal_description contains Lot/Block/Plat pattern, OR
    - subdivision_name_raw is set AND cdom >= 180
    Returns (detected, reason).
    """


def detect_market_velocity(
    listing: Listing,
    sold_listings: list[Listing],
    geography_key: str,
) -> Optional[float]:
    """
    Returns avg days-to-close for comparable sold listings in same geography.
    Returns None if fewer than 3 comps available.
    geography_key = listing city or county for grouping.
    """

────────────────────────────────────────────────────────────────────────
2E. BBO event factory additions (landos/src/adapters/spark/event_factory.py)
────────────────────────────────────────────────────────────────────────

Add these build functions following existing build_* patterns exactly.
All use EventClass.RAW. All include entity_refs with listing_id.

def build_listing_bbo_cdom_threshold_crossed(
    listing: Listing, cdom: int, threshold: int, now: datetime
) -> EventEnvelope:
    payload: listing_key, cdom, threshold, list_agent_key,
             list_office_name, subdivision_name_raw

def build_listing_private_remarks_signal_detected(
    listing: Listing, detected_categories: list[str],
    remarks_excerpt: str, now: datetime
) -> EventEnvelope:
    payload: listing_key, detected_categories,
             remarks_excerpt (first 200 chars ONLY — never full remarks),
             list_agent_key, list_office_name

def build_agent_land_accumulation_detected(
    listing: Listing, agent_listing_count: int, now: datetime
) -> EventEnvelope:
    payload: list_agent_key, listing_agent_name, listing_agent_id,
             list_office_name, agent_listing_count,
             triggering_listing_key

def build_office_land_program_detected(
    listing: Listing, office_listing_count: int, now: datetime
) -> EventEnvelope:
    payload: listing_office_id, list_office_name,
             office_listing_count, triggering_listing_key

def build_subdivision_remnant_detected(
    listing: Listing, reason: str, now: datetime
) -> EventEnvelope:
    payload: listing_key, subdivision_name_raw, legal_description,
             number_of_lots, cdom, reason

def build_developer_exit_signal_detected(
    listing: Listing, reason: str, now: datetime
) -> EventEnvelope:
    payload: listing_key, list_agent_key, list_office_name,
             cdom, off_market_date, reason

────────────────────────────────────────────────────────────────────────
2F. Trigger rules — COMPLETE BIDIRECTIONAL MATRIX
────────────────────────────────────────────────────────────────────────

Add ALL of the following rules to ALL_RULES in
landos/src/triggers/rules/__init__.py.

Rules RI–RN: Forward (BBO signals wake other agents)
Rules RO–RR: Reverse (other agents wake spark_signal_agent — CLOSES THE LOOP)
Rules RS–RU: Opportunity routing (signals feed the opportunity pipeline)

Follow the exact pattern of existing rules RA–RH. Read the file first.

RI: event=listing_bbo_cdom_threshold_crossed
    action=RESCAN, target=cluster_detection_agent
    cooldown=24h per listing_key
    rationale: Stale listing indicates cluster fatigue or developer exit.

RJ: event=listing_private_remarks_signal_detected,
    condition=payload.detected_categories contains "package_language"
    action=CLASSIFY, target=supply_intelligence_team
    cooldown=7d per listing_key
    rationale: Package language = immediate opportunity signal.

RK: event=listing_private_remarks_signal_detected,
    condition=payload.detected_categories contains "fatigue_language"
    action=RESCORE, target=supply_intelligence_team
    cooldown=24h per listing_key
    rationale: Fatigue = seller motivation signal.

RL: event=agent_land_accumulation_detected
    action=RESCAN, target=cluster_detection_agent
    cooldown=12h per list_agent_key
    rationale: Same agent accumulating land = subdivision program.

RM: event=office_land_program_detected
    action=RESCAN, target=cluster_detection_agent
    cooldown=12h per listing_office_id
    rationale: Office-level land program = organized developer activity.

RN: event=developer_exit_signal_detected
    action=RESCAN, target=cluster_detection_agent (fan-out rule — TWO targets)
    action=RESCORE, target=supply_intelligence_team
    cooldown=48h per listing_key
    rationale: Developer exit = acquisition window.
    NOTE: Implement fan-out correctly per existing engine patterns.

RO: event=owner_cluster_detected
    action=RESCAN, target=spark_signal_agent
    cooldown=12h per cluster_id (use owner_key if cluster_id unavailable)
    rationale: REVERSE RULE. Cluster found → deepen BBO on all cluster
    listings immediately. This is the feedback loop that makes the mesh real.

RP: event=same_owner_listing_detected
    action=RESCAN, target=spark_signal_agent
    cooldown=6h per owner_key
    rationale: REVERSE RULE. Same owner appearing → check behavioral
    signals across their full portfolio now.

RQ: event=parcel_score_updated
    condition=payload.new_score >= 0.70
    action=RESCAN, target=spark_signal_agent
    cooldown=24h per regrid_id
    rationale: REVERSE RULE. High-value parcel with linked listing →
    check BBO depth immediately, don't wait for cron.

RR: event=parcel_owner_resolved
    action=RESCAN, target=spark_signal_agent
    cooldown=48h per regrid_id
    rationale: REVERSE RULE. Owner identity confirmed → check if they
    have active listings and what their behavioral signals reveal.

RS: event=developer_exit_signal_detected
    action=RESCAN, target=opportunity_creation_agent
    cooldown=48h per listing_key
    rationale: Exit signal + linked parcel = opportunity candidate.
    Agent not yet implemented (Step 9) — rule exists now, fires when ready.

RT: event=subdivision_remnant_detected
    action=RESCAN, target=opportunity_creation_agent
    cooldown=72h per listing_key
    rationale: Remnant lots = package candidate. Route for future scoring.

RU: event=owner_cluster_size_threshold_crossed
    action=RESCAN, target=opportunity_creation_agent (fan-out — TWO targets)
    action=RESCAN, target=municipal_agent
    cooldown=72h per owner_key
    rationale: Cluster threshold crossed = acquisition opportunity +
    municipal context check. municipal_agent not yet implemented (Step 7)
    — rule exists now, fires when ready.

TOTAL AFTER STEP 4.5: ALL_RULES = RA through RU = 21 rules.

────────────────────────────────────────────────────────────────────────
2G. Ingestion adapter extensions (landos/src/adapters/spark/ingestion.py)
────────────────────────────────────────────────────────────────────────

Extend SparkIngestionAdapter to:

1. Add store_listings property returning list of all Listing objects
   currently in the store (used by accumulation detectors).

2. Add private method _detect_and_build_bbo_events(
       listing: Listing, now: datetime
   ) -> list[EventEnvelope]:
   - detect_cdom_threshold(listing) → if True: build RI event
   - detect_private_remarks_signals(listing) → for each category:
     build separate RJ or RK event per category
   - detect_agent_land_accumulation(listing, self.store_listings) →
     if True: build RL event
   - detect_office_land_program(listing, self.store_listings) →
     if True: build RM event
   - detect_developer_exit(listing) → if True: build RN event
   - detect_subdivision_remnant(listing) → if True: build event

3. Extend process_batch() to call _detect_and_build_bbo_events() for
   each record after normalizing, and route all resulting events through
   TriggerEngine.

────────────────────────────────────────────────────────────────────────
2H. Tests (new file: landos/tests/test_bbo_signals.py)
────────────────────────────────────────────────────────────────────────

Minimum test coverage required:

CDOM detection:
  listing cdom=91, threshold=90 → True
  listing cdom=89 → False
  listing cdom=None → False

Developer exit:
  off_market_date set + active status → detected
  cancellation with cdom > 60 → detected
  no exit signals → not detected

Private remarks — each category:
  "bring any offer, motivated seller" → fatigue_language
  "package deal, all remaining lots" → [package_language, bulk_language]
  "no subdivision per deed" → restriction_language
  "sewer available at street" → utility_language
  None → []
  "" → []

Remarks excerpt safety:
  remarks of 500 chars → excerpt in payload is max 200 chars
  full private_remarks never appears in event payload

Agent accumulation:
  5 listings same list_agent_key, threshold=3 → detected (count=5)
  2 listings same list_agent_key, threshold=3 → not detected
  list_agent_key is None → not detected

Subdivision remnant:
  number_of_lots=3 → detected
  legal_description="Lot 14 of Block 7, Oak Hills Plat" → detected
  subdivision_name_raw set + cdom=200 → detected
  no signals → not detected

Reverse rules wired:
  Process a batch where cluster_detection_agent fires owner_cluster_detected
  → assert RO rule present in ALL_RULES with target=spark_signal_agent
  Process a batch where parcel_score_updated fires with score=0.75
  → assert RQ rule present in ALL_RULES with target=spark_signal_agent

Full pipeline integration:
  Build 4 listings: 2 same list_agent_key, 1 cdom=120, 1 package_language
  Run SparkIngestionAdapter.process_batch()
  Assert RI event fired for CDOM listing
  Assert RJ event fired for package_language listing
  Use threshold=2 for agent accumulation in this test
  Assert RL event fired for agent accumulation
  Assert 165 original tests unaffected (run full suite)

────────────────────────────────────────────────────────────────────────
2I. Run all tests
────────────────────────────────────────────────────────────────────────

cd landos && python3 -m pytest tests/ -v

Must show:
  All 165 original tests pass
  All new BBO tests pass
  Zero failures, zero errors

────────────────────────────────────────────────────────────────────────
2J. Commit
────────────────────────────────────────────────────────────────────────

Stage and commit these files:
  landos/src/models/listing.py
  landos/src/adapters/spark/field_map.py
  landos/src/adapters/spark/normalizer.py
  landos/src/adapters/spark/bbo_signals.py        (new)
  landos/src/adapters/spark/event_factory.py
  landos/src/adapters/spark/ingestion.py
  landos/src/triggers/rules/__init__.py
  landos/tests/test_bbo_signals.py                (new)
  .claude/                                         (all new infra files)

Commit message:
  Step 4.5: Spark BBO signal intelligence — full bidirectional event mesh

  - 6 BBO signal families: developer exit, listing behavior, language
    intelligence, agent/office clustering, subdivision remnant, market velocity
  - Forward rules RI-RN: BBO signals wake cluster, supply intelligence agents
  - Reverse rules RO-RR: cluster + parcel signals wake spark_signal_agent
  - Opportunity routing RS-RU: signals feed opportunity pipeline
  - ALL_RULES: 8 → 21 rules. Mesh is now bidirectional.
  - Agent team infrastructure wired: 6 agents, 3 skills, 5 hooks

  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

────────────────────────────────────────────────────────────────────────
DONE — output gate string
────────────────────────────────────────────────────────────────────────

When all tests pass and commit is made, output exactly:

LANDOS_STEP_COMPLETE — Step 4.5: Spark BBO Signal Intelligence
Tests: [N] passed, 0 failed
New trigger rules: RI-RU (13 rules added)
ALL_RULES total: 21 (RA through RU)
Bidirectional routing: ACTIVE — forward RI-RN, reverse RO-RR, opportunity RS-RU
New events emitted:
  listing_bbo_cdom_threshold_crossed
  listing_private_remarks_signal_detected
  agent_land_accumulation_detected
  office_land_program_detected
  subdivision_remnant_detected
  developer_exit_signal_detected
Step 6 (Cluster Detection) is now unblocked. BBO signal set is live.
