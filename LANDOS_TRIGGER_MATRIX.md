# BaseMod LandOS — Trigger Matrix

> This file defines the routing rules that connect events to downstream work.
> It is the canonical reference for what wakes what, under what conditions,
> with what priority, and subject to what guardrails.

---

## Design principles

1. The trigger matrix is the routing brain. The event library defines what events exist and what they carry. The trigger matrix defines what happens when each event arrives — what agents wake, what objects get touched, under what conditions, and with what constraints.
2. The core unit of the matrix is the **trigger rule**, not the event type. A trigger rule combines an event, a condition, a wake target, a wake type, and guardrails. The same event type can have multiple trigger rules with different conditions and targets.
3. Every event must have at least one trigger rule, even if that rule is "log and take no downstream action." No event should arrive in the system with undefined routing.
4. Priority attaches to the trigger rule, not just the event. `listing_price_reduced` at 5% is not the same priority as `listing_price_reduced` at 25% inside a known cluster.
5. Guardrails are not afterthoughts — they are first-class components of every trigger rule. Cooldowns, materiality gates, blast-radius limits, and anti-loop controls are specified per rule or inherit from defaults.
6. All numeric thresholds (cooldowns, materiality, fan-out caps, score bands) in this document are **Phase 1 recommended defaults**. They are starting points calibrated for early operation with limited data. They should be tuned as the system accumulates real-world signal volume and processing experience. They are not eternal fixed truths.
7. The trigger matrix and the event library are companions. This file does not redefine events or payloads. It references them by canonical name.

---

## Wake-type taxonomy

Every trigger rule specifies one or more wake types — what kind of work the downstream agent or process performs. Wake types are named so that their cost, purpose, and scope are apparent.

### rescore
Recalculate a numeric score on an object (parcel opportunity_score, opportunity composite score, cluster fatigue_score, developer fatigue_score, subdivision stall_score).
- **Typical cost:** Medium. Reads object state + recent signals, runs scoring model, writes updated score.
- **Default cooldown:** 4 hours (parcel, opportunity), 24 hours (subdivision, site condo, municipality).
- **Example:** `listing_price_reduced` → rescore the linked Parcel's opportunity_score.

### rescan
Re-examine an entity or geography for new signals — pull fresh data, re-run detection logic, check for changes since last scan.
- **Typical cost:** Heavy. May involve external API calls, LLM processing, or multi-object analysis.
- **Default cooldown:** 24 hours (municipality), 12 hours (cluster), 30 days (stallout scan).
- **Example:** `owner_cluster_detected` → rescan the cluster's municipality for recent municipal events.

### create
Create a new first-class object in the system (Opportunity, OwnerCluster, SiteCondoProject, SiteFit, PricePackage).
- **Typical cost:** Medium to heavy. Object initialization, relationship linking, initial scoring.
- **Default cooldown:** None — creation is idempotent (dedupe_key prevents duplicates).
- **Example:** `historical_plat_stall_detected` → create an Opportunity of type `stalled_subdivision`.

### link
Establish or update a relationship between two existing objects (parcel-to-listing, parcel-to-cluster, owner-to-developer-entity).
- **Typical cost:** Light. Lookup + FK write.
- **Default cooldown:** None — linking is idempotent.
- **Example:** `listing_added` → link the Listing to its Parcel via address/parcel-number resolution.

### classify
Run LLM or rule-based classification on text content (listing remarks, broker notes, planning commission minutes, legal descriptions).
- **Typical cost:** Medium. LLM inference call + result storage.
- **Default cooldown:** Per-text-source, not per-object. Same remarks text should not be reclassified unless the classification model version changes.
- **Example:** `listing_added` → classify listing remarks for package language, fatigue language, restriction language, approval language, utility language.

### fit
Run a SiteFit, packaging, or pricing analysis for a specific parcel + home product combination.
- **Typical cost:** Heavy. Geometry analysis, setback checks, utility assessment, cost estimation.
- **Default cooldown:** 24 hours per parcel+home combination.
- **Example:** `parcel_vacancy_confirmed` → fit available HomeProducts against the confirmed-vacant parcel.

### notify
Alert a human operator, create an Action object, or push a message to an operator dashboard.
- **Typical cost:** Light. Write Action + optional push notification.
- **Default cooldown:** None — notifications are always delivered.
- **Example:** `recursion_limit_reached` → notify system operator.

### suppress
Mark an event or entity as suppressed — stop further processing. Typically triggered by human operator action.
- **Typical cost:** Light. Status update.
- **Default cooldown:** None.
- **Example:** `human_suppressed_event` → set the target event's status to `suppressed`.

### escalate
Increase the priority of an existing pending Action or trigger rule. Bumps something that was waiting into active processing.
- **Typical cost:** Light. Priority update.
- **Default cooldown:** None.
- **Example:** `incentive_deadline_upcoming` with <= 7 days → escalate any pending `incentive_application_required` Action.

---

## Routing-class assignment rules

Every event processed by the trigger engine is assigned a routing class that determines processing urgency and queue assignment. The event envelope carries an optional `routing_class` field. If present, it is used. If absent, the trigger engine assigns one based on these rules.

### Routing classes

- **immediate** — Process within seconds. Reserved for high-priority market signals and system alerts that lose value with delay.
- **standard** — Process within minutes. Normal operational cadence for most market events.
- **batch** — Process in next scheduled batch run. For bulk rescoring, municipality-wide rescans, and historical analysis that does not need real-time response.
- **background** — Process when resources allow. For speculative analysis, data enrichment, and non-time-sensitive housekeeping.

### Family-level defaults

These are defaults. Any specific trigger rule can override the family default.

| Family | Default Routing Class |
|---|---|
| Listing | `standard` |
| Cluster / owner | `standard` |
| Municipal process | `batch` |
| Historical stall | `batch` |
| Developer / exit | `standard` |
| Incentive | `batch` |
| Packaging | `standard` |
| Distribution / demand | `standard` |
| Transaction / execution | `standard` |
| Opportunity lifecycle | `standard` |
| Parcel state | `batch` |
| Human / operator | `immediate` |
| System / operational | `background` |

### Per-rule overrides

Specific trigger rules override family defaults when the signal carries special urgency or processing requirements. These overrides are noted in the trigger rule catalog below. Summary of the most important overrides:

| Event | Override | Reason |
|---|---|---|
| `listing_market_shock_candidate_detected` | → `immediate` | Extreme market signal, time-sensitive |
| `owner_cluster_detected` (5+ members) | → `immediate` | High-value multiplicative pattern |
| `municipality_rule_change_detected` | → `immediate` | Policy shockwave, must evaluate quickly |
| `municipality_rule_now_supports_split` | → `immediate` | Derived from rule change, jurisdiction-wide repricing |
| `developer_exit_window_detected` | → `immediate` | Time-sensitive acquisition opportunity |
| `incentive_deadline_upcoming` (≤ 7 days) | → `immediate` | Deadline-driven urgency |
| `opportunity_created` | → `immediate` | New opportunity needs immediate first scoring |
| `recursion_limit_reached` | → `immediate` | System alert, needs operator visibility |
| All human_operator events | → `immediate` | Human actions are always high priority |

### Dynamic upgrade rule

A normally `standard` or `batch` event can be dynamically upgraded to `immediate` if **all** of the following are true:
1. The event references an entity with `wake_priority <= 3` on any linked Opportunity.
2. The event is a raw event (new external data).
3. The entity has not been processed in the last 60 seconds (prevents upgrade storms).

---

## Priority hierarchy

Priority ranks trigger rules, not just event types. Priority 1 is highest (process first when multiple events compete for resources). Priority 10 is lowest.

