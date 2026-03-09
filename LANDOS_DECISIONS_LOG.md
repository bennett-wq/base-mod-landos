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

## 2026-03-08 | Claude Code and Codex are execution tools, not the "brain"
**Decision:** Tool choice should be separated from the actual system intelligence.
**Why:** The real brain is the object model + event architecture + trigger rules; tools are work surfaces and runtimes.
**Affects:** Technical workflow, team communications, implementation strategy.
**Reversible?:** Yes.

## 2026-03-08 | Michigan launch wedge is strategic
**Decision:** Michigan should be treated as the highest-priority proving ground.
**Why:** It combines stranded lots, stalled site condos/subdivisions, relevant legal changes, and a strong mismatch between supply and attainable product.
**Affects:** Early geography focus, municipal tracking, product examples, GTM wedge.
**Reversible?:** Yes.
