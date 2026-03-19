import { useState } from 'react'
import { Terminal, ArrowUp } from 'lucide-react'

interface LogEntry {
  timestamp: string
  agent: string
  message: string
  highlight?: boolean
}

const MOCK_LOGS: LogEntry[] = [
  {
    timestamp: '14:22:01',
    agent: 'Scout Agent',
    message: 'Evaluating 142 parcels in Scio Twp for immediate density arbitrage...',
  },
  {
    timestamp: '14:22:05',
    agent: 'Municipal Agent',
    message: 'Scanning 2026 Plat recordings for easement conflicts on parcel group B...',
  },
  {
    timestamp: '14:22:12',
    agent: 'Zoning Auditor',
    message: 'RE-CALCULATING: Setback deviation detected on Scio Ridge Rd. Adjusting yield models.',
    highlight: true,
  },
  {
    timestamp: '14:22:18',
    agent: 'Supply Intel',
    message: 'Syncing latest MLS listings for pricing velocity benchmark...',
  },
  {
    timestamp: '14:22:24',
    agent: 'Risk Engine',
    message: 'Flood zone overlay complete — 3 parcels flagged for FEMA panel review.',
  },
  {
    timestamp: '14:22:31',
    agent: 'Permit Tracker',
    message: 'Site plan review #SP-2026-041 approved by Pittsfield Twp Planning Commission.',
    highlight: true,
  },
  {
    timestamp: '14:22:38',
    agent: 'Demographic Agt',
    message: 'Growth corridor heat map updated. NW quadrant shows 12% YoY household formation.',
  },
  {
    timestamp: '14:22:45',
    agent: 'GIS Liaison',
    message: 'Parcel boundary reconciliation complete for cluster CL-0847. 2 overlaps resolved.',
  },
]

export function AgentTerminal() {
  const [input, setInput] = useState('')

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && input.trim()) {
      setInput('')
    }
  }

  return (
    <div className="absolute bottom-6 right-6 w-[400px] z-30">
      <div className="bg-white border border-outline-variant/30 rounded-2xl shadow-ambient-lg overflow-hidden flex flex-col max-h-[320px]">
        {/* Header */}
        <div className="bg-surface-container-low p-3 border-b border-outline-variant/10 flex items-center justify-between">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <Terminal size={14} className="text-primary" />
              <span className="text-[10px] font-bold text-on-surface uppercase tracking-widest">
                Agent Terminal
              </span>
            </div>
            <span className="text-[8px] font-medium text-on-surface-variant/60 uppercase tracking-tight mt-0.5">
              Live Swarm Reasoning Pipeline
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-[#059669] animate-pulse" />
            <span className="text-[9px] font-bold text-on-surface-variant uppercase">
              Swarm Ready
            </span>
          </div>
        </div>

        {/* Log area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5 font-mono" style={{ backgroundColor: '#FAF8F5' }}>
          {MOCK_LOGS.map((entry, i) => (
            <div
              key={i}
              className={`flex items-start gap-2 border-l-2 pl-2 ${
                entry.highlight
                  ? 'border-[#059669]/30 bg-[#059669]/5 rounded-r'
                  : 'border-primary/20'
              }`}
            >
              <span
                className={`text-[9px] shrink-0 font-medium ${
                  entry.highlight ? 'text-[#059669]/60' : 'text-on-surface-variant/50'
                }`}
              >
                [{entry.timestamp}]
              </span>
              <div className="flex flex-col">
                <span
                  className={`text-[9px] font-bold uppercase leading-none mb-1 ${
                    entry.highlight ? 'text-[#059669]' : 'text-primary'
                  }`}
                >
                  {entry.agent}
                </span>
                <p className={`text-[11px] text-on-surface leading-tight ${entry.highlight ? 'italic' : ''}`}>
                  {entry.message}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Input */}
        <div className="p-3 bg-white border-t border-outline-variant/10">
          <div className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full bg-surface-container-low border-none rounded-lg text-xs py-2.5 pl-3 pr-10 focus:ring-1 focus:ring-primary/30 placeholder-on-surface-variant/40 outline-none"
              placeholder="Send swarm instructions..."
            />
            <button
              onClick={() => {
                if (input.trim()) setInput('')
              }}
              className="absolute right-2 text-primary hover:text-primary-container transition-colors"
            >
              <ArrowUp size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
