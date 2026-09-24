/**
 * Application Constants
 * Centralized constants used throughout the application
 */

// Interaction Types
export const INTERACTION_TYPES = {
  MEETING: 'meeting',
  CALL: 'call',
  EMAIL: 'email',
  OTHER: 'other',
};

export const INTERACTION_TYPE_LABELS = {
  [INTERACTION_TYPES.MEETING]: 'Meeting',
  [INTERACTION_TYPES.CALL]: 'Call',
  [INTERACTION_TYPES.EMAIL]: 'Email',
  [INTERACTION_TYPES.OTHER]: 'Other',
};

// Interaction Status
export const INTERACTION_STATUS = {
  DRAFT: 'draft',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
  ARCHIVED: 'archived',
};

// Follow-up Status
export const FOLLOWUP_STATUS = {
  PENDING: 'pending',
  COMPLETED: 'completed',
  OVERDUE: 'overdue',
  CANCELLED: 'cancelled',
};

// User Roles
export const USER_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  SALES_REP: 'sales_rep',
  VIEWER: 'viewer',
};

// HCP Status
export const HCP_STATUS = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  PENDING: 'pending',
};

// Date Formats
export const DATE_FORMATS = {
  DISPLAY: 'MMM dd, yyyy',
  DISPLAY_WITH_TIME: 'MMM dd, yyyy HH:mm',
  API: 'yyyy-MM-dd',
  API_FULL: "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",
  TIME: 'HH:mm',
  SHORT_DATE: 'MM/dd/yyyy',
};

// Notification Types
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
};

// Toast Defaults
export const TOAST_DEFAULTS = {
  POSITION: 'top-right',
  AUTO_CLOSE: 5000,
  HIDE_PROGRESS_BAR: false,
  NEWEST_ON_TOP: true,
  CLOSE_ON_CLICK: true,
  RTL: false,
  PAUSE_ON_FOCUS_LOSS: true,
  DRAGGABLE: true,
  PAUSE_ON_HOVER: true,
};

// Pagination Defaults
export const PAGINATION_DEFAULTS = {
  PAGE: 1,
  LIMIT: 20,
  MAX_LIMIT: 100,
};

// API Status Codes
export const API_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  VALIDATION_ERROR: 422,
  INTERNAL_ERROR: 500,
};

// Local Storage Keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'authToken',
  REFRESH_TOKEN: 'refreshToken',
  USER: 'user',
  THEME: 'theme',
  SIDEBAR_STATE: 'sidebarState',
};