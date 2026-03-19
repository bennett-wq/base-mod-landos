import { NavLink } from 'react-router-dom'
import {
  Zap,
  Crosshair,
  Building2,
  Wallet,
  Bot,
  BarChart3,
  Rocket,
  Mail,
} from 'lucide-react'
import { cn } from '@/lib/cn'

const navItems = [
  { to: '/mesh', label: 'Mesh', icon: Zap },
  { to: '/radar', label: 'Radar', icon: Crosshair },
  { to: '/clusters', label: 'Clusters', icon: Building2 },
  { to: '/economics', label: 'Economics', icon: Wallet },
  { to: '/command', label: 'Command', icon: Bot },
  { to: '/pipeline', label: 'Pipeline', icon: BarChart3 },
  { to: '/missions', label: 'Missions', icon: Rocket },
] as const

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-full w-[240px] flex-col bg-surface-container-lowest">
      {/* Logo */}
      <div className="flex items-center gap-3 p-6">
        <div className="copper-gradient flex h-8 w-8 items-center justify-center rounded-lg">
          <span className="text-sm font-bold text-on-primary">B</span>
        </div>
        <div className="flex flex-col">
          <span className="text-lg font-bold leading-tight text-on-surface">
            BaseMod
          </span>
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
            NEXUS
          </span>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex flex-1 flex-col gap-0.5 px-3">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 text-[10px] font-bold uppercase tracking-[0.1em] transition-colors',
                isActive
                  ? 'border-l-[3px] border-primary bg-primary/5 font-semibold text-primary'
                  : 'text-on-surface-variant hover:bg-surface-container-low'
              )
            }
          >
            <Icon size={16} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Config at bottom */}
      <div className="border-t border-outline-variant/10 p-4">
        <NavLink
          to="/config"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-3 py-2.5 text-[10px] font-bold uppercase tracking-[0.1em] transition-colors',
              isActive
                ? 'border-l-[3px] border-primary bg-primary/5 font-semibold text-primary'
                : 'text-on-surface-variant hover:bg-surface-container-low'
            )
          }
        >
          <Mail size={16} strokeWidth={2} />
          Outreach
        </NavLink>
      </div>
    </aside>
  )
}
