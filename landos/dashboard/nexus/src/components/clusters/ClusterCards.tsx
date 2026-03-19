import { ScoreRing } from './ScoreRing'

type Tier = 'A' | 'B' | 'C'

export interface ClusterData {
  id: string
  owner: string
  township: string
  lots: number
  acreage: number
  avgLandValue: string
  supplyType: string
  score: number
  tier: Tier
  zoning: number
  infrastructure: number
  economicFit: number
}

export const CLUSTER_DATA: ClusterData[] = [
  { id: 'NEX-88129-WAS', owner: 'Horseshoe Lake Corp',   township: 'Saline Twp',    lots: 88,  acreage: 142,  avgLandValue: '$42,000',  supplyType: 'TIGHT',   score: 91, tier: 'A', zoning: 82, infrastructure: 45, economicFit: 91 },
  { id: 'NEX-71204-WAS', owner: 'Julian Francis Trust',   township: 'Lima Twp',      lots: 12,  acreage: 8.4,  avgLandValue: '$68,000',  supplyType: 'SCARCE',  score: 84, tier: 'A', zoning: 78, infrastructure: 62, economicFit: 88 },
  { id: 'NEX-55301-WAS', owner: 'Toll Brothers Holdings', township: 'Augusta Twp',   lots: 146, acreage: 312,  avgLandValue: '$5,907K',  supplyType: 'DORMANT', score: 67, tier: 'B', zoning: 84, infrastructure: 62, economicFit: 91 },
  { id: 'NEX-42018-WAS', owner: 'M/I Homes LLC',          township: 'Ann Arbor Twp', lots: 99,  acreage: 186,  avgLandValue: '$3,200K',  supplyType: 'TIGHT',   score: 52, tier: 'B', zoning: 60, infrastructure: 38, economicFit: 64 },
  { id: 'NEX-33905-WAS', owner: 'PulteGroup',             township: 'Ypsilanti Twp', lots: 82,  acreage: 94,   avgLandValue: '$1,800K',  supplyType: 'NORMAL',  score: 34, tier: 'C', zoning: 42, infrastructure: 28, economicFit: 40 },
]

const TIER_STYLES: Record<Tier, string> = {
  A: 'bg-primary text-white',
  B: 'bg-stone-400 text-white',
  C: 'bg-stone-300 text-stone-600',
}

interface DimensionBarProps {
  label: string
  value: number
}

function DimensionBar({ label, value }: DimensionBarProps) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] font-bold uppercase text-stone-500">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-stone-100">
        <div
          className={value < 50 ? 'h-full bg-amber-500' : 'h-full bg-primary'}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}

interface ClusterCardsProps {
  onViewIntel: (cluster: ClusterData) => void
}

export function ClusterCards({ onViewIntel }: ClusterCardsProps) {
  return (
    <section className="flex w-1/2 flex-col overflow-y-auto bg-surface p-8 hide-scrollbar">
      {/* Header */}
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-on-surface">Deep Cluster Intelligence</h2>
          <p className="mt-1 text-sm text-on-surface-variant">
            Found {CLUSTER_DATA.length} high-probability clusters in North Washtenaw
          </p>
        </div>
        <button className="rounded-lg border border-primary/20 px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-primary transition-colors hover:bg-primary/5">
          Sort by: Score
        </button>
      </div>

      {/* Cards */}
      <div className="space-y-6">
        {CLUSTER_DATA.map((cluster, i) => {
          const isFeatured = i === 0
          return (
            <article
              key={cluster.id}
              className={
                isFeatured
                  ? 'group relative overflow-hidden rounded-[1.25rem] border border-outline-variant/30 border-l-4 border-l-primary bg-surface-container-lowest p-7 shadow-sm'
                  : 'group relative overflow-hidden rounded-[1.25rem] border border-outline-variant/30 bg-surface-container-lowest p-7 shadow-sm opacity-90 transition-opacity hover:opacity-100'
              }
            >
              {/* Tier badge */}
              <div className={`absolute right-0 top-0 rounded-bl-xl px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest ${TIER_STYLES[cluster.tier]}`}>
                Tier {cluster.tier}{cluster.tier === 'A' ? ' Priority' : ''}
              </div>

              {/* Top row */}
              <div className="mb-6 flex items-start justify-between">
                <div className="space-y-1">
                  <h3 className="text-lg font-bold leading-none text-stone-900">{cluster.owner}</h3>
                  <p className="text-sm text-on-surface-variant">
                    {cluster.township} &bull; {cluster.lots} lots &bull; {cluster.acreage.toLocaleString()} acres
                  </p>
                </div>
                <ScoreRing score={cluster.score} size={64} />
              </div>

              {/* Stats row */}
              <div className="mb-6 grid grid-cols-4 gap-4 border-y border-stone-50 py-4">
                <div>
                  <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-stone-400">Lot Count</p>
                  <p className="text-sm font-bold text-on-surface">{cluster.lots} lots</p>
                </div>
                <div>
                  <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-stone-400">Acreage</p>
                  <p className="text-sm font-bold text-on-surface">{cluster.acreage} ac</p>
                </div>
                <div>
                  <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-stone-400">Avg Land</p>
                  <p className="text-sm font-bold text-on-surface">{cluster.avgLandValue}</p>
                </div>
                <div>
                  <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-stone-400">Supply</p>
                  <p className="text-sm font-bold text-primary">{cluster.supplyType}</p>
                </div>
              </div>

              {/* Dimension bars */}
              <div className="mb-8 space-y-3">
                <DimensionBar label="Zoning & Entitlement" value={cluster.zoning} />
                <DimensionBar label="Infrastructure Signal" value={cluster.infrastructure} />
                <DimensionBar label="Economic Demand Fit" value={cluster.economicFit} />
              </div>

              {/* CTA */}
              <button
                onClick={() => onViewIntel(cluster)}
                className="flex w-full items-center justify-center rounded-lg py-3 text-xs font-bold text-white shadow-sm transition-opacity hover:opacity-90"
                style={{ background: 'linear-gradient(155deg, #7f5313 0%, #9b6b2a 100%)' }}
              >
                View Full Intel
                <svg className="ml-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              </button>
            </article>
          )
        })}
      </div>
    </section>
  )
}
