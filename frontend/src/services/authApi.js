import { apiClient } from './apiClient';

export const authApi = {
  async register(data) {
    const response = await apiClient.post('/auth/register', {
      email: data.email,
      password: data.password,
      name: data.name,
    });
    return response.data;
  },

  async login(data) {
    const response = await apiClient.post('/auth/login', {
      email: data.email,
      password: data.password,
    });
    return response.data;
  },

  async getMe() {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};
