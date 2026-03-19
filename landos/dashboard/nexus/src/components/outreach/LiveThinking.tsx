const LOG_ENTRIES = [
  {
    agent: 'OUTREACH_ENGINE',
    text: 'Analyzing owner motivation signals for Horseshoe Lake Corp...',
    color: 'text-[#f7bb73]',
  },
  {
    agent: 'COMP_ANALYST',
    text: 'Pulling recent comparable sales within 3mi radius...',
    color: 'text-[#68dba9]',
  },
  {
    agent: 'ENGAGEMENT_BOT',
    text: 'Drafting personalized follow-up based on developer fatigue signal...',
    color: 'text-[#bdc7d8]',
  },
  {
    agent: 'SYSTEM',
    text: 'Template confidence score: 87% — recommended for send.',
    color: 'text-primary',
  },
]

export function LiveThinking() {
  return (
    <div className="relative overflow-hidden rounded-xl bg-[#1b1c1a] p-5 shadow-2xl">
      {/* Accent bar */}
      <div className="absolute left-0 top-0 h-full w-1 animate-pulse bg-primary" />

      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* macOS dots */}
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
          </div>
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/50">
            Outreach Intelligence
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#28c840] opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-[#28c840]" />
          </span>
          <span className="text-[9px] font-bold uppercase tracking-widest text-white/30">
            Active
          </span>
        </div>
      </div>

      {/* Log entries */}
      <div className="space-y-1.5 font-mono text-xs">
        {LOG_ENTRIES.map((entry, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-white/20">&gt;</span>
            <span className={`font-bold ${entry.color}`}>{entry.agent}:</span>
            <span className="text-white/80">{entry.text}</span>
          </div>
        ))}
        <div className="flex gap-2">
          <span className="text-white/20">&gt;</span>
          <span className="animate-pulse text-primary">_</span>
        </div>
      </div>
    </div>
  )
}
