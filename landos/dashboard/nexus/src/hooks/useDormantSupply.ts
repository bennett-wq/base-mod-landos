import { useQuery } from '@tanstack/react-query'
import { DORMANT_OWNERS } from '@/data/mockData'

export function useDormantOwners() {
  return useQuery({
    queryKey: ['dormant-owners'],
    queryFn: async () => DORMANT_OWNERS,
    staleTime: 30_000,
  })
}
