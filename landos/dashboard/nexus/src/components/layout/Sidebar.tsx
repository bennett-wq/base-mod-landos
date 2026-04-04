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
  { to: '/mesh', label: 'Mesh', icon: Zap, description: 'Event Nerve Center' },
  { to: '/radar', label: 'Radar', icon: Crosshair, description: 'Signal Discovery' },
  { to: '/clusters', label: 'Clusters', icon: Building2, description: 'Supply Intelligence' },
  { to: '/economics', label: 'Economics', icon: Wallet, description: 'Deal Analysis' },
  { to: '/command', label: 'Command', icon: Bot, description: 'Agent Control' },
  { to: '/pipeline', label: 'Pipeline', icon: BarChart3, description: 'Deal Tracker' },
  { to: '/missions', label: 'Missions', icon: Rocket, description: 'Field Operations' },
] as const

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-full w-[240px] flex-col bg-surface-container-lowest">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 pb-5 pt-6">
        <div className="copper-gradient flex h-9 w-9 items-center justify-center rounded-xl shadow-copper-glow">
          <span className="text-sm font-bold text-on-primary">B</span>
        </div>
        <div className="flex flex-col">
          <span className="text-lg font-bold leading-tight tracking-tight text-on-surface">
            BaseMod
          </span>
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
            NEXUS
          </span>
        </div>
      </div>

      {/* Section label */}
      <div className="px-6 pb-3 pt-4">
        <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-on-surface-variant/40">
          Navigation
        </span>
      </div>

      {/* Nav items */}
      <nav className="flex flex-1 flex-col gap-0.5 px-3">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-[11px] font-bold uppercase tracking-[0.08em] transition-all duration-200',
                isActive
                  ? 'border-l-[3px] border-primary bg-primary/5 font-semibold text-primary'
                  : 'border-l-[3px] border-transparent text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface'
              )
            }
          >
            <Icon size={16} strokeWidth={2} className="transition-colors" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom section */}
      <div className="px-3 pb-2">
        <div className="mb-2 h-px bg-surface-container-low" />

        <NavLink
          to="/config"
          className={({ isActive }) =>
            cn(
              'group flex items-center gap-3 rounded-xl px-3 py-2.5 text-[11px] font-bold uppercase tracking-[0.08em] transition-all duration-200',
              isActive
                ? 'border-l-[3px] border-primary bg-primary/5 font-semibold text-primary'
                : 'border-l-[3px] border-transparent text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface'
            )
          }
        >
          <Mail size={16} strokeWidth={2} className="transition-colors" />
          Outreach
        </NavLink>
      </div>

      {/* Version badge */}
      <div className="px-6 pb-5 pt-2">
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-1.5 rounded-full bg-success glow-pulse" />
          <span className="text-[9px] font-medium text-on-surface-variant/40">
            NEXUS v2.0 &middot; All systems nominal
          </span>
        </div>
      </div>
    </aside>
  )
}
