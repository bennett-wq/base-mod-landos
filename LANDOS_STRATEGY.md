# LANDOS_STRATEGY.md — BaseMod LandOS Strategic Context

> Canonical strategic context for LandOS. Do not duplicate content in CLAUDE.md or LANDOS_BUILD_ROADMAP.md.
> Update this file when strategy decisions change.

---

## What LandOS is

LandOS is an autonomous real estate operating system built on Claude Code multi-agent orchestration. In the 2026 context, AI agents run persistently, trigger on signals, hand off to each other, and act without human prompting. LandOS uses this to solve a specific problem — land in southeast Michigan that could become affordable housing sits invisible and fragmented. No one is connecting the dots.

LandOS does the connecting. It ingests MLS listings, parcel data (Regrid), permit history (municipal), and broker signals (Spark BBO) and turns them into structured events. Those events fire trigger rules. Trigger rules wake agents. Agents detect clusters of same-owner parcels, stalled developer inventories, site-condo opportunities, and underbuilt lots — and package them into attainable housing pathways.

---

## Agent architecture

| Role | Model | Responsibility |
|------|-------|----------------|
| PM Agent | Opus | Plans, specs, gates |
| Builder Agent | Sonnet | Implements, tests |
| Validator Agent | Haiku | Read-only, runs tests |
| Specialist agents | varies | Parcel, cluster, municipal, spark-signal, fit |

---

## Step 4.5 — Spark BBO Signal Intelligence (UNBLOCKED — NEXT AFTER INFRASTRUCTURE)

**BBO = Broker Back Office.** These are MLS fields only accessible with a private-role API key.
**BBO credentials confirmed. Step 4.5 builds before Step 6.**

BBO fields now available:
- `CumulativeDaysOnMarket` (CDOM)
- `PrivateRemarks`
- `ListAgentKey`
- `OffMarketDate`

Step 4.5 feeds Step 6 directly. Agent/Office Clustering (signal family 4) enriches cluster
detection with behavioral signals that parcel data alone cannot provide.

### The 6 signal families Step 4.5 will detect when unblocked

1. **Developer Exit signals** — patterns indicating a developer is winding down or exiting a position
2. **Listing Behavior signals** — CDOM accumulation, relist patterns, price cut cadence
3. **Language Intelligence** — PrivateRemarks parsing for package language, fatigue, restrictions, approvals, utilities
4. **Agent/Office Clustering** — same agent or office accumulating land listings across a geography
5. **Subdivision Remnant Inventory** — scattered lots from partially-built subdivisions still on market
6. **Market Velocity / Absorption Rate** — how fast land is moving in a given submarket

---

## Permanently out of scope (Phase 2+ only)

These objects and capabilities are not blocked — they are sequenced. They do not exist in Phase 1:

- `BuyerProfile`
- `IncentiveProgram`
- `TransactionPath`
- `SiteWorkEstimate`
- `PricePackage`
- Marketplace features
- Buyer-facing UI
- Transaction orchestration

---

## Current implementation state

- Steps 1–5 complete. **165/165 tests passing.**
- Step 4.5 (Spark BBO) is next — BBO credentials confirmed March 2026.
- Step 6 (Cluster Detection) follows Step 4.5 and will run on enriched BBO + parcel signal set.
- Run tests: `cd landos && python3 -m pytest tests/ -v`
