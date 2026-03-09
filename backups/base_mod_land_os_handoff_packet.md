# BaseMod LandOS — Full Handoff Packet

This document contains the canonical contents for the core project-memory files.

---

## FILE: 00_START_HERE.md

# BaseMod LandOS — Start Here

## What this is
This folder is the canonical handoff and project-memory packet for **BaseMod LandOS — Event Mesh**, also called **Land Swarm**.

LandOS is not a simple lead-generation tool, land scraper, or vacant-lot CRM. It is a **market-organizing system** designed to discover, understand, package, distribute, and convert fragmented land opportunity into attainable homeownership outcomes.

The core idea is that **authentic market signals** should wake the right downstream agents, objects, and workflows:
- listings wake parcels, clusters, municipalities, and packaging work
- clusters wake listings, broker notes, municipal scans, and owner expansion
- municipalities wake listings, parcels, clusters, incentives, and opportunity rescoring
- historical stallouts and site condos wake supply discovery even when no listing exists
- buyer demand and broker searches wake packaging and distribution priorities

The end-state is a platform where:
1. land that can realistically become housing is identified and structured,
2. BaseMod homes are matched to that land,
3. all-in pricing is made legible,
4. sellers and their brokers can engage through the platform,
5. buyers and buyer brokers can browse real land+home opportunities,
6. BaseMod monetizes as product layer, dealer, coordinator, and construction-management conduit.

## Why this matters
The current housing market is fragmented:
- land supply is hidden or mispriced,
- municipal signals are buried,
- policy unlocks are not surfaced,
- lots are not packaged with realistic homes and site costs,
- buyers only see finished resale homes,
- brokers have no good land+home product to show.

LandOS exists to turn fragmented land supply into structured, transactable, attainable homeownership inventory.

## Read this folder in this order
1. `00_START_HERE.md`
2. `LANDOS_HANDOFF_MASTER.md`
3. `LANDOS_DECISIONS_LOG.md`
4. `LANDOS_OBJECT_MODEL.md`
5. `LANDOS_EVENT_LIBRARY.md`
6. `LANDOS_TRIGGER_MATRIX.md`
7. `LANDOS_AGENT_TEAMS.md`
8. `LANDOS_DATA_SOURCES.md`
9. `LANDOS_BUILD_ROADMAP.md`
10. `CLAUDE.md`
11. `CODEX_TASKING.md`

## Current status summary
These major conclusions have already been reached:

### Confirmed system direction
- The moat is not any one data source or agent.
- The moat is the **wake-up architecture**: typed events, shared objects, cross-trigger logic, and recursion guardrails.
- This is an **event mesh**, not a linear pipeline.

### Confirmed priority triggers
The system must treat **listings, clusters, and municipalities** as co-equal trigger families:
- **Listings** are high-frequency sparks.
- **Clusters** are multiplicative pattern expanders.
- **Municipalities** are rules-of-the-game / process-change shockwaves.

### Confirmed strategic wedge
Michigan is a strong launch wedge because of:
- stranded lots,
- stalled subdivisions,
- stalled site-condo inventory,
- land-division reform under 2025 PA 58,
- the possibility of more aggressive local parcel division under Section 108(6) if locally authorized.

### Confirmed build sequence
1. Build the memory and documentation spine.
2. Build the object model and event schema.
3. Build the trigger engine.
4. Build the municipal agent MVP and historical stallout detection.
5. Build the packaging layer (fit + all-in pricing).
6. Build the market-facing browse / broker layer.
7. Build the conversion and transaction orchestration layer.

## Audience
These documents are written for two audiences at once:
- **Founder/operator**: needs plain-English explanation, priorities, and next-step clarity.
- **Technical partner / engineering systems**: needs precise objects, events, routing logic, and implementation constraints.

## Rules for future contributors
- Do not create overlapping “master” docs unless explicitly replacing one with another.
- Do not rely on chat history as the source of truth.
- Do not change core architecture without updating:
  - `LANDOS_HANDOFF_MASTER.md`
  - `LANDOS_DECISIONS_LOG.md`
  - the relevant specialized file
- All major decisions must be logged with rationale.

## Immediate recommended next step
Read the handoff master and decisions log first. Then either:
- continue architecture/documentation work, or
- begin implementation of the canonical object model and typed event schema.

