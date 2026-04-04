export function PageSkeleton() {
  return (
    <div className="min-h-screen w-full bg-surface p-8">
      <div className="animate-pulse space-y-6">
        <div className="h-7 w-48 rounded-lg bg-surface-container-low" />
        <div className="h-4 w-72 rounded-md bg-surface-container-low/60" />
        <div className="mt-4 h-80 w-full rounded-2xl bg-surface-container-low/40" />
        <div className="flex gap-6">
          <div className="h-32 flex-1 rounded-xl bg-surface-container-low/40" />
          <div className="h-32 flex-1 rounded-xl bg-surface-container-low/40" />
          <div className="h-32 flex-1 rounded-xl bg-surface-container-low/40" />
        </div>
      </div>
    </div>
  )
}
