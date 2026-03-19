import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { useClusters } from '@/hooks/useClusters'
import type { Signal } from '@/data/mockData'

const SIGNAL_STYLE: Record<Signal, { radius: number; fillColor: string; fillOpacity: number }> = {
  HIGHEST: { radius: 12, fillColor: '#7f5313', fillOpacity: 0.8 },
  HIGH:    { radius: 10, fillColor: '#7f5313', fillOpacity: 0.5 },
  MEDIUM:  { radius: 8,  fillColor: '#9CA3AF', fillOpacity: 0.5 },
  LOW:     { radius: 6,  fillColor: '#D1D5DB', fillOpacity: 0.4 },
}

export function MapCanvas() {
  const { data: clusters } = useClusters()

  return (
    <MapContainer
      center={[42.2808, -83.7430]}
      zoom={11}
      className="h-full w-full"
      zoomControl={false}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {clusters?.map((c) => {
        const style = SIGNAL_STYLE[c.signal]
        return (
          <CircleMarker
            key={c.owner}
            center={c.position}
            radius={style.radius}
            pathOptions={{
              fillColor: style.fillColor,
              fillOpacity: style.fillOpacity,
              weight: 2,
              color: '#ffffff',
            }}
          >
            <Popup>
              <div className="min-w-[220px] p-1 font-sans">
                <div className="mb-2 flex items-start justify-between">
                  <div>
                    <p className="text-sm font-bold text-[#1b1c1a] leading-tight">{c.owner}</p>
                    <p className="mt-0.5 text-[10px] font-bold uppercase tracking-wider text-[#827567]">
                      OWNER &bull; {c.township}
                    </p>
                  </div>
                  <span className="rounded bg-[#7f5313]/10 px-2 py-0.5 text-[10px] font-bold text-[#7f5313]">
                    {c.signal}
                  </span>
                </div>
                <div className="mb-3 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-tighter text-[#827567]">Lots</p>
                    <p className="text-sm font-semibold text-[#1b1c1a]">{c.lots}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-tighter text-[#827567]">Score</p>
                    <p className="text-sm font-semibold text-[#1b1c1a]">{c.score}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="flex-1 rounded-lg border border-[#7f5313]/20 py-2 text-[11px] font-bold text-[#7f5313] transition-colors hover:bg-[#7f5313]/5">
                    View Intel &rarr;
                  </button>
                  <button className="flex-1 rounded-lg bg-[#1b1c1a] py-2 text-[11px] font-bold text-white transition-colors hover:bg-[#30312f]">
                    Mission
                  </button>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}
