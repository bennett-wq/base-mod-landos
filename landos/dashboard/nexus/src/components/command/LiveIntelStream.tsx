import { useState } from 'react'
import { UserCheck, MoreVertical } from 'lucide-react'
import { useCommandSignals, useTriggerRules } from '@/hooks/useSignals'
import { Skeleton } from '@/components/shared/Skeleton'

type Tab = 'SIGNALS' | 'RULES'

export function LiveIntelStream() {
  const [activeTab, setActiveTab] = useState<Tab>('SIGNALS')
  const { data: signals, isLoading: signalsLoading } = useCommandSignals()
  const { data: rules, isLoading: rulesLoading } = useTriggerRules()

  const tabs: Tab[] = ['SIGNALS', 'RULES']

  return (
    <section className="w-[320px] shrink-0 bg-white border-l border-outline-variant/10 flex flex-col overflow-hidden z-40">
      {/* Header */}
      <div className="px-4 py-4 border-b border-outline-variant/10">
        <h2 className="text-[10px] font-bold tracking-[0.2em] text-on-surface uppercase mb-4">
          Live Intel Stream
        </h2>
        <div className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-1 text-[10px] font-bold transition-colors ${
                activeTab === tab
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-on-surface-variant/40 hover:text-on-surface-variant'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Feed content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'SIGNALS' && (
          <>
            {signalsLoading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} height="140px" className="rounded-xl" />
                ))
              : signals?.map((signal, i) => (
                  <div
                    key={i}
                    className="p-4 bg-surface-container-low/50 rounded-xl border border-outline-variant/10 shadow-sm relative group overflow-hidden"
                  >
                    <div className="absolute top-0 right-0 p-2 opacity-30 group-hover:opacity-100 transition-opacity">
                      <MoreVertical size={12} />
                    </div>
                    <div className="flex justify-between items-start mb-2">
                      <span
                        className={`text-[9px] font-extrabold px-2 py-0.5 rounded tracking-tighter ${signal.typeColor}`}
                      >
                        {signal.type}
                      </span>
                      <span className="text-[9px] text-on-surface-variant/50 font-mono">
                        {signal.timestamp}
                      </span>
                    </div>
                    <p className="text-sm font-bold text-on-surface">{signal.title}</p>
                    <p className="text-xs text-on-surface-variant mt-1 mb-4 leading-relaxed">
                      {signal.description}
                    </p>
                    <button className="w-full py-2 bg-white border border-primary/20 rounded-lg flex items-center justify-center gap-2 hover:bg-primary/5 transition-colors">
                      <UserCheck size={14} className="text-primary" />
                      <span className="text-[10px] font-bold text-primary uppercase">
                        {signal.action}
                      </span>
                    </button>
                  </div>
                ))}

            {/* Swarm Autonomy card */}
            <div className="p-4 bg-primary/5 rounded-xl border border-primary/10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold text-primary uppercase">
                  Swarm Autonomy
                </span>
                <span className="text-[10px] font-bold text-primary">82%</span>
              </div>
              <div className="w-full h-1.5 bg-primary/10 rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full" style={{ width: '82%' }} />
              </div>
              <p className="text-[9px] text-on-surface-variant mt-2">
                Autonomous decision threshold
              </p>
            </div>
          </>
        )}

        {activeTab === 'RULES' &&
          (rulesLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} height="80px" className="rounded-xl" />
              ))
            : rules?.map((rule, i) => (
                <div
                  key={i}
                  className="p-4 bg-surface-container-lowest rounded-xl border border-outline-variant/10 shadow-sm"
                >
                  <span className="text-[10px] font-bold text-on-surface-variant uppercase">
                    Rule: {rule.name}
                  </span>
                  <div className="flex items-center justify-between text-[10px] mt-3 mb-1.5">
                    <span className="text-on-surface-variant">{rule.description}</span>
                    <span className="font-bold text-primary">{rule.progress}%</span>
                  </div>
                  <div className="w-full bg-surface-container-low h-1 rounded-full overflow-hidden">
                    <div
                      className="bg-primary h-full transition-all rounded-full"
                      style={{ width: `${rule.progress}%` }}
                    />
                  </div>
                </div>
              )))}
      </div>
    </section>
  )
}