The `wake_priority` field in the event envelope maps to this hierarchy. When multiple events are queued, the trigger engine processes them in priority order within each routing class.

### Phase 1 priority table

| Priority | Trigger Rule | Wake Target(s) | Wake Type(s) |
|---|---|---|---|
| 1 | `listing_package_language_detected` → cluster + opportunity analysis | OwnerCluster, Opportunity, DeveloperEntity | create, rescore, classify |
| 2 | `roads_installed_majority_vacant_detected` → stallout + opportunity creation | Subdivision, Opportunity, Parcel(s) | create, rescore, rescan |
| 3 | `permits_pulled_majority_vacant_detected` → stallout + opportunity creation | Subdivision, Opportunity, Parcel(s) | create, rescore |
| 4 | `municipality_rule_now_supports_split` → jurisdiction-wide parcel rescore | Parcel(s), Opportunity(s) | rescore, fit |
| 5 | `bond_posted_no_progress_detected` → stallout analysis | Subdivision, Opportunity | create, rescore |
| 6 | `listing_expired_in_cluster` (compound) → cluster reassessment | OwnerCluster, DeveloperEntity, Opportunity | rescore, escalate |
| 7 | `distressed_developer_with_activity` (compound) → exit-window analysis | DeveloperEntity, Opportunity | create, rescore |
| 8 | `agent_subdivision_program_detected` → cluster + developer analysis | OwnerCluster, DeveloperEntity | create, link, rescore |
| 9 | `hoa_exists_majority_vacant_detected` → stallout + site-condo analysis | Subdivision, SiteCondoProject, Opportunity | create, rescore |
| 10 | `split_ready_parcel` (compound) → fit + packaging analysis | Parcel, Opportunity, SiteFit | create, fit |

### Priority assignment for unlisted rules

Trigger rules not in the top 10 receive priority based on their wake type cost:
- **create** (new Opportunity or Cluster): priority 3–5
- **rescore**: priority 5–7
- **rescan**: priority 6–8
- **classify**: priority 7
- **fit**: priority 6–8
- **link**: priority 8
- **notify**: priority 5 (operator alerts) or 9 (informational)
- **suppress / escalate**: priority 4

---

## Trigger rule catalog

Rules are organized by the event family that produces the triggering event. Each rule specifies what happens when a specific event arrives under specific conditions.

**Rule format:**
- **Priority:** 1–10
- **Routing class:** immediate | standard | batch | background
- **Wake type:** rescore | rescan | create | link | classify | fit | notify | suppress | escalate
- **Condition:** when the rule fires (or "always")
- **Wake target:** what object or agent receives the wake
- **Cooldown:** how long before the same wake can fire again for the same target
- **Notes:** additional context

Rules marked with [Phase 2] or [Phase 3+] are defined for completeness but are not active until those phases are enabled.

---

### Family 1: Listing events → trigger rules

#### listing_added → link to parcel
- **Priority:** 5 | **Routing:** standard | **Wake type:** link
- **Condition:** Always.
- **Wake target:** Parcel (via address/parcel-number resolution)
- **Cooldown:** None (idempotent).

#### listing_added → classify remarks
- **Priority:** 7 | **Routing:** standard | **Wake type:** classify
- **Condition:** Listing has non-empty remarks.
- **Wake target:** LLM classifier — produces `listing_package_language_detected`, `listing_fatigue_language_detected`, `listing_restriction_language_detected`, `listing_approval_language_detected`, `listing_utility_language_detected` as applicable.
- **Cooldown:** Per-listing. Same listing remarks are not reclassified unless model version changes.

#### listing_added → check cluster membership
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescan
- **Condition:** Always.
- **Wake target:** Cluster detection agent — checks if this listing's owner, agent, or office matches an existing cluster or seeds a new one.
- **Cooldown:** None (new listing is always checked).

#### listing_added → check municipality scan freshness
- **Priority:** 7 | **Routing:** batch | **Wake type:** rescan
- **Condition:** Listing's municipality has not been scanned in the last 30 days.
- **Wake target:** Municipality — triggers `listing_municipal_scan_required`.
- **Cooldown:** 30 days per municipality.

#### listing_added → rescore parcel
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Listing is successfully linked to a Parcel.
- **Wake target:** Parcel opportunity_score.
- **Cooldown:** 4 hours per parcel, overridden by this raw event.

#### listing_added → check large acreage
- **Priority:** 6 | **Routing:** standard | **Wake type:** classify
- **Condition:** Listing acreage >= 5.0 acres (Phase 1 default threshold).
- **Wake target:** Listing analysis agent — produces `listing_large_acreage_detected`.
- **Cooldown:** None (per-listing, one-time check).

#### listing_status_changed → update parcel + opportunity state
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Linked Parcel (rescore), linked Opportunity (status check).
- **Cooldown:** 4 hours per parcel.

#### listing_expired → rescore parcel + check cluster compound
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always. This event is always raw, always emitted directly by MLS ingestion pipeline alongside `listing_status_changed`. Never derived.
- **Wake target:** Linked Parcel (rescore), compound trigger evaluation for `listing_expired_in_cluster`.
- **Cooldown:** 4 hours per parcel, overridden by this raw event.
- **Notes:** Elevated from generic `listing_status_changed` because expirations inside clusters are a priority-6 compound trigger.

#### listing_price_reduced → rescore parcel + check packaging
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Linked Parcel (rescore). If `percent_change > 10%` and an Opportunity exists at status `fit_checked` or `packaged`, also trigger packaging regeneration (see Packaging Regeneration Rules below).
- **Cooldown:** 4 hours per parcel.

#### listing_relisted → rescore parcel + check cluster
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Linked Parcel (rescore), cluster detection agent (check if relist pattern signals fatigue).
- **Cooldown:** 4 hours per parcel, overridden by this raw event.

#### listing_cdom_threshold_crossed → rescore parcel + check stallout
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Linked Parcel (rescore with CDOM signal), linked Subdivision if applicable (stallout check).
- **Cooldown:** 4 hours per parcel.

#### listing_large_acreage_detected → check split candidacy
- **Priority:** 6 | **Routing:** standard | **Wake type:** classify
- **Condition:** Always.
- **Wake target:** Split analysis agent — evaluates frontage, municipality posture, estimated resultant lots. May produce `parcel_split_candidate_identified`.
- **Cooldown:** 24 hours per parcel.

#### listing_package_language_detected → cluster + opportunity + developer analysis
- **Priority:** 1 | **Routing:** immediate | **Wake type:** create, rescore, classify
- **Condition:** Always. This is the #1 priority signal.
- **Wake target:** Cluster detection agent (create or expand cluster), Opportunity (create if none exists), DeveloperEntity (check for exit signals).
- **Cooldown:** 12 hours per cluster.
- **Notes:** Package language is the strongest single signal of developer exit readiness. It immediately activates the full downstream chain.

#### listing_fatigue_language_detected → developer + cluster rescore
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** DeveloperEntity (fatigue_score rescore), linked OwnerCluster (fatigue_score rescore).
- **Cooldown:** 12 hours per developer entity.

#### listing_restriction_language_detected → parcel flag + fit check
- **Priority:** 7 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Linked Parcel (update environmental/restriction flags), SiteFit (recheck if fit exists).
- **Cooldown:** 24 hours per parcel.

#### listing_approval_language_detected → parcel rescore + municipality check
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Linked Parcel (rescore — approvals increase opportunity), Municipality (check if approval is recorded in municipal events).
- **Cooldown:** 24 hours per parcel.

#### listing_utility_language_detected → parcel utility update
- **Priority:** 7 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Linked Parcel (update utility fields), SiteFit (recheck utility analysis if fit exists).
- **Cooldown:** 24 hours per parcel.

