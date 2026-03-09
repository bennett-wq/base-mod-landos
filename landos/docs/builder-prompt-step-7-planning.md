# Planning Prompt — Historical Listing Enrichment + Steps 7–10 Roadmap
# Generated: 2026-03-09
# Paste this into a fresh Claude Code chat opened at the repo root.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are the PM/Planning Agent for BaseMod LandOS — an autonomous real estate
operating system built on an event mesh architecture. This session has TWO parts:

  PART 1: Scope and implement Historical Listing Enrichment
  PART 2: Map the forward roadmap (Steps 7–10) based on real data insights

════════════════════════════════════════════════════════════════════════
CONTEXT — READ THESE FILES BEFORE DOING ANYTHING
════════════════════════════════════════════════════════════════════════

Start by reading:
  landos/docs/SESSION_HANDOFF_CURRENT.md   — current state, live data results
  landos/docs/LANDOS_DECISIONS_LOG.md      — locked architectural decisions
  landos/docs/SESSION_LOG.md               — session history
  landos/docs/builder-prompt-step-6.md     — Step 6 context (cluster detection)
  CLAUDE.md                                — non-negotiable architecture truths

Project root: /Users/bennett2026/Desktop/Kingdom LandOS/BaseMod LandOS/
Python workspace: landos/
Run all tests:
  python3 -m pytest "/Users/bennett2026/Desktop/Kingdom LandOS/BaseMod LandOS/landos/tests/" -v

**NEVER use `cd landos &&` — it corrupts the shell cwd and breaks hooks.**

Current state:
  Steps 1–6 + 4.5 complete. 237/237 tests pass. Zero regressions allowed.
  Live pipeline operational with real Washtenaw County data:
    - 95 active Spark MLS land listings
    - 10,266 vacant parcels from Regrid CSV
    - 2,229 parcel clusters (1,112 owner, 81 subdivision, 1,036 proximity)
    - 47 clusters with active listings
    - 23 Tier 1 high-convergence opportunities
    - 76 dormant supply clusters (22,057 acres) — Toll Brothers 146 lots,
      M/I Homes 99, Pulte 59

  Spark API: https://replication.sparkapi.com/Reso/OData/Property
  Auth: Bearer token from SPARK_API_KEY in .env
  OData filters work: $filter, $top, $orderby, PropertyType, StandardStatus,
  CountyOrParish

Architecture rules — never violate:
  - LandOS is an event mesh. Every signal can wake any agent. No pipelines.
  - The moat is the wake-up logic. Signals must compound, not terminate.
  - InMemory stores only. No database persistence.
  - Before creating any file, read adjacent existing files for patterns.
  - All decisions go in LANDOS_DECISIONS_LOG.md.

════════════════════════════════════════════════════════════════════════
PART 1 — HISTORICAL LISTING ENRICHMENT
════════════════════════════════════════════════════════════════════════

The insight: An owner who listed at $500K, sat 200 days, withdrew, and is
now relisting at $400K with "bring all offers" is a completely different
opportunity than a fresh listing at $400K. We need historical listing
behavior to unlock the deepest signals.

────────────────────────────────────────────────────────────────────────
1A. Historical Spark data pull
────────────────────────────────────────────────────────────────────────

Read landos/scripts/ingest_spark_live.py first — it has the working API client.

Extend fetch_listings() or create fetch_historical_listings() to also pull:
  - StandardStatus eq 'Expired'
  - StandardStatus eq 'Withdrawn'
  - StandardStatus eq 'Closed'
  - StandardStatus eq 'Canceled'

Same county filter (Washtenaw). Same PropertyType eq 'Land'.

Consider using $orderby=StatusChangeTimestamp desc and a reasonable $top
(500–1000) to get recent history without pulling the entire MLS archive.

Key fields to capture from historical listings:
  - ListingKey, ListingId (for matching)
  - StandardStatus (Expired/Withdrawn/Closed/Canceled)
  - ListPrice, OriginalListPrice, PreviousListPrice, ClosePrice
  - CumulativeDaysOnMarket
  - StatusChangeTimestamp (when it expired/withdrew/closed)
  - PrivateRemarks (★ the gold — why it died)
  - ListAgentKey, ListingOfficeId (agent/office patterns)
  - UnparsedAddress, ParcelNumber (for parcel matching)
  - SellerName (for owner matching to clusters)
  - SubdivisionName, LegalDescription

