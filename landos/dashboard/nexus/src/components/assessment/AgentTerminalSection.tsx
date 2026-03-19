const LOG_ENTRIES = [
  {
    time: '14:22:05',
    agent: 'MUNICIPAL AGENT',
    agentColor: 'text-primary',
    message: 'Scanning 2026 Plat recordings for easement conflicts...',
  },
  {
    time: '14:22:12',
    agent: 'ZONING AUDITOR',
    agentColor: 'text-yellow-500',
    message: 'RE-CALCULATING: Setback deviation detected on Scio Ridge Rd.',
  },
  {
    time: '14:22:18',
    agent: 'SUPPLY INTEL',
    agentColor: 'text-blue-400',
    message: 'Syncing latest MLS listings for pricing velocity benchmark...',
  },
  {
    time: '14:22:31',
    agent: 'SYSTEM',
    agentColor: 'text-stone-500 italic',
    message: 'Core thread optimization complete. Ready for manual override.',
  },
  {
    time: '14:22:45',
    agent: 'MUNICIPAL AGENT',
    agentColor: 'text-primary',
    message: 'Cross-referencing environmental buffer requirements (Parcel 44-B)...',
  },
]

export function AgentTerminalSection() {
  return (
    <section className="bg-[#1b1c1a] rounded-xl overflow-hidden shadow-2xl">
      {/* Title bar */}
      <div className="bg-[#252524] px-5 py-3 flex items-center justify-between border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-[#FF5F56]" />
            <div className="w-3 h-3 rounded-full bg-[#FFBD2E]" />
            <div className="w-3 h-3 rounded-full bg-[#27C93F]" />
          </div>
          <span className="text-[11px] font-bold uppercase tracking-[0.1em] text-white/40 ml-2">
            Agent Terminal — Live Thinking
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono text-white/30">SYSTEM: ACTIVE</span>
          <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" />
        </div>
      </div>

      {/* Log entries */}
      <div className="p-5 font-mono text-[11px] leading-relaxed space-y-2">
        {LOG_ENTRIES.map((entry, i) => (
          <div key={i} className="flex gap-4">
            <span className="text-white/25 shrink-0">[{entry.time}]</span>
            <p className="text-white/70">
              <span className={`font-bold ${entry.agentColor}`}>{entry.agent}:</span>{' '}
              {entry.message}
            </p>
          </div>
        ))}
        {/* Blinking cursor line */}
        <div className="flex gap-4 items-center">
          <span className="text-white/25 shrink-0">[14:22:50]</span>
          <span className="w-2 h-4 bg-primary terminal-blink inline-block" />
        </div>
      </div>
    </section>
  )
}
