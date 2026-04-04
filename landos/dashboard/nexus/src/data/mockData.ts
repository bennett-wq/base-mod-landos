// ─── Centralized Mock Data ───────────────────────────────────────────────────
// Single source of truth for all mock data across NEXUS components.
// Replace the async fetchers in hooks/ with real API calls when ready.

// ─── Agent Types ─────────────────────────────────────────────────────────────

export type AgentStatus = 'ACTIVE' | 'PULSING' | 'IDLE' | 'COOLDOWN'

export interface Agent {
  name: string
  status: AgentStatus
  events: string
}

export interface AgentExpanded {
  name: string
  status: AgentStatus
  statusText: string
}

// ─── Cluster Types ───────────────────────────────────────────────────────────

export type Signal = 'HIGHEST' | 'HIGH' | 'MEDIUM' | 'LOW'
export type Tier = 'A' | 'B' | 'C'

export interface Cluster {
  id: string
  owner: string
  township: string
  position: [number, number]
  signal: Signal
  lots: number
  acreage: number
  avgLandValue: string
  supplyType: string
  score: number
  tier: Tier
  zoning: number
  infrastructure: number
  economicFit: number
  // Evidence fields from strategic ranker
  stallSignals?: string[]
  stallConfidence?: number
  infrastructureInvested?: boolean
  vacancyRatio?: number
  listingCount?: number
  listingAgents?: string[]
  bboSignalCount?: number
  opportunityType?: string
  parcelCount?: number
  subdivisionName?: string
}

export interface ClusterSummary {
  name: string
  lots: number
  type: string
  location: string
}

export interface TargetRow {
  owner: string
  lots: number
  signal: 'HIGHEST' | 'HIGH' | 'MED' | 'LOW'
  tier: string
  margin: string
}

// ─── Signal Types ────────────────────────────────────────────────────────────

export interface IntelSignal {
  type: string
  timestamp: string
  title: string
  description: string
  tier: number
}

export interface CommandSignal {
  type: string
  typeColor: string
  timestamp: string
  title: string
  description: string
  action: string
}

export interface TriggerRule {
  name: string
  progress: number
  description: string
}

// ─── Pipeline Types ──────────────────────────────────────────────────────────

export interface PipelineDeal {
  id: string
  title: string
  tier?: number
  entityType?: string
  location?: string
  lotCount?: number
  score?: number
  signal?: string
  updatedAgo: string
  note?: string
  contactStatus?: string
  lastContact?: string
  askingPrice?: string
  negotiationStatus?: string
  progressPercent?: number
  dueDiligence?: string
  // Evidence fields
  stallSignals?: string[]
  stallConfidence?: number
  infrastructureInvested?: boolean
  vacancyRatio?: number
  listingCount?: number
  listingAgents?: string[]
  acreage?: number
}

export interface PipelineStage {
  name: string
  deals: PipelineDeal[]
}

// ─── Mission Types ───────────────────────────────────────────────────────────

export interface Mission {
  title: string
  date: string
  agents: number
  clusters: number
  tier1: number
  duration: string
  dimmed?: boolean
}

// ─── Metric Types ────────────────────────────────────────────────────────────

export interface Metric {
  label: string
  value: string
  highlight?: boolean
}

export interface RadarStat {
  label: string
  value: string
  highlight: boolean
}

export interface DormantOwner {
  name: string
  lots: number
}

// ─── Data ────────────────────────────────────────────────────────────────────

export const AGENTS: Agent[] = [
  { name: 'Supply Intel', status: 'ACTIVE', events: '42.4k events' },
  { name: 'Municipal Intel', status: 'PULSING', events: '12.1k events' },
  { name: 'Demographic Agt', status: 'ACTIVE', events: '8.2k events' },
  { name: 'Zoning Auditor', status: 'IDLE', events: '3.4k events' },
  { name: 'Risk Engine', status: 'ACTIVE', events: '6.1k events' },
  { name: 'Permit Tracker', status: 'COOLDOWN', events: '1.8k events' },
  { name: 'GIS Liaison', status: 'ACTIVE', events: '1.2k events' },
  { name: 'Macro Harvester', status: 'IDLE', events: '892 events' },
]

