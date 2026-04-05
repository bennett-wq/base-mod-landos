import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchStrategic, type ApiStrategicOpp } from '@/lib/api'
import type { PipelineStage, PipelineDeal } from '@/data/mockData'
import { usePipelineStore, PIPELINE_STAGES, type PipelineStageName } from '@/stores/pipelineStore'

/**
 * Convert a strategic opportunity into a PipelineDeal.
 *
 * Signal classification respects precedence_tier from the backend:
 * - Tier 1 owner cluster with historical failed exits = HIGHEST
 *   (even if 0 active listings — this is the key product insight)
 * - Active listings alone are not enough for HIGHEST
 */
function strategicToDeal(opp: ApiStrategicOpp): PipelineDeal {
  const hasHistoricalEvidence =
    opp.owner_linked_failed_exit_count > 0 ||
    opp.has_relist_cycle ||
    opp.partial_release_detected ||
    opp.expired_listing_count > 0 ||
    opp.distress_language_detected ||
    opp.fatigue_language_detected

  const signal = opp.precedence_tier === 1 && hasHistoricalEvidence ? 'HIGHEST'
    : opp.precedence_tier === 1 ? 'HIGH'
    : opp.has_active_listings && opp.composite_score >= 0.3 ? 'HIGH'
    : undefined

  return {
    id: opp.opportunity_id,
    title: opp.name || opp.owner_name || 'Unknown',
    tier: opp.precedence_tier === 1 || opp.composite_score >= 0.4 ? 1 : undefined,
    entityType: opp.opportunity_type === 'owner_cluster' ? 'OWNER'
      : opp.opportunity_type === 'stalled_subdivision' ? 'SUBDIVISION'
      : 'CLUSTER',
    location: 'Washtenaw Co',
    lotCount: opp.lot_count,
    score: Math.round(opp.composite_score * 100),
    signal,
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
    queryFn: async (): Promise<PipelineStage[]> => {
      const res = await fetchStrategic({ min_lots: 3, limit: 50 })
      const deals = res.opportunities.map(strategicToDeal)
      return buildStages(deals, dealStages)
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
