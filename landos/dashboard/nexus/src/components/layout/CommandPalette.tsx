import { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search,
  Pencil,
  RotateCcw,
  Eye,
  FileSearch,
  Zap,
  Activity,
  Crosshair,
  DollarSign,
  Settings,
} from 'lucide-react'
import { cn } from '@/lib/cn'

interface CommandPaletteProps {
  open: boolean
  onClose: () => void
}

interface CommandItem {
  icon: React.ElementType
  label: string
  shortcut?: string
  action?: () => void
}

interface CommandGroup {
  title: string
  items: CommandItem[]
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  const groups: CommandGroup[] = [
    {
      title: 'MISSIONS',
      items: [
        { icon: Pencil, label: 'Launch Polygon Sweep', shortcut: '⌘P' },
        { icon: RotateCcw, label: 'Resume Washtenaw Scan', shortcut: '⌘W' },
      ],
    },
    {
      title: 'PIPELINE',
      items: [
        { icon: Eye, label: 'View Tier 1 Clusters', shortcut: '⌘⇧C' },
        { icon: FileSearch, label: 'Open Deal Tracker', shortcut: '⌘⇧D' },
      ],
    },
    {
      title: 'AGENTS',
      items: [
        { icon: Zap, label: 'Wake Scout Agent' },
        { icon: Activity, label: 'Check Municipal Agent Status' },
      ],
    },
    {
      title: 'NAVIGATE',
      items: [
        { icon: Crosshair, label: 'Go to Radar', shortcut: '⌘2', action: () => navigate('/radar') },
        { icon: DollarSign, label: 'Go to Economics', shortcut: '⌘4', action: () => navigate('/economics') },
        { icon: Settings, label: 'Go to Config', shortcut: '⌘8', action: () => navigate('/config') },
      ],
    },
  ]

  const allItems = groups.flatMap((g) => g.items)

  // Reset state when opened
  useEffect(() => {
    if (open) {
      setQuery('')
      setSelectedIndex(0)
      // Focus input after render
      requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open])

  const executeItem = useCallback(
    (item: CommandItem) => {
      if (item.action) item.action()
      onClose()
    },
    [onClose]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((i) => (i + 1) % allItems.length)
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((i) => (i - 1 + allItems.length) % allItems.length)
      } else if (e.key === 'Enter') {
        e.preventDefault()
        const item = allItems[selectedIndex]
        if (item) executeItem(item)
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    },
    [onClose, allItems, selectedIndex, executeItem]
  )

  if (!open) return null

  let flatIndex = 0

  return (
    <div
      className="fixed inset-0 z-50 bg-on-surface/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="mx-auto mt-[20vh] w-full max-w-[640px] overflow-hidden rounded-[16px] bg-white shadow-ambient-lg"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Search header */}
        <div className="flex items-center gap-4 border-b border-outline-variant/10 px-6 py-5">
          <Search size={20} strokeWidth={2} className="text-on-surface-variant/50" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search commands, agents, clusters..."
            className="flex-1 border-none bg-transparent p-0 text-base font-medium text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-0"
          />
          <div className="rounded bg-surface-container-low px-2 py-0.5">
            <span className="text-[9px] font-bold text-on-surface-variant">⌘K</span>
          </div>
        </div>

        {/* Results */}
        <div className="max-h-[480px] overflow-y-auto py-4">
          {groups.map((group) => (
            <section key={group.title} className="mb-4">
              <header className="px-6 py-2">
                <h3 className="text-[9px] font-bold uppercase tracking-widest text-on-surface-variant">
                  {group.title}
                </h3>
              </header>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const idx = flatIndex++
                  const isSelected = idx === selectedIndex
                  const Icon = item.icon
                  return (
                    <div
                      key={item.label}
                      className={cn(
                        'flex cursor-pointer items-center justify-between px-6 py-2.5 transition-colors',
                        isSelected
                          ? 'border-l-[3px] border-primary bg-primary/5'
                          : 'hover:bg-surface-container-low'
                      )}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      onClick={() => executeItem(item)}
                    >
                      <div className="flex items-center gap-4">
                        <Icon
                          size={16}
                          strokeWidth={2}
                          className={
                            isSelected
                              ? 'text-primary'
                              : 'text-on-surface-variant'
                          }
                        />
                        <span
                          className={cn(
                            'text-sm',
                            isSelected
                              ? 'font-semibold text-primary'
                              : 'font-medium text-on-surface-variant'
                          )}
                        >
                          {item.label}
                        </span>
                      </div>
                      {item.shortcut && (
                        <span className="text-[11px] font-medium tracking-tight text-on-surface-variant/50">
                          {item.shortcut}
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            </section>
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-outline-variant/10 bg-surface-container-low px-6 py-3">
          <span className="text-[9px] text-on-surface-variant">
            ESC to close · ↑↓ to navigate · ↵ to select
          </span>
          <span className="text-[9px] text-on-surface-variant/60">
            NEXUS v2.0.0
          </span>
        </div>
      </div>
    </div>
  )
}
