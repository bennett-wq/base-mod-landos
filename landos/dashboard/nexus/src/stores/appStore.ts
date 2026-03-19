import { create } from 'zustand'

interface AppState {
  // Active selections
  selectedCounty: string
  selectedClusterId: string | null
  activeMissionId: string | null

  // UI state
  commandPaletteOpen: boolean
  sidebarCollapsed: boolean

  // Actions
  setSelectedCounty: (county: string) => void
  setSelectedCluster: (id: string | null) => void
  setActiveMission: (id: string | null) => void
  toggleCommandPalette: () => void
  toggleSidebar: () => void
}

export const useAppStore = create<AppState>((set) => ({
  selectedCounty: 'Washtenaw',
  selectedClusterId: null,
  activeMissionId: null,
  commandPaletteOpen: false,
  sidebarCollapsed: false,

  setSelectedCounty: (county) => set({ selectedCounty: county }),
  setSelectedCluster: (id) => set({ selectedClusterId: id }),
  setActiveMission: (id) => set({ activeMissionId: id }),
  toggleCommandPalette: () => set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}))
