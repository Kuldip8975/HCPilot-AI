import axiosInstance from '../api/axios';
import { ENDPOINTS } from '../api/endpoints';

/**
 * Follow-up actions.
 */
export const followupService = {
  // Note: axiosInstance's response interceptor already unwraps
  // response.data, so every method below returns `response` directly
  // (not `response.data` - that was double-unwrapping and returning
  // undefined to any caller that inspected the result).

  // Lists the current user's own follow-up records. Used by
  // InteractionHistoryPage to key each interaction card's ACTUAL
  // scheduled follow-up date/status. Hits GET /api/v1/followups.
  getFollowups: async () => {
    const response = await axiosInstance.get(ENDPOINTS.FOLLOWUP.LIST);
    return response;
  },

  completeFollowup: async (followupId) => {
    const response = await axiosInstance.put(ENDPOINTS.FOLLOWUP.COMPLETE(followupId));
    return response;
  },

  // Checks whether an HCP already has a pending follow-up near the
  // requested time, WITHOUT booking anything. Called by InteractionForm
  // before logging an interaction with "Schedule follow-up" checked, so
  // a double-booked time is caught up front instead of failing after the
  // visit is already saved. Hits the backend's
  // GET /api/v1/followups/check-availability?hcp_id=...&scheduled_date=...
  checkAvailability: async (hcpId, scheduledDate) => {
    const response = await axiosInstance.get(ENDPOINTS.FOLLOWUP.CHECK_AVAILABILITY, {
      params: { hcp_id: hcpId, scheduled_date: scheduledDate },
    });
    return response;
  },

  // Actually creates the follow-up record, once availability has already
  // been confirmed. Hits POST /api/v1/followups.
  createFollowup: async (data) => {
    const response = await axiosInstance.post(ENDPOINTS.FOLLOWUP.CREATE, data);
    return response;
  },
};

export default followupService;