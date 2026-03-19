import { useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { closeMissionTheater, tickMission } from '../../store/missionsSlice';
import { setActiveTab } from '../../store/uiSlice';
import { addToast } from '../../store/meshSlice';
import { AGENTS } from '../../data/agents';

const PHASE_META = {
  deploying: { label: 'DEPLOYING', color: '#ffb800', glow: 'shadow-[0_0_30px_rgba(255,184,0,0.15)]' },
  scanning:  { label: 'SCANNING',  color: '#00f0ff', glow: 'shadow-[0_0_30px_rgba(0,240,255,0.15)]' },
  analyzing: { label: 'ANALYZING', color: '#a855f7', glow: 'shadow-[0_0_30px_rgba(168,85,247,0.15)]' },
  complete:  { label: 'COMPLETE',  color: '#00ff88', glow: 'shadow-[0_0_30px_rgba(0,255,136,0.15)]' },
};

const LOG_COLORS = {
  deploying: 'text-nexus-amber',
  scanning: 'text-nexus-cyan',
  analyzing: 'text-nexus-purple',
  complete: 'text-nexus-emerald',
  success: 'text-nexus-emerald',
  system: 'text-brass',
  phase: 'text-brass-bright',
};

function AgentAvatar({ agentId, phase, delay = 0 }) {
  const agent = AGENTS.find(a => a.id === agentId);
  if (!agent) return null;
  const isActive = phase !== 'complete';

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: delay * 0.15, type: 'spring', stiffness: 200 }}
      className="flex flex-col items-center gap-2"
    >
      <div className="relative">
        {/* Pulse ring */}
        {isActive && (
          <motion.div
            animate={{ scale: [1, 1.6, 1], opacity: [0.4, 0, 0.4] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            className="absolute inset-0 rounded-full"
            style={{ border: `2px solid ${agent.color}` }}
          />
        )}
        {/* Orbit ring */}
        {isActive && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
            className="absolute -inset-2"
          >
            <div className="w-2 h-2 rounded-full absolute top-0 left-1/2 -translate-x-1/2" style={{ background: agent.color, boxShadow: `0 0 8px ${agent.color}` }} />
          </motion.div>
        )}
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl border-2 relative z-10"
          style={{
            background: 'linear-gradient(135deg, #1a1a2e, #0e0e18)',
            borderColor: agent.color + '60',
            boxShadow: isActive ? `0 0 20px ${agent.color}30, inset 0 0 20px ${agent.color}10` : 'none',
          }}
        >
          {agent.icon}
        </div>
        {/* Status dot */}
        <div
          className="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full border-2 border-void-0 z-20"
          style={{ background: isActive ? agent.color : '#00ff88' }}
        />
      </div>
      <div className="text-center">
        <div className="font-display text-[11px] font-semibold text-white/60">{agent.name}</div>
        <div className="text-[9px] font-mono" style={{ color: agent.color }}>
          {isActive ? 'ACTIVE' : 'DONE'}
        </div>
      </div>
    </motion.div>
  );
}

