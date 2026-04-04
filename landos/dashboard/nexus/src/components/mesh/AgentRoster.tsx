import { useAgents } from '@/hooks/useAgents'
import { Skeleton } from '@/components/shared/Skeleton'
import type { AgentStatus } from '@/data/mockData'

const STATUS_CONFIG: Record<AgentStatus, { color: string; labelColor: string; label: string; pulse?: boolean }> = {
  ACTIVE:   { color: 'bg-success',  labelColor: 'text-success',  label: 'SCANNING', pulse: false },
  PULSING:  { color: 'bg-primary',  labelColor: 'text-primary',  label: 'PULSING',  pulse: true },
  IDLE:     { color: 'bg-outline',  labelColor: 'text-on-surface-variant/50', label: 'IDLE' },
  COOLDOWN: { color: 'bg-warning',  labelColor: 'text-warning',  label: 'COOLDOWN' },
}

export function AgentRoster() {
  const { data: agents, isLoading } = useAgents()

  return (
    <section className="w-[240px] shrink-0 flex flex-col p-4 space-y-3 overflow-y-auto bg-surface-container-low">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[9px] font-bold tracking-[0.12em] text-on-surface-variant/60 uppercase">
          Active Agents
        </span>
        <span className="text-[9px] font-semibold bg-primary/10 text-primary rounded-full px-2.5 py-0.5 tabular-nums">
          {agents ? `${String(agents.length).padStart(2, '0')}/${String(agents.length).padStart(2, '0')}` : '—'}
        </span>
      </div>
      <div className="space-y-2">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} height="56px" className="rounded-xl" />
            ))
          : agents?.map((agent, i) => {
              const config = STATUS_CONFIG[agent.status]
              const isReduced = agent.status === 'IDLE' || agent.status === 'COOLDOWN'
              return (
                <div
                  key={agent.name}
                  className={`group p-3.5 bg-surface-container-lowest rounded-xl shadow-ambient-sm hover:shadow-ambient transition-all duration-200 cursor-pointer ${
                    isReduced ? 'opacity-70' : ''
                  }`}
                  style={{ animationDelay: `${i * 50}ms` }}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-on-surface group-hover:text-primary transition-colors">
                      {agent.name}
                    </span>
                    <div
                      className={`w-2 h-2 rounded-full ${config.color} ${config.pulse ? 'agent-pulse' : ''}`}
                    />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-on-surface-variant/60 tabular-nums">{agent.events}</span>
                    <span className={`text-[9px] font-bold uppercase tracking-tight ${config.labelColor}`}>
                      {config.label}
                    </span>
                  </div>
                </div>
              )
            })}
      </div>
    </section>
  )
}
