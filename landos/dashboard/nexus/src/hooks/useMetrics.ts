import { useQuery } from '@tanstack/react-query'
import { fetchStats } from '@/lib/api'
import type { Metric } from '@/data/mockData'

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: async (): Promise<Metric[]> => {
      const stats = await fetchStats()
      return [
        { label: 'Active Listings', value: stats.active_listings.toLocaleString() },
        { label: 'Vacant Parcels', value: stats.vacant_parcels.toLocaleString() },
        { label: 'Clusters', value: stats.clusters.toLocaleString() },
        { label: 'With Listings', value: stats.clusters_with_listings.toLocaleString(), highlight: true },
        { label: 'Opportunities', value: stats.opportunities.toLocaleString() },
      ]
    },
    staleTime: 30_000,
  })
}
