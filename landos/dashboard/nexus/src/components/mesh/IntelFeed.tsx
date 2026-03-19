import { useState } from 'react'
import { ExternalLink } from 'lucide-react'

type Tab = 'SIGNALS' | 'RULES' | 'CLUSTERS'

const SIGNALS = [
  {
    type: 'SUBDIVISION REMNANT',
    timestamp: '2m ago',
    title: 'Horseshoe Lake Corp — 88 lots identified',
    description: 'Historical plat remnant detected in Augusta Twp. Owner cluster spans 3 adjacent sections.',
    tier: 1,
  },
  {
    type: 'OWNER CLUSTER',
    timestamp: '8m ago',
    title: 'Julian Francis Trust — 12 parcels',
    description: 'Concentrated ownership in Ypsilanti Charter Twp. 4 parcels have active BBO language.',
    tier: 1,
  },
  {
    type: 'PRICE REDUCTION',
    timestamp: '14m ago',
    title: '2.4 acre parcel, Saline — 15% reduction',
    description: 'Listed 180 days. Third price reduction signals motivated seller. Adjacent to approved PUD.',
    tier: 2,
  },
  {
    type: 'MUNICIPAL EVENT',
    timestamp: '22m ago',
    title: 'Ypsilanti Twp adopted Section 108(6)',
    description: '47 parcels affected by new site-condo density allowance. Rescoring triggered.',
    tier: 1,
  },
  {
    type: 'PACKAGE LANGUAGE',
    timestamp: '31m ago',
    title: 'Broker notes: "will sell as package"',
    description: '6 lots in Dexter identified with BBO/package language in MLS remarks field.',
    tier: 2,
  },
]

const RULES = [
  { name: 'Listing Added (RA)', progress: 85, description: 'Classifying Remarks' },
  { name: 'Price Changed (RB)', progress: 100, description: 'Complete' },
  { name: 'BBO Detected (RI)', progress: 62, description: 'Cross-referencing clusters' },
  { name: 'Municipal Scan (RV)', progress: 44, description: 'Processing hearings' },
]

const CLUSTERS = [
  { name: 'Toll Brothers Holdings', lots: 146, type: 'Highest Owner', location: 'Dexter, MI' },
  { name: 'Pulte Homes Corp', lots: 82, type: 'Pipelining', location: 'Saline, MI' },
  { name: 'M/I Homes LLC', lots: 99, type: 'Dormant Supply', location: 'Pittsfield Twp' },
  { name: 'Julian Francis Trust', lots: 12, type: 'Active Cluster', location: 'Ypsilanti Twp' },
]

export function IntelFeed() {
  const [activeTab, setActiveTab] = useState<Tab>('SIGNALS')

  const tabs: Tab[] = ['SIGNALS', 'RULES', 'CLUSTERS']

  return (
    <section className="w-[320px] shrink-0 bg-surface-container-low border-l border-outline-variant/10 flex flex-col overflow-hidden">
      {/* Tab bar */}
      <div className="flex border-b border-outline-variant/10">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-4 text-[10px] font-bold tracking-widest transition-colors ${
              activeTab === tab
                ? 'text-primary border-b-2 border-primary'
                : 'text-on-surface-variant/60 hover:text-on-surface-variant'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Feed content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'SIGNALS' &&
          SIGNALS.map((signal, i) => (
            <div
              key={i}
              className="p-4 bg-surface-container-lowest rounded-xl border border-outline-variant/10 shadow-sm"
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-[9px] font-bold bg-primary/10 text-primary px-2 py-0.5 rounded">
                  {signal.type}
                </span>
                <span className="text-[9px] text-on-surface-variant/50">{signal.timestamp}</span>
              </div>
              <p className="text-xs font-bold text-on-surface">{signal.title}</p>
              <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                {signal.description}
              </p>
              <div className="mt-3 flex items-center justify-between border-t border-outline-variant/5 pt-3">
                <div className="flex items-center gap-1.5">
                  <div
                    className={`w-1.5 h-1.5 rounded-full ${signal.tier === 1 ? 'bg-primary' : 'bg-on-surface-variant/40'}`}
                  />
                  <span
                    className={`text-[10px] font-bold ${signal.tier === 1 ? 'text-primary' : 'text-on-surface-variant/60'}`}
                  >
                    TIER {signal.tier}
                  </span>
                </div>
                <ExternalLink size={12} className="text-on-surface-variant/40" />
              </div>
            </div>
          ))}

        {activeTab === 'RULES' &&
          RULES.map((rule, i) => (
            <div
              key={i}
              className="p-4 bg-surface-container-lowest rounded-xl border border-outline-variant/10 shadow-sm"
            >
              <span className="text-[10px] font-bold text-on-surface-variant uppercase">
                Rule: {rule.name}
              </span>
              <div className="flex items-center justify-between text-[10px] mt-3 mb-1.5">
                <span className="text-on-surface-variant">{rule.description}</span>
                <span className="font-bold text-primary">{rule.progress}%</span>
              </div>
              <div className="w-full bg-surface-container-low h-1 rounded-full overflow-hidden">
                <div
                  className="bg-primary h-full transition-all"
                  style={{ width: `${rule.progress}%` }}
                />
              </div>
            </div>
          ))}

        {activeTab === 'CLUSTERS' && (
          <div className="space-y-2">
            <span className="text-[10px] font-bold text-on-surface-variant/60 uppercase px-1">
              Top Clusters
            </span>
            {CLUSTERS.map((cluster, i) => (
              <div
                key={i}
                className="p-3 bg-surface-container-lowest border border-outline-variant/10 rounded-xl"
              >
                <div className="flex justify-between">
                  <span className="text-xs font-bold">{cluster.name}</span>
                  <span className="text-xs font-bold text-primary">{cluster.lots} lots</span>
                </div>
                <div className="flex justify-between mt-1">
                  <span className="text-[10px] text-on-surface-variant uppercase">
                    {cluster.type}
                  </span>
                  <span className="text-[10px] text-on-surface-variant">{cluster.location}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
