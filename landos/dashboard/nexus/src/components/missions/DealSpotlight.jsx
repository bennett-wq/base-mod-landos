import { useMemo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { closeSpotlight, createMission } from '../../store/missionsSlice';
import { setActiveTab } from '../../store/uiSlice';
import { addToast } from '../../store/meshSlice';

const TYPE_COLORS = { owner: '#a855f7', subdivision: '#00f0ff', proximity: '#3b82f6', agent: '#00ff88', office: '#ffb800' };
const SIG_META = {
  HIGHEST: { color: '#ff2d55', label: 'HIGHEST SIGNAL', bg: 'bg-nexus-crimson/15 text-nexus-crimson' },
  HIGH:    { color: '#f97316', label: 'HIGH SIGNAL', bg: 'bg-nexus-orange/15 text-nexus-orange' },
  MEDIUM:  { color: '#ffb800', label: 'MEDIUM SIGNAL', bg: 'bg-nexus-amber/15 text-nexus-amber' },
  LOW:     { color: '#6b7280', label: 'LOW SIGNAL', bg: 'bg-white/8 text-white/40' },
  NONE:    { color: '#3b82f6', label: 'NO SIGNAL', bg: 'bg-nexus-blue/15 text-nexus-blue' },
};
const TIER_META = {
  A: { color: '#00ff88', bg: 'bg-nexus-emerald/15 text-nexus-emerald border-nexus-emerald/20' },
  B: { color: '#00f0ff', bg: 'bg-nexus-cyan/15 text-nexus-cyan border-nexus-cyan/20' },
  C: { color: '#ffb800', bg: 'bg-nexus-amber/15 text-nexus-amber border-nexus-amber/20' },
  X: { color: '#ff2d55', bg: 'bg-nexus-crimson/15 text-nexus-crimson border-nexus-crimson/20' },
};

function ScoreRing({ score, size = 100 }) {
  const circ = 2 * Math.PI * 42;
  const offset = circ - (score / 100) * circ;
  const color = score >= 70 ? '#00ff88' : score >= 50 ? '#ffb800' : '#ff2d55';
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg viewBox="0 0 100 100" className="w-full h-full" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="6" />
        <motion.circle
          cx="50" cy="50" r="42" fill="none" stroke={color} strokeWidth="6" strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.4, 0, 0.2, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, type: 'spring' }}
          className="font-display text-[28px] font-extrabold"
          style={{ color }}
        >
          {score}
        </motion.div>
        <div className="text-[8px] text-white/15 uppercase tracking-widest">Score</div>
      </div>
    </div>
  );
}

function DimBar({ label, value, delay = 0 }) {
  const color = value >= 70 ? '#00ff88' : value >= 50 ? '#ffb800' : '#ff2d55';
  return (
    <div className="flex items-center gap-2.5">
      <div className="text-[10px] text-white/25 w-[80px] text-right">{label}</div>
      <div className="flex-1 h-2 bg-void-4 rounded-sm overflow-hidden">
        <motion.div
          className="h-full rounded-sm"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8, delay, ease: [0.4, 0, 0.2, 1] }}
        />
      </div>
      <div className="text-[11px] font-semibold w-8 font-mono" style={{ color }}>{Math.floor(value)}</div>
    </div>
  );
}

function HomeCard({ model, price, sqft, beds, baths, fit }) {
  return (
    <div className="bg-void-3 rounded-xl p-4 border border-white/5 hover:border-brass-dim transition-colors cursor-pointer">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-lg bg-void-4 border border-white/6 flex items-center justify-center text-xl">🏠</div>
        <div>
          <div className="font-display text-[13px] font-bold text-[#e0e0e0]">{model}</div>
          <div className="text-[10px] text-white/20">{sqft} sqft · {beds}BR/{baths}BA</div>
        </div>
        <div className="ml-auto text-right">
          <div className="font-display text-[16px] font-bold text-brass-bright">${price.toLocaleString()}</div>
          <div className="text-[9px] text-white/15">installed</div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className="text-[9px] text-white/15">Geometry fit:</div>
        <div className="flex-1 h-1.5 bg-void-4 rounded overflow-hidden">
          <div className="h-full rounded bg-nexus-emerald" style={{ width: `${fit}%` }} />
        </div>
        <div className="text-[10px] font-semibold text-nexus-emerald">{fit}%</div>
      </div>
    </div>
  );
}