## One-sentence definition
**BaseMod LandOS is the operating system that turns fragmented land supply into attainable homeownership inventory by mapping signals, waking the right agents, packaging homes that fit, and routing the market toward transaction.**

---

## FILE: LANDOS_HANDOFF_MASTER.md

# BaseMod LandOS — Handoff Master

## Official naming
- **Program name:** BaseMod LandOS — Event Mesh
- **Nickname:** Land Swarm

## Canonical mission
Turn fragmented land supply into structured, transactable, attainable homeownership inventory.

## Canonical vision
Build the operating system that continuously maps land liquidity, development readiness, policy unlocks, seller intent, buyer affordability, and installable home options—then turns those signals into transactable housing outcomes.

## The breakthrough insight
The system's power comes from **authentic signals triggering the next right agents, which create new authentic signals, which trigger the next right agents**, in a compounding cascade that organizes the market into housing outcomes.

This is not “agents for the sake of agents.”
This is a **signal architecture** where:
- objects hold durable market memory,
- events express meaningful market change,
- agents perform bounded work,
- outcomes become increasingly packageable and transactable.

## What LandOS is not
LandOS is not:
- just an MLS scraper,
- just a vacant-lot database,
- just a CRM,
- just a modular home configurator,
- just a lead gen funnel.

It is a **market-state engine + packaging engine + distribution engine + transaction engine**.

## Core thesis
Every meaningful land signal should be allowed to wake the market graph. Every major object should be able to receive events, emit events, and trigger next-best actions. The system should keep routing, enriching, packaging, and distributing opportunity until a credible housing outcome exists.

## Why this exists
Housing is constrained not only by cost, but by fragmentation:
- buildable land is hidden or misunderstood,
- municipal process data is scattered,
- incentives are obscure,
- sellers do not know what their land can support,
- buyer brokers do not have a clean land+home product to show,
- buyers cannot easily compare vacant land opportunities to resale homes,
- builders do not have a machine to surface all the low-friction, ready-ish opportunities.

LandOS exists to connect all of that.

## End-state platform concept
For every viable parcel, lot, cluster, subdivision, site condo, or administratively splittable tract:
1. identify the opportunity,
2. understand the policy/municipal context,
3. fit the right BaseMod home product,
4. estimate site work and all-in price,
5. expose it to the market through buyers, brokers, and sellers,
6. convert it into a delivered housing outcome.

The end-state experience is that buyers and brokers can browse **land+home opportunities** the way they browse existing homes today.

## BaseMod's role in the ecosystem
BaseMod may play one or several of these roles depending on the opportunity:
- direct buyer/controller of land,
- conduit between seller and end buyer,
- merchandiser/packager of land+home outcomes,
- dealer of the home product,
- construction management coordinator,
- lead source and transaction organizer,
- data and signal infrastructure layer.

The system should be designed so BaseMod does not need to own every parcel to capture value.

## Major object families
### Supply-side objects
- Parcel
- Listing
- Owner
- OwnerCluster
- Subdivision
- SiteCondoProject
- Municipality
- MunicipalEvent
- DeveloperEntity
- IncentiveProgram
- Opportunity

### Demand-side objects
- BuyerProfile
- BrokerProfile
- SavedSearch
- BudgetBand
- GeographyPreference
- HomeProductPreference
- FinancingProfile

### Product/packaging objects
- HomeProduct
- HomeVariant
- SetbackFit
- UtilityFit
- SiteWorkEstimate
- PricePackage
- DeliveryTimeline

### Execution objects
- Action
- AgentRun
- OutreachTask
- IncentiveApplication
- TransactionPath
- ConstructionPath

## Core trigger families
### Listings
Listings are high-frequency entry points. They should wake:
- parcels,
- owner linkage,
- clusters,
- municipal scans,
- broker notes,
- packaging,
- incentives,
- buyer matching.

### Clusters
Clusters are multiplicative expanders. They should wake:
- broker deep notes,
- owner/entity research,
- adjacent parcel scans,
- municipal scans,
- listing rescans,
- opportunity generation.

### Municipalities
Municipalities are first-class active objects. They should wake:
- parcel rescoring,
- large-acreage scans,
- listing rescans,
- cluster recomputation,
- incentive rematching,
- geography-wide opportunity refreshes.

