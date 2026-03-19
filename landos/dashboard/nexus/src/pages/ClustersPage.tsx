import { useState } from 'react'
import { ClusterMap } from '../components/clusters/ClusterMap'
import { ClusterCards, CLUSTER_DATA } from '../components/clusters/ClusterCards'
import { ClusterDetailModal } from '../components/clusters/ClusterDetailModal'
import type { ClusterData } from '../components/clusters/ClusterCards'

export default function ClustersPage() {
  const [selectedCluster, setSelectedCluster] = useState<ClusterData | null>(null)
  const firstOwner = CLUSTER_DATA[0]?.owner ?? ''

  return (
    <>
      <div className="-m-8 flex h-[calc(100vh-56px-56px)] overflow-hidden">
        {/* Map half (left) */}
        <section className="relative w-1/2 bg-stone-200">
          <ClusterMap selectedOwner={selectedCluster?.owner ?? firstOwner} />
        </section>

        {/* Cards half (right) */}
        <ClusterCards onViewIntel={(cluster) => setSelectedCluster(cluster)} />
      </div>

      {/* Detail modal */}
      {selectedCluster && (
        <ClusterDetailModal
          cluster={selectedCluster}
          onClose={() => setSelectedCluster(null)}
        />
      )}
    </>
  )
}
