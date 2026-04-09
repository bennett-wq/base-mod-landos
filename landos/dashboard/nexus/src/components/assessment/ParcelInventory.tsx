import type { ApiParcel } from '@/lib/api'

interface ParcelInventoryProps {
  parcels: ApiParcel[]
}

export function ParcelInventory({ parcels }: ParcelInventoryProps) {
  if (parcels.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-on-surface-variant">
        <p className="text-[10px] font-bold uppercase tracking-widest mb-2">Parcel Inventory</p>
        <p className="text-sm">No parcel data available for this opportunity.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Parcel Inventory
        </h3>
        <span className="px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-bold rounded">
          {parcels.length} Parcels
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
                  Acreage
                </th>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Zoning
                </th>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Status
                </th>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-widest text-on-surface-variant">
                  Owner
                </th>
              </tr>
            </thead>
            <tbody>
              {parcels.map((parcel, i) => {
                const displayId = parcel.source_system_ids?.regrid_id
                  || parcel.parcel_number_raw
                  || parcel.parcel_id
                const status = parcel.vacancy_status?.toUpperCase() ?? 'UNKNOWN'
                const isVacant = status === 'VACANT'
                return (
                  <tr
                    key={parcel.parcel_id}
                    className={i % 2 === 1 ? 'bg-surface-container-low/30' : 'bg-white'}
                  >
                    <td className="px-6 py-4 text-sm font-bold text-primary tracking-tight">
                      {displayId}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium">
                      {parcel.acreage ? `${parcel.acreage.toFixed(1)} ac` : '—'}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium">
                      {parcel.zoning_raw || '—'}
                    </td>
                    <td className="px-6 py-4">
                      {isVacant ? (
                        <span className="px-2 py-0.5 rounded bg-surface-container text-on-surface-variant text-[10px] font-bold uppercase">
                          Vacant
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-bold uppercase">
                          {status}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-on-surface-variant leading-relaxed max-w-xs truncate">
                      {parcel.owner_name_raw || '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
