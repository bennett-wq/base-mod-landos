import { useState } from 'react'
import { Search, Mail, ChevronRight, CheckCircle, AlertTriangle } from 'lucide-react'
import { usePipelineMutation } from '@/hooks/usePipeline'
import { PIPELINE_STAGES, type PipelineStageName } from '@/stores/pipelineStore'

export interface Deal {
  id: string
  title: string
  tier?: number
  entityType?: string
  location?: string
  lotCount?: number
  score?: number
  signal?: string
  updatedAgo: string
  note?: string
  contactStatus?: string
  lastContact?: string
  askingPrice?: string
  negotiationStatus?: string
  progressPercent?: number
  dueDiligence?: string
  // Evidence fields
  stallSignals?: string[]
  stallConfidence?: number
  infrastructureInvested?: boolean
  vacancyRatio?: number
  listingCount?: number
  listingAgents?: string[]
  acreage?: number
}

interface DealCardProps {
  deal: Deal
  stage: string
}

const SIGNAL_SHORT: Record<string, string> = {
  high_vacancy: 'Vacancy',
  roads_installed: 'Infra',
  no_recent_activity: 'Dormant',
  plat_age: 'Aged Plat',
  bonds_posted: 'Bonds',
}

export function DealCard({ deal, stage }: DealCardProps) {
  const [showMoveMenu, setShowMoveMenu] = useState(false)
  const { mutate: moveDeal } = usePipelineMutation()
  const isTier1 = deal.tier === 1
  const showProgress = stage === 'UNDER CONTRACT' && deal.progressPercent != null
  const hasEvidence = (deal.stallSignals?.length ?? 0) > 0
  const hasListings = (deal.listingCount ?? 0) > 0

  const currentIdx = PIPELINE_STAGES.indexOf(stage as PipelineStageName)
  const nextStage = currentIdx >= 0 && currentIdx < PIPELINE_STAGES.length - 1
    ? PIPELINE_STAGES[currentIdx + 1]
    : null

  return (
    <div
      className={`bg-white p-5 rounded-xl shadow-ambient-sm hover:shadow-ambient transition-all duration-200 ${
        isTier1 ? 'border-l-[3px] border-primary' : ''
      }`}
    >
      {/* Title + Tier badge */}
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-sm font-bold text-on-surface leading-tight pr-4 capitalize">
          {deal.title}
        </h4>
        {isTier1 && (
          <span className="text-[9px] font-bold text-primary tracking-widest uppercase whitespace-nowrap bg-primary/8 px-1.5 py-0.5 rounded">
            Tier 1
          </span>
        )}
      </div>

      {/* Progress bar for UNDER CONTRACT */}
      {showProgress && (
        <>
          <div className="w-full bg-surface-container-low h-1.5 rounded-full overflow-hidden mb-3">
            <div
              className="copper-gradient h-full rounded-full transition-all duration-500"
              style={{ width: `${deal.progressPercent}%` }}
            />
          </div>
          {deal.dueDiligence && (
            <div className="text-[10px] font-medium text-on-surface-variant">
              {deal.dueDiligence}
            </div>
          )}
        </>
      )}

      {/* Data rows */}
      {!showProgress && (
        <div className="space-y-1.5 mb-3">
          {deal.entityType && (
            <div className="flex items-center text-[11px] text-on-surface-variant font-medium">
              <span className="w-16 text-on-surface-variant/50">ENTITY</span>
              <span className="text-on-surface">{deal.entityType}</span>
            </div>
          )}
          {deal.lotCount != null && (
            <div className="flex items-center text-[11px] text-on-surface-variant font-medium">
              <span className="w-16 text-on-surface-variant/50">LOTS</span>
              <span className="text-on-surface">{deal.lotCount} lots{deal.acreage ? ` / ${deal.acreage.toFixed(1)} ac` : ''}</span>
            </div>
          )}
          {deal.vacancyRatio != null && (
            <div className="flex items-center text-[11px] text-on-surface-variant font-medium">
              <span className="w-16 text-on-surface-variant/50">VACANT</span>
              <span className="text-on-surface">{Math.round(deal.vacancyRatio * 100)}%</span>
            </div>
          )}
          {hasListings && (
            <div className="flex items-center text-[11px] text-on-surface-variant font-medium">
              <span className="w-16 text-on-surface-variant/50">AGENT</span>
              <span className="text-on-surface">{deal.listingAgents?.join(', ') || `${deal.listingCount} listing(s)`}</span>
            </div>
          )}
          {deal.contactStatus && (
            <div className="flex items-center text-[11px] text-on-surface-variant font-medium">
              <span className="w-16 text-on-surface-variant/50">STATUS</span>
              <span className="text-on-surface">{deal.contactStatus}</span>
            </div>
          )}
          {deal.note && (
            <p className="text-[11px] text-on-surface-variant/70 italic mt-1">
              &ldquo;{deal.note}&rdquo;
            </p>
          )}
        </div>
      )}

      {/* Evidence tags */}
      {hasEvidence && !showProgress && (
        <div className="flex flex-wrap gap-1 mb-3">
          {deal.stallSignals!.slice(0, 3).map((s) => (
            <span key={s} className="inline-block rounded px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-wider bg-surface-container-low text-on-surface-variant">
              {SIGNAL_SHORT[s] ?? s}
            </span>
          ))}
          {deal.infrastructureInvested && (
            <span className="inline-block rounded px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-wider bg-primary/10 text-primary">
              Infra
            </span>
          )}
        </div>
      )}

      {/* Footer — icons, score, signal */}
      {!showProgress && (
        <div className="flex items-center justify-between pt-2 border-t border-surface-container-low">
          <div className="flex gap-1.5">
            {deal.infrastructureInvested && (
              <CheckCircle className="w-3.5 h-3.5 text-primary" />
            )}
            {hasListings && (
              <Mail className="w-3.5 h-3.5 text-primary" />
            )}
            {(deal.stallConfidence ?? 0) >= 0.45 && (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            )}
            {(stage === 'DISCOVERED' || stage === 'RESEARCHED') && (
              <Search className="w-3.5 h-3.5 text-outline-variant" />
            )}
          </div>

          <div className="text-right">
            {deal.score != null && (
              <div className="text-[9px] text-on-surface-variant/50 tabular-nums">Score: {deal.score}</div>
            )}
            {deal.signal && (
              <div className="text-[9px] font-bold text-primary">
                {deal.signal}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stage progression button */}
      {nextStage && (
        <div className="relative mt-3 pt-3 border-t border-surface-container-low">
          <button
            type="button"
            onClick={() => setShowMoveMenu(!showMoveMenu)}
            className="w-full flex items-center justify-center gap-1 rounded-lg py-2 text-[10px] font-bold uppercase tracking-widest text-primary hover:bg-primary/5 transition-colors"
          >
            Move to {nextStage}
            <ChevronRight className="w-3 h-3" />
          </button>

          {showMoveMenu && (
            <div className="absolute bottom-full left-0 right-0 mb-1 rounded-lg bg-white border border-outline-variant/30 shadow-lg z-10 py-1">
              {PIPELINE_STAGES.filter((s) => s !== stage).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => {
                    moveDeal({ dealId: deal.id, newStage: s })
                    setShowMoveMenu(false)
                  }}
                  className="w-full text-left px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