export default function DealSpotlight() {
  const dispatch = useDispatch();
  const { spotlightOpen, spotlightCluster } = useSelector(s => s.missions);
  const c = spotlightCluster;

  // Deterministic dimension scores derived from cluster properties (must be before early return)
  const dims = useMemo(() => {
    if (!c) return { zoning: 0, economics: 0, infrastructure: 0, signal: 0, entitlement: 0, demand: 0 };
    const seed = (c.id || '').split('').reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
    const s = (offset) => ((seed * 13 + offset * 37) % 100);
    return {
      zoning: 40 + (s(1) % 50),
      economics: c.margin >= 15 ? 70 + (s(2) % 25) : 30 + (s(2) % 40),
      infrastructure: 20 + (s(3) % 70),
      signal: c.signal === 'HIGHEST' ? 90 : c.signal === 'HIGH' ? 70 : c.signal === 'MEDIUM' ? 50 : 30,
      entitlement: 35 + (s(4) % 55),
      demand: 45 + (s(5) % 45),
    };
  }, [c]);

  // Stable CDOM value derived from cluster
  const cdomDays = useMemo(() => {
    if (!c) return 0;
    const seed = (c.id || '').split('').reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
    return 90 + (seed % 60);
  }, [c]);

  if (!c) return null;

  const sig = SIG_META[c.signal] || SIG_META.NONE;
  const tier = TIER_META[c.tier] || TIER_META.C;

  // Simulated economics
  const landCost = c.landVal || 35000;
  const buildCost = 89000;
  const siteCost = 18000;
  const totalCost = landCost + buildCost + siteCost + 12000 + 7050 + 16470;
  const retailPrice = c.margin >= 15 ? Math.floor(totalCost / (1 - c.margin / 100)) : 279000;
  const profit = retailPrice - totalCost;
  const portfolioProfit = profit * c.lots;

  return (
    <AnimatePresence>
      {spotlightOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[600] flex items-center justify-center"
        >
          <div className="absolute inset-0 bg-void-0/90 backdrop-blur-xl" onClick={() => dispatch(closeSpotlight())} />

          <motion.div
            initial={{ scale: 0.9, y: 30, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.9, y: 30, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 200, damping: 25 }}
            className="relative w-[960px] max-h-[88vh] bg-void-1 border border-white/8 rounded-2xl overflow-hidden"
            style={{ boxShadow: `0 0 60px ${sig.color}10, 0 24px 80px rgba(0,0,0,0.6)` }}
          >
            {/* Holographic top accent */}
            <div className="h-1 w-full" style={{ background: `linear-gradient(90deg, transparent, ${sig.color}, ${tier.color}, transparent)` }} />

            {/* Header */}
            <div className="px-8 py-6 border-b border-white/5">
              <div className="flex items-start gap-4">
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl border-2 shrink-0"
                  style={{ borderColor: TYPE_COLORS[c.type] + '40', background: TYPE_COLORS[c.type] + '10' }}
                >
                  {c.type === 'owner' ? '👤' : c.type === 'subdivision' ? '🏘️' : c.type === 'proximity' ? '📍' : c.type === 'agent' ? '🏷️' : '🏢'}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h2 className="font-display text-[24px] font-extrabold text-[#e0e0e0]">{c.name}</h2>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${sig.bg}`}>{sig.label}</span>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${tier.bg}`}>TIER {c.tier}</span>
                  </div>
                  <div className="text-[12px] text-white/22">
                    {c.type.toUpperCase()} cluster · {c.city} · {c.lots} lots · {c.acres.toLocaleString()} acres
                  </div>
                </div>
                <button
                  onClick={() => dispatch(closeSpotlight())}
                  className="w-9 h-9 rounded-lg bg-void-3 border border-white/6 text-white/30 text-lg flex items-center justify-center hover:bg-void-4 hover:text-white/50 transition-all cursor-pointer"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 divide-x divide-white/5 overflow-y-auto max-h-[calc(88vh-130px)]">
              {/* Column 1: Score + Dimensions */}
              <div className="p-6 space-y-5">
                <div className="flex items-center gap-5">
                  <ScoreRing score={c.score} />
                  <div className="flex-1 space-y-2">
                    <DimBar label="Zoning" value={dims.zoning} delay={0.1} />
                    <DimBar label="Economics" value={dims.economics} delay={0.2} />
                    <DimBar label="Infra" value={dims.infrastructure} delay={0.3} />
                    <DimBar label="Signal" value={dims.signal} delay={0.4} />
                    <DimBar label="Entitlement" value={dims.entitlement} delay={0.5} />
                    <DimBar label="Demand" value={dims.demand} delay={0.6} />
                  </div>
                </div>

                {/* Key Stats */}
                <div className="grid grid-cols-2 gap-2">
                  {[
                    [c.lots, 'Lots'],
                    [`${c.acres.toLocaleString()} ac`, 'Acreage'],
                    [`$${(landCost / 1000).toFixed(0)}K`, 'Avg Land Cost'],
                    [c.conc, 'Concentration'],
                  ].map(([v, l], i) => (
                    <motion.div
                      key={l}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 * i }}
                      className="bg-void-2 rounded-lg p-3"
                    >
                      <div className="font-display text-[16px] font-bold text-brass-bright">{v}</div>
                      <div className="text-[9px] text-white/15 uppercase tracking-widest">{l}</div>
                    </motion.div>
                  ))}
                </div>

                {/* Active Signals */}
                <div>
                  <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-2">Active Signals</div>
                  <div className="space-y-1">
                    {[
                      c.signal === 'HIGHEST' && { icon: '🚪', text: 'Developer exit pattern detected', color: 'text-nexus-crimson' },
                      c.signal !== 'NONE' && { icon: '🔥', text: `CDOM fatigue — avg ${cdomDays} days`, color: 'text-nexus-amber' },
                      c.lots > 20 && { icon: '📦', text: 'Package language in BBO remarks', color: 'text-nexus-cyan' },
                      { icon: '👤', text: `Owner cluster — ${c.lots} linked parcels`, color: 'text-nexus-purple' },
                      c.tier === 'A' && { icon: '💎', text: 'Multi-signal convergence (Tier 1)', color: 'text-nexus-emerald' },
                    ].filter(Boolean).map((s, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 + 0.1 * i }}
                        className="flex items-center gap-2 py-1.5 px-2.5 rounded bg-void-2 text-[11px]"
                      >
                        <span>{s.icon}</span>
                        <span className={s.color}>{s.text}</span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Column 2: Economics */}
              <div className="p-6 space-y-5">
                <div>
                  <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-3">Deal Economics</div>
                  <div className="space-y-1">
                    {[
                      ['Land Cost', `$${landCost.toLocaleString()}`, '#c9a44e'],
                      ['Build (Factory)', `$${buildCost.toLocaleString()}`, '#00f0ff'],
                      ['Site Work', `$${siteCost.toLocaleString()}`, '#3b82f6'],
                      ['Soft Costs', '$12,000', '#ffb800'],
                      ['Contingency', '$7,050', '#f97316'],
                      ['Closing', '$16,470', '#ff2d55'],
                    ].map(([label, val, color]) => (
                      <div key={label} className="flex items-center gap-2 py-1">
                        <div className="w-2 h-2 rounded-sm" style={{ background: color }} />
                        <div className="text-[11px] text-white/30 flex-1">{label}</div>
                        <div className="text-[11px] font-semibold text-white/45 font-mono">{val}</div>
                      </div>
                    ))}
                    <div className="border-t border-white/6 pt-2 mt-2 flex items-center">
                      <div className="text-[11px] font-semibold text-brass flex-1">Total Project Cost</div>
                      <div className="font-display text-[16px] font-bold text-brass-bright">${totalCost.toLocaleString()}</div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-void-2 rounded-lg p-3.5">
                    <div className="font-display text-[22px] font-extrabold text-nexus-emerald">${profit.toLocaleString()}</div>
                    <div className="text-[9px] text-white/15 uppercase tracking-widest">Profit / Unit</div>
                  </div>
                  <div className="bg-void-2 rounded-lg p-3.5">
                    <div className="font-display text-[22px] font-extrabold text-nexus-emerald">{c.margin}%</div>
                    <div className="text-[9px] text-white/15 uppercase tracking-widest">Margin</div>
                  </div>
                  <div className="bg-void-2 rounded-lg p-3.5 col-span-2">
                    <div className="font-display text-[22px] font-extrabold text-brass-bright">${portfolioProfit.toLocaleString()}</div>
                    <div className="text-[9px] text-white/15 uppercase tracking-widest">Total Portfolio Profit ({c.lots} lots)</div>
                  </div>
                </div>

                {/* Retail pricing */}
                <div>
                  <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-2">Target Retail</div>
                  <div className="bg-void-2 rounded-xl p-4 text-center border border-white/5">
                    <div className="font-display text-[32px] font-extrabold text-brass-bright">${retailPrice.toLocaleString()}</div>
                    <div className="text-[10px] text-white/15 uppercase tracking-widest">All-In Installed Price</div>
                  </div>
                </div>
              </div>

              {/* Column 3: Home Fit + Actions */}
              <div className="p-6 space-y-5">
                <div>
                  <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-3">Home Product Fit</div>
                  <div className="space-y-2">
                    <HomeCard model="BaseMod 1200" price={199000} sqft={1200} beds={3} baths={2} fit={92} />
                    <HomeCard model="BaseMod 1500" price={239000} sqft={1500} beds={3} baths={2} fit={85} />
                    <HomeCard model="BaseMod 1800" price={279000} sqft={1800} beds={4} baths={2.5} fit={72} />
                  </div>
                </div>

                {/* Actions */}
                <div>
                  <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-3">Actions</div>
                  <div className="space-y-2">
                    <button
                      onClick={() => {
                        dispatch(createMission({
                          polygon: null,
                          agents: ['supply_intelligence', 'cluster_detection', 'spark_signal', 'opportunity_creation'],
                          name: `Deep scan — ${c.name}`,
                        }));
                        dispatch(closeSpotlight());
                        dispatch(addToast({ icon: '🚀', message: `Deep scan deployed for ${c.name}` }));
                      }}
                      className="w-full py-3 bg-brass text-void-0 rounded-xl font-display font-bold text-[13px] cursor-pointer hover:bg-brass-bright hover:shadow-[0_0_20px_var(--color-brass-glow)] transition-all border-none flex items-center justify-center gap-2"
                    >
                      <span>🚀</span> Deploy Deep Scan
                    </button>
                    <button
                      onClick={() => dispatch(addToast({ icon: '📋', message: `Broker note generated for ${c.name}` }))}
                      className="w-full py-3 bg-void-3 text-white/40 rounded-xl font-display font-bold text-[13px] border border-white/8 cursor-pointer hover:border-brass-dim hover:text-brass transition-all flex items-center justify-center gap-2"
                    >
                      <span>📋</span> Generate Broker Note
                    </button>
                    <button
                      onClick={() => dispatch(addToast({ icon: '📊', message: `Deal package exported for ${c.name}` }))}
                      className="w-full py-3 bg-void-3 text-white/40 rounded-xl font-display font-bold text-[13px] border border-white/8 cursor-pointer hover:border-brass-dim hover:text-brass transition-all flex items-center justify-center gap-2"
                    >
                      <span>📊</span> Export Deal Package
                    </button>
                    <button
                      onClick={() => {
                        dispatch(closeSpotlight());
                        dispatch(setActiveTab('radar'));
                      }}
                      className="w-full py-3 bg-void-3 text-white/40 rounded-xl font-display font-bold text-[13px] border border-white/8 cursor-pointer hover:border-brass-dim hover:text-brass transition-all flex items-center justify-center gap-2"
                    >
                      <span>🗺️</span> View on Map
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
