export const COMMANDS = [
  {
    group: 'Pipeline',
    items: [
      { icon: '▶', label: 'Run Full Pipeline', shortcut: '⌘⇧R', action: 'runPipeline' },
      { icon: '📡', label: 'Ingest Spark MLS', shortcut: '⌘⇧S', action: 'ingestSpark' },
      { icon: '🗺', label: 'Ingest Regrid CSV', shortcut: '⌘⇧G', action: 'ingestRegrid' },
      { icon: '📋', label: 'Signal Report', shortcut: '⌘⇧I', action: 'signalReport' },
    ],
  },
  {
    group: 'Agents',
    items: [
      { icon: '⚡', label: 'Wake All Agents', shortcut: '', action: 'wakeAll' },
      { icon: '🔮', label: 'Force Cluster Rescan', shortcut: '', action: 'rescan' },
      { icon: '📡', label: 'BBO Discovery', shortcut: '', action: 'bbo' },
      { icon: '🏛', label: 'Municipal Scan', shortcut: '', action: 'muni' },
    ],
  },
  {
    group: 'Claude Skills',
    items: [
      { icon: '🔄', label: '/loop — Poll pipeline 5m', shortcut: '', action: 'loop' },
      { icon: '📝', label: '/commit — Commit changes', shortcut: '', action: 'commit' },
      { icon: '🔍', label: '/simplify — Code quality', shortcut: '', action: 'simplify' },
      { icon: '🏗', label: '/feature-dev — Next step', shortcut: '', action: 'featureDev' },
    ],
  },
];
