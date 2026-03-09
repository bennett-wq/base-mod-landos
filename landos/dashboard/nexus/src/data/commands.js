export const COMMANDS = [
  {
    group: 'Missions',
    items: [
      { icon: '🗺️', label: 'Polygon Search — Draw on map', shortcut: '⌘⇧P', action: 'polygonSearch', dispatch: 'drawMode' },
      { icon: '📦', label: 'Upload Data — CSV, Excel, GeoJSON', shortcut: '⌘⇧U', action: 'uploadData', dispatch: 'uploadPortal' },
      { icon: '🚀', label: 'Deploy All Agents — Full county scan', shortcut: '', action: 'deployAll', dispatch: 'deployAll' },
      { icon: '📊', label: 'Generate Signal Report', shortcut: '⌘⇧I', action: 'signalReport' },
    ],
  },
  {
    group: 'Pipeline',
    items: [
      { icon: '▶', label: 'Run Full Pipeline', shortcut: '⌘⇧R', action: 'runPipeline' },
      { icon: '📡', label: 'Ingest Spark MLS', shortcut: '⌘⇧S', action: 'ingestSpark' },
      { icon: '🗺', label: 'Ingest Regrid CSV', shortcut: '⌘⇧G', action: 'ingestRegrid' },
    ],
  },
  {
    group: 'Agents',
    items: [
      { icon: '⚡', label: 'Wake All Agents', shortcut: '', action: 'wakeAll' },
      { icon: '🔮', label: 'Force Cluster Rescan', shortcut: '', action: 'rescan' },
      { icon: '📡', label: 'BBO Signal Discovery', shortcut: '', action: 'bbo' },
      { icon: '🏛', label: 'Municipal Scan (Step 7)', shortcut: '', action: 'muni' },
      { icon: '💎', label: 'Opportunity Convergence', shortcut: '', action: 'opportunity' },
    ],
  },
  {
    group: 'Navigate',
    items: [
      { icon: '⚡', label: 'Go to Mesh', shortcut: '', action: 'nav:mesh', dispatch: 'nav' },
      { icon: '🎯', label: 'Go to Radar', shortcut: '', action: 'nav:radar', dispatch: 'nav' },
      { icon: '🏢', label: 'Go to Clusters', shortcut: '', action: 'nav:clusters', dispatch: 'nav' },
      { icon: '🤖', label: 'Go to Command', shortcut: '', action: 'nav:command', dispatch: 'nav' },
      { icon: '🚀', label: 'Go to Missions', shortcut: '', action: 'nav:missions', dispatch: 'nav' },
      { icon: '📊', label: 'Go to Economics', shortcut: '', action: 'nav:economics', dispatch: 'nav' },
    ],
  },
];
