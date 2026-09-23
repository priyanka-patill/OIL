import { apiClient } from './client';

export const analyticsApi = {
  // Part 3A — Foundation & Cross-Report Intelligence
  getRecurringPatterns: (params) =>
    apiClient.get('/analytics/patterns', { params }),

  getPatternById: (patternId) =>
    apiClient.get(`/analytics/patterns/${patternId}`),

  getRelatedReports: (reportId, params) =>
    apiClient.get(`/analytics/related-reports/${reportId}`, { params }),

  getDuplicates: () =>
    apiClient.get('/analytics/duplicates'),

  getCorrelations: (params) =>
    apiClient.get('/analytics/correlation', { params }),

  // Part 3B — SIF Precursor Density, Trends & Hotspots
  getSifDensity: (params) =>
    apiClient.get('/analytics/density', { params }),

  getDimensionAnalytics: (dimension, params) =>
    apiClient.get(`/analytics/${dimension}`, { params }),

  getTrends: (params) =>
    apiClient.get('/analytics/trends', { params }),

  getHotspots: (params) =>
    apiClient.get('/analytics/hotspots', { params }),

  // Part 3C — Barrier Intelligence & BDI
  getBarrierAnalytics: (params) =>
    apiClient.get('/analytics/barriers', { params }),

  getBarrierDetail: (barrierCategory, params) =>
    apiClient.get(
      `/analytics/barriers/${encodeURIComponent(barrierCategory)}`,
      { params }
    ),

  getBdi: (params) =>
    apiClient.get('/analytics/bdi', { params }),

  getBdiTrends: (params) =>
    apiClient.get('/analytics/bdi/trends', { params }),

  // Part 3D — Potential Risk Escalation & Analytical Prioritization
  getEscalation: (params) =>
    apiClient.get('/analytics/escalation', { params }),

  getEscalationDetail: (entityType, entityId, params) =>
    apiClient.get(
      `/analytics/escalation/${entityType}/${encodeURIComponent(entityId)}`,
      { params }
    ),

  getPriorities: (params) =>
    apiClient.get('/analytics/priorities', { params }),
};

