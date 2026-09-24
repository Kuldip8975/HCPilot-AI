/**
 * Application Configuration
 * Centralizes all environment variables and app settings
 */

// Environment detection
export const isDevelopment = import.meta.env.MODE === 'development';
export const isProduction = import.meta.env.MODE === 'production';
export const isTest = import.meta.env.MODE === 'test';

// API Configuration - IMPORTANT: Do NOT include /api/v1 here!
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
};

// App Configuration
export const APP_CONFIG = {
  name: import.meta.env.VITE_APP_NAME || 'Naukri CRM HCP Module',
  version: import.meta.env.VITE_APP_VERSION || '1.0.0',
  environment: import.meta.env.VITE_APP_ENV || 'development',
};

// Feature Flags
export const FEATURES = {
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  enableNotifications: import.meta.env.VITE_ENABLE_NOTIFICATIONS !== 'false',
  enableDarkMode: import.meta.env.VITE_ENABLE_DARK_MODE === 'true',
};

// Pagination Defaults
export const PAGINATION = {
  defaultLimit: 20,
  maxLimit: 100,
  defaultPage: 1,
};

// Toast Configuration
export const TOAST_CONFIG = {
  duration: 5000,
  position: 'top-right',
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
};

// Date Format Configuration
export const DATE_FORMATS = {
  display: 'MMM dd, yyyy',
  displayWithTime: 'MMM dd, yyyy HH:mm',
  api: 'yyyy-MM-dd',
  apiFull: "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",
  time: 'HH:mm',
  shortDate: 'MM/dd/yyyy',
};

// Color Theme Constants
export const COLORS = {
  primary: '#2563eb',
  secondary: '#64748b',
  success: '#22c55e',
  danger: '#ef4444',
  warning: '#f59e0b',
  info: '#3b82f6',
  dark: '#1e293b',
  light: '#f8fafc',
};