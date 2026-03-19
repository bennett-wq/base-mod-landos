import { useState } from 'react'
import { MapCanvas } from '../components/radar/MapCanvas'
import { DrawControls } from '../components/radar/DrawControls'
import { LaunchBar } from '../components/radar/LaunchBar'
import { IntelSidebar } from '../components/radar/IntelSidebar'
import { SwarmActiveOverlay } from '../components/radar/SwarmActiveOverlay'

export default function RadarPage() {
  const [drawActive, setDrawActive] = useState(false)
  const [swarmActive, setSwarmActive] = useState(false)

  return (
    <div className="-m-8 flex h-[calc(100vh-56px-56px)] overflow-hidden">
      {/* Map area */}
      <div className="relative flex-1">
        <MapCanvas />

        <DrawControls active={drawActive} onToggle={() => setDrawActive((d) => !d)} />

        {drawActive && (
          <LaunchBar
            onClear={() => setDrawActive(false)}
            onLaunch={() => {
              setDrawActive(false)
              setSwarmActive(true)
            }}
          />
        )}

        {swarmActive && <SwarmActiveOverlay />}
      </div>

      {/* Intelligence sidebar */}
      <IntelSidebar />
    </div>
  )
}