### Historical stallouts
Historical municipal and plat/site-condo forensics seed supply even without live listings.

### Buyer demand
Saved searches, buyer budgets, location preferences, and broker interest should wake packaging and prioritization.

## The Michigan wedge
Michigan is a particularly strong launch market because:
- it has a meaningful amount of stranded lot and vacant land opportunity,
- stalled subdivisions and site condos are common,
- land division law has shifted,
- municipalities may create more aggressive local division possibilities under Section 108(6),
- the gap between land availability and attainable home product is significant.

## Priority strategic wedges inside Michigan
1. **Stranded lots**
2. **Stalled subdivisions**
3. **Stalled site condos**
4. **5+ acre land-division candidates**
5. **Subsection 6 municipality opportunities**
6. **Developer fatigue / exit-window inventory**
7. **Infrastructure-complete, vertically incomplete projects**

## Historical stallout thesis
A large amount of valuable opportunity may come from projects that stalled 10–15 years ago:
- plats recorded,
- master deeds recorded,
- roads installed,
- utilities installed,
- but lots still vacant.

These should be detected by comparing historical municipal/deed/plat signals to current parcel vacancy and, where possible, aerial evidence.

## Site-condo thesis
Site condos are a major hidden category because they are often under-detected by ordinary subdivision screens. They should be discovered via:
- master deed signals,
- legal-description patterns (`UNIT`, `CONDOMINIUM`, `SITE CONDO`),
- vacancy ratios,
- age,
- roads/infrastructure signals.

## Developer fatigue / exit-window thesis
The system should detect when a developer has shifted from value-maximizing buildout to inventory monetization. Key patterns include:
- same-agent inventory program,
- package or remaining-inventory language,
- long CDOM,
- roads installed with high vacancy,
- repeated relists and price drift,
- broker-note fatigue signals.

## Packaging thesis
Land is not enough. The platform must package land into buyer-legible opportunity:
- what home fits,
- what assumptions were used,
- what setbacks and zoning considerations apply,
- what site work range is likely,
- what the all-in price range is,
- what timeline is realistic,
- what incentives may apply.

Packaging is the trust layer.

## Marketplace thesis
The platform should ultimately expose:
- lots and land that can become housing,
- BaseMod home options that fit,
- all-in pricing ranges,
- municipality/site highlights,
- feasibility confidence,
- broker/buyer-friendly browse experiences.

This should create a new kind of market behavior:
buyers compare land+home to resale homes in one mental workflow.

## Business model thesis
BaseMod monetizes where it sits in the value chain:
- home/dealer margin,
- construction management fee,
- transaction coordination,
- data advantage,
- distribution advantage,
- possibly financing/referral and ancillary revenue over time.

## System design principles
1. Use genuine signals only.
2. Let every major object receive and emit events.
3. Use typed events and deterministic state updates where possible.
4. Use LLMs for ambiguity, summarization, classification, and extraction—not as the sole source of truth.
5. Keep confidence and assumptions explicit.
6. Keep humans in the loop on critical inflection points.
7. Build recursion guardrails from day one.
8. Optimize for a real housing outcome, not just signal generation.

## Immediate next build priorities
1. Finalize the documentation spine.
2. Finalize canonical object model.
3. Finalize event schema and event library.
4. Finalize trigger matrix and guardrails.
5. Build municipal history / stallout logic.
6. Build listing + cluster + municipality cross-wake engine.
7. Build packaging prototype (home fit + all-in pricing).
8. Build first broker/buyer browse experience.

## Never forget
- The product is the signal architecture, not a loose collection of agents.
- Packaging matters as much as sourcing.
- The buyer/broker experience is the proof of category creation.
- The first wedge is high-confidence land opportunity, not universal perfection.
- Trust comes from grounded assumptions and clear explanations.
- BaseMod’s societal impact comes from making overlooked land legible and attainable as housing.

---

## FILE: LANDOS_DECISIONS_LOG.md

# BaseMod LandOS — Decisions Log

> Purpose: preserve not just conclusions, but the reasons behind them.
> Format: Date | Decision | Why | Affects | Reversible?

