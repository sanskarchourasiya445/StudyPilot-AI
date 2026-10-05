import { apiClient } from './apiClient';

export const searchApi = {
  async searchResourceChunks(resourceId, query, topK = 5) {
    const response = await apiClient.post(`/resources/${resourceId}/search`, {
      query,
      top_k: topK,
    });
    return response.data;
  },
};
