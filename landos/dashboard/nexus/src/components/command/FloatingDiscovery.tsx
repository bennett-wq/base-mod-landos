import { ShieldCheck } from 'lucide-react'

export function FloatingDiscovery() {
  return (
    <div className="absolute top-12 left-1/2 -translate-x-1/2 w-[340px] z-30 pointer-events-auto">
      <div
        className="bg-white/90 backdrop-blur-xl border border-primary/30 rounded-2xl p-4 shadow-2xl"
        style={{
          boxShadow: '0 0 20px rgba(127, 83, 19, 0.4), 0 0 40px rgba(127, 83, 19, 0.2)',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-primary" />
            <span className="text-[10px] font-bold text-primary uppercase tracking-widest">
              Live Discovery
            </span>
          </div>
          <span className="text-[9px] text-on-surface-variant font-mono">ID: NW-2024-X</span>
        </div>

        <div className="space-y-3">
          {/* Owner row */}
          <div className="flex items-center gap-3 p-2 rounded-lg bg-surface-container-low/50">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">
              SV
            </div>
            <div className="flex-1">
              <p className="text-[10px] text-on-surface-variant font-bold uppercase">
                Primary Owner
              </p>
              <p className="text-sm font-bold text-on-surface leading-tight">Samuel Vail</p>
            </div>
          </div>

          {/* Contact grid */}
          <div className="grid grid-cols-2 gap-2">
            <div className="p-2 rounded-lg bg-white/50 border border-outline-variant/10">
              <p className="text-[9px] text-on-surface-variant font-bold uppercase">Phone</p>
              <p className="text-xs font-semibold">(734) 555-0192</p>
            </div>
            <div className="p-2 rounded-lg bg-white/50 border border-outline-variant/10 overflow-hidden">
              <p className="text-[9px] text-on-surface-variant font-bold uppercase">Email</p>
              <p className="text-xs font-semibold truncate">svail@remax-platinum.com</p>
            </div>
          </div>

          {/* Broker / Trust */}
          <div className="p-2 rounded-lg bg-primary/5 border border-primary/10">
            <p className="text-[9px] text-primary font-bold uppercase">
              Listing Broker / Trust
            </p>
            <div className="flex justify-between items-center mt-0.5">
              <p className="text-xs font-bold text-on-surface">Julian Francis Trust</p>
              <p className="text-[10px] font-mono font-bold text-primary">(734) 555-0481</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
