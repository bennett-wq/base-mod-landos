interface Row {
  acquisition: string
  profit: string
  margin: string
  tier: string
  tierStyle: string
  impact: string
  isTarget?: boolean
}

const ROWS: Row[] = [
  {
    acquisition: '$239k',
    profit: '$154k',
    margin: '37.5%',
    tier: 'A+',
    tierStyle: 'bg-primary text-white',
    impact: '+$1.19M',
    isTarget: true,
  },
  {
    acquisition: '$264k',
    profit: '$129k',
    margin: '31.2%',
    tier: 'A',
    tierStyle: 'bg-primary text-white',
    impact: '+$942k',
  },
  {
    acquisition: '$294k',
    profit: '$99k',
    margin: '24.8%',
    tier: 'B',
    tierStyle: 'bg-stone-300 text-on-surface',
    impact: '+$611k',
  },
  {
    acquisition: '$319k',
    profit: '$64k',
    margin: '16.5%',
    tier: 'C',
    tierStyle: 'bg-stone-200 text-on-surface-variant',
    impact: '+$394k',
  },
]

export function DealSensitivity() {
  return (
    <div className="col-span-12 lg:col-span-7 rounded-xl bg-white p-8 shadow-[0_12px_32px_rgba(27,28,26,0.04)]">
      <div className="mb-6">
        <h3 className="text-[11px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
          Deal Sensitivity
        </h3>
        <p className="mt-1 text-xs text-on-surface-variant/60">
          Acquisition price impact on project viability
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-surface-container">
              <th className="pb-3 text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/50">
                Acquisition
              </th>
              <th className="pb-3 text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/50">
                Profit
              </th>
              <th className="pb-3 text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/50">
                Margin
              </th>
              <th className="pb-3 text-center text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/50">
                Tier
              </th>
              <th className="pb-3 text-right text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/50">
                Portfolio Impact
              </th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {ROWS.map((row) => (
              <tr
                key={row.acquisition}
                className={
                  row.isTarget
                    ? 'border-l-4 border-l-primary bg-primary/5'
                    : 'border-b border-surface-container/40'
                }
              >
                <td className="py-4 font-semibold text-on-surface">
                  {row.acquisition}
                  {row.isTarget && (
                    <span className="ml-1.5 text-[10px] text-primary">(Target)</span>
                  )}
                </td>
                <td className="py-4 font-mono">{row.profit}</td>
                <td
                  className={`py-4 font-bold ${
                    row.tier === 'A+' || row.tier === 'A'
                      ? 'text-primary'
                      : 'text-on-surface-variant'
                  }`}
                >
                  {row.margin}
                </td>
                <td className="py-4 text-center">
                  <span
                    className={`inline-block rounded px-2 py-0.5 text-[10px] font-bold ${row.tierStyle}`}
                  >
                    {row.tier}
                  </span>
                </td>
                <td className="py-4 text-right font-medium">{row.impact}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
