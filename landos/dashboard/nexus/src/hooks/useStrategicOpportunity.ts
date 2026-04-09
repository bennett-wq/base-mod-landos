import { useQuery } from '@tanstack/react-query'
import { fetchStrategicById, type ApiStrategicOpp, type ApiParcel } from '@/lib/api'

export function useStrategicOpportunity(id: string | undefined) {
  return useQuery({
    queryKey: ['strategic', id],
    queryFn: () => fetchStrategicById(id!),
    enabled: !!id,
    staleTime: 60_000,
    select: (data) => data ?? undefined,
  })
}

export type { ApiStrategicOpp, ApiParcel }
