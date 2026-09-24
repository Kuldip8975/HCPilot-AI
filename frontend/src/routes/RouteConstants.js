export const ROUTES = {
  // Public Routes
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',

  // Protected Routes
  DASHBOARD: '/dashboard',
  HOME: '/',

  // Doctor-only Routes (role: "doctor")
  DOCTOR_DASHBOARD: '/doctor-dashboard',

  // HCP Management
  HCPS: '/hcps',
  HCP_DETAILS: '/hcps/:id',
  HCP_CREATE: '/hcps/create',
  HCP_EDIT: '/hcps/:id/edit',

  // Interaction Management
  INTERACTIONS: '/interactions',
  INTERACTION_NEW: '/interactions/new',
  INTERACTION_DETAILS: '/interactions/:id',
  INTERACTION_EDIT: '/interactions/:id/edit',
  INTERACTION_HISTORY: '/interactions/history',

  // Chat
  CHAT: '/chat',
  CHAT_SESSION: '/chat/:sessionId',

  // Analytics
  ANALYTICS: '/analytics',
  ANALYTICS_REPORTS: '/analytics/reports',

  // Compliance / audit trail
  ACTIVITY_LOG: '/activity-log',

  // AI-powered smart search over past interactions
  SMART_SEARCH: '/smart-search',

  // Next Best Action - weekly HCP priority ranking
  PRIORITIES: '/priorities',

  // Settings
  SETTINGS: '/settings',
  SETTINGS_PROFILE: '/settings/profile',
  SETTINGS_PREFERENCES: '/settings/preferences',

  // Fallback
  NOT_FOUND: '*',
};