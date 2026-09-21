import { apiClient } from './client';

export const interventionsApi = {
  // Generate intervention recommendation for a report
  generateIntervention: (reportId) =>
    apiClient.post('/interventions/generate', { report_id: reportId }),

  // List interventions with filters & pagination
  getInterventions: (params) =>
    apiClient.get('/interventions', { params }),

  // Get intervention detail by ID
  getInterventionById: (id) =>
    apiClient.get(`/interventions/${id}`),

  // Get interventions for a specific report
  getInterventionsForReport: (reportId) =>
    apiClient.get(`/interventions/report/${reportId}`),

  // Submit Part 4B HSE Review (ACCEPT, MODIFY, REJECT)
  submitReview: (interventionId, payload) =>
    apiClient.post(`/interventions/${interventionId}/review`, payload),

  // Get review audit history for an intervention
  getReviewHistory: (interventionId) =>
    apiClient.get(`/interventions/${interventionId}/review/history`),
};
