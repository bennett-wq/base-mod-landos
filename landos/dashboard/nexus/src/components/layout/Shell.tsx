import { useState, useEffect, useCallback } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'
import { MetricsStrip } from './MetricsStrip'
import { CommandPalette } from './CommandPalette'

export function Shell() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)

  const closeCommandPalette = useCallback(() => {
    setCommandPaletteOpen(false)
  }, [])

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

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
