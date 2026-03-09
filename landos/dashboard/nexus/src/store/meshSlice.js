import { createSlice } from '@reduxjs/toolkit';
import { AGENTS, RULES, SIGNAL_TYPES } from '../data/agents';
import { CLUSTERS, CITIES } from '../data/clusters';

const rand = (a) => a[Math.floor(Math.random() * a.length)];
const fmtTime = () => new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

const signalBodies = {
  listing_added: () => `New listing — ${(Math.random() * 20 + 1).toFixed(1)}ac in ${rand(CITIES)}`,
  listing_price_reduced: () => `Price cut $${Math.floor(Math.random() * 50000 + 10000)} on ${(Math.random() * 10 + 2).toFixed(1)}ac`,
  owner_cluster_detected: () => { const c = rand(CLUSTERS); return `${c.name} — ${c.lots} parcels, ${c.acres} acres`; },
  cdom_threshold_crossed: () => `CDOM ≥ 90 — fatigue indicator active`,
  private_remarks_signal: () => `BBO: "${rand(['package deal','take all lots','bring any offer','motivated seller','remaining lots'])}" in remarks`,
  developer_exit_signal: () => `Dev exit — ${rand(['expired 120d','withdrawn + CDOM','cancellation','off-market'])}`,
  parcel_score_updated: () => `Score: ${(Math.random() * .4 + .3).toFixed(2)} → ${(Math.random() * .4 + .5).toFixed(2)}`,
  parcel_linked: () => `Parcel linked to MLS — haversine 50m match`,
  subdivision_remnant: () => `Remnant: ${rand(CLUSTERS).name} — ${Math.floor(Math.random() * 15 + 2)} lots`,
  agent_accumulation: () => `Agent accum: ${rand(['RE/MAX','KW','Howard Hanna'])} with ${Math.floor(Math.random() * 8 + 3)} listings`,
};

const initialState = {
  agents: AGENTS.map(a => ({ ...a, stats: { ...a.stats } })),
  rules: RULES.map(r => ({ ...r })),
  signals: [],
  clusters: CLUSTERS,
  eventsPerSecond: 0,
  totalRulesFired: 0,
  totalWakes: 0,
  toasts: [],
};

const meshSlice = createSlice({
  name: 'mesh',
  initialState,
  reducers: {
    addSignal(state) {
      const sig = rand(SIGNAL_TYPES);
      const body = signalBodies[sig.type]?.() || sig.type;
      state.signals.unshift({
        id: Date.now() + Math.random(),
        type: sig.type,
        tier: sig.tier,
        icon: sig.icon,
        body,
        time: fmtTime(),
        family: sig.family,
        tags: [sig.family, rand(CITIES)],
      });
      if (state.signals.length > 50) state.signals.pop();

      // Fire a random rule
      const ruleIdx = Math.floor(Math.random() * state.rules.length);
      state.rules[ruleIdx].fires += 1;

      // Update counters
      state.eventsPerSecond = Math.floor(Math.random() * 8 + 2);
      state.totalRulesFired += Math.floor(Math.random() * 3);
      state.totalWakes += Math.floor(Math.random() * 2);
    },

    tickAgents(state) {
      state.agents.forEach(a => {
        const r = Math.random();
        if (r > 0.9) a.status = 'scanning';
        else if (r > 0.7) a.status = 'online';
        else if (r > 0.6) a.status = 'cooldown';
        a.stats.events += Math.floor(Math.random() * 10);
        a.stats.rules += Math.floor(Math.random() * 2);
      });
    },

    addToast(state, action) {
      state.toasts.push({ id: Date.now(), ...action.payload });
    },

    removeToast(state, action) {
      state.toasts = state.toasts.filter(t => t.id !== action.payload);
    },
  },
});

export const { addSignal, tickAgents, addToast, removeToast } = meshSlice.actions;
export default meshSlice.reducer;