#### listing_broker_note_required → create action [Phase 2]
- **Priority:** 7 | **Routing:** standard | **Wake type:** notify
- **Condition:** Always.
- **Wake target:** Action (type: broker_note_creation, assigned to operator).
- **Cooldown:** 7 days per listing.

#### listing_cluster_expansion_required → cluster rescan
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescan
- **Condition:** Always.
- **Wake target:** Cluster detection agent — expand search around the candidate entity.
- **Cooldown:** 12 hours per cluster candidate.

#### listing_municipal_scan_required → municipality rescan
- **Priority:** 7 | **Routing:** batch | **Wake type:** rescan
- **Condition:** Municipality has not been scanned in last 30 days.
- **Wake target:** Municipal scan agent.
- **Cooldown:** 30 days per municipality.

#### listing_incentive_scan_required → incentive check [Phase 2]
- **Priority:** 8 | **Routing:** batch | **Wake type:** rescan
- **Condition:** Municipality has applicable incentive programs not yet matched.
- **Wake target:** Incentives matching agent.
- **Cooldown:** 30 days per municipality.

#### listing_market_shock_candidate_detected → immediate alert + rescore
- **Priority:** 3 | **Routing:** immediate | **Wake type:** rescore, notify
- **Condition:** Always.
- **Wake target:** Linked Parcel (rescore), linked Opportunity (rescore), operator notification.
- **Cooldown:** None — shocks are always processed.

---

### Family 2: Cluster / owner events → trigger rules

#### same_owner_listing_detected → cluster check
- **Priority:** 6 | **Routing:** standard | **Wake type:** create, link
- **Condition:** Always.
- **Wake target:** Cluster detection agent — create or expand OwnerCluster.
- **Cooldown:** 12 hours per owner.

#### owner_cluster_detected → full downstream chain
- **Priority:** 4 | **Routing:** standard (immediate if 5+ members) | **Wake type:** rescan, rescore, create
- **Condition:** Always.
- **Wake target:** Municipality rescan (if not recently scanned), all cluster Parcels (rescore), Opportunity creation (if cluster meets threshold), DeveloperEntity check.
- **Cooldown:** 12 hours per cluster.

#### owner_cluster_size_threshold_crossed → cluster rescore + opportunity check
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore, create
- **Condition:** Always.
- **Wake target:** OwnerCluster (fatigue_score rescore), Opportunity (create or rescore if threshold >= 5).
- **Cooldown:** 12 hours per cluster.

#### agent_subdivision_program_detected → cluster + developer + opportunity
- **Priority:** 8 (per priority hierarchy) | **Routing:** standard | **Wake type:** create, link, rescore
- **Condition:** Always.
- **Wake target:** OwnerCluster (create/expand), DeveloperEntity (link agent to developer), Opportunity (create if subdivision has vacancy).
- **Cooldown:** 12 hours per agent+subdivision pair.

#### office_inventory_program_detected → cluster + developer analysis
- **Priority:** 7 | **Routing:** standard | **Wake type:** create, link, rescore
- **Condition:** Always.
- **Wake target:** OwnerCluster (create/expand), DeveloperEntity (link office program to developer).
- **Cooldown:** 12 hours per office+geography pair.

#### cluster_municipal_scan_required → municipality rescan
- **Priority:** 7 | **Routing:** batch | **Wake type:** rescan
- **Condition:** Municipality not recently scanned (30-day default).
- **Wake target:** Municipal scan agent.
- **Cooldown:** 30 days per municipality.

#### cluster_broker_note_required → create action [Phase 2]
- **Priority:** 7 | **Routing:** standard | **Wake type:** notify
- **Condition:** Always.
- **Wake target:** Action (type: broker_note_creation for cluster context).
- **Cooldown:** 7 days per cluster.

---

### Family 3: Municipal process events → trigger rules

All municipal process detection events follow a common routing pattern: they update the Municipality and linked Subdivision/SiteCondoProject objects, then trigger parcel rescoring for affected parcels.

#### Common municipal detection routing pattern

The following events share this routing logic: `site_plan_approved_detected`, `plat_recorded_detected`, `engineering_approved_detected`, `permit_pulled_detected`, `roads_installed_detected`, `roads_accepted_detected`, `public_sewer_extension_detected`, `water_extension_detected`, `bond_posted_detected`, `bond_extension_detected`, `bond_released_detected`, `hoa_created_detected`, `master_deed_recorded_detected`, `municipality_infrastructure_extension_detected`.

For each:
- **Priority:** 6 | **Routing:** batch | **Wake type:** rescore, link
- **Condition:** Always.
- **Wake target:** Municipality (update `last_municipal_event_at`), linked Subdivision or SiteCondoProject (rescore stall_score if applicable), affected Parcels (rescore opportunity_score if parcel_ids are present in the MunicipalEvent).
- **Cooldown:** 24 hours per subdivision/project. Per-parcel cooldown of 4 hours, overridden by raw municipal events.

#### Elevated municipal detection rules

These municipal events have additional routing beyond the common pattern:

#### roads_installed_majority_vacant_detected → stallout + opportunity creation
- **Priority:** 2 | **Routing:** immediate | **Wake type:** create, rescore, rescan
- **Condition:** Always. This is priority #2 in the hierarchy.
- **Wake target:** Subdivision (stallout flag + stall_score), Opportunity (create type `stalled_subdivision` if none exists), all vacant Parcels in the subdivision (rescore).
- **Cooldown:** 30 days per subdivision (stallout scan frequency default).
- **Notes:** Roads installed + majority vacant is one of the strongest stall signals. It indicates significant infrastructure investment that was never recovered through home construction.

#### permits_pulled_majority_vacant_detected → stallout analysis
- **Priority:** 3 | **Routing:** standard | **Wake type:** create, rescore
- **Condition:** Always.
- **Wake target:** Subdivision (stallout analysis), Opportunity (create if vacancy_ratio > 0.5).
- **Cooldown:** 30 days per subdivision.

#### approved_no_vertical_progress_detected → stallout analysis
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore, create
- **Condition:** years_since_approval >= 3.0 (Phase 1 default).
- **Wake target:** Subdivision/SiteCondoProject (stall_score rescore), Opportunity (create if none exists and vacancy is high).
- **Cooldown:** 30 days per subdivision.

#### bond_posted_no_progress_detected → stallout analysis
- **Priority:** 5 | **Routing:** standard | **Wake type:** create, rescore
- **Condition:** Always. Priority #5 in hierarchy.
- **Wake target:** Subdivision (stall analysis), Opportunity (create if warranted).
- **Cooldown:** 30 days per subdivision.

#### bond_release_delay_detected → stallout + notify
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore, notify
- **Condition:** delay_days >= 90 (Phase 1 default).
- **Wake target:** Subdivision (stall_score adjustment), operator notification.
- **Cooldown:** 30 days per bond.

#### bond_released_detected → stallout rescan
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescan
- **Condition:** Always. A bond release is a meaningful positive or administrative signal.
- **Wake target:** Subdivision (rescan — did conditions actually get met, or did the bond lapse?), Subdivision bond_status update to `released`.
- **Cooldown:** 24 hours per subdivision (overrides the 30-day stallout scan default because a bond release is a significant state change).
- **Notes:** This event was added to close a gap — every MunicipalEvent type now has a corresponding detection event.

