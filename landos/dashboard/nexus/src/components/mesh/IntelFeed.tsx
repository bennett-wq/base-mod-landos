import { useState } from 'react'
import { motion } from 'framer-motion'
import { ExternalLink } from 'lucide-react'
import { useSignals } from '@/hooks/useSignals'
import { useClusterSummaries } from '@/hooks/useClusters'
import { Skeleton } from '@/components/shared/Skeleton'
import { TRIGGER_RULES } from '@/data/mockData'

type Tab = 'SIGNALS' | 'RULES' | 'CLUSTERS'

export function IntelFeed() {
  const [activeTab, setActiveTab] = useState<Tab>('SIGNALS')
  const { data: signals, isLoading: signalsLoading } = useSignals()
  const { data: clusterSummaries, isLoading: clustersLoading } = useClusterSummaries()

  const tabs: Tab[] = ['SIGNALS', 'RULES', 'CLUSTERS']

  return (
    <section className="w-[320px] shrink-0 bg-surface-container-low flex flex-col overflow-hidden">
      {/* Tab bar */}
      <div className="flex">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-4 text-[10px] font-bold tracking-[0.1em] transition-all duration-200 ${
              activeTab === tab
                ? 'text-primary border-b-2 border-primary'
                : 'text-on-surface-variant/40 border-b-2 border-transparent hover:text-on-surface-variant'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Feed content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {activeTab === 'SIGNALS' &&
          (signalsLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} height="120px" className="rounded-xl" />
              ))
            : signals?.map((signal, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06, duration: 0.25 }}
                  className="group p-4 bg-surface-container-lowest rounded-xl shadow-ambient-sm hover:shadow-ambient transition-all duration-200"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[9px] font-bold bg-primary/8 text-primary px-2 py-0.5 rounded-md tracking-tight">
                      {signal.type}
                    </span>
                    <span className="text-[9px] text-on-surface-variant/40 tabular-nums">{signal.timestamp}</span>
                  </div>
                  <p className="text-xs font-bold text-on-surface leading-snug">{signal.title}</p>
                  <p className="text-[11px] text-on-surface-variant mt-1 leading-relaxed">
                    {signal.description}
                  </p>
                  <div className="mt-3 flex items-center justify-between pt-3">
                    <div className="flex items-center gap-1.5">
                      <div
                        className={`w-1.5 h-1.5 rounded-full ${signal.tier === 1 ? 'bg-primary' : 'bg-on-surface-variant/30'}`}
                      />
                      <span
                        className={`text-[9px] font-bold tracking-tight ${signal.tier === 1 ? 'text-primary' : 'text-on-surface-variant/50'}`}
                      >
                        TIER {signal.tier}
                      </span>
                    </div>
                    <ExternalLink size={11} className="text-on-surface-variant/30 group-hover:text-primary transition-colors" />
                  </div>
                </motion.div>
              )))}

        {activeTab === 'RULES' &&
          TRIGGER_RULES.map((rule, i) => (
            <div
              key={i}
              className="p-4 bg-surface-container-lowest rounded-xl shadow-ambient-sm"
            >
              <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-tight">
                Rule: {rule.name}
              </span>
              <div className="flex items-center justify-between text-[10px] mt-3 mb-1.5">
                <span className="text-on-surface-variant/70">{rule.description}</span>
                <span className="font-bold text-primary tabular-nums">{rule.progress}%</span>
              </div>
              <div className="w-full bg-surface-container-low h-1 rounded-full overflow-hidden">
                <div
                  className="bg-primary h-full rounded-full transition-all duration-500"
                  style={{ width: `${rule.progress}%` }}
                />
              </div>
            </div>
          ))}

        {activeTab === 'CLUSTERS' && (
          <div className="space-y-2">
            <span className="text-[9px] font-bold text-on-surface-variant/40 uppercase tracking-[0.12em] px-1">
              Top Clusters
            </span>
            {clustersLoading
              ? Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} height="56px" className="rounded-xl" />
                ))
              : clusterSummaries?.map((cluster, i) => (
                  <div
                    key={i}
                    className="p-3.5 bg-surface-container-lowest rounded-xl shadow-ambient-sm hover:shadow-ambient transition-all duration-200 cursor-pointer"
                  >
                    <div className="flex justify-between">
                      <span className="text-xs font-bold text-on-surface">{cluster.name}</span>
                      <span className="text-xs font-bold text-primary tabular-nums">{cluster.lots} lots</span>
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-[10px] text-on-surface-variant/60 uppercase tracking-tight">
                        {cluster.type}
                      </span>
                      <span className="text-[10px] text-on-surface-variant/50">{cluster.location}</span>
                    </div>
                  </div>
                ))}
          </div>
        )}
      </div>
    </section>
  )
}