## 2026-03-08 | LandOS is an event mesh, not a pipeline
**Decision:** The system architecture will be designed as a cross-triggered event mesh rather than a linear sourcing pipeline.  
**Why:** Listings, clusters, municipalities, historical stallouts, and human actions can all wake downstream work in multiple directions. A pipeline model would lose the compounding benefit of authentic cross-signals.  
**Affects:** Entire architecture, object model, event schema, trigger engine, agent design.  
**Reversible?:** No, this is foundational.

## 2026-03-08 | The moat is the wake-up logic
**Decision:** The core moat is the typed event system, object graph, trigger rules, and recursion controls—not any single data source or isolated agent.  
**Why:** Data can be copied, agents can be rebuilt, but the architecture that turns signals into next-best actions across a market graph is much harder to replicate.  
**Affects:** Product strategy, engineering priority, documentation priority.  
**Reversible?:** No.

## 2026-03-08 | Listings, clusters, and municipalities are co-equal trigger families
**Decision:** Listings, clusters, and municipalities must all be first-class origin nodes for the swarm.  
**Why:** Listings are high-frequency sparks, clusters are pattern expanders, and municipalities are policy/process shockwaves. Any one of them can legitimately wake the others.  
**Affects:** Event library, trigger matrix, agent routing, object design.  
**Reversible?:** No.

## 2026-03-08 | Municipality must be a first-class active object
**Decision:** Municipality is not just reference metadata; it is an active object with its own state, events, and wake authority.  
**Why:** Rule changes, permits, infrastructure signals, plats, site plan activity, and split-friendly posture can reprice whole geographies.  
**Affects:** Object model, municipal agent design, scoring, wake logic.  
**Reversible?:** No.

## 2026-03-08 | Historical municipal forensics are a priority
**Decision:** Municipal process/history should be analyzed 10–15 years back to identify stalled subdivisions and site condos.  
**Why:** Some of the best opportunities likely stalled during or after the Great Recession and still have incomplete vertical development despite prior entitlement and infrastructure investment.  
**Affects:** Data-source strategy, municipal agent scope, historical stall scoring, site-condo forensics.  
**Reversible?:** No.

## 2026-03-08 | Recorded plats vs current vacant-lot ratios are a key stall signal
**Decision:** Recorded plats mapped against current vacant parcels are a core statewide stalled-subdivision detection method.  
**Why:** Plats indicate legal subdivision creation and often imply advanced development work; persistent vacancy years later is a strong stranded-development signal.  
**Affects:** Stallout detection, historical event ingestion, subdivision objects.  
**Reversible?:** No.

## 2026-03-08 | Master deed + vacant unit ratio is a key site-condo signal
**Decision:** Site-condo opportunities should be detected via master deed signals and legal-description/unit analysis.  
**Why:** Site condos often fall outside ordinary subdivision analysis and represent a meaningful hidden inventory pool.  
**Affects:** SiteCondoProject object, legal-description parsing, municipal/deed ingestion.  
**Reversible?:** No.

## 2026-03-08 | Developer fatigue should be inferred behaviorally
**Decision:** Developer exit readiness will be inferred through behavior patterns, not relied on primarily through financial distress data.  
**Why:** Same-agent programs, long CDOM, package language, roads installed + vacancy, and monetization behavior are more actionable than opaque financial facts.  
**Affects:** Trigger matrix, event library, broker note design, opportunity scoring.  
**Reversible?:** No.

## 2026-03-08 | Packaging is a first-class system layer
**Decision:** LandOS must package land into buyer-legible land+home outcomes, not merely source supply.  
**Why:** The category-creating move is letting buyers and brokers compare land+home opportunities to existing homes.  
**Affects:** Product roadmap, object model, pricing engine, marketplace design.  
**Reversible?:** No.

## 2026-03-08 | BaseMod need not own every parcel
**Decision:** The platform should support multiple operating modes: buy, control, package, market through, dealer-enable, coordinate, and construction-manage.  
**Why:** Value accrues from orchestration and packaging, not only direct land ownership.  
**Affects:** Business model, workflow design, marketplace architecture, transaction path design.  
**Reversible?:** Low.

## 2026-03-08 | Documentation spine before implementation
**Decision:** The project memory and canonical documentation set must be created before heavy implementation work begins.  
**Why:** The biggest immediate risk is context fragmentation and decision drift, not lack of coding power.  
**Affects:** Workflow, tooling, collaboration with technical partner, agent usage.  
**Reversible?:** Yes, but strongly discouraged.

