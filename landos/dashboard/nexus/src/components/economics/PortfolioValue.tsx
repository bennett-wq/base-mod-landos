const LINE_ITEMS = [
  { label: 'Opportunities', value: '23 Tier 1 clusters' },
  { label: 'Total Revenue', value: '$64.2M' },
  { label: 'Target IRR', value: '28.4%' },
]

export function PortfolioValue() {
  return (
    <div className="col-span-12 lg:col-span-4 flex flex-col justify-between rounded-xl border border-primary/10 bg-primary/5 p-8">
      <div>
        <h3 className="text-[11px] font-bold uppercase tracking-[0.15em] text-primary">
          Tier 1 Portfolio Value
        </h3>
        <p className="mt-1 text-xs text-primary/60">Aggregate projections for Washtenaw</p>
        <div className="mt-10">
          <span className="text-4xl font-bold tracking-tight text-primary">$18.3M</span>
          <p className="mt-2 text-sm font-semibold text-on-surface">Projected Net Profit</p>
        </div>
      </div>

      <div className="mt-8 space-y-0">
        {LINE_ITEMS.map((item, i) => (
          <div
            key={item.label}
            className={`flex items-center justify-between py-3 ${
              i < LINE_ITEMS.length - 1 ? 'border-b border-primary/10' : ''
            }`}
          >
            <span className="text-xs font-medium text-on-surface-variant">{item.label}</span>
            <span className="text-xs font-bold text-on-surface">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
