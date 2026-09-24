/**
 * API Endpoint Constants
 * All backend API endpoints organized by resource
 */

const API_VERSION = '/api/v1';

export const ENDPOINTS = {
  // Auth endpoints
  AUTH: {
    LOGIN: `${API_VERSION}/auth/login`,
    REGISTER: `${API_VERSION}/auth/register`,
    LOGOUT: `${API_VERSION}/auth/logout`,
    REFRESH: `${API_VERSION}/auth/refresh`,
    ME: `${API_VERSION}/auth/me`,
    FORGOT_PASSWORD: `${API_VERSION}/auth/forgot-password`,
    RESET_PASSWORD: `${API_VERSION}/auth/reset-password`,
  },

  // HCP endpoints
  HCP: {
    LIST: `${API_VERSION}/hcps`,
    DETAIL: (id) => `${API_VERSION}/hcps/${id}`,
    CREATE: `${API_VERSION}/hcps`,
    UPDATE: (id) => `${API_VERSION}/hcps/${id}`,
    DELETE: (id) => `${API_VERSION}/hcps/${id}`,
    SEARCH: `${API_VERSION}/hcps/search`,
    INTERACTIONS: (id) => `${API_VERSION}/hcps/${id}/interactions`,
  },

  // Interaction endpoints
  INTERACTION: {
    LIST: `${API_VERSION}/interactions`,
    DETAIL: (id) => `${API_VERSION}/interactions/${id}`,
    CREATE: `${API_VERSION}/interactions`,
    UPDATE: (id) => `${API_VERSION}/interactions/${id}`,
    DELETE: (id) => `${API_VERSION}/interactions/${id}`,
    FOLLOWUP: (id) => `${API_VERSION}/interactions/${id}/followup`,
    HISTORY: `${API_VERSION}/interactions/history`,
  },

  // Chat endpoints
  CHAT: {
    SEND: `${API_VERSION}/ai/chat`,
    STREAM: `${API_VERSION}/ai/chat/stream`,
    SESSIONS: `${API_VERSION}/ai/chat/sessions`,
    SESSION_DETAIL: (id) => `${API_VERSION}/ai/chat/sessions/${id}`,
    SESSION_DELETE: (id) => `${API_VERSION}/ai/chat/sessions/${id}`,
  },

  // Analytics endpoints
  ANALYTICS: {
    DASHBOARD: `${API_VERSION}/analytics/dashboard`,
    INTERACTIONS: `${API_VERSION}/analytics/interactions`,
    HCP: `${API_VERSION}/analytics/hcps`,
    EXPORT: `${API_VERSION}/analytics/export`,
  },

  // Follow-up endpoints
  FOLLOWUP: {
    LIST: `${API_VERSION}/followups`,
    CREATE: `${API_VERSION}/followups`,
    CHECK_AVAILABILITY: `${API_VERSION}/followups/check-availability`,
    UPDATE: (id) => `${API_VERSION}/followups/${id}`,
    COMPLETE: (id) => `${API_VERSION}/followups/${id}/complete`,
  },

  // User endpoints
  USER: {
    PROFILE: `${API_VERSION}/users/profile`,
    UPDATE: `${API_VERSION}/users/profile`,
    PREFERENCES: `${API_VERSION}/users/preferences`,
  },

  // Doctor-only endpoints (role: "doctor")
  DOCTOR: {
    PROFILE: `${API_VERSION}/doctor/me/profile`,
    FOLLOWUPS: `${API_VERSION}/doctor/follow-ups`,
    STATS: `${API_VERSION}/doctor/stats`,
    HISTORY: `${API_VERSION}/doctor/history`,
    ANALYTICS: `${API_VERSION}/doctor/analytics`,
  },

  // Audit / compliance activity log
  AUDIT: {
    LIST: `${API_VERSION}/audit-logs`,
  },

  // AI-powered search over your own past interactions (RAG)
  SEARCH: {
    ASK: `${API_VERSION}/search/ask`,
  },

  // Next Best Action - weekly HCP priority ranking + Smart Day Planner
  PRIORITY: {
    WEEKLY: `${API_VERSION}/priorities/weekly`,
    DAY_PLAN: `${API_VERSION}/priorities/day-plan`,
    MARK_VISITED: `${API_VERSION}/priorities/day-plan/mark-visited`,
    ANALYTICS: `${API_VERSION}/priorities/day-plan/analytics`,
  },
};

// Helper function to build URLs with parameters
export const buildUrl = (endpoint, params = {}) => {
  let url = endpoint;
  Object.keys(params).forEach((key) => {
    url = url.replace(`:${key}`, params[key]);
  });
  return url;
};