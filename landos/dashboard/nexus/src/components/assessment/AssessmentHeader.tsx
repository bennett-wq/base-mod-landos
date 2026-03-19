import { MapPin, Phone, MessageSquare, ChevronRight } from 'lucide-react'

interface AssessmentHeaderProps {
  assetId: string
  entityName: string
  address: string
}

export function AssessmentHeader({ assetId, entityName, address }: AssessmentHeaderProps) {
  return (
    <header className="mb-10">
      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.1em] text-primary mb-2">
        <span>Active Entity</span>
        <ChevronRight className="h-3 w-3" />
        <span className="text-on-surface">{entityName}</span>
      </div>
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-xl font-bold tracking-tight text-on-surface">
              Deep Assessment <span className="text-on-surface-variant font-light">(Layer 2)</span>
            </h1>
            <span className="px-2 py-0.5 bg-primary/10 text-primary text-[9px] font-bold uppercase tracking-widest rounded">
              Layer 2 Assessment
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm text-on-surface-variant">
            <span className="font-medium">Asset ID: {assetId}</span>
            <span className="flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5" />
              {address}
            </span>
          </div>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-5 py-2.5 border border-primary text-primary font-bold rounded-lg text-sm hover:bg-surface-container-low transition-all">
            <Phone className="h-4 w-4" />
            Call Broker
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 copper-gradient text-white font-bold rounded-lg text-sm shadow-md hover:scale-[1.02] transition-all">
            <MessageSquare className="h-4 w-4" />
            Message Agent
          </button>
        </div>
      </div>
    </header>
  )
}
