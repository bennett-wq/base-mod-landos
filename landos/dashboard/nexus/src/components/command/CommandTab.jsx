import { useState, useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { addToast } from '../../store/meshSlice';
import { createMission } from '../../store/missionsSlice';

const RUNNER_LOGS = {
  supply: [
    { c: 'text-nexus-emerald', t: 'Spark ingestion complete — 95 listings normalized' },
    { c: 'text-nexus-emerald', t: 'BBO signal scan: 12 fatigue, 8 package, 3 exit' },
    { c: 'text-nexus-cyan', t: '47 listings linked to parcel clusters' },
    { c: 'text-nexus-emerald', t: 'Scoring pipeline: 67 parcels rescored (Δ≥0.05)' },
    { c: 'text-nexus-amber', t: 'Cooldown active: RJ (pkg_lang) — 6d 23h remaining' },
    { c: 'text-nexus-emerald', t: 'Price reduction: 3 listings in Ann Arbor TWP' },
    { c: 'text-nexus-cyan', t: 'New listing: 12.4ac Webster TWP — $189,000' },
    { c: 'text-nexus-emerald', t: 'Haversine match: listing → parcel (32m distance)' },
    { c: 'text-nexus-amber', t: 'CDOM ≥ 120: 4 listings flagged for deep scan' },
    { c: 'text-nexus-emerald', t: 'Wake instruction: RESCORE 14 parcels' },
  ],
  cluster: [
    { c: 'text-nexus-emerald', t: 'ParcelClusterDetector: 2,229 clusters' },
    { c: 'text-nexus-emerald', t: 'ClusterDetector: 23 agent groups, 11 office programs' },
    { c: 'text-nexus-cyan', t: '47 clusters with active listings cross-referenced' },
    { c: 'text-nexus-emerald', t: 'Toll Brothers: 146 lots — HIGHEST signal' },
    { c: 'text-nexus-emerald', t: 'Dormant supply: 76 clusters, 22,057 acres' },
    { c: 'text-nexus-purple', t: 'Owner match: "MI HOMES" → 3 clusters merged' },
    { c: 'text-nexus-cyan', t: 'Proximity cluster: 8 parcels within 50m centroid' },
    { c: 'text-nexus-emerald', t: 'Subdivision remnant detected: Whitmore Lake Estates' },
  ],
  bbo: [
    { c: 'text-nexus-cyan', t: 'Scanning 95 active listings for BBO signals...' },
    { c: 'text-nexus-emerald', t: 'CDOM thresholds: 18 listings ≥ 90 days' },
    { c: 'text-nexus-emerald', t: 'Package language: 8 matches' },
    { c: 'text-nexus-amber', t: 'Fatigue language: 12 matches' },
    { c: 'text-nexus-crimson', t: 'Developer exit: 3 signals detected' },
    { c: 'text-nexus-emerald', t: 'Remarks: "take all lots" — flagged' },
    { c: 'text-nexus-cyan', t: 'Agent accumulation: RE/MAX 6 listings same subdivision' },
    { c: 'text-nexus-amber', t: 'Withdrawn + relisted pattern: 2 detections' },
  ],
  municipal: [
    { c: 'text-nexus-cyan', t: 'Awaiting Step 7 implementation' },
    { c: 'text-nexus-cyan', t: 'Will scan: plat recordings, permits, zoning changes' },
    { c: 'text-nexus-cyan', t: 'Will detect: land bank packages, township surplus' },
    { c: 'text-nexus-amber', t: 'RC fires on cluster ≥3 — 12hr cooldown per cluster' },
  ],
};

const RUNNERS = [
  {
    id: 'supply', agentId: 'supply_intelligence',
    icon: '🔭', name: 'Supply Intelligence', desc: 'Spark MLS → parcel scoring → event routing',
    color: '#00f0ff',
    stats: [['1,247', 'Events'], ['89', 'Rules'], ['96%', 'Hit Rate']],
    config: [
      { key: 'spark_endpoint', label: 'Spark API Endpoint', value: 'replication.sparkapi.com/Reso/OData' },
      { key: 'score_threshold', label: 'Score Threshold (Δ)', value: '0.05' },
      { key: 'cdom_fatigue', label: 'CDOM Fatigue Days', value: '90' },
      { key: 'haversine_match', label: 'Haversine Match (m)', value: '50' },
    ],
  },
  {
    id: 'cluster', agentId: 'cluster_detection',
    icon: '🔮', name: 'Cluster Detection', desc: 'Dual-detector: MLS + parcel-side clustering',
    color: '#a855f7',
    stats: [['892', 'Events'], ['156', 'Rules'], ['99%', 'Hit Rate']],
    config: [
      { key: 'proximity_threshold', label: 'Proximity Threshold (m)', value: '50' },
      { key: 'min_cluster_size', label: 'Min Cluster Size', value: '3' },
      { key: 'owner_dedup', label: 'Owner Dedup Method', value: 'name-normalized' },
    ],
  },
  {
    id: 'bbo', agentId: 'spark_signal',
    icon: '📡', name: 'BBO Signal Intel', desc: 'Regex pattern matching on private remarks, CDOM, agent accumulation',
    color: '#ff2d55',
    stats: [['534', 'Events'], ['67', 'Rules'], ['94%', 'Hit Rate']],
    config: [
      { key: 'fatigue_patterns', label: 'Fatigue Patterns', value: 'motivated, must sell, price reduced' },
      { key: 'package_patterns', label: 'Package Patterns', value: 'take all, package deal, remaining lots' },
      { key: 'exit_patterns', label: 'Exit Patterns', value: 'withdrawn, expired, cancelled' },
    ],
  },
  {
    id: 'municipal', agentId: 'municipal_intelligence',
    icon: '🏛️', name: 'Municipal Intelligence', desc: 'Cross-references clusters with municipal records, zoning, incentives',
    color: '#ffb800',
    stats: [['45', 'Events'], ['12', 'Rules'], ['—', 'Hit Rate']],
    config: [
      { key: 'pa58_check', label: 'PA 58 Division Check', value: 'enabled' },
      { key: 'plat_lookback', label: 'Plat Lookback Years', value: '15' },
    ],
  },
];

function TerminalRunner({ runner }) {
  const dispatch = useDispatch();
  const [logs, setLogs] = useState(RUNNER_LOGS[runner.id].slice(0, 3));
  const [running, setRunning] = useState(runner.id === 'bbo');
  const [showConfig, setShowConfig] = useState(false);
  const [input, setInput] = useState('');
  const logsRef = useRef(null);
  const intervalRef = useRef(null);

  const startRunner = () => {
    setRunning(true);
    setLogs(prev => [...prev, { c: 'text-brass', t: '── Agent started ──' }]);
    dispatch(addToast({ icon: '⚡', message: `${runner.name} started` }));

    if (runner.id !== 'municipal') {
      dispatch(createMission({
        polygon: null,
        agents: [runner.agentId],
        name: `${runner.name} — manual run`,
      }));
    }
  };

  // Typewriter log effect when running
  useEffect(() => {
    if (!running) return;
    const allLogs = RUNNER_LOGS[runner.id];
    intervalRef.current = setInterval(() => {
      const line = allLogs[Math.floor(Math.random() * allLogs.length)];
      const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setLogs(prev => {
        const next = [...prev, { c: line.c, t: `[${time}] ${line.t}` }];
        return next.length > 30 ? next.slice(-20) : next;
      });
    }, 1500 + Math.random() * 2000);
    return () => clearInterval(intervalRef.current);
  }, [running, runner.id]);

  // Auto-scroll
  useEffect(() => {
    logsRef.current?.scrollTo(0, logsRef.current.scrollHeight);
  }, [logs.length]);

  const handleCommand = () => {
    if (!input.trim()) return;
    const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLogs(prev => [
      ...prev,
      { c: 'text-brass-bright', t: `[${time}] $ ${input}` },
      { c: 'text-white/30', t: `[${time}] Command acknowledged. Processing...` },
    ]);
    setInput('');
  };

  const isIdle = runner.id === 'municipal';

  return (
    <div className="bg-void-1 flex flex-col overflow-hidden relative">
      {/* Active glow */}
      {running && (
        <div className="absolute inset-0 pointer-events-none" style={{ boxShadow: `inset 0 0 30px ${runner.color}08` }} />
      )}

      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2.5 shrink-0 relative z-10">
        <div
          className="w-9 h-9 rounded-[9px] flex items-center justify-center text-lg border"
          style={{
            background: running ? runner.color + '10' : 'var(--color-void-3)',
            borderColor: running ? runner.color + '30' : 'rgba(255,255,255,0.05)',
          }}
        >
          {runner.icon}
        </div>
        <div className="min-w-0">
          <div className="font-display font-bold text-[14px] text-[#e0e0e0] truncate">{runner.name}</div>
          <div className="text-[10px] text-white/20">{runner.desc}</div>
        </div>
        <div className={`ml-auto flex items-center gap-1.5 text-[11px] font-medium ${
          running ? 'text-nexus-amber' : isIdle ? 'text-white/15' : 'text-nexus-emerald'
        }`}>
          <span className={`w-2 h-2 rounded-full bg-current ${running ? 'animate-breathe' : ''}`} />
          {running ? 'Running' : isIdle ? 'Step 7' : 'Ready'}
        </div>
      </div>

      {/* Stats */}
      <div className="flex gap-2 px-4 py-2.5 shrink-0">
        {runner.stats.map(([v, l]) => (
          <div key={l} className="bg-void-2 rounded-md px-3 py-1.5 flex-1">
            <div className="font-display text-[16px] font-bold text-brass-bright">{v}</div>
            <div className="text-[8px] text-white/12 uppercase tracking-widest">{l}</div>
          </div>
        ))}
      </div>

      {/* Terminal / Config */}
      <div className="flex-1 overflow-hidden px-4 pb-1 relative z-10">
        {showConfig ? (
          <div className="space-y-2">
            <div className="text-[9px] text-white/12 uppercase tracking-widest mb-2">Configuration</div>
            {runner.config.map(c => (
              <div key={c.key} className="flex items-center gap-2">
                <div className="text-[10px] text-white/25 w-[140px]">{c.label}</div>
                <input
                  defaultValue={c.value}
                  className="flex-1 bg-void-3 border border-white/6 rounded px-2.5 py-1 text-[11px] text-[#e0e0e0] font-mono outline-none focus:border-brass-dim transition-colors"
                />
              </div>
            ))}
          </div>
        ) : (
          <div ref={logsRef} className="bg-void-2 rounded-lg p-2.5 text-[11px] leading-[1.7] font-mono h-full overflow-y-auto">
            {logs.map((l, i) => (
              <div key={i} className={l.c}>{l.t}</div>
            ))}
            <span className="inline-block w-1.5 h-3.5 bg-brass animate-breathe ml-0.5" />
          </div>
        )}
      </div>

      {/* Input + Actions */}
      <div className="px-4 py-2 border-t border-white/5 shrink-0 relative z-10">
        {!showConfig && (
          <div className="flex gap-2 mb-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCommand()}
              placeholder={`Command ${runner.name}...`}
              className="flex-1 bg-void-3 border border-white/6 rounded-md px-3 py-1.5 text-[11px] text-[#e0e0e0] font-mono outline-none focus:border-brass-dim transition-colors"
            />
          </div>
        )}
        <div className="flex gap-2">
          <button
            onClick={running ? () => { setRunning(false); setLogs(prev => [...prev, { c: 'text-nexus-crimson', t: '── Agent stopped ──' }]); } : startRunner}
            disabled={isIdle}
            className={`px-4 py-1.5 rounded-md font-mono text-[11px] font-semibold cursor-pointer transition-all border-none ${
              running ? 'bg-nexus-crimson/20 text-nexus-crimson hover:bg-nexus-crimson/30' :
              isIdle ? 'bg-void-3 text-white/12 cursor-not-allowed' :
              'bg-brass text-void-0 hover:bg-brass-bright hover:shadow-[0_0_12px_var(--color-brass-glow)]'
            }`}
          >
            {running ? '■ Stop' : '▶ Run'}
          </button>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className={`px-4 py-1.5 rounded-md font-mono text-[11px] font-semibold border cursor-pointer transition-all ${
              showConfig ? 'bg-brass/10 border-brass/30 text-brass' : 'bg-void-3 text-white/38 border-white/6 hover:border-brass-dim hover:text-brass'
            }`}
          >
            {showConfig ? '← Logs' : '⚙ Config'}
          </button>
          <button
            onClick={() => setLogs([])}
            className="px-4 py-1.5 bg-void-3 text-white/38 rounded-md font-mono text-[11px] font-semibold border border-white/6 cursor-pointer hover:border-brass-dim hover:text-brass transition-all"
          >
            Clear
          </button>
        </div>
      </div>
    </div>
  );
}

export default function CommandTab() {
  return (
    <div className="grid grid-cols-2 grid-rows-2 h-full gap-px bg-white/4">
      {RUNNERS.map(r => <TerminalRunner key={r.id} runner={r} />)}
    </div>
  );
}
