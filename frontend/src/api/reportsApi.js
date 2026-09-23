import { apiClient, API_BASE_URL } from './client';

export const reportsApi = {
  getReports: async (params = {}) => {
    return apiClient.get('/reports', { params });
  },

  getReportById: async (id) => {
    return apiClient.get(`/reports/${id}`);
  },

  createReport: async (reportData) => {
    return apiClient.post('/reports', reportData);
  },

  updateReport: async (id, reportData) => {
    return apiClient.put(`/reports/${id}`, reportData);
  },

  submitReview: async (id, reviewData) => {
    return apiClient.post(`/reports/${id}/review`, reviewData);
  },

  getReviewHistory: async (id) => {
    return apiClient.get(`/reports/${id}/review`);
  },

  analyzeReport: async (id) => {
    return apiClient.post(`/reports/${id}/analyze`);
  },

  getAnalysis: async (id) => {
    return apiClient.get(`/reports/${id}/analysis`);
  },

  uploadAttachments: async (reportId, files) => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    return apiClient.post(`/reports/${reportId}/attachments`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  getAttachments: async (reportId) => {
    return apiClient.get(`/reports/${reportId}/attachments`);
  },

  getAttachmentDownloadUrl: (attachmentId) => {
    return `${API_BASE_URL}/attachments/${attachmentId}/download`;
  },

  getAttachmentPreviewUrl: (attachmentId) => {
    return `${API_BASE_URL}/attachments/${attachmentId}/preview`;
  },

  deleteAttachment: async (attachmentId) => {
    return apiClient.delete(`/attachments/${attachmentId}`);
  },
};