#### site_condo_regime_detected → project identification
- **Priority:** 5 | **Routing:** standard | **Wake type:** create, link
- **Condition:** Always. This is stage 1 of the site-condo detection pipeline.
- **Wake target:** Site-condo detection agent — create SiteCondoProject object if one does not exist, link to parcels/units. Produces `site_condo_project_detected`.
- **Cooldown:** None (creation is idempotent via dedupe).
- **Notes:** This event records the *structural/legal* discovery that a condo regime exists on this land (master deed, legal description pattern, MLS condo field). It does not assess development status — that's downstream.

#### developer_control_active_detected → developer + stallout analysis
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore, link
- **Condition:** years_under_developer_control >= 3.0 (Phase 1 default — developer control lasting this long is a signal).
- **Wake target:** DeveloperEntity (link if not already linked, fatigue_score rescore), Subdivision/SiteCondoProject (stall_score rescore).
- **Cooldown:** 24 hours per project.

#### hoa_exists_majority_vacant_detected → stallout + opportunity
- **Priority:** 9 | **Routing:** standard | **Wake type:** create, rescore
- **Condition:** Always. Priority #9 in hierarchy.
- **Wake target:** Subdivision/SiteCondoProject (stall_score), Opportunity (create if none exists).
- **Cooldown:** 30 days per project.

#### municipality_rule_change_detected → evaluate split impact
- **Priority:** 3 | **Routing:** immediate | **Wake type:** classify
- **Condition:** Always. This is a raw event — the factual discovery that a municipality changed its rules. Discovered from authoritative records (ordinance text, planning commission minutes, zoning amendments).
- **Wake target:** Municipal intelligence agent — evaluate whether the rule change favors land division. If it does, produces `municipality_rule_now_supports_split` (derived).
- **Cooldown:** None — rule changes are always processed.
- **Notes:** This is the raw counterpart to the derived `municipality_rule_now_supports_split`. The raw event records the fact; the derived event records the system's conclusion about its impact on splits.

#### municipality_rule_now_supports_split → jurisdiction-wide parcel rescore
- **Priority:** 4 | **Routing:** immediate | **Wake type:** rescore, fit
- **Condition:** Always. This is a derived event — the system's conclusion that a rule change favors land division. Priority #4 in hierarchy.
- **Wake target:** All qualifying Parcels in the municipality (see Blast-Radius Controls below for fan-out rules). Qualifying means: `acreage >= 2.0 AND vacancy_status IN (vacant, partially_improved)`. Also rescore all existing Opportunities in the municipality.
- **Cooldown:** 24 hours per municipality (overridden by the rule change itself).
- **Notes:** This is a policy shockwave that can reprice every qualifying parcel in the jurisdiction. Fan-out must be controlled (see Blast-Radius Controls).

#### municipality_split_capacity_increased → parcel rescore
- **Priority:** 6 | **Routing:** batch | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Qualifying Parcels in the municipality (same filter as above but processed in batch).
- **Cooldown:** 24 hours per municipality.

#### municipality_frontage_rules_favorable_detected → parcel rescore
- **Priority:** 6 | **Routing:** batch | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Large-acreage Parcels in the municipality (acreage >= 5.0).
- **Cooldown:** 24 hours per municipality.

#### municipality_permit_activity_increased → municipality rescore
- **Priority:** 7 | **Routing:** batch | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Municipality object only (update `market_wake_score`). Does NOT trigger individual parcel rescoring — the municipality score change will be picked up in the next batch cycle.
- **Cooldown:** 24 hours per municipality.

#### municipality_incentive_program_detected → incentive matching [Phase 2]
- **Priority:** 7 | **Routing:** batch | **Wake type:** rescan
- **Condition:** Always.
- **Wake target:** Incentives matching agent — check all Opportunities in the municipality for potential matches.
- **Cooldown:** 30 days per municipality.

#### municipality_subdivision_stagnation_pattern_detected → municipality-wide stallout scan
- **Priority:** 5 | **Routing:** batch | **Wake type:** rescan
- **Condition:** stalled_subdivision_count >= 3 (Phase 1 default).
- **Wake target:** All Subdivisions in the municipality (stall rescore), operator notification.
- **Cooldown:** 30 days per municipality.

---

### Family 4: Historical stall / site-condo events → trigger rules

#### historical_plat_stall_detected → opportunity creation
- **Priority:** 4 | **Routing:** standard | **Wake type:** create, rescore
- **Condition:** vacancy_ratio >= 0.4 AND years_since_plat >= 5.0 (Phase 1 defaults).
- **Wake target:** Opportunity (create type `stalled_subdivision`), Subdivision (stall_score rescore), vacant Parcels (rescore).
- **Cooldown:** 30 days per subdivision.

#### historical_subdivision_stall_detected → opportunity creation + developer check
- **Priority:** 4 | **Routing:** standard | **Wake type:** create, rescore, link
- **Condition:** stall_confidence >= 0.6 (Phase 1 default).
- **Wake target:** Opportunity (create if none exists), DeveloperEntity (link if developer is identifiable, fatigue_score rescore).
- **Cooldown:** 30 days per subdivision.

#### site_condo_project_detected → vacancy assessment
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescan, create
- **Condition:** Always. This is stage 2 of the site-condo detection pipeline — a SiteCondoProject object was created.
- **Wake target:** Site-condo detection agent — assess vacancy ratio, unit count, age. May produce `site_condo_high_vacancy_detected`.
- **Cooldown:** 30 days per project.

#### site_condo_high_vacancy_detected → opportunity creation
- **Priority:** 5 | **Routing:** standard | **Wake type:** create, rescore
- **Condition:** vacancy_ratio >= 0.4 AND age_years >= 3.0 (Phase 1 defaults). This is stage 3 of the pipeline.
- **Wake target:** Opportunity (create type `stalled_site_condo`), SiteCondoProject (stall_score rescore).
- **Cooldown:** 30 days per project.

#### unfinished_site_condo_detected → opportunity creation + developer analysis
- **Priority:** 5 | **Routing:** standard | **Wake type:** create, rescore, link
- **Condition:** Always. This is stage 4 (the stall conclusion) of the site-condo detection pipeline.
- **Wake target:** Opportunity (create or rescore), DeveloperEntity (link and fatigue_score rescore), vacant Parcels/units (rescore).
- **Cooldown:** 30 days per project.
- **Notes:** This event's `event_family` is `historical_stall`, not `municipal_process`. It was moved here because it is a stall conclusion, not a municipal process discovery.

#### partial_buildout_stagnation_detected → opportunity + stallout
- **Priority:** 5 | **Routing:** standard | **Wake type:** create, rescore
- **Condition:** years_since_last_build >= 3.0 (Phase 1 default).
- **Wake target:** Opportunity (create type `stalled_subdivision`), Subdivision (stall_score rescore).
- **Cooldown:** 30 days per subdivision.

---

### Family 5: Developer / exit-window events → trigger rules

#### developer_entity_distress_detected → compound check + opportunity
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore, create
- **Condition:** distress_confidence >= 0.6 (Phase 1 default).
- **Wake target:** DeveloperEntity (fatigue_score update), compound trigger evaluation for `distressed_developer_with_activity`, Opportunity (create type `developer_exit` if cluster/subdivision has high vacancy).
- **Cooldown:** 24 hours per developer entity.

#### remaining_inventory_program_detected → opportunity + developer rescore
- **Priority:** 4 | **Routing:** standard | **Wake type:** create, rescore
- **Condition:** remaining_lot_count >= 3 (Phase 1 default).
- **Wake target:** Opportunity (create type `developer_exit`), DeveloperEntity (fatigue_score rescore).
- **Cooldown:** 24 hours per developer entity.

#### coordinated_broker_liquidation_detected → developer + cluster rescore
- **Priority:** 4 | **Routing:** standard | **Wake type:** rescore, link
- **Condition:** lot_count >= 3 (Phase 1 default).
- **Wake target:** DeveloperEntity (fatigue_score rescore), OwnerCluster (fatigue_score rescore).
- **Cooldown:** 24 hours per developer entity.

