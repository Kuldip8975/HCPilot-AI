import axiosInstance from '../api/axios';

/**
 * Public support/FAQ chat service - powers the RAG-based widget on the
 * homepage. This calls a public endpoint (no login required), since it's
 * meant for anonymous visitors who haven't signed up yet.
 */
export const supportService = {
  /**
   * Ask the support assistant a question about the product.
   * @param {string} message
   * @returns {Promise<{success: boolean, answer: string, sources: string[]}>}
   */
  sendMessage: async (message) => {
    const response = await axiosInstance.post('/api/v1/support/chat', { message });
    return response;
  },
};

export default supportService;