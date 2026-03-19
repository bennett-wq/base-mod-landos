import { Routes, Route, Navigate } from 'react-router-dom'
import { Shell } from './components/layout/Shell'
import MeshPage from './pages/MeshPage'
import RadarPage from './pages/RadarPage'
import ClustersPage from './pages/ClustersPage'
import EconomicsPage from './pages/EconomicsPage'
import CommandPage from './pages/CommandPage'
import PipelinePage from './pages/PipelinePage'
import MissionsPage from './pages/MissionsPage'
import ConfigPage from './pages/ConfigPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Navigate to="/mesh" replace />} />
        <Route path="mesh" element={<MeshPage />} />
        <Route path="radar" element={<RadarPage />} />
        <Route path="clusters" element={<ClustersPage />} />
        <Route path="economics" element={<EconomicsPage />} />
        <Route path="command" element={<CommandPage />} />
        <Route path="pipeline" element={<PipelinePage />} />
        <Route path="missions" element={<MissionsPage />} />
        <Route path="config" element={<ConfigPage />} />
      </Route>
    </Routes>
  )
}