## 2026-03-08 | Use file-based memory as source of truth
**Decision:** Durable project memory must live in files, not in chat memory or tool-internal memory.  
**Why:** Sessions reset, models compress, and context can drift. Files preserve the project.  
**Affects:** Repo structure, handoff process, Claude/Codex usage.  
**Reversible?:** No.

## 2026-03-08 | Claude Code and Codex are execution tools, not the “brain”
**Decision:** Tool choice should be separated from the actual system intelligence.  
**Why:** The real brain is the object model + event architecture + trigger rules; tools are work surfaces and runtimes.  
**Affects:** Technical workflow, team communications, implementation strategy.  
**Reversible?:** Yes.

## 2026-03-08 | Michigan launch wedge is strategic
**Decision:** Michigan should be treated as the highest-priority proving ground.  
**Why:** It combines stranded lots, stalled site condos/subdivisions, relevant legal changes, and a strong mismatch between supply and attainable product.  
**Affects:** Early geography focus, municipal tracking, product examples, GTM wedge.  
**Reversible?:** Yes.

---

## FILE: LANDOS_OBJECT_MODEL.md

# BaseMod LandOS — Object Model

> This file defines the first-class objects in the system.

## Design principles
1. Objects are durable memory; events are change.
2. Objects should be normalized enough to avoid duplication, but pragmatic enough to ship.
3. Every object should support confidence, timestamps, and source provenance where relevant.
4. LLM-derived fields should be labeled as derived/inferred, not confused with authoritative source fields.

## Core objects
- Parcel
- Listing
- Owner
- OwnerCluster
- Subdivision
- SiteCondoProject
- Municipality
- MunicipalEvent
- DeveloperEntity
- IncentiveProgram
- Opportunity
- BuyerProfile
- BrokerProfile
- HomeProduct
- SiteFit / SetbackFit
- SiteWorkEstimate
- PricePackage
- TransactionPath

## Parcel (minimum shape)
- parcel_id
- source_system_ids
- jurisdiction_state
- county
- municipality_id
- apn_or_parcel_number
- legal_description_raw
- acreage
- geometry
- current_owner_id or owner_name_raw
- vacancy_status
- land_use_class
- created_at
- updated_at

## Listing (minimum shape)
- listing_id
- source_system
- listing_key
- standard_status
- list_price
- original_list_price
- parcel_id if known
- subdivision_name_raw
- remarks_raw
- listing_agent
- listing_office
- dom
- cdom
- created_at
- updated_at

## Municipality (minimum shape)
- municipality_id
- name
- state
- county
- approval authority type
- land division posture
- SB 23 posture
- Section 108(6) posture
- frontage rules summary
- lot size rules summary
- sewer/water service summary
- incentive density score
- market wake score

## Object model implementation notes
- IDs should be stable and portable.
- Favor append-only event history over destructive overwrite where possible.
- Track provenance on critical fields.
- Separate raw source fields from normalized/derived fields.
- Support confidence on ambiguous fields.

---

## FILE: LANDOS_EVENT_LIBRARY.md

# BaseMod LandOS — Event Library

## Canonical event envelope
Every event should include:
- event_id
- event_type
- event_family
- occurred_at
- observed_at
- source_system
- source_record_id
- source_confidence
- entity_refs
- payload
- derived_from_event_ids
- causal_chain_id
- generation_depth
- wake_priority
- routing_class
- dedupe_key
- fingerprint_hash
- ttl
- status

## Event families
### Listing events
- listing_added
- listing_status_changed
- listing_price_reduced
- listing_relisted
- listing_cdom_threshold_crossed
- listing_large_acreage_detected
- package_language_detected
- developer_fatigue_language_detected
- restriction_language_detected
- approval_language_detected
- utility_language_detected
- listing_broker_note_required
- listing_cluster_expansion_required
- listing_municipal_scan_required
- listing_incentive_scan_required
- listing_market_shock_candidate_detected

### Cluster / owner events
- same_owner_listing_detected
- owner_cluster_detected
- owner_cluster_size_threshold_crossed
- agent_subdivision_program_detected
- office_inventory_program_detected
- cluster_municipal_scan_required
- cluster_broker_note_required

