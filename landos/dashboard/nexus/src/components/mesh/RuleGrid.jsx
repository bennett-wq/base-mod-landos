import { useSelector } from 'react-redux';

export default function RuleGrid() {
  const rules = useSelector(s => s.mesh.rules);

  return (
    <div className="grid grid-cols-2 gap-1 p-2">
      {rules.map(r => (
        <div key={r.id} className="p-2 rounded-md bg-void-2 border border-transparent hover:border-white/6 hover:bg-void-3 cursor-pointer transition-all relative overflow-hidden">
          <div className="text-[11px] font-semibold text-brass mb-0.5">{r.id}</div>
          <div className="text-[9px] text-white/17 truncate">{r.name}</div>
          {r.fires > 0 && (
            <div className="absolute top-1.5 right-2 text-[10px] font-semibold text-white/12">{r.fires}×</div>
          )}
          {r.cooldown && (
            <div className="absolute bottom-0 left-0 h-[2px] bg-nexus-amber" style={{ width: `${Math.random() * 100}%` }} />
          )}
        </div>
      ))}
    </div>
  );
}
