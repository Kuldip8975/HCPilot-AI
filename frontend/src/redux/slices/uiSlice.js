import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  isLoading: false,
  loadingMessage: null,
  sidebarOpen: true,
  theme: 'light',
  activeModal: null,
  modalData: null,
  activeTab: null,
  isMobile: window.innerWidth < 768,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.isLoading = action.payload;
      if (action.payload === false) {
        state.loadingMessage = null;
      }
    },
    setLoadingWithMessage: (state, action) => {
      state.isLoading = true;
      state.loadingMessage = action.payload;
    },
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action) => {
      state.sidebarOpen = action.payload;
    },
    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
      // Apply theme to document
      document.documentElement.setAttribute('data-theme', state.theme);
    },
    setTheme: (state, action) => {
      state.theme = action.payload;
      document.documentElement.setAttribute('data-theme', action.payload);
    },
    openModal: (state, action) => {
      state.activeModal = action.payload.modalId;
      state.modalData = action.payload.data || null;
    },
    closeModal: (state) => {
      state.activeModal = null;
      state.modalData = null;
    },
    setActiveTab: (state, action) => {
      state.activeTab = action.payload;
    },
    setMobile: (state, action) => {
      state.isMobile = action.payload;
      if (action.payload) {
        state.sidebarOpen = false;
      }
    },
  },
});

// Selectors
export const selectIsLoading = (state) => state.ui.isLoading;
export const selectLoadingMessage = (state) => state.ui.loadingMessage;
export const selectSidebarOpen = (state) => state.ui.sidebarOpen;
export const selectTheme = (state) => state.ui.theme;
export const selectActiveModal = (state) => state.ui.activeModal;
export const selectModalData = (state) => state.ui.modalData;
export const selectActiveTab = (state) => state.ui.activeTab;
export const selectIsMobile = (state) => state.ui.isMobile;

export const {
  setLoading,
  setLoadingWithMessage,
  toggleSidebar,
  setSidebarOpen,
  toggleTheme,
  setTheme,
  openModal,
  closeModal,
  setActiveTab,
  setMobile,
} = uiSlice.actions;

export default uiSlice.reducer;