### Municipal process events
- site_plan_approved_detected
- plat_recorded_detected
- engineering_approved_detected
- permit_pulled_detected
- permits_pulled_majority_vacant_detected
- approved_no_vertical_progress_detected
- roads_installed_detected
- roads_accepted_detected
- roads_installed_majority_vacant_detected
- public_sewer_extension_detected
- water_extension_detected
- bond_posted_detected
- bond_extension_detected
- bond_release_delay_detected
- bond_posted_no_progress_detected
- hoa_created_detected
- master_deed_recorded_detected
- site_condo_regime_detected
- developer_control_active_detected
- hoa_exists_majority_vacant_detected
- unfinished_site_condo_detected
- municipality_rule_now_supports_split
- municipality_split_capacity_increased
- municipality_frontage_rules_favorable_detected
- municipality_permit_activity_increased
- municipality_infrastructure_extension_detected
- municipality_incentive_program_detected
- municipality_subdivision_stagnation_pattern_detected

### Historical stall / site condo events
- historical_plat_stall_detected
- historical_subdivision_stall_detected
- site_condo_project_detected
- site_condo_high_vacancy_detected
- improved_subdivision_stagnation_detected

### Developer / exit-window events
- developer_entity_distress_detected
- remaining_inventory_program_detected
- coordinated_broker_liquidation_detected
- subdivision_sellout_strategy_detected
- developer_exit_window_detected
- broker_signaled_bulk_flexibility_detected

### Incentive events
- incentive_detected
- incentive_potential_match_detected
- incentive_application_required
- incentive_deadline_upcoming
- incentive_paperwork_started
- incentive_paperwork_completed
- incentive_award_confirmed

### Packaging events
- parcel_geometry_fit_detected
- home_model_fit_detected
- utility_assumption_confident_detected
- site_work_estimate_completed
- all_in_price_viable_detected
- package_ready_for_distribution
- fit_requires_human_review

### Distribution / demand events
- buyer_search_profile_created
- buyer_search_matches_opportunity
- broker_saved_search_created
- broker_interest_detected
- seller_engagement_started
- seller_ready_to_transact
- opportunity_ready_for_distribution

### Transaction / execution events
- site_feasibility_confirmed
- buyer_ready_to_proceed
- lender_path_available
- contractor_path_available
- orderable_package_created

### Human/operator events
- human_marked_interesting
- human_requested_rescan
- human_verified_opportunity
- human_suppressed_event

---

## FILE: LANDOS_TRIGGER_MATRIX.md

# BaseMod LandOS — Trigger Matrix

## Priority wake hierarchy
1. package_language_detected
2. roads_installed_majority_vacant_detected
3. permits_pulled_majority_vacant_detected
4. municipality_rule_now_supports_split
5. bond_posted_no_progress_detected
6. listing_expired inside meaningful owner cluster
7. developer_entity_distress_detected + fresh listing activity
8. agent_subdivision_program_detected
9. hoa_exists_majority_vacant_detected
10. frontage + acreage + favorable municipality split candidate

## Core logic
- Listing -> parcel/municipality/opportunity wake
- Cluster -> opportunity/municipality wake
- Municipality -> parcels/clusters/opportunities wake
- Historical stall -> subdivision/site condo/opportunity wake
- Opportunity -> packaging wake
- Buyer profile -> distribution wake

## Guardrails
- Hard cap on chain depth
- No same-object heavy wake twice inside cooldown unless material delta
- Require material score change for medium/heavy rescoring
- Municipality-origin events must be scoped by parcel class / acreage / geography
- Stallout scans should not rerun on every small signal
- Packaging must not regenerate endlessly for minor data changes

---

## FILE: LANDOS_AGENT_TEAMS.md

# BaseMod LandOS — Agent Teams

## 1. Supply Intelligence Team
Purpose: discover supply-side opportunity earlier and more accurately than the market.

## 2. Municipal Intelligence Team
Purpose: turn municipal policy and process motion into structured events that reprice opportunity.

## 3. Stallout & Site-Condo Forensics Team
Purpose: find stranded subdivisions and site condos, especially older projects invisible to live-market-only views.

## 4. Broker Notes & Market Intelligence Team
Purpose: capture the non-obvious commercial truth hidden in remarks, broker patterns, and back-office notes.

