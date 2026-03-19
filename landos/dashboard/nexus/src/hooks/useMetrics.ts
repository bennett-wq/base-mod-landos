import { useQuery } from '@tanstack/react-query'
import { METRICS } from '@/data/mockData'

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: async () => METRICS,
    staleTime: 30_000,
  })
}
