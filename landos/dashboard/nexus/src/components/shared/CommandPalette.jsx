import { useState, useEffect, useRef, useMemo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { closeCommandPalette, setActiveTab } from '../../store/uiSlice';
import { addToast } from '../../store/meshSlice';
import { toggleDrawMode, toggleUploadPortal, createMission, openSpotlight } from '../../store/missionsSlice';
import { COMMANDS } from '../../data/commands';
import { motion, AnimatePresence } from 'framer-motion';

export default function CommandPalette() {
  const dispatch = useDispatch();
  const open = useSelector(s => s.ui.commandPaletteOpen);
  const clusters = useSelector(s => s.mesh.clusters);
  const [filter, setFilter] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) { setFilter(''); setSelectedIdx(0); setTimeout(() => inputRef.current?.focus(), 50); }
  }, [open]);

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') dispatch(closeCommandPalette()); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [dispatch]);

  // Build flat list of all searchable items (commands + clusters)
  const allItems = useMemo(() => {
    const f = filter.toLowerCase();
    const items = [];

    // Commands
    COMMANDS.forEach(group => {
      group.items.forEach(item => {
        if (item.label.toLowerCase().includes(f)) {
          items.push({ ...item, group: group.group, type: 'command' });
        }
      });
    });

    // Cluster search (only when filtering)
    if (f.length >= 2) {
      clusters
        .filter(c => c.name.toLowerCase().includes(f) || c.city.toLowerCase().includes(f))
        .slice(0, 6)
        .forEach(c => {
          items.push({
            type: 'cluster',
            icon: c.type === 'owner' ? '👤' : c.type === 'subdivision' ? '🏘️' : '📍',
            label: `${c.name} — ${c.lots} lots, ${c.signal}`,
            group: 'Clusters',
            action: `cluster:${c.id}`,
            cluster: c,
          });
        });
    }

    return items;
  }, [filter, clusters]);

  const execute = (item) => {
    dispatch(closeCommandPalette());

    // Handle special dispatches
    if (item.dispatch === 'drawMode') {
      dispatch(setActiveTab('radar'));
      setTimeout(() => dispatch(toggleDrawMode()), 100);
      return;
    }
    if (item.dispatch === 'uploadPortal') {
      dispatch(toggleUploadPortal());
      return;
    }
    if (item.dispatch === 'deployAll') {
      dispatch(createMission({
        polygon: null,
        agents: ['supply_intelligence', 'cluster_detection', 'spark_signal', 'opportunity_creation'],
        name: 'Full county scan — all agents',
      }));
      dispatch(addToast({ icon: '🚀', message: 'Full county scan deployed — 4 agents' }));
      return;
    }
    if (item.dispatch === 'nav') {
      const tab = item.action.split(':')[1];
      dispatch(setActiveTab(tab));
      return;
    }
    if (item.type === 'cluster') {
      // Import openSpotlight dynamically to avoid circular deps
      dispatch(openSpotlight(item.cluster));
      return;
    }

    dispatch(addToast({ icon: '⚡', message: `${item.label} triggered` }));
  };

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIdx(i => Math.min(i + 1, allItems.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIdx(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && allItems[selectedIdx]) { e.preventDefault(); execute(allItems[selectedIdx]); }
  };

  // Group items for display
  const grouped = useMemo(() => {
    const groups = {};
    allItems.forEach(item => {
      if (!groups[item.group]) groups[item.group] = [];
      groups[item.group].push(item);
    });
    return Object.entries(groups);
  }, [allItems]);

  let flatIdx = -1;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 bg-void-0/80 backdrop-blur-xl z-[1000] flex items-start justify-center pt-[15vh]"
          onClick={(e) => { if (e.target === e.currentTarget) dispatch(closeCommandPalette()); }}
        >
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            className="w-[600px] bg-void-2 border border-white/6 rounded-xl shadow-[0_24px_80px_rgba(0,0,0,0.6)] overflow-hidden"
          >
            <div className="flex items-center px-5 border-b border-white/5">
              <span className="text-brass text-[16px] mr-2">⚡</span>
              <input
                ref={inputRef}
                value={filter}
                onChange={(e) => { setFilter(e.target.value); setSelectedIdx(0); }}
                onKeyDown={handleKeyDown}
                className="flex-1 bg-transparent border-none outline-none text-[#e0e0e0] font-mono text-[14px] py-4"
                placeholder="Search commands, clusters, parcels..."
              />
              <kbd className="text-[10px] text-white/10 px-1.5 py-0.5 rounded bg-white/4 border border-white/5 font-mono">ESC</kbd>
            </div>
            <div className="max-h-[380px] overflow-y-auto p-2">
              {grouped.map(([group, items]) => (
                <div key={group} className="px-3 py-1">
                  <div className="text-[10px] text-white/12 uppercase tracking-widest mb-2">{group}</div>
                  {items.map(item => {
                    flatIdx++;
                    const idx = flatIdx;
                    return (
                      <div
                        key={item.action}
                        onClick={() => execute(item)}
                        onMouseEnter={() => setSelectedIdx(idx)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors ${
                          selectedIdx === idx ? 'bg-void-4 ring-1 ring-brass/20' : 'hover:bg-void-4'
                        }`}
                      >
                        <span className="text-[14px] w-6 text-center">{item.icon}</span>
                        <span className="flex-1 text-[13px] text-white/65">{item.label}</span>
                        {item.type === 'cluster' && (
                          <span className="text-[9px] text-brass-dim px-1.5 py-0.5 rounded bg-brass/5">spotlight</span>
                        )}
                        {item.shortcut && (
                          <kbd className="text-[10px] text-white/12 px-1.5 py-0.5 rounded bg-white/5 border border-white/6 font-mono">
                            {item.shortcut}
                          </kbd>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
              {allItems.length === 0 && (
                <div className="text-center py-8 text-white/15 text-[12px]">No results found</div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
