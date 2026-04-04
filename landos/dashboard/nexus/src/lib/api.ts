/**
 * LandOS API client — fetches real pipeline intelligence from the FastAPI backend.
 *
 * Falls back gracefully: if the API is unreachable, hooks return mock data
 * so the dashboard stays functional during development without the backend running.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function apiFetch<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`)
    if (!res.ok) throw new Error(`API ${res.status}`)
    return await res.json()
  } catch {
    console.warn(`[LandOS API] ${path} unavailable — using fallback data`)
    return fallback
  }
}

// ── Typed API calls ─────────────────────────────────────────────────────────

export interface ApiStats {
  active_listings: number
  total_parcels: number
  vacant_parcels: number
  clusters: number
  clusters_with_listings: number
  opportunities: number
  pipeline_run: Record<string, unknown>
}

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

export interface ApiStrategicResponse {
  count: number
  query: { min_lots: number | null; infrastructure_only: boolean | null }
  opportunities: ApiStrategicOpp[]
}

export interface ApiStrategicOpp {
  opportunity_id: string
  name: string
  opportunity_type: string
  municipality_id?: string
  lot_count: number
  total_acreage: number
  infrastructure_invested: boolean
  stall_confidence: number
  vacancy_ratio: number
  composite_score: number
  has_active_listings: boolean
  listing_count: number
  bbo_signal_count: number
  owner_name: string
  subdivision_name: string
  listing_keys: string[]
  listing_agents: string[]
  parcel_ids: string[]
  centroid_lat?: number
  centroid_lon?: number
  stall_signals: string[]
  score_breakdown: Record<string, number>
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

export function fetchSignals(limit = 50): Promise<ApiSignalResponse> {
  return apiFetch(`/api/signals?limit=${limit}`, { count: 0, signals: [] })
}

export function fetchStrategic(params?: {
  min_lots?: number
  infrastructure?: boolean
}): Promise<ApiStrategicResponse> {
  const searchParams = new URLSearchParams()
  if (params?.min_lots) searchParams.set('min_lots', String(params.min_lots))
  if (params?.infrastructure) searchParams.set('infrastructure', 'true')
  const qs = searchParams.toString()
  return apiFetch(`/api/strategic${qs ? `?${qs}` : ''}`, {
    count: 0,
    query: { min_lots: null, infrastructure_only: null },
    opportunities: [],
  })
}
