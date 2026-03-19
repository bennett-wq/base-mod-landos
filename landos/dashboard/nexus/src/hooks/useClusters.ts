import { useQuery } from '@tanstack/react-query'
import { CLUSTERS, CLUSTER_SUMMARIES, TARGETS, RADAR_STATS } from '@/data/mockData'

export function useClusters() {
  return useQuery({
    queryKey: ['clusters'],
    queryFn: async () => CLUSTERS,
    staleTime: 30_000,
  })
}

export function useClusterSummaries() {
  return useQuery({
    queryKey: ['clusters', 'summaries'],
    queryFn: async () => CLUSTER_SUMMARIES,
    staleTime: 30_000,
  })
}

export function useTargets() {
  return useQuery({
    queryKey: ['targets'],
    queryFn: async () => TARGETS,
    staleTime: 30_000,
  })
}

export function useRadarStats() {
  return useQuery({
    queryKey: ['radar', 'stats'],
    queryFn: async () => RADAR_STATS,
    staleTime: 30_000,
  })
}
