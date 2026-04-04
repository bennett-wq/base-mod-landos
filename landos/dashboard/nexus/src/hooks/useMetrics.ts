import { useQuery } from '@tanstack/react-query'
import { fetchStats } from '@/lib/api'
import { METRICS, type Metric } from '@/data/mockData'

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: async () => {
      const stats = await fetchStats()
      if (stats.active_listings > 0 || stats.clusters > 0) {
        const metrics: Metric[] = [
          { label: 'Active Listings', value: stats.active_listings.toLocaleString() },
          { label: 'Vacant Parcels', value: stats.vacant_parcels.toLocaleString() },
          { label: 'Clusters', value: stats.clusters.toLocaleString() },
          { label: 'With Listings', value: stats.clusters_with_listings.toLocaleString(), highlight: true },
          { label: 'Opportunities', value: stats.opportunities.toLocaleString() },
        ]
        return metrics
      }
      return METRICS
    },
    staleTime: 30_000,
  })
}
