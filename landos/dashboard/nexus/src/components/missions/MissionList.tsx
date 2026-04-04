import { Calendar, Users } from 'lucide-react'
import { useMissions } from '@/hooks/useMissions'
import { Skeleton } from '@/components/shared/Skeleton'
import type { Mission } from '@/data/mockData'

function MissionCard({ mission }: { mission: Mission }) {
  return (
    <div
      className={`cursor-pointer rounded-xl bg-white p-5 shadow-ambient-sm hover:shadow-ambient transition-all duration-200 ${
        mission.dimmed ? 'opacity-50 grayscale' : ''
      }`}
    >
      <div className="mb-3 flex items-start justify-between">
        <h4 className="text-sm font-bold text-on-surface">{mission.title}</h4>
        <span className="rounded-md bg-surface-container-low px-2 py-0.5 text-[9px] font-bold uppercase tracking-tight text-on-surface-variant/60">
          Completed
        </span>
      </div>

      <div className="mb-3 grid grid-cols-2 gap-y-2 text-xs">
        <div className="flex items-center gap-2 text-on-surface-variant">
          <Calendar size={12} className="text-outline" />
          {mission.date}
        </div>
        <div className="flex items-center gap-2 text-on-surface-variant">
          <Users size={12} className="text-outline" />
          {mission.agents} Agents
        </div>
      </div>

      {!mission.dimmed && (
        <div className="mt-1 flex items-center justify-between rounded-xl bg-surface-container-low px-3 py-2.5">
          <div className="text-center">
            <p className="text-[9px] font-bold uppercase tracking-tight text-on-surface-variant/50">Clusters</p>
            <p className="text-sm font-black text-on-surface tabular-nums">
              {mission.clusters.toLocaleString()}
            </p>
          </div>
          <div className="h-6 w-px bg-outline-variant/20" />
          <div className="text-center">
            <p className="text-[9px] font-bold uppercase tracking-tight text-primary">Tier 1</p>
            <p className="text-sm font-black text-primary tabular-nums">{mission.tier1}</p>
          </div>
          <div className="h-6 w-px bg-outline-variant/20" />
          <div className="text-center">
            <p className="text-[9px] font-bold uppercase tracking-tight text-on-surface-variant/50">Duration</p>
            <p className="text-sm font-black text-on-surface tabular-nums">{mission.duration}</p>
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
      <div className="mb-2 flex items-center justify-between px-1">
        <h2 className="text-[9px] font-bold uppercase tracking-[0.12em] text-on-surface-variant/60">
          Recent Missions
        </h2>
        <span className="cursor-pointer text-[10px] font-bold text-primary hover:underline transition-colors">VIEW ALL</span>
      </div>
      <div className="space-y-3 overflow-y-auto pr-2" style={{ maxHeight: '750px' }}>
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
