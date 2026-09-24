import axiosInstance from '../api/axios';
import { ENDPOINTS } from '../api/endpoints';

export const hcpService = {
  getHCPs: async (filters = {}, pagination = {}) => {
    try {
      const params = {
        ...filters,
        page: pagination.page || 1,
        limit: pagination.limit || 20,
        search: filters.search || '',
      };
      const response = await axiosInstance.get(ENDPOINTS.HCP.LIST, { params });
      return response;
    } catch (error) {
      throw error;
    }
  },

  getHCPById: async (id) => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.HCP.DETAIL(id));
      return response;
    } catch (error) {
      throw error;
    }
  },

  searchHCPs: async (query, filters = {}) => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.HCP.SEARCH, {
        params: { q: query, ...filters },
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  createHCP: async (data) => {
    try {
      const response = await axiosInstance.post(ENDPOINTS.HCP.CREATE, data);
      return response;
    } catch (error) {
      throw error;
    }
  },

  updateHCP: async (id, data) => {
    try {
      const response = await axiosInstance.put(ENDPOINTS.HCP.UPDATE(id), data);
      return response;
    } catch (error) {
      throw error;
    }
  },

  deleteHCP: async (id) => {
    try {
      const response = await axiosInstance.delete(ENDPOINTS.HCP.DELETE(id));
      return response;
    } catch (error) {
      throw error;
    }
  },
};