export const AGENTS_EXPANDED: AgentExpanded[] = [
  { name: 'Supply Intel', status: 'ACTIVE', statusText: 'Calculating all-in waterfalls for 12 new clusters...' },
  { name: 'Municipal Agent', status: 'PULSING', statusText: 'Scanning 2026 Plat recordings in Scio Twp...' },
  { name: 'Zoning Auditor', status: 'COOLDOWN', statusText: 'Analyzing 142 parcels in Scio Twp for density...' },
  { name: 'Risk Engine', status: 'ACTIVE', statusText: 'Re-scoring 23 Tier 1 opportunities post-price shift...' },
  { name: 'Permit Tracker', status: 'ACTIVE', statusText: 'Monitoring 8 active site plan reviews in Washtenaw...' },
  { name: 'Demographic Agt', status: 'PULSING', statusText: 'Pulling 2025 Census tract updates for growth overlay...' },
  { name: 'GIS Liaison', status: 'IDLE', statusText: '' },
  { name: 'Macro Harvester', status: 'IDLE', statusText: '' },
]

export const CLUSTERS: Cluster[] = [
  { id: 'NEX-88129-WAS', owner: 'Horseshoe Lake Corp',   township: 'Saline Twp',    position: [42.165, -83.83],  signal: 'HIGHEST', lots: 88,  acreage: 142,  avgLandValue: '$42,000',  supplyType: 'TIGHT',   score: 91, tier: 'A', zoning: 82, infrastructure: 45, economicFit: 91 },
  { id: 'NEX-71204-WAS', owner: 'Julian Francis Trust',   township: 'Lima Twp',      position: [42.238, -83.612], signal: 'HIGHEST', lots: 12,  acreage: 8.4,  avgLandValue: '$68,000',  supplyType: 'SCARCE',  score: 84, tier: 'A', zoning: 78, infrastructure: 62, economicFit: 88 },
  { id: 'NEX-55301-WAS', owner: 'Toll Brothers Holdings', township: 'Augusta Twp',   position: [42.338, -83.862], signal: 'HIGH',    lots: 146, acreage: 312,  avgLandValue: '$5,907K',  supplyType: 'DORMANT', score: 67, tier: 'B', zoning: 84, infrastructure: 62, economicFit: 91 },
  { id: 'NEX-42018-WAS', owner: 'M/I Homes LLC',          township: 'Ann Arbor Twp', position: [42.248, -83.729], signal: 'MEDIUM',  lots: 99,  acreage: 186,  avgLandValue: '$3,200K',  supplyType: 'TIGHT',   score: 52, tier: 'B', zoning: 60, infrastructure: 38, economicFit: 64 },
  { id: 'NEX-33905-WAS', owner: 'PulteGroup',             township: 'Ypsilanti Twp', position: [42.189, -83.777], signal: 'LOW',     lots: 82,  acreage: 94,   avgLandValue: '$1,800K',  supplyType: 'NORMAL',  score: 34, tier: 'C', zoning: 42, infrastructure: 28, economicFit: 40 },
]

export const CLUSTER_SUMMARIES: ClusterSummary[] = [
  { name: 'Toll Brothers Holdings', lots: 146, type: 'Highest Owner', location: 'Dexter, MI' },
  { name: 'Pulte Homes Corp', lots: 82, type: 'Pipelining', location: 'Saline, MI' },
  { name: 'M/I Homes LLC', lots: 99, type: 'Dormant Supply', location: 'Pittsfield Twp' },
  { name: 'Julian Francis Trust', lots: 12, type: 'Active Cluster', location: 'Ypsilanti Twp' },
]

export const TARGETS: TargetRow[] = [
  { owner: 'Toll Brothers',        lots: 146, signal: 'HIGHEST', tier: 'A', margin: '33.0%' },
  { owner: 'M/I Homes LLC',        lots: 99,  signal: 'HIGHEST', tier: 'A', margin: '38.7%' },
  { owner: 'Horseshoe Lake Corp',  lots: 88,  signal: 'HIGHEST', tier: 'A', margin: '29.4%' },
  { owner: 'PulteGroup',           lots: 82,  signal: 'HIGH',    tier: 'B', margin: '24.2%' },
  { owner: 'Lennar Corp',          lots: 112, signal: 'MED',     tier: 'A', margin: '18.5%' },
  { owner: 'Julian Francis Trust', lots: 12,  signal: 'HIGHEST', tier: 'A', margin: '41.2%' },
  { owner: 'NVR Inc',              lots: 64,  signal: 'HIGH',    tier: 'B', margin: '22.8%' },
  { owner: 'Meritage Homes',       lots: 47,  signal: 'MED',     tier: 'B', margin: '19.1%' },
  { owner: 'Taylor Morrison',      lots: 38,  signal: 'LOW',     tier: 'C', margin: '15.3%' },
  { owner: 'Century Complete',     lots: 29,  signal: 'LOW',     tier: 'C', margin: '12.7%' },
]

