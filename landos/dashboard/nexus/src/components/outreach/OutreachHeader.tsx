interface OutreachHeaderProps {
  activeTab: 'sms' | 'email'
  onTabChange: (tab: 'sms' | 'email') => void
}

export function OutreachHeader({ activeTab, onTabChange }: OutreachHeaderProps) {
  return (
    <div className="flex items-center justify-between bg-surface-container-low px-8 py-3">
      <div className="flex items-center gap-6">
        <h1 className="text-lg font-bold text-on-surface">Outreach Hub</h1>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onTabChange('sms')}
            className={`px-4 py-2 text-[10px] font-bold uppercase tracking-[0.1em] transition-colors ${
              activeTab === 'sms'
                ? 'border-b-2 border-primary text-primary'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            SMS Templates
          </button>
          <button
            onClick={() => onTabChange('email')}
            className={`px-4 py-2 text-[10px] font-bold uppercase tracking-[0.1em] transition-colors ${
              activeTab === 'email'
                ? 'border-b-2 border-primary text-primary'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Email Templates
          </button>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs font-semibold text-on-surface">Horseshoe Lake Corp</span>
        <span className="h-1 w-1 rounded-full bg-outline" />
        <span className="text-xs text-on-surface-variant">Samuel Vail, RE/MAX</span>
      </div>
    </div>
  )
}
