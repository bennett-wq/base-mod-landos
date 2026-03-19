const WF_DATA = [
  { label: 'Factory Cost', value: 89000, color: 'var(--color-nexus-cyan)' },
  { label: 'Site Work', value: 18000, color: 'var(--color-nexus-blue)' },
  { label: 'Infrastructure', value: 22000, color: 'var(--color-nexus-purple)' },
  { label: 'Soft Costs', value: 12000, color: 'var(--color-nexus-amber)' },
  { label: 'Contingency (5%)', value: 7050, color: 'var(--color-nexus-orange)' },
  { label: 'Land Cost', value: 35000, color: 'var(--color-brass)' },
  { label: 'Closing (9%)', value: 16470, color: 'var(--color-nexus-crimson)' },
];

const TOTAL = WF_DATA.reduce((s, r) => s + r.value, 0);
const RETAIL = 279000;
const PROFIT = RETAIL - TOTAL;
const MARGIN = (PROFIT / RETAIL * 100).toFixed(1);
const MAX_V = Math.max(...WF_DATA.map(r => r.value));

const SENSITIVITY = [239000, 259000, 279000, 299000, 319000].map(price => {
  const profit = price - TOTAL;
  const margin = (profit / price * 100).toFixed(1);
  const tier = margin >= 25 ? 'A' : margin >= 15 ? 'B' : margin > 0 ? 'C' : 'X';
  return { price, profit, margin, tier, positive: profit > 0, highlight: price === 279000 };
});

const TIER_BADGE = { A: 'bg-nexus-emerald/15 text-nexus-emerald', B: 'bg-nexus-cyan/15 text-nexus-cyan', C: 'bg-nexus-amber/15 text-nexus-amber', X: 'bg-nexus-crimson/15 text-nexus-crimson' };

