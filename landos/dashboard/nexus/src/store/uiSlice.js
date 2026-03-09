import { createSlice } from '@reduxjs/toolkit';

const uiSlice = createSlice({
  name: 'ui',
  initialState: {
    activeTab: 'mesh',
    rightPanel: 'signals',
    selectedAgent: null,
    commandPaletteOpen: false,
    agentDetailOpen: false,
  },
  reducers: {
    setActiveTab(state, action) { state.activeTab = action.payload; },
    setRightPanel(state, action) { state.rightPanel = action.payload; },
    setSelectedAgent(state, action) {
      state.selectedAgent = action.payload;
      state.agentDetailOpen = !!action.payload;
    },
    toggleCommandPalette(state) { state.commandPaletteOpen = !state.commandPaletteOpen; },
    closeCommandPalette(state) { state.commandPaletteOpen = false; },
    closeAgentDetail(state) { state.agentDetailOpen = false; state.selectedAgent = null; },
  },
});

export const { setActiveTab, setRightPanel, setSelectedAgent, toggleCommandPalette, closeCommandPalette, closeAgentDetail } = uiSlice.actions;
export default uiSlice.reducer;
