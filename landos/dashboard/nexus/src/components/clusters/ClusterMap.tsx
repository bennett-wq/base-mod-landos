import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

type Signal = 'HIGHEST' | 'HIGH' | 'MEDIUM' | 'LOW'

interface ClusterMarker {
  owner: string
  township: string
  position: [number, number]
  signal: Signal
  lots: number
  score: number
}

const SIGNAL_STYLE: Record<Signal, { radius: number; fillColor: string; fillOpacity: number }> = {
  HIGHEST: { radius: 12, fillColor: '#7f5313', fillOpacity: 0.8 },
  HIGH:    { radius: 10, fillColor: '#7f5313', fillOpacity: 0.5 },
  MEDIUM:  { radius: 8,  fillColor: '#9CA3AF', fillOpacity: 0.5 },
  LOW:     { radius: 6,  fillColor: '#D1D5DB', fillOpacity: 0.4 },
}

const CLUSTERS: ClusterMarker[] = [
  { owner: 'Horseshoe Lake Corp',   township: 'Saline Twp',    position: [42.165, -83.83],  signal: 'HIGHEST', lots: 88,  score: 91 },
  { owner: 'Julian Francis Trust',   township: 'Lima Twp',      position: [42.238, -83.612], signal: 'HIGHEST', lots: 12,  score: 84 },
  { owner: 'Toll Brothers Holdings', township: 'Augusta Twp',   position: [42.338, -83.862], signal: 'HIGH',    lots: 146, score: 67 },
  { owner: 'M/I Homes LLC',          township: 'Ann Arbor Twp', position: [42.248, -83.729], signal: 'MEDIUM',  lots: 99,  score: 52 },
  { owner: 'PulteGroup',             township: 'Ypsilanti Twp', position: [42.189, -83.777], signal: 'LOW',     lots: 82,  score: 34 },
]

interface ClusterMapProps {
  selectedOwner?: string
}

export function ClusterMap({ selectedOwner }: ClusterMapProps) {
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
      {CLUSTERS.map((c) => {
        const style = SIGNAL_STYLE[c.signal]
        const isSelected = selectedOwner === c.owner
        return (
          <CircleMarker
            key={c.owner}
            center={c.position}
            radius={isSelected ? style.radius + 3 : style.radius}
            pathOptions={{
              fillColor: style.fillColor,
              fillOpacity: isSelected ? 1 : style.fillOpacity,
              weight: isSelected ? 4 : 2,
              color: isSelected ? '#7f5313' : '#ffffff',
            }}
          >
            <Popup>
              <div className="min-w-[180px] p-1 font-sans">
                <p className="text-sm font-bold text-[#1b1c1a] leading-tight">{c.owner}</p>
                <p className="mt-0.5 text-[10px] font-bold uppercase tracking-wider text-[#827567]">
                  {c.township}
                </p>
                <div className="mt-2 grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-[10px] font-bold uppercase text-[#827567]">Lots</p>
                    <p className="text-sm font-semibold text-[#1b1c1a]">{c.lots}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold uppercase text-[#827567]">Score</p>
                    <p className="text-sm font-semibold text-[#1b1c1a]">{c.score}</p>
                  </div>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}

      {/* Legend */}
      <div className="leaflet-bottom leaflet-left">
        <div className="leaflet-control mb-4 ml-4 flex items-center space-x-4 rounded-lg border border-stone-200 bg-white px-4 py-2 shadow-sm">
          <div className="flex items-center space-x-2">
            <div className="h-3 w-3 rounded-full bg-primary" />
            <span className="text-[10px] font-bold uppercase tracking-tight text-on-surface-variant">Active Clusters</span>
          </div>
          <div className="h-4 w-px bg-stone-200" />
          <span className="text-[10px] font-bold uppercase tracking-tight text-stone-400">Layer: Heatmap (Zoning)</span>
        </div>
      </div>
    </MapContainer>
  )
}
