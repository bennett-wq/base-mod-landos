import { useAgents } from '@/hooks/useAgents'
import { Skeleton } from '@/components/shared/Skeleton'
import type { AgentStatus } from '@/data/mockData'

const STATUS_CONFIG: Record<AgentStatus, { color: string; labelColor: string; pulse?: boolean }> = {
  ACTIVE: { color: 'bg-[#059669]', labelColor: 'text-[#059669]' },
  PULSING: { color: 'bg-primary', labelColor: 'text-primary', pulse: true },
  IDLE: { color: 'bg-[#9CA3AF]', labelColor: 'text-on-surface-variant/50' },
  COOLDOWN: { color: 'bg-[#D97706]', labelColor: 'text-[#D97706]' },
}

export function AgentRoster() {
  const { data: agents, isLoading } = useAgents()

  return (
    <section className="w-[240px] shrink-0 flex flex-col p-4 space-y-4 overflow-y-auto bg-surface-container-low">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase">
          Active Agents
        </span>
        <span className="text-[9px] font-medium bg-primary/10 text-primary rounded-full px-2 py-0.5">
          {agents ? `${String(agents.length).padStart(2, '0')}/${String(agents.length).padStart(2, '0')}` : '—'}
        </span>
      </div>
      <div className="space-y-2">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} height="60px" className="rounded-xl" />
            ))
          : agents?.map((agent) => {
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
