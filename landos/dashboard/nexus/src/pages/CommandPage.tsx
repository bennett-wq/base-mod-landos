import { AgentRosterExpanded } from '../components/command/AgentRosterExpanded'
import { NeuralCore } from '../components/command/NeuralCore'
import { FloatingDiscovery } from '../components/command/FloatingDiscovery'
import { AgentTerminal } from '../components/command/AgentTerminal'
import { LiveIntelStream } from '../components/command/LiveIntelStream'

export default function CommandPage() {
  return (
    <div className="-m-8 flex h-[calc(100vh-56px-56px)] overflow-hidden relative">
      {/* Left — Agent Roster (300px) */}
      <AgentRosterExpanded />

      {/* Center — Neural Core + overlays */}
      <div className="flex-1 relative overflow-hidden">
        <NeuralCore />
        <FloatingDiscovery />
        <AgentTerminal />
      </div>

      {/* Right — Live Intel Stream (320px) */}
      <LiveIntelStream />
    </div>
  )
}
