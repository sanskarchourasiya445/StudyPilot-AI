import { apiClient } from './apiClient';

function isValidId(id) {
  return id && id !== 'undefined' && id !== 'null' && String(id).trim().length > 0;
}

export const conversationApi = {
  async getConversations() {
    const response = await apiClient.get('/conversations');
    return response.data;
  },

  async getConversation(id) {
    if (!isValidId(id)) return null;
    const response = await apiClient.get(`/conversations/${id}`);
    return response.data;
  },

  async getMessages(id) {
    if (!isValidId(id)) return [];
    const response = await apiClient.get(`/conversations/${id}/messages`);
    return response.data;
  },

  async deleteConversation(id) {
    if (!isValidId(id)) return null;
    const response = await apiClient.delete(`/conversations/${id}`);
    return response.data;
  },
};
