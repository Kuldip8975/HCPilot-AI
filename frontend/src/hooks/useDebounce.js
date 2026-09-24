import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * useDebounce Hook
 * Debounces a value by the specified delay
 */
export const useDebounce = (value, delay = 500) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, delay]);

  return debouncedValue;
};

/**
 * useDebouncedCallback Hook
 * Debounces a callback function
 */
export const useDebouncedCallback = (callback, delay = 500) => {
  const timeoutRef = useRef(null);

  const debouncedCallback = useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedCallback;
};

export default useDebounce;