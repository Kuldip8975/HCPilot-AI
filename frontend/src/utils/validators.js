/**
 * Validate email format
 */
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate phone number
 */
export const isValidPhone = (phone) => {
  const phoneRegex = /^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/;
  return phoneRegex.test(phone);
};

/**
 * Validate URL
 */
export const isValidUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/**
 * Validate date is not in the past
 */
export const isFutureDate = (date) => {
  const parsedDate = new Date(date);
  const now = new Date();
  return parsedDate > now;
};

/**
 * Validate date is not in the future
 */
export const isPastDate = (date) => {
  const parsedDate = new Date(date);
  const now = new Date();
  return parsedDate < now;
};

/**
 * Validate required field
 */
export const isRequired = (value) => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  return true;
};

/**
 * Validate min length
 */
export const minLength = (value, min) => {
  if (!value) return false;
  return String(value).length >= min;
};

/**
 * Validate max length
 */
export const maxLength = (value, max) => {
  if (!value) return true;
  return String(value).length <= max;
};

/**
 * Validate between min and max
 */
export const between = (num, min, max) => {
  if (num === null || num === undefined) return false;
  return num >= min && num <= max;
};

/**
 * Create a validation function with rules
 */
export const createValidator = (rules) => {
  return (value) => {
    for (const rule of rules) {
      const { validate, message } = rule;
      if (!validate(value)) {
        return message;
      }
    }
    return null;
  };
};

/**
 * Common validation rules
 */
export const VALIDATION_RULES = {
  email: (value) => ({
    valid: isValidEmail(value),
    message: 'Please enter a valid email address',
  }),
  phone: (value) => ({
    valid: isValidPhone(value),
    message: 'Please enter a valid phone number',
  }),
  required: (value) => ({
    valid: isRequired(value),
    message: 'This field is required',
  }),
  minLength: (min) => (value) => ({
    valid: minLength(value, min),
    message: `Must be at least ${min} characters`,
  }),
  maxLength: (max) => (value) => ({
    valid: maxLength(value, max),
    message: `Must be at most ${max} characters`,
  }),
};