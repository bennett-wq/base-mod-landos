import { useEffect } from 'react'
import { Sparkles, X, FileText, Package, Map, Rocket } from 'lucide-react'
import type { ClusterData } from './ClusterCards'

interface ClusterDetailModalProps {
  cluster: ClusterData
  onClose: () => void
}

const ECONOMICS = [
  { label: 'Land Acquisition', value: '$42,000' },
  { label: 'Soft Costs / Permitting', value: '$15,000' },
  { label: 'Vertical Build (Avg)', value: '$86,767' },
  { label: 'Factory Unit Cost', value: '$93,361', highlight: true },
  { label: 'Contingency', value: '$12,256' },
]

const HOME_MODELS = [
  { name: 'Hawthorne', cost: '$199k Production Cost', fit: 92 },
  { name: 'Belmont', cost: '$239k Production Cost', fit: 85 },
  { name: 'Aspen', cost: '$279k Production Cost', fit: 72 },
]

const SIGNALS = [
  { label: 'Dev Exit Probability', value: '92%', valueClass: 'text-primary' },
  { label: 'CDOM Avg (90d)', value: '156 Days', valueClass: 'text-on-surface' },
  { label: 'Package Language', value: 'Detected', valueClass: 'text-on-surface' },
  { label: 'Linked Entities', value: '3 Found', valueClass: 'text-on-surface' },
]

export function ClusterDetailModal({ cluster, onClose }: ClusterDetailModalProps) {
  // ESC key handler
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-on-surface/40 p-8 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="mt-[10vh] flex max-h-[80vh] w-full max-w-[960px] flex-col overflow-hidden rounded-[1.5rem] border border-white/20 bg-surface shadow-ambient-lg">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-stone-100 bg-white p-8">
          <div>
            <div className="mb-1 flex items-center space-x-3">
              <h2 className="text-2xl font-bold tracking-tight">{cluster.owner}</h2>
              <span className="rounded bg-green-50 px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-green-700">
                HIGHEST
              </span>
              <span className="rounded bg-stone-100 px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-stone-600">
                TIER {cluster.tier}
              </span>
            </div>
            <p className="text-on-surface-variant">
              Cluster ID: {cluster.id} &bull; Last updated 42m ago
            </p>
          </div>
          <button
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-full transition-colors hover:bg-stone-50"
          >
            <X className="h-5 w-5 text-stone-400" />
          </button>
        </div>

        {/* Body — 3 columns */}
        <div className="hide-scrollbar grid flex-1 grid-cols-3 gap-0 overflow-y-auto bg-surface-container-low">
          {/* Column 1: Score & Active Signals */}
          <div className="flex flex-col space-y-8 border-r border-stone-200/60 p-8">
            <div className="flex items-center space-x-6">
              <div className="flex h-20 w-20 items-center justify-center rounded-full border border-primary/20 bg-white ring-8 ring-primary/5">
                <div className="text-center">
                  <span className="block text-2xl font-black leading-none text-primary">{cluster.score}</span>
                  <span className="text-[10px] font-bold uppercase text-stone-400">Index</span>
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-on-surface">Momentum Up</p>
                <p className="text-[10px] font-semibold text-green-600">+4.2% since launch</p>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-[10px] font-bold uppercase tracking-[0.15em] text-stone-400">
                Active Signals
              </h4>
              <div className="space-y-3">
                {SIGNALS.map((s) => (
                  <div
                    key={s.label}
                    className="flex items-center justify-between rounded-xl border border-stone-100 bg-white p-3"
                  >
                    <span className="text-xs font-medium text-on-surface-variant">{s.label}</span>
                    <span className={`text-xs font-bold ${s.valueClass}`}>{s.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Column 2: Economics Waterfall */}
          <div className="border-r border-stone-200/60 bg-white p-8">
            <h4 className="mb-6 text-[10px] font-bold uppercase tracking-[0.15em] text-stone-400">
              Economics Waterfall
            </h4>
            <div className="space-y-4">
              {ECONOMICS.map((item) => (
                <div key={item.label} className="flex justify-between border-b border-stone-50 pb-2">
                  <span className="text-sm text-stone-600">{item.label}</span>
                  <span className={`text-sm font-bold ${item.highlight ? 'text-primary' : ''}`}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>

            {/* Profit highlight */}
            <div className="-mx-8 mt-8 border-l-4 border-primary bg-primary/5 px-8 py-6">
              <div className="mb-2 flex justify-between">
                <span className="text-xs font-bold uppercase text-on-surface">Estimated Profit</span>
                <span className="text-lg font-bold text-primary">$103,800</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs font-bold uppercase text-on-surface">Net Margin</span>
                <span className="text-lg font-bold text-primary">33.2%</span>
              </div>
            </div>
          </div>

          {/* Column 3: Home Product Fit */}
          <div className="flex flex-col space-y-8 p-8">
            <h4 className="text-[10px] font-bold uppercase tracking-[0.15em] text-stone-400">
              Home Product Fit
            </h4>
            <div className="space-y-6">
              {HOME_MODELS.map((model) => (
                <div key={model.name} className="space-y-2">
                  <div className="flex items-end justify-between">
                    <div>
                      <p className="text-sm font-bold text-on-surface">{model.name}</p>
                      <p className="text-[10px] font-medium text-on-surface-variant">{model.cost}</p>
                    </div>
                    <span className="text-sm font-bold text-primary">{model.fit}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-stone-100">
                    <div className="h-full bg-primary" style={{ width: `${model.fit}%` }} />
                  </div>
                </div>
              ))}
            </div>

            {/* AI Suggestion */}
            <div className="mt-auto flex items-start space-x-3 rounded-xl bg-inverse-surface p-4 text-white">
              <Sparkles className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
              <p className="text-[10px] leading-relaxed">
                NEXUS AI Suggests: High priority for{' '}
                <span className="font-bold text-primary">Hawthorne XMOD</span> for optimal lot
                coverage and margin.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-stone-100 bg-white p-6">
          <div className="flex space-x-2">
            <button className="flex items-center rounded-lg border border-stone-200 px-5 py-2.5 text-xs font-bold text-on-surface-variant transition-colors hover:bg-stone-50">
              <FileText className="mr-2 h-4 w-4" />
              Generate Broker Note
            </button>
            <button className="flex items-center rounded-lg border border-stone-200 px-5 py-2.5 text-xs font-bold text-on-surface-variant transition-colors hover:bg-stone-50">
              <Package className="mr-2 h-4 w-4" />
              Export Deal Package
            </button>
          </div>
          <div className="flex space-x-3">
            <button className="flex items-center rounded-lg px-5 py-2.5 text-xs font-bold text-primary transition-colors hover:bg-primary/5">
              <Map className="mr-2 h-4 w-4" />
              View on Map
            </button>
            <button
              className="flex items-center rounded-lg px-6 py-2.5 text-xs font-bold text-white shadow-md transition-transform hover:scale-[1.02]"
              style={{ background: 'linear-gradient(155deg, #7f5313 0%, #9b6b2a 100%)' }}
            >
              <Rocket className="mr-2 h-4 w-4" />
              Deploy Deep Scan
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
