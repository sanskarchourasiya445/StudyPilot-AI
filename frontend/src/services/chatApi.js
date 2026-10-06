import { apiClient } from './apiClient';

function normalizeQuery(text) {
  if (!text || typeof text !== 'string') return text;
  let q = text.trim();
  // Normalize common technical compound terms and frequent student typos
  q = q.replace(/\bno[\s-]+sql\b/gi, 'NoSQL');
  q = q.replace(/\bdifferenciate\b/gi, 'differentiate');
  return q;
}

export const chatApi = {
  async sendMessage({
    message,
    scope = null,
    resource_id = null,
    resource_ids = null,
    conversation_id = null,
  }) {
    const payload = { message: normalizeQuery(message) };

    if (scope && scope.mode) {
      payload.scope = scope;
      payload.resource_ids = scope.resource_ids || [];
      if (scope.mode === 'selected' && payload.resource_ids.length === 1) {
        payload.resource_id = payload.resource_ids[0];
      }
    } else if (resource_ids !== null && Array.isArray(resource_ids)) {
      payload.scope = {
        mode: resource_ids.length > 0 ? 'selected' : 'all',
        resource_ids: resource_ids,
      };
      payload.resource_ids = resource_ids;
      if (resource_ids.length === 1) {
        payload.resource_id = resource_ids[0];
      }
    } else if (resource_id) {
      payload.scope = { mode: 'selected', resource_ids: [resource_id] };
      payload.resource_id = resource_id;
      payload.resource_ids = [resource_id];
    } else {
      payload.scope = { mode: 'all', resource_ids: [] };
      payload.resource_ids = [];
    }

    if (conversation_id) payload.conversation_id = conversation_id;

    const response = await apiClient.post('/chat', payload);
    return response.data;
  },
};
