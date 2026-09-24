import { format, formatDistanceToNow, parseISO } from 'date-fns';
import { DATE_FORMATS } from './constants';

/**
 * Format a date string to display format
 */
export const formatDate = (date, formatStr = DATE_FORMATS.DISPLAY) => {
  if (!date) return '-';
  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date;
    return format(parsedDate, formatStr);
  } catch (error) {
    return '-';
  }
};

/**
 * Format a date to relative time (e.g., "2 hours ago")
 */
export const formatRelativeTime = (date) => {
  if (!date) return '-';
  try {
    const parsedDate = typeof date === 'string' ? parseISO(date) : date;
    return formatDistanceToNow(parsedDate, { addSuffix: true });
  } catch (error) {
    return '-';
  }
};

/**
 * Format a number with commas
 */
export const formatNumber = (num) => {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('en-US').format(num);
};

/**
 * Format a percentage
 */
export const formatPercentage = (num, decimals = 1) => {
  if (num === null || num === undefined) return '-';
  return `${num.toFixed(decimals)}%`;
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text, maxLength = 100) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * Capitalize first letter
 */
export const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

/**
 * Format phone number
 */
export const formatPhone = (phone) => {
  if (!phone) return '-';
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  return phone;
};

/**
 * Get initials from name
 */
export const getInitials = (name) => {
  if (!name) return '';
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
};

/**
 * Truncate wallet address
 */
export const truncateAddress = (address, start = 6, end = 4) => {
  if (!address) return '';
  if (address.length <= start + end) return address;
  return `${address.slice(0, start)}...${address.slice(-end)}`;
};