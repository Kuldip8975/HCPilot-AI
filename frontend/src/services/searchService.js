import axiosInstance from '../api/axios';
import { ENDPOINTS } from '../api/endpoints';

/**
 * AI-powered search over the logged-in rep's own past interactions (RAG).
 * Backend: POST /api/v1/search/ask
 *   - Builds a fresh TF-IDF index from this rep's own interaction rows
 *     (topics/summary/notes), retrieves the most relevant ones, and asks
 *     the LLM to answer grounded only in those matches.
 *   - Data is scoped to the logged-in user (hcp_id filter is optional,
 *     narrows the search to one doctor).
 */
export const searchService = {
  /**
   * @param {string} question - natural-language question, e.g.
   *   "What did Dr. Kuldip say about the clinical trial last month?"
   * @param {string|null} hcpId - optional HCP UUID to narrow the search
   *   to a single doctor's interactions only.
   */
  askAboutInteractions: async (question, hcpId = null) => {
    try {
      const response = await axiosInstance.post(ENDPOINTS.SEARCH.ASK, {
        question,
        hcp_id: hcpId || null,
      });
      return response;
    } catch (error) {
      throw error;
    }
  },
};