const LOG_ENTRIES = [
  {
    time: '00:01:22',
    agent: 'SCOUT_ALPHA',
    agentColor: 'text-primary',
    message:
      'Identifying property clusters with >10 acres and recent zoning revisions.',
  },
  {
    time: '00:01:28',
    agent: 'GEO_EPSILON',
    agentColor: 'text-yellow-500',
    message:
      'Hydrology maps updated. 43 parcels removed due to wetland overlap > 40%.',
  },
  {
    time: '00:01:34',
    agent: 'MUNI_DELTA',
    agentColor: 'text-blue-400',
    message:
      'Fetching plat records for Sector 4... 12 records retrieved. Parsing legal descriptions.',
  },
  {
    time: '00:01:39',
    agent: 'CORE_OS',
    agentColor: 'text-stone-500',
    message:
      'Cross-referencing Dexter-Ann Arbor Rd target with active listing data. Match found. Listing price $1.2M.',
  },
  {
    time: '00:01:41',
    agent: 'SCOUT_BETA',
    agentColor: 'text-primary',
    message:
      'Evaluating ingress/egress for cluster 2,229. Road frontage confirmed.',
  },
]

export function SwarmTerminal() {
  return (
    <section className="bg-[#1b1c1a] rounded-xl overflow-hidden shadow-2xl">
      {/* Title bar */}
      <div className="flex items-center justify-between border-b border-white/5 bg-[#252524] px-5 py-3">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="h-3 w-3 rounded-full bg-[#FF5F56]" />
            <div className="h-3 w-3 rounded-full bg-[#FFBD2E]" />
            <div className="h-3 w-3 rounded-full bg-[#27C93F]" />
          </div>
          <span className="ml-2 text-[11px] font-bold uppercase tracking-[0.1em] text-white/40">
            Swarm Thought Process
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-[10px] text-white/30">SYSTEM: ACTIVE</span>
          <div className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
        </div>
      </div>

      {/* Log entries */}
      <div className="space-y-2 p-5 font-mono text-[11px] leading-relaxed">
        {LOG_ENTRIES.map((entry, i) => (
          <div key={i} className="flex gap-4">
            <span className="shrink-0 text-white/25">[{entry.time}]</span>
            <p className="text-white/70">
              <span className={`font-bold ${entry.agentColor}`}>{entry.agent}:</span>{' '}
              {entry.message}
            </p>
          </div>
        ))}

        {/* Blinking cursor */}
        <div className="flex items-center gap-4">
          <span className="shrink-0 text-white/25">[00:01:45]</span>
          <span className="terminal-blink inline-block h-4 w-2 bg-primary" />
          <span className="italic text-outline">Swarm is thinking...</span>
        </div>
      </div>
    </section>
  )
}