export const RADAR_STATS: RadarStat[] = [
  { label: 'Clusters',    value: '2,229', highlight: false },
  { label: 'Total Lots',  value: '10,266', highlight: false },
  { label: 'High Signal', value: '847',   highlight: true },
  { label: 'Tier 1 Opps', value: '23',    highlight: false },
]

export const SIGNALS: IntelSignal[] = [
  {
    type: 'SUBDIVISION REMNANT',
    timestamp: '2m ago',
    title: 'Horseshoe Lake Corp — 88 lots identified',
    description: 'Historical plat remnant detected in Augusta Twp. Owner cluster spans 3 adjacent sections.',
    tier: 1,
  },
  {
    type: 'OWNER CLUSTER',
    timestamp: '8m ago',
    title: 'Julian Francis Trust — 12 parcels',
    description: 'Concentrated ownership in Ypsilanti Charter Twp. 4 parcels have active BBO language.',
    tier: 1,
  },
  {
    type: 'PRICE REDUCTION',
    timestamp: '14m ago',
    title: '2.4 acre parcel, Saline — 15% reduction',
    description: 'Listed 180 days. Third price reduction signals motivated seller. Adjacent to approved PUD.',
    tier: 2,
  },
  {
    type: 'MUNICIPAL EVENT',
    timestamp: '22m ago',
    title: 'Ypsilanti Twp adopted Section 108(6)',
    description: '47 parcels affected by new site-condo density allowance. Rescoring triggered.',
    tier: 1,
  },
  {
    type: 'PACKAGE LANGUAGE',
    timestamp: '31m ago',
    title: 'Broker notes: "will sell as package"',
    description: '6 lots in Dexter identified with BBO/package language in MLS remarks field.',
    tier: 2,
  },
]

export const COMMAND_SIGNALS: CommandSignal[] = [
  {
    type: 'SUBDIVISION REMNANT',
    typeColor: 'bg-primary/10 text-primary',
    timestamp: '2m ago',
    title: 'Ann Arbor NW Cluster',
    description: 'Detected 14.5 acre split candidate from historical deeds.',
    action: 'Contact Owner',
  },
  {
    type: 'ZONING SHIFT',
    typeColor: 'bg-[#059669]/10 text-[#059669]',
    timestamp: '14m ago',
    title: 'Dexter Village Rezoning',
    description: 'Public hearing notice for R-3 conversion on Baker Rd.',
    action: 'Contact Broker',
  },
  {
    type: 'PRICE REDUCTION',
    typeColor: 'bg-primary/10 text-primary',
    timestamp: '31m ago',
    title: 'Saline 2.4ac — 15% Drop',
    description: 'Third price reduction signals motivated seller. Adjacent to approved PUD.',
    action: 'Contact Owner',
  },
]

export const TRIGGER_RULES: TriggerRule[] = [
  { name: 'Listing Added (RA)', progress: 85, description: 'Classifying Remarks' },
  { name: 'Price Changed (RB)', progress: 100, description: 'Complete' },
  { name: 'BBO Detected (RI)', progress: 62, description: 'Cross-referencing clusters' },
  { name: 'Municipal Scan (RV)', progress: 44, description: 'Processing hearings' },
]

