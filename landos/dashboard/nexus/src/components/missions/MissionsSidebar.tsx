import {
  LayoutDashboard,
  Radar,
  Users,
  Archive,
  TrendingUp,
  HelpCircle,
  LogOut,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/cn'

interface NavItem {
  label: string
  icon: LucideIcon
  active?: boolean
}

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard },
  { label: 'Land Swarm', icon: Radar },
  { label: 'Agent Tracking', icon: Users, active: true },
  { label: 'Mission Archives', icon: Archive },
  { label: 'Analytics', icon: TrendingUp },
]

export function MissionsSidebar() {
  return (
    <aside className="flex h-full w-[280px] flex-shrink-0 flex-col bg-white py-8">
      {/* Header */}
      <div className="mb-10 px-6">
        <div className="flex items-center gap-3">
          <div className="copper-gradient flex h-8 w-8 items-center justify-center rounded-lg">
            <Radar size={16} className="text-on-primary" />
          </div>
          <div>
            <h1 className="text-xl font-black text-on-surface">Acquisition HQ</h1>
            <p className="text-[10px] font-bold uppercase tracking-widest text-primary">
              Strategic Control
            </p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1">
        {navItems.map(({ label, icon: Icon, active }) => (
          <button
            key={label}
            className={cn(
              'flex w-full items-center gap-3 border-l-[3px] px-6 py-3 text-sm transition-all',
              active
                ? 'border-primary bg-surface-container-low font-semibold text-primary'
                : 'border-transparent text-on-surface-variant hover:text-primary'
            )}
          >
            <Icon size={18} strokeWidth={2} />
            <span className="font-medium">{label}</span>
          </button>
        ))}
      </nav>

      {/* Bottom actions */}
      <div className="mt-auto space-y-4 px-6">
        <button className="copper-gradient w-full rounded-lg py-3 text-sm font-bold text-white shadow-sm transition-transform active:scale-95">
          Wake the Swarm
        </button>
        <div className="border-t border-outline-variant/20 pt-4">
          <button className="flex w-full items-center gap-3 py-2 text-sm text-on-surface-variant transition-colors hover:text-primary">
            <HelpCircle size={16} />
            <span>Support</span>
          </button>
          <button className="flex w-full items-center gap-3 py-2 text-sm text-on-surface-variant transition-colors hover:text-primary">
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </aside>
  )
}
