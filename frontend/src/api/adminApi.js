import { apiClient } from './client';

export const adminApi = {
  getUsers: async (params = {}) => {
    return apiClient.get('/admin/users', { params });
  },

  updateUser: async (userId, userData) => {
    return apiClient.put(`/admin/users/${userId}`, userData);
  },

  getAuditLogs: async (params = {}) => {
    return apiClient.get('/admin/audit-logs', { params });
  },
};