## 5. Packaging Team
Purpose: turn raw land opportunity into a buyer-legible homeownership package.

## 6. Incentives & Policy Team
Purpose: improve economics and unlockability through incentives and policy understanding.

## 7. Market Activation Team
Purpose: expose opportunities to sellers, brokers, and buyers in the right format.

## 8. Transaction Resolution Team
Purpose: turn promising packaged opportunities into executed housing outcomes.

---

## FILE: LANDOS_DATA_SOURCES.md

# BaseMod LandOS — Data Sources

## Key sources
- Spark / MLS data
- Regrid / Airtable parcel universe
- Mission Control historical ATTOM summaries
- Planning commission agendas and minutes
- Register of Deeds / recorded documents
- Permit systems
- GIS / utility / infrastructure layers
- Satellite / aerial imagery
- Broker notes / human notes
- Buyer / broker demand signals

## Confidence philosophy
High confidence:
- recorded plats/master deeds
- permit records
- parcel system facts
- GIS service coverage where authoritative

Medium confidence:
- listing remarks
- legal-description parsing
- inferred owner clusters
- aerial interpretation

Lower-confidence / inferential:
- LLM classifications
- municipal posture interpretation if not clearly documented
- soft signals about seller readiness

---

## FILE: LANDOS_BUILD_ROADMAP.md

# BaseMod LandOS — Build Roadmap

## Phase 0 — Documentation & Memory Spine
## Phase 1 — Signal Engine
## Phase 2 — Municipal & Stallout Intelligence
## Phase 3 — Packaging Engine
## Phase 4 — Market Activation Layer
## Phase 5 — Transaction Resolution Layer
## Phase 6 — Flywheel / Network Effects

## Phase ordering logic
1. Memory first.
2. Signals second.
3. Packaging third.
4. Distribution fourth.
5. Transaction execution fifth.
6. Flywheel after real usage exists.

---

## FILE: CLAUDE.md

# CLAUDE.md — BaseMod LandOS Project Memory

## Project identity
You are working on **BaseMod LandOS — Event Mesh** (“Land Swarm”).

LandOS is the operating system that turns fragmented land supply into attainable homeownership inventory by mapping signals, waking the right agents, packaging homes that fit, and routing the market toward transaction.

## Non-negotiable architectural truths
1. LandOS is an event mesh, not a pipeline.
2. The moat is the wake-up logic.
3. Listings, clusters, and municipalities are co-equal trigger families.
4. Municipalities are first-class active objects, not passive metadata.
5. Historical stallouts and site condos are strategic supply wedges.
6. Packaging is a first-class system layer.
7. File-based memory is the source of truth, not chat memory.
8. Major changes must update the handoff and decisions log.

---

## FILE: CODEX_TASKING.md

# CODEX_TASKING.md — BaseMod LandOS Implementation Guide

## Before starting any task
Read:
1. 00_START_HERE.md
2. LANDOS_HANDOFF_MASTER.md
3. LANDOS_DECISIONS_LOG.md
4. the file for the relevant domain
5. this file

## Repo structure recommendation
```text
/docs
  /architecture
  /data
  /decisions
  /municipal
  /product
  /ops

/src
  /objects
  /events
  /triggers
  /agents
  /adapters
  /municipal
  /packaging
  /matching
  /transactions
  /shared
```

## Priority near-term build targets
1. canonical event envelope
2. object models
3. trigger engine scaffold
4. listing->parcel->municipality->cluster flow
5. historical plat stall detector
6. site condo detector
7. first packaging path

---

## FILE: README_PACKET_OVERVIEW.txt

BaseMod LandOS Handoff Packet

This packet contains the full foundational memory/docs kit for the project.

Primary files:
- 00_START_HERE.md
- LANDOS_HANDOFF_MASTER.md
- LANDOS_DECISIONS_LOG.md
- LANDOS_OBJECT_MODEL.md
- LANDOS_EVENT_LIBRARY.md
- LANDOS_TRIGGER_MATRIX.md
- LANDOS_AGENT_TEAMS.md
- LANDOS_DATA_SOURCES.md
- LANDOS_BUILD_ROADMAP.md
- CLAUDE.md
- CODEX_TASKING.md

Suggested next action:
Place these in your repo/project folder immediately and treat them as canonical.

