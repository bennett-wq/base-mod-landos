import { Lock, Globe, FileText } from 'lucide-react'
import type { ApiStrategicOpp } from '@/lib/api'

interface BrokerNotesProps {
  opportunity: ApiStrategicOpp
}

export function BrokerNotes({ opportunity: opp }: BrokerNotesProps) {
  const excerpts = opp.remarks_excerpts ?? []
  const signals = opp.broker_signals ?? []

  const hasContent = excerpts.length > 0 || signals.length > 0

  if (!hasContent) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-on-surface-variant">
        <FileText className="h-8 w-8 text-on-surface-variant/30 mb-4" />
        <p className="text-[10px] font-bold uppercase tracking-widest mb-2">Broker Intelligence</p>
        <p className="text-sm">No broker notes or remarks detected for this opportunity.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Broker Intelligence Notes
        </h3>
        <div className="flex gap-2">
          {opp.package_language_detected && (
            <span className="px-2 py-1 text-[9px] font-bold bg-primary/10 text-primary rounded uppercase">
              Package Language
            </span>
          )}
          {opp.fatigue_language_detected && (
            <span className="px-2 py-1 text-[9px] font-bold bg-yellow-500/10 text-yellow-700 rounded uppercase">
              Fatigue
            </span>
          )}
          {opp.distress_language_detected && (
            <span className="px-2 py-1 text-[9px] font-bold bg-error/10 text-error rounded uppercase">
              Distress
            </span>
          )}
        </div>
      </div>

      {/* Remarks excerpts */}
      {excerpts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {excerpts.map((text, i) => (
            <div
              key={i}
              className="bg-white rounded-xl p-5 border border-outline-variant/10 border-l-4 border-l-error/50"
            >
              <div className="flex justify-between items-start mb-3">
                <span className="px-2 py-0.5 bg-error/10 text-error text-[9px] font-bold rounded uppercase">
                  Private Remarks
                </span>
                <span className="font-mono text-[11px] font-bold text-on-surface-variant">
                  Excerpt {i + 1}
                </span>
              </div>
              <p className="text-sm leading-relaxed text-on-surface-variant">{text}</p>
              <div className="pt-3 border-t border-outline-variant/10 flex items-center gap-2 text-[10px] text-on-surface-variant font-medium mt-4">
                <Lock className="h-3 w-3" />
                BBO Private Disclosure
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Broker signals */}
      {signals.length > 0 && (
        <>
          <h4 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-4">
            Detected Signals
          </h4>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {signals.map((signal, i) => (
              <div
                key={i}
                className="bg-white rounded-xl p-5 border border-outline-variant/10"
              >
                <div className="flex items-start gap-3">
                  <Globe className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                  <p className="text-sm text-on-surface-variant">{signal}</p>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Summary flags */}
      <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
        <FlagCard label="Splits Available" active={opp.splits_available} />
        <FlagCard label="All Offers" active={opp.all_offers_considered} />
        <FlagCard label="Seller is Agent" active={opp.seller_is_agent} />
        <FlagCard label="Site Tested" active={opp.site_tested} />
        <FlagCard label="Has Documents" active={opp.has_documents} />
        <FlagCard label="Infrastructure Ready" active={opp.infrastructure_ready_detected} />
        <FlagCard label="Development Ready" active={opp.development_ready_detected} />
        <FlagCard label="Is Buildable" active={opp.is_buildable} />
      </div>
    </div>
  )
}

function FlagCard({ label, active }: { label: string; active: boolean }) {
  return (
    <div className={`rounded-lg p-3 text-center text-[11px] font-bold uppercase tracking-wider ${
      active
        ? 'bg-primary/10 text-primary'
        : 'bg-surface-container-low text-on-surface-variant/50'
    }`}>
      {label}
    </div>
  )
}
