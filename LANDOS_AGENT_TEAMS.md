# BaseMod LandOS — Agent Teams

> This file defines the agent teams that perform bounded work inside the LandOS event mesh.
> It is the execution-layer companion to the trigger matrix: the trigger matrix defines what wakes what;
> this file defines what each agent team does when woken — its responsibilities, objects, inputs, outputs, and constraints.

---

## How agent teams fit into LandOS

### Relationship to the event library and trigger matrix
The event library (`LANDOS_EVENT_LIBRARY.md`) defines what events exist and what data they carry. The trigger matrix (`LANDOS_TRIGGER_MATRIX.md`) defines the routing rules — when an event arrives, what agent or process is woken, under what conditions, and with what guardrails. This file defines the teams that execute the woken work.

Agent teams do not decide when to run. The trigger engine decides. Agent teams receive a wake instruction (event + context), perform bounded work, and emit results — which may be new events, updated objects, or actions for human operators.

### Relationship to the object model
Each agent team reads from and writes to specific objects defined in `LANDOS_OBJECT_MODEL.md`. Teams should only touch the objects listed in their section below. If a team needs data from an object outside its scope, it reads it — it does not modify it.

### The moat is not the agents
Agent teams are replaceable execution units. The moat is the wake-up architecture: the typed event system, the object graph, the trigger rules, and the recursion controls. Agents perform bounded work; the trigger matrix orchestrates the system. A team can be rewritten, split, or merged without changing the architecture — as long as it honors its inputs, outputs, and object boundaries.

### Agents perform bounded work
Every agent run should be:
- **Scoped:** operates on a specific entity or small set of entities, not the whole database.
- **Traceable:** produces an AgentRun record with inputs, outputs, duration, and events emitted.
- **Idempotent where possible:** running the same agent on the same inputs should produce the same results.
- **Guardrailed:** respects cooldowns, materiality gates, and generation-depth limits enforced by the trigger engine.

---

## Team 1: Supply Intelligence Team

**Purpose:** Discover supply-side opportunity earlier and more accurately than the market.

### Core responsibilities
- Ingest MLS feed data and emit listing events (`listing_added`, `listing_status_changed`, `listing_expired`, `listing_price_reduced`, `listing_relisted`).
- Resolve parcel linkages — match listings to parcels via address, parcel number, or geo-match.
- Detect owner clusters — identify when multiple listings share an owner, agent, or office.
- Flag large-acreage listings (>= 5.0 acres) for split candidacy analysis.
- Detect market shock candidates (extreme price moves, unusual volume).
- Resolve parcel ownership and vacancy status from county/assessor data.

### Primary objects touched
- **Reads:** Listing, Parcel, Owner, Municipality (for scan freshness check)
- **Creates/updates:** Listing, Parcel (linkage + score update), Owner, OwnerCluster, DeveloperEntity (initial link)

### Representative events subscribed to
- `listing_added`, `listing_status_changed`, `listing_expired`, `listing_price_reduced`, `listing_relisted`
- `same_owner_listing_detected`, `owner_cluster_detected`, `owner_cluster_size_threshold_crossed`
- `agent_subdivision_program_detected`, `office_inventory_program_detected`
- `listing_cluster_expansion_required`

### Typical outputs produced
- Parcel-to-listing linkages (via `link` wake type)
- `listing_large_acreage_detected`, `listing_market_shock_candidate_detected`
- `same_owner_listing_detected`, `owner_cluster_detected`, `owner_cluster_size_threshold_crossed`
- `agent_subdivision_program_detected`, `office_inventory_program_detected`
- `parcel_linked_to_listing`, `parcel_owner_resolved`, `parcel_score_updated`
- `listing_municipal_scan_required`, `cluster_municipal_scan_required` (requests to Team 2)
- `listing_broker_note_required`, `cluster_broker_note_required` (requests to Team 4)

### Wake-up responsibilities
This team is woken by the trigger engine when listing-family and cluster/owner-family events arrive. It is the primary entry point for new market signals. Its outputs cascade to nearly every other team — municipal scans, stallout checks, packaging, and scoring all depend on supply intelligence.

