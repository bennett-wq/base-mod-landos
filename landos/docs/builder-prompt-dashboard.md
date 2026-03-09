# Builder Prompt — LandOS NEXUS Command Center
# Updated: 2026-03-09
# Paste this into a fresh Claude Code chat opened at the repo root.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are continuing work on the LandOS NEXUS Command Center — a React-based
agent visualization and signal intelligence dashboard for BaseMod LandOS.

════════════════════════════════════════════════════════════════════════
WHAT EXISTS — READ BEFORE DOING ANYTHING
════════════════════════════════════════════════════════════════════════

Project root: /Users/bennett2026/Desktop/Kingdom LandOS/BaseMod LandOS/
Python workspace: landos/
Dashboard source: landos/dashboard/nexus/

**NEVER use `cd landos &&` — it corrupts the shell cwd and breaks hooks.**

Node.js 22 required (via nvm):
  export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && nvm use 22

Dev server:
  cd landos/dashboard/nexus && npm run dev

Build + Deploy:
  cd landos/dashboard/nexus && npm run build
  netlify deploy --prod --dir=dist --site=89f73bdf-1508-435c-a9ae-ea638b1ccab2

Live URL: https://agents.basemodhomes.com
Netlify admin: https://app.netlify.com/projects/landos-nexus
DNS: CNAME agents.basemodhomes.com → landos-nexus.netlify.app

────────────────────────────────────────────────────────────────────────
CURRENT STACK
────────────────────────────────────────────────────────────────────────

