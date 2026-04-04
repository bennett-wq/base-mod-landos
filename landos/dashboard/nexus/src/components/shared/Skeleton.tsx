interface SkeletonProps {
  width?: string
  height?: string
  className?: string
}

export function Skeleton({ width, height = '1rem', className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded-xl bg-surface-container-low/80 ${className}`}
      style={{ width, height }}
    />
  )
}