#### subdivision_sellout_strategy_detected → developer + opportunity
- **Priority:** 4 | **Routing:** standard | **Wake type:** rescore, create
- **Condition:** confidence >= 0.6 (Phase 1 default).
- **Wake target:** DeveloperEntity (exit_window_flag check), Opportunity (create or rescore).
- **Cooldown:** 24 hours per subdivision.

#### developer_exit_window_detected → immediate opportunity + notify
- **Priority:** 3 | **Routing:** immediate | **Wake type:** create, rescore, notify
- **Condition:** exit_confidence >= 0.7 (Phase 1 default).
- **Wake target:** Opportunity (create type `developer_exit` with high priority), operator notification (high-value acquisition opportunity), OwnerCluster (rescore).
- **Cooldown:** 24 hours per developer entity.

#### broker_signaled_bulk_flexibility_detected → developer + opportunity rescore [Phase 2]
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore
- **Condition:** confidence >= 0.5 (Phase 1 default).
- **Wake target:** DeveloperEntity (fatigue_score input), linked Opportunity (rescore).
- **Cooldown:** 7 days per listing/cluster.

---

### Family 6: Incentive events → trigger rules [Phase 2]

#### incentive_detected → match against opportunities
- **Priority:** 7 | **Routing:** batch | **Wake type:** rescan
- **Condition:** Always.
- **Wake target:** Incentives matching agent — check all Opportunities in the program's jurisdiction.
- **Cooldown:** 30 days per program.

#### incentive_potential_match_detected → opportunity rescore
- **Priority:** 7 | **Routing:** standard | **Wake type:** rescore
- **Condition:** match_confidence >= 0.5.
- **Wake target:** Opportunity (rescore with incentive boost).
- **Cooldown:** 7 days per opportunity+program pair.

#### incentive_application_required → create action
- **Priority:** 6 | **Routing:** standard | **Wake type:** notify
- **Condition:** Always.
- **Wake target:** Action (type: incentive_application, with deadline if known).
- **Cooldown:** None.

#### incentive_deadline_upcoming → escalate action
- **Priority:** 5 (→ immediate if days_remaining <= 7) | **Routing:** standard (→ immediate) | **Wake type:** escalate
- **Condition:** days_remaining <= 30.
- **Wake target:** Existing pending incentive application Action (escalate priority).
- **Cooldown:** None — deadline alerts always fire.

#### incentive_paperwork_started → log only
- **Priority:** 9 | **Routing:** background | **Wake type:** — (no downstream wake)
- **Condition:** Always.
- **Notes:** Recorded for audit trail and UI state. No downstream trigger.

#### incentive_paperwork_completed → log only
- **Priority:** 9 | **Routing:** background | **Wake type:** — (no downstream wake)
- **Condition:** Always.
- **Notes:** Same as above.

#### incentive_award_confirmed → opportunity rescore + packaging update
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Linked Opportunity (rescore with confirmed incentive value), PricePackage (incremental update with incentive_offset).
- **Cooldown:** None — award confirmation is always processed.

---

### Family 7: Packaging events → trigger rules

#### parcel_geometry_fit_detected → create SiteFit
- **Priority:** 6 | **Routing:** standard | **Wake type:** fit
- **Condition:** Always.
- **Wake target:** Packaging agent — run full SiteFit analysis for each fitting home product. Produces `home_model_fit_detected`.
- **Cooldown:** 24 hours per parcel+home combination.

#### home_model_fit_detected → pricing + opportunity update
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore, create
- **Condition:** fit_result IN (fits, marginal).
- **Wake target:** Opportunity (status → `fit_checked`), PricePackage (create/update for this parcel+home combination).
- **Cooldown:** 24 hours per parcel+home combination.

#### utility_assumption_confident_detected → pricing enablement
- **Priority:** 7 | **Routing:** standard | **Wake type:** rescore
- **Condition:** utility_confidence >= 0.7 (Phase 1 default).
- **Wake target:** SiteFit (update utility fields), PricePackage (enable pricing if other prerequisites are met).
- **Cooldown:** 24 hours per parcel.

#### site_work_estimate_completed → price package creation [Phase 2]
- **Priority:** 6 | **Routing:** standard | **Wake type:** create, rescore
- **Condition:** Always.
- **Wake target:** PricePackage (create or update with site work costs), Opportunity (rescore with pricing data).
- **Cooldown:** 24 hours per parcel+home combination.

#### all_in_price_viable_detected → opportunity advancement [Phase 2]
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Opportunity (status → `packaged`), produces `package_ready_for_distribution`.
- **Cooldown:** 24 hours per opportunity.

#### package_ready_for_distribution → distribution enablement [Phase 2]
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore
- **Condition:** feasibility_confidence >= 0.6 (Phase 1 default).
- **Wake target:** Opportunity (status → `distributed`), produces `opportunity_ready_for_distribution`.
- **Cooldown:** 24 hours per opportunity.
- **Notes:** This is the packaging system declaring the package complete. `opportunity_ready_for_distribution` (Family 8) is the distribution system declaring it routable to channels. Intentionally a two-step handoff.

#### fit_requires_human_review → create action
- **Priority:** 5 | **Routing:** standard | **Wake type:** notify
- **Condition:** Always.
- **Wake target:** Action (type: fit_review, assigned to operator with context about what was uncertain).
- **Cooldown:** 7 days per parcel+home combination.

---

### Family 8: Distribution / demand events → trigger rules [Phase 2/3+]

#### buyer_search_profile_created → match against opportunities [Phase 3+]
- **Priority:** 7 | **Routing:** standard | **Wake type:** rescan
- **Wake target:** Matching engine — find Opportunities that match buyer criteria.
- **Cooldown:** None.

#### buyer_search_matches_opportunity → notify + rescore [Phase 3+]
- **Priority:** 6 | **Routing:** standard | **Wake type:** notify, rescore
- **Wake target:** Opportunity (demand signal rescore), broker/buyer notification.
- **Cooldown:** 24 hours per buyer+opportunity pair.

#### broker_saved_search_created → match against opportunities [Phase 3+]
- **Priority:** 7 | **Routing:** standard | **Wake type:** rescan
- **Wake target:** Matching engine.
- **Cooldown:** None.

#### broker_interest_detected → opportunity rescore [Phase 2]
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Opportunity (demand signal boost to composite score).
- **Cooldown:** 24 hours per broker+opportunity pair.

#### seller_engagement_started → opportunity update [Phase 2]
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Opportunity (status → `engaged`).
- **Cooldown:** None.

#### seller_ready_to_transact → opportunity advancement [Phase 2]
- **Priority:** 4 | **Routing:** standard | **Wake type:** rescore, notify
- **Condition:** Always.
- **Wake target:** Opportunity (rescore with seller-ready signal), operator notification.
- **Cooldown:** None.

#### opportunity_ready_for_distribution → channel routing [Phase 2]
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescan
- **Condition:** Always.
- **Wake target:** Distribution engine — route to marketplace, broker network, etc.
- **Cooldown:** 24 hours per opportunity.

---

### Family 9: Transaction / execution events → trigger rules [Phase 3+]

All transaction events follow a similar pattern: update the Opportunity status and notify the operator.

#### site_feasibility_confirmed → opportunity advancement
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore, notify
- **Wake target:** Opportunity (rescore + status update), operator notification.

#### buyer_ready_to_proceed → opportunity advancement
- **Priority:** 4 | **Routing:** standard | **Wake type:** rescore, notify
- **Wake target:** Opportunity (status → next phase), operator notification.

