import { useSelector, useDispatch } from 'react-redux';
import { setActiveTab, toggleCommandPalette } from '../../store/uiSlice';

const TABS = [
  { id: 'mesh', label: '⚡ Mesh' },
  { id: 'radar', label: '🎯 Radar' },
  { id: 'clusters', label: '🏢 Clusters' },
  { id: 'command', label: '🤖 Command' },
  { id: 'economics', label: '📊 Economics' },
];

export default function Navbar() {
  const dispatch = useDispatch();
  const activeTab = useSelector(s => s.ui.activeTab);
  const { eventsPerSecond, totalRulesFired, totalWakes } = useSelector(s => s.mesh);

  return (
    <nav className="h-[52px] bg-void-1 border-b border-white/5 flex items-center px-5 gap-4 z-50 shrink-0">
      {/* Brand */}
      <div className="flex items-center gap-2.5">
        <div className="w-[30px] h-[30px] bg-gradient-to-br from-brass to-brass-bright rounded-[7px] flex items-center justify-center font-display font-black text-[15px] text-void-0 shadow-[0_0_14px_var(--color-brass-glow)]">
          L
        </div>
        <div>
          <div className="font-display font-bold text-[16px] text-brass tracking-wide">LandOS NEXUS</div>
          <div className="text-[10px] text-white/16 tracking-[2px] uppercase">Command Center</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-0.5 ml-8">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => dispatch(setActiveTab(tab.id))}
            className={`px-4 py-2 rounded-t-md text-[12px] font-medium tracking-wide border border-transparent border-b-0 transition-all cursor-pointer
              ${activeTab === tab.id
                ? 'text-brass bg-void-2 border-white/5'
                : 'text-white/25 hover:text-white/45 hover:bg-void-2'
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Metrics */}
      <div className="flex gap-5 ml-auto items-center">
        <div className="text-center">
          <div className="text-[14px] font-semibold text-brass-bright tabular-nums">{eventsPerSecond}</div>
          <div className="text-[9px] text-white/18 uppercase tracking-widest">Events/s</div>
        </div>
        <div className="text-center">
          <div className="text-[14px] font-semibold text-brass-bright tabular-nums">{totalRulesFired}</div>
          <div className="text-[9px] text-white/18 uppercase tracking-widest">Rules</div>
        </div>
        <div className="text-center">
          <div className="text-[14px] font-semibold text-brass-bright tabular-nums">{totalWakes}</div>
          <div className="text-[9px] text-white/18 uppercase tracking-widest">Wakes</div>
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-medium bg-nexus-emerald/15 text-nexus-emerald border border-nexus-emerald/10">
        <span className="w-1.5 h-1.5 rounded-full bg-current animate-breathe" />
        Mesh Online
      </div>

      <span className="px-2.5 py-0.5 rounded text-[10px] font-semibold tracking-widest uppercase bg-nexus-cyan/15 text-nexus-cyan border border-nexus-cyan/8">
        Phase 1
      </span>

      {/* Command trigger */}
      <button
        onClick={() => dispatch(toggleCommandPalette())}
        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-void-3 border border-white/6 text-white/25 text-[12px] cursor-pointer hover:border-brass-dim hover:text-brass transition-all"
      >
        Command
        <kbd className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-white/5 border border-white/6">⌘K</kbd>
      </button>
    </nav>
  );
}
