import { Terminal } from 'lucide-react'
import { useMetrics } from '@/hooks/useMetrics'

export function MetricsStrip() {
  const { data: metrics } = useMetrics()

  return (
    <footer className="fixed bottom-0 left-0 z-30 ml-[240px] flex h-[56px] w-[calc(100%-240px)] items-center justify-between border-t border-outline-variant/10 bg-white px-8">
      <div className="flex items-center gap-12">
        {metrics?.map((m) => (
          <div key={m.label} className="flex flex-col">
            <span
              className={`text-[9px] font-bold uppercase tracking-widest ${
                m.highlight
                  ? 'text-primary'
                  : 'text-on-surface-variant'
              }`}
            >
              {m.label}
            </span>
            <span
              className={`text-sm font-extrabold ${
                m.highlight ? 'text-primary' : 'text-on-surface'
              }`}
            >
              {m.value}
            </span>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 rounded-full border border-outline-variant/20 bg-surface-container-low px-4 py-2">
        <Terminal size={14} strokeWidth={2} className="text-primary" />
        <span className="text-[9px] font-bold uppercase tracking-widest text-on-surface">
          Trigger Rules: 31
        </span>
      </div>
    </footer>
  )
}
