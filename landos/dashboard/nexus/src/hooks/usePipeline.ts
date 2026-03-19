import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PIPELINE_STAGES } from '@/data/mockData'

export function usePipeline() {
  return useQuery({
    queryKey: ['pipeline'],
    queryFn: async () => PIPELINE_STAGES,
    staleTime: 30_000,
  })
}

export function usePipelineMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ dealId, newStage }: { dealId: string; newStage: string }) => {
      // Mock: just return success. Replace with API call later.
      return { dealId, newStage }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline'] })
    },
  })
}
