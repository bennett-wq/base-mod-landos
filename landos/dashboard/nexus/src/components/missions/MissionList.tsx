import { useMissions } from '@/hooks/useMissions'
import { Skeleton } from '@/components/shared/Skeleton'
import type { Mission } from '@/data/mockData'

function MissionCard({ mission }: { mission: Mission }) {
  return (
    <div
      className={`cursor-pointer rounded-xl border-l-4 border-outline-variant bg-white p-5 shadow-ambient transition-colors hover:bg-surface-container-low ${
        mission.dimmed ? 'opacity-60 grayscale' : ''
      }`}
    >
      <div className="mb-3 flex items-start justify-between">
        <h4 className="text-sm font-bold text-on-surface">{mission.title}</h4>
        <span className="rounded bg-surface-container-high px-2 py-0.5 text-[10px] font-bold uppercase text-on-surface-variant">
          Completed
        </span>
      </div>

      <div className="mb-3 grid grid-cols-2 gap-y-2 text-xs">
        <div className="flex items-center gap-2 text-on-surface-variant">
          <span className="text-outline">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          </span>
          {mission.date}
        </div>
        <div className="flex items-center gap-2 text-on-surface-variant">
          <span className="text-outline">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </span>
          {mission.agents} Agents
        </div>
      </div>

      {!mission.dimmed && (
        <div className="mt-1 flex items-center justify-between rounded-lg bg-surface-container px-3 py-2">
          <div className="text-center">
            <p className="text-[10px] font-bold uppercase text-outline">Clusters</p>
            <p className="text-sm font-black text-on-surface">
              {mission.clusters.toLocaleString()}
            </p>
          </div>
          <div className="h-6 w-px bg-outline-variant/30" />
          <div className="text-center">
            <p className="text-[10px] font-bold uppercase text-primary">Tier 1</p>
            <p className="text-sm font-black text-primary">{mission.tier1}</p>
          </div>
          <div className="h-6 w-px bg-outline-variant/30" />
          <div className="text-center">
            <p className="text-[10px] font-bold uppercase text-outline">Duration</p>
            <p className="text-sm font-black text-on-surface">{mission.duration}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export function MissionList() {
  const { data: missions, isLoading } = useMissions()

  return (
    <aside className="col-span-12 space-y-4 lg:col-span-4">
      <div className="mb-2 flex items-center justify-between px-2">
        <h2 className="text-[10px] font-black uppercase tracking-widest text-on-surface-variant">
          Recent Missions
        </h2>
        <span className="cursor-pointer text-[10px] font-bold text-primary">VIEW ALL</span>
      </div>
      <div className="space-y-4 overflow-y-auto pr-2" style={{ maxHeight: '750px' }}>
        {isLoading
          ? Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} height="160px" className="rounded-xl" />
            ))
          : missions?.map((mission) => (
              <MissionCard key={mission.title} mission={mission} />
            ))}
      </div>
    </aside>
  )
}
