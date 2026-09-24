import axiosInstance from '../api/axios';
import { ENDPOINTS } from '../api/endpoints';

export const analyticsService = {
  getDashboard: async (dateRange = {}) => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.ANALYTICS.DASHBOARD, {
        params: dateRange,
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  getInteractionAnalytics: async (aggregation = 'daily', dateRange = {}) => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.ANALYTICS.INTERACTIONS, {
        params: { aggregation, ...dateRange },
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  getHCPAnalytics: async (topN = 10, metric = 'interactions') => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.ANALYTICS.HCP, {
        params: { top_n: topN, metric },
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  exportReport: async (reportType, dateRange = {}, format = 'pdf') => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.ANALYTICS.EXPORT, {
        params: { type: reportType, format, ...dateRange },
        responseType: 'blob',
      });
      return response;
    } catch (error) {
      throw error;
    }
  },
};