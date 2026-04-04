import { Terminal } from 'lucide-react'
import { useMetrics } from '@/hooks/useMetrics'

export function MetricsStrip() {
  const { data: metrics } = useMetrics()

  return (
    <footer className="fixed bottom-0 left-0 z-30 ml-[240px] flex h-[52px] w-[calc(100%-240px)] items-center justify-between bg-white/90 px-8 backdrop-blur-xl">
      {/* Left — Key metrics */}
      <div className="flex items-center gap-10">
        {metrics?.map((m) => (
          <div key={m.label} className="flex items-center gap-2.5">
            <span
              className={`text-[9px] font-bold uppercase tracking-[0.12em] ${
                m.highlight ? 'text-primary' : 'text-on-surface-variant/60'
              }`}
            >
              {m.label}
            </span>
            <span
              className={`text-sm font-extrabold tabular-nums ${
                m.highlight ? 'text-primary' : 'text-on-surface'
              }`}
            >
              {m.value}
            </span>
          </div>
        ))}
      </div>

      {/* Right — System status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 rounded-full bg-surface-container-low px-4 py-1.5">
          <Terminal size={13} strokeWidth={2} className="text-primary" />
          <span className="text-[9px] font-bold uppercase tracking-[0.1em] text-on-surface-variant">
            Trigger Rules: 37
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-1.5 w-1.5 rounded-full bg-success glow-pulse" />
          <span className="text-[9px] font-medium text-on-surface-variant/50">Live</span>
        </div>
      </div>
    </footer>
  )
}
