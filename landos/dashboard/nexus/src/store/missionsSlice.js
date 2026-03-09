import { createSlice } from '@reduxjs/toolkit';
import { v4 as uuid } from 'uuid';

/* ─── Mission states ──────────────────────────────────────────────── */
// deploying → scanning → analyzing → complete | failed
const MISSION_PHASES = ['deploying', 'scanning', 'analyzing', 'complete'];

const PHASE_MESSAGES = {
  deploying: [
    'Initializing agent subsystems...',
    'Loading geographic boundaries...',
    'Preparing signal classifiers...',
    'Establishing mesh connection...',
  ],
  scanning: [
    'Scanning parcel records within polygon...',
    'Cross-referencing MLS listings...',
    'Checking owner clusters in target zone...',
    'Pulling municipal history for area...',
    'Running BBO signal detection...',
    'Analyzing CDOM thresholds...',
    'Matching subdivision remnants...',
  ],
  analyzing: [
    'Scoring convergence signals...',
    'Ranking opportunities by Tier...',
    'Generating deal economics...',
    'Packaging home-fit analysis...',
    'Calculating installed-price ranges...',
    'Evaluating developer fatigue indicators...',
    'Cross-matching incentive programs...',
  ],
  complete: [
    'Mission complete. Results ready for review.',
  ],
};

const AGENT_DEPLOY_LINES = {
  supply_intelligence: [
    'Activating Spark MLS adapter...',
    'Normalizing listing feeds for target zone...',
    'Running price-reduction detection...',
    'Linking parcels via haversine match...',
    'Scoring pipeline active — Δ≥0.05 threshold...',
  ],
  cluster_detection: [
    'ParcelClusterDetector initializing...',
    'Filtering vacant parcels in polygon...',
    'Running owner-name dedup...',
    'Detecting proximity clusters (50m threshold)...',
    'Cross-referencing subdivision boundaries...',
  ],
  spark_signal: [
    'BBO regex engine loaded...',
    'Scanning private remarks for package language...',
    'Checking CDOM ≥ 90 day fatigue...',
    'Detecting agent accumulation patterns...',
    'Flagging developer exit signals...',
  ],
  municipal_intelligence: [
    'Loading municipal records database...',
    'Scanning plat recordings in target zone...',
    'Checking PA 58 division allowances...',
    'Evaluating zoning overlay districts...',
    'Matching incentive programs...',
  ],
  opportunity_creation: [
    'Convergence engine warming up...',
    'Evaluating multi-signal overlap...',
    'Generating Tier 1 opportunity candidates...',
    'Packaging deal economics...',
    'Routing to deal spotlight...',
  ],
};

/* ─── Upload classification types ─────────────────────────────────── */
const UPLOAD_TYPES = [
  { id: 'listings', label: 'MLS Listings', icon: '📋', desc: 'CSV/Excel of property listings with addresses, prices, CDOM' },
  { id: 'parcels', label: 'Parcel Data', icon: '🗺️', desc: 'Regrid CSV, county GIS exports, or parcel shapefiles' },
  { id: 'zoning', label: 'Zoning Ordinances', icon: '📜', desc: 'Municipal zoning codes, overlay districts, special provisions' },
  { id: 'plats', label: 'Plat Maps / Site Plans', icon: '📐', desc: 'Recorded plats, subdivision maps, site condo master deeds' },
  { id: 'incentives', label: 'Incentive Programs', icon: '💰', desc: 'Grant programs, tax abatements, infrastructure subsidies' },
  { id: 'custom', label: 'Custom Dataset', icon: '📦', desc: 'Any other structured data — describe it and we will classify' },
];

const initialState = {
  /* Active missions */
  missions: [],
  activeMissionId: null,

  /* Upload portal */
  uploads: [],
  uploadPortalOpen: false,

  /* Deal spotlight */
  spotlightCluster: null,
  spotlightOpen: false,

  /* Polygon draw state */
  drawMode: false,
  drawnPolygon: null, // GeoJSON

  /* Mission theater */
  theaterOpen: false,
  theaterMissionId: null,
};

