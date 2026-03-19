import { X, Package, Building2, TrendingUp, MapPin, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface AgentDetailPanelProps {
  nodeIndex: number | null
  onClose: () => void
}

const NODE_DETAILS = [
  {
    name: 'Packaging Intelligence',
    Icon: Package,
    status: 'Operational',
    stats: { runs: '24', duration: '1.2s', events: '156', hitRate: '94%' },
    ops: [
      { label: 'Mesh Handshake → Zoning', time: '2 mins ago', detail: 'Hash: 0x8a9b' },
      { label: 'Parity Scan Complete', time: '8 mins ago', detail: '4 new lots detected' },
      { label: 'BBO Cross-Reference', time: '14 mins ago', detail: '12 matches found' },
      { label: 'Package Yield Calc', time: '22 mins ago', detail: 'Cluster C-1042' },
    ],
  },
  {
    name: 'Municipal Intelligence',
    Icon: Building2,
    status: 'Pulsing',
    stats: { runs: '18', duration: '3.4s', events: '89', hitRate: '87%' },
    ops: [
      { label: 'Zoning Ordinance Scan', time: '1 min ago', detail: 'Scio Twp' },
      { label: 'Plat Recording Check', time: '5 mins ago', detail: '3 new plats' },
      { label: 'Section 108 Analysis', time: '12 mins ago', detail: 'Ypsilanti Twp' },
      { label: 'Density Variance Audit', time: '18 mins ago', detail: '7 parcels flagged' },
    ],
  },
  {
    name: 'Economic Analysis',
    Icon: TrendingUp,
    status: 'Operational',
    stats: { runs: '31', duration: '0.8s', events: '204', hitRate: '96%' },
    ops: [
      { label: 'Waterfall Recalculation', time: '3 mins ago', detail: 'Cluster C-0847' },
      { label: 'Comp Pull Complete', time: '9 mins ago', detail: '14 comps matched' },
      { label: 'Sensitivity Grid Update', time: '15 mins ago', detail: 'Market shift +2.1%' },
      { label: 'Cost Basis Refresh', time: '28 mins ago', detail: 'All active parcels' },
    ],
  },
  {
    name: 'Spatial Engine',
    Icon: MapPin,
    status: 'Operational',
    stats: { runs: '42', duration: '2.1s', events: '312', hitRate: '91%' },
    ops: [
      { label: 'Proximity Cluster Scan', time: '1 min ago', detail: '50m radius sweep' },
      { label: 'Centroid Calculation', time: '6 mins ago', detail: '1,036 clusters' },
      { label: 'Parcel Boundary Check', time: '11 mins ago', detail: 'Augusta Twp' },
      { label: 'GIS Layer Sync', time: '20 mins ago', detail: 'Regrid update' },
    ],
  },
  {
    name: 'Signal Processor',
    Icon: Sparkles,
    status: 'Operational',
    stats: { runs: '56', duration: '0.4s', events: '428', hitRate: '98%' },
    ops: [
      { label: 'BBO Language Scan', time: '30s ago', detail: '6 new matches' },
      { label: 'Price Reduction Alert', time: '4 mins ago', detail: 'Saline parcel' },
      { label: 'Stallout Detection', time: '10 mins ago', detail: '2 subdivisions flagged' },
      { label: 'Remarks NLP Pass', time: '16 mins ago', detail: '95 listings processed' },
    ],
  },
]

export function AgentDetailPanel({ nodeIndex, onClose }: AgentDetailPanelProps) {
  const isOpen = nodeIndex !== null
  const detail = nodeIndex !== null ? NODE_DETAILS[nodeIndex] : null

  return (
    <AnimatePresence>
      {isOpen && detail && (
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 30, stiffness: 300 }}
          className="absolute right-0 top-0 bottom-0 w-[360px] bg-white border-l border-outline-variant/10 z-50 p-6 flex flex-col"
          style={{ boxShadow: '-12px 0 32px rgba(27, 28, 26, 0.04)' }}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-lg bg-surface-container-low flex items-center justify-center mr-3">
                <detail.Icon size={20} className="text-primary" />
              </div>
              <div>
                <h3 className="font-bold text-on-surface leading-tight">{detail.name}</h3>
                <span className="text-[10px] font-bold text-[#059669] uppercase tracking-wider">
                  {detail.status}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-on-surface-variant hover:text-on-surface transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="p-4 bg-surface-container-low rounded-xl">
              <span className="text-[10px] font-bold text-on-surface-variant uppercase">
                Runs Today
              </span>
              <p className="text-xl font-bold text-on-surface mt-1">{detail.stats.runs}</p>
            </div>
            <div className="p-4 bg-surface-container-low rounded-xl">
              <span className="text-[10px] font-bold text-on-surface-variant uppercase">
                Avg Duration
              </span>
              <p className="text-xl font-bold text-on-surface mt-1">{detail.stats.duration}</p>
            </div>
            <div className="p-4 bg-surface-container-low rounded-xl">
              <span className="text-[10px] font-bold text-on-surface-variant uppercase">
                Events Emitted
              </span>
              <p className="text-xl font-bold text-on-surface mt-1">{detail.stats.events}</p>
            </div>
            <div className="p-4 bg-surface-container-low rounded-xl">
              <span className="text-[10px] font-bold text-on-surface-variant uppercase">
                Hit Rate
              </span>
              <p className="text-xl font-bold text-primary mt-1">{detail.stats.hitRate}</p>
            </div>
          </div>

          {/* Recent operations */}
          <div className="flex-1">
            <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest block mb-3">
              Recent Operations
            </span>
            <div className="space-y-3">
              {detail.ops.map((op, i) => (
                <div key={i} className="flex items-start">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 mr-3 shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs font-semibold">{op.label}</p>
                    <p className="text-[10px] text-on-surface-variant mt-0.5">
                      {op.time} &middot; {op.detail}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Re-initialize button */}
          <button className="w-full py-3 copper-gradient rounded-xl text-white text-sm font-bold shadow-lg shadow-primary/20 mt-6">
            Re-initialize Agent
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
