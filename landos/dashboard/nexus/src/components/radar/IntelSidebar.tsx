import { useState } from 'react'
import { Search } from 'lucide-react'

type Signal = 'All' | 'Highest' | 'High' | 'Med' | 'Low'

interface TargetRow {
  owner: string
  lots: number
  signal: 'HIGHEST' | 'HIGH' | 'MED' | 'LOW'
  tier: string
  margin: string
}

const STATS = [
  { label: 'Clusters',    value: '2,229', highlight: false },
  { label: 'Total Lots',  value: '10,266', highlight: false },
  { label: 'High Signal', value: '847',   highlight: true },
  { label: 'Tier 1 Opps', value: '23',    highlight: false },
]

const SIGNAL_FILTERS: Signal[] = ['All', 'Highest', 'High', 'Med', 'Low']

const TARGETS: TargetRow[] = [
  { owner: 'Toll Brothers',        lots: 146, signal: 'HIGHEST', tier: 'A', margin: '33.0%' },
  { owner: 'M/I Homes LLC',        lots: 99,  signal: 'HIGHEST', tier: 'A', margin: '38.7%' },
  { owner: 'Horseshoe Lake Corp',  lots: 88,  signal: 'HIGHEST', tier: 'A', margin: '29.4%' },
  { owner: 'PulteGroup',           lots: 82,  signal: 'HIGH',    tier: 'B', margin: '24.2%' },
  { owner: 'Lennar Corp',          lots: 112, signal: 'MED',     tier: 'A', margin: '18.5%' },
  { owner: 'Julian Francis Trust', lots: 12,  signal: 'HIGHEST', tier: 'A', margin: '41.2%' },
  { owner: 'NVR Inc',              lots: 64,  signal: 'HIGH',    tier: 'B', margin: '22.8%' },
  { owner: 'Meritage Homes',       lots: 47,  signal: 'MED',     tier: 'B', margin: '19.1%' },
  { owner: 'Taylor Morrison',      lots: 38,  signal: 'LOW',     tier: 'C', margin: '15.3%' },
  { owner: 'Century Complete',     lots: 29,  signal: 'LOW',     tier: 'C', margin: '12.7%' },
]

const SIGNAL_BADGE: Record<string, string> = {
  HIGHEST: 'bg-primary/10 text-primary',
  HIGH:    'bg-primary/50 text-white',
  MED:     'bg-[#efeeeb] text-[#827567]',
  LOW:     'bg-[#e4e2df] text-[#827567]',
}

export function IntelSidebar() {
  const [activeFilter, setActiveFilter] = useState<Signal>('All')
  const [search, setSearch] = useState('')

  const filtered = TARGETS.filter((t) => {
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
          {STATS.map((s) => (
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
        </div>
      </div>
    </aside>
  )
}