const missionsSlice = createSlice({
  name: 'missions',
  initialState,
  reducers: {
    /* ── Polygon Drawing ────────────────────────────────────────── */
    toggleDrawMode(state) {
      state.drawMode = !state.drawMode;
      if (!state.drawMode) state.drawnPolygon = null;
    },
    setDrawnPolygon(state, action) {
      state.drawnPolygon = action.payload;
      state.drawMode = false;
    },
    clearPolygon(state) {
      state.drawnPolygon = null;
    },

    /* ── Mission Lifecycle ──────────────────────────────────────── */
    createMission(state, action) {
      const { polygon, agents, name } = action.payload;
      const id = uuid();
      const mission = {
        id,
        name: name || `Mission ${state.missions.length + 1}`,
        polygon,
        agents: agents || ['supply_intelligence', 'cluster_detection'],
        phase: 'deploying',
        phaseIndex: 0,
        progress: 0,
        logs: [{ time: new Date().toISOString(), text: 'Mission created. Deploying agents...', type: 'system' }],
        results: null,
        createdAt: new Date().toISOString(),
        findings: { parcels: 0, clusters: 0, opportunities: 0, signals: 0 },
      };
      state.missions.unshift(mission);
      state.activeMissionId = id;
      state.theaterOpen = true;
      state.theaterMissionId = id;
      state.drawnPolygon = null;
    },

    tickMission(state, action) {
      const mission = state.missions.find(m => m.id === action.payload);
      if (!mission || mission.phase === 'complete') return;

      mission.progress = Math.min(100, mission.progress + 2 + Math.random() * 3);

      // Add a log line
      const phaseMessages = PHASE_MESSAGES[mission.phase] || [];
      const agentLines = mission.agents.flatMap(a => AGENT_DEPLOY_LINES[a] || []);
      const allLines = [...phaseMessages, ...agentLines];
      const line = allLines[Math.floor(Math.random() * allLines.length)];
      if (line) {
        mission.logs.push({
          time: new Date().toISOString(),
          text: line,
          type: mission.phase === 'complete' ? 'success' : mission.phase,
        });
      }
      if (mission.logs.length > 80) mission.logs = mission.logs.slice(-60);

      // Update findings
      if (mission.phase === 'scanning') {
        mission.findings.parcels += Math.floor(Math.random() * 12);
        mission.findings.clusters += Math.random() > 0.7 ? 1 : 0;
        mission.findings.signals += Math.floor(Math.random() * 3);
      }
      if (mission.phase === 'analyzing') {
        mission.findings.opportunities += Math.random() > 0.8 ? 1 : 0;
      }

      // Phase transitions
      if (mission.progress >= 33 && mission.phaseIndex === 0) {
        mission.phase = 'scanning';
        mission.phaseIndex = 1;
        mission.logs.push({ time: new Date().toISOString(), text: '── Phase: SCANNING ──', type: 'phase' });
      }
      if (mission.progress >= 66 && mission.phaseIndex === 1) {
        mission.phase = 'analyzing';
        mission.phaseIndex = 2;
        mission.logs.push({ time: new Date().toISOString(), text: '── Phase: ANALYZING ──', type: 'phase' });
      }
      if (mission.progress >= 100) {
        mission.phase = 'complete';
        mission.phaseIndex = 3;
        mission.findings.parcels = Math.max(mission.findings.parcels, 40 + Math.floor(Math.random() * 200));
        mission.findings.clusters = Math.max(mission.findings.clusters, 3 + Math.floor(Math.random() * 15));
        mission.findings.opportunities = Math.max(mission.findings.opportunities, 1 + Math.floor(Math.random() * 8));
        mission.findings.signals = Math.max(mission.findings.signals, 10 + Math.floor(Math.random() * 40));
        mission.logs.push({ time: new Date().toISOString(), text: `Mission complete — ${mission.findings.opportunities} opportunities discovered`, type: 'success' });
      }
    },

    closeMissionTheater(state) {
      state.theaterOpen = false;
    },
    openMissionTheater(state, action) {
      state.theaterMissionId = action.payload;
      state.theaterOpen = true;
    },

    /* ── Upload Portal ──────────────────────────────────────────── */
    toggleUploadPortal(state) {
      state.uploadPortalOpen = !state.uploadPortalOpen;
    },
    addUpload(state, action) {
      const { fileName, fileSize, fileType, dataType, description } = action.payload;
      state.uploads.unshift({
        id: uuid(),
        fileName,
        fileSize,
        fileType,
        dataType: dataType || null,
        description: description || '',
        status: 'classifying', // classifying → processing → ingested | failed
        progress: 0,
        createdAt: new Date().toISOString(),
        records: null,
      });
    },
    classifyUpload(state, action) {
      const { uploadId, dataType, description } = action.payload;
      const upload = state.uploads.find(u => u.id === uploadId);
      if (upload) {
        upload.dataType = dataType;
        upload.description = description || upload.description;
        upload.status = 'processing';
      }
    },
    tickUpload(state, action) {
      const upload = state.uploads.find(u => u.id === action.payload);
      if (!upload || upload.status === 'ingested') return;
      upload.progress = Math.min(100, upload.progress + 5 + Math.random() * 10);
      if (upload.progress >= 100) {
        upload.status = 'ingested';
        upload.records = Math.floor(Math.random() * 500 + 50);
      }
    },

    /* ── Deal Spotlight ─────────────────────────────────────────── */
    openSpotlight(state, action) {
      state.spotlightCluster = action.payload;
      state.spotlightOpen = true;
    },
    closeSpotlight(state) {
      state.spotlightOpen = false;
      state.spotlightCluster = null;
    },
  },
});

export const UPLOAD_TYPE_OPTIONS = UPLOAD_TYPES;
export const {
  toggleDrawMode, setDrawnPolygon, clearPolygon,
  createMission, tickMission, closeMissionTheater, openMissionTheater,
  toggleUploadPortal, addUpload, classifyUpload, tickUpload,
  openSpotlight, closeSpotlight,
} = missionsSlice.actions;
export default missionsSlice.reducer;
