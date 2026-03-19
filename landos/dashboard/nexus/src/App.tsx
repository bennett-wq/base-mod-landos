import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Shell } from './components/layout/Shell'
import { PageSkeleton } from './components/shared/PageSkeleton'

const MeshPage = lazy(() => import('./pages/MeshPage'))
const RadarPage = lazy(() => import('./pages/RadarPage'))
const ClustersPage = lazy(() => import('./pages/ClustersPage'))
const EconomicsPage = lazy(() => import('./pages/EconomicsPage'))
const CommandPage = lazy(() => import('./pages/CommandPage'))
const PipelinePage = lazy(() => import('./pages/PipelinePage'))
const MissionsPage = lazy(() => import('./pages/MissionsPage'))
const ConfigPage = lazy(() => import('./pages/ConfigPage'))
const DeepAssessmentPage = lazy(() => import('./pages/DeepAssessmentPage'))

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Navigate to="/mesh" replace />} />
        <Route path="mesh" element={<Suspense fallback={<PageSkeleton />}><MeshPage /></Suspense>} />
        <Route path="radar" element={<Suspense fallback={<PageSkeleton />}><RadarPage /></Suspense>} />
        <Route path="clusters" element={<Suspense fallback={<PageSkeleton />}><ClustersPage /></Suspense>} />
        <Route path="economics" element={<Suspense fallback={<PageSkeleton />}><EconomicsPage /></Suspense>} />
        <Route path="command" element={<Suspense fallback={<PageSkeleton />}><CommandPage /></Suspense>} />
        <Route path="pipeline" element={<Suspense fallback={<PageSkeleton />}><PipelinePage /></Suspense>} />
        <Route path="missions" element={<Suspense fallback={<PageSkeleton />}><MissionsPage /></Suspense>} />
        <Route path="config" element={<Suspense fallback={<PageSkeleton />}><ConfigPage /></Suspense>} />
        <Route path="assessment/:id" element={<Suspense fallback={<PageSkeleton />}><DeepAssessmentPage /></Suspense>} />
      </Route>
    </Routes>
  )
}