#### lender_path_available → opportunity advancement
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore
- **Wake target:** Opportunity (financing path confirmed).

#### contractor_path_available → opportunity advancement
- **Priority:** 5 | **Routing:** standard | **Wake type:** rescore
- **Wake target:** Opportunity (construction path confirmed).

#### orderable_package_created → final convergence notification
- **Priority:** 3 | **Routing:** immediate | **Wake type:** notify
- **Wake target:** Operator notification (transaction-ready opportunity), Opportunity (status → final pre-transaction state).
- **Notes:** This is the culmination event. All components converged. High priority.

---

### Family 10: Opportunity lifecycle events → trigger rules

#### opportunity_created → first scoring + fit check
- **Priority:** 3 | **Routing:** immediate | **Wake type:** rescore, fit
- **Condition:** Always.
- **Wake target:** Scoring engine (compute initial opportunity_score), Packaging agent (check if any HomeProducts fit the parcels).
- **Cooldown:** None — creation triggers immediate first assessment.

#### opportunity_score_changed → downstream rescore (with anti-loop)
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Only emitted if `abs(score_delta) >= 0.05` (materiality gate). Subject to anti-loop guardrails (see Anti-Loop Guardrails section).
- **Wake target:** Linked Parcels (rescore, but see anti-loop one-direction rule — if this event was caused by a `parcel_score_updated`, the parcel rescore is suppressed within this causal chain).
- **Cooldown:** 4 hours per opportunity.

#### opportunity_status_changed → state-dependent routing
- **Priority:** 5 | **Routing:** standard | **Wake type:** varies
- **Condition:** Always.
- **Wake target:** Depends on the transition:
  - `detected → scored`: trigger fit analysis.
  - `scored → fit_checked`: trigger packaging.
  - `fit_checked → packaged`: trigger distribution readiness check.
  - `packaged → distributed`: log only (distribution system handles routing).
  - `→ rejected`: log + notify operator.
  - `→ stale`: log + queue for rescan.
- **Cooldown:** None — status transitions are always processed.

#### opportunity_rejected → log + notify
- **Priority:** 6 | **Routing:** standard | **Wake type:** notify
- **Condition:** Always.
- **Wake target:** Operator notification (with rejection reason for learning), log for analytics.
- **Cooldown:** None.

#### opportunity_stale → rescan queue
- **Priority:** 8 | **Routing:** batch | **Wake type:** rescan
- **Condition:** days_inactive >= 90 (Phase 1 default).
- **Wake target:** Linked Parcels (rescan for fresh signals), Municipality (check for new events).
- **Cooldown:** 30 days per opportunity.

---

### Family 11: Parcel state-change events → trigger rules

