import { apiClient } from './client';

export const authApi = {
  login: async (email, password) => {
    return apiClient.post('/api/auth/login', { email, password });
  },

  signup: async (userData) => {
    return apiClient.post('/api/auth/signup', userData);
  },

  logout: async () => {
    try {
      return await apiClient.post('/api/auth/logout');
    } catch {
      // Ignore logout API errors
    } finally {
      localStorage.removeItem('oil_auth_token');
      localStorage.removeItem('oil_user_data');
    }
  },

  getMe: async () => {
    return apiClient.get('/api/auth/me');
  },
};
