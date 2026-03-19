import { useQuery } from '@tanstack/react-query'
import { AGENTS, AGENTS_EXPANDED } from '@/data/mockData'

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => AGENTS,
    staleTime: 30_000,
  })
}

export function useAgentsExpanded() {
  return useQuery({
    queryKey: ['agents', 'expanded'],
    queryFn: async () => AGENTS_EXPANDED,
    staleTime: 30_000,
  })
}
