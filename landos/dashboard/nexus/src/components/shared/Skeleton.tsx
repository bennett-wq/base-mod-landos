interface SkeletonProps {
  width?: string
  height?: string
  className?: string
}

export function Skeleton({ width, height = '1rem', className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-surface-container-low rounded ${className}`}
      style={{ width, height }}
    />
  )
}
