import { useState, useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { closeCommandPalette } from '../../store/uiSlice';
import { addToast } from '../../store/meshSlice';
import { COMMANDS } from '../../data/commands';
import { motion, AnimatePresence } from 'framer-motion';

export default function CommandPalette() {
  const dispatch = useDispatch();
  const open = useSelector(s => s.ui.commandPaletteOpen);
  const [filter, setFilter] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) { setFilter(''); setTimeout(() => inputRef.current?.focus(), 50); }
  }, [open]);

  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') dispatch(closeCommandPalette()); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [dispatch]);

  const execute = (item) => {
    dispatch(closeCommandPalette());
    dispatch(addToast({ icon: '⚡', message: `${item.label} triggered` }));
  };

  const f = filter.toLowerCase();

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
            className="w-[560px] bg-void-2 border border-white/6 rounded-xl shadow-[0_24px_80px_rgba(0,0,0,0.6)] overflow-hidden"
          >
            <div className="flex items-center px-5 border-b border-white/5">
              <span className="text-brass text-[16px] mr-2">⚡</span>
              <input
                ref={inputRef}
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="flex-1 bg-transparent border-none outline-none text-[#e0e0e0] font-mono text-[14px] py-4"
                placeholder="Type a command..."
              />
            </div>
            <div className="max-h-[300px] overflow-y-auto p-2">
              {COMMANDS.map(group => {
                const items = group.items.filter(i => i.label.toLowerCase().includes(f));
                if (!items.length) return null;
                return (
                  <div key={group.group} className="px-3 py-1">
                    <div className="text-[10px] text-white/12 uppercase tracking-widest mb-2">{group.group}</div>
                    {items.map(item => (
                      <div
                        key={item.action}
                        onClick={() => execute(item)}
                        className="flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer hover:bg-void-4 transition-colors"
                      >
                        <span className="text-[14px] w-6 text-center">{item.icon}</span>
                        <span className="flex-1 text-[13px] text-white/65">{item.label}</span>
                        {item.shortcut && (
                          <kbd className="text-[10px] text-white/12 px-1.5 py-0.5 rounded bg-white/5 border border-white/6 font-mono">
                            {item.shortcut}
                          </kbd>
                        )}
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
