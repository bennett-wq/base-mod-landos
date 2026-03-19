export default function MetricsStrip() {
  return (
    <div className="flex h-full">
      <div className="flex-1 flex gap-px bg-white/4">
        {[
          { label: 'Active Listings', value: '95', delta: '+3 today', up: true },
          { label: 'Vacant Parcels', value: '10,266', delta: 'Regrid CSV', up: null },
          { label: 'Clusters', value: '2,229', delta: '1,112 own / 81 sub / 1,036 prox', up: true },
          { label: 'Tier 1', value: '23', delta: 'High convergence', up: true, crimson: true },
          { label: 'Dormant', value: '22,057', delta: 'acres / 76 clusters', up: null },
        ].map(m => (
          <div key={m.label} className="flex-1 bg-void-1 px-5 py-3 flex flex-col justify-center">
            <div className="text-[10px] text-white/17 uppercase tracking-[1.5px] mb-1">{m.label}</div>
            <div className={`font-display text-[26px] font-extrabold leading-none tabular-nums ${m.crimson ? 'text-nexus-crimson' : 'text-brass-bright'}`}>{m.value}</div>
            <div className={`text-[10px] font-medium mt-1 ${m.up === true ? 'text-nexus-emerald' : m.up === false ? 'text-nexus-crimson' : 'text-white/12'}`}>{m.delta}</div>
          </div>
        ))}
      </div>

      <div className="w-[380px] shrink-0 bg-void-1 border-l border-white/5 px-5 py-3 flex flex-col gap-1.5">
        <div className="text-[10px] text-white/17 uppercase tracking-[1.5px]">Pipeline Pulse</div>
        {[
          { name: 'Spark MLS', stat: '95', color: '#00ff88', pct: 100, active: true },
          { name: 'Regrid CSV', stat: '10,266', color: '#00f0ff', pct: 100, active: true },
          { name: 'Cluster Detection', stat: '2,229', color: '#a855f7', pct: 100, active: true },
          { name: 'Trigger Engine', stat: '31 rules', color: '#c9a44e', pct: 100, active: true },
          { name: 'Municipal Scan', stat: 'Step 7', color: '#ffb800', pct: 0, active: false },
        ].map(p => (
          <div key={p.name} className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full shrink-0 ${p.active ? 'animate-breathe' : 'opacity-30'}`} style={{ background: p.color }} />
            <div className={`text-[11px] flex-1 ${p.active ? 'text-white/35' : 'text-white/15'}`}>{p.name}</div>
            <div className={`text-[11px] font-medium tabular-nums ${p.active ? 'text-white/50' : 'text-white/12'}`}>{p.stat}</div>
            <div className="w-14 h-1 bg-void-4 rounded-sm overflow-hidden">
              <div className="h-full rounded-sm transition-all duration-500" style={{ width: `${p.pct}%`, background: p.color }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