### Human-in-the-loop points
- `listing_market_shock_candidate_detected` → operator notification (always).
- `listing_broker_note_required` / `cluster_broker_note_required` → Action for operator to create BrokerNote (Phase 2).

### Boundaries
- Does **not** scan municipal records — that is Team 2.
- Does **not** assess stallout or site-condo status — that is Team 3.
- Does **not** classify listing remarks for language signals — that is Team 4.
- Does **not** run SiteFit or packaging — that is Team 5.
- Does **not** route opportunities to market — that is Team 7.

---

## Team 2: Municipal Intelligence Team

**Purpose:** Turn municipal policy and process motion into structured events that reprice opportunity.

### Core responsibilities
- Scan municipal records: planning commission minutes, register of deeds, permit systems, zoning amendments, ordinance text, GIS data.
- Create MunicipalEvent objects for each discovered action (plat recordings, bond postings, road acceptances, permit pulls, infrastructure extensions, rule changes, etc.).
- Emit the corresponding `_detected` events into the mesh for each MunicipalEvent ingested.
- Evaluate rule changes to determine whether they favor land division — producing `municipality_rule_now_supports_split` when they do.
- Track municipality-level aggregate signals: permit activity trends, subdivision stagnation patterns, split capacity, frontage favorability.

### Primary objects touched
- **Reads:** Municipality, Subdivision, SiteCondoProject, Parcel (for geography scoping)
- **Creates/updates:** Municipality (fields: `last_municipal_event_at`, `land_division_posture`, `market_wake_score`), MunicipalEvent

### Representative events subscribed to
- `listing_municipal_scan_required` (from Team 1)
- `cluster_municipal_scan_required` (from Team 1)
- `human_requested_rescan` (when target is a municipality)
- Scheduled scans per stallout-scan frequency rules (30-day default per municipality)

### Typical outputs produced
- MunicipalEvent objects (one per discovered action)
- Raw detection events: `site_plan_approved_detected`, `plat_recorded_detected`, `engineering_approved_detected`, `permit_pulled_detected`, `roads_installed_detected`, `roads_accepted_detected`, `public_sewer_extension_detected`, `water_extension_detected`, `bond_posted_detected`, `bond_extension_detected`, `bond_released_detected`, `hoa_created_detected`, `master_deed_recorded_detected`, `municipality_infrastructure_extension_detected`, `municipality_rule_change_detected`
- Derived events: `municipality_rule_now_supports_split`, `municipality_split_capacity_increased`, `municipality_frontage_rules_favorable_detected`, `municipality_permit_activity_increased`, `municipality_incentive_program_detected`, `municipality_subdivision_stagnation_pattern_detected`
- Derived compound inputs: `site_condo_regime_detected`, `developer_control_active_detected`

### Wake-up responsibilities
This team is woken when listings or clusters need a municipality scanned, when scheduled scan intervals fire, or when a human operator requests a rescan. Its outputs are policy shockwaves — `municipality_rule_now_supports_split` can trigger jurisdiction-wide parcel rescoring (subject to blast-radius controls in the trigger matrix).

### Human-in-the-loop points
- Ambiguous rule-change interpretations may require human review before emitting `municipality_rule_now_supports_split`.
- `municipality_subdivision_stagnation_pattern_detected` → operator notification when 3+ subdivisions are stalled in a single municipality.

### Boundaries
- Does **not** draw stallout conclusions — it discovers and records municipal events. Stallout assessment is Team 3.
- Does **not** classify listing remarks or broker notes — that is Team 4.
- Does **not** rescore parcels directly — it emits events; the trigger engine routes rescoring to the appropriate scoring process.
- Does **not** manage incentive applications — it may discover programs (`municipality_incentive_program_detected`), but matching and applications are Team 6.

---

## Team 3: Stallout & Site-Condo Forensics Team

**Purpose:** Find stranded subdivisions and site condos, especially older projects invisible to live-market-only views.

