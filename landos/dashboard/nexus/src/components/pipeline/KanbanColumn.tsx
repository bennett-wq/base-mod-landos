import { motion } from 'framer-motion'
import { DealCard } from './DealCard'
import { EmptyColumn } from './EmptyColumn'
import type { Deal } from './DealCard'

interface KanbanColumnProps {
  name: string
  deals: Deal[]
}

export function KanbanColumn({ name, deals }: KanbanColumnProps) {
  const isEmpty = deals.length === 0
  const isClosedEmpty = name === 'CLOSED' && isEmpty

  return (
    <div className="flex-shrink-0 w-[280px] flex flex-col gap-4 snap-start">
      {/* Column header */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-[11px] font-bold tracking-[0.1em] text-on-surface-variant uppercase">
          {name}
        </h3>
        <span
          className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-extrabold ${
            isEmpty
              ? 'bg-stone-100 text-stone-400'
              : 'bg-primary/10 text-primary'
          }`}
        >
          {deals.length}
        </span>
      </div>

      {/* Cards or empty state */}
      {isClosedEmpty ? (
        <EmptyColumn />
      ) : (
        deals.map((deal, i) => (
          <motion.div
            key={deal.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, duration: 0.3 }}
          >
            <DealCard deal={deal} stage={name} />
          </motion.div>
        ))
      )}
    </div>
  )
}
