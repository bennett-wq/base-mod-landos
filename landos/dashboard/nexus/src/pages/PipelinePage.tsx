import { useState } from 'react'
import { Plus } from 'lucide-react'
import { KanbanBoard, useTotalDeals } from '../components/pipeline/KanbanBoard'

export default function PipelinePage() {
  const [showTooltip, setShowTooltip] = useState(false)
  const totalDeals = useTotalDeals()

  return (
    <>
      {/* Full-bleed breakout */}
      <div className="-m-8 min-h-[calc(100vh-56px)] bg-surface p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-on-surface">
              Pipeline — Deal Tracker
            </h2>
            <p className="text-on-surface-variant mt-1 text-sm">
              {totalDeals} active deals across all stages
            </p>
          </div>
          <button className="copper-gradient text-on-primary text-xs font-bold uppercase tracking-widest px-5 py-2.5 rounded-lg hover:opacity-90 transition-opacity">
            Add Lead
          </button>
        </div>

        {/* Kanban board */}
        <KanbanBoard />
      </div>

      {/* FAB — fixed bottom-right */}
      <button
        className="fixed bottom-8 right-8 z-20 w-14 h-14 copper-gradient text-white rounded-full shadow-lg flex items-center justify-center hover:scale-105 active:scale-95 transition-all group"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <Plus className="w-6 h-6" />
        {showTooltip && (
          <span className="absolute right-full mr-4 bg-inverse-surface text-white text-[9px] font-bold py-2 px-3 rounded-lg whitespace-nowrap uppercase tracking-widest">
            Add New Lead
          </span>
        )}
      </button>
    </>
  )
}
