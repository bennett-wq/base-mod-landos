import { useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setSelectedAgent, setRightPanel } from '../../store/uiSlice';
import useMeshCanvas from '../../hooks/useMeshCanvas';
import SignalFeed from './SignalFeed';
import RuleGrid from './RuleGrid';
import ClusterMini from './ClusterMini';
import MetricsStrip from './MetricsStrip';

const STATUS_COLORS = { online: 'text-nexus-emerald', scanning: 'text-nexus-cyan', cooldown: 'text-nexus-amber', idle: 'text-white/15' };

export default function MeshTab() {
  const dispatch = useDispatch();
  const canvasRef = useRef(null);
  const agents = useSelector(s => s.mesh.agents);
  const signals = useSelector(s => s.mesh.signals);
  const selectedAgent = useSelector(s => s.ui.selectedAgent);
  const rightPanel = useSelector(s => s.ui.rightPanel);
  const { spawnParticle } = useMeshCanvas(canvasRef);

  // Spawn particles when new signals arrive
  const lastSignalRef = useRef(null);
  useEffect(() => {
    if (signals.length > 0 && signals[0].id !== lastSignalRef.current) {
      lastSignalRef.current = signals[0].id;
      spawnParticle(signals[0].family);
    }
  }, [signals, spawnParticle]);

  return (
    <div className="grid grid-cols-[280px_1fr_320px] grid-rows-[1fr_170px] h-full gap-px bg-white/4">
      {/* Left — Agent Roster */}
      <div className="bg-void-1 overflow-y-auto p-2">
        <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2 mb-2">
          <span className="font-display font-semibold text-[11px] text-white/30 uppercase tracking-[1.5px]">Agent Mesh</span>
          <span className="ml-auto text-[10px] text-white/12 px-2 py-0.5 bg-white/4 rounded-full">{agents.length} agents</span>
        </div>
        {agents.map(a => (
          <div
            key={a.id}
            onClick={() => dispatch(setSelectedAgent(a.id))}
            className={`p-3 rounded-lg border cursor-pointer transition-all mb-1 relative overflow-hidden group
              ${selectedAgent === a.id ? 'bg-void-3 border-white/8' : 'border-transparent hover:bg-void-3 hover:border-white/5'}`}
            style={{ '--ac': a.color }}
          >
            <div className={`absolute left-0 top-0 bottom-0 w-[3px] transition-opacity ${selectedAgent === a.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`} style={{ background: a.color }} />
            <div className="flex items-center gap-2 mb-1">
              <div className="w-[30px] h-[30px] rounded-[7px] flex items-center justify-center text-[15px] bg-void-4 border border-white/5 shrink-0">{a.icon}</div>
              <div className="min-w-0">
                <div className="font-display font-semibold text-[12px] text-[#e0e0e0] truncate">{a.name}</div>
                <div className="text-[9px] text-white/17">{a.role}</div>
              </div>
              <div className={`ml-auto flex items-center gap-1 text-[10px] font-medium ${STATUS_COLORS[a.status]}`}>
                <span className="w-1.5 h-1.5 rounded-full bg-current animate-breathe" />
                {a.status}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-1 text-[10px] text-white/17">
              <div><b className="text-white/40 font-medium">{a.stats.events.toLocaleString()}</b> events</div>
              <div><b className="text-white/40 font-medium">{a.stats.rules}</b> rules</div>
              <div>Wake: <b className="text-white/40 font-medium">{a.stats.wake}</b></div>
              <div>IDs: <b className="text-white/40 font-medium">{a.rules.join(',')}</b></div>
            </div>
            <div className="flex gap-[3px] mt-1.5">
              {a.rules.map((_, i) => (
                <div key={i} className={`w-3.5 h-[3px] rounded-sm transition-all ${Math.random() > 0.5 ? 'opacity-100 bg-brass shadow-[0_0_6px_var(--color-brass-glow)]' : 'opacity-30 bg-brass-dim'}`} />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Center — Canvas */}
      <div className="bg-void-0 relative overflow-hidden">
        <canvas ref={canvasRef} className="w-full h-full block" />
        <div className="absolute top-3 left-1/2 -translate-x-1/2 flex gap-5 bg-void-0/80 backdrop-blur-xl px-5 py-2 rounded-full border border-white/5 z-10">
          {[['Clusters', '2,229'], ['Tier 1', '23'], ['Rules', '31'], ['Depth Cap', '5']].map(([l, v]) => (
            <div key={l} className="flex items-center gap-1.5 text-[11px] text-white/30">
              {l} <span className="font-semibold text-brass-bright tabular-nums">{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right — Signals/Rules/Clusters */}
      <div className="bg-void-1 flex flex-col overflow-hidden">
        <RightPanelTabs />
        <div className="flex-1 overflow-y-auto p-2">
          {rightPanel === 'signals' && <SignalFeed />}
          {rightPanel === 'rules' && <RuleGrid />}
          {rightPanel === 'clusters' && <ClusterMini />}
        </div>
      </div>

      {/* Bottom — Metrics */}
      <div className="col-span-3 bg-void-1 border-t border-white/5">
        <MetricsStrip />
      </div>
    </div>
  );
}

function RightPanelTabs() {
  const dispatch = useDispatch();
  const active = useSelector(s => s.ui.rightPanel);
  const tabs = [['signals', 'Signals'], ['rules', 'Rules'], ['clusters', 'Clusters']];
  return (
    <div className="flex border-b border-white/5 shrink-0">
      {tabs.map(([id, label]) => (
        <button
          key={id}
          onClick={() => dispatch(setRightPanel(id))}
          className={`flex-1 py-2.5 text-center text-[10px] font-medium uppercase tracking-widest border-b-2 transition-all cursor-pointer
            ${active === id ? 'text-brass border-brass' : 'text-white/17 border-transparent hover:text-white/30'}`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
