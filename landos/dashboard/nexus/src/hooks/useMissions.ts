import { useQuery } from '@tanstack/react-query'
import { MISSIONS } from '@/data/mockData'

export function useMissions() {
  return useQuery({
    queryKey: ['missions'],
    queryFn: async () => MISSIONS,
    staleTime: 30_000,
  })
}
