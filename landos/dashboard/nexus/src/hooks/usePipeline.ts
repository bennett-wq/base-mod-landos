import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchStrategic, type ApiStrategicOpp } from '@/lib/api'
import { PIPELINE_STAGES as MOCK_STAGES, type PipelineStage, type PipelineDeal } from '@/data/mockData'
import { usePipelineStore, PIPELINE_STAGES, type PipelineStageName } from '@/stores/pipelineStore'

/** Convert a strategic opportunity into a PipelineDeal with evidence fields. */
function strategicToDeal(opp: ApiStrategicOpp): PipelineDeal {
  return {
    id: opp.opportunity_id,
    title: opp.name || opp.owner_name || 'Unknown',
    tier: opp.composite_score >= 0.4 ? 1 : undefined,
    entityType: opp.opportunity_type === 'owner_cluster' ? 'OWNER'
      : opp.opportunity_type === 'stalled_subdivision' ? 'SUBDIVISION'
      : 'CLUSTER',
    location: 'Washtenaw Co',
    lotCount: opp.lot_count,
    score: Math.round(opp.composite_score * 100),
    signal: opp.has_active_listings ? 'HIGHEST' : (opp.lot_count >= 10 ? 'HIGH' : undefined),
    updatedAgo: 'From pipeline',
    // Evidence fields
    stallSignals: opp.stall_signals ?? [],
    stallConfidence: opp.stall_confidence,
    infrastructureInvested: opp.infrastructure_invested,
    vacancyRatio: opp.vacancy_ratio,
    listingCount: opp.listing_count,
    listingAgents: opp.listing_agents,
    acreage: opp.total_acreage,
  }
}

/** Build pipeline stages from API data + local stage assignments. */
function buildStages(
  deals: PipelineDeal[],
  dealStages: Record<string, PipelineStageName>
): PipelineStage[] {
  const stageMap: Record<PipelineStageName, PipelineDeal[]> = {
    'DISCOVERED': [],
    'RESEARCHED': [],
    'OUTREACH DRAFTED': [],
    'CONTACTED': [],
    'NEGOTIATING': [],
    'UNDER CONTRACT': [],
    'CLOSED': [],
  }

  for (const deal of deals) {
    const stage = dealStages[deal.id] ?? 'DISCOVERED'
    stageMap[stage].push(deal)
  }

  return PIPELINE_STAGES.map((name) => ({
    name,
    deals: stageMap[name],
  }))
}

export function usePipeline() {
  const dealStages = usePipelineStore((s) => s.dealStages)

  return useQuery({
    queryKey: ['pipeline', dealStages],
    queryFn: async () => {
      const res = await fetchStrategic({ min_lots: 3 })
      if (res.opportunities.length > 0) {
        const deals = res.opportunities.slice(0, 30).map(strategicToDeal)
        return buildStages(deals, dealStages)
      }
      return MOCK_STAGES
    },
    staleTime: 30_000,
  })
}

export function usePipelineMutation() {
  const queryClient = useQueryClient()
  const moveDeal = usePipelineStore((s) => s.moveDeal)

  return useMutation({
    mutationFn: async ({ dealId, newStage }: { dealId: string; newStage: PipelineStageName }) => {
      moveDeal(dealId, newStage)
      return { dealId, newStage }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline'] })
    },
  })
}
