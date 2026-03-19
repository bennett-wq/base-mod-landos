import { CheckCircle } from 'lucide-react'

export function EmptyColumn() {
  return (
    <div className="border-2 border-dashed border-outline-variant/20 rounded-xl p-8 flex flex-col items-center justify-center text-center">
      <CheckCircle className="w-8 h-8 text-stone-300 mb-3" />
      <p className="text-xs text-stone-400 leading-relaxed font-medium">
        No closed deals yet
      </p>
      <button className="mt-4 text-[10px] font-bold text-primary uppercase tracking-widest hover:underline">
        View Archives
      </button>
    </div>
  )
}
