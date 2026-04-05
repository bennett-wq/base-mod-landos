import { useState } from 'react'
import { Search } from 'lucide-react'
import { useTargets, useRadarStats } from '@/hooks/useClusters'
import { Skeleton } from '@/components/shared/Skeleton'

type SignalFilter = 'All' | 'Highest' | 'High' | 'Med' | 'Low'

const SIGNAL_FILTERS: SignalFilter[] = ['All', 'Highest', 'High', 'Med', 'Low']

const SIGNAL_BADGE: Record<string, string> = {
  HIGHEST: 'bg-primary/10 text-primary',
  HIGH:    'bg-primary/50 text-white',
  MED:     'bg-[#efeeeb] text-[#827567]',
  LOW:     'bg-[#e4e2df] text-[#827567]',
}

export function IntelSidebar() {
  const [activeFilter, setActiveFilter] = useState<SignalFilter>('All')
  const [search, setSearch] = useState('')
  const { data: targets, isLoading: targetsLoading } = useTargets()
  const { data: stats, isLoading: statsLoading } = useRadarStats()

  const filtered = (targets ?? []).filter((t) => {
    if (activeFilter !== 'All') {
      const mapped = activeFilter.toUpperCase() === 'MED' ? 'MED' : activeFilter.toUpperCase()
      if (t.signal !== mapped) return false
    }
    if (search && !t.owner.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <aside className="flex h-full w-[380px] shrink-0 flex-col bg-white">
      <div className="flex-1 overflow-y-auto p-6">
        {/* Header */}
        <p className="mb-6 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Radar Intelligence
        </p>

        {/* Stats Grid */}
        <div className="mb-8 grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-surface-container-low bg-surface-container-low">
          {statsLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-white p-4">
                  <Skeleton width="60px" height="10px" className="mb-2" />
                  <Skeleton width="80px" height="24px" />
                </div>
              ))
            : stats?.map((s) => (
                <div key={s.label} className="bg-white p-4">
                  <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-[#827567]">
                    {s.label}
                  </p>
                  <p className={`text-2xl font-bold ${s.highlight ? 'text-primary' : 'text-on-surface'}`}>
                    {s.value}
                  </p>
                </div>
              ))}
        </div>

        {/* Filters */}
        <div className="mb-8 space-y-6">
          <h4 className="border-b border-surface-container-low pb-2 text-[11px] font-bold uppercase tracking-[0.15em] text-on-surface">
            Analysis Filters
          </h4>

          {/* Signal Intensity */}
          <div>
            <label className="mb-3 block text-[10px] font-bold uppercase text-[#827567]">
              Signal Intensity
            </label>
            <div className="flex gap-1 rounded-lg bg-surface-container-low p-1">
              {SIGNAL_FILTERS.map((f) => (
                <button
                  key={f}
                  onClick={() => setActiveFilter(f)}
                  className={`flex-1 rounded py-1.5 text-[10px] font-bold transition-colors ${
                    activeFilter === f
                      ? 'bg-white text-on-surface shadow-sm'
                      : 'text-[#827567] hover:bg-white/50'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* Owner Search */}
          <div>
            <label className="mb-2 block text-[10px] font-bold uppercase text-[#827567]">
              Owner Search
            </label>
            <div className="relative">
              <Search
                size={14}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[#827567]"
              />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Filter by entity..."
                className="w-full rounded-lg border-none bg-surface-container-low py-2.5 pl-9 pr-3 text-xs font-medium text-on-surface placeholder:text-[#d4c4b4] focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
          </div>
        </div>

        {/* Results Table */}
        <div>
          <h4 className="mb-4 flex justify-between border-b border-surface-container-low pb-2 text-[11px] font-bold uppercase tracking-[0.15em] text-on-surface">
            Targets <span>({filtered.length})</span>
          </h4>
          {targetsLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} height="32px" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <p className="text-xs text-on-surface-variant/50 text-center py-8">
              {(targets ?? []).length === 0
                ? 'No targets found. Run the pipeline to detect opportunities.'
                : 'No targets match current filters.'}
            </p>
          ) : (
            <table className="w-full border-separate border-spacing-y-1 text-left">
              <thead>
                <tr className="text-[9px] font-bold uppercase tracking-tighter text-[#827567]">
                  <th className="pb-1">Owner</th>
                  <th className="pb-1 text-center">Lots</th>
                  <th className="pb-1 text-center">Signal</th>
                  <th className="pb-1 text-center">Tier</th>
                  <th className="pb-1 text-right">Margin</th>
                </tr>
              </thead>
              <tbody className="text-xs">
                {filtered.map((t) => (
                  <tr key={t.owner} className="group cursor-pointer">
                    <td className="py-2.5 font-semibold text-on-surface transition-colors group-hover:text-primary">
                      {t.owner}
                    </td>
                    <td className="py-2.5 text-center text-on-surface-variant">{t.lots}</td>
                    <td className="py-2.5 text-center">
                      <span
                        className={`rounded px-1.5 py-0.5 text-[9px] font-bold ${SIGNAL_BADGE[t.signal]}`}
                      >
                        {t.signal}
                      </span>
                    </td>
                    <td className="py-2.5 text-center text-on-surface-variant">{t.tier}</td>
                    <td className="py-2.5 text-right font-bold text-primary">{t.margin}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </aside>
  )
}
