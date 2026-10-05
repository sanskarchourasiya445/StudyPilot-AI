import { apiClient } from './apiClient';

export const resourceApi = {
  async getResources() {
    const response = await apiClient.get('/resources');
    return response.data;
  },

  async getResource(resourceId) {
    const response = await apiClient.get(`/resources/${resourceId}`);
    return response.data;
  },

  async uploadPdf(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/resources/pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async addYoutube(url) {
    const response = await apiClient.post('/resources/youtube', { url });
    return response.data;
  },

  async deleteResource(resourceId) {
    const response = await apiClient.delete(`/resources/${resourceId}`);
    return response.data;
  },
};
