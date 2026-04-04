import { ChevronDown } from 'lucide-react'

const SEGMENTS = [
  { label: 'Factory', value: '$128.4k', pct: 42, color: 'bg-[#B07D3B]' },
  { label: 'Site Work', value: '$45.2k', pct: 15, color: 'bg-[#C4954F]' },
  { label: 'Infrastructure', value: '$36.1k', pct: 12, color: 'bg-[#D4AD6A]' },
  { label: 'Soft Costs', value: '$28.0k', pct: 9, color: 'bg-[#9CA3AF]' },
]

const DOT_COLORS = ['bg-[#B07D3B]', 'bg-[#C4954F]', 'bg-[#D4AD6A]', 'bg-[#9CA3AF]']

export function CostWaterfallChart() {
  return (
    <div className="col-span-12 lg:col-span-8 rounded-xl bg-white p-8 shadow-ambient">
      {/* Header */}
      <div className="mb-10 flex items-center justify-between">
        <h3 className="text-[11px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
          Cost Waterfall
        </h3>
        <div className="flex cursor-pointer items-center gap-2 rounded-lg border border-outline-variant/10 bg-surface-container-low px-3 py-1.5 text-xs font-semibold text-on-surface">
          Aspen XMOD &rarr; Ypsilanti
          <ChevronDown className="h-3.5 w-3.5" />
        </div>
      </div>

      <div className="space-y-6">
        {/* Allocation header */}
        <div className="flex flex-col gap-2">
          <div className="flex justify-between text-[11px] font-bold uppercase tracking-tight text-on-surface-variant/60">
            <span>Component Allocation</span>
            <span>Value per unit</span>
          </div>

          {/* Stacked bar */}
          <div className="flex h-12 w-full overflow-hidden rounded-lg ring-1 ring-outline-variant/5">
            {SEGMENTS.map((s) => (
              <div
                key={s.label}
                className={`h-full ${s.color}`}
                style={{ width: `${s.pct}%` }}
                title={s.label}
              />
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 gap-y-4 border-t border-surface-container pt-4 md:grid-cols-4">
          {SEGMENTS.map((s, i) => (
            <div key={s.label} className="flex items-center gap-2">
              <div className={`h-2 w-2 rounded-full ${DOT_COLORS[i]}`} />
              <span className="text-xs font-medium">
                {s.label}: {s.value}
              </span>
            </div>
          ))}
        </div>

        {/* Summary stats */}
        <div className="mt-8 flex items-center justify-between border-t border-surface-container pt-8">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
              Total Project Cost
            </p>
            <h4 className="mt-1 text-3xl font-bold text-primary">
              $312,480{' '}
              <span className="text-sm font-medium text-on-surface-variant/40">/ Unit</span>
            </h4>
          </div>
          <div className="flex gap-12 text-right">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
                Profit / Unit
              </p>
              <h4 className="mt-1 text-2xl font-bold text-primary">$103.8k</h4>
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
                Margin
              </p>
              <h4 className="mt-1 text-2xl font-bold text-primary">33.2%</h4>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
