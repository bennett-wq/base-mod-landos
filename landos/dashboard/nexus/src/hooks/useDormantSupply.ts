import { useQuery } from '@tanstack/react-query'
import { fetchClusters } from '@/lib/api'
import { DORMANT_OWNERS, type DormantOwner } from '@/data/mockData'

export function useDormantOwners() {
  return useQuery({
    queryKey: ['dormant-owners'],
    queryFn: async () => {
      // Fetch large owner clusters (10+ lots) that don't have active listings
      const res = await fetchClusters({ min_lots: 10 })
      if (res.clusters.length > 0) {
        const dormant: DormantOwner[] = res.clusters
          .filter((c) => !c._has_active_listings)
          .slice(0, 15)
          .map((c) => ({
            name: c._group_key || c.cluster_id.slice(0, 12),
            lots: c._parcel_count,
          }))
        if (dormant.length > 0) return dormant
      }
      return DORMANT_OWNERS
    },
    staleTime: 30_000,
  })
}
