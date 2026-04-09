import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  BarChart3,
  DollarSign,
  Grid3x3,
  MessageSquareText,
  Scale,
  Leaf,
  Loader2,
  AlertTriangle,
} from 'lucide-react'
import { AssessmentHeader } from '../components/assessment/AssessmentHeader'
import { AssessmentView } from '../components/assessment/AssessmentView'
import { ParcelInventory } from '../components/assessment/ParcelInventory'
import { BrokerNotes } from '../components/assessment/BrokerNotes'
import { useStrategicOpportunity } from '../hooks/useStrategicOpportunity'

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
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, isError } = useStrategicOpportunity(id)
  const [activeView, setActiveView] = useState<SubView>('assessment')

  const opp = data?.opportunity
  const parcels = data?.parcels ?? []

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-on-surface-variant">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-sm">Loading assessment data…</p>
      </div>
    )
  }

  // Error / not found
  if (isError || !opp) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-on-surface-variant">
        <AlertTriangle className="h-8 w-8 text-yellow-600 mb-4" />
        <p className="text-sm font-bold mb-1">Opportunity not found</p>
        <p className="text-xs text-on-surface-variant/60">
          {id ? `No data for ID: ${id}` : 'No opportunity ID provided in URL.'}
        </p>
      </div>
    )
  }

  // Build header props from real data
  const entityName = opp.owner_name || opp.name || 'Unknown Entity'
  const address = opp.subdivision_name
    ? `${opp.subdivision_name}, ${opp.municipality_id || 'MI'}`
    : opp.municipality_id || 'Washtenaw County, MI'
  const assetId = opp.opportunity_id.slice(0, 12).toUpperCase()

  return (
    <div className="flex -m-8 min-h-[calc(100vh-120px)]">
      {/* Sub-navigation sidebar */}
      <aside className="w-64 flex-shrink-0 bg-white py-6">
        <div className="px-6 mb-6">
          <h2 className="text-[9px] font-bold uppercase tracking-[0.12em] text-on-surface-variant/60">
            Site Feasibility
          </h2>
        </div>
        <nav className="px-3 space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            const isActive = activeView === item.key
            return (
              <button
                key={item.key}
                onClick={() => setActiveView(item.key)}
                className={`flex items-center gap-3 w-full rounded-xl px-3 py-3 text-left transition-all duration-200 ${
                  isActive
                    ? 'border-l-[3px] border-primary text-primary font-semibold bg-primary/5'
                    : 'border-l-[3px] border-transparent text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface'
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
          assetId={assetId}
          entityName={entityName}
          address={address}
        />

        {activeView === 'assessment' && <AssessmentView opportunity={opp} />}
        {activeView === 'parcels' && <ParcelInventory parcels={parcels} />}
        {activeView === 'broker-notes' && <BrokerNotes opportunity={opp} />}
        {activeView === 'financials' && <ComingSoon label="Financials" />}
        {activeView === 'zoning' && <ComingSoon label="Zoning" />}
        {activeView === 'environmental' && <ComingSoon label="Environmental" />}
      </div>
    </div>
  )
}
