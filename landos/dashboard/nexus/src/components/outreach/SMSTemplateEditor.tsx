import { useState } from 'react'
import { ChevronLeft, Battery, Signal, Wifi } from 'lucide-react'

const SMS_TEMPLATES = [
  { id: 'followup', label: 'Follow-up', category: 'Follow-up Sequences' },
  { id: 'pricing', label: 'Pricing Update', category: 'Pricing Adjustments' },
  { id: 'model', label: 'New Model Match', category: 'Model Matching' },
  { id: 'market', label: 'Market Insight', category: 'Market Intelligence' },
] as const

const PLACEHOLDERS = ['{{OwnerName}}', '{{LotID}}', '{{Township}}', '{{LotCount}}', '{{AvgLandValue}}']

const DEFAULT_SMS = `Hi {{OwnerName}}, Samuel Vail here from BaseMod. We've identified {{LotCount}} lots near {{Township}} as prime candidates for our modular development program. Are you open to a quick call this week?`

const MOCK_VALUES: Record<string, string> = {
  '{{OwnerName}}': 'Michael Rossi',
  '{{LotID}}': 'Lot #442-B',
  '{{Township}}': 'Willis, MI',
  '{{LotCount}}': '20',
  '{{AvgLandValue}}': '$47,500',
}

function resolveTemplate(text: string): string {
  let resolved = text
  for (const [key, val] of Object.entries(MOCK_VALUES)) {
    resolved = resolved.split(key).join(val)
  }
  return resolved
}

export function SMSTemplateEditor() {
  const [activeTemplate, setActiveTemplate] = useState('followup')
  const [smsBody, setSmsBody] = useState(DEFAULT_SMS)

  const charCount = smsBody.length
  const segments = Math.ceil(charCount / 160) || 1

  const insertPlaceholder = (placeholder: string) => {
    setSmsBody((prev) => prev + placeholder)
  }

  return (
    <div className="flex flex-1 gap-0 overflow-hidden">
      {/* Left — Template Library */}
      <div className="w-[240px] shrink-0 overflow-y-auto bg-surface-container-low p-5">
        <span className="mb-4 block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          SMS Templates
        </span>
        <div className="space-y-2">
          {SMS_TEMPLATES.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTemplate(t.id)}
              className={`w-full rounded-xl p-3 text-left text-xs font-bold transition-all ${
                activeTemplate === t.id
                  ? 'border-l-4 border-primary bg-primary/5 text-on-surface'
                  : 'bg-white text-on-surface-variant hover:bg-white/80'
              }`}
            >
              {t.label}
              <span className="mt-0.5 block text-[9px] font-medium text-on-surface-variant/60">
                {t.category}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Center — SMS Editor */}
      <div className="flex flex-1 flex-col overflow-y-auto p-6">
        <label className="mb-2 block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          SMS Body
        </label>
        <textarea
          value={smsBody}
          onChange={(e) => setSmsBody(e.target.value)}
          className="min-h-[200px] w-full resize-none rounded-xl border border-outline-variant/10 bg-white p-5 font-mono text-sm leading-relaxed text-on-surface-variant focus:border-primary/40 focus:outline-none focus:ring-1 focus:ring-primary/20"
        />
        <div className="mt-2 text-[9px] text-on-surface-variant">
          {charCount} / 160 characters &middot; {segments} segment{segments > 1 ? 's' : ''}
        </div>

        <div className="mt-4">
          <label className="mb-2 block text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
            Dynamic Placeholders
          </label>
          <div className="flex flex-wrap gap-2">
            {PLACEHOLDERS.map((p) => (
              <button
                key={p}
                onClick={() => insertPlaceholder(p)}
                className="rounded-full bg-surface-container-low px-3 py-1 text-[9px] font-semibold text-on-surface transition-colors hover:border-primary/40"
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 flex gap-3">
          <button className="flex-1 copper-gradient flex items-center justify-center gap-2 rounded-lg py-3 text-sm font-bold text-on-primary shadow-md">
            Send SMS
          </button>
          <button className="rounded-lg border border-outline-variant/30 px-5 py-3 text-sm font-bold text-on-surface-variant transition-colors hover:bg-surface-container-low">
            Save Draft
          </button>
        </div>
      </div>

      {/* Right — Phone Preview */}
      <div className="flex w-[280px] shrink-0 flex-col items-center bg-surface-container-low px-4 py-6">
        <span className="mb-4 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Recipient Preview
        </span>

        {/* iPhone mockup */}
        <div className="relative w-[260px] overflow-hidden rounded-[2.5rem] border-[6px] border-stone-800 bg-white shadow-2xl">
          {/* Notch */}
          <div className="absolute left-1/2 top-0 z-10 h-5 w-28 -translate-x-1/2 rounded-b-2xl bg-stone-800" />

          {/* Screen */}
          <div className="flex flex-col bg-[#f2f2f7] pt-7">
            {/* Status bar */}
            <div className="flex items-center justify-between px-6 pb-1 text-[9px] font-semibold text-stone-800">
              <span>9:41</span>
              <div className="flex items-center gap-1">
                <Signal size={10} />
                <Wifi size={10} />
                <Battery size={10} />
              </div>
            </div>

            {/* Chat header */}
            <div className="flex flex-col items-center border-b border-gray-300 px-4 pb-3">
              <div className="mb-1 flex h-9 w-9 items-center justify-center rounded-full bg-gray-400">
                <span className="text-xs font-bold text-white">SV</span>
              </div>
              <span className="text-[10px] font-semibold text-gray-800">Samuel Vail</span>
            </div>

            {/* Chat area */}
            <div className="flex min-h-[280px] flex-col gap-3 p-3">
              <div className="self-center rounded-full bg-gray-200/50 px-3 py-0.5">
                <span className="text-[9px] font-medium text-gray-500">Today 2:42 PM</span>
              </div>

              {/* Message bubble */}
              <div className="max-w-[85%] self-start rounded-2xl rounded-bl-none bg-[#E9E9EB] p-3 text-[11px] leading-snug text-black">
                {resolveTemplate(smsBody)}
              </div>

              <span className="pl-1 text-[9px] text-gray-400">Just now</span>
            </div>

            {/* Input bar */}
            <div className="border-t border-gray-200 bg-white p-2.5">
              <div className="flex items-center gap-2">
                <div className="flex h-7 flex-1 items-center rounded-full border border-gray-300 px-3">
                  <span className="text-[10px] text-gray-300">iMessage</span>
                </div>
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-500">
                  <ChevronLeft size={12} className="rotate-[225deg] text-white" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
