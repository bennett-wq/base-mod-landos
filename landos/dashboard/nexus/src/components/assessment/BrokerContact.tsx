import { Phone, Mail } from 'lucide-react'

export function BrokerContact() {
  return (
    <div className="bg-white rounded-xl p-6 ghost-border">
      <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-5">
        Primary Broker Contact
      </h3>
      <div className="flex items-start gap-4 mb-5">
        <div className="h-16 w-16 rounded-full copper-gradient flex items-center justify-center flex-shrink-0">
          <span className="text-white text-lg font-bold">SV</span>
        </div>
        <div>
          <p className="text-lg font-bold text-on-surface">Samuel Vail</p>
          <p className="text-sm text-on-surface-variant">RE/MAX Platinum</p>
        </div>
      </div>
      <div className="space-y-3 mb-6">
        <div className="flex items-center gap-3 text-sm">
          <Phone className="h-4 w-4 text-primary" />
          <span className="text-on-surface-variant font-medium">(734) 555-0192</span>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <Mail className="h-4 w-4 text-primary" />
          <span className="text-on-surface-variant font-medium">svail@remax-platinum.com</span>
        </div>
      </div>
      <div className="space-y-2">
        <button className="w-full copper-gradient text-white py-2.5 rounded-lg font-bold text-sm shadow-md transition-all active:scale-[0.98] flex items-center justify-center gap-2">
          <Phone className="h-4 w-4" />
          Call Broker
        </button>
        <button className="w-full border border-outline-variant/30 hover:bg-surface-container-low text-on-surface py-2.5 rounded-lg font-bold text-sm transition-all flex items-center justify-center gap-2">
          <Mail className="h-4 w-4" />
          Send Message
        </button>
      </div>
    </div>
  )
}
