import { apiClient } from './apiClient';

export const chatApi = {
  async sendMessage({
    message,
    scope = null,
    resource_id = null,
    resource_ids = null,
    conversation_id = null,
  }) {
    const payload = { message };

    if (scope && scope.mode) {
      payload.scope = scope;
      payload.resource_ids = scope.resource_ids || [];
    } else if (resource_ids !== null && Array.isArray(resource_ids)) {
      payload.scope = {
        mode: resource_ids.length > 0 ? 'selected' : 'all',
        resource_ids: resource_ids,
      };
      payload.resource_ids = resource_ids;
    } else if (resource_id) {
      payload.scope = { mode: 'selected', resource_ids: [resource_id] };
      payload.resource_id = resource_id;
    } else {
      payload.scope = { mode: 'all', resource_ids: [] };
      payload.resource_ids = [];
    }

    if (conversation_id) payload.conversation_id = conversation_id;

    const response = await apiClient.post('/chat', payload);
    return response.data;
  },
};
