# BaseMod LandOS — Build Roadmap

> This file defines the build sequence for LandOS — what gets built in each phase,
> why the ordering is what it is, and what "done enough" looks like before moving forward.
> It is the sequencing companion to the architecture docs: the object model, event library,
> trigger matrix, agent teams, and data sources define *what* to build;
> this file defines *when* and *in what order*.

---

## Why sequencing matters

LandOS is a layered system where each layer depends on the trust established by the layer below it:

1. **Memory before signals.** If the documentation spine and object model are not stable, every implementation decision will be built on drift.
2. **Signals before packaging.** Packaging a land+home opportunity requires trustworthy parcel data, municipal context, and stallout detection. Packaging on top of unreliable signals produces unreliable packages.
3. **Packaging before distribution.** Exposing packages to buyers and brokers before the packages are trustworthy destroys credibility. The first packages shown to the market must be defensible.
4. **Distribution before transaction orchestration.** Transaction resolution tools are meaningless without a credible flow of packaged, distributed opportunities reaching real buyers.
5. **Flywheel after real usage.** Network effects, feedback loops, and optimization only matter once real transactions are happening.

The system should resist the temptation to jump to UI, marketplace, or consumer-facing work before the signal engine is trustworthy. Trust is the rate limiter.

---

## Phase-gating principle

Downstream phases should not be activated until upstream trust is real. This is not a suggestion — it is a design constraint enforced by the trigger matrix's phase-gating mechanism (trigger rules marked [Phase 2] or [Phase 3+] are not active until their phase is enabled).

**Concrete gates:**
- Packaging (Phase 3) should not begin until supply discovery and municipal intelligence are producing trustworthy, verified signals.
- Distribution (Phase 4) should not begin until packaging is producing defensible land+home packages with real pricing ranges.
- Transaction orchestration (Phase 5) should not begin until there is a credible pipeline of distributed packages with real buyer/broker engagement.
- Flywheel optimization (Phase 6) should not begin until real transactions have been completed and the system has operational data to learn from.

Each phase section below includes explicit "ready to move on" conditions that define when the gate opens.

---

## Phase 0 — Documentation & Memory Spine

### Goal
Establish the canonical project memory, architecture decisions, and documentation set that all implementation work will build from.

### Major capabilities to build
- Canonical object model with all Phase 1 objects fully defined
- Event library with all Phase 1 events defined, classified, and payload-specified
- Trigger matrix with all Phase 1 routing rules, guardrails, and priority hierarchy
- Agent teams doc with responsibilities, object scopes, and event subscriptions for all 8 teams
- Data sources doc with source categories, confidence tiers, and ingestion priorities
- Build roadmap (this file) with phase-by-phase sequencing and acceptance criteria
- Session continuity system (SESSION_HANDOFF_CURRENT.md + SESSION_LOG.md + SESSION_RITUAL.md)
- Decisions log with all locked architecture decisions and rationale

### Key documents / system layers it depends on
- Founder's strategic vision and architectural decisions
- Michigan market knowledge and opportunity thesis

### Ready to move on when
- All Phase 1 objects are fully defined in the object model
- All Phase 1 events are defined with payloads in the event library
- All Phase 1 trigger rules are specified in the trigger matrix
- Event library and trigger matrix are alignment-checked and confirmed clean
- Agent teams, data sources, and build roadmap are deepened to execution grade
- All locked decisions are recorded in the decisions log
- No unresolved architectural ambiguities remain that would block the first implementation pass

### What not to attempt in this phase
- No implementation code
- No source-specific field mapping (deferred to Phase 1 implementation)
- No UI prototyping
- No external data connections

---

## Phase 1 — Signal Engine

### Goal
Build the core signal infrastructure: ingest live market data, resolve parcels, detect clusters, scan municipal records, detect stallouts and site condos, and produce the first scored Opportunities. This is the foundation that everything else builds on.

### Major capabilities to build

#### 1a. Canonical event envelope and trigger engine scaffold
- Implement the event envelope schema (event_id, event_type, event_family, event_class, timestamps, entity_refs, payload, causal chain fields)
- Build the trigger engine that receives events, evaluates routing rules, enforces cooldowns, enforces materiality gates, and dispatches wake instructions to agents
- Implement generation-depth hard cap (default: 5) and anti-loop guardrails (materiality, one-direction causality, object-level cooldowns)
- Implement phase-gating so Phase 2+ trigger rules exist but do not fire

#### 1b. Object model scaffold
- Implement all 12 Phase 1 objects: Parcel, Listing, Municipality, MunicipalEvent, Owner, OwnerCluster, Subdivision, SiteCondoProject, DeveloperEntity, Opportunity, HomeProduct, SiteFit
- Implement the 2 lightweight system objects: AgentRun, Action
- Establish object storage, relationship linking, and scoring fields

