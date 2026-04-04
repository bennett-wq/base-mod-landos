import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Pipeline stage progression store.
 *
 * Tracks which stage each deal is in. Persisted to localStorage
 * so operator work survives page refreshes.
 *
 * Deals start in DISCOVERED (from the strategic ranker API).
 * The operator moves them through stages as they work the queue.
 */

export const PIPELINE_STAGES = [
  'DISCOVERED',
  'RESEARCHED',
  'OUTREACH DRAFTED',
  'CONTACTED',
  'NEGOTIATING',
  'UNDER CONTRACT',
  'CLOSED',
] as const

export type PipelineStageName = typeof PIPELINE_STAGES[number]

interface PipelineState {
  /** Map of deal ID → stage name. Deals not in this map are in DISCOVERED. */
  dealStages: Record<string, PipelineStageName>
  /** Move a deal to a new stage */
  moveDeal: (dealId: string, toStage: PipelineStageName) => void
  /** Reset a deal back to DISCOVERED */
  resetDeal: (dealId: string) => void
  /** Get the stage for a deal (defaults to DISCOVERED) */
  getStage: (dealId: string) => PipelineStageName
}

export const usePipelineStore = create<PipelineState>()(
  persist(
    (set, get) => ({
      dealStages: {},

      moveDeal: (dealId, toStage) =>
        set((state) => ({
          dealStages: { ...state.dealStages, [dealId]: toStage },
        })),

      resetDeal: (dealId) =>
        set((state) => {
          const { [dealId]: _, ...rest } = state.dealStages
          return { dealStages: rest }
        }),

      getStage: (dealId) => get().dealStages[dealId] ?? 'DISCOVERED',
    }),
    { name: 'landos-pipeline-stages' }
  )
)
