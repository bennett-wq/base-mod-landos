export function PageSkeleton() {
  return (
    <div className="min-h-screen w-full bg-surface p-8">
      <div className="animate-pulse space-y-8">
        <div className="h-8 w-64 rounded-lg bg-outline-variant/20" />
        <div className="h-96 w-full rounded-xl bg-outline-variant/10" />
        <div className="h-12 w-full rounded-lg bg-outline-variant/10" />
      </div>
    </div>
  )
}
