import { useState } from 'react'
import {
  BarChart3,
  DollarSign,
  Grid3x3,
  MessageSquareText,
  Scale,
  Leaf,
} from 'lucide-react'
import { AssessmentHeader } from '../components/assessment/AssessmentHeader'
import { AssessmentView } from '../components/assessment/AssessmentView'
import { ParcelInventory } from '../components/assessment/ParcelInventory'
import { BrokerNotes } from '../components/assessment/BrokerNotes'

type SubView = 'assessment' | 'financials' | 'parcels' | 'broker-notes' | 'zoning' | 'environmental'

const NAV_ITEMS: { key: SubView; label: string; icon: typeof BarChart3 }[] = [
  { key: 'assessment', label: 'Assessment', icon: BarChart3 },
  { key: 'financials', label: 'Financials', icon: DollarSign },
  { key: 'parcels', label: 'Parcels', icon: Grid3x3 },
  { key: 'broker-notes', label: 'Broker Notes', icon: MessageSquareText },
  { key: 'zoning', label: 'Zoning', icon: Scale },
  { key: 'environmental', label: 'Environmental', icon: Leaf },
]

function ComingSoon({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-32 text-on-surface-variant">
      <p className="text-[10px] font-bold uppercase tracking-widest mb-2">{label}</p>
      <p className="text-sm">Coming soon — under development.</p>
    </div>
  )
}

export default function DeepAssessmentPage() {
  const [activeView, setActiveView] = useState<SubView>('assessment')

  return (
    <div className="flex -m-8 min-h-[calc(100vh-120px)]">
      {/* Sub-navigation sidebar */}
      <aside className="w-64 flex-shrink-0 bg-white border-r border-outline-variant/10 py-6">
        <div className="px-6 mb-6">
          <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
            Site Feasibility
          </h2>
        </div>
        <nav className="px-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            const isActive = activeView === item.key
            return (
              <button
                key={item.key}
                onClick={() => setActiveView(item.key)}
                className={`flex items-center gap-3 w-full px-3 py-3 text-left transition-all ${
                  isActive
                    ? 'border-l-[3px] border-primary text-primary font-semibold bg-primary/5'
                    : 'text-on-surface-variant hover:bg-surface-container-low hover:text-primary'
                }`}
              >
                <Icon className="h-[18px] w-[18px]" />
                <span className="text-sm">{item.label}</span>
              </button>
            )
          })}
        </nav>
      </aside>

      {/* Main content area */}
      <div className="flex-1 overflow-y-auto p-8 bg-surface">
        <AssessmentHeader
          assetId="NEX-88129-WAS"
          entityName="Horseshoe Lake Corporation"
          address="Horseshoe Lake Rd, Augusta Township, MI"
        />

        {activeView === 'assessment' && <AssessmentView />}
        {activeView === 'parcels' && <ParcelInventory />}
        {activeView === 'broker-notes' && <BrokerNotes />}
        {activeView === 'financials' && <ComingSoon label="Financials" />}
        {activeView === 'zoning' && <ComingSoon label="Zoning" />}
        {activeView === 'environmental' && <ComingSoon label="Environmental" />}
      </div>
    </div>
  )
}
