import { apiClient } from './client';

export const authApi = {
  login: async (email, password) => {
    return apiClient.post('/auth/login', { email, password });
  },

  signup: async (userData) => {
    return apiClient.post('/auth/signup', userData);
  },

  logout: async () => {
    try {
      return await apiClient.post('/auth/logout');
    } catch {
      // Ignore logout API errors
    } finally {
      localStorage.removeItem('oil_auth_token');
      localStorage.removeItem('oil_user_data');
    }
  },

  getMe: async () => {
    return apiClient.get('/auth/me');
  },
};
