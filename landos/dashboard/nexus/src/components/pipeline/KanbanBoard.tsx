import { KanbanColumn } from './KanbanColumn'
import type { Deal } from './DealCard'

interface Stage {
  name: string
  deals: Deal[]
}

const STAGES: Stage[] = [
  {
    name: 'DISCOVERED',
    deals: [
      {
        id: 'd1',
        title: 'Horseshoe Lake Corp',
        tier: 1,
        entityType: 'CORPORATION',
        location: 'Augusta Twp, Washtenaw',
        lotCount: 92,
        score: 67,
        signal: 'HIGHEST',
        updatedAgo: 'Updated 2h ago',
      },
      {
        id: 'd2',
        title: 'Julian Francis',
        entityType: 'INDIVIDUAL',
        location: 'Superior Twp',
        lotCount: 34,
        score: 42,
        updatedAgo: 'Updated 5h ago',
      },
      {
        id: 'd3',
        title: 'Toll Brothers Holdings',
        tier: 1,
        entityType: 'OWNER',
        location: 'Augusta Twp',
        lotCount: 146,
        score: 71,
        signal: 'HIGHEST',
        updatedAgo: 'Updated 2h ago',
      },
      {
        id: 'd4',
        title: 'M/I Homes',
        entityType: 'BUILDER',
        location: 'York Twp',
        lotCount: 99,
        score: 55,
        signal: 'HIGH',
        updatedAgo: 'Updated 6h ago',
      },
    ],
  },
  {
    name: 'RESEARCHED',
    deals: [
      {
        id: 'r1',
        title: 'PulteGroup',
        location: 'Pittsfield Twp',
        lotCount: 59,
        score: 48,
        updatedAgo: 'Updated 4h ago',
      },
      {
        id: 'r2',
        title: 'Lennar',
        location: 'Scio Twp',
        lotCount: 210,
        score: 52,
        updatedAgo: 'Updated 8h ago',
      },
      {
        id: 'r3',
        title: 'NVR Inc',
        location: 'Lima Twp',
        lotCount: 44,
        score: 39,
        updatedAgo: 'Updated 1d ago',
      },
    ],
  },
  {
    name: 'OUTREACH DRAFTED',
    deals: [
      {
        id: 'o1',
        title: 'Meritage Homes',
        tier: 1,
        location: 'Saline',
        lotCount: 78,
        note: 'Proposal for mixed-use assemblage finalized.',
        signal: 'HIGH',
        updatedAgo: 'Updated 3h ago',
      },
      {
        id: 'o2',
        title: 'Taylor Morrison',
        location: 'Dexter Twp',
        lotCount: 36,
        note: 'Initial outreach letter drafted.',
        updatedAgo: 'Updated 12h ago',
      },
    ],
  },
  {
    name: 'CONTACTED',
    deals: [
      {
        id: 'c1',
        title: 'Century Complete',
        contactStatus: 'Sent / Awaiting',
        lastContact: 'Mar 12',
        updatedAgo: 'Updated 1d ago',
      },
      {
        id: 'c2',
        title: 'Saline Valley Farms',
        contactStatus: 'Follow-up Scheduled',
        lastContact: 'Mar 15',
        updatedAgo: 'Updated 8h ago',
      },
    ],
  },
  {
    name: 'NEGOTIATING',
    deals: [
      {
        id: 'n1',
        title: 'Bank of Ann Arbor',
        tier: 1,
        lotCount: 28,
        location: 'Ann Arbor Twp',
        askingPrice: '$4.2M Asking',
        negotiationStatus: 'In Counter',
        updatedAgo: 'Updated 6h ago',
      },
    ],
  },
  {
    name: 'UNDER CONTRACT',
    deals: [
      {
        id: 'u1',
        title: 'Westover Hills',
        progressPercent: 65,
        dueDiligence: 'Due Diligence: Day 39/60',
        updatedAgo: 'Updated 1h ago',
      },
    ],
  },
  {
    name: 'CLOSED',
    deals: [],
  },
]

export const TOTAL_DEALS = STAGES.reduce((sum, s) => sum + s.deals.length, 0)

export function KanbanBoard() {
  return (
    <div className="kanban-scroll flex gap-6 overflow-x-auto pb-8 -mx-8 px-8 snap-x snap-mandatory">
      {STAGES.map((stage) => (
        <KanbanColumn key={stage.name} name={stage.name} deals={stage.deals} />
      ))}
    </div>
  )
}