- Vite 7 + React 19 + Redux Toolkit + Tailwind CSS 4
- Framer Motion (animations)
- react-leaflet + Leaflet (maps)
- IBM Plex Mono + Outfit (typography)
- Brass/void dark theme (#050508 bg, #c9a44e brass accent)

────────────────────────────────────────────────────────────────────────
PROJECT STRUCTURE
────────────────────────────────────────────────────────────────────────

landos/dashboard/nexus/src/
├── store/
│   ├── index.js          — Redux store config
│   ├── meshSlice.js      — Agents, rules, signals, clusters, toasts
│   └── uiSlice.js        — Active tab, panels, overlays
├── data/
│   ├── agents.js         — 7 agents, 22 rules, 10 signal types, event families
│   ├── clusters.js       — 60 generated clusters with realistic Washtenaw data
│   └── commands.js       — Command palette actions (pipeline, agents, Claude skills)
├── hooks/
│   └── useMeshCanvas.js  — Canvas-based particle system for event mesh visualization
├── components/
│   ├── shared/
│   │   ├── Navbar.jsx        — Top nav with tabs, metrics, status, cmd+K trigger
│   │   ├── CommandPalette.jsx — ⌘K overlay with Pipeline/Agent/Claude skill commands
│   │   ├── AgentDetail.jsx   — Slide-over panel with stats, rules, chat interface
│   │   └── ToastContainer.jsx — Notification toasts
│   ├── mesh/
│   │   ├── MeshTab.jsx       — 3-column layout: agents | canvas | signals
│   │   ├── SignalFeed.jsx     — Live signal stream with tier-coded borders
│   │   ├── RuleGrid.jsx      — 22 trigger rules with fire counts + cooldown bars
│   │   ├── ClusterMini.jsx   — Compact cluster list with type badges
│   │   └── MetricsStrip.jsx  — Bottom metrics bar + pipeline pulse
│   ├── radar/
│   │   └── RadarTab.jsx      — Leaflet map + filterable sortable table (intel-style)
│   ├── clusters/
│   │   └── ClustersTab.jsx   — Satellite map + score rings + dimension bars
│   ├── command/
│   │   └── CommandTab.jsx    — 4 agent runners with logs, stats, Run/Logs/Config
│   └── economics/
│       └── EconomicsTab.jsx  — Cost waterfall, sensitivity grid, comps, dormant supply

────────────────────────────────────────────────────────────────────────
5 TABS
────────────────────────────────────────────────────────────────────────

1. ⚡ MESH — Central event mesh canvas with particle flows between 7 agent
   nodes orbiting the Trigger Engine hub. Left: agent roster with status.
   Right: signals/rules/clusters tabs. Bottom: metrics + pipeline pulse.

2. 🎯 RADAR — Leaflet dark map with circle markers colored by signal level
   (HIGHEST/HIGH/MEDIUM/LOW/NONE). Sidebar: stats bar, filter dropdowns
   (signal/tier/concentration/owner search), sortable table. Click row to
   fly-to on map. Inspired by intel.basemodhomes.com radar view.

3. 🏢 CLUSTERS — Satellite imagery map with markers colored by cluster type
   (owner/subdivision/proximity/agent/office). Right panel: top 8 clusters
   with SVG score rings, dimension bars (zoning/economics/infra/signal),
   stat grids. Inspired by intel.basemodhomes.com signal detail panels.

4. 🤖 COMMAND — 2x2 grid of agent runners: Supply Intelligence, Cluster
   Detection, BBO Signal Discovery, Municipal Intelligence. Each has
   status indicator, stats row, scrollable log output, action buttons.
   Inspired by intel.basemodhomes.com command tab agent cards.

5. 📊 ECONOMICS — Left: cost waterfall (7 line items), sensitivity grid
   (5 price points with profit/margin/tier/portfolio). Right: market comps,
   Tier 1 portfolio value, dormant supply economics with top holders.

────────────────────────────────────────────────────────────────────────
DESIGN SYSTEM
────────────────────────────────────────────────────────────────────────

Colors (Tailwind @theme):
  void-0..void-5: #050508 → #22223a (backgrounds)
  brass/brass-bright/brass-dim: #c9a44e / #e8c96a / #6b5a2a (accent)
  nexus-cyan: #00f0ff (listings)
  nexus-emerald: #00ff88 (opportunities, success)
  nexus-crimson: #ff2d55 (Tier 1, dev exit, errors)
  nexus-amber: #ffb800 (municipal, warnings, cooldowns)
  nexus-purple: #a855f7 (clusters)
  nexus-blue: #3b82f6 (parcels)
  nexus-orange: #f97316 (historical, municipal router)

Typography:
  --font-mono: IBM Plex Mono (data, metrics, code)
  --font-display: Outfit (headings, large numbers)

Animations:
  breathe: 2s ease-in-out infinite (status dots)
  Framer Motion: slide-over panels, signal feed items, command palette, toasts
  Canvas: particle system with cubic-eased trails between agent nodes

────────────────────────────────────────────────────────────────────────
BACKEND DATA CONTEXT
────────────────────────────────────────────────────────────────────────

The dashboard currently uses simulated data matching real LandOS numbers.
The Python backend pipeline produces:
  - 95 active Spark MLS land listings (Washtenaw County)
  - 10,266 vacant parcels from Regrid CSV
  - 2,229 parcel clusters (1,112 owner, 81 subdivision, 1,036 proximity)
  - 47 clusters with active listings
  - 23 Tier 1 high-convergence opportunities
  - 76 dormant supply clusters (22,057 acres)
  - 31 active trigger rules across 7 agent wake targets

Future work: Wire the React frontend to a FastAPI backend that imports
and runs the existing pipeline code from landos/src/ and landos/scripts/.

────────────────────────────────────────────────────────────────────────
NEXT SESSION PRIORITIES
────────────────────────────────────────────────────────────────────────

1. Wire live data: Build FastAPI backend (landos/dashboard/api.py) that
   imports pipeline code and serves real data to the React frontend.

2. WebSocket signal feed: Replace simulated signals with real events
   from the TriggerEngine as the pipeline runs.

3. Agent chat enhancement: Connect chat to actual Claude Code subagents
   using /loop and hooks for real-time agent interaction.

4. Cluster detail drill-down: Click cluster → modal with all parcels,
   matched listings, BBO signals, remarks text, CDOM timeline.

5. Code-split: Lazy-load tab components to reduce initial bundle (currently
   554KB). Use React.lazy() + Suspense.

6. Step 7 (Municipal scan): When implemented, light up the Municipal
   Intelligence runner and add municipal event types to the signal feed.

────────────────────────────────────────────────────────────────────────
IMPORTANT CONSTRAINTS
────────────────────────────────────────────────────────────────────────

- Do NOT modify any existing landos/src/ or landos/tests/ code
- The existing 237 tests must still pass after any changes
- All dashboard code stays in landos/dashboard/
- Node 22 required for Vite 7 + Tailwind 4 (nvm use 22)
- Deploy via Netlify CLI to site ID 89f73bdf-1508-435c-a9ae-ea638b1ccab2
