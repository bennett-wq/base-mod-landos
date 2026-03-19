import { ScoreRing } from '@/components/clusters/ScoreRing'

interface AgentStatus {
  name: string
  detail: string
  progress: number
  queued?: boolean
}

const agents: AgentStatus[] = [
  { name: 'Scout Agent', detail: 'Scanning parcels...', progress: 68 },
  { name: 'Municipal Agent', detail: 'Reading planning docs...', progress: 42 },
  { name: 'Tax Assessor', detail: 'Waiting for Scout...', progress: 0 },
  { name: 'Geospatial Engine', detail: 'Near complete', progress: 91 },
  { name: 'Zoning Auditor', detail: 'Starting analysis...', progress: 15 },
  { name: 'Comp Analyst', detail: 'Queued', progress: 0, queued: true },
  { name: 'Home Fit Agent', detail: 'Queued', progress: 0, queued: true },
]

function AgentProgressBar({ agent }: { agent: AgentStatus }) {
  const isActive = agent.progress > 0
  const isQueued = agent.queued

  return (
    <div className={`space-y-2 ${isQueued || (!isActive && !isQueued) ? 'opacity-50' : ''}`}>
      <div className="flex items-center justify-between text-xs">
        <span
          className={`${isActive ? 'font-bold text-on-surface' : 'font-medium italic text-on-surface'}`}
        >
          {agent.name} — {agent.detail}
        </span>
        {isActive ? (
          <span className="font-black text-primary">{agent.progress}%</span>
        ) : (
          <span className="italic text-outline">{isQueued ? 'Queued' : 'Waiting'}</span>
        )}
      </div>
      <div
        className={`h-1.5 w-full overflow-hidden rounded-full ${
          isQueued ? 'bg-surface-container-high' : 'bg-surface-container'
        }`}
      >
        {isActive && (
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${agent.progress}%` }}
          />
        )}
      </div>
    </div>
  )
}

const summaryStats = [
  { label: 'Listings', value: '95' },
  { label: 'Vacant', value: '10,266' },
  { label: 'Tier 1', value: '23', accent: true },
]

export function ActiveMission() {
  return (
    <section className="col-span-12 space-y-6 lg:col-span-8">
      <div className="relative overflow-hidden rounded-2xl bg-white p-8 shadow-ambient">
        {/* Header */}
        <div className="mb-8 flex flex-col gap-4 border-b border-outline-variant/20 pb-6 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <span className="flex h-2 w-2 animate-pulse rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">
                Live Mission Deployment
              </span>
            </div>
            <h2 className="text-2xl font-black text-on-surface">
              Washtenaw — Deep Scan Alpha
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-[10px] font-bold uppercase text-outline">Elapsed</p>
              <p className="text-xl font-black tracking-tight text-primary">00:02:47</p>
            </div>
            <button className="rounded-lg bg-error/10 px-4 py-2 text-xs font-bold uppercase tracking-wider text-error transition-colors hover:bg-error/20">
              Abort Mission
            </button>
          </div>
        </div>

        {/* Two-column split */}
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          {/* Left — Agent Swarm Status */}
          <div className="space-y-5">
            <h3 className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-on-surface-variant">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              Agent Swarm Status
            </h3>
            <div className="space-y-4">
              {agents.map((agent) => (
                <AgentProgressBar key={agent.name} agent={agent} />
              ))}
            </div>
          </div>

          {/* Right — Live Discovery */}
          <div className="space-y-5">
            <h3 className="flex items-center gap-2 text-xs font-black uppercase tracking-widest text-on-surface-variant">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              Live Discovery
            </h3>

            <div className="rounded-xl border border-outline-variant/20 bg-surface-container-low p-6">
              {/* Score Ring */}
              <div className="mb-5 flex justify-center">
                <ScoreRing score={92} size={120} />
              </div>

              {/* Target details */}
              <div className="mb-5 space-y-1 text-center">
                <p className="text-[10px] font-bold uppercase tracking-widest text-primary">
                  High-Value Target Found
                </p>
                <h4 className="text-lg font-bold leading-tight text-on-surface">
                  12.4 AC — Dexter-Ann Arbor Rd
                </h4>
                <p className="text-sm text-on-surface-variant">
                  Owner: Greenfield Acquisitions LLC
                </p>
              </div>

              {/* Info cards */}
              <div className="mb-5 grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-outline-variant/10 bg-white p-3">
                  <p className="mb-1 text-[8px] font-bold uppercase text-outline">Tax Status</p>
                  <p className="text-xs font-bold text-green-700">Delinquent</p>
                </div>
                <div className="rounded-xl border border-outline-variant/10 bg-white p-3">
                  <p className="mb-1 text-[8px] font-bold uppercase text-outline">Zoning</p>
                  <p className="text-xs font-bold text-on-surface">Agri-Res</p>
                </div>
              </div>

              {/* CTA */}
              <button className="w-full rounded-xl border border-primary/20 bg-white py-3 text-sm font-bold text-primary transition-all hover:bg-primary hover:text-white active:scale-95">
                View Full Assessment
              </button>
            </div>

            {/* Summary stats */}
            <div className="grid grid-cols-3 gap-3">
              {summaryStats.map((stat) => (
                <div key={stat.label} className="rounded-xl bg-surface-container-low p-3 text-center">
                  <p className="text-[10px] font-bold uppercase text-outline">{stat.label}</p>
                  <p
                    className={`text-lg font-black ${stat.accent ? 'text-primary' : 'text-on-surface'}`}
                  >
                    {stat.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
