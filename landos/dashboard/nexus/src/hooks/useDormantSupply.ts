import { useQuery } from '@tanstack/react-query'
import { fetchClusters } from '@/lib/api'
import type { DormantOwner } from '@/data/mockData'

export function useDormantOwners() {
  return useQuery({
    queryKey: ['dormant-owners'],
    queryFn: async (): Promise<DormantOwner[]> => {
      // Large owner clusters (10+ lots) with no active listings = dormant supply
      const res = await fetchClusters({ min_lots: 10 })
      return res.clusters
        .filter((c) => !c._has_active_listings)
        .slice(0, 15)
        .map((c) => ({
          name: c._group_key || c.cluster_id.slice(0, 12),
          lots: c._parcel_count,
        }))
    },
    staleTime: 30_000,
  })
}
