import { useQuery } from '@tanstack/react-query'
import { fetchClusters, fetchStats, fetchStrategic, type ApiCluster, type ApiStrategicOpp } from '@/lib/api'
import {
  CLUSTERS,
  CLUSTER_SUMMARIES,
  TARGETS,
  RADAR_STATS,
  type Cluster,
  type ClusterSummary,
  type TargetRow,
  type RadarStat,
} from '@/data/mockData'

/**
 * Map an API strategic opportunity to the Cluster shape components expect.
 * Uses REAL scores from the strategic ranker, not random numbers.
 */
function strategicToCluster(opp: ApiStrategicOpp, index: number): Cluster {
  const signal = opp.has_active_listings && opp.lot_count >= 10 ? 'HIGHEST' as const
    : opp.has_active_listings ? 'HIGH' as const
    : opp.lot_count >= 20 ? 'MEDIUM' as const
    : 'LOW' as const

  const tier = opp.composite_score >= 0.4 ? 'A' as const
    : opp.composite_score >= 0.2 ? 'B' as const
    : 'C' as const

  // Use real centroid from pipeline, fall back to spread across Washtenaw
  const position: [number, number] = opp.centroid_lat && opp.centroid_lon
    ? [opp.centroid_lat, opp.centroid_lon]
    : [42.25 + (index * 0.015), -83.75 - (index * 0.02)]

  // Scores derived from REAL pipeline data, not random
  const breakdown = opp.score_breakdown || {}
  const infraScore = Math.round((breakdown.infrastructure ?? 0) * 100)
  const vacancyScore = Math.round((breakdown.vacancy_ratio ?? opp.vacancy_ratio) * 100)
  const listingScore = Math.round((breakdown.listing_activity ?? 0) * 100)

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
    // Real dimension scores from the pipeline
    zoning: Math.max(10, vacancyScore),
    infrastructure: Math.max(10, infraScore),
    economicFit: Math.max(10, listingScore + Math.round((breakdown.lot_count ?? 0) * 50)),
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

export function useClusters() {
  return useQuery({
    queryKey: ['clusters'],
    queryFn: async () => {
      // Use the strategic ranker — it has composite scores and real breakdowns
      const res = await fetchStrategic({ min_lots: 3 })
      if (res.opportunities.length > 0) {
        return res.opportunities.slice(0, 20).map(strategicToCluster)
      }
      return CLUSTERS
    },
    staleTime: 30_000,
  })
}

export function useClusterSummaries() {
  return useQuery({
    queryKey: ['clusters', 'summaries'],
    queryFn: async () => {
      const res = await fetchClusters({ has_listings: true })
      if (res.clusters.length > 0) {
        return res.clusters.slice(0, 10).map(clusterToSummary)
      }
      return CLUSTER_SUMMARIES
    },
    staleTime: 30_000,
  })
}

export function useTargets() {
  return useQuery({
    queryKey: ['targets'],
    queryFn: async () => {
      const res = await fetchStrategic({ min_lots: 5 })
      if (res.opportunities.length > 0) {
        const targets: TargetRow[] = res.opportunities.slice(0, 15).map((opp) => ({
          owner: opp.owner_name || opp.name || 'Unknown',
          lots: opp.lot_count,
          signal: opp.has_active_listings && opp.lot_count >= 10 ? 'HIGHEST' as const
            : opp.has_active_listings ? 'HIGH' as const
            : opp.lot_count >= 20 ? 'MED' as const
            : 'LOW' as const,
          tier: opp.composite_score >= 0.4 ? 'A' : opp.composite_score >= 0.2 ? 'B' : 'C',
          margin: '—',
        }))
        return targets
      }
      return TARGETS
    },
    staleTime: 30_000,
  })
}

export function useRadarStats() {
  return useQuery({
    queryKey: ['radar', 'stats'],
    queryFn: async () => {
      const stats = await fetchStats()
      if (stats.clusters > 0) {
        const radarStats: RadarStat[] = [
          { label: 'Clusters', value: stats.clusters.toLocaleString(), highlight: false },
          { label: 'Vacant Parcels', value: stats.vacant_parcels.toLocaleString(), highlight: false },
          { label: 'With Listings', value: stats.clusters_with_listings.toLocaleString(), highlight: true },
          { label: 'Opportunities', value: stats.opportunities.toLocaleString(), highlight: false },
        ]
        return radarStats
      }
      return RADAR_STATS
    },
    staleTime: 30_000,
  })
}
