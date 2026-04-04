import { MessageCircle } from 'lucide-react'
import { useAgentsExpanded } from '@/hooks/useAgents'
import { Skeleton } from '@/components/shared/Skeleton'
import type { AgentStatus } from '@/data/mockData'

const STATUS_DOT: Record<AgentStatus, string> = {
  ACTIVE: 'bg-[#059669]',
  PULSING: 'bg-primary agent-pulse',
  IDLE: 'bg-[#9CA3AF]',
  COOLDOWN: 'bg-[#D97706]',
}

export function AgentRosterExpanded() {
  const { data: agents, isLoading } = useAgentsExpanded()
  const activeCount = agents?.filter((a) => a.status !== 'IDLE').length ?? 0

  return (
    <section className="w-[300px] shrink-0 flex flex-col p-4 space-y-4 overflow-y-auto bg-surface-container-low/50">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-bold tracking-widest text-on-surface-variant uppercase">
          Command Swarm
        </span>
        <span className="text-[10px] font-medium text-on-surface-variant/60">
          ACTIVE: {String(activeCount).padStart(2, '0')}
        </span>
      </div>

      <div className="space-y-3">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} height="80px" className="rounded-xl" />
            ))
          : agents?.map((agent) => {
              const isExpanded = agent.status !== 'IDLE'
              return isExpanded ? (
                <div
                  key={agent.name}
                  className="p-4 bg-white rounded-xl shadow-ambient-sm hover:shadow-ambient transition-all duration-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-on-surface">{agent.name}</span>
                    <div className={`w-2 h-2 rounded-full ${STATUS_DOT[agent.status]}`} />
                  </div>
                  <p className="text-[11px] text-on-surface-variant/80 mb-3 leading-relaxed line-clamp-2">
                    <span className="font-bold text-primary">STATUS:</span> {agent.statusText}
                  </p>
                  <div className="flex gap-2">
                    <button className="flex-1 py-1.5 bg-surface-container-low hover:bg-primary/5 text-[10px] font-bold text-primary rounded-lg border border-primary/10 transition-colors uppercase tracking-tight">
                      Schedule
                    </button>
                    <button className="px-2 py-1.5 bg-surface-container-low hover:bg-primary/5 text-primary rounded-lg border border-primary/10 transition-colors">
                      <MessageCircle size={14} />
                    </button>
                  </div>
                </div>
              ) : (
                <div
                  key={agent.name}
                  className="p-3 bg-white/60 rounded-xl border border-outline-variant/10 opacity-70"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-on-surface">{agent.name}</span>
                    <span className="text-[9px] font-bold text-on-surface-variant/40">IDLE</span>
                  </div>
                </div>
              )
            })}
      </div>
    </section>
  )
}