export const PIPELINE_STAGES: PipelineStage[] = [
  {
    name: 'DISCOVERED',
    deals: [
      {
        id: 'd1',
        title: 'Horseshoe Lake Corp',
        tier: 1,
        entityType: 'CORPORATION',
        location: 'Augusta Twp, Washtenaw',
        lotCount: 92,
        score: 67,
        signal: 'HIGHEST',
        updatedAgo: 'Updated 2h ago',
      },
      {
        id: 'd2',
        title: 'Julian Francis',
        entityType: 'INDIVIDUAL',
        location: 'Superior Twp',
        lotCount: 34,
        score: 42,
        updatedAgo: 'Updated 5h ago',
      },
      {
        id: 'd3',
        title: 'Toll Brothers Holdings',
        tier: 1,
        entityType: 'OWNER',
        location: 'Augusta Twp',
        lotCount: 146,
        score: 71,
        signal: 'HIGHEST',
        updatedAgo: 'Updated 2h ago',
      },
      {
        id: 'd4',
        title: 'M/I Homes',
        entityType: 'BUILDER',
        location: 'York Twp',
        lotCount: 99,
        score: 55,
        signal: 'HIGH',
        updatedAgo: 'Updated 6h ago',
      },
    ],
  },
  {
    name: 'RESEARCHED',
    deals: [
      {
        id: 'r1',
        title: 'PulteGroup',
        location: 'Pittsfield Twp',
        lotCount: 59,
        score: 48,
        updatedAgo: 'Updated 4h ago',
      },
      {
        id: 'r2',
        title: 'Lennar',
        location: 'Scio Twp',
        lotCount: 210,
        score: 52,
        updatedAgo: 'Updated 8h ago',
      },
      {
        id: 'r3',
        title: 'NVR Inc',
        location: 'Lima Twp',
        lotCount: 44,
        score: 39,
        updatedAgo: 'Updated 1d ago',
      },
    ],
  },
  {
    name: 'OUTREACH DRAFTED',
    deals: [
      {
        id: 'o1',
        title: 'Meritage Homes',
        tier: 1,
        location: 'Saline',
        lotCount: 78,
        note: 'Proposal for mixed-use assemblage finalized.',
        signal: 'HIGH',
        updatedAgo: 'Updated 3h ago',
      },
      {
        id: 'o2',
        title: 'Taylor Morrison',
        location: 'Dexter Twp',
        lotCount: 36,
        note: 'Initial outreach letter drafted.',
        updatedAgo: 'Updated 12h ago',
      },
    ],
  },
  {
    name: 'CONTACTED',
    deals: [
      {
        id: 'c1',
        title: 'Century Complete',
        contactStatus: 'Sent / Awaiting',
        lastContact: 'Mar 12',
        updatedAgo: 'Updated 1d ago',
      },
      {
        id: 'c2',
        title: 'Saline Valley Farms',
        contactStatus: 'Follow-up Scheduled',
        lastContact: 'Mar 15',
        updatedAgo: 'Updated 8h ago',
      },
    ],
  },
  {
    name: 'NEGOTIATING',
    deals: [
      {
        id: 'n1',
        title: 'Bank of Ann Arbor',
        tier: 1,
        lotCount: 28,
        location: 'Ann Arbor Twp',
        askingPrice: '$4.2M Asking',
        negotiationStatus: 'In Counter',
        updatedAgo: 'Updated 6h ago',
      },
    ],
  },
  {
    name: 'UNDER CONTRACT',
    deals: [
      {
        id: 'u1',
        title: 'Westover Hills',
        progressPercent: 65,
        dueDiligence: 'Due Diligence: Day 39/60',
        updatedAgo: 'Updated 1h ago',
      },
    ],
  },
  {
    name: 'CLOSED',
    deals: [],
  },
]

export const MISSIONS: Mission[] = [
  {
    title: 'Washtenaw County Sweep',
    date: 'Oct 12, 2023',
    agents: 12,
    clusters: 2229,
    tier1: 23,
    duration: '14m 22s',
  },
  {
    title: 'Scio Twp Phase 2',
    date: 'Oct 10, 2023',
    agents: 8,
    clusters: 841,
    tier1: 12,
    duration: '08m 10s',
  },
  {
    title: 'Dexter Overlay Scan',
    date: 'Oct 08, 2023',
    agents: 5,
    clusters: 312,
    tier1: 4,
    duration: '03m 45s',
    dimmed: true,
  },
]

export const METRICS: Metric[] = [
  { label: 'Active Listings', value: '95' },
  { label: 'Vacant Parcels', value: '10,266' },
  { label: 'Clusters', value: '2,229' },
  { label: 'Tier 1 Opps', value: '23', highlight: true },
  { label: 'Dormant Acres', value: '22,057' },
]

export const DORMANT_OWNERS: DormantOwner[] = [
  { name: 'Toll Brothers', lots: 146 },
  { name: 'M/I Homes', lots: 99 },
  { name: 'PulteGroup', lots: 82 },
  { name: 'Lennar Corp', lots: 74 },
  { name: 'KB Home', lots: 61 },
  { name: 'NVR Inc', lots: 54 },
  { name: 'Taylor Morrison', lots: 38 },
  { name: 'Century', lots: 29 },
]
