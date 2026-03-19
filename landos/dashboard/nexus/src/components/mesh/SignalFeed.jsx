import { useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';

const TIER_COLORS = { t1: '#ff2d55', t2: '#ffb800', t3: '#00f0ff', t4: '#a855f7', t5: '#3b82f6' };
const TIER_BORDERS = { t1: 'border-l-nexus-crimson', t2: 'border-l-nexus-amber', t3: 'border-l-nexus-cyan', t4: 'border-l-nexus-purple', t5: 'border-l-nexus-blue' };

export default function SignalFeed() {
  const signals = useSelector(s => s.mesh.signals);

  return (
    <AnimatePresence initial={false}>
      {signals.slice(0, 30).map(sig => (
        <motion.div
          key={sig.id}
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
          className={`p-2 px-3 rounded-lg mb-1 border-l-[3px] ${TIER_BORDERS[sig.tier] || 'border-l-transparent'} hover:bg-void-3 transition-colors`}
        >
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-[12px]">{sig.icon}</span>
            <span className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: TIER_COLORS[sig.tier] }}>
              {sig.type.replace(/_/g, ' ')}
            </span>
            <span className="text-[9px] text-white/10 ml-auto tabular-nums">{sig.time}</span>
          </div>
          <div className="text-[11px] text-white/28 leading-snug">{sig.body}</div>
          <div className="flex gap-1.5 mt-1">
            {sig.tags.map(t => (
              <span key={t} className="text-[9px] px-1.5 py-0.5 rounded bg-white/4 text-white/17">{t}</span>
            ))}
          </div>
        </motion.div>
      ))}
    </AnimatePresence>
  );
}