### Core responsibilities
- Compare historical plats against current parcel vacancy to detect stalled subdivisions.
- Detect site-condo projects via master deed analysis, legal-description patterns, and MLS field detection.
- Assess vacancy ratios, infrastructure investment vs. vertical progress, bond-posted-but-no-progress patterns.
- Produce stallout and site-condo detection events that create Opportunities.
- Maintain and rescore `stall_score` on Subdivision and SiteCondoProject objects.

### Primary objects touched
- **Reads:** Subdivision, SiteCondoProject, Parcel, MunicipalEvent, Municipality, DeveloperEntity
- **Creates/updates:** Subdivision (`stall_score`, `stallout_flag`), SiteCondoProject (`stall_score`, vacancy assessment), Opportunity (type: `stalled_subdivision` or `stalled_site_condo`)

### Representative events subscribed to
- Municipal detection events that imply stall conditions: `roads_installed_majority_vacant_detected`, `permits_pulled_majority_vacant_detected`, `approved_no_vertical_progress_detected`, `bond_posted_no_progress_detected`, `bond_release_delay_detected`, `hoa_exists_majority_vacant_detected`
- `site_condo_regime_detected` (pipeline stage 1 → triggers project creation)
- `site_condo_project_detected` (pipeline stage 2 → triggers vacancy assessment)
- Scheduled stallout rescan intervals (30-day default per subdivision/project)
- Override signals: `bond_released_detected`, `permit_pulled_detected`, `roads_accepted_detected`, `listing_added` in a stalled area, `human_requested_rescan`

### Typical outputs produced
- `historical_plat_stall_detected`, `historical_subdivision_stall_detected`
- `site_condo_project_detected`, `site_condo_high_vacancy_detected`
- `partial_buildout_stagnation_detected`, `unfinished_site_condo_detected`
- Opportunity objects (types: `stalled_subdivision`, `stalled_site_condo`)
- Updated `stall_score` on Subdivision and SiteCondoProject objects

### Wake-up responsibilities
This team is woken by municipal detection events that carry stall signals, by the site-condo detection pipeline stages, and by scheduled scan intervals. Its outputs create Opportunities and link to DeveloperEntity for downstream exit-window analysis (developer/exit-window events, Family 5 in the trigger matrix).

### Human-in-the-loop points
- Complex stall assessments with low confidence may warrant human review before creating an Opportunity.
- Historical forensics for very old projects (10–15 years) may need human validation of data accuracy.

### Boundaries
- Does **not** scan municipal records — it consumes events produced by Team 2.
- Does **not** perform developer exit-window analysis — that is covered by developer/exit-window events and the trigger matrix routing to DeveloperEntity.
- Does **not** run packaging or fit analysis — that is Team 5.
- Does **not** create MunicipalEvent objects — it reads them.

---

## Team 4: Broker Notes & Market Intelligence Team

**Purpose:** Capture the non-obvious commercial truth hidden in remarks, broker patterns, and back-office notes.

