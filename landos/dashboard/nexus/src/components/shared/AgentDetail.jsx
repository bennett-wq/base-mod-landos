import { useState, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { closeAgentDetail } from '../../store/uiSlice';
import { motion, AnimatePresence } from 'framer-motion';

const RESPONSES = [
  'Processing. All rules evaluated. Systems nominal.',
  'Rescan running across active rules. Results propagating.',
  'New wake instructions generated. Priority: IMMEDIATE.',
  'Convergence points found. Routing to opportunity engine.',
  'BBO signal check complete. Fatigue indicators detected.',
];

export default function AgentDetail() {
  const dispatch = useDispatch();
  const { agentDetailOpen, selectedAgent } = useSelector(s => s.ui);
  const agents = useSelector(s => s.mesh.agents);
  const rules = useSelector(s => s.mesh.rules);
  const agent = agents.find(a => a.id === selectedAgent);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const msgsRef = useRef(null);

  const send = () => {
    if (!input.trim()) return;
    const newMsgs = [...messages, { from: 'user', text: input }];
    setInput('');
    setMessages(newMsgs);
    setTimeout(() => {
      setMessages(prev => [...prev, { from: 'agent', text: RESPONSES[Math.floor(Math.random() * RESPONSES.length)] }]);
      msgsRef.current?.scrollTo(0, msgsRef.current.scrollHeight);
    }, 600 + Math.random() * 800);
  };

  if (!agent) return null;

  return (
    <AnimatePresence>
      {agentDetailOpen && (
        <div className="fixed inset-0 z-[500]">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-void-0/50"
            onClick={() => dispatch(closeAgentDetail())}
          />
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            className="absolute top-0 right-0 bottom-0 w-[500px] bg-void-1 border-l border-white/6 shadow-[-20px_0_60px_rgba(0,0,0,0.5)] overflow-y-auto p-7"
          >
            <button
              onClick={() => dispatch(closeAgentDetail())}
              className="absolute top-3.5 right-3.5 w-8 h-8 rounded-md bg-void-3 border border-white/6 text-white/30 text-lg flex items-center justify-center hover:bg-void-4 hover:text-white/50 transition-all cursor-pointer"
            >
              ×
            </button>

            <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl bg-void-3 border border-white/6 mb-3" style={{ borderColor: agent.color + '30' }}>
              {agent.icon}
            </div>
            <h2 className="font-display text-[22px] font-extrabold text-[#e0e0e0] mb-1">{agent.name}</h2>
            <p className="text-[12px] text-white/22 mb-5 leading-relaxed">{agent.description}</p>

            {/* Stats */}
            <div className="mb-5">
              <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-2 pb-1.5 border-b border-white/4">Performance</div>
              <div className="grid grid-cols-2 gap-2">
                {[
                  [agent.stats.events.toLocaleString(), 'Events'],
                  [agent.stats.rules, 'Rules Fired'],
                  [agent.stats.wake, 'Last Wake'],
                  [agent.wakeTypes.join(', '), 'Wake Types'],
                ].map(([val, label]) => (
                  <div key={label} className="p-2 px-3 bg-void-2 rounded-md">
                    <div className="font-display text-[18px] font-bold text-brass-bright">{val}</div>
                    <div className="text-[10px] text-white/17">{label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Rules */}
            <div className="mb-5">
              <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-2 pb-1.5 border-b border-white/4">Active Rules</div>
              {agent.rules.map(rid => {
                const rule = rules.find(r => r.id === rid);
                if (!rule) return null;
                const heat = rule.fires > 5 ? 'hot' : rule.fires > 0 ? 'warm' : 'cold';
                const heatStyles = { hot: 'bg-nexus-crimson/15 text-nexus-crimson', warm: 'bg-nexus-amber/15 text-nexus-amber', cold: 'bg-white/4 text-white/12' };
                return (
                  <div key={rid} className="flex items-center gap-2 py-1.5 px-2.5 rounded bg-void-2 mb-1 text-[11px]">
                    <span className="font-semibold text-brass w-8">{rule.id}</span>
                    <span className="flex-1 text-white/28">{rule.name}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded ${heatStyles[heat]}`}>{heat.toUpperCase()}</span>
                  </div>
                );
              })}
            </div>

            {/* Chat */}
            <div className="mb-5">
              <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-2 pb-1.5 border-b border-white/4">Agent Chat</div>
              <div className="bg-void-2 rounded-lg p-3">
                <div ref={msgsRef} className="max-h-[180px] overflow-y-auto mb-2 space-y-1.5">
                  <div className="py-1.5 px-2.5 rounded-lg text-[12px] bg-void-3 text-white/45 mr-[20%]">
                    {agent.name} ready. Monitoring {agent.rules.length} rules. Last scan {agent.stats.wake} ago.
                  </div>
                  {messages.map((m, i) => (
                    <div key={i} className={`py-1.5 px-2.5 rounded-lg text-[12px] ${m.from === 'user' ? 'bg-brass-glow text-brass-bright ml-[20%] border border-white/5' : 'bg-void-3 text-white/45 mr-[20%]'}`}>
                      {m.text}
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && send()}
                    className="flex-1 bg-void-3 border border-white/6 rounded-md px-3 py-2 text-[#e0e0e0] font-mono text-[12px] outline-none focus:border-brass-dim transition-colors"
                    placeholder={`Message ${agent.name}...`}
                  />
                  <button onClick={send} className="px-4 py-2 bg-brass text-void-0 border-none rounded-md font-mono text-[11px] font-semibold cursor-pointer hover:bg-brass-bright hover:shadow-[0_0_12px_var(--color-brass-glow)] transition-all">
                    Send
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
