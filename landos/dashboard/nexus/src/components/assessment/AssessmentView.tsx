import { CheckCircle, Clock, ExternalLink } from 'lucide-react'
import { ScoreRing } from '../clusters/ScoreRing'
import { BrokerContact } from './BrokerContact'
import { AgentTerminalSection } from './AgentTerminalSection'

const DIMENSIONS = [
  { label: 'Zoning Fit', value: 82, color: 'bg-primary' },
  { label: 'Lot Economics', value: 45, color: 'bg-yellow-500' },
  { label: 'Infrastructure', value: 68, color: 'bg-primary' },
  { label: 'Market Signal', value: 91, color: 'bg-primary' },
]

const WATERFALL = [
  { label: 'Factory (Net VIP)', value: '$93,361' },
  { label: 'Site Work', value: '$86,767' },
  { label: 'Infrastructure', value: '$50,000' },
  { label: 'Soft Costs', value: '$15,000' },
  { label: 'Contingency (5%)', value: '$12,256' },
  { label: 'Land / Lot', value: '$42,000' },
  { label: 'Closing (9%)', value: '$27,095' },
]

const SUBTOTAL = '$326,479'

const UTILITIES = [
  { label: 'Sewer', status: 'available' as const, icon: CheckCircle },
  { label: 'Water', status: 'available' as const, icon: CheckCircle },
  { label: 'Gas', status: 'pending' as const, icon: Clock },
  { label: 'Electric', status: 'available' as const, icon: CheckCircle },
]

const EXTERNAL_LINKS = [
  'County Soil Map',
  'EPA Flood Zone',
  'Historical Plat Archives',
]

export function AssessmentView() {
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
            <ScoreRing score={64} size={160} />
          </div>
          <div className="space-y-4 mt-8">
            {DIMENSIONS.map((d) => (
              <div key={d.label}>
                <div className="flex justify-between text-[11px] font-bold uppercase tracking-wider mb-1.5">
                  <span>{d.label}</span>
                  <span>{d.value}%</span>
                </div>
                <div className="h-1.5 w-full bg-surface-container-low rounded-full overflow-hidden">
                  <div
                    className={`h-full ${d.color} rounded-full transition-all duration-700`}
                    style={{ width: `${d.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Column 2: Cost Waterfall */}
        <div className="bg-white rounded-xl p-8 ghost-border">
          <div className="flex justify-between items-start mb-6">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
              Cost Waterfall
            </h3>
            <span className="px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-bold rounded">
              Hawthorne MOD
            </span>
          </div>
          <div className="space-y-3">
            {WATERFALL.map((item) => (
              <div
                key={item.label}
                className="flex justify-between items-center py-2 border-b border-outline-variant/10"
              >
                <span className="text-sm font-medium">{item.label}</span>
                <span className="text-sm font-mono text-on-surface">{item.value}</span>
              </div>
            ))}
            {/* Subtotal */}
            <div className="flex justify-between items-center py-2 mt-2">
              <span className="text-sm font-bold uppercase">Subtotal</span>
              <span className="text-sm font-mono font-bold text-on-surface">{SUBTOTAL}</span>
            </div>
          </div>
          {/* Portfolio Value highlight */}
          <div className="mt-8 p-4 bg-surface-container-low rounded-lg border-l-4 border-primary">
            <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant block mb-1">
              Portfolio Value
            </span>
            <span className="text-2xl font-bold text-on-surface">$18.3M</span>
          </div>
        </div>

        {/* Column 3: Compliance + Contact */}
        <div className="flex flex-col gap-8">
          {/* Compliance Status */}
          <div className="bg-white rounded-xl p-8 ghost-border">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-6">
              Compliance Status
            </h3>
            <div className="grid grid-cols-2 gap-4 mb-8">
              {UTILITIES.map((u) => {
                const isAvailable = u.status === 'available'
                return (
                  <div
                    key={u.label}
                    className="bg-surface-container-low rounded-xl p-4 flex flex-col items-center text-center"
                  >
                    {isAvailable ? (
                      <CheckCircle className="h-5 w-5 text-green-600 mb-2" />
                    ) : (
                      <Clock className="h-5 w-5 text-yellow-600 mb-2" />
                    )}
                    <span className="text-[11px] font-bold uppercase mb-1">{u.label}</span>
                    <span
                      className={`text-[10px] font-semibold uppercase ${
                        isAvailable ? 'text-green-700' : 'text-yellow-700'
                      }`}
                    >
                      {isAvailable ? 'Available' : 'Pending'}
                    </span>
                  </div>
                )
              })}
            </div>

            {/* External data links */}
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant mb-3 flex items-center gap-2">
              <ExternalLink className="h-3.5 w-3.5" />
              External Data Links
            </h4>
            <ul className="space-y-1">
              {EXTERNAL_LINKS.map((link) => (
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

          {/* Broker Contact */}
          <BrokerContact />
        </div>
      </div>

      {/* Agent Terminal */}
      <AgentTerminalSection />
    </div>
  )
}