#### parcel_linked_to_listing → rescore + cluster check
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore, rescan
- **Condition:** Always.
- **Wake target:** Parcel (rescore with listing data), Cluster detection agent (check if this parcel's owner/agent matches an existing cluster).
- **Cooldown:** 4 hours per parcel, overridden by this event (new linkage is significant).

#### parcel_owner_resolved → cluster check + developer check
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescan, link
- **Condition:** Always.
- **Wake target:** Cluster detection agent (check if owner matches clusters), DeveloperEntity resolution (check if owner is a known developer).
- **Cooldown:** 4 hours per parcel.

#### parcel_score_updated → opportunity rescore (with anti-loop)
- **Priority:** 6 | **Routing:** standard | **Wake type:** rescore
- **Condition:** Only emitted if `abs(score_delta) >= 0.05` (materiality gate). Subject to anti-loop guardrails.
- **Wake target:** Linked Opportunity (rescore, but see anti-loop one-direction rule — if this event was caused by an `opportunity_score_changed`, the opportunity rescore is suppressed within this causal chain).
- **Cooldown:** 4 hours per parcel.

#### parcel_vacancy_confirmed → fit + opportunity
- **Priority:** 5 | **Routing:** standard | **Wake type:** fit, rescore
- **Condition:** vacancy_status = `vacant` AND confidence >= 0.7.
- **Wake target:** Packaging agent (check HomeProduct fit), linked Opportunity (rescore with confirmed vacancy).
- **Cooldown:** 24 hours per parcel.

#### parcel_split_candidate_identified → opportunity creation + fit
- **Priority:** 5 | **Routing:** standard | **Wake type:** create, fit
- **Condition:** confidence >= 0.6 (Phase 1 default).
- **Wake target:** Opportunity (create type `land_division_candidate`), compound trigger evaluation for `split_ready_parcel`.
- **Cooldown:** 24 hours per parcel.

---

### Family 12: Human / operator events → trigger rules

All human operator events are routed as `immediate`. Human actions are always the highest-priority input.

#### human_marked_interesting → rescore + rescan
- **Priority:** 3 | **Routing:** immediate | **Wake type:** rescore, rescan
- **Condition:** Always.
- **Wake target:** The marked entity (rescore with human-interest signal boost), Municipality (rescan if entity is geographic).
- **Cooldown:** None — human actions always override cooldown.

#### human_requested_rescan → full rescan
- **Priority:** 2 | **Routing:** immediate | **Wake type:** rescan
- **Condition:** Always.
- **Wake target:** The specified entity (full rescan bypassing cooldown).
- **Cooldown:** None — explicit human override.

#### human_verified_opportunity → opportunity update
- **Priority:** 3 | **Routing:** immediate | **Wake type:** rescore
- **Condition:** Always.
- **Wake target:** Opportunity (status advancement + confidence boost + human-verified flag).
- **Cooldown:** None.

#### human_suppressed_event → suppress
- **Priority:** 4 | **Routing:** immediate | **Wake type:** suppress
- **Condition:** Always.
- **Wake target:** The specified event (status → `suppressed`). Any pending downstream triggers from this event are canceled.
- **Cooldown:** None.

---

### Family 13: System / operational events → trigger rules

#### agent_run_completed → log only
- **Priority:** 9 | **Routing:** background | **Wake type:** — (no downstream wake)
- **Condition:** Always.
- **Notes:** Recorded for audit, debugging, and observability. No downstream trigger.

#### agent_run_failed → notify + retry evaluation
- **Priority:** 5 | **Routing:** immediate | **Wake type:** notify
- **Condition:** Always.
- **Wake target:** Operator notification (with failure details), retry evaluation (if the triggering event is retry-eligible, re-queue with backoff).
- **Cooldown:** None — failures always surface.

#### recursion_limit_reached → alert
- **Priority:** 2 | **Routing:** immediate | **Wake type:** notify
- **Condition:** Always.
- **Wake target:** Operator alert (system guardrail activated — investigate the causal chain). Log the full chain for debugging.
- **Cooldown:** None.
- **Notes:** This event is terminal — it does NOT trigger any further derived events.

#### cooldown_triggered → log only
- **Priority:** 10 | **Routing:** background | **Wake type:** — (no downstream wake)
- **Condition:** Always.
- **Notes:** Recorded for observability. High-frequency in steady state — background only.

#### event_processing_error → notify + retry
- **Priority:** 4 | **Routing:** immediate | **Wake type:** notify
- **Condition:** Always.
- **Wake target:** Operator notification, retry queue (if retry_eligible = true, re-queue with exponential backoff, max 3 retries).
- **Cooldown:** None.

---

## Compound trigger evaluation rules

Three compound events are defined. Each requires multiple independent conditions to be true simultaneously. The trigger engine evaluates compound conditions using these rules.

### General evaluation policy

- **Evaluation strategy:** Eager by default. When any component event arrives, the trigger engine immediately checks whether all other components are currently satisfied.
- **Component lookup:** Query the most recent matching events for each other component, scoped by shared entity_refs, within the time window.
- **Time window:** Configurable per compound event. Clock starts from the *oldest* component event in the conjunction. If the window expires before all components are satisfied, the evaluation is abandoned — no compound event fires.
- **Re-fire policy:** A compound event can re-fire if a *new* component event arrives after the previous compound event was fully processed, and all conditions are met again with the new component. The dedupe_key prevents exact duplicates.
- **Revocation:** No explicit revocation. If conditions were met and the compound event fired, it was correct at that point in time. If conditions change later (e.g., the cluster dissolves, the developer resolves distress), that is a new event — not a retraction of the old compound event.
- **Future batching note:** Some heavy municipality-scale compounds may later need batch evaluation rather than eager evaluation, especially if they involve checking hundreds of parcels. The architecture supports both. For Phase 1, all three defined compounds use eager evaluation because their component events are entity-scoped (specific listing + cluster, specific developer + listing, specific parcel + municipality), not jurisdiction-wide scans.

### listing_expired_in_cluster

- **Priority:** 6
- **Components:** `listing_expired` + the listing's parcel belongs to an active OwnerCluster with 3+ members.
- **Entity overlap required:** The listing's `parcel_id` must be in the cluster's `parcel_ids`.
- **Time window:** Cluster must be active (detected or updated within last 365 days).
- **Evaluation trigger:** When `listing_expired` arrives, check if the listing's parcel belongs to a qualifying cluster.
- **Wake target:** OwnerCluster (fatigue_score rescore), DeveloperEntity (rescore if linked), Opportunity (create or rescore).
- **Routing class:** standard.

### distressed_developer_with_activity

- **Priority:** 7
- **Components:** `developer_entity_distress_detected` + at least one `listing_added` or `listing_price_reduced` for a parcel owned by the same developer within the last 90 days.
- **Entity overlap required:** Shared `developer_entity_id` (via parcel ownership).
- **Time window:** 90 days. Listing activity must have occurred within 90 days of distress detection.
- **Evaluation trigger:** When either component arrives, check if the other component exists within the window.
- **Wake target:** DeveloperEntity (exit_window_flag evaluation), Opportunity (create type `developer_exit`).
- **Routing class:** standard.

### split_ready_parcel

- **Priority:** 10
- **Components:** Parcel has adequate frontage (>= 2x municipality minimum) + adequate acreage (>= 2x minimum lot size) + municipality `land_division_posture` is `permissive` or `moderate`.
- **Entity overlap required:** Same `parcel_id` and `municipality_id`.
- **Time window:** Municipality posture must be current (assessed within last 365 days).
- **Evaluation trigger:** When `parcel_split_candidate_identified` arrives, check municipality posture. When `municipality_rule_now_supports_split` arrives, check qualifying parcels.
- **Wake target:** Opportunity (create type `land_division_candidate`), Packaging agent (fit analysis for resultant lots).
- **Routing class:** standard.
- **Future batch note:** When `municipality_rule_now_supports_split` triggers this compound, it may need to evaluate hundreds of parcels. Phase 1 handles this by applying blast-radius controls (see below) to limit fan-out. Future phases may batch the evaluation.

---

## Anti-loop guardrails

The most critical guardrails in the system prevent score-change cascades between Parcels and Opportunities. Three interlocking layers ensure the event mesh cannot run away.

### Layer 1: Materiality gate (agent-side)

Score-change events are only emitted when the delta exceeds a materiality threshold. If a rescore computes a new value but the delta is below the threshold, the object is updated silently — no event is emitted, no downstream wake occurs.

**Phase 1 recommended materiality thresholds:**

| Score type | Threshold | Threshold type | Rationale |
|---|---|---|---|
| Parcel opportunity_score | >= 0.05 | Absolute (on 0.0–1.0 scale) | Prevents noise from minor signal fluctuations |
| Opportunity opportunity_score | >= 0.05 | Absolute | Same rationale |
| OwnerCluster fatigue_score | >= 0.10 | Absolute | Fatigue is a coarser signal, wider band |
| DeveloperEntity fatigue_score | >= 0.10 | Absolute | Same rationale |
| Subdivision stall_score | >= 0.10 | Absolute | Stall scores shift slowly |
| SiteCondoProject stall_score | >= 0.10 | Absolute | Same rationale |

### Layer 2: One-direction causality (engine-side)

Within a single `causal_chain_id`, score signals can only flow in one direction per chain. The trigger engine enforces this by inspecting the causal lineage of incoming events:

**Rule A:** If an agent run was triggered by an `opportunity_score_changed` event, and the agent computes a `parcel_score_updated` event, that parcel event's wake targets are restricted to non-scoring consumers only (UI refresh, reporting, staleness tracking). It does NOT re-enter the opportunity scorer within the same causal chain.

**Rule B:** If an agent run was triggered by a `parcel_score_updated` event, and the agent computes an `opportunity_score_changed` event, that opportunity event does NOT re-enter the parcel scorer within the same causal chain.

**Implementation:** The trigger engine checks `derived_from_event_ids` lineage. If the chain contains both `parcel_score_updated` and `opportunity_score_changed`, any further score-change event in that chain is routed to `background` with wake targets limited to logging and UI.

### Layer 3: Object-level cooldown (engine-side)

Even if materiality and causality guardrails somehow fail, object-level cooldowns prevent re-processing:

**Phase 1 recommended cooldown defaults:**

| Object Type | Default Cooldown | Override Condition |
|---|---|---|
| Parcel (for rescoring) | 4 hours | Any raw event with entity_refs matching this parcel |
| Opportunity (for rescoring) | 4 hours | Any raw event for a linked parcel |
| Municipality | 24 hours | `municipality_rule_change_detected`, `municipality_infrastructure_extension_detected` |
| OwnerCluster | 12 hours | `listing_added` or `listing_expired` for a parcel in the cluster |
| Subdivision | 24 hours | Any municipal process event linking to this subdivision |
| SiteCondoProject | 24 hours | Same as Subdivision |
| DeveloperEntity | 24 hours | `listing_added` / `listing_expired` for parcels owned by the entity |

**Critical override rule:** A raw event (`event_class = raw`) **always** overrides cooldown for any object it references in `entity_refs`. Raw events represent new external reality. The system should never ignore fresh real-world data because of an internal cooldown.

Derived events do NOT override cooldown unless their `wake_priority <= 3` (high priority).

### Chain-depth hard cap

When the trigger engine is about to emit a derived event with `generation_depth > 5`:
1. Do NOT emit the intended event.
2. Emit `recursion_limit_reached` with the intended event_type, causal_chain_id, and depth.
3. Log the full causal chain for debugging.
4. `recursion_limit_reached` is terminal — it does NOT trigger any further derived events.
5. The hard cap of 5 is a Phase 1 default. It can be adjusted per deployment but should not be changed without understanding cascade implications.

---

## Blast-radius controls

Municipality-scope events can affect hundreds or thousands of parcels. Without fan-out controls, a single `municipality_rule_now_supports_split` event could trigger 5,000 parcel rescores simultaneously. These rules limit the blast radius.

### Municipality event fan-out rules

**Phase 1 recommended defaults:**

| Municipality Event | Parcel Filter | Max Fan-Out | Routing Class |
|---|---|---|---|
| `municipality_rule_now_supports_split` | `acreage >= 2.0 AND vacancy_status IN (vacant, partially_improved)` | 500 parcels per batch | batch |
| `municipality_infrastructure_extension_detected` | Parcels within extension area (if GIS available) OR `vacancy_status = vacant` in municipality | 200 parcels per batch | batch |
| `municipality_split_capacity_increased` | Same filter as `municipality_rule_now_supports_split` | 500 parcels per batch | batch |
| `municipality_frontage_rules_favorable_detected` | `acreage >= 5.0` | 200 parcels per batch | batch |
| `municipality_permit_activity_increased` | None — updates Municipality object only, no individual parcel rescoring | 0 (municipality-level only) | batch |
| `municipality_subdivision_stagnation_pattern_detected` | All Subdivisions in municipality | 50 subdivisions per batch | batch |

### Fan-out execution rules

1. When a municipality event's qualifying parcels exceed the max fan-out, parcels are processed in batches ordered by existing `opportunity_score` (highest first). This ensures the most promising parcels are rescored first.
2. Each batch is processed as a separate `batch` routing class job. Batches are spaced at minimum 5-minute intervals to prevent resource contention.
3. If the parcel filter returns zero qualifying parcels, the event is logged with a note ("no qualifying parcels found") and no downstream processing occurs.
4. Fan-out caps are Phase 1 defaults. They should be tuned based on actual database size and processing capacity.

### Subdivision/project-scope fan-out

Events that target all parcels within a Subdivision or SiteCondoProject (e.g., stallout detections) are not subject to municipality-level fan-out caps because subdivisions are typically smaller (10–200 lots). However:
- If a Subdivision has more than 500 parcels, apply the same batching logic as municipality events.
- This threshold is unlikely to be hit in Phase 1 Michigan data but exists as a safety valve.

---

## Packaging regeneration rules

Packaging (SiteFit, PricePackage) is expensive to compute and should not regenerate for every minor data change. These rules define when packaging work is triggered.

### Triggers that cause full packaging regeneration

Full regeneration means: re-run SiteFit, recompute SiteWorkEstimate, recalculate PricePackage from scratch.

| Trigger Event | Condition | Routing Class |
|---|---|---|
| `home_model_fit_detected` | Always (new fit result) | standard |
| `listing_price_reduced` | `percent_change > 10%` AND Opportunity exists at `fit_checked` or `packaged` | standard |
| `municipality_rule_now_supports_split` | Opportunity exists in affected municipality | batch (24-hour cooldown) |
| `parcel_vacancy_confirmed` | vacancy_status changed AND SiteFit exists | standard |
| `listing_restriction_language_detected` | SiteFit exists for this parcel | standard |
| `municipality_frontage_rules_favorable_detected` | SiteFit exists with setback concerns | batch |

### Triggers that cause incremental packaging update

Incremental update means: update the PricePackage price fields without re-running SiteFit or SiteWorkEstimate.

| Trigger Event | Condition | What Updates |
|---|---|---|
| `listing_price_reduced` (≤ 10%) | PricePackage exists | land_cost field only |
| `incentive_award_confirmed` | PricePackage exists | incentive_offset field |
| `site_work_estimate_completed` | PricePackage exists | site_work fields |

### Triggers that do NOT cause packaging action

| Trigger Event | Why Not |
|---|---|
| `parcel_score_updated` | Score changes alone don't affect physical fit or pricing |
| `opportunity_score_changed` | Same — score is a ranking signal, not a packaging input |
| `listing_cdom_threshold_crossed` | CDOM affects opportunity scoring, not packaging |
| `owner_cluster_detected` | Cluster detection is a supply signal, not a packaging input |
| `listing_fatigue_language_detected` | Fatigue is a developer signal, not a packaging input |

### Minimum packaging regeneration interval

Full packaging regeneration for the same Opportunity: **24 hours** minimum between runs.
If multiple packaging triggers arrive within the window, they are coalesced — the regeneration runs once using the latest data.

---

## Stallout-scan frequency rules

Stallout scans (checking subdivisions and site-condo projects for stall conditions) are expensive because they cross-reference historical municipal records, parcel vacancy, infrastructure state, and development timelines.

### Default scan intervals

| Scan Type | Default Interval | Routing Class |
|---|---|---|
| Individual subdivision stallout rescan | 30 days | batch |
| Individual site-condo project rescan | 30 days | batch |
| Full municipality stallout sweep | 90 days | background |
| Full system-wide stallout sweep | 180 days | background |

### Override signals (immediate rescan)

These events override the default interval and trigger an immediate stallout rescan of the affected subdivision or project, regardless of when the last scan occurred:

- `bond_released_detected` — a bond release is a significant state change
- `permit_pulled_detected` — new permits in a stalled area may signal reactivation
- `roads_accepted_detected` — road acceptance may signal project completion progress
- `listing_added` for a parcel in the subdivision — new market activity in a stalled area
- `human_requested_rescan` — explicit operator override
- `municipality_rule_change_detected` — policy change may affect stall assessment

### Scan suppression

If a stallout scan finds no change (same vacancy ratio, same stall_score within materiality threshold), the next scan interval is doubled (up to a max of 180 days). This prevents repeated scanning of truly dormant projects that show no movement.

If a scan finds a material change (stall_score delta >= 0.10), the interval resets to the default (30 days).

---

## Implementation notes

1. **Event ordering:** The trigger engine should process events in the order they are observed (`observed_at`), not the order they occurred (`occurred_at`). For historical scans, many events with old `occurred_at` dates will arrive with recent `observed_at` timestamps. Processing by `observed_at` ensures the system handles them in the order it learned about them.

2. **At-least-once delivery:** The trigger engine should guarantee at-least-once event delivery. Combined with `dedupe_key` and `fingerprint_hash`, this ensures no event is lost and no event is processed redundantly. Exactly-once semantics are not required for Phase 1 — idempotent wake actions make at-least-once sufficient.

3. **Dead-letter handling:** If an event fails processing after 3 retries (with exponential backoff), it should be moved to a dead-letter queue. The `event_processing_error` event is emitted. Dead-letter events are not automatically retried — they require operator review.

4. **Observability:** The trigger engine should emit metrics for: events processed per minute (by family and routing class), average processing latency (by routing class), cooldown hit rate (percentage of events suppressed by cooldown), materiality gate hit rate (percentage of score changes below threshold), compound event evaluation count and success rate, dead-letter queue depth.

5. **Trigger rule versioning:** Trigger rules should be versioned alongside the event library. When a trigger rule changes (new condition, new wake target, new cooldown), the version should increment. This enables A/B testing of routing strategies and rollback if a rule change causes problems.

6. **Configuration vs. code:** Thresholds, cooldowns, fan-out caps, and materiality gates should be configuration values, not hardcoded constants. This allows tuning without code deployment. The recommended defaults in this document are the initial configuration values.

7. **Relationship to the event library:** This file references events by their canonical names defined in `LANDOS_EVENT_LIBRARY.md`. Any event added to or removed from the event library must have a corresponding trigger rule added to or removed from this file. The two files must stay in sync.

8. **Relationship to the agent teams:** This file defines what agents are woken and under what conditions. `LANDOS_AGENT_TEAMS.md` defines what each agent does when woken — its inputs, outputs, capabilities, and constraints. The trigger matrix is the routing layer; the agent teams doc is the execution layer.

9. **Phase gating:** Trigger rules marked [Phase 2] or [Phase 3+] should not be active until those phases are enabled. The trigger engine should support phase-based rule activation so that rules can be defined in advance but only fire when their phase is live. This is a deployment-level configuration, not a code change.

10. **Event library sync note:** The following changes have been applied to `LANDOS_EVENT_LIBRARY.md` and are now in sync:
    - `municipality_rule_change_detected` added as raw; `municipality_rule_now_supports_split` changed to derived.
    - `bond_released_detected` added (raw, Phase 1, municipal process family).
    - `unfinished_site_condo_detected` moved to `event_family: historical_stall`.
