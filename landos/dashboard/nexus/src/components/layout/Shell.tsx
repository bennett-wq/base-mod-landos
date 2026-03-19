import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'
import { MetricsStrip } from './MetricsStrip'
import { CommandPalette } from './CommandPalette'
import { useAppStore } from '@/stores/appStore'

export function Shell() {
  const commandPaletteOpen = useAppStore((s) => s.commandPaletteOpen)
  const toggleCommandPalette = useAppStore((s) => s.toggleCommandPalette)

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        toggleCommandPalette()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [toggleCommandPalette])

  const closeCommandPalette = () => {
    if (commandPaletteOpen) toggleCommandPalette()
  }

  return (
    <div className="min-h-screen bg-surface">
      <Sidebar />

      {/* Main content area */}
      <div className="ml-[240px] min-h-screen pb-[56px]">
        <TopNav />
        <main className="p-8">
          <Outlet />
        </main>
      </div>

      <MetricsStrip />

      <CommandPalette open={commandPaletteOpen} onClose={closeCommandPalette} />
    </div>
  )
}