#### 1c. MLS ingestion pipeline (Spark)
- Connect to Spark MLS RETS/RESO feed
- Emit listing-family events: `listing_added`, `listing_status_changed`, `listing_expired`, `listing_price_reduced`, `listing_relisted`
- Source-to-object field mapping for Listing object
- Agent teams active: Supply Intelligence Team (Team 1)

#### 1d. Parcel universe and linkage
- Ingest Regrid parcel data for priority Michigan counties
- Implement parcel-to-listing linkage (address match, parcel number match, geo match)
- Implement owner resolution from parcel records
- Emit parcel-state events: `parcel_linked_to_listing`, `parcel_owner_resolved`, `parcel_score_updated`

#### 1e. Cluster detection
- Implement owner/agent/office cluster detection logic
- Emit cluster events: `same_owner_listing_detected`, `owner_cluster_detected`, `owner_cluster_size_threshold_crossed`, `agent_subdivision_program_detected`, `office_inventory_program_detected`

#### 1f. Listing remarks classification
- Build LLM classification pipeline for listing remarks
- Emit classification events: `listing_package_language_detected` (priority 1), `listing_fatigue_language_detected`, `listing_restriction_language_detected`, `listing_approval_language_detected`, `listing_utility_language_detected`
- Agent teams active: Broker Notes & Market Intelligence Team (Team 4)

#### 1g. Municipal scanning
- Build municipal scan agent for priority Michigan municipalities
- Connect to Register of Deeds (priority counties), permit systems, planning commission minutes
- Emit municipal process detection events (all 16 raw events in the municipal_process family)
- Evaluate rule changes and emit `municipality_rule_now_supports_split` when applicable
- Agent teams active: Municipal Intelligence Team (Team 2)

#### 1h. Stallout and site-condo detection
- Build stallout detection agent: compare historical plats vs. current vacancy, assess infrastructure-invested-but-vacant patterns
- Build site-condo detection agent: master deed scan, legal description parsing, vacancy assessment
- Emit historical stall events: `historical_plat_stall_detected`, `historical_subdivision_stall_detected`, `site_condo_project_detected`, `site_condo_high_vacancy_detected`, `partial_buildout_stagnation_detected`, `unfinished_site_condo_detected`
- Agent teams active: Stallout & Site-Condo Forensics Team (Team 3)

#### 1i. Opportunity creation and scoring
- Implement Opportunity object lifecycle (detected → scored → fit_checked → ...)
- Implement initial scoring engine for parcel opportunity_score and Opportunity composite score
- Emit opportunity lifecycle events: `opportunity_created`, `opportunity_score_changed`, `opportunity_status_changed`

#### 1j. First fit analysis (geometry only)
- Implement SiteFit geometry analysis: can a BaseMod home model physically fit on this parcel?
- Emit: `parcel_geometry_fit_detected`, `home_model_fit_detected`, `fit_requires_human_review`
- Agent teams active: Packaging Team (Team 5, geometry fit only — no pricing yet)

### Key documents / system layers it depends on
- Phase 0 documentation spine (complete)
- Object model (Phase 1 objects fully defined)
- Event library (Phase 1 events fully specified)
- Trigger matrix (Phase 1 rules fully specified)
- Data sources (Phase 1 source priorities established)

### Data sources active in Phase 1
Per LANDOS_DATA_SOURCES.md implementation sequencing:
1. Spark MLS feed
2. Regrid parcel data
3. Register of Deeds (priority counties)
4. Permit systems (priority municipalities)
5. Planning commission minutes (priority municipalities)
6. County assessor / tax records

### Ready to move on when
- MLS ingestion is producing listing events reliably
- Parcel-to-listing linkage is working with acceptable match rates
- Cluster detection is identifying owner/agent patterns
- LLM remarks classification is producing classification events with reasonable accuracy
- Municipal scan agent is producing detection events for at least 3 priority municipalities
- Stallout detection has identified candidate stalled subdivisions from historical plat data
- Site-condo detection has identified candidate projects from master deed data
- Opportunity objects are being created and scored
- First SiteFit geometry analysis has run for at least a sample set of parcels
- The trigger engine is routing events, enforcing cooldowns, and respecting anti-loop guardrails
- An operator can review scored Opportunities and their supporting signals in some minimal interface (does not need to be the final UI)

### What not to attempt in this phase
- No all-in pricing or PricePackage creation
- No site work estimation
- No incentive matching or application tracking
- No marketplace or consumer-facing UI
- No buyer/broker matching
- No seller outreach tooling
- No transaction orchestration
- No demand-side data ingestion

