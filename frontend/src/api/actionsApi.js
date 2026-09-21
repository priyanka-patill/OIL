import { apiClient } from './client';

export const actionsApi = {
  // Create operational action from HSE-approved/modified intervention
  createAction: (payload) =>
    apiClient.post('/actions', payload),

  // List all assigned actions with backend filters (Manager view)
  getAssignedActions: (params) =>
    apiClient.get('/actions', { params }),

  // List actions assigned specifically to authenticated user (My Actions)
  getMyActions: (params) =>
    apiClient.get('/actions/my', { params }),

  // Get action detail by ID
  getActionById: (id) =>
    apiClient.get(`/actions/${id}`),

  // Update action status lifecycle
  updateStatus: (id, payload) =>
    apiClient.patch(`/actions/${id}/status`, payload),

  // Reassign action to user & department
  reassign: (id, payload) =>
    apiClient.patch(`/actions/${id}/assign`, payload),

  // Update action priority
  updatePriority: (id, payload) =>
    apiClient.patch(`/actions/${id}/priority`, payload),

  // Update action due date
  updateDueDate: (id, payload) =>
    apiClient.patch(`/actions/${id}/due-date`, payload),

  // Add comment to action
  addComment: (id, payload) =>
    apiClient.post(`/actions/${id}/comments`, payload),

  // Part 4D — SLA Monitoring & Escalation API Methods
  getSlaSummary: () =>
    apiClient.get('/actions/sla/summary'),

  evaluateSla: () =>
    apiClient.post('/actions/sla/evaluate'),

  getSlaDetail: (id) =>
    apiClient.get(`/actions/${id}/sla`),

  getSlaHistory: (id) =>
    apiClient.get(`/actions/${id}/sla/history`),

  // Part 4E — Completion, HSE Verification & Impact Tracking API Methods
  completeAction: (id, payload) =>
    apiClient.post(`/actions/${id}/complete`, payload),

  verifyAction: (id, payload) =>
    apiClient.post(`/actions/${id}/verify`, payload),

  reopenAction: (id, payload) =>
    apiClient.post(`/actions/${id}/reopen`, payload),

  addEvidence: (id, payload) =>
    apiClient.post(`/actions/${id}/evidence`, payload),

  getCompletionHistory: (id) =>
    apiClient.get(`/actions/${id}/completion-history`),

  getImpactAnalysis: (id) =>
    apiClient.get(`/actions/${id}/impact`),

  recalculateImpact: (id, params) =>
    apiClient.post(`/actions/${id}/impact/recalculate`, null, { params }),

  // Part 4F — HSE Action Center & Integration API Methods
  getActionCenterSummary: (params) =>
    apiClient.get('/action-center/summary', { params }),

  getActionCenterSections: (params) =>
    apiClient.get('/action-center/sections', { params }),
};
