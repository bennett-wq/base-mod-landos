import { configureStore } from '@reduxjs/toolkit';
import meshReducer from './meshSlice';
import uiReducer from './uiSlice';

export const store = configureStore({
  reducer: {
    mesh: meshReducer,
    ui: uiReducer,
  },
});
