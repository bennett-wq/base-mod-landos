import { Terminal } from 'lucide-react'

const LOG_ENTRIES = [
  { time: '00:01:22', agent: 'SCOUT_ALPHA', msg: 'Identifying property clusters in Washtenaw County...' },
  { time: '00:01:28', agent: 'GEO_EPSILON', msg: 'Hydrology maps updated. 4 parcels flagged for flood zone encroachment.' },
  { time: '00:01:34', agent: 'LEGAL_CORE',  msg: 'Cross-referencing ownership entities. Linked 3 shells to Toll Brothers.' },
  { time: '00:01:39', agent: 'SWARM_MASTER', msg: 'Infiltrating municipal permit archives...' },
  { time: '00:01:45', agent: 'ECON_DELTA',   msg: 'Running margin projections on 23 Tier-1 clusters.' },
]

export function SwarmActiveOverlay() {
  return (
    <>
      {/* Floating progress bar at top */}
      <div className="absolute left-1/2 top-8 z-30 w-96 -translate-x-1/2">
        <div className="flex items-center gap-4 rounded-full border border-[#7f5313]/20 bg-white/90 px-6 py-3 shadow-lg backdrop-blur-md">
          <span className="whitespace-nowrap text-[13px] font-bold text-on-surface">
            Swarm Active{' '}
            <span className="text-primary-container">&mdash; 3 of 7 agents deployed</span>
          </span>
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-container">
            <div
              className="h-full rounded-full bg-primary shadow-[0_0_8px_rgba(127,83,19,0.5)]"
              style={{ width: '43%' }}
            />
          </div>
        </div>
      </div>

      {/* Dark terminal docked at bottom */}
      <div className="absolute bottom-6 left-6 right-6 z-30">
        <div className="flex h-[180px] flex-col rounded-xl border border-white/5 bg-[#1b1c1a]/95 p-4 shadow-2xl backdrop-blur-md">
          {/* Terminal header */}
          <div className="mb-3 flex items-center justify-between border-b border-white/10 pb-2">
            <div className="flex items-center gap-2">
              <Terminal size={16} className="text-[#7f5313]" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-white/80">
                Swarm Cognitive Stream
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 animate-pulse rounded-full bg-[#22c55e]" />
              <span className="text-[9px] font-bold uppercase tracking-wider text-[#22c55e]/80">
                Live Thinking
              </span>
            </div>
          </div>

          {/* Log entries */}
          <div className="flex-1 space-y-1 overflow-y-auto font-mono text-[12px] leading-loose">
            {LOG_ENTRIES.map((e, i) => (
              <div key={i} className="flex gap-3">
                <span className="text-[#7f5313]/70">[{e.time}]</span>
                <span className="text-[#f7bb73]">{e.agent}:</span>
                <span className={`text-white/80 ${i === LOG_ENTRIES.length - 1 ? 'animate-pulse' : ''}`}>
                  {e.msg}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}
