import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'
import { MetricsStrip } from './MetricsStrip'
import { CommandPalette } from './CommandPalette'
import { useAppStore } from '@/stores/appStore'

export function Shell() {
  const commandPaletteOpen = useAppStore((s) => s.commandPaletteOpen)
  const toggleCommandPalette = useAppStore((s) => s.toggleCommandPalette)
  const location = useLocation()

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

        {/* Ghost gradient overlays */}
        <div
          className="pointer-events-none fixed right-0 top-0 h-full w-1/2 opacity-30 mix-blend-multiply"
          style={{ background: 'radial-gradient(circle at 100% 0%, #ffddb8 0%, transparent 70%)' }}
        />
        <div
          className="pointer-events-none fixed bottom-0 left-[240px] h-1/2 w-1/2 opacity-15 mix-blend-multiply"
          style={{ background: 'radial-gradient(circle at 0% 100%, #9b6b2a 0%, transparent 70%)' }}
        />

        <main className="p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <MetricsStrip />

      <CommandPalette open={commandPaletteOpen} onClose={closeCommandPalette} />
    </div>
  )
}
