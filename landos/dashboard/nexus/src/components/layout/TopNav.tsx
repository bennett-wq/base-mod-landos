import { useLocation } from 'react-router-dom'
import { Search, Bell } from 'lucide-react'

const breadcrumbs: Record<string, string> = {
  '/mesh': 'Mesh — Event Nerve Center',
  '/radar': 'Radar — Signal Discovery',
  '/clusters': 'Clusters — Supply Intelligence',
  '/economics': 'Economics — Deal Analysis',
  '/command': 'Command — Agent Control',
  '/pipeline': 'Pipeline — Data Ingestion',
  '/missions': 'Missions — Field Operations',
  '/config': 'Config — System Settings',
}

export function TopNav() {
  const { pathname } = useLocation()
  const breadcrumb = breadcrumbs[pathname] ?? 'NEXUS'

  return (
    <header className="sticky top-0 z-30 flex h-[56px] items-center justify-between bg-white/80 px-6 backdrop-blur-md">
      {/* Breadcrumb */}
      <span className="text-sm font-bold text-primary">{breadcrumb}</span>

      {/* Search */}
      <div className="flex w-[320px] items-center gap-2 rounded-full border border-outline-variant/10 bg-surface-container-low px-3 py-1.5">
        <Search size={14} strokeWidth={2} className="text-on-surface-variant/50" />
        <input
          type="text"
          placeholder="Search event mesh..."
          className="w-full border-none bg-transparent p-0 text-xs text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-0"
        />
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-4">
        {/* Bell with notification dot */}
        <button className="relative text-on-surface-variant transition-colors hover:text-primary">
          <Bell size={20} strokeWidth={2} />
          <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-primary" />
        </button>

        {/* User avatar */}
        <div className="copper-gradient flex h-8 w-8 items-center justify-center rounded-full">
          <span className="text-[10px] font-bold text-white">BL</span>
        </div>
      </div>
    </header>
  )
}
