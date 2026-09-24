import { combineReducers } from '@reduxjs/toolkit';

import authReducer from './slices/authSlice';
import uiReducer from './slices/uiSlice';
import interactionReducer from './slices/interactionSlice';
import hcpReducer from './slices/hcpSlice';
import notificationReducer from './slices/notificationSlice';
import chatReducer from './slices/chatSlice';

export const rootReducer = combineReducers({
  auth: authReducer,
  ui: uiReducer,
  interactions: interactionReducer,
  hcps: hcpReducer,
  notifications: notificationReducer,
  chat: chatReducer,
});