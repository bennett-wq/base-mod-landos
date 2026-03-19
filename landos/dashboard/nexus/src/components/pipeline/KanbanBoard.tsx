import { KanbanColumn } from './KanbanColumn'
import { usePipeline } from '@/hooks/usePipeline'
import { Skeleton } from '@/components/shared/Skeleton'

export function KanbanBoard() {
  const { data: stages, isLoading } = usePipeline()

  if (isLoading) {
    return (
      <div className="flex gap-6 -mx-8 px-8">
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton key={i} width="280px" height="400px" className="shrink-0 rounded-xl" />
        ))}
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
