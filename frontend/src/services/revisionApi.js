import { apiClient } from './apiClient';

export const revisionApi = {
  getSchedule: async () => {
    const response = await apiClient.get('/revision');
    return response.data;
  },

  getDue: async () => {
    const response = await apiClient.get('/revision/due');
    return response.data;
  },

  getUpcoming: async (limit = 10) => {
    const response = await apiClient.get('/revision/upcoming', {
      params: { limit },
    });
    return response.data;
  },
};
