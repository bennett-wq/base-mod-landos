import { Lock, Globe, History } from 'lucide-react'

interface BrokerNote {
  type: 'private' | 'public'
  mlsNumber: string
  address: string
  text: string
  timestamp: string
}

const NOTES: BrokerNote[] = [
  {
    type: 'private',
    mlsNumber: 'MLS #23033936',
    address: '9286 Potterville Drive',
    text: 'Expired. You may walk the lots. Please be respectful of adjacent private properties. Highland Ave. has not been developed east of Raphael St. but it is a platted private road. Seller highly motivated — bridge loan expires in 45 days.',
    timestamp: 'Updated 2 days ago',
  },
  {
    type: 'public',
    mlsNumber: 'MLS #23041122',
    address: 'Parcel Group Alpha — Six Mile Rd',
    text: '5 Vacant lots being sold together. Each lot is 30ft x 100ft. Lot #1 has frontage on Six Mile Rd. Lot #2 & Lot #3 are contiguous. Excellent opportunity for small residential cluster development.',
    timestamp: 'Public Listing',
  },
  {
    type: 'private',
    mlsNumber: 'PORTFOLIO-20',
    address: 'Estate Settlement — Horseshoe Lake',
    text: 'Seller highly motivated due to estate settlement. Open to creative financing or package deals for all 20 parcels. Previous buyer fell through due to personal reasons, not feasibility. Environmental reports clean.',
    timestamp: 'Confidential Intel',
  },
  {
    type: 'public',
    mlsNumber: 'SCIO-39',
    address: 'Scio Twp Cluster Development',
    text: 'Rare opportunity in Scio Twp. 39 parcels with proximity to utilities. Township has expressed interest in supporting residential development. Zoning is currently AG but variance expected to be approved.',
    timestamp: 'Market Insight',
  },
  {
    type: 'private',
    mlsNumber: 'MLS #23055701',
    address: '1140 Horseshoe Lake Rd',
    text: 'Stranded lot — sewer line 200ft away. Owner has not responded to previous offers but neighbor reports financial distress. Adjacent parcel H-12-04-301-002 also owned by same entity.',
    timestamp: 'Updated 5 days ago',
  },
  {
    type: 'public',
    mlsNumber: 'MLS #23060044',
    address: '2885 Augusta Township Line',
    text: 'Large acreage parcel with road frontage on two sides. Topography is flat with mature tree line on northern boundary. Soil report available upon request. Priced below recent comps for quick sale.',
    timestamp: 'Active Listing',
  },
]

export function BrokerNotes() {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Broker Intelligence Notes
        </h3>
        <div className="flex gap-2">
          <span className="px-2 py-1 text-[9px] font-bold bg-error/10 text-error rounded uppercase">
            Private Disclosure
          </span>
          <span className="px-2 py-1 text-[9px] font-bold bg-surface-container text-on-surface-variant rounded uppercase">
            Public Record
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {NOTES.map((note) => {
          const isPrivate = note.type === 'private'
          return (
            <div
              key={note.mlsNumber}
              className={`bg-white rounded-xl p-5 border border-outline-variant/10 ${
                isPrivate ? 'border-l-4 border-l-error/50' : ''
              }`}
            >
              <div className="flex justify-between items-start mb-3">
                {isPrivate ? (
                  <span className="px-2 py-0.5 bg-error/10 text-error text-[9px] font-bold rounded uppercase">
                    Private
                  </span>
                ) : (
                  <span className="px-2 py-0.5 bg-surface-container text-on-surface-variant text-[9px] font-bold rounded uppercase">
                    Public
                  </span>
                )}
                <span className="font-mono text-[11px] font-bold text-on-surface-variant">
                  {note.mlsNumber}
                </span>
              </div>
              <h4 className="text-sm font-bold text-on-surface mb-2">{note.address}</h4>
              <p className="text-sm leading-relaxed text-on-surface-variant mb-4">{note.text}</p>
              <div className="pt-3 border-t border-outline-variant/10 flex items-center gap-2 text-[10px] text-on-surface-variant font-medium">
                {isPrivate ? (
                  <>
                    <Lock className="h-3 w-3" />
                    <History className="h-3 w-3" />
                  </>
                ) : (
                  <Globe className="h-3 w-3" />
                )}
                {note.timestamp}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
