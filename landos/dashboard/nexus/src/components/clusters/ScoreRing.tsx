import { motion } from 'framer-motion'

interface ScoreRingProps {
  score: number
  size?: number
}

export function ScoreRing({ score, size = 80 }: ScoreRingProps) {
  const half = size / 2
  const r = half - 6
  const circumference = 2 * Math.PI * r
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="-rotate-90" width={size} height={size}>
        <circle
          cx={half}
          cy={half}
          r={r}
          fill="transparent"
          stroke="#f5f3f0"
          strokeWidth={4}
        />
        <motion.circle
          cx={half}
          cy={half}
          r={r}
          fill="transparent"
          stroke="#7f5313"
          strokeWidth={4}
          strokeDasharray={circumference}
          strokeLinecap="round"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={size >= 100 ? 'text-2xl font-black text-primary leading-none' : 'text-xl font-bold text-on-surface leading-none'}>
          {score}
        </span>
        <span className="text-[8px] font-bold uppercase text-[#827567]">Score</span>
      </div>
    </div>
  )
}
