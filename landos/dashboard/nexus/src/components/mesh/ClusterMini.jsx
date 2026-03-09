import { useSelector } from 'react-redux';

const TYPE_STYLES = {
  owner: 'bg-nexus-purple/15 text-nexus-purple',
  subdivision: 'bg-nexus-cyan/15 text-nexus-cyan',
  proximity: 'bg-nexus-blue/15 text-nexus-blue',
  agent: 'bg-nexus-emerald/15 text-nexus-emerald',
  office: 'bg-nexus-amber/15 text-nexus-amber',
};

const TIER_COLORS = { A: 'text-nexus-emerald', B: 'text-nexus-cyan', C: 'text-nexus-amber', X: 'text-nexus-crimson' };

export default function ClusterMini() {
  const clusters = useSelector(s => s.mesh.clusters);

  return (
    <>
      {clusters.slice(0, 12).map(c => (
        <div key={c.id} className="p-2 px-3 rounded-lg mb-1 bg-void-2 border border-transparent hover:border-white/6 hover:bg-void-3 cursor-pointer transition-all">
          <div className="flex items-center gap-1.5">
            <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded uppercase tracking-wide ${TYPE_STYLES[c.type]}`}>{c.type}</span>
            <span className="text-[12px] font-medium text-white/65 truncate">{c.name}</span>
            <span className="ml-auto text-[14px] font-bold text-brass-bright">{c.lots}</span>
          </div>
          <div className="flex gap-3 mt-1 text-[10px] text-white/17">
            <span>{c.acres.toLocaleString()} ac</span>
            <span>{c.hasListing ? '✓ Listed' : '○ No listing'}</span>
            <span className={TIER_COLORS[c.tier]}>Tier {c.tier}</span>
          </div>
        </div>
      ))}
    </>
  );
}