---

## Phase 2 — Municipal & Stallout Intelligence Deepening + Packaging Engine

### Goal
Deepen municipal intelligence coverage, add pricing and packaging capabilities, build the incentive matching layer, and produce the first complete land+home packages that could credibly be shown to a broker or buyer.

### Major capabilities to build

#### 2a. Expanded municipal coverage
- Extend municipal scanning to additional Michigan municipalities beyond the initial priority set
- Add GIS / utility layer ingestion for SiteFit utility assessment
- Add aerial imagery ingestion for vacancy confirmation and corroboration
- Expand Register of Deeds coverage to additional counties

#### 2b. Full packaging pipeline
- Implement SiteWorkEstimate (site work cost estimation)
- Implement PricePackage (all-in pricing: land + home + site work + fees)
- Emit: `site_work_estimate_completed`, `all_in_price_viable_detected`, `package_ready_for_distribution`
- Implement packaging regeneration rules (per trigger matrix: full regen vs. incremental update)
- Agent teams fully active: Packaging Team (Team 5, full scope)

#### 2c. Incentive matching
- Implement IncentiveProgram and IncentiveApplication objects
- Build incentive discovery and matching agent
- Emit incentive-family events: `incentive_detected`, `incentive_potential_match_detected`, `incentive_application_required`, `incentive_deadline_upcoming`, `incentive_award_confirmed`
- Agent teams active: Incentives & Policy Team (Team 6)

#### 2d. BrokerNote and operator tooling
- Implement BrokerNote object and creation workflow
- Build operator interface for: opportunity review, broker note creation, human verification, event suppression, forced rescans
- Enable human_operator event family in production

#### 2e. Initial distribution capability
- Implement `opportunity_ready_for_distribution` routing
- Build seller engagement tracking: `seller_engagement_started`, `seller_ready_to_transact`
- Build broker interest tracking: `broker_interest_detected`
- Agent teams active: Market Activation Team (Team 7, initial scope)

#### 2f. Additional MLS coverage
- Connect RealComp MLS (metro Detroit) using the same ingestion architecture as Spark

### Key documents / system layers it depends on
- Phase 1 signal engine (operational and producing trustworthy signals)
- Data sources Phase 2 sources (GIS, aerial imagery, ATTOM, RealComp, operator interface)

### Ready to move on when
- At least 10 Opportunities have been fully packaged with all-in pricing ranges
- At least 3 packages have been reviewed by a human and confirmed as defensible (fit is realistic, pricing range is credible, municipal context is accurate)
- Incentive matching is running for at least one active incentive program
- BrokerNote creation workflow is operational
- An operator can review a complete package (parcel + home + site work + pricing + municipal context + incentives if applicable) and present it to a broker with confidence
- Seller outreach has been initiated for at least one packaged opportunity

### What not to attempt in this phase
- No consumer-facing marketplace UI
- No buyer self-service search
- No transaction execution tooling
- No construction coordination
- No lender/contractor databases
- No demand-side matching at scale

---

## Phase 3 — Market Activation Layer

### Goal
Build the buyer/broker-facing experience that lets the market discover and engage with packaged land+home opportunities. This is the layer where the platform becomes visible to the market.

### Major capabilities to build

#### 3a. Marketplace browse experience
- Build buyer-facing browse interface for packaged opportunities
- Build broker-facing search and saved-search functionality
- Implement BuyerProfile, BrokerProfile, SavedSearch objects

#### 3b. Demand-side event pipeline
- Emit demand events: `buyer_search_profile_created`, `buyer_search_matches_opportunity`, `broker_saved_search_created`
- Feed demand signals back into opportunity scoring (composite score boost from real engagement)
- Agent teams fully active: Market Activation Team (Team 7, full scope)

#### 3c. Seller engagement at scale
- Systematize seller outreach beyond manual one-off contacts
- Build outreach tracking and response management
- Build seller negotiation support tools

#### 3d. Distribution channel routing
- Route packaged opportunities to appropriate channels based on opportunity type, geography, and market readiness
- Track channel performance (which channels produce engagement, which produce transactions)

### Key documents / system layers it depends on
- Phase 2 packaging engine (producing defensible packages)
- Phase 2 incentive matching (operational)
- Credible operator verification of package quality

### Ready to move on when
- At least 5 brokers have engaged with packaged opportunities through the platform
- At least 3 buyers have expressed interest in specific opportunities
- At least 1 seller engagement has progressed to negotiation stage
- Demand signals are flowing back into opportunity scoring
- The browse experience is functional enough that a broker can independently find and evaluate opportunities

