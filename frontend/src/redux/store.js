import { configureStore } from '@reduxjs/toolkit';
import { rootReducer } from './rootReducer';

// Custom middleware for logging (development only)
const loggerMiddleware = (store) => (next) => (action) => {
  if (import.meta.env.DEV) {
    console.group(`[Redux] ${action.type}`);
    console.log('Previous State:', store.getState());
    console.log('Action:', action);
    const result = next(action);
    console.log('Next State:', store.getState());
    console.groupEnd();
    return result;
  }
  return next(action);
};

// Create store
export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
      thunk: {
        extraArgument: {},
      },
    }).concat(loggerMiddleware),
  devTools: import.meta.env.DEV,
});

// Store reference for interceptors
if (typeof window !== 'undefined') {
  window.__REDUX_STORE__ = store;
}

// Remove TypeScript types - they are not needed in JavaScript
// export type RootState = ReturnType<typeof store.getState>;
// export type AppDispatch = typeof store.dispatch;