import axiosInstance from '../api/axios';
import { ENDPOINTS } from '../api/endpoints';

export const priorityService = {
  getWeeklyPriorities: async () => {
    const response = await axiosInstance.get(ENDPOINTS.PRIORITY.WEEKLY);
    return response;
  },

  getDayPlan: async ({ timeBudgetMinutes, latitude, longitude, excludeHcpIds }) => {
    const response = await axiosInstance.post(ENDPOINTS.PRIORITY.DAY_PLAN, {
      time_budget_minutes: timeBudgetMinutes,
      ...(latitude != null && longitude != null ? { latitude, longitude } : {}),
      ...(excludeHcpIds && excludeHcpIds.length > 0 ? { exclude_hcp_ids: excludeHcpIds } : {}),
    });
    return response;
  },

  markDayPlanVisited: async (hcpId) => {
    const response = await axiosInstance.post(ENDPOINTS.PRIORITY.MARK_VISITED, { hcp_id: hcpId });
    return response;
  },

  getDayPlanAnalytics: async () => {
    const response = await axiosInstance.get(ENDPOINTS.PRIORITY.ANALYTICS);
    return response;
  },
};