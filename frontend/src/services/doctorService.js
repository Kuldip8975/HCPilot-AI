import axiosInstance from '../api/axios';
import { ENDPOINTS } from '../api/endpoints';

/**
 * API calls for the doctor-facing dashboard - only usable by a logged-in
 * user with role === 'doctor' (the backend enforces this and returns 403
 * otherwise). This is a completely separate view from the sales-rep app:
 * a doctor logs in and sees which reps have scheduled follow-ups with
 * them, their visit history, and a simple overview/analytics summary.
 */
export const doctorService = {
  getMyProfile: async () => {
    const response = await axiosInstance.get(ENDPOINTS.DOCTOR.PROFILE);
    return response;
  },

  getMyFollowUps: async (upcomingOnly = true) => {
    const response = await axiosInstance.get(ENDPOINTS.DOCTOR.FOLLOWUPS, {
      params: { upcoming_only: upcomingOnly },
    });
    return response;
  },

  getMyStats: async () => {
    const response = await axiosInstance.get(ENDPOINTS.DOCTOR.STATS);
    return response;
  },

  getMyHistory: async (limit = 50) => {
    const response = await axiosInstance.get(ENDPOINTS.DOCTOR.HISTORY, {
      params: { limit },
    });
    return response;
  },

  getMyAnalytics: async (days = 30) => {
    const response = await axiosInstance.get(ENDPOINTS.DOCTOR.ANALYTICS, {
      params: { days },
    });
    return response;
  },
};

export default doctorService;