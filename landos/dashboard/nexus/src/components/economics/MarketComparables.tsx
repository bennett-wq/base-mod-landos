export function MarketComparables() {
  return (
    <div className="col-span-12 lg:col-span-5 rounded-xl bg-white p-8 shadow-[0_12px_32px_rgba(27,28,26,0.04)]">
      <div className="mb-8">
        <h3 className="text-[11px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
          Market Comparables
        </h3>
        <div className="mt-1 flex items-center gap-2">
          <span className="text-[10px] font-medium text-on-surface-variant/60">
            Source: SparkAPI &middot; Washtenaw County &middot; 12mo
          </span>
        </div>
      </div>

      <div className="space-y-8">
        {/* New Construction */}
        <div className="flex items-end justify-between">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-primary">
              New Construction
            </span>
            <h4 className="text-3xl font-bold text-on-surface">$312,000</h4>
            <p className="text-xs text-on-surface-variant/60">Average List Price</p>
          </div>
          <div className="text-right">
            <span className="rounded-full bg-primary/10 px-2 py-1 text-[10px] font-bold text-primary">
              +16.9% Premium
            </span>
          </div>
        </div>

        {/* Existing Homes */}
        <div className="flex items-end justify-between border-t border-surface-container pt-8">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/60">
              Existing Homes
            </span>
            <h4 className="text-3xl font-bold text-on-surface-variant/40">$267,000</h4>
            <p className="text-xs text-on-surface-variant/60">Average Sale Price</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-medium text-on-surface-variant/40">Baseline Market</p>
          </div>
        </div>

        {/* Quote block */}
        <div className="mt-4 rounded-lg border-l-4 border-primary bg-surface-container-low p-4">
          <p className="text-xs italic leading-relaxed text-on-surface-variant">
            &ldquo;Current supply gap of 4,200 units in the sub-market supports a price ceiling of
            $345k for high-efficiency modules.&rdquo;
          </p>
        </div>
      </div>
    </div>
  )
}
