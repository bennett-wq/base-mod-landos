import { useState, useEffect, useMemo, useRef } from 'react';
import { useSelector } from 'react-redux';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const SIG_COLORS = { HIGHEST: '#ff2d55', HIGH: '#f97316', MEDIUM: '#ffb800', LOW: '#6b7280', NONE: '#3b82f6' };
const SIG_BADGE = { HIGHEST: 'bg-nexus-crimson/15 text-nexus-crimson', HIGH: 'bg-nexus-orange/15 text-nexus-orange', MEDIUM: 'bg-nexus-amber/15 text-nexus-amber', LOW: 'bg-white/8 text-white/40', NONE: 'bg-nexus-blue/15 text-nexus-blue' };
const TIER_BADGE = { A: 'bg-nexus-emerald/15 text-nexus-emerald', B: 'bg-nexus-cyan/15 text-nexus-cyan', C: 'bg-nexus-amber/15 text-nexus-amber', X: 'bg-nexus-crimson/15 text-nexus-crimson' };

function FlyTo({ lat, lng }) {
  const map = useMap();
  useEffect(() => { if (lat && lng) map.flyTo([lat, lng], 14); }, [lat, lng, map]);
  return null;
}

export default function RadarTab() {
  const clusters = useSelector(s => s.mesh.clusters);
  const [sigFilter, setSigFilter] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [concFilter, setConcFilter] = useState('');
  const [ownerFilter, setOwnerFilter] = useState('');
  const [sortKey, setSortKey] = useState('lots');
  const [sortDir, setSortDir] = useState('desc');
  const [flyTarget, setFlyTarget] = useState({ lat: null, lng: null });

  const filtered = useMemo(() => {
    let data = clusters.filter(c => {
      if (sigFilter && c.signal !== sigFilter) return false;
      if (tierFilter && c.tier !== tierFilter) return false;
      if (concFilter && c.conc !== concFilter) return false;
      if (ownerFilter && !c.name.toLowerCase().includes(ownerFilter.toLowerCase())) return false;
      return true;
    });
    data.sort((a, b) => {
      const va = a[sortKey], vb = b[sortKey];
      if (typeof va === 'string') return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
      return sortDir === 'asc' ? va - vb : vb - va;
    });
    return data;
  }, [clusters, sigFilter, tierFilter, concFilter, ownerFilter, sortKey, sortDir]);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const highSignal = filtered.filter(c => c.signal === 'HIGHEST' || c.signal === 'HIGH').length;
  const tierA = filtered.filter(c => c.tier === 'A').length;
  const totalLots = filtered.reduce((s, c) => s + c.lots, 0);

  return (
    <div className="grid grid-cols-[1fr_400px] h-full gap-px bg-white/4">
      {/* Map */}
      <div className="relative bg-void-0">
        <MapContainer center={[42.28, -83.75]} zoom={10} className="w-full h-full" zoomControl={true} attributionControl={false}>
          <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" maxZoom={18} />
          <FlyTo lat={flyTarget.lat} lng={flyTarget.lng} />
          {filtered.map(c => (
            <CircleMarker key={c.id} center={[c.lat, c.lng]} radius={Math.max(6, Math.min(20, c.lots / 3))} pathOptions={{ fillColor: SIG_COLORS[c.signal], fillOpacity: 0.7, color: c.conc === 'TIGHT' ? '#c9a44e' : 'rgba(255,255,255,0.12)', weight: c.conc === 'TIGHT' ? 2 : 1 }}>
              <Popup><b style={{ color: '#c9a44e' }}>{c.name}</b><br />{c.lots} lots · {c.acres.toLocaleString()} ac<br />Signal: {c.signal} · Tier {c.tier}<br />Margin: {c.margin}% · {c.city}</Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      {/* Sidebar */}
      <div className="bg-void-1 flex flex-col overflow-hidden">
        {/* Stats */}
        <div className="flex gap-px bg-white/4 border-b border-white/5 shrink-0">
          {[[filtered.length, 'Clusters'], [totalLots.toLocaleString(), 'Total Lots'], [highSignal, 'High Signal'], [tierA, 'Tier A']].map(([v, l]) => (
            <div key={l} className="flex-1 bg-void-1 px-3.5 py-2.5 text-center">
              <div className="font-display text-[20px] font-bold text-brass-bright">{v}</div>
              <div className="text-[9px] text-white/15 uppercase tracking-widest">{l}</div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="px-3 py-2.5 border-b border-white/5 flex flex-wrap gap-2 shrink-0">
          {[['Signal', sigFilter, setSigFilter, ['HIGHEST','HIGH','MEDIUM','LOW']], ['Tier', tierFilter, setTierFilter, ['A','B','C','X']], ['Conc.', concFilter, setConcFilter, ['TIGHT','MODERATE','SPREAD']]].map(([label, val, set, opts]) => (
            <div key={label} className="flex flex-col gap-1">
              <div className="text-[9px] text-white/15 uppercase tracking-widest">{label}</div>
              <select value={val} onChange={e => set(e.target.value)} className="bg-void-3 border border-white/6 rounded px-2.5 py-1 text-[#e0e0e0] font-mono text-[11px] outline-none focus:border-brass-dim">
                <option value="">All</option>
                {opts.map(o => <option key={o}>{o}</option>)}
              </select>
            </div>
          ))}
          <div className="flex flex-col gap-1">
            <div className="text-[9px] text-white/15 uppercase tracking-widest">Owner</div>
            <input value={ownerFilter} onChange={e => setOwnerFilter(e.target.value)} placeholder="Search..." className="bg-void-3 border border-white/6 rounded px-2.5 py-1 text-[#e0e0e0] font-mono text-[11px] outline-none w-[110px] focus:border-brass-dim" />
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-y-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                {[['name', 'Owner'], ['lots', 'Lots'], ['signal', 'Signal'], ['tier', 'Tier'], ['margin', 'Margin']].map(([k, l]) => (
                  <th key={k} onClick={() => toggleSort(k)} className={`sticky top-0 bg-void-2 px-2.5 py-2 text-[10px] font-semibold uppercase tracking-wide text-left cursor-pointer border-b border-white/5 z-10 ${sortKey === k ? 'text-brass' : 'text-white/22 hover:text-white/38'}`}>
                    {l} {sortKey === k && (sortDir === 'asc' ? '▲' : '▼')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} onClick={() => setFlyTarget({ lat: c.lat, lng: c.lng })} className={`cursor-pointer border-l-[3px] ${c.signal === 'HIGHEST' ? 'border-l-nexus-crimson' : c.signal === 'HIGH' ? 'border-l-nexus-orange' : c.signal === 'MEDIUM' ? 'border-l-nexus-amber' : 'border-l-transparent'} hover:[&>td]:bg-void-3`}>
                  <td className="px-2.5 py-1.5 text-[11px] text-white/55 border-b border-white/4 transition-colors">
                    <span className="font-medium text-white/65">{c.name}</span>
                    <br /><span className="text-[10px] text-white/15">{c.city} · {c.type}</span>
                  </td>
                  <td className="px-2.5 py-1.5 text-[11px] text-white/40 border-b border-white/4 transition-colors">{c.lots}</td>
                  <td className="px-2.5 py-1.5 border-b border-white/4 transition-colors">
                    <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded ${SIG_BADGE[c.signal]}`}>{c.signal}</span>
                  </td>
                  <td className="px-2.5 py-1.5 border-b border-white/4 transition-colors">
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${TIER_BADGE[c.tier]}`}>{c.tier}</span>
                  </td>
                  <td className={`px-2.5 py-1.5 text-[11px] border-b border-white/4 transition-colors ${c.margin >= 15 ? 'text-nexus-emerald' : c.margin > 0 ? 'text-nexus-amber' : 'text-nexus-crimson'}`}>{c.margin}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
