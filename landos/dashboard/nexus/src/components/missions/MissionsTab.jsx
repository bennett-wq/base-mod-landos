import { useSelector, useDispatch } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { openMissionTheater, toggleUploadPortal, toggleDrawMode, createMission } from '../../store/missionsSlice';
import { setActiveTab } from '../../store/uiSlice';
import { addToast } from '../../store/meshSlice';
import { AGENTS } from '../../data/agents';

const PHASE_STYLES = {
  deploying: { color: '#ffb800', bg: 'bg-nexus-amber/15 text-nexus-amber', icon: '🚀' },
  scanning:  { color: '#00f0ff', bg: 'bg-nexus-cyan/15 text-nexus-cyan', icon: '🔭' },
  analyzing: { color: '#a855f7', bg: 'bg-nexus-purple/15 text-nexus-purple', icon: '🧬' },
  complete:  { color: '#00ff88', bg: 'bg-nexus-emerald/15 text-nexus-emerald', icon: '✓' },
};

function MissionCard({ mission }) {
  const dispatch = useDispatch();
  const phase = PHASE_STYLES[mission.phase];
  const isActive = mission.phase !== 'complete';

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={() => dispatch(openMissionTheater(mission.id))}
      className="bg-void-2 rounded-xl border border-white/5 p-5 cursor-pointer hover:border-white/10 transition-all group relative overflow-hidden"
    >
      {/* Active shimmer */}
      {isActive && (
        <motion.div
          className="absolute inset-0 pointer-events-none"
          style={{ background: `linear-gradient(90deg, transparent, ${phase.color}05, transparent)` }}
          animate={{ x: ['-100%', '200%'] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
        />
      )}

      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-3">
          <motion.div
            animate={isActive ? { rotate: 360 } : {}}
            transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
            className="w-10 h-10 rounded-xl flex items-center justify-center text-lg border"
            style={{ borderColor: phase.color + '30', background: phase.color + '10' }}
          >
            {phase.icon}
          </motion.div>
          <div className="flex-1 min-w-0">
            <div className="font-display text-[15px] font-bold text-[#e0e0e0] truncate">{mission.name}</div>
            <div className="text-[10px] text-white/18">
              {new Date(mission.createdAt).toLocaleString()} · {mission.agents.length} agents
            </div>
          </div>
          <span className={`text-[9px] font-bold px-2.5 py-1 rounded-full ${phase.bg}`}>
            {mission.phase.toUpperCase()}
          </span>
        </div>

        {/* Agent pills */}
        <div className="flex gap-1.5 mb-3">
          {mission.agents.map(aid => {
            const agent = AGENTS.find(a => a.id === aid);
            return agent ? (
              <span key={aid} className="text-[9px] px-2 py-0.5 rounded-full bg-void-3 text-white/30 border border-white/5 flex items-center gap-1">
                <span>{agent.icon}</span> {agent.name}
              </span>
            ) : null;
          })}
        </div>

        {/* Progress */}
        <div className="h-1.5 bg-void-4 rounded-full overflow-hidden mb-3">
          <motion.div
            className="h-full rounded-full"
            style={{ background: phase.color }}
            animate={{ width: `${mission.progress}%` }}
          />
        </div>

        {/* Findings grid */}
        <div className="grid grid-cols-4 gap-2">
          {[
            [mission.findings.parcels, 'Parcels', '#3b82f6'],
            [mission.findings.clusters, 'Clusters', '#a855f7'],
            [mission.findings.signals, 'Signals', '#00f0ff'],
            [mission.findings.opportunities, 'Opps', '#00ff88'],
          ].map(([val, label, color]) => (
            <div key={label} className="bg-void-3 rounded-lg p-2 text-center">
              <div className="font-display text-[14px] font-bold" style={{ color }}>{val}</div>
              <div className="text-[8px] text-white/12 uppercase tracking-widest">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

export default function MissionsTab() {
  const dispatch = useDispatch();
  const { missions, uploads } = useSelector(s => s.missions);

  const activeMissions = missions.filter(m => m.phase !== 'complete');
  const completedMissions = missions.filter(m => m.phase === 'complete');

  return (
    <div className="grid grid-cols-[1fr_340px] h-full gap-px bg-white/4">
      {/* Main area */}
      <div className="bg-void-1 overflow-y-auto p-6 space-y-6">
        {/* Quick actions */}
        <div className="flex gap-3">
          <button
            onClick={() => dispatch(toggleUploadPortal())}
            className="flex-1 py-4 bg-void-2 border border-white/6 rounded-xl text-center cursor-pointer hover:border-brass-dim hover:bg-void-3 transition-all group"
          >
            <div className="text-[24px] mb-2 group-hover:scale-110 transition-transform">📦</div>
            <div className="font-display text-[12px] font-semibold text-white/40 group-hover:text-brass transition-colors">Upload Data</div>
            <div className="text-[10px] text-white/12">CSV, Excel, GeoJSON, PDF</div>
          </button>
          <button
            onClick={() => { dispatch(setActiveTab('radar')); setTimeout(() => dispatch(toggleDrawMode()), 100); }}
            className="flex-1 py-4 bg-void-2 border border-white/6 rounded-xl text-center cursor-pointer hover:border-brass-dim hover:bg-void-3 transition-all group"
          >
            <div className="text-[24px] mb-2 group-hover:scale-110 transition-transform">🗺️</div>
            <div className="font-display text-[12px] font-semibold text-white/40 group-hover:text-brass transition-colors">Polygon Search</div>
            <div className="text-[10px] text-white/12">Draw on Radar map</div>
          </button>
          <button
            onClick={() => {
              dispatch(createMission({
                polygon: null,
                agents: ['supply_intelligence', 'cluster_detection', 'spark_signal', 'opportunity_creation'],
                name: 'Full county scan — all agents',
              }));
              dispatch(addToast({ icon: '🚀', message: 'Full county scan deployed — 4 agents' }));
            }}
            className="flex-1 py-4 bg-void-2 border border-white/6 rounded-xl text-center cursor-pointer hover:border-brass-dim hover:bg-void-3 transition-all group"
          >
            <div className="text-[24px] mb-2 group-hover:scale-110 transition-transform">🤖</div>
            <div className="font-display text-[12px] font-semibold text-white/40 group-hover:text-brass transition-colors">Deploy Agent</div>
            <div className="text-[10px] text-white/12">Custom scan mission</div>
          </button>
          <button
            onClick={() => dispatch(addToast({ icon: '📊', message: 'Signal intelligence report generating...' }))}
            className="flex-1 py-4 bg-void-2 border border-white/6 rounded-xl text-center cursor-pointer hover:border-brass-dim hover:bg-void-3 transition-all group"
          >
            <div className="text-[24px] mb-2 group-hover:scale-110 transition-transform">📊</div>
            <div className="font-display text-[12px] font-semibold text-white/40 group-hover:text-brass transition-colors">Generate Report</div>
            <div className="text-[10px] text-white/12">Signal intelligence brief</div>
          </button>
        </div>

        {/* Active missions */}
        {activeMissions.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <motion.div
                animate={{ opacity: [1, 0.4, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="w-2 h-2 rounded-full bg-nexus-amber"
              />
              <div className="text-[10px] text-white/12 uppercase tracking-[1.5px]">Active Missions</div>
              <span className="text-[10px] text-nexus-amber font-semibold">{activeMissions.length}</span>
            </div>
            <div className="space-y-3">
              {activeMissions.map(m => <MissionCard key={m.id} mission={m} />)}
            </div>
          </div>
        )}

        {/* Completed missions */}
        {completedMissions.length > 0 && (
          <div>
            <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-3">Completed Missions</div>
            <div className="space-y-3">
              {completedMissions.map(m => <MissionCard key={m.id} mission={m} />)}
            </div>
          </div>
        )}

        {missions.length === 0 && (
          <div className="text-center py-20">
            <div className="text-[48px] mb-4">🎯</div>
            <div className="font-display text-[18px] font-bold text-white/25 mb-2">No missions yet</div>
            <div className="text-[12px] text-white/12 max-w-[400px] mx-auto">
              Draw a polygon on the Radar map to select territory, then deploy agents to scan for opportunities. Or upload data to feed the mesh.
            </div>
          </div>
        )}
      </div>

      {/* Sidebar: Upload activity */}
      <div className="bg-void-1 border-l border-white/5 flex flex-col overflow-hidden">
        <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2 shrink-0">
          <span className="text-[10px] text-white/12 uppercase tracking-[1.5px]">Data Feed</span>
          <span className="ml-auto text-[10px] text-white/10">{uploads.length} files</span>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {uploads.length === 0 ? (
            <div className="text-center py-10">
              <div className="text-[28px] mb-2">📂</div>
              <div className="text-[11px] text-white/15">No uploads yet</div>
            </div>
          ) : (
            uploads.map(u => {
              const ext = u.fileName.split('.').pop().toUpperCase();
              const statusColor = u.status === 'ingested' ? 'text-nexus-emerald' : u.status === 'processing' ? 'text-nexus-cyan' : 'text-nexus-amber';
              return (
                <div key={u.id} className="bg-void-2 rounded-lg p-3 border border-white/4">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[12px]">📄</span>
                    <span className="text-[11px] text-white/45 truncate flex-1">{u.fileName}</span>
                    <span className={`text-[9px] font-semibold ${statusColor}`}>{u.status.toUpperCase()}</span>
                  </div>
                  {u.status === 'processing' && (
                    <div className="h-1 bg-void-4 rounded overflow-hidden mt-1.5">
                      <div className="h-full bg-nexus-cyan rounded" style={{ width: `${u.progress}%` }} />
                    </div>
                  )}
                  {u.records && (
                    <div className="text-[10px] text-nexus-emerald mt-1">{u.records} records ingested</div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
