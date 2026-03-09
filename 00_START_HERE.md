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

### Continuity and trust order (read these first, every session)
1. `00_START_HERE.md`
2. `LANDOS_HANDOFF_MASTER.md`
3. `LANDOS_DECISIONS_LOG.md`
4. `SESSION_HANDOFF_CURRENT.md` — the live session baton
5. `NEXT_STEPS.md` — current operational priorities

### Topic-specific docs (read as needed for the current task)
6. `LANDOS_OBJECT_MODEL.md`
7. `LANDOS_EVENT_LIBRARY.md`
8. `LANDOS_TRIGGER_MATRIX.md`
9. `LANDOS_AGENT_TEAMS.md`
10. `LANDOS_DATA_SOURCES.md`
11. `LANDOS_BUILD_ROADMAP.md`

### Tool configuration
12. `CLAUDE.md`
13. `CODEX_TASKING.md`

### Session continuity
- `SESSION_HANDOFF_CURRENT.md` — the live baton (updated every session)
- `SESSION_LOG.md` — the historical archive (append-only)
- `SESSION_RITUAL.md` — the operating manual for session handoff

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
- Do not create overlapping "master" docs unless explicitly replacing one with another.
- Do not rely on chat history as the source of truth.
- Do not change core architecture without updating:
  - `LANDOS_HANDOFF_MASTER.md`
  - `LANDOS_DECISIONS_LOG.md`
  - the relevant specialized file
- All major decisions must be logged with rationale.

## Immediate recommended next step
Read `LANDOS_HANDOFF_MASTER.md`, `LANDOS_DECISIONS_LOG.md`, and `SESSION_HANDOFF_CURRENT.md` first. Then:
- Apply the event-library sync pass so `LANDOS_EVENT_LIBRARY.md` fully matches the finalized decisions reflected in `LANDOS_TRIGGER_MATRIX.md`.
- See `NEXT_STEPS.md` for the full current priority list.

## One-sentence definition
**BaseMod LandOS is the operating system that turns fragmented land supply into attainable homeownership inventory by mapping signals, waking the right agents, packaging homes that fit, and routing the market toward transaction.**
