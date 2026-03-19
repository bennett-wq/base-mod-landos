const AGENTS = [
  { name: 'Supply Intel', status: 'ACTIVE' as const, events: '42.4k events' },
  { name: 'Municipal Intel', status: 'PULSING' as const, events: '12.1k events' },
  { name: 'Demographic Agt', status: 'ACTIVE' as const, events: '8.2k events' },
  { name: 'Zoning Auditor', status: 'IDLE' as const, events: '3.4k events' },
  { name: 'Risk Engine', status: 'ACTIVE' as const, events: '6.1k events' },
  { name: 'Permit Tracker', status: 'COOLDOWN' as const, events: '1.8k events' },
  { name: 'GIS Liaison', status: 'ACTIVE' as const, events: '1.2k events' },
  { name: 'Macro Harvester', status: 'IDLE' as const, events: '892 events' },
] as const

type AgentStatus = 'ACTIVE' | 'PULSING' | 'IDLE' | 'COOLDOWN'

const STATUS_CONFIG: Record<AgentStatus, { color: string; labelColor: string; pulse?: boolean }> = {
  ACTIVE: { color: 'bg-[#059669]', labelColor: 'text-[#059669]' },
  PULSING: { color: 'bg-primary', labelColor: 'text-primary', pulse: true },
  IDLE: { color: 'bg-[#9CA3AF]', labelColor: 'text-on-surface-variant/50' },
  COOLDOWN: { color: 'bg-[#D97706]', labelColor: 'text-[#D97706]' },
}

export function AgentRoster() {
  return (
    <section className="w-[240px] shrink-0 flex flex-col p-4 space-y-4 overflow-y-auto bg-surface-container-low">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase">
          Active Agents
        </span>
        <span className="text-[9px] font-medium bg-primary/10 text-primary rounded-full px-2 py-0.5">
          08/08
        </span>
      </div>
      <div className="space-y-2">
        {AGENTS.map((agent) => {
          const config = STATUS_CONFIG[agent.status]
          const isReduced = agent.status === 'IDLE' || agent.status === 'COOLDOWN'
          return (
            <div
              key={agent.name}
              className={`p-3 bg-surface-container-lowest rounded-xl border border-outline-variant/10 shadow-sm hover:border-primary/30 transition-all cursor-pointer ${isReduced ? 'opacity-80' : ''}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-on-surface">{agent.name}</span>
                <div
                  className={`w-2 h-2 rounded-full ${config.color} ${config.pulse ? 'agent-pulse' : ''}`}
                />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-on-surface-variant">{agent.events}</span>
                <span className={`text-[10px] font-medium uppercase ${config.labelColor}`}>
                  {agent.status === 'ACTIVE' ? 'SCANNING' : agent.status}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
