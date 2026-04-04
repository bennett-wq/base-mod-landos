import { ArrowRight } from 'lucide-react'
import { useDormantOwners } from '@/hooks/useDormantSupply'
import { Skeleton } from '@/components/shared/Skeleton'

export function DormantSupply() {
  const { data: owners, isLoading } = useDormantOwners()

  return (
    <div className="relative col-span-12 overflow-hidden rounded-xl bg-white p-8 shadow-ambient">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 className="text-[11px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
            Dormant Supply
          </h3>
          <div className="mt-2 flex gap-4">
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-primary" />
              <span className="text-xs font-bold">76 clusters</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-primary/40" />
              <span className="text-xs font-bold">22,057 acres</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-stone-300" />
              <span className="text-xs font-bold">$772M total value</span>
            </div>
          </div>
        </div>
        <button className="flex items-center gap-2 text-xs font-bold text-primary hover:underline">
          View Supply Map <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Owner cards grid */}
      <div className="grid grid-cols-2 gap-6 md:grid-cols-4 lg:grid-cols-6">
        {isLoading
          ? Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} height="80px" className="rounded-lg" />
            ))
          : owners?.map((owner) => (
              <div
                key={owner.name}
                className="rounded-lg border border-outline-variant/10 bg-surface p-4"
              >
                <h5 className="mb-1 text-[10px] font-bold uppercase text-on-surface-variant">
                  {owner.name}
                </h5>
                <p className="text-xl font-bold text-primary">
                  {owner.lots}{' '}
                  <span className="text-[10px] font-medium text-on-surface-variant/40">units</span>
                </p>
              </div>
            ))}
      </div>
    </div>
  )
}
