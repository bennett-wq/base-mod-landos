import { MapPin, Phone, MessageSquare, ChevronRight } from 'lucide-react'

interface AssessmentHeaderProps {
  assetId: string
  entityName: string
  address: string
}

export function AssessmentHeader({ assetId, entityName, address }: AssessmentHeaderProps) {
  return (
    <header className="mb-10">
      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.1em] text-primary mb-3">
        <span>Active Entity</span>
        <ChevronRight className="h-3 w-3 text-on-surface-variant/40" />
        <span className="text-on-surface">{entityName}</span>
      </div>
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-xl font-bold tracking-tight text-on-surface">
              Deep Assessment <span className="text-on-surface-variant/50 font-normal">(Layer 2)</span>
            </h1>
            <span className="px-2.5 py-0.5 bg-primary/8 text-primary text-[9px] font-bold uppercase tracking-[0.1em] rounded-md">
              Layer 2
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm text-on-surface-variant/70">
            <span className="font-medium tabular-nums">Asset ID: {assetId}</span>
            <span className="flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5" />
              {address}
            </span>
          </div>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-5 py-2.5 bg-surface-container-low text-on-surface-variant font-bold rounded-lg text-[10px] uppercase tracking-[0.08em] hover:bg-surface-container transition-all">
            <Phone className="h-3.5 w-3.5" />
            Call Broker
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 copper-gradient text-white font-bold rounded-lg text-[10px] uppercase tracking-[0.08em] shadow-md shadow-primary/15 transition-all">
            <MessageSquare className="h-3.5 w-3.5" />
            Message Agent
          </button>
        </div>
      </div>
    </header>
  )
}
