import { configureStore } from '@reduxjs/toolkit';
import meshReducer from './meshSlice';
import uiReducer from './uiSlice';
import missionsReducer from './missionsSlice';

export const store = configureStore({
  reducer: {
    mesh: meshReducer,
    ui: uiReducer,
    missions: missionsReducer,
  },
});
