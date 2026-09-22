import { apiClient } from './client';

export const analyticsApi = {
  // Part 3A — Foundation & Cross-Report Intelligence
  getRecurringPatterns: (params) =>
    apiClient.get('/api/analytics/patterns', { params }),

  getPatternById: (patternId) =>
    apiClient.get(`/api/analytics/patterns/${patternId}`),

  getRelatedReports: (reportId, params) =>
    apiClient.get(`/api/analytics/related-reports/${reportId}`, { params }),

  getDuplicates: () =>
    apiClient.get('/api/analytics/duplicates'),

  getCorrelations: (params) =>
    apiClient.get('/api/analytics/correlation', { params }),

  // Part 3B — SIF Precursor Density, Trends & Hotspots
  getSifDensity: (params) =>
    apiClient.get('/api/analytics/density', { params }),

  getDimensionAnalytics: (dimension, params) =>
    apiClient.get(`/api/analytics/${dimension}`, { params }),

  getTrends: (params) =>
    apiClient.get('/api/analytics/trends', { params }),

  getHotspots: (params) =>
    apiClient.get('/api/analytics/hotspots', { params }),

  // Part 3C — Barrier Intelligence & BDI
  getBarrierAnalytics: (params) =>
    apiClient.get('/api/analytics/barriers', { params }),

  getBarrierDetail: (barrierCategory, params) =>
    apiClient.get(
      `/api/analytics/barriers/${encodeURIComponent(barrierCategory)}`,
      { params }
    ),

  getBdi: (params) =>
    apiClient.get('/api/analytics/bdi', { params }),

  getBdiTrends: (params) =>
    apiClient.get('/api/analytics/bdi/trends', { params }),

  // Part 3D — Potential Risk Escalation & Analytical Prioritization
  getEscalation: (params) =>
    apiClient.get('/api/analytics/escalation', { params }),

  getEscalationDetail: (entityType, entityId, params) =>
    apiClient.get(
      `/api/analytics/escalation/${entityType}/${encodeURIComponent(entityId)}`,
      { params }
    ),

  getPriorities: (params) =>
    apiClient.get('/api/analytics/priorities', { params }),
};