────────────────────────────────────────────────────────────────────────
1B. Historical-to-cluster matching
────────────────────────────────────────────────────────────────────────

For each historical listing, attempt to match it to existing clusters via:

1. **Parcel number match** — same ParcelNumber as a parcel in a cluster
2. **Address match** — same normalized address
3. **Owner name match** — SellerName matches cluster owner_key
4. **Agent/office match** — same ListAgentKey as active cluster listings

When a match is found, enrich the cluster with historical context.

────────────────────────────────────────────────────────────────────────
1C. New signal families from historical data
────────────────────────────────────────────────────────────────────────

SIGNAL: SELLER_CAPITULATION
  Price trajectory across listing attempts:
    OriginalListPrice → PreviousListPrice → current ListPrice
  Score: percentage drop from original. >20% = strong signal.
  Emit: seller_capitulation_detected

SIGNAL: CUMULATIVE_MARKET_EXPOSURE
  Total days across ALL listing attempts on the same parcel/owner.
  Current CDOM is one attempt. Stacked CDOM across history reveals true fatigue.
  A lot with 90 CDOM current but 600 CDOM cumulative is deeply stale.
  Emit: cumulative_exposure_threshold_crossed (thresholds: 365, 730 days)

SIGNAL: HISTORICAL_REMARKS_INTELLIGENCE
  PrivateRemarks from expired/withdrawn listings often contain:
    - "septic failed" / "perc test failed" → site risk
    - "wetland setback" / "floodplain" → entitlement constraint
    - "buyer financing fell through" → demand signal (buyer existed)
    - "seller changed mind" / "not ready" → timing signal
    - "split pending" / "survey in progress" → active development
  Categorize and score. These remarks are MORE valuable than active remarks
  because they explain WHY deals died.
  Emit: historical_remarks_signal_detected

SIGNAL: RELISTING_VELOCITY
  Time between withdrawal/expiration and new listing attempt.
  Fast relisting (<90 days) = motivated seller, deal fell through
  Slow relisting (>365 days) = dormant, may need outreach to wake
  Emit: relisting_velocity_detected

SIGNAL: SITE_RISK_FLAG
  Same parcel with 2+ failed listing attempts = possible site issue.
  Cross-reference with remarks for specific risk categories.
  Emit: site_risk_pattern_detected

────────────────────────────────────────────────────────────────────────
1D. Trigger rules for historical signals
────────────────────────────────────────────────────────────────────────

Design new rules following the existing RA–RU pattern. Each historical
signal should:
  - Wake the appropriate downstream agents
  - Feed back into cluster scoring (historical data enriches clusters)
  - Feed back into BBO signal deepening (RP/RO feedback loop)

Proposed rules (assign IDs after reading existing rules/__init__.py):
  - seller_capitulation_detected → RESCORE supply_intelligence_team
  - cumulative_exposure_threshold_crossed → RESCAN cluster_detection_agent
  - historical_remarks_signal_detected → CLASSIFY supply_intelligence_team
  - relisting_velocity_detected → RESCORE supply_intelligence_team
  - site_risk_pattern_detected → FLAG risk_assessment_agent (future)

────────────────────────────────────────────────────────────────────────
1E. Integration with signal report
────────────────────────────────────────────────────────────────────────

