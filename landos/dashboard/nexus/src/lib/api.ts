/**
 * LandOS API client — fetches real pipeline intelligence from the FastAPI backend.
 *
 * Every operator-critical hook calls through here.
 * If the API is unreachable, callers get typed empty responses (NOT mock data).
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/** True when the last API call succeeded — used by MetricsStrip "Live" indicator. */
let _lastFetchOk = false
export function isApiLive(): boolean { return _lastFetchOk }

export async function apiFetch<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`)
    if (!res.ok) throw new Error(`API ${res.status}`)
    _lastFetchOk = true
    return await res.json()
  } catch {
    console.warn(`[LandOS API] ${path} unavailable — returning empty`)
    _lastFetchOk = false
    return fallback
  }
}

// ── Stats ───────────────────────────────────────────────────────────────────

export interface ApiStats {
  active_listings: number
  total_parcels: number
  vacant_parcels: number
  clusters: number
  clusters_with_listings: number
  opportunities: number
  pipeline_run: Record<string, unknown>
}

export function fetchStats(): Promise<ApiStats> {
  return apiFetch('/api/stats', {
    active_listings: 0,
    total_parcels: 0,
    vacant_parcels: 0,
    clusters: 0,
    clusters_with_listings: 0,
    opportunities: 0,
    pipeline_run: {},
  })
}

// ── Clusters ────────────────────────────────────────────────────────────────

export interface ApiClusterResponse {
  count: number
  total: number
  clusters: ApiCluster[]
}

export interface ApiCluster {
  cluster_id: string
  cluster_type: string
  detection_method: string
  member_count: number
  municipality_id?: string
  total_acreage?: number
  total_list_value?: number
  parcel_ids?: string[]
  listing_ids?: string[]
  owner_ids?: string[]
  geographic_centroid?: { type: string; coordinates: number[] }
  _group_key: string
  _parcel_count: number
  _listing_count: number
  _has_active_listings: boolean
}

export function fetchClusters(params?: {
  min_lots?: number
  has_listings?: boolean
  cluster_type?: string
}): Promise<ApiClusterResponse> {
  const searchParams = new URLSearchParams()
  if (params?.min_lots) searchParams.set('min_lots', String(params.min_lots))
  if (params?.has_listings) searchParams.set('has_listings', 'true')
  if (params?.cluster_type) searchParams.set('cluster_type', params.cluster_type)
  const qs = searchParams.toString()
  return apiFetch(`/api/clusters${qs ? `?${qs}` : ''}`, { count: 0, total: 0, clusters: [] })
}

// ── Signals ─────────────────────────────────────────────────────────────────

export interface ApiSignalResponse {
  count: number
  signals: ApiSignal[]
}

export interface ApiSignal {
  signal_id: number
  event_type: string
  event_id: string
  entity_ref_summary: string
  fired_rules: string
  payload_summary: string
  created_at: string
}

export function fetchSignals(limit = 50): Promise<ApiSignalResponse> {
  return apiFetch(`/api/signals?limit=${limit}`, { count: 0, signals: [] })
}

// ── Strategic Opportunities ─────────────────────────────────────────────────

export interface ApiStrategicResponse {
  count: number
  query: { min_lots: number | null; infrastructure_only: boolean | null }
  opportunities: ApiStrategicOpp[]
}

/**
 * Full StrategicOpportunity from the backend.
 * This is the PRODUCT — every field here is computed by the pipeline,
 * not derived in the frontend.
 */
export interface ApiStrategicOpp {
  opportunity_id: string
  name: string
  opportunity_type: string   // "stalled_subdivision" | "owner_cluster" | "subdivision_cluster"
  municipality_id?: string
  precedence_tier: number    // 1 = highest priority (owner clusters), 4 = lowest

  // Core metrics
  lot_count: number
  total_acreage: number
  infrastructure_invested: boolean
  stall_confidence: number
  vacancy_ratio: number

  // Signal presence
  has_active_listings: boolean
  listing_count: number       // ACTIVE listings only
  bbo_signal_count: number
  municipal_posture: string

  // Identification
  owner_name: string
  subdivision_name: string
  cluster_id?: string
  subdivision_id?: string

  // Listings detail
  listing_keys: string[]
  listing_agents: string[]

  // Parcel IDs
  parcel_ids: string[]

  // Centroid for map
  centroid_lat?: number
  centroid_lon?: number

  // Stall evidence
  stall_signals: string[]

  // Historical listing evidence — SEPARATE from live listing_count
  historical_listing_count: number
  expired_listing_count: number
  withdrawn_listing_count: number
  canceled_listing_count: number
  has_relist_cycle: boolean
  partial_release_detected: boolean
  max_cdom: number
  avg_cdom: number

  // BBO note evidence
  package_language_detected: boolean
  fatigue_language_detected: boolean
  distress_language_detected: boolean
  infrastructure_ready_detected: boolean
  development_ready_detected: boolean
  remarks_excerpts: string[]

  // Structured infrastructure profile
  structured_infra_score: number
  infra_flags: string[]
  has_public_sewer: boolean
  has_public_water: boolean
  has_natural_gas: boolean
  has_paved_road: boolean
  is_buildable: boolean
  is_site_condo: boolean
  has_wetland: boolean

  // Broker-note intelligence
  broker_signals: string[]
  splits_available: boolean
  all_offers_considered: boolean
  seller_is_agent: boolean
  site_tested: boolean
  has_documents: boolean
  document_count: number

  // Owner-linked historical seller evidence
  owner_linked_active_count: number
  owner_linked_historical_count: number
  owner_linked_failed_exit_count: number
  owner_linked_expired_count: number
  owner_linked_withdrawn_count: number
  owner_linked_canceled_count: number
  owner_linked_agents: string[]
  owner_linked_offices: string[]
  owner_linked_listing_keys: string[]
  repeat_agent_on_owner_inventory: boolean
  owner_link_match_methods: string[]
  owner_link_confidence: number
  owner_linked_notes_present: boolean
  owner_linked_documents_present: boolean
  owner_linked_notes_count: number
  owner_linked_document_count: number

  // Legal description evidence
  legal_lot_numbers: number[]
  same_sub_listing_count: number

  // Composite history score
  history_signal_score: number

  // Computed
  composite_score: number
  score_breakdown: Record<string, number>
}

// ── Strategic Detail (single opportunity + parcels) ────────────────────────

export interface ApiParcel {
  parcel_id: string
  regrid_id?: string
  municipality_id?: string
  county?: string
  vacancy_status?: string
  acreage?: number
  owner_name_raw?: string
  opportunity_score?: number
  centroid_lat?: number
  centroid_lon?: number
  address_raw?: string
  zoning_raw?: string
  subdivision_id?: string
  source_system_ids?: Record<string, string>
  parcel_number_raw?: string
  legal_description_raw?: string
}

export interface ApiStrategicDetailResponse {
  opportunity: ApiStrategicOpp
  parcels: ApiParcel[]
}

export function fetchStrategicById(id: string): Promise<ApiStrategicDetailResponse | null> {
  return apiFetch(`/api/strategic/${encodeURIComponent(id)}`, null)
}

// ── Strategic List ─────────────────────────────────────────────────────────

export function fetchStrategic(params?: {
  min_lots?: number
  infrastructure?: boolean
  limit?: number
}): Promise<ApiStrategicResponse> {
  const searchParams = new URLSearchParams()
  if (params?.min_lots) searchParams.set('min_lots', String(params.min_lots))
  if (params?.infrastructure) searchParams.set('infrastructure', 'true')
  if (params?.limit) searchParams.set('limit', String(params.limit))
  const qs = searchParams.toString()
  return apiFetch(`/api/strategic${qs ? `?${qs}` : ''}`, {
    count: 0,
    query: { min_lots: null, infrastructure_only: null },
    opportunities: [],
  })
}
