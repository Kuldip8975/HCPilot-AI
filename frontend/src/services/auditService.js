import axiosInstance from '../api/axios';
import { ENDPOINTS } from '../api/endpoints';

export const auditService = {
  getMyActivity: async (limit = 100) => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.AUDIT.LIST, { params: { limit } });
      return response;
    } catch (error) {
      throw error;
    }
  },
};

export default auditService;