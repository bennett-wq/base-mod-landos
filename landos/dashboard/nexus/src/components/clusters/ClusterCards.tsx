import { motion } from 'framer-motion'
import { ScoreRing } from './ScoreRing'
import { useClusters } from '@/hooks/useClusters'
import { Skeleton } from '@/components/shared/Skeleton'
import type { Cluster, Tier } from '@/data/mockData'

const TIER_STYLES: Record<Tier, string> = {
  A: 'bg-primary text-white',
  B: 'bg-outline text-white',
  C: 'bg-surface-container-highest text-on-surface-variant',
}

const SIGNAL_LABELS: Record<string, string> = {
  high_vacancy: 'High Vacancy',
  roads_installed: 'Infrastructure Invested',
  no_recent_activity: 'No Recent Activity',
  plat_age: 'Aged Plat',
  bonds_posted: 'Bonds Posted',
  permits_with_vacancy: 'Permits + Vacancy',
}

function EvidenceTag({ signal }: { signal: string }) {
  const label = SIGNAL_LABELS[signal] ?? signal
  const isInfra = signal === 'roads_installed'
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider ${
        isInfra
          ? 'bg-primary/10 text-primary'
          : 'bg-surface-container-low text-on-surface-variant'
      }`}
    >
      {label}
    </span>
  )
}

interface ClusterCardsProps {
  onViewIntel: (cluster: Cluster) => void
}

export function ClusterCards({ onViewIntel }: ClusterCardsProps) {
  const { data: clusters, isLoading } = useClusters()

  return (
    <section className="flex w-1/2 flex-col overflow-y-auto bg-surface p-8 hide-scrollbar">
      {/* Header */}
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-on-surface">Deep Cluster Intelligence</h2>
          <p className="mt-1 text-sm text-on-surface-variant">
            Found {clusters?.length ?? 0} high-probability clusters in Washtenaw County
          </p>
        </div>
        <button className="rounded-lg border border-primary/20 px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-primary transition-colors hover:bg-primary/5">
          Sort by: Score
        </button>
      </div>

      {/* Cards */}
      <div className="space-y-6">
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} height="300px" className="rounded-[1.25rem]" />
            ))
          : clusters?.map((cluster, i) => {
              const isFeatured = i === 0
              const hasStallEvidence = (cluster.stallSignals?.length ?? 0) > 0
              const hasListings = (cluster.listingCount ?? 0) > 0
              return (
                <motion.article
                  key={cluster.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08, duration: 0.3 }}
                  className={
                    isFeatured
                      ? 'group relative overflow-hidden rounded-[1.25rem] border border-outline-variant/30 border-l-4 border-l-primary bg-surface-container-lowest p-7 shadow-sm transition-shadow duration-200 hover:shadow-md'
                      : 'group relative overflow-hidden rounded-[1.25rem] border border-outline-variant/30 bg-surface-container-lowest p-7 shadow-sm opacity-90 transition-all duration-200 hover:opacity-100 hover:shadow-md'
                  }
                >
                  {/* Tier badge */}
                  <div className={`absolute right-0 top-0 rounded-bl-xl px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest ${TIER_STYLES[cluster.tier]}`}>
                    Tier {cluster.tier}{cluster.tier === 'A' ? ' Priority' : ''}
                  </div>

                  {/* Top row */}
                  <div className="mb-5 flex items-start justify-between">
                    <div className="space-y-1">
                      <h3 className="text-lg font-bold leading-none text-on-surface capitalize">{cluster.owner}</h3>
                      <p className="text-sm text-on-surface-variant">
                        {cluster.township} &bull; {cluster.lots} lots &bull; {cluster.acreage.toFixed(1)} acres
                      </p>
                    </div>
                    <ScoreRing score={cluster.score} size={64} />
                  </div>

                  {/* Stats row — real data */}
                  <div className="mb-5 grid grid-cols-4 gap-4 border-y border-surface-container-low py-4">
                    <div>
                      <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">Lots</p>
                      <p className="text-sm font-bold text-on-surface">{cluster.lots}</p>
                    </div>
                    <div>
                      <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">Acreage</p>
                      <p className="text-sm font-bold text-on-surface">{cluster.acreage.toFixed(1)} ac</p>
                    </div>
                    <div>
                      <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">Vacancy</p>
                      <p className="text-sm font-bold text-on-surface">
                        {cluster.vacancyRatio != null ? `${Math.round(cluster.vacancyRatio * 100)}%` : '—'}
                      </p>
                    </div>
                    <div>
                      <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">Listings</p>
                      <p className={`text-sm font-bold ${hasListings ? 'text-primary' : 'text-on-surface'}`}>
                        {cluster.listingCount ?? 0} active
                      </p>
                    </div>
                  </div>

                  {/* Stall evidence tags */}
                  {hasStallEvidence && (
                    <div className="mb-5">
                      <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">
                        Stall Evidence ({Math.round((cluster.stallConfidence ?? 0) * 100)}% confidence)
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {cluster.stallSignals!.map((signal) => (
                          <EvidenceTag key={signal} signal={signal} />
                        ))}
                        {cluster.infrastructureInvested && !cluster.stallSignals?.includes('roads_installed') && (
                          <EvidenceTag signal="roads_installed" />
                        )}
                      </div>
                    </div>
                  )}

                  {/* Listing agents — who is active on this cluster */}
                  {hasListings && cluster.listingAgents && cluster.listingAgents.length > 0 && (
                    <div className="mb-5">
                      <p className="mb-1.5 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">
                        Active Agents
                      </p>
                      <p className="text-xs text-on-surface-variant">
                        {cluster.listingAgents.join(', ')}
                      </p>
                    </div>
                  )}

                  {/* Supply type + opportunity type */}
                  <div className="mb-6 flex items-center gap-2">
                    <span className={`rounded px-2.5 py-1 text-[9px] font-bold uppercase tracking-wider ${
                      cluster.supplyType === 'STALLED' ? 'bg-amber-50 text-amber-700'
                        : cluster.supplyType === 'ACTIVE' ? 'bg-green-50 text-green-700'
                        : cluster.supplyType === 'DORMANT' ? 'bg-red-50 text-red-700'
                        : 'bg-surface-container-low text-on-surface-variant'
                    }`}>
                      {cluster.supplyType}
                    </span>
                    {cluster.opportunityType && (
                      <span className="rounded px-2.5 py-1 text-[9px] font-bold uppercase tracking-wider bg-surface-container-low text-on-surface-variant">
                        {cluster.opportunityType.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>

                  {/* CTA */}
                  <button
                    onClick={() => onViewIntel(cluster)}
                    className="flex w-full items-center justify-center rounded-lg py-3 text-xs font-bold text-white shadow-sm transition-opacity hover:opacity-90 active:scale-[0.98]"
                    style={{ background: 'linear-gradient(155deg, #7f5313 0%, #9b6b2a 100%)' }}
                  >
                    View Full Intel
                    <svg className="ml-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                  </button>
                </motion.article>
              )
            })}
      </div>
    </section>
  )
}
