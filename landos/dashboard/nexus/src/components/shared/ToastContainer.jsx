import { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { removeToast } from '../../store/meshSlice';
import { motion, AnimatePresence } from 'framer-motion';

export default function ToastContainer() {
  const dispatch = useDispatch();
  const toasts = useSelector(s => s.mesh.toasts);

  useEffect(() => {
    toasts.forEach(t => {
      setTimeout(() => dispatch(removeToast(t.id)), 2800);
    });
  }, [toasts, dispatch]);

  return (
    <div className="fixed bottom-5 right-5 z-[2000] flex flex-col gap-2">
      <AnimatePresence>
        {toasts.map(t => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 8, x: 8 }}
            animate={{ opacity: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="flex items-center gap-2 px-4 py-2.5 bg-void-2 border border-white/6 rounded-lg shadow-[0_8px_32px_rgba(0,0,0,0.4)] text-[12px] text-white/65 min-w-[280px]"
          >
            <span className="text-[16px]">{t.icon}</span>
            {t.message}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
