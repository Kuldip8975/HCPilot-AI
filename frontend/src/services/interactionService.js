import axiosInstance from '../api/axios';
import { ENDPOINTS } from '../api/endpoints';

export const interactionService = {
  getInteractions: async (filters = {}, pagination = {}) => {
    try {
      const params = {
        ...filters,
        page: pagination.page || 1,
        limit: pagination.limit || 20,
      };
      const response = await axiosInstance.get(ENDPOINTS.INTERACTION.LIST, { params });
      return response;
    } catch (error) {
      throw error;
    }
  },

  getInteractionById: async (id) => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.INTERACTION.DETAIL(id));
      return response;
    } catch (error) {
      throw error;
    }
  },

  createInteraction: async (data) => {
    try {
      const response = await axiosInstance.post(ENDPOINTS.INTERACTION.CREATE, data);
      return response;
    } catch (error) {
      throw error;
    }
  },

  createInteractionWithAI: async (description, hcpId, context = {}) => {
    try {
      const response = await axiosInstance.post('/api/v1/ai/chat/log-interaction', {
        description,
        hcp_id: hcpId,
        context,
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  transcribeVoice: async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      const response = await axiosInstance.post('/api/v1/ai/chat/transcribe', formData, {
        // Override the instance's default 'application/json' so the browser
        // sets the correct multipart/form-data boundary itself.
        headers: { 'Content-Type': undefined },
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  updateInteraction: async (id, data) => {
    try {
      const response = await axiosInstance.put(ENDPOINTS.INTERACTION.UPDATE(id), data);
      return response;
    } catch (error) {
      throw error;
    }
  },

  updateInteractionWithAI: async (id, description) => {
    try {
      const response = await axiosInstance.post('/api/v1/ai/chat/edit-interaction', {
        interaction_id: id,
        description,
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  deleteInteraction: async (id) => {
    try {
      const response = await axiosInstance.delete(ENDPOINTS.INTERACTION.DELETE(id));
      return response;
    } catch (error) {
      throw error;
    }
  },

  getHistory: async (filters = {}) => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.INTERACTION.HISTORY, {
        params: filters,
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  scheduleFollowup: async (interactionId, followupData) => {
    try {
      const response = await axiosInstance.post(
        ENDPOINTS.INTERACTION.FOLLOWUP(interactionId),
        followupData
      );
      return response;
    } catch (error) {
      throw error;
    }
  },
};