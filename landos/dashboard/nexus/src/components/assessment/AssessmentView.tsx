import { CheckCircle, Clock, ExternalLink } from 'lucide-react'
import { ScoreRing } from '../clusters/ScoreRing'
import { BrokerContact } from './BrokerContact'
import { AgentTerminalSection } from './AgentTerminalSection'
import type { ApiStrategicOpp } from '@/lib/api'

interface AssessmentViewProps {
  opportunity: ApiStrategicOpp
}

export function AssessmentView({ opportunity: opp }: AssessmentViewProps) {
  const score = Math.round((opp.composite_score ?? 0) * 100)

  // Derive dimension bars from score breakdown or infrastructure flags
  const breakdown = opp.score_breakdown ?? {}
  const dimensions = [
    {
      label: 'Infrastructure',
      value: Math.round((opp.structured_infra_score ?? 0) * 100),
      color: (opp.structured_infra_score ?? 0) >= 0.5 ? 'bg-primary' : 'bg-yellow-500',
    },
    {
      label: 'Seller Intent',
      value: Math.round((breakdown.seller_intent ?? 0) * 100),
      color: (breakdown.seller_intent ?? 0) >= 0.1 ? 'bg-primary' : 'bg-yellow-500',
    },
    {
      label: 'Ownership',
      value: Math.round((breakdown.ownership_concentration ?? 0) * 100),
      color: (breakdown.ownership_concentration ?? 0) >= 0.1 ? 'bg-primary' : 'bg-yellow-500',
    },
    {
      label: 'Market Signal',
      value: Math.round((breakdown.history_signals ?? 0) * 100),
      color: (breakdown.history_signals ?? 0) >= 0.05 ? 'bg-primary' : 'bg-yellow-500',
    },
  ]

  // Utilities from infrastructure flags
  const utilities = [
    { label: 'Sewer', available: opp.has_public_sewer },
    { label: 'Water', available: opp.has_public_water },
    { label: 'Gas', available: opp.has_natural_gas },
    { label: 'Paved Road', available: opp.has_paved_road },
  ]

  const agents = opp.listing_agents?.length ? opp.listing_agents : opp.owner_linked_agents ?? []
  const offices = opp.owner_linked_offices ?? []

  return (
    <div className="space-y-8">
      {/* 3-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Column 1: Score + Dimensions */}
        <div className="bg-white rounded-xl p-8 ghost-border flex flex-col">
          <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-6">
            Assessment Score
          </h3>
          <div className="flex flex-col items-center justify-center py-4">
            <ScoreRing score={score} size={160} />
          </div>
          <div className="space-y-4 mt-8">
            {dimensions.map((d) => (
              <div key={d.label}>
                <div className="flex justify-between text-[11px] font-bold uppercase tracking-wider mb-1.5">
                  <span>{d.label}</span>
                  <span>{d.value}%</span>
                </div>
                <div className="h-1.5 w-full bg-surface-container-low rounded-full overflow-hidden">
                  <div
                    className={`h-full ${d.color} rounded-full transition-all duration-700`}
                    style={{ width: `${Math.min(d.value, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Key metrics */}
          <div className="mt-8 pt-6 border-t border-outline-variant/10 space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-on-surface-variant">Lots</span>
              <span className="font-bold">{opp.lot_count}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-on-surface-variant">Acreage</span>
              <span className="font-bold">{opp.total_acreage?.toFixed(1)} ac</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-on-surface-variant">Vacancy</span>
              <span className="font-bold">{Math.round((opp.vacancy_ratio ?? 0) * 100)}%</span>
            </div>
            {opp.stall_confidence > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-on-surface-variant">Stall Confidence</span>
                <span className="font-bold">{Math.round(opp.stall_confidence * 100)}%</span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-on-surface-variant">Precedence Tier</span>
              <span className="font-bold">Tier {opp.precedence_tier}</span>
            </div>
          </div>
        </div>

        {/* Column 2: Historical Evidence + Stall Signals */}
        <div className="bg-white rounded-xl p-8 ghost-border">
          <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-6">
            Historical Evidence
          </h3>

          {/* Evidence counts */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-surface-container-low rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-on-surface">{opp.historical_listing_count}</div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Historical</div>
            </div>
            <div className="bg-surface-container-low rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-on-surface">{opp.listing_count}</div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Active</div>
            </div>
            <div className="bg-surface-container-low rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-error">{opp.expired_listing_count}</div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Expired</div>
            </div>
            <div className="bg-surface-container-low rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-yellow-600">{opp.withdrawn_listing_count}</div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">Withdrawn</div>
            </div>
          </div>

          {/* CDOM */}
          {(opp.max_cdom > 0 || opp.avg_cdom > 0) && (
            <div className="mb-6 p-3 bg-surface-container-low rounded-lg">
              <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant mb-2">
                Days on Market
              </div>
              <div className="flex gap-6 text-sm">
                <span>Max CDOM: <strong>{opp.max_cdom}</strong></span>
                <span>Avg CDOM: <strong>{opp.avg_cdom}</strong></span>
              </div>
            </div>
          )}

          {/* Evidence flags */}
          <div className="space-y-2 mb-6">
            {opp.has_relist_cycle && (
              <div className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-error" />
                <span>Relist cycle detected</span>
              </div>
            )}
            {opp.partial_release_detected && (
              <div className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-error" />
                <span>Partial release detected</span>
              </div>
            )}
            {opp.owner_linked_failed_exit_count > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-error" />
                <span>{opp.owner_linked_failed_exit_count} failed exit(s) by this owner</span>
              </div>
            )}
            {opp.package_language_detected && (
              <div className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-primary" />
                <span>Package language in remarks</span>
              </div>
            )}
            {opp.fatigue_language_detected && (
              <div className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-yellow-500" />
                <span>Seller fatigue language detected</span>
              </div>
            )}
            {opp.distress_language_detected && (
              <div className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-error" />
                <span>Distress language detected</span>
              </div>
            )}
          </div>

          {/* Stall signals */}
          {opp.stall_signals?.length > 0 && (
            <>
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant mb-3">
                Stall Signals
              </h4>
              <ul className="space-y-1">
                {opp.stall_signals.map((signal, i) => (
                  <li key={i} className="text-sm text-on-surface-variant flex items-start gap-2">
                    <span className="text-yellow-500 mt-1">•</span>
                    {signal}
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* Owner-linked portfolio overview */}
          {opp.owner_linked_historical_count > 0 && (
            <div className="mt-6 p-4 bg-surface-container-low rounded-lg border-l-4 border-primary">
              <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">
                Owner Portfolio
              </span>
              <div className="text-sm space-y-1">
                <div>{opp.owner_linked_active_count} active, {opp.owner_linked_historical_count} historical listings</div>
                {opp.repeat_agent_on_owner_inventory && (
                  <div className="text-primary font-medium">Same agent across portfolio</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Column 3: Compliance + Contact */}
        <div className="flex flex-col gap-8">
          {/* Compliance Status */}
          <div className="bg-white rounded-xl p-8 ghost-border">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-6">
              Infrastructure Status
            </h3>
            <div className="grid grid-cols-2 gap-4 mb-8">
              {utilities.map((u) => (
                <div
                  key={u.label}
                  className="bg-surface-container-low rounded-xl p-4 flex flex-col items-center text-center"
                >
                  {u.available ? (
                    <CheckCircle className="h-5 w-5 text-green-600 mb-2" />
                  ) : (
                    <Clock className="h-5 w-5 text-yellow-600 mb-2" />
                  )}
                  <span className="text-[11px] font-bold uppercase mb-1">{u.label}</span>
                  <span
                    className={`text-[10px] font-semibold uppercase ${
                      u.available ? 'text-green-700' : 'text-yellow-700'
                    }`}
                  >
                    {u.available ? 'Available' : 'Unknown'}
                  </span>
                </div>
              ))}
            </div>

            {/* Infra flags */}
            {opp.infra_flags?.length > 0 && (
              <>
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant mb-3">
                  Infrastructure Flags
                </h4>
                <ul className="space-y-1 mb-6">
                  {opp.infra_flags.map((flag, i) => (
                    <li key={i} className="text-sm text-on-surface-variant">• {flag}</li>
                  ))}
                </ul>
              </>
            )}

            {/* Buildability */}
            <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-container-low">
              {opp.is_buildable ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <Clock className="h-5 w-5 text-yellow-600" />
              )}
              <span className="text-sm font-medium">
                {opp.is_buildable ? 'Buildable' : 'Buildability Unknown'}
              </span>
            </div>

            {/* External data links */}
            <div className="mt-6">
              <h4 className="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant mb-3 flex items-center gap-2">
                <ExternalLink className="h-3.5 w-3.5" />
                External Data Links
              </h4>
              <ul className="space-y-1">
                {['County Soil Map', 'EPA Flood Zone', 'Historical Plat Archives'].map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="flex items-center justify-between group p-2.5 rounded-lg hover:bg-surface-container-low transition-colors"
                    >
                      <span className="text-sm font-medium">{link}</span>
                      <ExternalLink className="h-3.5 w-3.5 text-on-surface-variant group-hover:translate-x-0.5 transition-transform" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Broker Contact */}
          <BrokerContact agents={agents} offices={offices} />
        </div>
      </div>

      {/* Agent Terminal */}
      <AgentTerminalSection />
    </div>
  )
}
