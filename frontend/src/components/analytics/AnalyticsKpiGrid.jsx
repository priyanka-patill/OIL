import React from 'react';
import {
  FileText,
  Sparkles,
  ShieldAlert,
  Percent,
  Repeat,
  AlertTriangle,
  Shield,
  TrendingUp,
  Info,
  CheckCircle2,
} from 'lucide-react';

export const AnalyticsKpiGrid = ({
  densityData,
  patternsData,
  barrierData,
  escalationData,
  reportsData,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <div
            key={i}
            className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl animate-pulse h-32 flex flex-col justify-between"
          >
            <div className="h-4 bg-slate-800 rounded w-1/2" />
            <div className="h-8 bg-slate-800 rounded w-1/3" />
          </div>
        ))}
      </div>
    );
  }

  // Extract metrics from API responses safely
  const totalReports = densityData?.total_reports ?? reportsData?.total ?? 0;
  const analyzedReports = densityData?.eligible_analyzed_reports ?? 0;
  const aiSifCount = densityData?.ai_sif_potential_count ?? 0;
  const hseSifCount = densityData?.hse_sif_potential_count ?? 0;

  // Primary SIF count preference: HSE validated if available, else AI
  const effectiveSifCount = hseSifCount > 0 ? hseSifCount : aiSifCount;

  // Precursor density (descriptive ratio)
  const densityPercent = densityData?.effective_sif_precursor_density
    ? (densityData.effective_sif_precursor_density * 100).toFixed(1)
    : analyzedReports > 0
    ? ((effectiveSifCount / analyzedReports) * 100).toFixed(1)
    : '0.0';

  const patternCount = patternsData?.total_patterns_found ?? 0;
  const openActionsCount = reportsData?.open_actions ?? 0;

  // Barrier concerns: count of barriers meeting recurrence threshold
  const barrierConcernsCount = barrierData?.barriers
    ? barrierData.barriers.filter((b) => b.recurrence_count > 1).length
    : 0;

  // Potential escalation indicators count
  const escalationCount = escalationData?.summary?.escalating_entities_count ?? 0;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Total Reports */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Total Reports
            </span>
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-3xl font-extrabold text-slate-100">{totalReports}</p>
            <p className="text-[11px] text-slate-400 mt-1">Persisted backend records</p>
          </div>
        </div>

        {/* KPI 2: Analyzed Reports */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Analyzed Reports
            </span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-3xl font-extrabold text-slate-100">{analyzedReports}</p>
            <p className="text-[11px] text-slate-400 mt-1">
              {totalReports > 0 ? `${((analyzedReports / totalReports) * 100).toFixed(0)}% coverage` : 'No data'}
            </p>
          </div>
        </div>

        {/* KPI 3: SIF-Potential Reports */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider">
              SIF-Potential Reports
            </span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-amber-400">{effectiveSifCount}</span>
              <span className="text-xs text-slate-400">SIF Precursors</span>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-1">
              <span>AI: <strong className="text-amber-300">{aiSifCount}</strong></span>
              <span>•</span>
              <span>HSE: <strong className="text-emerald-400">{hseSifCount}</strong></span>
            </div>
          </div>
        </div>

        {/* KPI 4: SIF Precursor Density */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              <span>Precursor Density</span>
              <div className="group relative cursor-pointer">
                <Info className="w-3.5 h-3.5 text-slate-500" />
                <div className="absolute right-0 bottom-full mb-2 hidden group-hover:block w-56 p-2 rounded bg-slate-950 border border-slate-700 text-[10px] text-slate-300 shadow-xl z-20">
                  Descriptive ratio of SIF-Potential reports to eligible analyzed reports. Not a future probability.
                </div>
              </div>
            </span>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Percent className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-3xl font-extrabold text-slate-100">{densityPercent}%</p>
            <p className="text-[11px] text-slate-400 mt-1">
              {effectiveSifCount} SIF-Potential / {analyzedReports} analyzed
            </p>
          </div>
        </div>

        {/* KPI 5: Recurring Patterns */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Recurring Patterns
            </span>
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Repeat className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-3xl font-extrabold text-slate-100">{patternCount}</p>
            <p className="text-[11px] text-slate-400 mt-1">Cross-report pattern clusters</p>
          </div>
        </div>

        {/* KPI 6: Open Actions */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Open Actions
            </span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-3xl font-extrabold text-slate-100">{openActionsCount}</p>
            <p className="text-[11px] text-rose-400 mt-1">Action required status</p>
          </div>
        </div>

        {/* KPI 7: Recurring Barrier Concerns */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Barrier Concerns
            </span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Shield className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-3xl font-extrabold text-slate-100">{barrierConcernsCount}</p>
            <p className="text-[11px] text-amber-400 mt-1">Recurring barrier degradation</p>
          </div>
        </div>

        {/* KPI 8: Potential Escalation Indicators */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Potential Escalations
            </span>
            <div className="p-2 rounded-xl bg-orange-500/10 text-orange-400 border border-orange-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <p className="text-3xl font-extrabold text-slate-100">{escalationCount}</p>
            <p className="text-[11px] text-slate-400 mt-1">Risk escalation evidence</p>
          </div>
        </div>
      </div>
    </div>
  );
};
