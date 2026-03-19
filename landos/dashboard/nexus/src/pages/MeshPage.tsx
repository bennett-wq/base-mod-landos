import { useState } from 'react'
import { AgentRoster } from '../components/mesh/AgentRoster'
import { MeshCanvas } from '../components/mesh/MeshCanvas'
import { IntelFeed } from '../components/mesh/IntelFeed'
import { AgentDetailPanel } from '../components/mesh/AgentDetailPanel'

export default function MeshPage() {
  const [selectedNode, setSelectedNode] = useState<number | null>(null)

  return (
    <div className="-m-8 flex h-[calc(100vh-56px-56px)] overflow-hidden relative">
      <AgentRoster />
      <MeshCanvas onNodeClick={(i) => setSelectedNode(i)} />
      <IntelFeed />
      <AgentDetailPanel nodeIndex={selectedNode} onClose={() => setSelectedNode(null)} />
    </div>
  )
}
