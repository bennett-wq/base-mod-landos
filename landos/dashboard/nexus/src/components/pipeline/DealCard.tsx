import { Search, Landmark, Package, Mail } from 'lucide-react'

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
}

interface DealCardProps {
  deal: Deal
  stage: string
}

export function DealCard({ deal, stage }: DealCardProps) {
  const isTier1 = deal.tier === 1
  const showProgress = stage === 'UNDER CONTRACT' && deal.progressPercent != null

  return (
    <div
      className={`bg-white p-5 rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer ${
        isTier1 ? 'border-l-[3px] border-primary' : ''
      }`}
    >
      {/* Title + Tier badge */}
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-sm font-bold text-on-surface leading-tight pr-4">
          {deal.title}
        </h4>
        {isTier1 && (
          <span className="text-[10px] font-bold text-primary tracking-widest uppercase whitespace-nowrap">
            Tier 1
          </span>
        )}
      </div>

      {/* Progress bar for UNDER CONTRACT */}
      {showProgress && (
        <>
          <div className="w-full bg-stone-100 h-1.5 rounded-full overflow-hidden mb-3">
            <div
              className="copper-gradient h-full rounded-full"
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

      {/* Data rows — varies by stage */}
      {!showProgress && (
        <div className="space-y-1.5 mb-4">
          {deal.entityType && (
            <div className="flex items-center text-[11px] text-on-surface-variant font-medium">
              <span className="w-16">ENTITY</span>
              <span className="text-on-surface">{deal.entityType}</span>
            </div>
          )}
          {deal.location && (
            <div className="flex items-center text-[11px] text-on-surface-variant font-medium">
              <span className="w-16">LOC</span>
              <span className="text-on-surface">{deal.location}</span>
            </div>
          )}
          {deal.lotCount != null && (
            <div className="flex items-center text-[11px] text-on-surface-variant font-medium">
              <span className="w-16">UNITS</span>
              <span className="text-on-surface">{deal.lotCount} lots</span>
            </div>
          )}
          {deal.contactStatus && (
            <div className="flex items-center text-[11px] text-on-surface-variant font-medium">
              <span className="w-16">STATUS</span>
              <span className="text-on-surface">{deal.contactStatus}</span>
            </div>
          )}
          {deal.lastContact && (
            <div className="flex items-center text-[11px] text-on-surface-variant font-medium">
              <span className="w-16">LAST</span>
              <span className="text-on-surface">{deal.lastContact}</span>
            </div>
          )}
          {deal.note && (
            <p className="text-[11px] text-on-surface-variant italic">
              "{deal.note}"
            </p>
          )}
        </div>
      )}

      {/* Footer — icons, score, signal, price */}
      {!showProgress && (
        <div className="flex items-center justify-between pt-3 border-t border-stone-50">
          <div className="flex gap-2">
            {(stage === 'DISCOVERED' || stage === 'RESEARCHED') && (
              <Search className="w-3.5 h-3.5 text-stone-300" />
            )}
            {(stage === 'DISCOVERED' || stage === 'RESEARCHED') &&
              (deal.score ?? 0) >= 50 && (
                <Landmark className="w-3.5 h-3.5 text-stone-300" />
              )}
            {stage === 'DISCOVERED' && isTier1 && (
              <Package className="w-3.5 h-3.5 text-stone-300" />
            )}
            {stage === 'OUTREACH DRAFTED' && (
              <Mail className={`w-3.5 h-3.5 ${isTier1 ? 'text-primary' : 'text-stone-300'}`} />
            )}
          </div>

          <div className="text-right">
            {deal.askingPrice && (
              <div className="text-[11px] font-bold text-on-surface">
                {deal.askingPrice}
              </div>
            )}
            {deal.negotiationStatus && (
              <div className="text-[9px] text-primary font-bold">
                {deal.negotiationStatus}
              </div>
            )}
            {deal.score != null && (
              <div className="text-[9px] text-stone-400">Score: {deal.score}</div>
            )}
            {deal.signal && (
              <div className="text-[9px] font-bold text-primary">
                Signal: {deal.signal}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Timestamp */}
      <p className="text-[9px] text-stone-400 mt-2">{deal.updatedAgo}</p>
    </div>
  )
}