### Core responsibilities
- Classify listing remarks using LLM analysis — detecting package language, fatigue language, restriction language, approval language, and utility language.
- Create and maintain BrokerNote objects (Phase 2) — structured intelligence extracted from broker conversations, agent remarks, and market observations.
- Detect broker-signaled flexibility for bulk or package deals.
- Provide the classification signals that feed developer exit-window analysis (package language is the #1 priority signal in the entire trigger matrix).

### Primary objects touched
- **Reads:** Listing (remarks text), OwnerCluster (context for broker note creation), DeveloperEntity (context)
- **Creates/updates:** BrokerNote (Phase 2)

### Representative events subscribed to
- `listing_added` → classify remarks (trigger rule: "listing_added → classify remarks")
- `listing_broker_note_required` (from Team 1, Phase 2)
- `cluster_broker_note_required` (from Team 1, Phase 2)

### Typical outputs produced
- `listing_package_language_detected` — priority 1 signal, triggers full downstream chain
- `listing_fatigue_language_detected` — developer/cluster fatigue scoring
- `listing_restriction_language_detected` — parcel environmental/restriction flags
- `listing_approval_language_detected` — parcel score boost from discovered approvals
- `listing_utility_language_detected` — parcel utility field updates
- `broker_signaled_bulk_flexibility_detected` (Phase 2) — developer flexibility signal
- BrokerNote objects (Phase 2)

### Wake-up responsibilities
This team is woken primarily by `listing_added` (every new listing with non-empty remarks is classified). Its single most important output — `listing_package_language_detected` — is priority 1 in the wake hierarchy and triggers cluster creation, opportunity creation, and developer analysis simultaneously.

### Human-in-the-loop points
- BrokerNote creation (Phase 2) is an Action assigned to a human operator — the system flags that a note is needed, but a human writes it.
- LLM classification results with low confidence may need human review.

### Boundaries
- Does **not** perform parcel rescoring — it emits classification events; the trigger engine routes rescoring.
- Does **not** create clusters or opportunities — those are downstream effects of its classification events.
- Does **not** do packaging or pricing — that is Team 5.
- Does **not** contact brokers or sellers — that is Team 7.

---

## Team 5: Packaging Team

**Purpose:** Turn raw land opportunity into a buyer-legible homeownership package.

### Core responsibilities
- Run geometry fit analysis — determine which BaseMod home models physically fit on a parcel (dimensions, shape, setbacks).
- Perform full SiteFit analysis — setback checks, utility assessment, access evaluation, environmental constraints.
- Estimate site work costs (Phase 2) — grading, foundation, utility connections, driveway, landscaping.
- Calculate all-in pricing (Phase 2) — land + home + site work + fees.
- Assess package readiness — determine when a complete land+home package is ready for market distribution.
- Flag fit assessments that need human review when automated confidence is insufficient.

### Primary objects touched
- **Reads:** Parcel (geometry, vacancy, utility fields, restrictions), HomeProduct, Opportunity, Municipality (zoning/setback context)
- **Creates/updates:** SiteFit, SiteWorkEstimate (Phase 2), PricePackage (Phase 2), Opportunity (status transitions: `scored` → `fit_checked` → `packaged`)

### Representative events subscribed to
- `opportunity_created` → first fit check (immediate priority)
- `parcel_vacancy_confirmed` → fit against confirmed-vacant parcel
- `parcel_geometry_fit_detected` → full SiteFit analysis
- `home_model_fit_detected` → pricing and opportunity update
- `utility_assumption_confident_detected` → pricing enablement
- Packaging regeneration triggers per trigger matrix rules (e.g., `listing_price_reduced` > 10%, `municipality_rule_now_supports_split`, `listing_restriction_language_detected`)
- `parcel_split_candidate_identified` → fit analysis for resultant lots (compound trigger `split_ready_parcel`)

### Typical outputs produced
- `parcel_geometry_fit_detected` — which home models can physically fit
- `home_model_fit_detected` — confirmed SiteFit result per parcel+home combination
- `utility_assumption_confident_detected` — utility assessment complete
- `site_work_estimate_completed` (Phase 2)
- `all_in_price_viable_detected` (Phase 2) — all-in price within viable range
- `package_ready_for_distribution` (Phase 2) — complete package ready for market
- `fit_requires_human_review` — Action for operator when confidence is low
- Updated SiteFit, SiteWorkEstimate, PricePackage objects
- Opportunity status transitions

### Wake-up responsibilities
This team is woken when new Opportunities are created (immediate first fit check), when parcels are confirmed vacant, when packaging regeneration is triggered by price changes or policy changes, and when fit results need downstream pricing. Its outputs advance Opportunities through the lifecycle and hand off to distribution (Team 7).

### Human-in-the-loop points
- `fit_requires_human_review` → Action assigned to operator with context about what was uncertain (site fit, utility, pricing, zoning).
- Manual review recommended when fit_confidence < 0.7 or when environmental/restriction flags are present.

### Boundaries
- Does **not** discover supply — it packages what other teams have found.
- Does **not** scan municipalities or assess stallouts — it reads municipal context.
- Does **not** distribute or market packages — that is Team 7.
- Does **not** manage transactions — that is Team 8.
- Does **not** handle incentive applications — it may incorporate incentive values into pricing (via `incentive_award_confirmed`), but incentive discovery and applications are Team 6.

---

## Team 6: Incentives & Policy Team

**Purpose:** Improve economics and unlockability through incentives and policy understanding.

### Core responsibilities
- Discover incentive programs — tax abatements, grants, density bonuses, infrastructure subsidies, down payment assistance.
- Match incentive programs against existing Opportunities by jurisdiction, property type, and eligibility criteria.
- Track incentive application lifecycle — from discovery through paperwork to award confirmation.
- Monitor incentive deadlines and escalate when deadlines approach.

### Primary objects touched
- **Reads:** IncentiveProgram, Opportunity, Municipality, Parcel
- **Creates/updates:** IncentiveProgram (Phase 2), IncentiveApplication (Phase 2), Opportunity (rescore with incentive boost)

### Representative events subscribed to
- `municipality_incentive_program_detected` (from Team 2)
- `listing_incentive_scan_required` (from Team 1)
- `incentive_detected` → match against opportunities
- `incentive_potential_match_detected` → opportunity rescore
- `incentive_deadline_upcoming` → escalate pending actions

### Typical outputs produced
- `incentive_detected` — new program discovered
- `incentive_potential_match_detected` — program matched to opportunity
- `incentive_application_required` — Action for operator to begin paperwork
- `incentive_deadline_upcoming` — escalation of pending applications
- `incentive_paperwork_started`, `incentive_paperwork_completed` — lifecycle tracking
- `incentive_award_confirmed` → triggers PricePackage update (incremental: `incentive_offset` field)
- Updated IncentiveProgram and IncentiveApplication objects

### Wake-up responsibilities
This team is woken when municipalities report new incentive programs, when listings trigger incentive scans, and when deadline timers fire. Its outputs directly improve opportunity economics — an `incentive_award_confirmed` event updates the PricePackage and can make a previously marginal opportunity viable.

### Human-in-the-loop points
- `incentive_application_required` → Action assigned to operator (paperwork is manual in Phase 2).
- `incentive_paperwork_started` and `incentive_paperwork_completed` are human-initiated events.
- Incentive eligibility interpretation may need human review for ambiguous programs.

### Boundaries
- Does **not** discover municipal records — it receives `municipality_incentive_program_detected` from Team 2.
- Does **not** run packaging or pricing — it provides incentive values that Team 5 incorporates.
- Does **not** do seller/buyer outreach — that is Team 7.
- Phase 2 scope — most incentive events are not active until Phase 2.

---

## Team 7: Market Activation Team

**Purpose:** Expose opportunities to sellers, brokers, and buyers in the right format.

### Core responsibilities
- Route packaged opportunities to distribution channels — marketplace, broker network, direct buyer outreach, MLS exposure.
- Match buyer search profiles and broker saved searches against packaged opportunities.
- Manage seller engagement — outreach initiation, response tracking, negotiation support.
- Track demand signals — buyer views, saves, inquiries, broker interest — and feed them back as opportunity rescore inputs.

### Primary objects touched
- **Reads:** Opportunity, PricePackage, SiteFit, Parcel, Municipality, HomeProduct
- **Creates/updates:** BuyerProfile (Phase 3+), BrokerProfile (Phase 3+), SavedSearch (Phase 3+), OutreachTask, Opportunity (status: → `distributed`, → `engaged`)

### Representative events subscribed to
- `package_ready_for_distribution` (from Team 5, Phase 2)
- `opportunity_ready_for_distribution` (Phase 2)
- `buyer_search_profile_created` (Phase 3+)
- `broker_saved_search_created` (Phase 3+)
- `seller_ready_to_transact` (Phase 2) — handoff trigger to Team 8

### Typical outputs produced
- `opportunity_ready_for_distribution` — opportunity routed to channels
- `buyer_search_matches_opportunity` (Phase 3+) — match notification
- `broker_interest_detected` (Phase 2) — demand signal for opportunity rescore
- `seller_engagement_started` (Phase 2) — outreach initiated
- `seller_ready_to_transact` (Phase 2) — seller willing to deal, triggers Team 8
- Opportunity status updates (→ `distributed`, → `engaged`)

### Wake-up responsibilities
This team is woken when packaging declares a package ready for distribution and when buyer/broker search activity occurs. It is the bridge between the supply/packaging engine and the transaction engine. Its demand-side signals (broker interest, buyer matches) feed back into opportunity scoring, creating a feedback loop that helps the system prioritize the most market-ready opportunities.

### Human-in-the-loop points
- Seller outreach is heavily human-driven — the system identifies who to contact and why, but a human makes the contact.
- Broker engagement and relationship management require human judgment.
- Pricing negotiation support is human-led.

### Boundaries
- Does **not** create packages — it distributes what Team 5 has packaged.
- Does **not** discover supply or scan municipalities — it operates on already-scored, already-packaged Opportunities.
- Does **not** close transactions or coordinate construction — that is Team 8.
- Phase 2/3+ scope — most distribution and demand events are not active until later phases.

---

## Team 8: Transaction Resolution Team

**Purpose:** Turn promising packaged opportunities into executed housing outcomes.

### Core responsibilities
- Confirm site feasibility — coordinate site visits, soil tests, surveys that go beyond automated SiteFit.
- Coordinate buyer readiness — financing, intent confirmation, deposit.
- Identify lender paths — match opportunity to available financing products.
- Identify contractor paths — match opportunity to construction contractors with capacity and geography fit.
- Assemble the final orderable package — land + home + site work + financing + contractor + timeline all confirmed.

### Primary objects touched
- **Reads:** Opportunity, PricePackage, SiteFit, Parcel, Municipality, HomeProduct, BuyerProfile (Phase 3+), BrokerProfile (Phase 3+)
- **Creates/updates:** TransactionPath (Phase 3+), ConstructionPath (Phase 3+), Opportunity (status: → `converted` or final pre-transaction state)

### Representative events subscribed to
- `seller_ready_to_transact` (from Team 7)
- `buyer_ready_to_proceed` (Phase 3+)
- `site_feasibility_confirmed` (Phase 3+)
- `lender_path_available` (Phase 3+)
- `contractor_path_available` (Phase 3+)

### Typical outputs produced
- `site_feasibility_confirmed` — feasibility independently verified
- `buyer_ready_to_proceed` — buyer intent confirmed
- `lender_path_available` — financing path identified
- `contractor_path_available` — construction path identified
- `orderable_package_created` — the culmination event; all components converged (priority 3, immediate routing)
- Opportunity status transitions to final pre-transaction state
- TransactionPath and ConstructionPath objects (Phase 3+)

### Wake-up responsibilities
This team is woken when a seller is ready to transact and when buyer, lender, and contractor signals arrive. `orderable_package_created` is the culmination event of the entire LandOS pipeline — it means a real housing outcome is imminent. This event triggers immediate operator notification.

### Human-in-the-loop points
- This is the most human-intensive team. Nearly every step requires human coordination:
  - Site visits and feasibility confirmation
  - Buyer conversations and financing coordination
  - Lender and contractor negotiations
  - Contract preparation and closing coordination
- The system provides structure, tracking, and signal routing. Humans execute the transaction.

### Boundaries
- Does **not** discover supply, scan municipalities, or assess stallouts.
- Does **not** run packaging — it consumes completed packages from Team 5.
- Does **not** manage incentive applications — that is Team 6.
- Does **not** do market activation or outreach — that is Team 7. Team 8 takes over once a seller is ready and a buyer is engaged.
- Phase 3+ scope — most transaction events are not active until later phases.

---

## Implementation sequencing note

Not all teams are active from Phase 1. The build sequence implied by the canonical docs:

- **Phase 1 (active):** Teams 1, 2, 3, 4, 5 (fit analysis only — no pricing yet)
- **Phase 2 (next):** Teams 5 (full pricing), 6, 7 (initial distribution)
- **Phase 3+ (later):** Teams 7 (full demand-side), 8

This matches the build roadmap: supply discovery → municipal intelligence → stallout/site-condo detection → packaging → distribution → transaction. Each team should be scaffolded in phase order, with the trigger matrix's phase-gating controlling which rules are active.
