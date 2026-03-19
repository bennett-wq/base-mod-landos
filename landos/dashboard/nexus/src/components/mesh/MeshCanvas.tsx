import { Package, Building2, TrendingUp, MapPin, Sparkles, Zap } from 'lucide-react'

interface MeshCanvasProps {
  onNodeClick: (nodeIndex: number) => void
}

const NODES = [
  { label: 'PACKAGING', Icon: Package, angle: -90 },
  { label: 'MUNICIPAL', Icon: Building2, angle: -18 },
  { label: 'ECONOMIC', Icon: TrendingUp, angle: 54 },
  { label: 'SPATIAL', Icon: MapPin, angle: 126 },
  { label: 'SIGNAL', Icon: Sparkles, angle: 198 },
]

const ORBIT_RADIUS = 160

export function MeshCanvas({ onNodeClick }: MeshCanvasProps) {
  const cx = 300
  const cy = 260

  return (
    <section className="flex-1 relative overflow-hidden flex items-center justify-center">
      {/* Dot grid background */}
      <div
        className="absolute inset-0 z-0 pointer-events-none opacity-20"
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
        className="absolute inset-0 pointer-events-none opacity-20 mix-blend-multiply"
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
          r={ORBIT_RADIUS}
          fill="none"
          stroke="#d4c4b4"
          strokeWidth="1"
          strokeDasharray="8 4"
          opacity="0.4"
        />
        <circle
          cx={cx}
          cy={cy}
          r={240}
          fill="none"
          stroke="#d4c4b4"
          strokeWidth="1"
          strokeDasharray="4 8"
          opacity="0.2"
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
              className="mesh-line-active"
            />
          )
        })}

        {/* Center hub */}
        <defs>
          <linearGradient id="copperGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#7f5313" />
            <stop offset="100%" stopColor="#9b6b2a" />
          </linearGradient>
        </defs>
        <circle cx={cx} cy={cy} r={36} fill="url(#copperGrad)" />
        <circle cx={cx} cy={cy} r={40} fill="none" stroke="white" strokeWidth="4" />

        {/* Orbiting node circles */}
        {NODES.map((node, i) => {
          const rad = (node.angle * Math.PI) / 180
          const nx = cx + ORBIT_RADIUS * Math.cos(rad)
          const ny = cy + ORBIT_RADIUS * Math.sin(rad)
          return (
            <g key={node.label}>
              {/* Clickable circle */}
              <circle
                cx={nx}
                cy={ny}
                r={24}
                fill="white"
                stroke="#7f5313"
                strokeWidth="2"
                opacity="0.6"
                className="cursor-pointer hover:opacity-100 transition-opacity"
                onClick={() => onNodeClick(i)}
              />
            </g>
          )
        })}
      </svg>

      {/* HTML overlay for icons (better rendering than SVG foreignObject) */}
      <div className="absolute inset-0 z-20 pointer-events-none flex items-center justify-center">
        <div className="relative w-full max-w-[600px] max-h-[520px]" style={{ aspectRatio: '600/520' }}>
          {/* Center icon */}
          <div
            className="absolute pointer-events-none flex items-center justify-center"
            style={{
              left: `${(cx / 600) * 100}%`,
              top: `${(cy / 520) * 100}%`,
              transform: 'translate(-50%, -50%)',
            }}
          >
            <Zap size={28} className="text-white" strokeWidth={2.5} />
          </div>

          {/* TRIGGER ENGINE label */}
          <div
            className="absolute pointer-events-none flex items-center justify-center"
            style={{
              left: `${(cx / 600) * 100}%`,
              top: `${((cy + 56) / 520) * 100}%`,
              transform: 'translate(-50%, -50%)',
            }}
          >
            <div className="bg-white/90 backdrop-blur-sm px-4 py-1.5 rounded-full border border-outline-variant/20 shadow-sm">
              <span className="text-[9px] font-bold tracking-widest text-primary uppercase">
                Trigger Engine
              </span>
            </div>
          </div>

          {/* Orbiting node icons + labels */}
          {NODES.map((node, i) => {
            const rad = (node.angle * Math.PI) / 180
            const nx = cx + ORBIT_RADIUS * Math.cos(rad)
            const ny = cy + ORBIT_RADIUS * Math.sin(rad)
            const Icon = node.Icon
            return (
              <div
                key={node.label}
                className="absolute pointer-events-auto cursor-pointer group"
                style={{
                  left: `${(nx / 600) * 100}%`,
                  top: `${(ny / 520) * 100}%`,
                  transform: 'translate(-50%, -50%)',
                }}
                onClick={() => onNodeClick(i)}
              >
                <div className="w-12 h-12 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
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
