import { useSelector } from 'react-redux';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const TYPE_COLORS = { owner: '#a855f7', subdivision: '#00f0ff', proximity: '#3b82f6', agent: '#00ff88', office: '#ffb800' };
const TYPE_ICONS = { owner: '👤', subdivision: '🏘️', proximity: '📍', agent: '🏷️', office: '🏢' };
const TYPE_STYLES = { owner: 'bg-nexus-purple/15 text-nexus-purple', subdivision: 'bg-nexus-cyan/15 text-nexus-cyan', proximity: 'bg-nexus-blue/15 text-nexus-blue', agent: 'bg-nexus-emerald/15 text-nexus-emerald', office: 'bg-nexus-amber/15 text-nexus-amber' };
const SIG_BADGE = { HIGHEST: 'bg-nexus-crimson/15 text-nexus-crimson', HIGH: 'bg-nexus-orange/15 text-nexus-orange', MEDIUM: 'bg-nexus-amber/15 text-nexus-amber', LOW: 'bg-white/8 text-white/40', NONE: 'bg-nexus-blue/15 text-nexus-blue' };

function ScoreRing({ score, size = 80 }) {
  const circ = 2 * Math.PI * 42;
  const offset = circ - (score / 100) * circ;
  const color = score >= 70 ? 'var(--color-nexus-emerald)' : score >= 50 ? 'var(--color-nexus-amber)' : 'var(--color-nexus-crimson)';
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg viewBox="0 0 100 100" className="w-full h-full" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="50" cy="50" r="42" fill="none" stroke="var(--color-void-4)" strokeWidth="8" />
        <circle cx="50" cy="50" r="42" fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset} style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center font-display text-[22px] font-extrabold text-brass-bright">{score}</div>
    </div>
  );
}

function DimBar({ label, value }) {
  const color = value >= 70 ? 'var(--color-nexus-emerald)' : value >= 50 ? 'var(--color-nexus-amber)' : 'var(--color-nexus-crimson)';
  return (
    <div className="flex items-center gap-2">
      <div className="text-[10px] text-white/25 w-20 text-right">{label}</div>
      <div className="flex-1 h-1.5 bg-void-4 rounded-sm overflow-hidden">
        <div className="h-full rounded-sm transition-all duration-500" style={{ width: `${value}%`, background: color }} />
      </div>
      <div className="text-[10px] font-semibold text-white/38 w-7">{Math.floor(value)}</div>
    </div>
  );
}

export default function ClustersTab() {
  const clusters = useSelector(s => s.mesh.clusters);
  const top = clusters.slice(0, 8);

  return (
    <div className="grid grid-cols-2 h-full gap-px bg-white/4">
      {/* Map */}
      <div className="relative bg-void-0">
        <MapContainer center={[42.28, -83.75]} zoom={10} className="w-full h-full" zoomControl={true} attributionControl={false}>
          <TileLayer url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" maxZoom={18} />
          <TileLayer url="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}" maxZoom={18} />
          {clusters.map(c => (
            <CircleMarker key={c.id} center={[c.lat, c.lng]} radius={Math.max(5, Math.min(18, c.lots / 4))} pathOptions={{ fillColor: TYPE_COLORS[c.type], fillOpacity: 0.6, color: 'rgba(255,255,255,0.08)', weight: 1 }}>
              <Popup><b style={{ color: TYPE_COLORS[c.type] }}>{c.name}</b><br />{c.type.toUpperCase()} · {c.lots} lots<br />{c.acres.toLocaleString()} ac · Score: {c.score}</Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      {/* Detail Panel */}
      <div className="bg-void-1 flex flex-col overflow-hidden">
        <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2 shrink-0">
          <span className="font-display font-semibold text-[11px] text-white/30 uppercase tracking-[1.5px]">Cluster Intelligence</span>
          <span className="ml-auto text-[10px] text-white/12 px-2 py-0.5 bg-white/4 rounded-full">2,229 detected</span>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {top.map(c => (
            <div key={c.id} className="bg-void-2 rounded-xl p-4 border border-white/5">
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center text-xl bg-void-3 border border-white/5">{TYPE_ICONS[c.type]}</div>
                <div>
                  <div className="font-display text-[18px] font-bold text-[#e0e0e0]">{c.name}</div>
                  <div className="text-[10px] text-white/20">{c.type.toUpperCase()} · {c.city}</div>
                </div>
                <span className={`ml-auto text-[9px] font-semibold px-1.5 py-0.5 rounded ${SIG_BADGE[c.signal]}`}>{c.signal}</span>
              </div>

              <div className="flex items-center gap-4 mb-3">
                <ScoreRing score={c.score} />
                <div className="flex-1 space-y-1.5">
                  <DimBar label="Zoning" value={40 + Math.random() * 50} />
                  <DimBar label="Economics" value={30 + Math.random() * 60} />
                  <DimBar label="Infra" value={20 + Math.random() * 70} />
                  <DimBar label="Signal" value={c.signal === 'HIGHEST' ? 90 : c.signal === 'HIGH' ? 70 : c.signal === 'MEDIUM' ? 50 : 30} />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                {[[c.lots, 'Lots'], [c.acres.toLocaleString(), 'Acres'], [`$${(c.landVal / 1000).toFixed(0)}K`, 'Land Value']].map(([v, l]) => (
                  <div key={l} className="bg-void-3 rounded-md p-2.5">
                    <div className="font-display text-[18px] font-bold text-brass-bright">{v}</div>
                    <div className="text-[9px] text-white/15 uppercase tracking-widest">{l}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
