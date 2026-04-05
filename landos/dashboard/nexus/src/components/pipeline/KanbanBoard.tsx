import { KanbanColumn } from './KanbanColumn'
import { usePipeline } from '@/hooks/usePipeline'
import { Skeleton } from '@/components/shared/Skeleton'

export function KanbanBoard() {
  const { data: stages, isLoading, isError } = usePipeline()

  if (isLoading) {
    return (
      <div className="flex gap-6 -mx-8 px-8">
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton key={i} width="280px" height="400px" className="shrink-0 rounded-xl" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center py-20 text-on-surface-variant">
        <p className="text-sm">Failed to load pipeline data. Is the API running?</p>
      </div>
    )
  }

  const totalDeals = stages?.reduce((sum, s) => sum + s.deals.length, 0) ?? 0
  if (totalDeals === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-on-surface-variant">
        <p className="text-sm font-medium">No opportunities in the pipeline yet.</p>
        <p className="mt-1 text-xs">Run the pipeline to populate strategic opportunities.</p>
      </div>
    )
  }

  return (
    <div className="kanban-scroll flex gap-6 overflow-x-auto pb-8 -mx-8 px-8 snap-x snap-mandatory">
      {stages?.map((stage) => (
        <KanbanColumn key={stage.name} name={stage.name} deals={stage.deals} />
      ))}
    </div>
  )
}

export function useTotalDeals() {
  const { data: stages } = usePipeline()
  return stages?.reduce((sum, s) => sum + s.deals.length, 0) ?? 0
}
