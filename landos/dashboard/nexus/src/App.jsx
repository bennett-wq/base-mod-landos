import { useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { addSignal, tickAgents } from './store/meshSlice';
import { toggleCommandPalette } from './store/uiSlice';
import { toggleUploadPortal, toggleDrawMode } from './store/missionsSlice';
import Navbar from './components/shared/Navbar';
import MeshTab from './components/mesh/MeshTab';
import RadarTab from './components/radar/RadarTab';
import ClustersTab from './components/clusters/ClustersTab';
import CommandTab from './components/command/CommandTab';
import MissionsTab from './components/missions/MissionsTab';
import EconomicsTab from './components/economics/EconomicsTab';
import CommandPalette from './components/shared/CommandPalette';
import AgentDetail from './components/shared/AgentDetail';
import ToastContainer from './components/shared/ToastContainer';
import MissionTheater from './components/missions/MissionTheater';
import DataUploadPortal from './components/missions/DataUploadPortal';
import DealSpotlight from './components/missions/DealSpotlight';

const TABS = { mesh: MeshTab, radar: RadarTab, clusters: ClustersTab, command: CommandTab, missions: MissionsTab, economics: EconomicsTab };

export default function App() {
  const dispatch = useDispatch();
  const activeTab = useSelector(s => s.ui.activeTab);
  const ActiveComponent = TABS[activeTab];

  // Signal generation loop
  useEffect(() => {
    const id = setInterval(() => dispatch(addSignal()), 1200 + Math.random() * 2000);
    return () => clearInterval(id);
  }, [dispatch]);

  // Agent status tick
  useEffect(() => {
    const id = setInterval(() => dispatch(tickAgents()), 5000);
    return () => clearInterval(id);
  }, [dispatch]);

  // Keyboard shortcuts
  const handleKeyDown = useCallback((e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      dispatch(toggleCommandPalette());
    }
    // ⌘⇧U — Upload
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'U') {
      e.preventDefault();
      dispatch(toggleUploadPortal());
    }
    // ⌘⇧P — Polygon draw (when on radar)
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'P') {
      e.preventDefault();
      dispatch(toggleDrawMode());
    }
  }, [dispatch]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden">
      <Navbar />
      <div className="flex-1 overflow-hidden">
        <ActiveComponent />
      </div>
      {/* Overlays — ordered by z-index */}
      <CommandPalette />
      <AgentDetail />
      <ToastContainer />
      <DealSpotlight />
      <DataUploadPortal />
      <MissionTheater />
    </div>
  );
}
