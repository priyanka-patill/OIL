import React from 'react';
import { Database, CheckCircle2, AlertTriangle, FileText, Info, Sparkles } from 'lucide-react';

export const AnalyticsDataQualitySection = ({ densityData, duplicatesData, reportsData, isLoading }) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl animate-pulse h-36 flex items-center justify-center">
        <span className="text-xs text-slate-500">Checking database data quality & completeness...</span>
      </div>
    );
  }

  const totalReports = densityData?.total_reports ?? reportsData?.total ?? 0;
  const analyzedReports = densityData?.eligible_analyzed_reports ?? 0;
  const hseValidated = reportsData?.reports ? reportsData.reports.filter((r) => r.status === 'HSE_VALIDATED').length : 0;
  const duplicateGroups = duplicatesData?.total_groups || duplicatesData?.duplicate_groups?.length || 0;

  const coveragePercent = totalReports > 0 ? ((analyzedReports / totalReports) * 100).toFixed(0) : '0';

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Data Quality & Completeness Intelligence
          </h2>
        </div>
        <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-xl">
          {coveragePercent}% AI Coverage
        </span>
      </div>

      <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-[11px] text-slate-300 flex items-start gap-2">
        <Info className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <p>
          "Analytics coverage depends on report field completeness and AI/HSE review coverage. High analysis coverage does not guarantee 100% data accuracy without HSE validation."
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-[10px] font-bold text-slate-400 uppercase">Total Database Records</span>
          <p className="text-2xl font-extrabold text-slate-100 mt-1">{totalReports}</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-[10px] font-bold text-indigo-400 uppercase">AI Analyzed Reports</span>
          <p className="text-2xl font-extrabold text-indigo-400 mt-1">{analyzedReports}</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-[10px] font-bold text-emerald-400 uppercase">HSE Validated Reports</span>
          <p className="text-2xl font-extrabold text-emerald-400 mt-1">{hseValidated}</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-[10px] font-bold text-amber-400 uppercase">Duplicate Groups</span>
          <p className="text-2xl font-extrabold text-amber-400 mt-1">{duplicateGroups}</p>
        </div>
      </div>
    </div>
  );
};
