import { Pencil, X } from 'lucide-react'

interface DrawControlsProps {
  active: boolean
  onToggle: () => void
}

export function DrawControls({ active, onToggle }: DrawControlsProps) {
  return (
    <button
      onClick={onToggle}
      className={
        active
          ? 'absolute bottom-8 left-8 z-20 flex items-center gap-2 rounded-full border border-white/20 bg-[#1b1c1a] px-6 py-3 text-sm font-bold text-white shadow-xl transition-all hover:-translate-y-0.5'
          : 'absolute bottom-8 left-8 z-20 flex items-center gap-2 rounded-full bg-gradient-to-br from-[#7f5313] to-[#9b6b2a] px-6 py-3 text-sm font-bold text-white shadow-xl transition-all hover:-translate-y-0.5'
      }
    >
      {active ? (
        <>
          <X size={16} /> Cancel Draw
        </>
      ) : (
        <>
          <Pencil size={16} /> Draw Territory
        </>
      )}
    </button>
  )
}
