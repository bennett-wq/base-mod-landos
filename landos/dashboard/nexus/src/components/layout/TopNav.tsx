import { useLocation } from 'react-router-dom'
import { Search, Bell, Command } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'

const breadcrumbs: Record<string, { section: string; detail: string }> = {
  '/mesh': { section: 'Mesh', detail: 'Event Nerve Center' },
  '/radar': { section: 'Radar', detail: 'Signal Discovery' },
  '/clusters': { section: 'Clusters', detail: 'Supply Intelligence' },
  '/economics': { section: 'Economics', detail: 'Deal Analysis' },
  '/command': { section: 'Command', detail: 'Agent Control' },
  '/pipeline': { section: 'Pipeline', detail: 'Deal Tracker' },
  '/missions': { section: 'Missions', detail: 'Field Operations' },
  '/config': { section: 'Outreach', detail: 'Communication Hub' },
}

export function TopNav() {
  const { pathname } = useLocation()
  const crumb = breadcrumbs[pathname]
  const toggleCommandPalette = useAppStore((s) => s.toggleCommandPalette)

  return (
    <header className="sticky top-0 z-30 flex h-[56px] items-center justify-between bg-white/80 px-6 backdrop-blur-xl">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2">
        <span className="text-sm font-bold text-on-surface">
          {crumb?.section ?? 'NEXUS'}
        </span>
        {crumb && (
          <>
            <span className="text-on-surface-variant/30">/</span>
            <span className="text-xs font-medium text-on-surface-variant">
              {crumb.detail}
            </span>
          </>
        )}
      </div>

      {/* Search — now clickable to open command palette */}
      <button
        onClick={toggleCommandPalette}
        className="flex w-[320px] items-center gap-2 rounded-full bg-surface-container-low/80 px-4 py-2 transition-colors hover:bg-surface-container"
      >
        <Search size={14} strokeWidth={2} className="text-on-surface-variant/40" />
        <span className="flex-1 text-left text-xs text-on-surface-variant/40">
          Search event mesh...
        </span>
        <div className="flex items-center gap-0.5 rounded-md bg-surface-container px-1.5 py-0.5">
          <Command size={10} className="text-on-surface-variant/50" />
          <span className="text-[10px] font-semibold text-on-surface-variant/50">K</span>
        </div>
      </button>

      {/* Right actions */}
      <div className="flex items-center gap-4">
        {/* Bell with notification dot */}
        <button className="relative rounded-lg p-1.5 text-on-surface-variant transition-colors hover:bg-surface-container-low hover:text-primary">
          <Bell size={18} strokeWidth={2} />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-primary ring-2 ring-white" />
        </button>

        {/* User avatar */}
        <div className="copper-gradient flex h-8 w-8 items-center justify-center rounded-full shadow-sm">
          <span className="text-[10px] font-bold text-white">BL</span>
        </div>
      </div>
    </header>
  )
}
