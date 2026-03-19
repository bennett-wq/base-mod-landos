const PARCELS = [
  {
    id: 'H-12-04-300-012',
    lotSize: '12.4 ac',
    zoning: 'R-1',
    status: 'vacant' as const,
    findings: 'Slight slope to North; optimal for Hawthorne model placement.',
  },
  {
    id: 'H-12-04-300-013',
    lotSize: '8.1 ac',
    zoning: 'R-1',
    status: 'listed' as const,
    findings: 'Includes existing retention pond; high ecological value noted.',
  },
  {
    id: 'H-12-04-300-014',
    lotSize: '15.2 ac',
    zoning: 'AG',
    status: 'vacant' as const,
    findings: 'Direct road access point; requires minor soil stabilization.',
  },
  {
    id: 'H-12-04-300-015',
    lotSize: '4.5 ac',
    zoning: 'R-1',
    status: 'vacant' as const,
    findings: 'Utility easement bisects parcel; limits vertical build footprint.',
  },
  {
    id: 'H-12-04-301-001',
    lotSize: '6.8 ac',
    zoning: 'R-2',
    status: 'listed' as const,
    findings: 'Adjacent to municipal water hookup; minimal infrastructure cost.',
  },
  {
    id: 'H-12-04-301-002',
    lotSize: '9.3 ac',
    zoning: 'R-1',
    status: 'vacant' as const,
    findings: 'Flat topography, sandy loam soil. Ideal for slab-on-grade.',
  },
  {
    id: 'H-12-04-301-003',
    lotSize: '3.7 ac',
    zoning: 'R-1',
    status: 'vacant' as const,
    findings: 'Narrow frontage; may require variance for setback compliance.',
  },
  {
    id: 'H-12-04-301-004',
    lotSize: '11.0 ac',
    zoning: 'AG',
    status: 'vacant' as const,
    findings: 'Former agricultural use; Phase 1 ESA clear. Ready for development.',
  },
]

export function ParcelInventory() {
  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Parcel Inventory
        </h3>
        <span className="px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-bold rounded">
          {PARCELS.length} Parcels
        </span>
      </div>

      <div className="bg-white rounded-xl overflow-hidden ghost-border">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-surface-container-low/50">
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Parcel ID
                </th>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Lot Size
                </th>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Zoning
                </th>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Status
                </th>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Agent Findings
                </th>
              </tr>
            </thead>
            <tbody>
              {PARCELS.map((parcel, i) => (
                <tr
                  key={parcel.id}
                  className={i % 2 === 1 ? 'bg-surface-container-low/30' : 'bg-white'}
                >
                  <td className="px-6 py-4 text-sm font-bold text-primary tracking-tight">
                    {parcel.id}
                  </td>
                  <td className="px-6 py-4 text-sm font-medium">{parcel.lotSize}</td>
                  <td className="px-6 py-4 text-sm font-medium">{parcel.zoning}</td>
                  <td className="px-6 py-4">
                    {parcel.status === 'listed' ? (
                      <span className="px-2 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-bold uppercase">
                        Listed
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant text-[10px] font-bold uppercase">
                        Vacant
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm italic text-on-surface-variant leading-relaxed max-w-xs">
                    {parcel.findings}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
