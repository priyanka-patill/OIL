import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Building2, Sparkles, RefreshCw, AlertCircle } from 'lucide-react';

import { analyticsApi } from '../api/analyticsApi';
import { reportsApi } from '../api/reportsApi';

import { AnalyticsFilterBar } from '../components/analytics/AnalyticsFilterBar';
import { AnalyticsKpiGrid } from '../components/analytics/AnalyticsKpiGrid';
import { AnalyticsTrendsSection } from '../components/analytics/AnalyticsTrendsSection';
import { AnalyticsHotspotsSection } from '../components/analytics/AnalyticsHotspotsSection';
import { AnalyticsPatternsSection } from '../components/analytics/AnalyticsPatternsSection';
import { AnalyticsBarrierSection } from '../components/analytics/AnalyticsBarrierSection';
import { AnalyticsEscalationSection } from '../components/analytics/AnalyticsEscalationSection';
import { AnalyticsDataQualitySection } from '../components/analytics/AnalyticsDataQualitySection';

export const SafetyIntelligencePage = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Initial filter state from URL query parameters
  const [filters, setFilters] = useState({
    date_preset: searchParams.get('date_preset') || '90d',
    start_date: searchParams.get('start_date') || '',
    end_date: searchParams.get('end_date') || '',
    site: searchParams.get('site') || '',
    department: searchParams.get('department') || '',
    work_type: searchParams.get('work_type') || '',
    barrier: searchParams.get('barrier') || '',
    sif_class: searchParams.get('sif_class') || '',
  });

  // State for all API responses
  const [densityData, setDensityData] = useState(null);
  const [patternsData, setPatternsData] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [barrierData, setBarrierData] = useState(null);
  const [bdiData, setBdiData] = useState(null);
  const [bdiTrendData, setBdiTrendData] = useState(null);
  const [escalationData, setEscalationData] = useState(null);
  const [priorityData, setPriorityData] = useState(null);
  const [duplicatesData, setDuplicatesData] = useState(null);
  const [reportsData, setReportsData] = useState(null);

  const [isLoading, setIsLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState(null);
  const [error, setError] = useState(null);

  // Sync state to URL search params
  const updateFilters = (newFilters) => {
    setFilters(newFilters);
    const params = {};
    Object.keys(newFilters).forEach((k) => {
      if (newFilters[k]) params[k] = newFilters[k];
    });
    setSearchParams(params, { replace: true });
  };

  const handleResetFilters = () => {
    const defaultFilters = {
      date_preset: '90d',
      start_date: '',
      end_date: '',
      site: '',
      department: '',
      work_type: '',
      barrier: '',
      sif_class: '',
    };
    setFilters(defaultFilters);
    setSearchParams({});
  };

  // Main data fetch function using backend analytics APIs
  const fetchAllAnalytics = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    // Build backend query params
    const apiParams = {};
    if (filters.site) apiParams.site = filters.site;
    if (filters.department) apiParams.department = filters.department;
    if (filters.work_type) apiParams.work_type = filters.work_type;
    if (filters.barrier) apiParams.barrier = filters.barrier;
    if (filters.date_preset && filters.date_preset !== 'custom') {
      apiParams.date_preset = filters.date_preset;
    }
    if (filters.start_date) apiParams.start_date = filters.start_date;
    if (filters.end_date) apiParams.end_date = filters.end_date;

    try {
      const [
        densityRes,
        patternsRes,
        trendsRes,
        barrierRes,
        bdiRes,
        bdiTrendsRes,
        escalationRes,
        priorityRes,
        duplicatesRes,
        reportsRes,
      ] = await Promise.all([
        analyticsApi.getSifDensity(apiParams).catch(() => ({ data: null })),
        analyticsApi.getRecurringPatterns(apiParams).catch(() => ({ data: null })),
        analyticsApi.getTrends({ ...apiParams, period: 'month' }).catch(() => ({ data: null })),
        analyticsApi.getBarrierAnalytics(apiParams).catch(() => ({ data: null })),
        analyticsApi.getBdi(apiParams).catch(() => ({ data: null })),
        analyticsApi.getBdiTrends({ ...apiParams, period: 'month' }).catch(() => ({ data: null })),
        analyticsApi.getEscalation({ ...apiParams, dimension: 'equipment_id' }).catch(() => ({ data: null })),
        analyticsApi.getPriorities({ ...apiParams, dimension: 'equipment_id' }).catch(() => ({ data: null })),
        analyticsApi.getDuplicates().catch(() => ({ data: null })),
        reportsApi.getReports({ limit: 100 }).catch(() => ({ data: null })),
      ]);

      setDensityData(densityRes?.data || null);
      setPatternsData(patternsRes?.data || null);
      setTrendData(trendsRes?.data || null);
      setBarrierData(barrierRes?.data || null);
      setBdiData(bdiRes?.data || null);
      setBdiTrendData(bdiTrendsRes?.data || null);
      setEscalationData(escalationRes?.data || null);
      setPriorityData(priorityRes?.data || null);
      setDuplicatesData(duplicatesRes?.data || null);
      setReportsData(reportsRes?.data || null);

      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Error loading Safety Intelligence dashboard data:', err);
      setError('Failed to fetch backend analytics. Please check server connectivity.');
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchAllAnalytics();
  }, [fetchAllAnalytics]);

  return (
    <div className="space-y-6">
      {/* Banner Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-amber-950/50 border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center gap-2 text-xs text-amber-400 font-semibold uppercase tracking-wider mb-1">
            <Building2 className="w-4 h-4" />
            <span>Oil India Limited — Industrial Safety Intelligence</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <span>Safety Intelligence Dashboard</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold uppercase">
              safety_intelligence_v1
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Unified, auditable, filterable intelligence connecting reports, SIF precursor density, barrier degradation, and risk escalation.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {lastRefreshed && (
            <span className="text-[11px] text-slate-400">
              Refreshed: <strong className="text-slate-200">{lastRefreshed}</strong>
            </span>
          )}
          <button
            onClick={fetchAllAnalytics}
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-200 bg-slate-800 hover:bg-slate-700 transition-all border border-slate-700 disabled:opacity-50 shadow"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Global Filter Bar */}
      <AnalyticsFilterBar
        filters={filters}
        onFilterChange={updateFilters}
        onReset={handleResetFilters}
      />

      {/* KPI Cards Grid */}
      <AnalyticsKpiGrid
        densityData={densityData}
        patternsData={patternsData}
        barrierData={barrierData}
        escalationData={escalationData}
        reportsData={reportsData}
        isLoading={isLoading}
      />

      {/* Temporal Trend Analytics */}
      <AnalyticsTrendsSection
        trendData={trendData}
        bdiTrendData={bdiTrendData}
        isLoading={isLoading}
      />

      {/* Dimensional Hotspots & Concentration */}
      <AnalyticsHotspotsSection
        filters={filters}
        isLoading={isLoading}
      />

      {/* Recurring Safety Patterns */}
      <AnalyticsPatternsSection
        patternsData={patternsData}
        isLoading={isLoading}
      />

      {/* Barrier Intelligence & BDI */}
      <AnalyticsBarrierSection
        barrierData={barrierData}
        bdiData={bdiData}
        filters={filters}
        isLoading={isLoading}
      />

      {/* Potential Risk Escalation & Analytical Priority */}
      <AnalyticsEscalationSection
        escalationData={escalationData}
        priorityData={priorityData}
        filters={filters}
        isLoading={isLoading}
      />

      {/* Data Quality & Completeness Intelligence */}
      <AnalyticsDataQualitySection
        densityData={densityData}
        duplicatesData={duplicatesData}
        reportsData={reportsData}
        isLoading={isLoading}
      />
    </div>
  );
};
