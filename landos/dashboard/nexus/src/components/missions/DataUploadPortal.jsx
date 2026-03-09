import { useState, useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import { toggleUploadPortal, addUpload, classifyUpload, tickUpload, UPLOAD_TYPE_OPTIONS } from '../../store/missionsSlice';

const STATUS_STYLES = {
  classifying: { label: 'Classifying...', color: '#ffb800', bg: 'bg-nexus-amber/15 text-nexus-amber' },
  processing: { label: 'Processing', color: '#00f0ff', bg: 'bg-nexus-cyan/15 text-nexus-cyan' },
  ingested: { label: 'Ingested', color: '#00ff88', bg: 'bg-nexus-emerald/15 text-nexus-emerald' },
  failed: { label: 'Failed', color: '#ff2d55', bg: 'bg-nexus-crimson/15 text-nexus-crimson' },
};

function UploadItem({ upload }) {
  const dispatch = useDispatch();
  const [selectedType, setSelectedType] = useState(upload.dataType || '');
  const [desc, setDesc] = useState(upload.description || '');

  // Auto-tick processing uploads
  useEffect(() => {
    if (upload.status !== 'processing') return;
    const id = setInterval(() => dispatch(tickUpload(upload.id)), 300);
    return () => clearInterval(id);
  }, [upload.status, upload.id, dispatch]);

  const handleClassify = () => {
    if (!selectedType) return;
    dispatch(classifyUpload({ uploadId: upload.id, dataType: selectedType, description: desc }));
  };

  const style = STATUS_STYLES[upload.status];
  const ext = upload.fileName.split('.').pop().toUpperCase();

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-void-2 border border-white/5 rounded-xl p-4 relative overflow-hidden"
    >
      {/* Progress shimmer */}
      {upload.status === 'processing' && (
        <motion.div
          className="absolute inset-0 pointer-events-none"
          style={{ background: `linear-gradient(90deg, transparent, ${style.color}08, transparent)` }}
          animate={{ x: ['-100%', '100%'] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
        />
      )}

      <div className="flex items-start gap-3 relative z-10">
        {/* File icon */}
        <div className="w-12 h-14 rounded-lg bg-void-3 border border-white/6 flex flex-col items-center justify-center shrink-0">
          <span className="text-[18px]">
            {upload.dataType ? UPLOAD_TYPE_OPTIONS.find(t => t.id === upload.dataType)?.icon || '📦' : '📄'}
          </span>
          <span className="text-[8px] font-mono text-white/20 mt-0.5">{ext}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div className="font-display text-[13px] font-semibold text-[#e0e0e0] truncate">{upload.fileName}</div>
            <span className={`text-[9px] font-semibold px-2 py-0.5 rounded-full ${style.bg}`}>{style.label}</span>
          </div>
          <div className="text-[10px] text-white/18 mb-2">
            {(upload.fileSize / 1024).toFixed(1)} KB
            {upload.records && <> · <span className="text-nexus-emerald font-semibold">{upload.records} records ingested</span></>}
          </div>

          {/* Classification UI */}
          {upload.status === 'classifying' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              className="mt-3 space-y-2"
            >
              <div className="text-[10px] text-brass font-semibold uppercase tracking-widest mb-2">What is this data?</div>
              <div className="grid grid-cols-3 gap-1.5">
                {UPLOAD_TYPE_OPTIONS.map(opt => (
                  <button
                    key={opt.id}
                    onClick={() => setSelectedType(opt.id)}
                    className={`p-2.5 rounded-lg border text-left cursor-pointer transition-all ${
                      selectedType === opt.id
                        ? 'bg-brass/10 border-brass/30 shadow-[0_0_12px_var(--color-brass-glow)]'
                        : 'bg-void-3 border-white/5 hover:border-white/12'
                    }`}
                  >
                    <div className="text-[14px] mb-1">{opt.icon}</div>
                    <div className="text-[10px] font-semibold text-white/55">{opt.label}</div>
                    <div className="text-[9px] text-white/15 leading-snug mt-0.5">{opt.desc}</div>
                  </button>
                ))}
              </div>

              {selectedType === 'custom' && (
                <textarea
                  value={desc}
                  onChange={e => setDesc(e.target.value)}
                  placeholder="Describe this dataset..."
                  className="w-full bg-void-3 border border-white/6 rounded-lg px-3 py-2 text-[12px] text-[#e0e0e0] font-mono outline-none resize-none h-16 focus:border-brass-dim transition-colors"
                />
              )}

              <button
                onClick={handleClassify}
                disabled={!selectedType}
                className={`w-full py-2.5 rounded-lg font-display font-bold text-[12px] transition-all border-none cursor-pointer ${
                  selectedType
                    ? 'bg-brass text-void-0 hover:bg-brass-bright hover:shadow-[0_0_16px_var(--color-brass-glow)]'
                    : 'bg-void-3 text-white/15 cursor-not-allowed'
                }`}
              >
                Classify & Ingest
              </button>
            </motion.div>
          )}

          {/* Progress bar */}
          {upload.status === 'processing' && (
            <div className="h-1.5 bg-void-4 rounded-full overflow-hidden mt-2">
              <motion.div
                className="h-full rounded-full"
                style={{ background: style.color }}
                animate={{ width: `${upload.progress}%` }}
              />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function DataUploadPortal() {
  const dispatch = useDispatch();
  const { uploadPortalOpen, uploads } = useSelector(s => s.missions);

  const onDrop = useCallback((files) => {
    files.forEach(file => {
      dispatch(addUpload({
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
      }));
    });
  }, [dispatch]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/json': ['.json'],
      'application/pdf': ['.pdf'],
      'application/geo+json': ['.geojson'],
      'application/zip': ['.zip'],
    },
  });

  return (
    <AnimatePresence>
      {uploadPortalOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[700] flex items-center justify-center"
        >
          <div className="absolute inset-0 bg-void-0/90 backdrop-blur-xl" onClick={() => dispatch(toggleUploadPortal())} />

          <motion.div
            initial={{ scale: 0.92, y: 20, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.92, y: 20, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 200, damping: 25 }}
            className="relative w-[700px] max-h-[80vh] bg-void-1 border border-white/8 rounded-2xl overflow-hidden shadow-[0_24px_80px_rgba(0,0,0,0.6)]"
          >
            {/* Header */}
            <div className="px-7 py-5 border-b border-white/5 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brass/10 border border-brass/20 flex items-center justify-center text-xl">📦</div>
              <div>
                <h2 className="font-display text-[18px] font-extrabold text-[#e0e0e0]">Data Ingestion Portal</h2>
                <p className="text-[11px] text-white/20">Upload listings, parcels, zoning ordinances, plat maps, or any structured data</p>
              </div>
              <button
                onClick={() => dispatch(toggleUploadPortal())}
                className="ml-auto w-9 h-9 rounded-lg bg-void-3 border border-white/6 text-white/30 text-lg flex items-center justify-center hover:bg-void-4 hover:text-white/50 transition-all cursor-pointer"
              >
                ×
              </button>
            </div>

            <div className="p-7 space-y-4 overflow-y-auto max-h-[calc(80vh-80px)]">
              {/* Drop Zone */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${
                  isDragActive
                    ? 'border-brass bg-brass/5 shadow-[0_0_30px_var(--color-brass-glow)]'
                    : 'border-white/8 hover:border-brass-dim hover:bg-white/[0.01]'
                }`}
              >
                <input {...getInputProps()} />
                <motion.div
                  animate={isDragActive ? { scale: 1.1, y: -5 } : { scale: 1, y: 0 }}
                  className="text-[48px] mb-3"
                >
                  {isDragActive ? '🎯' : '📂'}
                </motion.div>
                <div className="font-display text-[16px] font-bold text-white/45 mb-2">
                  {isDragActive ? 'Drop to ingest' : 'Drop files here or click to browse'}
                </div>
                <div className="text-[12px] text-white/15">
                  CSV, Excel, JSON, GeoJSON, PDF, ZIP
                </div>
                <div className="flex justify-center gap-4 mt-4 text-[10px] text-white/10">
                  {['MLS Listings', 'Regrid Parcels', 'Zoning Codes', 'Plat Maps', 'Incentives'].map(t => (
                    <span key={t} className="px-2 py-1 rounded bg-white/4">{t}</span>
                  ))}
                </div>
              </div>

              {/* Upload List */}
              {uploads.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] text-white/12 uppercase tracking-[1.5px] mb-2">Recent Uploads</div>
                  {uploads.map(u => <UploadItem key={u.id} upload={u} />)}
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