export default function EconomicsTab() {
  return (
    <div className="grid grid-cols-2 h-full gap-px bg-white/4">
      {/* Left */}
      <div className="bg-void-1 overflow-y-auto p-5 space-y-6">
        {/* Waterfall */}
        <div>
          <h2 className="font-display font-bold text-[16px] text-[#e0e0e0] mb-3 pb-2 border-b border-white/5">Cost Waterfall — Modular Home</h2>
          <div className="space-y-1">
            {WF_DATA.map(r => (
              <div key={r.label} className="flex items-center gap-2 py-1.5">
                <div className="text-[11px] text-white/30 w-[140px]">{r.label}</div>
                <div className="flex-1 h-2 bg-void-3 rounded overflow-hidden">
                  <div className="h-full rounded transition-all duration-500" style={{ width: `${r.value / MAX_V * 100}%`, background: r.color }} />
                </div>
                <div className="text-[12px] font-semibold text-white/45 w-20 text-right tabular-nums">${r.value.toLocaleString()}</div>
              </div>
            ))}
            <div className="flex items-center gap-2 py-2.5 mt-1 border-t border-white/6">
              <div className="text-[11px] font-semibold text-brass w-[140px]">Total Project Cost</div>
              <div className="flex-1 h-2 bg-void-3 rounded overflow-hidden"><div className="h-full rounded bg-brass" style={{ width: '100%' }} /></div>
              <div className="text-[14px] font-semibold text-brass-bright w-20 text-right tabular-nums">${TOTAL.toLocaleString()}</div>
            </div>
            <div className="flex items-center gap-2 py-1">
              <div className="text-[11px] font-semibold text-white/30 w-[140px]">Profit / Unit</div>
              <div className="flex-1 h-2 bg-void-3 rounded overflow-hidden"><div className="h-full rounded bg-nexus-emerald" style={{ width: `${PROFIT / RETAIL * 100}%` }} /></div>
              <div className="text-[14px] font-bold text-nexus-emerald w-20 text-right tabular-nums">${PROFIT.toLocaleString()}</div>
            </div>
            <div className="flex items-center gap-2">
              <div className="text-[11px] text-white/30 w-[140px]">Margin</div>
              <div className="flex-1" />
              <div className="text-[14px] font-bold text-nexus-emerald w-20 text-right">{MARGIN}%</div>
            </div>
          </div>
        </div>

        {/* Sensitivity */}
        <div>
          <h2 className="font-display font-bold text-[16px] text-[#e0e0e0] mb-3 pb-2 border-b border-white/5">Deal Sensitivity</h2>
          <div className="grid grid-cols-5 gap-1">
            {['Price', 'Profit', 'Margin', 'Tier', 'Portfolio (10)'].map(h => (
              <div key={h} className="bg-void-3 rounded-md p-2.5 text-center text-[10px] text-white/22 uppercase tracking-wide">{h}</div>
            ))}
            {SENSITIVITY.map(s => [
              <div key={s.price + 'p'} className={`bg-void-2 rounded-md p-2.5 text-center ${s.highlight ? 'border border-brass-dim shadow-[0_0_8px_var(--color-brass-glow)]' : ''}`}>
                <div className="text-[10px] text-white/25">${(s.price / 1000).toFixed(0)}K</div>
              </div>,
              <div key={s.price + 'pr'} className={`bg-void-2 rounded-md p-2.5 text-center ${s.highlight ? 'border border-brass-dim shadow-[0_0_8px_var(--color-brass-glow)]' : ''}`}>
                <div className={`font-display text-[14px] font-bold ${s.positive ? 'text-nexus-emerald' : 'text-nexus-crimson'}`}>{s.positive ? '+' : ''}${s.profit.toLocaleString()}</div>
              </div>,
              <div key={s.price + 'm'} className={`bg-void-2 rounded-md p-2.5 text-center ${s.highlight ? 'border border-brass-dim shadow-[0_0_8px_var(--color-brass-glow)]' : ''}`}>
                <div className={`text-[12px] ${s.positive ? 'text-nexus-emerald' : 'text-nexus-crimson'}`}>{s.margin}%</div>
              </div>,
              <div key={s.price + 't'} className={`bg-void-2 rounded-md p-2.5 text-center ${s.highlight ? 'border border-brass-dim shadow-[0_0_8px_var(--color-brass-glow)]' : ''}`}>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${TIER_BADGE[s.tier]}`}>{s.tier}</span>
              </div>,
              <div key={s.price + 'port'} className={`bg-void-2 rounded-md p-2.5 text-center ${s.highlight ? 'border border-brass-dim shadow-[0_0_8px_var(--color-brass-glow)]' : ''}`}>
                <div className={`font-display text-[14px] font-bold ${s.positive ? 'text-nexus-emerald' : 'text-nexus-crimson'}`}>{s.positive ? '+' : ''}${(s.profit * 10).toLocaleString()}</div>
              </div>,
            ])}
          </div>
        </div>
      </div>

      {/* Right */}
      <div className="bg-void-1 overflow-y-auto p-5 space-y-6">
        {/* Market Comps */}
        <div>
          <h2 className="font-display font-bold text-[16px] text-[#e0e0e0] mb-3 pb-2 border-b border-white/5">Market Comparables</h2>
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[['New Construction', '$312K', 'Avg close · 45 DOM'], ['Existing Homes', '$267K', 'Avg close · 28 DOM'], ['Premium %', '+16.9%', 'New vs existing']].map(([t, v, s]) => (
              <div key={t} className="bg-void-2 rounded-lg p-3.5 text-center">
                <div className="text-[10px] text-white/20 uppercase tracking-widest mb-2">{t}</div>
                <div className={`font-display text-[22px] font-bold ${t === 'Premium %' ? 'text-nexus-emerald' : 'text-brass-bright'}`}>{v}</div>
                <div className="text-[10px] text-white/20 mt-1">{s}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Portfolio */}
        <div>
          <h2 className="font-display font-bold text-[16px] text-[#e0e0e0] mb-3 pb-2 border-b border-white/5">Tier 1 Portfolio Value</h2>
          <div className="grid grid-cols-2 gap-2">
            {[['23', 'Tier 1 Opps'], [`$${((PROFIT * 23 * 10) / 1e6).toFixed(1)}M`, 'Portfolio Profit (10 lots ea)'], [`${MARGIN}%`, 'Blended Margin'], [`$${((RETAIL * 23 * 10) / 1e6).toFixed(1)}M`, 'Total Revenue']].map(([v, l]) => (
              <div key={l} className="bg-void-2 rounded-md p-3">
                <div className="font-display text-[18px] font-bold text-brass-bright">{v}</div>
                <div className="text-[9px] text-white/15 uppercase tracking-widest">{l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Dormant */}
        <div>
          <h2 className="font-display font-bold text-[16px] text-[#e0e0e0] mb-3 pb-2 border-b border-white/5">Dormant Supply Economics</h2>
          <div className="grid grid-cols-3 gap-2 mb-4">
            {[['76', 'Dormant Clusters'], ['22,057', 'Acres'], [`$${((22057 * 35000) / 1e6).toFixed(0)}M`, 'Est. Land Value']].map(([v, l]) => (
              <div key={l} className="bg-void-2 rounded-md p-3">
                <div className="font-display text-[18px] font-bold text-brass-bright">{v}</div>
                <div className="text-[9px] text-white/15 uppercase tracking-widest">{l}</div>
              </div>
            ))}
          </div>
          <h3 className="font-display font-bold text-[13px] text-[#e0e0e0] mb-2">Top Dormant Holders</h3>
          {[['Toll Brothers', 146, 892], ['M/I Homes', 99, 567], ['Pulte Group', 59, 334], ['Lennar Corp', 42, 256], ['NVR Inc', 38, 213]].map(([n, l, a]) => (
            <div key={n} className="flex items-center gap-2 py-1.5 border-b border-white/4">
              <span className="text-[12px] text-white/55 flex-1">{n}</span>
              <span className="text-[12px] font-semibold text-brass-bright">{l} lots</span>
              <span className="text-[11px] text-white/20">{a.toLocaleString()} ac</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
