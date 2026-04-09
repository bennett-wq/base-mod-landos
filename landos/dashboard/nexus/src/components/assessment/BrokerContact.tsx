import { Phone, Mail, Users } from 'lucide-react'

interface BrokerContactProps {
  agents: string[]
  offices: string[]
}

export function BrokerContact({ agents, offices }: BrokerContactProps) {
  const primaryAgent = agents[0] || null
  const primaryOffice = offices[0] || null

  if (!primaryAgent && !primaryOffice) {
    return (
      <div className="bg-white rounded-xl p-6 ghost-border">
        <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-5">
          Broker Contact
        </h3>
        <div className="flex flex-col items-center justify-center py-6 text-on-surface-variant">
          <Users className="h-6 w-6 text-on-surface-variant/30 mb-3" />
          <p className="text-sm">No broker information available.</p>
        </div>
      </div>
    )
  }

  const initials = primaryAgent
    ? primaryAgent.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
    : '??'

  return (
    <div className="bg-white rounded-xl p-6 ghost-border">
      <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant mb-5">
        Primary Broker Contact
      </h3>
      <div className="flex items-start gap-4 mb-5">
        <div className="h-16 w-16 rounded-full copper-gradient flex items-center justify-center flex-shrink-0">
          <span className="text-white text-lg font-bold">{initials}</span>
        </div>
        <div>
          <p className="text-lg font-bold text-on-surface">{primaryAgent || 'Unknown Agent'}</p>
          <p className="text-sm text-on-surface-variant">{primaryOffice || 'Office unknown'}</p>
        </div>
      </div>

      {/* Additional agents */}
      {agents.length > 1 && (
        <div className="mb-5 space-y-2">
          <h4 className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
            Other Agents ({agents.length - 1})
          </h4>
          {agents.slice(1).map((agent, i) => (
            <div key={i} className="text-sm text-on-surface-variant">{agent}</div>
          ))}
        </div>
      )}

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
