import { Brain, Package, Building2, TrendingUp, MapPin, Sparkles } from 'lucide-react'

const NODES = [
  { label: 'PACKAGING', Icon: Package, angle: -90 },
  { label: 'MUNICIPAL', Icon: Building2, angle: -18 },
  { label: 'ECONOMIC', Icon: TrendingUp, angle: 54 },
  { label: 'SPATIAL', Icon: MapPin, angle: 126 },
  { label: 'SIGNAL', Icon: Sparkles, angle: 198 },
]

const ORBIT_RADIUS = 160

export function NeuralCore() {
  const cx = 300
  const cy = 260

  return (
    <section className="flex-1 relative overflow-hidden flex items-center justify-center bg-surface scanline">
      {/* Dot grid background */}
      <div
        className="absolute inset-0 z-0 pointer-events-none opacity-10"
        style={{
          backgroundImage: 'radial-gradient(#d4c4b4 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }}
      />

      {/* Ghost gradient top-right */}
      <div
        className="absolute inset-0 pointer-events-none opacity-40 mix-blend-multiply"
        style={{
          background: 'radial-gradient(circle at 100% 0%, #ffddb8 0%, transparent 70%)',
        }}
      />
      {/* Ghost gradient bottom-left */}
      <div
        className="absolute inset-0 pointer-events-none opacity-10 mix-blend-multiply"
        style={{
          background: 'radial-gradient(circle at 0% 100%, #9b6b2a 0%, transparent 70%)',
        }}
      />

      {/* SVG layer */}
      <svg
        viewBox="0 0 600 520"
        className="relative z-10 w-full max-w-[600px] max-h-[520px]"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Concentric dashed circles */}
        <circle
          cx={cx}
          cy={cy}
          r={180}
          fill="none"
          stroke="#d4c4b4"
          strokeWidth="1"
          strokeDasharray="8 4"
          opacity="0.3"
        />
        <circle
          cx={cx}
          cy={cy}
          r={280}
          fill="none"
          stroke="#d4c4b4"
          strokeWidth="1"
          strokeDasharray="4 8"
          opacity="0.1"
        />

        {/* Dashed connection lines from center to each node */}
        {NODES.map((node) => {
          const rad = (node.angle * Math.PI) / 180
          const nx = cx + ORBIT_RADIUS * Math.cos(rad)
          const ny = cy + ORBIT_RADIUS * Math.sin(rad)
          return (
            <line
              key={node.label}
              x1={cx}
              y1={cy}
              x2={nx}
              y2={ny}
              stroke="#d4c4b4"
              strokeWidth="1"
              strokeDasharray="4"
              opacity="0.3"
            />
          )
        })}

        {/* Center hub - larger 88px (44r) */}
        <defs>
          <linearGradient id="neuralCopperGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#7f5313" />
            <stop offset="100%" stopColor="#9b6b2a" />
          </linearGradient>
        </defs>
        <circle cx={cx} cy={cy} r={44} fill="url(#neuralCopperGrad)" />
        <circle cx={cx} cy={cy} r={48} fill="none" stroke="white" strokeWidth="4" />

        {/* Orbiting node circles */}
        {NODES.map((node) => {
          const rad = (node.angle * Math.PI) / 180
          const nx = cx + ORBIT_RADIUS * Math.cos(rad)
          const ny = cy + ORBIT_RADIUS * Math.sin(rad)
          return (
            <circle
              key={node.label}
              cx={nx}
              cy={ny}
              r={20}
              fill="white"
              stroke="#7f5313"
              strokeWidth="1"
              opacity="0.3"
            />
          )
        })}
      </svg>

      {/* HTML overlay for icons */}
      <div className="absolute inset-0 z-20 pointer-events-none flex items-center justify-center">
        <div className="relative w-full max-w-[600px] max-h-[520px]" style={{ aspectRatio: '600/520' }}>
          {/* Center Brain icon with neural glow */}
          <div
            className="absolute pointer-events-none flex items-center justify-center"
            style={{
              left: `${(cx / 600) * 100}%`,
              top: `${(cy / 520) * 100}%`,
              transform: 'translate(-50%, -50%)',
            }}
          >
            <div
              className="w-[88px] h-[88px] rounded-full copper-gradient flex items-center justify-center border-4 border-white"
              style={{
                boxShadow: '0 0 20px rgba(127, 83, 19, 0.4), 0 0 40px rgba(127, 83, 19, 0.2)',
              }}
            >
              <Brain size={32} className="text-white" strokeWidth={2} />
            </div>
          </div>

          {/* NEURAL CORE ALPHA label */}
          <div
            className="absolute pointer-events-none flex items-center justify-center"
            style={{
              left: `${(cx / 600) * 100}%`,
              top: `${((cy + 64) / 520) * 100}%`,
              transform: 'translate(-50%, -50%)',
            }}
          >
            <div className="bg-white/95 backdrop-blur-md px-5 py-2 rounded-full border border-primary/20 shadow-lg">
              <span className="text-[11px] font-extrabold tracking-[0.2em] text-primary uppercase">
                Neural Core Alpha
              </span>
            </div>
          </div>

          {/* Orbiting node icons + labels */}
          {NODES.map((node) => {
            const rad = (node.angle * Math.PI) / 180
            const nx = cx + ORBIT_RADIUS * Math.cos(rad)
            const ny = cy + ORBIT_RADIUS * Math.sin(rad)
            const Icon = node.Icon
            return (
              <div
                key={node.label}
                className="absolute"
                style={{
                  left: `${(nx / 600) * 100}%`,
                  top: `${(ny / 520) * 100}%`,
                  transform: 'translate(-50%, -50%)',
                }}
              >
                <div className="w-10 h-10 rounded-full bg-white border border-primary/20 flex items-center justify-center shadow-lg">
                  <Icon size={16} className="text-primary" />
                </div>
                <span className="absolute top-full left-1/2 -translate-x-1/2 mt-1 text-[8px] font-bold tracking-widest text-on-surface-variant uppercase whitespace-nowrap">
                  {node.label}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
