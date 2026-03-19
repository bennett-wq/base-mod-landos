# BaseMod NEXUS — Claude Code Implementation Prompts
## Comprehensive Redesign of agents.basemodhomes.com
### March 19, 2026

---

## HOW TO USE THIS DOCUMENT

Feed each prompt to Claude Code **in order**. Each prompt is self-contained with:
- **What to build** (scope)
- **Exact files to create/modify**
- **Design tokens and patterns** (so Claude Code doesn't need to see the HTML)
- **Acceptance criteria** (binary pass/fail)
- **What NOT to do** (scope guard)

Wait for each prompt to complete before moving to the next. Prompts are designed to be ~2,000-4,000 tokens each — the sweet spot for Claude Code output quality.

---

## PROMPT 0: Project Scaffold & Design System Foundation

```
You are building "BaseMod NEXUS" — a React + Vite + Tailwind CSS application that replaces the current agents.basemodhomes.com. This is an institutional-grade land intelligence platform.

### Task: Create the project scaffold and design system foundation.

### Create these files:

1. `package.json` with dependencies:
   - react, react-dom, react-router-dom
   - @tanstack/react-query
   - tailwindcss, postcss, autoprefixer
   - lucide-react (icons — DO NOT use Material Symbols in React, use Lucide equivalents)
   - leaflet, react-leaflet (maps)
   - framer-motion (animations)
   - clsx, tailwind-merge
   - vite, @vitejs/plugin-react

2. `tailwind.config.js` with this EXACT color system (Material Design 3 tonal palette):
   ```js
   colors: {
     "primary": "#7f5313",
     "primary-container": "#9b6b2a",
     "on-primary": "#ffffff",
     "on-primary-container": "#fffbff",
     "primary-fixed": "#ffddb8",
     "primary-fixed-dim": "#f7bb73",
     "surface": "#fbf9f6",
     "surface-container-lowest": "#ffffff",
     "surface-container-low": "#f5f3f0",
     "surface-container": "#efeeeb",
     "surface-container-high": "#eae8e5",
     "surface-container-highest": "#e4e2df",
     "on-surface": "#1b1c1a",
     "on-surface-variant": "#504539",
     "outline": "#827567",
     "outline-variant": "#d4c4b4",
     "secondary": "#555f6d",
     "tertiary": "#006948",
     "tertiary-container": "#00855d",
     "error": "#ba1a1a",
     "error-container": "#ffdad6",
     "inverse-surface": "#30312f",
   }
   ```
   Font family: `"Inter", sans-serif` for all (headline, body, label).
   Border radius: `DEFAULT: 0.25rem, lg: 0.5rem, xl: 0.75rem, full: 9999px`

3. `src/styles/globals.css` with:
   - Tailwind directives
   - `.copper-gradient { background: linear-gradient(155deg, #7f5313 0%, #9b6b2a 100%); }`
   - `.agent-pulse` animation (pulsing ring effect)
   - `.scanline` animation (subtle scan effect)
   - Custom scrollbar styles (thin, copper-tinted)
   - Ghost border utility: `outline: 1px solid rgba(212, 196, 180, 0.2)`

4. `src/lib/cn.ts` — utility combining clsx + tailwind-merge

5. `src/App.tsx` with React Router setup. Routes:
   - `/mesh` — Mesh (Event Nerve Center)
   - `/radar` — Radar (Map Intelligence)
   - `/clusters` — Clusters (Intelligence Dossier)
   - `/economics` — Economics (Deal Analysis)
   - `/command` — Command (Swarm Control)
   - `/pipeline` — Pipeline (Deal Tracker)
   - `/missions` — Missions Control
   - `/config` — Config/Settings
   Default redirect: `/mesh`

### Design System Rules (CRITICAL — enforce everywhere):
- NO explicit borders for sectioning. Use background color shifts between surface levels.
- Ambient shadows only: `box-shadow: 0 12px 32px rgba(27, 28, 26, 0.04)`
- No dark mode. Light warm palette only.
- Labels: always uppercase, letter-spacing 0.05-0.2em, font-bold, text-[10px] or text-[11px]
- Cards: white bg (#fff), 1rem radius, 1.75-2.25rem padding
- Primary CTA buttons: copper-gradient, white text, rounded-lg
- Active nav: 3px left copper border + copper text + bg-primary/5

### Acceptance Criteria:
- [ ] `npm run dev` starts without errors
- [ ] Tailwind config produces correct copper colors
- [ ] All routes render placeholder pages
- [ ] Inter font loads from Google Fonts
- [ ] No Material Symbols — Lucide React icons only

### Do NOT:
- Install any UI component library (no shadcn, no MUI, no Ant)
- Create any page content yet — just scaffolding
- Add dark mode support
```

---

## PROMPT 1: Shared Layout Shell (SideNav + TopNav + Footer)

```
Build the shared layout shell that wraps all pages. This is the persistent navigation chrome.

### Create these files:

1. `src/components/layout/SideNav.tsx`
   - Fixed left, 240px wide, full height
   - White background (surface-container-lowest)
   - Right border: use surface-container-low background shift, NOT a border line
   - Logo area: "BaseMod" in text-xl font-bold + "NEXUS" in text-[10px] tracking-[0.2em] text-primary uppercase
   - Nav items with Lucide icons:
     - Mesh (Zap icon)
     - Radar (Crosshair icon)
     - Clusters (Building2 icon)
     - Economics (Wallet icon)
     - Command (Bot icon)
     - Pipeline (BarChart3 icon)
     - Missions (Rocket icon)
   - Active state: border-l-[3px] border-primary text-primary bg-primary/5 font-semibold
   - Inactive: text-stone-500 hover:bg-stone-100
   - Bottom: Config (Settings icon) separated by border-t border-stone-100
   - Use react-router-dom NavLink for active state detection

2. `src/components/layout/TopNav.tsx`
   - Sticky top, z-30, h-[56px]
   - ml-[240px] w-[calc(100%-240px)]
   - bg-white/80 backdrop-blur-md
   - Left: breadcrumb text (e.g. "Radar / Washtenaw County") in text-primary font-bold text-sm
   - Center: Search input — pill-shaped, bg-surface-container-low, border border-outline-variant/10, Search icon, placeholder "Search event mesh..."
   - Right: Notification bell icon button + User avatar (circle with initials "JD", copper bg, white text)

3. `src/components/layout/MetricsStrip.tsx`
   - Fixed bottom footer bar, h-[64px], white bg
   - Border-t border-outline-variant/10
   - ml-[240px]
   - Flex row of metric columns:
     - Active Listings: 95
     - Vacant Parcels: 10,266
     - Clusters: 2,229
     - Tier 1 Opps: 23 (in primary color)
     - Dormant Acres: 22,057
   - Each metric: label in text-[9px] uppercase tracking-widest, value in text-sm font-extrabold
   - Right side: pill showing "Trigger Rules: 31" with Terminal icon

4. `src/components/layout/AppLayout.tsx`
   - Composes SideNav + TopNav + MetricsStrip
   - Main content area: ml-[240px] min-h-[calc(100vh-56px)] pb-[64px]
   - Renders <Outlet /> for route content

5. `src/components/layout/CommandPalette.tsx`
   - Triggered by Cmd+K keyboard shortcut
   - Modal overlay with 40% dark backdrop
   - White rounded-[16px] card, max-w-[640px], centered
   - Search input at top with Cmd+K badge
   - Grouped command list: MISSIONS, PIPELINE, AGENTS, NAVIGATE
   - Each item: icon + label + keyboard shortcut
   - Selected item: border-l-[3px] border-primary bg-primary/5
   - Footer: ESC to close, arrow keys to navigate, version "NEXUS v4.2.1"

### Acceptance Criteria:
- [ ] SideNav highlights the current route
- [ ] TopNav is sticky and blurs content behind it
- [ ] MetricsStrip is always visible at bottom
- [ ] Cmd+K opens/closes the command palette
- [ ] ESC closes the command palette
- [ ] All text uses Inter font
- [ ] No explicit border lines between sections — only tonal shifts

### Do NOT:
- Implement command palette actions yet — just the UI
- Fetch any real data — use hardcoded values
```

---

## PROMPT 2: Mesh Page (Event Nerve Center)

```
Build the Mesh page — the event nerve center visualization showing the trigger engine and agent network.

### Create these files:

1. `src/pages/MeshPage.tsx` — 3-column layout:
   - Left column (240px): Agent Roster
   - Center: Event Mesh Canvas (SVG visualization)
   - Right column (320px): Intel Feed

2. `src/components/mesh/AgentRoster.tsx`
   - Column of agent status cards
   - Each card: white bg, rounded-xl, subtle border
   - Agent name (text-xs font-bold), status dot (colored), event count, status label
   - Status colors: green (#059669) = active, copper (#B07D3B) + pulse animation = pulsing, gray (#9CA3AF) = idle, amber (#D97706) = cooldown
   - 8 agents: Supply Intel, Municipal Intel, Demographic Agt, Zoning Auditor, Risk Engine, Permit Tracker, GIS Liaison, Macro Harvester
   - Header: "Active Agents" label + "08/08" count

3. `src/components/mesh/MeshCanvas.tsx`
   - SVG-based visualization on a dot-grid background (radial-gradient dots, 32px spacing, outline-variant color at 20% opacity)
   - Two concentric dashed circles (r=180, r=280) in outline-variant
   - 6 mesh connection lines from center to orbiting nodes (dashed, outline-variant)
   - Center: 72px copper-gradient circle with Zap icon, "TRIGGER ENGINE" label below
   - 5 orbiting nodes: white circles (48px) with copper border, each with a different icon (Package, Building, TrendingUp, Map, Sparkles)
   - Small floating copper dots as particles (decorative)
   - Right-side slide-over panel (360px): Agent detail view with stats grid (Runs Today, Avg Duration, Events Emitted, Hit Rate), recent operations list, "Re-initialize Agent" copper button

4. `src/components/mesh/IntelFeed.tsx`
   - Right column, bg-surface-container-low
   - Tab bar: SIGNALS | RULES | CLUSTERS (SIGNALS active with copper underline)
   - Signal cards: white bg, rounded-xl, type badge (e.g. "SUBDIVISION REMNANT" in primary/10 bg), timestamp, title, description, tier indicator
   - Progress/rule card: rule name, progress bar (copper fill), percentage
   - Cluster listing: compact cards with owner name, lot count, location

### Design Details:
- Dot grid background: `background-image: radial-gradient(#d4c4b4 1px, transparent 1px); background-size: 32px 32px;` at 20% opacity
- Ghost gradients: fixed positioned radial gradients in top-right and bottom-left corners for warmth

### Acceptance Criteria:
- [ ] 3-column layout renders correctly
- [ ] SVG mesh visualization shows center hub + orbiting nodes + connection lines
- [ ] Agent cards show correct status colors and pulse animation
- [ ] Intel feed tabs switch content
- [ ] Slide-over panel appears when clicking a mesh node
- [ ] Dot grid background is visible but subtle

### Do NOT:
- Make the mesh interactive/draggable yet
- Connect to any backend
- Implement real WebSocket connections
```

---

## PROMPT 3: Command Page (Swarm Control)

```
Build the Command page — the live agent intelligence and swarm control interface.

### Create these files:

1. `src/pages/CommandPage.tsx` — 3-section layout:
   - Left (300px): Agent roster with expanded cards
   - Center: Neural core visualization + floating intel window
   - Right (320px): Live intel stream

2. `src/components/command/AgentRosterExpanded.tsx`
   - Wider cards than Mesh page (300px column)
   - Each card shows: agent name, status dot, STATUS text with description (e.g. "Calculating all-in waterfalls for 12 new clusters...")
   - Two action buttons per card: "Schedule" button + chat icon button
   - Cards for active agents are full-opacity, idle agents at opacity-70

3. `src/components/command/NeuralCore.tsx`
   - Same SVG base as Mesh but with "Neural Core Alpha" branding
   - Larger center circle (88px) with copper-gradient, neural-glow box-shadow, Brain icon
   - `neural-glow: box-shadow: 0 0 20px rgba(127, 83, 19, 0.4), 0 0 40px rgba(127, 83, 19, 0.2)`
   - Scanline animation overlay on the dot grid
   - Floating "Live Discovery" window above center: white/90 backdrop-blur card with owner details (name, phone, email, listing broker/trust info)

4. `src/components/command/AgentTerminal.tsx`
   - Floating card positioned at bottom-right, 400px wide, 320px tall
   - Header: "Agent Terminal" + "Live Swarm Reasoning Pipeline" subtitle + green pulse dot + "Swarm Ready"
   - Monospace font log entries with timestamps, agent names (colored), and messages
   - Each entry: border-l-2 border-primary/20, timestamp in text-[9px], agent name in uppercase primary color, message text
   - Bottom: text input "Send swarm instructions..." with send button
   - Background: warm off-white (#FAF8F5)

5. `src/components/command/LiveIntelStream.tsx`
   - Right column with "Live Intel Stream" header
   - Tabs: SIGNALS | RULES
   - Intel cards with "Contact Owner" / "Contact Broker" action buttons
   - "Swarm Autonomy" progress card: percentage bar showing 82%

### Acceptance Criteria:
- [ ] Neural core pulses with glow effect
- [ ] Agent terminal shows scrollable log entries
- [ ] Terminal input field is functional (captures text, clears on enter)
- [ ] Live Discovery floating window renders above the neural core
- [ ] Scanline animation is subtle and doesn't interfere with readability

### Do NOT:
- Implement actual agent communication
- Auto-scroll the terminal (let user control scroll)
```

---

## PROMPT 4: Radar Page (Map Intelligence)

```
Build the Radar page — the primary map interface with polygon drawing, cluster markers, and intelligence sidebar.

### Create these files:

1. `src/pages/RadarPage.tsx` — full-width layout:
   - Left: Map canvas (flex-1)
   - Right: Intelligence sidebar (380px)

2. `src/components/radar/MapCanvas.tsx`
   - Leaflet map with Mapbox Light tiles (or OpenStreetMap as fallback)
   - Default center: Washtenaw County, MI (42.2808, -83.7430), zoom 11
   - Polygon draw tool (Leaflet Draw) with copper-colored polygon (#7f5313, dashed stroke, 10% fill)
   - Cluster markers: colored circles sized by lot count
     - HIGHEST: copper-gradient, 48px, white text
     - HIGH: primary/60, 40px
     - MEDIUM: gray (#9CA3AF), 32px
     - LOW: light gray (#D1D5DB), 24px
   - Click marker → popup card: owner name, township, lot count, score, "View Intel" + "Mission" buttons
   - Floating "Draw Territory" button: bottom-left, copper-gradient, pill shape
   - "Launch Mission" bar: bottom-center, dark bg (stone-900), shows "Scan X parcels in Y townships" + Launch/Clear buttons

3. `src/components/radar/IntelSidebar.tsx`
   - 380px right panel, white bg, scrollable
   - Stats grid at top: 2x2 grid showing Clusters, Total Lots, High Signal, Tier 1 Opps
   - Filters section: Signal Intensity segmented control (All/Highest/High/Med/Low), Tier dropdown, Concentration dropdown, Owner Search input
   - Results table: Owner, Lots, Signal (badge), Tier, Margin columns
   - Table rows are clickable with hover:text-primary transition

4. `src/components/radar/RadarSwarmActive.tsx`
   - Alternate radar state when a mission is active
   - Floating progress bar at top: "Swarm Active — 3 of 7 agents deployed" with copper progress bar
   - SVG polygon overlay with glowing copper bubbles at cluster locations
   - Pulsing marker with radar-pulse animation at active scan location
   - "Live Thinking Terminal" docked at bottom: dark bg (#1b1c1a/95), monospace log entries, green status dots

5. `src/hooks/useMapDraw.ts` — custom hook for Leaflet Draw polygon management

### Acceptance Criteria:
- [ ] Leaflet map renders with correct center/zoom for Washtenaw County
- [ ] Polygon draw tool creates copper-colored polygons
- [ ] Cluster markers render at correct sizes/colors
- [ ] Clicking a marker shows the popup card
- [ ] Intelligence sidebar filters are functional (client-side filtering)
- [ ] "Launch Mission" bar appears after drawing a polygon
- [ ] Swarm active state shows progress and terminal

### Do NOT:
- Connect to real Elasticsearch or SparkAPI
- Implement actual geo_shape queries
- Use Google Maps (use Leaflet + OpenStreetMap/Mapbox)
```

---

## PROMPT 5: Clusters Page (Intelligence Dossier)

```
Build the Clusters page — the deep cluster intelligence view with 50/50 map/list split and detail modal.

### Create these files:

1. `src/pages/ClustersPage.tsx` — 50/50 split:
   - Left half: Map view with cluster overlay
   - Right half: Scrollable cluster card list

2. `src/components/clusters/ClusterCards.tsx`
   - Header: "Deep Cluster Intelligence" title + result count + sort button
   - Cards with: owner name, township, lot count, acreage
   - Score ring (SVG circular progress): primary color stroke, score number in center
   - Stats row: 4-column grid (Lot Count, Acreage, Avg Land, Supply)
   - Dimension bars: progress bars for Zoning & Entitlement, Infrastructure Signal, Economic Demand Fit
   - "View Full Intel" copper-gradient button
   - Active card: full opacity with "Tier A Priority" badge (top-right, primary bg, white text)
   - Secondary cards: opacity-80 hover:opacity-100 with "Unlock Intel" gray button

3. `src/components/clusters/ClusterDetailModal.tsx`
   - Full overlay modal: stone-900/40 backdrop with backdrop-blur
   - Max-w-[960px] centered card with rounded-[1.5rem]
   - Header: cluster name + HIGHEST badge + TIER A badge + close button
   - 3-column body:
     - Col 1: Score ring (larger) + "Active Signals" list (Dev Exit Probability, CDOM Avg, Package Language, Linked Entities)
     - Col 2: Economics Waterfall (line items: Land Acquisition, Soft Costs, Vertical Build, Factory Unit Cost) + Estimated Profit/Net Margin highlight box
     - Col 3: Home Product Fit (Hawthorne 92%, Belmont 85%, Aspen 72% — progress bars) + AI suggestion card (dark bg with sparkle icon)
   - Footer: "Generate Broker Note" + "Export Deal Package" buttons (left), "View on Map" + "Deploy Deep Scan" copper button (right)

### Acceptance Criteria:
- [ ] 50/50 split renders correctly
- [ ] Score rings animate on mount (SVG stroke-dashoffset transition)
- [ ] Dimension progress bars have correct percentages
- [ ] Modal opens when clicking "View Full Intel" on a card
- [ ] Modal 3-column layout is correct
- [ ] Close button and backdrop click close the modal

### Do NOT:
- Implement actual "Deploy Deep Scan" functionality
- Connect to any data source
```

---

## PROMPT 6: Deep Assessment Pages (Layer 2)

```
Build the Deep Assessment view — the detailed property/cluster analysis with multiple sub-views.

### Create these files:

1. `src/pages/DeepAssessmentPage.tsx`
   - Alternative navigation: top nav shows "BaseMod LandOS" with Portfolio/Feasibility/Financials/Environmental tabs
   - Left sidebar (256px) with: Site Feasibility heading, Assessment/Financials/Zoning/Environmental/Agent Logs nav items
   - Main content scrollable

2. `src/components/assessment/AssessmentHeader.tsx`
   - Breadcrumb: "Active Entity → Horseshoe Lake Corporation"
   - Title: "Deep Assessment (Layer 2)" with "Layer 2 Assessment" badge
   - Asset ID, address with location pin
   - Action buttons: "Call Broker" (outline) + "Message Agent" (copper-gradient)

3. `src/components/assessment/ScoreRing.tsx`
   - Large circular SVG progress ring (160x160)
   - Score number (64), "Review" status label
   - Sub-dimension bars: Zoning Fit 82%, Lot Economics 45% (yellow), Infrastructure 68%, Market Signal 91%

4. `src/components/assessment/CostWaterfall.tsx`
   - Line-item breakdown: Factory, Site Work, Infrastructure, Soft Costs, Contingency, Land/Lot, Closing
   - Monospace values aligned right
   - "Portfolio Value" highlight box at bottom with border-l-4 border-primary

5. `src/components/assessment/ComplianceStatus.tsx`
   - Utility grid: Sewer (green), Water (green), Gas (yellow/pending), Electric (green)
   - Each as a small card with icon, label, status
   - External data links list: County Soil Map, EPA Flood Zone, Historical Plat Archives

6. `src/components/assessment/BrokerContact.tsx`
   - Broker photo/avatar, name, company
   - Phone and email with icons
   - "Call Broker" copper button + "Message" outline button

7. `src/components/assessment/BrokerNotes.tsx`
   - Grid of note cards (2-column)
   - PRIVATE notes: primary bg badge, border-l-4 border-error/50
   - PUBLIC notes: gray badge
   - Each with MLS number, address, note text, timestamp

8. `src/components/assessment/ParcelInventory.tsx`
   - Full-width table: Parcel ID, Lot Size, Status, Agent Findings
   - Alternating row backgrounds (warm off-white)
   - Status badges: "Vacant" (gray), "Listed" (primary/10)
   - Agent findings in italic

9. `src/components/assessment/AgentTerminalSection.tsx`
   - Dark terminal (stone-950 bg) with macOS window controls (red/yellow/green dots)
   - "Agent Terminal — Live Thinking" header
   - Monospace log entries with colored agent names
   - Blinking cursor at bottom

### Acceptance Criteria:
- [ ] 3-column grid layout renders correctly
- [ ] Score ring SVG animates
- [ ] Cost waterfall items are properly aligned
- [ ] Compliance icons show correct colors per status
- [ ] Broker notes distinguish PRIVATE vs PUBLIC visually
- [ ] Parcel table has alternating row colors
- [ ] Terminal has realistic log entries with blinking cursor
- [ ] Navigation between Assessment sub-views works

### Do NOT:
- Implement actual phone/email actions
- Connect to Michigan.gov or any external data
```

---

## PROMPT 7: Economics Page (Deal Analysis)

```
Build the Economics page — the financial modeling and deal analysis dashboard.

### Create these files:

1. `src/pages/EconomicsPage.tsx` — bento grid layout with header

2. `src/components/economics/CostWaterfallChart.tsx`
   - Col-span-8 card
   - Stacked horizontal bar showing component allocation (copper gradient segments)
   - Legend with colored dots: Factory $128.4k, Site Work $45.2k, Infra $36.1k, Soft Costs $28k
   - Summary: Total Project Cost $312,480/Unit, Profit/Unit $103.8k, Margin 33.2%
   - Dropdown selector: "Aspen XMOD → Ypsilanti"

3. `src/components/economics/PortfolioValue.tsx`
   - Col-span-4 card with copper tinted background (primary/5)
   - $18.3M projected net profit (large text)
   - Line items: 23 Tier 1 clusters, $64.2M total revenue, 28.4% target IRR

4. `src/components/economics/DealSensitivity.tsx`
   - Col-span-7 table
   - Columns: Acquisition, Profit, Margin, Tier (badge), Portfolio Impact
   - Highlighted row for target price
   - Tier badges: A+ (copper), A (copper), B (gray), C (light gray)

5. `src/components/economics/MarketComparables.tsx`
   - Col-span-5 card
   - New Construction: $312,000 avg list price with "+16.9% Premium" badge
   - Existing Homes: $267,000 avg sale price (muted)
   - Quote block with border-l-4 border-primary

6. `src/components/economics/DormantSupply.tsx`
   - Col-span-12 full-width card
   - Header with legend dots: 76 clusters, 22,057 acres, $772M total value
   - Grid of owner cards: Toll Brothers 146, M/I Homes 99, PulteGroup 82, etc.

### Acceptance Criteria:
- [ ] Bento grid renders with correct column spans
- [ ] Stacked bar has distinct copper gradient segments
- [ ] Sensitivity table highlights target row
- [ ] Portfolio value card has warm copper-tinted background
- [ ] Dormant supply grid shows all owner cards
- [ ] All monetary values formatted with $ and commas

### Do NOT:
- Build interactive sliders or calculators yet
- Use Chart.js or Recharts — build with CSS/HTML
```

---

## PROMPT 8: Pipeline Page (Deal Tracker Kanban)

```
Build the Pipeline page — the Kanban-style deal tracking board.

### Create these files:

1. `src/pages/PipelinePage.tsx` — horizontal scrolling kanban

2. `src/components/pipeline/KanbanBoard.tsx`
   - Horizontal scroll container with snap-x
   - 7 columns, each 280px: DISCOVERED, RESEARCHED, OUTREACH DRAFTED, CONTACTED, NEGOTIATING, UNDER CONTRACT, CLOSED
   - Column header: uppercase label + count badge (rounded-full bg-primary/10)

3. `src/components/pipeline/DealCard.tsx`
   - White card, rounded-xl, shadow-sm hover:shadow-md
   - Tier 1 cards: border-l-[3px] border-primary
   - Content: title, entity type, location, unit count
   - Score and signal indicator at bottom
   - Timestamp: "Updated Xh ago"
   - Under Contract cards: progress bar showing due diligence progress

4. `src/components/pipeline/EmptyColumn.tsx`
   - Dashed border placeholder for empty columns
   - Icon + "No closed deals yet..." message
   - "View Archives" link

5. FAB button: fixed bottom-right, copper bg, + icon, "Add New Lead" tooltip on hover

### Acceptance Criteria:
- [ ] Horizontal scroll works smoothly
- [ ] Columns have correct headers and counts
- [ ] Tier 1 cards have copper left border
- [ ] Empty "CLOSED" column shows placeholder
- [ ] FAB tooltip appears on hover
- [ ] Cards are visually distinct per stage

### Do NOT:
- Implement drag-and-drop (yet)
- Add filtering or sorting
```

---

## PROMPT 9: Missions Control Page (Wake the Swarm)

```
Build the Missions Control page — the mission deployment and monitoring interface.

### Create these files:

1. `src/pages/MissionsPage.tsx` — alternative layout:
   - Left sidebar (different from main nav): "Acquisition HQ" branding, Dashboard/Land Swarm/Agent Tracking/Mission Archives/Analytics nav
   - "Wake the Swarm" copper button at bottom of sidebar

2. `src/components/missions/ActionBar.tsx`
   - 4-card grid: Upload Data, Polygon Search, Deploy Agent, Generate Report
   - Each: icon container (surface-container-low bg, hover:copper transition), title, description

3. `src/components/missions/MissionList.tsx`
   - Left column (col-span-4), scrollable
   - Mission cards: title, date, agent count, stats grid (Clusters/Tier 1/Duration)
   - border-l-4 border-outline-variant
   - Completed badges

4. `src/components/missions/ActiveMission.tsx`
   - Main area (col-span-8)
   - Header: pulsing green dot + "Live Mission Deployment" + mission title + elapsed time + "Abort Mission" button
   - Left half: Agent Swarm Status — progress bars for each agent (Scout 68%, Municipal 42%, Tax Assessor waiting, Geospatial 91%, Zoning 15%, two queued)
   - Right half: Live Discovery — large score ring (92) + target details (acreage, address, owner) + Tax Status/Zoning info cards + "View Full Assessment" button + summary stats (Listings/Vacant/Tier 1)
   - Bottom: Swarm Thought Process terminal (dark bg, monospace, scrollable log)

### Acceptance Criteria:
- [ ] Action bar cards have hover effects on icons
- [ ] Mission list is scrollable independent of main content
- [ ] Active mission shows real-time-style progress bars
- [ ] Agent progress bars show correct colors (copper for active, gray for queued)
- [ ] Terminal section has blinking cursor animation
- [ ] "Abort Mission" button is styled as dark/danger

### Do NOT:
- Implement actual mission orchestration
- Connect to Claude Agent SDK
```

---

## PROMPT 10: Outreach Pages (Broker SMS + Email Templates)

```
Build the Outreach pages — broker communication template editors.

### Create these files:

1. `src/pages/OutreachPage.tsx` — different top nav ("EstateIntel" branding)
   - Sidebar: Outreach Hub with Campaigns/Templates/Contacts/Automation/Reporting nav
   - Context bar: target asset name + broker name

2. `src/components/outreach/SMSTemplateEditor.tsx`
   - 3-column layout: Template Library (1/3) | SMS Editor (flex-1) | Phone Preview
   - Template library: categorized cards (Follow-up, Pricing, New Model Match)
   - Editor: textarea with dynamic placeholders ({{OwnerName}}, {{LotID}}, etc.), character counter
   - Phone preview: iPhone mockup (280x580px, dark border, rounded-[3rem]) with iOS-style chat bubble

3. `src/components/outreach/EmailTemplateEditor.tsx`
   - 2-column: Template Library (col-span-4) | Editor (col-span-8)
   - Library cards: Developer Fatigue (active), Stale Listing, Direct Acquisition, Zoning Pivot
   - Editor: recipient info header, subject line input (pill-shaped), email body textarea
   - Dynamic placeholder buttons: {{OwnerName}}, {{LotCount}}, {{AvgLandValue}}
   - Actions: Copy to Clipboard, Save Draft, Send Outreach (copper-gradient)
   - "Live Intelligence Thinking" terminal at bottom: dark bg, animated agent reasoning

### Acceptance Criteria:
- [ ] Template library cards are selectable (active state with border-l-4 primary)
- [ ] SMS editor shows character count and segment count
- [ ] Phone preview renders realistic iOS chat bubble
- [ ] Email editor has placeholder insertion buttons
- [ ] Placeholders are visually distinct in the textarea
- [ ] Terminal shows animated thinking indicator

### Do NOT:
- Implement actual SMS/email sending
- Connect to any messaging API
```

---

## PROMPT 11: Data Layer & State Management

```
Wire up the data layer with React Query and mock data that matches the design.

### Create these files:

1. `src/data/mockData.ts` — all mock data in one file:
   - Agents array (8 agents with name, status, eventCount, latency)
   - Clusters array (use real-ish Washtenaw County data: Toll Brothers 146 lots, M/I Homes 99, PulteGroup 84, Lennar 112, etc.)
   - Signals array (recent event mesh signals)
   - Pipeline deals array (across all kanban stages)
   - Missions array (2-3 completed, 1 active)
   - Economics data (cost waterfall, sensitivity matrix, comparables)
   - Broker templates (SMS and email)

2. `src/hooks/useAgents.ts` — React Query hook for agent data
3. `src/hooks/useClusters.ts` — React Query hook for cluster data
4. `src/hooks/usePipeline.ts` — React Query hook with mutations for stage changes
5. `src/hooks/useMissions.ts` — React Query hook for mission data
6. `src/hooks/useSignals.ts` — React Query hook for signal feed (with simulated polling)

7. `src/stores/appStore.ts` — lightweight Zustand or context store for:
   - Active county selection
   - Command palette open/close state
   - Selected cluster ID
   - Active mission ID

8. `src/lib/queryClient.ts` — configured React Query client

### Wire all hooks into the existing page components, replacing hardcoded data.

### Acceptance Criteria:
- [ ] All pages render data from hooks (not hardcoded)
- [ ] React Query devtools show active queries
- [ ] Signal feed simulates new items every 10 seconds
- [ ] Pipeline mutations work (card stage changes reflected)
- [ ] App store correctly manages global state
- [ ] No TypeScript errors

### Do NOT:
- Create a backend or API
- Use Redux
```

---

## PROMPT 12: Animations, Polish & Performance

```
Final polish pass — add animations, transitions, and performance optimizations.

### Tasks:

1. **Page Transitions**: Add framer-motion page transitions (fade + slight upward slide, 200ms)

2. **Component Animations**:
   - Score rings: animate stroke-dashoffset on mount (1s ease-out)
   - Progress bars: animate width on mount (800ms ease-out)
   - Cards: staggered fade-in on list pages (50ms delay between items)
   - Modal: scale from 0.95 + fade in (200ms)
   - Command palette: slide down from top + fade (150ms)
   - Cluster markers on map: scale in on load (300ms spring)

3. **Micro-interactions**:
   - Nav items: 200ms color transition
   - Cards: hover shadow transition (200ms)
   - Buttons: active:scale-[0.98] press effect
   - Table rows: hover:text-primary transition

4. **Ghost Gradients**: Add fixed-position radial gradient overlays:
   - Top-right: radial-gradient(circle at 100% 0%, #ffddb8 0%, transparent 70%) at 40% opacity
   - Bottom-left: radial-gradient(circle at 0% 100%, #9b6b2a 0%, transparent 70%) at 20% opacity
   - pointer-events-none, mix-blend-multiply

5. **Performance**:
   - Lazy load all page components with React.lazy + Suspense
   - Memoize expensive computations (cluster filtering, economics calculations)
   - Virtualize long lists (pipeline cards, parcel inventory table)
   - Add loading skeletons for data-dependent sections

6. **Responsive**: Ensure sidebar collapses on screens < 1024px (hamburger menu)

### Acceptance Criteria:
- [ ] Page transitions are smooth and consistent
- [ ] Score rings animate on first render
- [ ] Ghost gradients add warmth without interfering with content
- [ ] Lighthouse performance score > 90
- [ ] No layout shifts on page load
- [ ] Pages lazy-load correctly

### Do NOT:
- Add any new features
- Change the design system colors or typography
- Break any existing functionality
```

---

## DEPLOYMENT NOTE

After all 13 prompts are complete, deploy to Netlify:

```bash
npm run build
netlify deploy --prod --dir=dist
```

Update the DNS for agents.basemodhomes.com to point to the new Netlify deployment.

---

## REFERENCE: Screen Inventory

| # | Screen | Page | Key Components |
|---|--------|------|----------------|
| 1 | Mesh (Event Nerve Center) | /mesh | Agent roster, SVG mesh, intel feed |
| 2 | Swarm Command | /command | Neural core, agent terminal, live intel |
| 3 | Command Palette | overlay | ⌘K search, grouped commands |
| 4 | Radar (Map Intelligence) | /radar | Leaflet map, polygon draw, sidebar |
| 5 | Radar (Swarm Active) | /radar (state) | Progress bar, thinking terminal |
| 6 | Clusters (Intelligence Dossier) | /clusters | 50/50 split, score rings, detail modal |
| 7 | Deep Assessment (Integrated) | /assessment/:id | Score, waterfall, compliance |
| 8 | Deep Assessment (Parcel) | /assessment/:id/parcels | Parcel inventory table |
| 9 | Deep Assessment (Broker Notes) | /assessment/:id/notes | PRIVATE/PUBLIC note cards |
| 10 | Deep Assessment (Contact) | /assessment/:id/contact | Broker contact card |
| 11 | Economics (Deal Analysis) | /economics | Bento grid, sensitivity table |
| 12 | Pipeline (Deal Tracker) | /pipeline | Kanban board, deal cards |
| 13 | Missions Control | /missions | Mission list, active mission, progress |
| 14 | Broker SMS Templates | /outreach/sms | Template library, phone preview |
| 15 | Broker Outreach Templates | /outreach/email | Email editor, live thinking |

---

## REFERENCE: Design Token Quick Sheet

```
Primary Copper:     #7f5313
Primary Container:  #9b6b2a
Surface (base):     #fbf9f6
Card White:         #ffffff
Surface Low:        #f5f3f0
Surface Container:  #efeeeb
Text Primary:       #1b1c1a
Text Secondary:     #504539
Outline:            #827567
Outline Variant:    #d4c4b4
Status Green:       #059669
Status Amber:       #D97706
Error Red:          #ba1a1a
Tertiary Green:     #006948

Font: Inter (400, 500, 600, 700, 800)
Label Style: uppercase, tracking-widest, font-bold, text-[10px]
Card Radius: rounded-xl (0.75rem)
Card Shadow: 0 12px 32px rgba(27, 28, 26, 0.04)
Copper Gradient: linear-gradient(155deg, #7f5313, #9b6b2a)
Active Nav: border-l-[3px] border-primary text-primary bg-primary/5
```