Extend signal_report.py tier scoring:
  - SELLER_CAPITULATION (>20% drop) → +3 score
  - CUMULATIVE_EXPOSURE (>365 days stacked) → +2 score
  - HISTORICAL_REMARKS (site risk) → -2 score (risk deduction)
  - HISTORICAL_REMARKS (buyer existed) → +2 score (demand confirmed)
  - RELISTING_VELOCITY (fast) → +2 score
  - SITE_RISK (2+ failures) → -3 score (flag, don't suppress)

────────────────────────────────────────────────────────────────────────
1F. Tests
────────────────────────────────────────────────────────────────────────

  - Historical listing fetch returns Expired/Withdrawn/Closed records
  - Parcel number matching links historical listing to cluster
  - Seller capitulation detection: $500K → $400K = 20% drop → detected
  - Cumulative CDOM stacking: 200 + 90 + current 120 = 410 → threshold crossed
  - Historical remarks categorization: "perc test failed" → site_risk
  - Relisting velocity: withdrew Jan 1, relisted Mar 1 = 59 days → fast
  - Site risk pattern: 3 failed attempts on same parcel → detected
  - All new signals route through TriggerEngine correctly
  - Zero regressions on 237 existing tests

════════════════════════════════════════════════════════════════════════
PART 2 — FORWARD ROADMAP (Steps 7–10)
════════════════════════════════════════════════════════════════════════

Based on the real data insights from the live pipeline, map out what
Steps 7–10 should accomplish. The 23 Tier 1 opportunities and 76 dormant
clusters give us concrete targets to design around.

────────────────────────────────────────────────────────────────────────
2A. Read the current state deeply
────────────────────────────────────────────────────────────────────────

Before planning, run the live pipeline to see current signal output:
  python3 landos/scripts/signal_report.py --top 95

Study the Tier 1 opportunities. What would a human do next with each one?
That action sequence IS the roadmap.

────────────────────────────────────────────────────────────────────────
2B. Proposed step mapping (refine based on data)
────────────────────────────────────────────────────────────────────────

STEP 7: MUNICIPAL INTELLIGENCE
  - Ypsilanti Charter Township as priority target
  - PA 58 of 2025 (Michigan Land Division Act amendments) as first-class signal
  - Zoning/entitlement posture per municipality
  - Which of our Tier 1 clusters are in favorable municipal contexts?
  - Which dormant supply is blocked by municipal constraints?

STEP 8: OPPORTUNITY SCORING & RANKING
  - Composite score across all signal families:
    cluster strength + BBO signals + historical behavior + municipal posture
  - Rank all opportunities: "If you had $5M, which 10 parcels do you buy first?"
  - Confidence bands (high/medium/low) based on signal convergence count
  - Output: ranked opportunity list with actionable intelligence per entry

STEP 9: PACKAGING INTELLIGENCE
  - For top-scored opportunities, what's the acquisition package?
  - Multiple parcels from same owner → bulk deal structure
  - Adjacent parcels from different owners → assemblage opportunity
  - Subdivision remnants → complete the plat
  - Estimate: total acreage, parcel count, estimated acquisition cost range
  - This is where the "attainable homeownership inventory" thesis becomes concrete

STEP 10: AGENT ORCHESTRATION & OUTPUT
  - Wire the multi-agent system for production runs
  - Scheduled pipeline: Spark refresh → Regrid refresh → cluster scan →
    historical enrichment → scoring → report generation
  - Alert system: new Tier 1 opportunity detected → notification
  - Dashboard/export: structured output for human decision-makers
  - API layer for downstream consumption

────────────────────────────────────────────────────────────────────────
2C. Document the roadmap
────────────────────────────────────────────────────────────────────────

Write the final roadmap to:
  landos/docs/ROADMAP_STEPS_7_10.md

Include for each step:
  - What it builds
  - What signals it produces
  - What it depends on
  - Acceptance criteria
  - Estimated scope (small/medium/large)

Also update:
  landos/docs/SESSION_HANDOFF_CURRENT.md — reflect new plan
  landos/docs/LANDOS_DECISIONS_LOG.md — any new locked decisions
  landos/docs/SESSION_LOG.md — append this session's work

════════════════════════════════════════════════════════════════════════
OUTPUT
════════════════════════════════════════════════════════════════════════

When both parts are complete, provide:

1. Summary of historical enrichment implementation (what was built, test count)
2. The Steps 7–10 roadmap with concrete scope per step
3. Updated Tier 1 opportunity count after historical enrichment
4. Top 5 highest-scored opportunities with full signal breakdown
5. Recommended next session focus

Do not declare done until all tests pass and documentation is updated.
