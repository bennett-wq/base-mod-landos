import { CostWaterfallChart } from '../components/economics/CostWaterfallChart'
import { PortfolioValue } from '../components/economics/PortfolioValue'
import { DealSensitivity } from '../components/economics/DealSensitivity'
import { MarketComparables } from '../components/economics/MarketComparables'
import { DormantSupply } from '../components/economics/DormantSupply'

export default function EconomicsPage() {
  return (
    <div className="-m-8 min-h-screen p-8">
      {/* Header */}
      <section className="mb-10 flex items-end justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-on-surface">Economics</h2>
          <p className="mt-1 text-sm text-on-surface-variant/70">
            Real-time unit cost analysis and deal sensitivity modeling.
          </p>
        </div>
        <div className="flex gap-3">
          <button className="rounded-lg bg-surface-container-low px-5 py-2.5 text-[10px] font-bold uppercase tracking-[0.08em] text-on-surface-variant transition-all hover:bg-surface-container">
            Export Model
          </button>
          <button className="copper-gradient rounded-lg px-6 py-2.5 text-[10px] font-bold uppercase tracking-[0.08em] text-white shadow-md shadow-primary/15 transition-all">
            Commit to Pipeline
          </button>
        </div>
      </section>

      {/* Bento grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Row 1: Waterfall + Portfolio */}
        <CostWaterfallChart />
        <PortfolioValue />

        {/* Row 2: Sensitivity + Comparables */}
        <DealSensitivity />
        <MarketComparables />

        {/* Row 3: Dormant Supply */}
        <DormantSupply />
      </div>

      {/* Footer */}
      <footer className="mt-10 border-t border-outline-variant/10 pb-20 pt-10">
        <div className="flex flex-col gap-6 text-[11px] font-medium text-on-surface-variant/50 md:flex-row">
          <p>Economic engine synchronized with Nexus Hub 42.1</p>
          <div className="flex gap-4">
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Live Market Feed
            </span>
            <span className="flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Cost Oracle v2.4
            </span>
          </div>
          <p className="md:ml-auto">&copy; 2026 BaseMod Systems. Proprietary Analysis Environment.</p>
        </div>
      </footer>
    </div>
  )
}