### What not to attempt in this phase
- No transaction closing infrastructure
- No construction management tooling
- No lender/contractor integration
- No flywheel optimization or A/B testing of routing strategies

---

## Phase 4 — Transaction Resolution Layer

### Goal
Build the infrastructure to take engaged opportunities through site feasibility, buyer commitment, financing, contractor assignment, and final orderable-package creation. This is where land+home opportunities become real housing outcomes.

### Major capabilities to build

#### 4a. Site feasibility confirmation
- Build site feasibility workflow: site visits, soil tests, surveys
- Emit: `site_feasibility_confirmed`
- Track feasibility outcomes and feed back into SiteFit confidence calibration

#### 4b. Buyer commitment and financing
- Implement buyer commitment tracking: `buyer_ready_to_proceed`
- Implement lender path identification: `lender_path_available`
- Build TransactionPath object

#### 4c. Contractor assignment
- Implement contractor matching: `contractor_path_available`
- Build ConstructionPath object
- Track contractor capacity and geography coverage

#### 4d. Orderable package creation
- Implement the culmination event: `orderable_package_created`
- All components converged: land + home + site work + financing + contractor + timeline
- Agent teams fully active: Transaction Resolution Team (Team 8)

### Key documents / system layers it depends on
- Phase 3 market activation (producing real buyer/broker engagement)
- Credible pipeline of engaged opportunities with real counterparties

### Ready to move on when
- At least 1 transaction has been fully closed (land acquired or controlled, home ordered, construction path confirmed)
- The system can trace the full signal chain from listing/stallout detection through packaging, distribution, engagement, and transaction
- Operational data exists for: conversion rates by opportunity type, time-to-transaction, packaging accuracy, pricing accuracy

### What not to attempt in this phase
- No flywheel optimization without operational data
- No geographic expansion beyond Michigan until the first proof exists
- No automated transaction execution — humans remain in the loop for all closing decisions

---

## Phase 5 — Flywheel / Network Effects

### Goal
Use real operational data and transaction outcomes to optimize the entire system — improve scoring models, tune trigger thresholds, expand geography, and build compounding network effects.

### Major capabilities to build

#### 5a. Scoring model calibration
- Use closed-transaction outcomes to calibrate opportunity scoring (which signals actually predicted successful transactions?)
- Tune trigger matrix thresholds (cooldowns, materiality gates, priority hierarchy) based on real-world event volumes and processing experience

#### 5b. Geographic expansion
- Expand beyond Michigan using the same architecture
- Adapt municipal scanning to new state/county systems
- Validate that the event mesh architecture generalizes

#### 5c. Network effects
- Broker adoption creates demand signals that improve opportunity prioritization
- Transaction outcomes create training data that improves scoring
- Municipal coverage creates moat (historical data is hard to replicate)
- Packaging track record creates trust (verified outcomes attract more participants)

#### 5d. Operational optimization
- A/B test routing strategies (trigger rule variants)
- Optimize processing efficiency (batch sizing, cooldown tuning, fan-out calibration)
- Build system observability dashboards

### Key documents / system layers it depends on
- Phase 4 transaction resolution (real transactions completed)
- Operational data from the full signal-to-transaction pipeline

### Ready to move on when
- This phase does not have a "move on" gate — it is the ongoing operating mode of a mature system.

### What not to attempt in this phase
- No fundamental architecture changes — the event mesh, object model, and trigger matrix should be stable. Optimization is tuning, not rebuilding.

---

## First implementation pass after documentation deepening

When all documentation deepening is complete (agent teams, data sources, build roadmap), the first implementation pass should cover these items in this order:

1. **Source-specific field mapping for Spark MLS** — map Spark RETS fields to Listing object fields. This is the first field-level schema work.
2. **Source-specific field mapping for Regrid** — map Regrid parcel fields to Parcel object fields.
3. **Canonical event envelope implementation** — implement the event schema in code.
4. **Object model scaffold** — implement Phase 1 object storage (database schema or equivalent).
5. **Trigger engine scaffold** — implement the routing engine that receives events and dispatches wake instructions.
6. **MLS ingestion pipeline** — connect to Spark, ingest listings, emit listing events.
7. **Parcel linkage** — resolve listings to parcels.
8. **Cluster detection** — identify owner/agent patterns.
9. **Listing remarks classification** — LLM pipeline for remarks analysis.
10. **Municipal scan agent (first municipality)** — scan one priority municipality end-to-end as proof of concept.

This sequence builds from data in → objects stored → events flowing → agents waking → signals compounding. Each step produces observable, testable output before the next step begins.
