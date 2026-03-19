import { Rocket } from 'lucide-react'

interface LaunchBarProps {
  onClear: () => void
  onLaunch: () => void
}

export function LaunchBar({ onClear, onLaunch }: LaunchBarProps) {
  return (
    <div className="absolute bottom-8 left-1/2 z-30 flex -translate-x-1/2 items-center gap-6 rounded-full bg-[#1b1c1a] px-6 py-3 shadow-2xl">
      <div className="flex items-center gap-3">
        <Rocket size={18} className="text-[#f7bb73]" />
        <div className="text-sm text-white">
          <span className="font-bold">Launch Mission</span>
          <span className="ml-2 text-white/40">Scan 1,847 parcels in 4 townships</span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onLaunch}
          className="rounded-full bg-[#7f5313] px-4 py-1.5 text-xs font-bold text-white transition-colors hover:bg-[#9b6b2a]"
        >
          Launch &rarr;
        </button>
        <button
          onClick={onClear}
          className="px-3 py-1.5 text-xs font-bold text-white/40 transition-colors hover:text-white"
        >
          Clear
        </button>
      </div>
    </div>
  )
}
