import { useQuery } from '@tanstack/react-query'
import { fetchClusters, fetchStats, fetchStrategic, type ApiCluster, type ApiStrategicOpp } from '@/lib/api'
import type { Cluster, ClusterSummary, TargetRow, RadarStat } from '@/data/mockData'

// ── Signal classification ───────────────────────────────────────────────────
// Signal MUST respect backend truth:
//   precedence_tier 1 with ANY historical evidence → HIGHEST (even 0 active listings)
//   precedence_tier 1 without historical evidence → HIGH
//   precedence_tier 2-3 with active listings → HIGH
//   everything else → MEDIUM or LOW by score

function classifySignal(opp: ApiStrategicOpp): 'HIGHEST' | 'HIGH' | 'MEDIUM' | 'LOW' {
  const hasHistoricalEvidence =
    opp.owner_linked_failed_exit_count > 0 ||
    opp.has_relist_cycle ||
    opp.partial_release_detected ||
    opp.expired_listing_count > 0 ||
    opp.distress_language_detected ||
    opp.fatigue_language_detected

  // Tier 1 owner-controlled clusters with historical exits = top priority
  if (opp.precedence_tier === 1 && hasHistoricalEvidence) return 'HIGHEST'
  if (opp.precedence_tier === 1) return 'HIGH'
  if (opp.has_active_listings && opp.composite_score >= 0.3) return 'HIGH'
  if (opp.composite_score >= 0.2) return 'MEDIUM'
  return 'LOW'
}

function classifyTier(opp: ApiStrategicOpp): 'A' | 'B' | 'C' {
  // Tier A = precedence_tier 1 OR high composite score
  if (opp.precedence_tier === 1) return 'A'
  if (opp.composite_score >= 0.4) return 'A'
  if (opp.composite_score >= 0.2) return 'B'
  return 'C'
}

// ── Transformers ────────────────────────────────────────────────────────────

function strategicToCluster(opp: ApiStrategicOpp, index: number): Cluster {
  const signal = classifySignal(opp)
  const tier = classifyTier(opp)

  // Real centroid from pipeline, fall back to spread across Washtenaw
  const position: [number, number] = opp.centroid_lat && opp.centroid_lon
    ? [opp.centroid_lat, opp.centroid_lon]
    : [42.25 + (index * 0.015), -83.75 - (index * 0.02)]

  // Scores from REAL pipeline breakdown
  const breakdown = opp.score_breakdown || {}
  const infraScore = Math.round((breakdown.infrastructure ?? 0) * 100)
  const vacancyScore = Math.round((breakdown.vacancy_ratio ?? opp.vacancy_ratio) * 100)
  const sellerIntentScore = Math.round((breakdown.seller_intent ?? 0) * 100)

  return {
    id: opp.opportunity_id,
    owner: opp.owner_name || opp.name || opp.subdivision_name || `Cluster ${index + 1}`,
    township: 'Washtenaw Co',
    position,
    signal,
    lots: opp.lot_count,
    acreage: opp.total_acreage,
    avgLandValue: '—',
    supplyType: opp.opportunity_type === 'stalled_subdivision' ? 'STALLED'
      : opp.has_active_listings ? 'ACTIVE'
      : opp.lot_count >= 20 ? 'DORMANT'
      : 'TIGHT',
    score: Math.round(opp.composite_score * 100),
    tier,
    // Dimension scores from pipeline breakdown
    zoning: Math.max(10, vacancyScore),
    infrastructure: Math.max(10, infraScore),
    economicFit: Math.max(10, sellerIntentScore),
    // Evidence fields — passed through from the strategic ranker
    stallSignals: opp.stall_signals ?? [],
    stallConfidence: opp.stall_confidence,
    infrastructureInvested: opp.infrastructure_invested,
    vacancyRatio: opp.vacancy_ratio,
    listingCount: opp.listing_count,
    listingAgents: opp.listing_agents,
    bboSignalCount: opp.bbo_signal_count,
    opportunityType: opp.opportunity_type,
    parcelCount: opp.lot_count,
    subdivisionName: opp.subdivision_name,
    // Owner-link evidence
    precedenceTier: opp.precedence_tier,
    historicalListingCount: opp.historical_listing_count,
    expiredListingCount: opp.expired_listing_count,
    withdrawnListingCount: opp.withdrawn_listing_count,
    ownerLinkedFailedExitCount: opp.owner_linked_failed_exit_count,
    hasRelistCycle: opp.has_relist_cycle,
    partialReleaseDetected: opp.partial_release_detected,
    packageLanguageDetected: opp.package_language_detected,
    fatigueLanguageDetected: opp.fatigue_language_detected,
    distressLanguageDetected: opp.distress_language_detected,
    maxCdom: opp.max_cdom,
    avgCdom: opp.avg_cdom,
    ownerLinkedHistoricalCount: opp.owner_linked_historical_count,
    ownerLinkConfidence: opp.owner_link_confidence,
    scoreBreakdown: opp.score_breakdown,
  }
}

function clusterToSummary(c: ApiCluster): ClusterSummary {
  return {
    name: c._group_key || c.cluster_id.slice(0, 12),
    lots: c._parcel_count,
    type: c.cluster_type === 'SAME_OWNER' ? 'Owner Cluster' : c.cluster_type,
    location: 'Washtenaw Co',
  }
}

// ── Hooks ───────────────────────────────────────────────────────────────────

export function useClusters() {
  return useQuery({
    queryKey: ['clusters'],
    queryFn: async (): Promise<Cluster[]> => {
      const res = await fetchStrategic({ min_lots: 3 })
      // Return real data — backend already sorts by precedence_tier ASC, composite_score DESC
      return res.opportunities.slice(0, 30).map(strategicToCluster)
    },
    staleTime: 30_000,
  })
}

export function useClusterSummaries() {
  return useQuery({
    queryKey: ['clusters', 'summaries'],
    queryFn: async (): Promise<ClusterSummary[]> => {
      const res = await fetchClusters({ has_listings: true })
      return res.clusters.slice(0, 10).map(clusterToSummary)
    },
    staleTime: 30_000,
  })
}

export function useTargets() {
  return useQuery({
    queryKey: ['targets'],
    queryFn: async (): Promise<TargetRow[]> => {
      const res = await fetchStrategic({ min_lots: 5 })
      return res.opportunities.slice(0, 15).map((opp) => ({
        owner: opp.owner_name || opp.name || 'Unknown',
        lots: opp.lot_count,
        signal: classifySignal(opp) === 'MEDIUM' ? 'MED' as const : classifySignal(opp) === 'LOW' ? 'LOW' as const : classifySignal(opp) === 'HIGHEST' ? 'HIGHEST' as const : 'HIGH' as const,
        tier: classifyTier(opp),
        margin: '—',
      }))
    },
    staleTime: 30_000,
  })
}

export function useRadarStats() {
  return useQuery({
    queryKey: ['radar', 'stats'],
    queryFn: async (): Promise<RadarStat[]> => {
      const stats = await fetchStats()
      return [
        { label: 'Clusters', value: stats.clusters.toLocaleString(), highlight: false },
        { label: 'Vacant Parcels', value: stats.vacant_parcels.toLocaleString(), highlight: false },
        { label: 'With Listings', value: stats.clusters_with_listings.toLocaleString(), highlight: true },
        { label: 'Opportunities', value: stats.opportunities.toLocaleString(), highlight: false },
      ]
    },
    staleTime: 30_000,
  })
}
