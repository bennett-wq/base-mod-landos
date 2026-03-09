import { useDispatch } from 'react-redux';
import { addToast } from '../../store/meshSlice';

const RUNNERS = [
  {
    icon: '🔭', name: 'Supply Intelligence Runner', desc: 'Pulls listings from Spark MLS, scores parcels, routes events',
    status: 'ready', statusLabel: 'Ready', statusClass: 'text-nexus-emerald',
    stats: [['1,247', 'Events'], ['89', 'Rules'], ['96%', 'Success']],
    logs: [
      { c: 'text-nexus-emerald', t: '[14:32:01] Spark ingestion complete — 95 listings normalized' },
      { c: 'text-nexus-emerald', t: '[14:32:03] BBO signal scan: 12 fatigue, 8 package, 3 exit' },
      { c: 'text-nexus-cyan', t: '[14:32:05] 47 listings linked to parcel clusters' },
      { c: 'text-nexus-emerald', t: '[14:32:06] Scoring pipeline: 67 parcels rescored (Δ≥0.05)' },
      { c: 'text-nexus-amber', t: '[14:31:45] Cooldown active: RJ (pkg_lang) — 6d 23h remaining' },
    ],
  },
  {
    icon: '🔮', name: 'Cluster Detection Runner', desc: 'Dual-detector across MLS listings and Regrid parcels',
    status: 'ready', statusLabel: 'Ready', statusClass: 'text-nexus-emerald',
    stats: [['892', 'Events'], ['156', 'Rules'], ['99%', 'Success']],
    logs: [
      { c: 'text-nexus-emerald', t: '[14:30:12] ParcelClusterDetector: 2,229 clusters' },
      { c: 'text-nexus-emerald', t: '[14:30:14] ClusterDetector: 23 agent groups, 11 office programs' },
      { c: 'text-nexus-cyan', t: '[14:30:15] 47 clusters with active listings cross-referenced' },
      { c: 'text-nexus-emerald', t: '[14:30:16] Toll Brothers: 146 lots — HIGHEST signal' },
      { c: 'text-nexus-emerald', t: '[14:30:17] Dormant supply: 76 clusters, 22,057 acres' },
    ],
  },
  {
    icon: '📡', name: 'BBO Signal Discovery', desc: 'Regex pattern matching on private remarks, CDOM, agent accumulation',
    status: 'running', statusLabel: 'Scanning', statusClass: 'text-nexus-amber',
    stats: [['534', 'Events'], ['67', 'Rules'], ['94%', 'Success']],
    logs: [
      { c: 'text-nexus-cyan', t: '[14:33:01] Scanning 95 active listings for BBO signals...' },
      { c: 'text-nexus-emerald', t: '[14:33:02] CDOM thresholds: 18 listings ≥ 90 days' },
      { c: 'text-nexus-emerald', t: '[14:33:03] Package language: 8 matches' },
      { c: 'text-nexus-amber', t: '[14:33:04] Fatigue language: 12 matches' },
      { c: 'text-nexus-crimson', t: '[14:33:05] Developer exit: 3 signals detected' },
    ],
  },
  {
    icon: '🏛️', name: 'Municipal Intelligence Runner', desc: 'Cross-references clusters with municipal records, zoning, incentives',
    status: 'idle', statusLabel: 'Step 7', statusClass: 'text-white/15',
    stats: [['45', 'Events'], ['12', 'Rules'], ['—', 'Success']],
    logs: [
      { c: 'text-nexus-cyan', t: '[—] Awaiting Step 7 implementation' },
      { c: 'text-nexus-cyan', t: '[—] Will scan: plat recordings, permits, zoning changes' },
      { c: 'text-nexus-cyan', t: '[—] Will detect: land bank packages, township surplus' },
      { c: 'text-nexus-amber', t: '[—] RC fires on cluster ≥3 — 12hr cooldown per cluster' },
    ],
  },
];

export default function CommandTab() {
  const dispatch = useDispatch();

  return (
    <div className="grid grid-cols-2 grid-rows-2 h-full gap-px bg-white/4">
      {RUNNERS.map(r => (
        <div key={r.name} className="bg-void-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2.5 shrink-0">
            <div className="w-9 h-9 rounded-[9px] flex items-center justify-center text-lg bg-void-3 border border-white/5">{r.icon}</div>
            <div className="min-w-0">
              <div className="font-display font-bold text-[14px] text-[#e0e0e0] truncate">{r.name}</div>
              <div className="text-[10px] text-white/20">{r.desc}</div>
            </div>
            <div className={`ml-auto flex items-center gap-1.5 text-[11px] font-medium ${r.statusClass}`}>
              <span className={`w-2 h-2 rounded-full bg-current ${r.status === 'running' ? 'animate-breathe' : ''}`} />
              {r.statusLabel}
            </div>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto px-4 py-3">
            <div className="flex gap-3 mb-3">
              {r.stats.map(([v, l]) => (
                <div key={l} className="bg-void-2 rounded-md px-3 py-2 flex-1">
                  <div className="font-display text-[18px] font-bold text-brass-bright">{v}</div>
                  <div className="text-[9px] text-white/15 uppercase tracking-widest">{l}</div>
                </div>
              ))}
            </div>
            <div className="bg-void-2 rounded-md p-2.5 text-[11px] leading-relaxed font-mono max-h-[120px] overflow-y-auto">
              {r.logs.map((l, i) => <div key={i} className={l.c}>{l.t}</div>)}
            </div>
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 border-t border-white/5 flex gap-2 shrink-0">
            <button onClick={() => dispatch(addToast({ icon: '⚡', message: `${r.name} triggered` }))} className="px-4 py-1.5 bg-brass text-void-0 rounded-md font-mono text-[11px] font-semibold cursor-pointer hover:bg-brass-bright hover:shadow-[0_0_12px_var(--color-brass-glow)] transition-all border-none">▶ Run</button>
            <button onClick={() => dispatch(addToast({ icon: '📋', message: `Viewing ${r.name} logs` }))} className="px-4 py-1.5 bg-void-3 text-white/38 rounded-md font-mono text-[11px] font-semibold border border-white/6 cursor-pointer hover:border-brass-dim hover:text-brass transition-all">Logs</button>
            <button onClick={() => dispatch(addToast({ icon: '⚙️', message: `${r.name} config` }))} className="px-4 py-1.5 bg-void-3 text-white/38 rounded-md font-mono text-[11px] font-semibold border border-white/6 cursor-pointer hover:border-brass-dim hover:text-brass transition-all">Config</button>
          </div>
        </div>
      ))}
    </div>
  );
}