function ProgressBar({ progress, phase }) {
  const meta = PHASE_META[phase];
  return (
    <div className="relative">
      <div className="h-2 bg-void-3 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full relative"
          style={{ background: `linear-gradient(90deg, ${meta.color}80, ${meta.color})` }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        >
          {/* Shimmer */}
          <motion.div
            className="absolute inset-0 rounded-full"
            style={{ background: `linear-gradient(90deg, transparent, ${meta.color}40, transparent)` }}
            animate={{ x: ['-100%', '200%'] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          />
        </motion.div>
      </div>
      <div className="flex justify-between mt-1.5">
        {['DEPLOY', 'SCAN', 'ANALYZE', 'COMPLETE'].map((label, i) => {
          const active = i <= (PHASE_META[phase] ? Object.keys(PHASE_META).indexOf(phase) : 0);
          return (
            <div key={label} className={`text-[9px] font-mono tracking-widest ${active ? 'text-brass-bright' : 'text-white/12'}`}>
              {label}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function MissionTheater() {
  const dispatch = useDispatch();
  const { theaterOpen, theaterMissionId, missions } = useSelector(s => s.missions);
  const mission = missions.find(m => m.id === theaterMissionId);
  const logsEndRef = useRef(null);

  // Auto-tick mission progress
  useEffect(() => {
    if (!theaterOpen || !mission || mission.phase === 'complete') return;
    const id = setInterval(() => dispatch(tickMission(mission.id)), 400);
    return () => clearInterval(id);
  }, [theaterOpen, mission?.id, mission?.phase, dispatch]);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mission?.logs?.length]);

  if (!mission) return null;

  const meta = PHASE_META[mission.phase];

  return (
    <AnimatePresence>
      {theaterOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[800] flex items-center justify-center"
        >
          {/* Backdrop with grid */}
          <div className="absolute inset-0 bg-void-0/95 backdrop-blur-2xl">
            <div className="absolute inset-0 opacity-[0.03]"
              style={{ backgroundImage: 'linear-gradient(rgba(201,164,78,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(201,164,78,0.3) 1px, transparent 1px)', backgroundSize: '60px 60px' }}
            />
          </div>

          {/* Content */}
          <motion.div
            initial={{ scale: 0.9, y: 20, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.9, y: 20, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 200, damping: 25 }}
            className={`relative w-[900px] max-h-[85vh] bg-void-1 border border-white/8 rounded-2xl overflow-hidden ${meta.glow}`}
          >
            {/* Header */}
            <div className="px-8 py-6 border-b border-white/5 flex items-center gap-4">
              <div className="flex items-center gap-3">
                <motion.div
                  animate={mission.phase !== 'complete' ? { rotate: 360 } : {}}
                  transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-xl border"
                  style={{ borderColor: meta.color + '40', background: meta.color + '10' }}
                >
                  {mission.phase === 'complete' ? '✓' : '⚡'}
                </motion.div>
                <div>
                  <h2 className="font-display text-[20px] font-extrabold text-[#e0e0e0]">{mission.name}</h2>
                  <div className="text-[11px] text-white/20">{mission.agents.length} agents deployed · {new Date(mission.createdAt).toLocaleTimeString()}</div>
                </div>
              </div>

              <div className="ml-auto flex items-center gap-3">
                <motion.div
                  animate={mission.phase !== 'complete' ? { opacity: [1, 0.4, 1] } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="flex items-center gap-2 px-4 py-1.5 rounded-full text-[11px] font-semibold tracking-widest"
                  style={{ background: meta.color + '15', color: meta.color, border: `1px solid ${meta.color}20` }}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: meta.color }} />
                  {meta.label}
                </motion.div>

                <button
                  onClick={() => dispatch(closeMissionTheater())}
                  className="w-9 h-9 rounded-lg bg-void-3 border border-white/6 text-white/30 text-lg flex items-center justify-center hover:bg-void-4 hover:text-white/50 transition-all cursor-pointer"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="grid grid-cols-[1fr_340px] divide-x divide-white/5">
              {/* Left: Agents + Progress + Findings */}
              <div className="p-8 space-y-6 overflow-y-auto max-h-[calc(85vh-100px)]">
                {/* Agent Avatars */}
                <div>
                  <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-4">Deployed Agents</div>
                  <div className="flex gap-6 justify-center py-4">
                    {mission.agents.map((aid, i) => (
                      <AgentAvatar key={aid} agentId={aid} phase={mission.phase} delay={i} />
                    ))}
                  </div>
                </div>

                {/* Progress */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-[10px] text-white/12 uppercase tracking-[1.5px]">Mission Progress</div>
                    <div className="font-display text-[18px] font-bold" style={{ color: meta.color }}>
                      {Math.floor(mission.progress)}%
                    </div>
                  </div>
                  <ProgressBar progress={mission.progress} phase={mission.phase} />
                </div>

                {/* Findings */}
                <div>
                  <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-3">Live Findings</div>
                  <div className="grid grid-cols-4 gap-2">
                    {[
                      [mission.findings.parcels, 'Parcels', '#3b82f6'],
                      [mission.findings.clusters, 'Clusters', '#a855f7'],
                      [mission.findings.signals, 'Signals', '#00f0ff'],
                      [mission.findings.opportunities, 'Opportunities', '#00ff88'],
                    ].map(([val, label, color]) => (
                      <motion.div
                        key={label}
                        className="bg-void-2 rounded-xl p-4 text-center border border-white/4"
                        animate={val > 0 ? { borderColor: [color + '00', color + '30', color + '00'] } : {}}
                        transition={{ duration: 2, repeat: Infinity }}
                      >
                        <motion.div
                          key={val}
                          initial={{ scale: 1.3 }}
                          animate={{ scale: 1 }}
                          className="font-display text-[28px] font-extrabold"
                          style={{ color }}
                        >
                          {val}
                        </motion.div>
                        <div className="text-[9px] text-white/15 uppercase tracking-widest mt-1">{label}</div>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Quick Actions (post-complete) */}
                {mission.phase === 'complete' && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex gap-3"
                  >
                    <button
                      onClick={() => {
                        dispatch(closeMissionTheater());
                        dispatch(setActiveTab('clusters'));
                        dispatch(addToast({ icon: '💎', message: `${mission.findings.opportunities} opportunities ready for review` }));
                      }}
                      className="flex-1 py-3 bg-brass text-void-0 rounded-xl font-display font-bold text-[13px] cursor-pointer hover:bg-brass-bright hover:shadow-[0_0_20px_var(--color-brass-glow)] transition-all border-none"
                    >
                      View Opportunities
                    </button>
                    <button
                      onClick={() => dispatch(addToast({ icon: '📊', message: 'Mission report exported' }))}
                      className="flex-1 py-3 bg-void-3 text-white/40 rounded-xl font-display font-bold text-[13px] border border-white/8 cursor-pointer hover:border-brass-dim hover:text-brass transition-all"
                    >
                      Export Report
                    </button>
                    <button
                      onClick={() => dispatch(closeMissionTheater())}
                      className="flex-1 py-3 bg-void-3 text-white/40 rounded-xl font-display font-bold text-[13px] border border-white/8 cursor-pointer hover:border-brass-dim hover:text-brass transition-all"
                    >
                      Back to Map
                    </button>
                  </motion.div>
                )}
              </div>

              {/* Right: Live Log */}
              <div className="flex flex-col max-h-[calc(85vh-100px)]">
                <div className="px-5 py-3 border-b border-white/5 flex items-center gap-2 shrink-0">
                  <span className="text-[10px] text-white/12 uppercase tracking-[1.5px]">Agent Log</span>
                  <span className="ml-auto text-[10px] text-white/10 font-mono">{mission.logs.length} lines</span>
                </div>
                <div className="flex-1 overflow-y-auto p-4 font-mono text-[11px] leading-[1.8]">
                  {mission.logs.map((log, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`${LOG_COLORS[log.type] || 'text-white/30'} ${log.type === 'phase' ? 'font-bold mt-2 mb-1' : ''}`}
                    >
                      <span className="text-white/10 mr-2">
                        {new Date(log.time).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                      {log.text}
                    </motion.div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
