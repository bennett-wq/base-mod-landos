import { useState } from 'react'
import { Copy, Send } from 'lucide-react'
import { LiveThinking } from './LiveThinking'

const EMAIL_TEMPLATES = [
  {
    id: 'fatigue',
    title: 'Developer Fatigue',
    description: 'Targeting long-held inventory with stalled construction activity or zoning delays.',
  },
  {
    id: 'stale',
    title: 'Stale Listing Acquisition',
    description: 'Focus on properties with 180+ days on market without price adjustments.',
  },
  {
    id: 'direct',
    title: 'Direct Acquisition Offer',
    description: 'Direct, high-liquidity offers for unlisted parcels within priority clusters.',
  },
  {
    id: 'zoning',
    title: 'Zoning Pivot Opportunity',
    description: 'Inquiry regarding entitlement changes in newly designated green belts.',
  },
] as const

const PLACEHOLDERS = ['{{OwnerName}}', '{{LotCount}}', '{{AvgLandValue}}', '{{Township}}', '{{MarginPct}}']

const DEFAULT_EMAIL = `Dear {{OwnerName}},

I've been monitoring the Horseshoe Lake cluster and noticed the {{LotCount}} lots currently under your management. Given the current market shift and the average land value of {{AvgLandValue}} in the {{Township}} sector, our fund is interested in a consolidated acquisition strategy.

We specialize in taking on "stalled" development projects where entitlements are already in place but vertical construction hasn't commenced.

Are you available for a brief call Thursday to discuss a clean exit for your client?

Best regards,
BaseMod Acquisition Team`

export function EmailTemplateEditor() {
  const [activeTemplate, setActiveTemplate] = useState('fatigue')
  const [subject, setSubject] = useState(
    'Portfolio Inquiry: Horseshoe Lake Development Opportunities'
  )
  const [body, setBody] = useState(DEFAULT_EMAIL)

  const insertPlaceholder = (placeholder: string) => {
    setBody((prev) => prev + placeholder)
  }

  return (
    <div className="flex flex-1 gap-0 overflow-hidden">
      {/* Left — Template Library */}
      <div className="w-[280px] shrink-0 overflow-y-auto bg-surface-container-low p-5">
        <span className="mb-4 block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Email Templates
        </span>
        <div className="space-y-3">
          {EMAIL_TEMPLATES.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTemplate(t.id)}
              className={`w-full rounded-xl p-4 text-left transition-all ${
                activeTemplate === t.id
                  ? 'border-l-4 border-primary bg-white shadow-sm'
                  : 'bg-white/60 hover:bg-white'
              }`}
            >
              <span className="text-sm font-bold text-on-surface">{t.title}</span>
              <span className="mt-1 block text-xs leading-relaxed text-on-surface-variant">
                {t.description}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Right — Email Editor */}
      <div className="flex flex-1 flex-col overflow-y-auto p-6">
        <div className="rounded-xl bg-white p-6 shadow-ambient">
          {/* Recipient header */}
          <div className="mb-6 flex items-center gap-4 border-b border-surface-container pb-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container">
              <span className="text-sm font-bold text-on-surface-variant">SV</span>
            </div>
            <div>
              <div className="text-sm font-bold text-on-surface">Samuel Vail</div>
              <div className="text-xs text-on-surface-variant">
                Listing Broker &middot; Horseshoe Lake Corporation
              </div>
            </div>
          </div>

          {/* Subject line */}
          <div className="mb-4 space-y-1">
            <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
              Subject Line
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full rounded-full border-transparent bg-surface-container-low px-5 py-2.5 text-sm font-medium text-on-surface focus:border-primary/40 focus:outline-none focus:ring-0"
              style={{ outline: '1px solid rgba(212, 196, 180, 0.2)' }}
            />
          </div>

          {/* Email body */}
          <div className="mb-4 space-y-1">
            <div className="flex items-center justify-between">
              <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                Email Body
              </label>
              <div className="flex gap-1.5">
                {PLACEHOLDERS.map((p) => (
                  <button
                    key={p}
                    onClick={() => insertPlaceholder(p)}
                    className="rounded bg-surface-container px-2 py-0.5 text-[10px] font-bold text-on-surface-variant transition-colors hover:bg-surface-container-high"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={12}
              className="w-full rounded-xl border-transparent bg-surface-container-low px-6 py-5 text-sm leading-relaxed text-on-surface focus:border-primary/40 focus:outline-none focus:ring-0"
              style={{ outline: '1px solid rgba(212, 196, 180, 0.2)' }}
            />
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-2">
            <button className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-primary transition-colors hover:underline">
              <Copy size={14} />
              Copy to Clipboard
            </button>
            <div className="flex gap-3">
              <button className="rounded-full bg-surface-container px-6 py-2.5 text-sm font-bold text-on-surface transition-colors hover:bg-surface-variant">
                Save Draft
              </button>
              <button className="copper-gradient flex items-center gap-2 rounded-full px-8 py-2.5 text-sm font-bold text-on-primary shadow-md transition-transform active:scale-95">
                <Send size={14} />
                Send Outreach
              </button>
            </div>
          </div>
        </div>

        {/* Live Thinking Terminal */}
        <div className="mt-6">
          <LiveThinking />
        </div>
      </div>
    </div>
  )
}
