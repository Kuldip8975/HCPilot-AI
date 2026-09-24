/**
 * Generate a unique ID
 */
export const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
};

/**
 * Deep clone an object
 */
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime());
  if (obj instanceof Array) return obj.map(item => deepClone(item));
  if (obj instanceof Object) {
    const cloned = {};
    Object.keys(obj).forEach(key => {
      cloned[key] = deepClone(obj[key]);
    });
    return cloned;
  }
  return obj;
};

/**
 * Debounce function
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Throttle function
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
};

/**
 * Group array by key
 */
export const groupBy = (array, key) => {
  return array.reduce((result, item) => {
    const groupKey = item[key];
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey].push(item);
    return result;
  }, {});
};

/**
 * Sort array by key
 */
export const sortBy = (array, key, order = 'asc') => {
  const sorted = [...array];
  sorted.sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];
    if (aVal < bVal) return order === 'asc' ? -1 : 1;
    if (aVal > bVal) return order === 'asc' ? 1 : -1;
    return 0;
  });
  return sorted;
};

/**
 * Filter array by search query
 */
export const filterBySearch = (array, searchFields, query) => {
  if (!query || query.trim() === '') return array;
  const lowerQuery = query.toLowerCase().trim();
  return array.filter(item => {
    return searchFields.some(field => {
      const value = item[field];
      if (!value) return false;
      return String(value).toLowerCase().includes(lowerQuery);
    });
  });
};

/**
 * Get query params from URL
 */
export const getQueryParams = () => {
  const params = new URLSearchParams(window.location.search);
  const result = {};
  for (const [key, value] of params) {
    result[key] = value;
  }
  return result;
};

/**
 * Set query params in URL
 */
export const setQueryParams = (params, replace = false) => {
  const url = new URL(window.location);
  Object.keys(params).forEach(key => {
    url.searchParams.set(key, params[key]);
  });
  if (replace) {
    window.history.replaceState({}, '', url);
  } else {
    window.history.pushState({}, '', url);
  }
};

/**
 * Download blob as file
 */
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Copy text to clipboard
 */
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
};

/**
 * Get browser information
 */
export const getBrowserInfo = () => {
  const ua = navigator.userAgent;
  const isChrome = ua.includes('Chrome') && !ua.includes('Edg');
  const isFirefox = ua.includes('Firefox');
  const isSafari = ua.includes('Safari') && !ua.includes('Chrome');
  const isEdge = ua.includes('Edg');
  return { isChrome, isFirefox, isSafari, isEdge };
};