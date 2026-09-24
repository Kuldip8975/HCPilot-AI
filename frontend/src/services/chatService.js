import axiosInstance from '../api/axios';
import { ENDPOINTS } from '../api/endpoints';

export const chatService = {
  sendMessage: async (message, sessionId, context = {}) => {
    try {
      const response = await axiosInstance.post(ENDPOINTS.CHAT.SEND, {
        message,
        session_id: sessionId,
        context,
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  sendMessageStream: (message, sessionId, context = {}, onMessage, onError, onComplete) => {
    const url = new URL(ENDPOINTS.CHAT.STREAM, axiosInstance.defaults.baseURL);
    const token = localStorage.getItem('authToken');
    
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
    
    const body = JSON.stringify({ message, session_id: sessionId, context });
    
    fetch(url, { method: 'POST', headers, body })
      .then((response) => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        function readStream() {
          reader.read().then(({ done, value }) => {
            if (done) { if (onComplete) onComplete(); return; }
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.error) { if (onError) onError(data.error); }
                  else if (data.content) { if (onMessage) onMessage(data.content); }
                } catch (e) { /* Skip invalid JSON */ }
              }
            }
            readStream();
          });
        }
        readStream();
      })
      .catch((error) => { if (onError) onError(error); });
  },

  getSessions: async () => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.CHAT.SESSIONS);
      return response;
    } catch (error) {
      throw error;
    }
  },

  getSession: async (sessionId) => {
    try {
      const response = await axiosInstance.get(ENDPOINTS.CHAT.SESSION_DETAIL(sessionId));
      return response;
    } catch (error) {
      throw error;
    }
  },

  deleteSession: async (sessionId) => {
    try {
      const response = await axiosInstance.delete(ENDPOINTS.CHAT.SESSION_DELETE(sessionId));
      return response;
    } catch (error) {
      throw error;
    }
  },
};