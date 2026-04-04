import { useEffect } from 'react'
import { X, FileText, Map, Rocket, AlertTriangle, CheckCircle, Clock, Activity } from 'lucide-react'
import type { Cluster } from '@/data/mockData'

interface ClusterDetailModalProps {
  cluster: Cluster
  onClose: () => void
}

const SIGNAL_DISPLAY: Record<string, { label: string; icon: typeof AlertTriangle; color: string }> = {
  high_vacancy: { label: 'High Vacancy Ratio', icon: AlertTriangle, color: 'text-amber-600' },
  roads_installed: { label: 'Infrastructure Invested', icon: CheckCircle, color: 'text-primary' },
  no_recent_activity: { label: 'No Recent Activity', icon: Clock, color: 'text-red-500' },
  plat_age: { label: 'Aged Plat (5+ years)', icon: Clock, color: 'text-on-surface-variant' },
  bonds_posted: { label: 'Bonds Posted', icon: Activity, color: 'text-primary' },
  permits_with_vacancy: { label: 'Permits Pulled + High Vacancy', icon: AlertTriangle, color: 'text-amber-600' },
}

export function ClusterDetailModal({ cluster, onClose }: ClusterDetailModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  const stallSignals = cluster.stallSignals ?? []
  const hasListings = (cluster.listingCount ?? 0) > 0
  const isStalled = cluster.opportunityType === 'stalled_subdivision'

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-on-surface/40 p-8 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="mt-[10vh] flex max-h-[80vh] w-full max-w-[960px] flex-col overflow-hidden rounded-[1.5rem] border border-white/20 bg-surface shadow-ambient-lg">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-surface-container-low bg-white p-8">
          <div>
            <div className="mb-1 flex items-center space-x-3">
              <h2 className="text-2xl font-bold tracking-tight capitalize">{cluster.owner}</h2>
              {isStalled && (
                <span className="rounded bg-amber-50 px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-amber-700">
                  STALLED
                </span>
              )}
              {hasListings && (
                <span className="rounded bg-green-50 px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-green-700">
                  {cluster.listingCount} LISTING{(cluster.listingCount ?? 0) > 1 ? 'S' : ''}
                </span>
              )}
              <span className="rounded bg-surface-container-low px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                TIER {cluster.tier}
              </span>
            </div>
            <p className="text-on-surface-variant">
              {cluster.lots} lots &bull; {cluster.acreage.toFixed(1)} acres &bull; {cluster.township}
              {cluster.subdivisionName ? ` &bull; ${cluster.subdivisionName}` : ''}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            title="Close"
            className="flex h-10 w-10 items-center justify-center rounded-full transition-colors hover:bg-surface-container-low"
          >
            <X className="h-5 w-5 text-on-surface-variant/50" />
          </button>
        </div>

        {/* Body — 3 columns */}
        <div className="hide-scrollbar grid flex-1 grid-cols-3 gap-0 overflow-y-auto bg-surface-container-low">
          {/* Column 1: Score & Evidence */}
          <div className="flex flex-col space-y-8 border-r border-outline-variant/15 p-8">
            <div className="flex items-center space-x-6">
              <div className="flex h-20 w-20 items-center justify-center rounded-full border border-primary/20 bg-white ring-8 ring-primary/5">
                <div className="text-center">
                  <span className="block text-2xl font-black leading-none text-primary">{cluster.score}</span>
                  <span className="text-[10px] font-bold uppercase text-on-surface-variant/50">Score</span>
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-on-surface">
                  {cluster.score >= 60 ? 'High Priority' : cluster.score >= 40 ? 'Medium Priority' : 'Monitor'}
                </p>
                <p className="text-[10px] font-semibold text-on-surface-variant">
                  Stall confidence: {Math.round((cluster.stallConfidence ?? 0) * 100)}%
                </p>
              </div>
            </div>

            {/* Stall evidence signals */}
            <div className="space-y-4">
              <h4 className="text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/50">
                Stall Evidence
              </h4>
              {stallSignals.length > 0 ? (
                <div className="space-y-3">
                  {stallSignals.map((signal) => {
                    const display = SIGNAL_DISPLAY[signal] ?? {
                      label: signal,
                      icon: Activity,
                      color: 'text-on-surface-variant',
                    }
                    const Icon = display.icon
                    return (
                      <div
                        key={signal}
                        className="flex items-center space-x-3 rounded-xl border border-surface-container-low bg-white p-3"
                      >
                        <Icon className={`h-4 w-4 flex-shrink-0 ${display.color}`} />
                        <span className="text-xs font-medium text-on-surface">{display.label}</span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <p className="text-xs text-on-surface-variant/60 italic">
                  No stall signals detected — this cluster is ranked on lot count, vacancy, and listing activity.
                </p>
              )}
            </div>

            {/* Infrastructure status */}
            <div className="space-y-3">
              <h4 className="text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/50">
                Infrastructure
              </h4>
              <div className={`flex items-center space-x-3 rounded-xl p-3 ${
                cluster.infrastructureInvested
                  ? 'border border-primary/20 bg-primary/5'
                  : 'border border-surface-container-low bg-white'
              }`}>
                <CheckCircle className={`h-4 w-4 ${cluster.infrastructureInvested ? 'text-primary' : 'text-on-surface-variant/30'}`} />
                <span className={`text-xs font-medium ${cluster.infrastructureInvested ? 'text-primary' : 'text-on-surface-variant/60'}`}>
                  {cluster.infrastructureInvested ? 'Roads / Utilities Invested' : 'No infrastructure evidence'}
                </span>
              </div>
            </div>
          </div>

          {/* Column 2: Metrics & Parcel Data */}
          <div className="border-r border-outline-variant/15 bg-white p-8">
            <h4 className="mb-6 text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/50">
              Acquisition Metrics
            </h4>
            <div className="space-y-4">
              <div className="flex justify-between border-b border-surface-container pb-2">
                <span className="text-sm text-on-surface-variant">Total Lots</span>
                <span className="text-sm font-bold">{cluster.lots}</span>
              </div>
              <div className="flex justify-between border-b border-surface-container pb-2">
                <span className="text-sm text-on-surface-variant">Total Acreage</span>
                <span className="text-sm font-bold">{cluster.acreage.toFixed(1)} ac</span>
              </div>
              <div className="flex justify-between border-b border-surface-container pb-2">
                <span className="text-sm text-on-surface-variant">Vacancy Ratio</span>
                <span className="text-sm font-bold">
                  {cluster.vacancyRatio != null ? `${Math.round(cluster.vacancyRatio * 100)}%` : '—'}
                </span>
              </div>
              <div className="flex justify-between border-b border-surface-container pb-2">
                <span className="text-sm text-on-surface-variant">Active Listings</span>
                <span className={`text-sm font-bold ${hasListings ? 'text-primary' : ''}`}>
                  {cluster.listingCount ?? 0}
                </span>
              </div>
              <div className="flex justify-between border-b border-surface-container pb-2">
                <span className="text-sm text-on-surface-variant">BBO Signals</span>
                <span className="text-sm font-bold">{cluster.bboSignalCount ?? 0}</span>
              </div>
              <div className="flex justify-between border-b border-surface-container pb-2">
                <span className="text-sm text-on-surface-variant">Parcels Tracked</span>
                <span className="text-sm font-bold">{cluster.parcelCount ?? cluster.lots}</span>
              </div>
            </div>

            {/* Opportunity type context */}
            <div className="-mx-8 mt-8 border-l-4 border-primary bg-primary/5 px-8 py-6">
              <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">
                Opportunity Type
              </p>
              <p className="text-sm font-bold text-on-surface capitalize">
                {(cluster.opportunityType ?? 'unknown').replace(/_/g, ' ')}
              </p>
              <p className="mt-2 text-xs text-on-surface-variant leading-relaxed">
                {isStalled
                  ? 'This is a platted subdivision with high vacancy and infrastructure invested. The developer may have stalled — acquisition opportunity for attainable housing.'
                  : hasListings
                  ? 'Active listings detected on this cluster. Contact the listing agent(s) to explore bulk acquisition or off-market negotiation.'
                  : 'Large dormant cluster with no current listing activity. May require direct owner outreach.'}
              </p>
            </div>
          </div>

          {/* Column 3: Action Queue */}
          <div className="flex flex-col space-y-8 p-8">
            <h4 className="text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/50">
              Next Actions
            </h4>

            {/* Listing agents */}
            {hasListings && cluster.listingAgents && cluster.listingAgents.length > 0 && (
              <div className="space-y-3">
                <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">
                  Contact These Agents
                </p>
                {cluster.listingAgents.map((agent, i) => (
                  <div key={i} className="flex items-center justify-between rounded-xl border border-surface-container-low bg-white p-3">
                    <span className="text-xs font-medium text-on-surface">{agent}</span>
                    <span className="text-[9px] font-bold text-primary uppercase">Reach Out</span>
                  </div>
                ))}
              </div>
            )}

            {/* Action items based on opportunity state */}
            <div className="space-y-3">
              <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">
                Recommended Steps
              </p>
              <div className="space-y-2">
                {isStalled && (
                  <>
                    <ActionStep number={1} text="Verify plat recording at Washtenaw Register of Deeds" />
                    <ActionStep number={2} text="Check infrastructure bond status with township" />
                    <ActionStep number={3} text="Identify current lot owner(s) via title search" />
                    <ActionStep number={4} text="Draft acquisition outreach" />
                  </>
                )}
                {!isStalled && hasListings && (
                  <>
                    <ActionStep number={1} text="Contact listing agent for package pricing" />
                    <ActionStep number={2} text="Request lot-by-lot breakdown and survey" />
                    <ActionStep number={3} text="Run comparable analysis on nearby sales" />
                    <ActionStep number={4} text="Evaluate site fit for BaseMod home models" />
                  </>
                )}
                {!isStalled && !hasListings && (
                  <>
                    <ActionStep number={1} text="Research owner via county assessor records" />
                    <ActionStep number={2} text="Check for any pending development applications" />
                    <ActionStep number={3} text="Draft cold outreach to owner" />
                    <ActionStep number={4} text="Evaluate zoning compatibility" />
                  </>
                )}
              </div>
            </div>

            {/* Coordinate info */}
            {cluster.position && (
              <div className="mt-auto rounded-xl bg-surface-container-low p-4">
                <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/50">
                  Location
                </p>
                <p className="text-xs font-medium text-on-surface tabular-nums">
                  {cluster.position[0].toFixed(5)}, {cluster.position[1].toFixed(5)}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-surface-container-low bg-white p-6">
          <div className="flex space-x-2">
            <button type="button" className="flex items-center rounded-lg border border-outline-variant/20 px-5 py-2.5 text-xs font-bold text-on-surface-variant transition-colors hover:bg-surface-container-low">
              <FileText className="mr-2 h-4 w-4" />
              Generate Broker Note
            </button>
          </div>
          <div className="flex space-x-3">
            <button type="button" className="flex items-center rounded-lg px-5 py-2.5 text-xs font-bold text-primary transition-colors hover:bg-primary/5">
              <Map className="mr-2 h-4 w-4" />
              View on Map
            </button>
            <button
              type="button"
              className="flex items-center rounded-lg px-6 py-2.5 text-xs font-bold text-white shadow-md transition-transform hover:scale-[1.02] copper-gradient"
            >
              <Rocket className="mr-2 h-4 w-4" />
              Move to Pipeline
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function ActionStep({ number, text }: { number: number; text: string }) {
  return (
    <div className="flex items-start space-x-3 rounded-lg bg-white p-3">
      <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary">
        {number}
      </span>
      <span className="text-xs text-on-surface-variant leading-relaxed">{text}</span>
    </div>
  )
}
