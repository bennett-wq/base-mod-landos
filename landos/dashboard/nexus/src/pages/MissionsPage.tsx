import { MissionsSidebar } from '@/components/missions/MissionsSidebar'
import { ActionBar } from '@/components/missions/ActionBar'
import { MissionList } from '@/components/missions/MissionList'
import { ActiveMission } from '@/components/missions/ActiveMission'
import { SwarmTerminal } from '@/components/missions/SwarmTerminal'

export default function MissionsPage() {
  return (
    <div className="-m-8 flex min-h-[calc(100vh-120px)]">
      {/* Missions Sidebar (its own nav, not the main NEXUS sidebar) */}
      <MissionsSidebar />

      {/* Main content area */}
      <div className="flex-1 overflow-y-auto bg-surface p-8">
        {/* Action bar */}
        <ActionBar />

        {/* Mission list + Active mission */}
        <div className="grid grid-cols-12 gap-8">
          <MissionList />
          <ActiveMission />
        </div>

        {/* Swarm terminal */}
        <div className="mt-8">
          <SwarmTerminal />
        </div>
      </div>
    </div>
  )
}
