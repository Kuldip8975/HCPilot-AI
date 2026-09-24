import { toast } from 'react-toastify';

/**
 * Request interceptor - adds auth token to headers
 */
export const requestInterceptor = (config) => {
  const token = localStorage.getItem('authToken');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Add timestamp to GET requests to prevent caching
  if (config.method === 'get') {
    config.params = {
      ...config.params,
      _t: Date.now(),
    };
  }

  return config;
};

/**
 * Request error handler
 */
export const requestErrorHandler = (error) => {
  console.error('Request error:', error);
  return Promise.reject(error);
};

/**
 * Response success handler
 */
export const responseSuccessHandler = (response) => {
  // Return the data directly for convenience
  return response.data || response;
};

// The backend actually sends errors in TWO different shapes, depending on
// which code path produced them:
//   1. Plain FastAPI HTTPException (most hand-raised errors in endpoints):
//        { "detail": "some string" }  or  { "detail": [ {msg, loc, ...} ] }
//   2. The app's custom error handlers (app/api/middleware/error_handler.py -
//      AppException, RequestValidationError, and unhandled exceptions):
//        { "success": false, "error": { "code", "message", "details", "timestamp" } }
//      For validation errors specifically, "error.message" is ALWAYS the
//      generic string "Validation error" - the actual field-level messages
//      are in "error.details": [ { field, message, type }, ... ].
// Without handling both shapes, real backend error text (especially the
// specific validation reason, e.g. "time_budget_minutes: Input should be
// greater than 0") never reaches the toast - it silently falls back to a
// generic message instead.
const getErrorMessage = (data, fallback) => {
  if (!data) return fallback;

  // Shape 2: custom { success, error: { message, details } } envelope.
  if (data.error) {
    const { message, details } = data.error;
    if (Array.isArray(details) && details.length > 0) {
      const fieldMessages = details
        .map((d) => (d && (d.message || d.msg)) ? (d.field ? `${d.field}: ${d.message || d.msg}` : (d.message || d.msg)) : null)
        .filter(Boolean);
      if (fieldMessages.length > 0) return fieldMessages.join('; ');
    }
    if (typeof message === 'string' && message) return message;
  }

  // Shape 1: standard FastAPI { detail } - string or Pydantic error array.
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail) && data.detail.length > 0) {
    const fieldMessages = data.detail
      .map((d) => (d && (d.msg || d.message)) || null)
      .filter(Boolean);
    if (fieldMessages.length > 0) return fieldMessages.join('; ');
  }

  if (typeof data.message === 'string' && data.message) return data.message;

  return fallback;
};

/**
 * Response error handler
 */
export const responseErrorHandler = (error) => {
  const { response, config } = error;

  // Network error
  if (!response) {
    toast.error('Network error. Please check your connection.');
    return Promise.reject(error);
  }

  // Handle specific status codes
  switch (response.status) {
    case 400:
      toast.error(getErrorMessage(response.data, 'Bad request'));
      break;

    case 401:
      // Unauthorized - clear session and redirect
      localStorage.removeItem('authToken');
      localStorage.removeItem('refreshToken');

      // Dispatch logout action if store is available
      if (window.__REDUX_STORE__) {
        window.__REDUX_STORE__.dispatch({ type: 'auth/logout/fulfilled' });
      }

      // Redirect to login if not already there
      if (window.location.pathname !== '/login') {
        toast.error('Session expired. Please login again.');
        window.location.href = '/login';
      }
      break;

    case 403:
      toast.error(getErrorMessage(response.data, 'Access forbidden'));
      break;

    case 404:
      toast.error(getErrorMessage(response.data, 'Resource not found'));
      break;

    case 409:
      // Conflict - e.g. double-booking on a follow-up. The backend's
      // detail message already explains what clashed and who booked it.
      toast.error(getErrorMessage(response.data, 'This conflicts with an existing booking.'));
      break;

    case 422:
      // Validation errors - show the specific field-level message(s), not
      // just the generic "Validation error" wrapper text (see
      // getErrorMessage's comment above for why the plain error.message
      // alone isn't useful here).
      toast.error(getErrorMessage(response.data, 'Validation error'));
      break;

    case 429:
      toast.error('Too many requests. Please try again later.');
      break;

    case 500:
      toast.error('Server error. Please try again later.');
      break;

    default:
      toast.error(getErrorMessage(response.data, 'An unexpected error occurred'));
  }

  return Promise.reject(error);
};