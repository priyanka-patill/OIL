import React, { useState } from 'react';
import { TrendingUp, BarChart2, Table, Calendar, Info } from 'lucide-react';

export const AnalyticsTrendsSection = ({ trendData, bdiTrendData, isLoading }) => {
  const [viewMode, setViewMode] = useState('chart'); // 'chart' | 'table'
  const [selectedMetric, setSelectedMetric] = useState('volume'); // 'volume' | 'sif' | 'density'

  if (isLoading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl animate-pulse h-64 flex items-center justify-center">
        <span className="text-xs text-slate-500">Loading temporal trends from backend...</span>
      </div>
    );
  }

  const trends = trendData?.trends || [];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Temporal Trend Analytics
            </h2>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Observed report volume, SIF precursor density, and barrier occurrences over time.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Metric selector buttons */}
          <div className="flex p-1 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-semibold">
            <button
              onClick={() => setSelectedMetric('volume')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                selectedMetric === 'volume'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Report Volume
            </button>
            <button
              onClick={() => setSelectedMetric('sif')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                selectedMetric === 'sif'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              SIF Precursors
            </button>
            <button
              onClick={() => setSelectedMetric('density')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                selectedMetric === 'density'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Density (%)
            </button>
          </div>

          {/* View toggle button */}
          <button
            onClick={() => setViewMode(viewMode === 'chart' ? 'table' : 'chart')}
            className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200 transition-all"
            title={viewMode === 'chart' ? 'Switch to Table View' : 'Switch to Chart View'}
          >
            {viewMode === 'chart' ? <Table className="w-4 h-4" /> : <BarChart2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {trends.length === 0 ? (
        <div className="p-8 text-center text-slate-400 space-y-2">
          <Calendar className="w-8 h-8 mx-auto text-slate-600" />
          <p className="text-xs font-semibold">No temporal trend data available for selected filters.</p>
          <p className="text-[11px] text-slate-500">
            Try expanding the date range or clearing specific site/department filters.
          </p>
        </div>
      ) : viewMode === 'chart' ? (
        /* Visual Chart View */
        <div className="space-y-3">
          <div className="h-56 w-full flex items-end justify-between gap-2 pt-6 pb-2 px-2 bg-slate-950/60 rounded-xl border border-slate-800/80">
            {trends.map((t, idx) => {
              const maxVal = Math.max(
                1,
                ...trends.map((item) =>
                  selectedMetric === 'volume'
                    ? item.total_reports
                    : selectedMetric === 'sif'
                    ? item.sif_potential_count
                    : (item.sif_precursor_density || 0) * 100
                )
              );

              const currentVal =
                selectedMetric === 'volume'
                  ? t.total_reports
                  : selectedMetric === 'sif'
                  ? t.sif_potential_count
                  : ((t.sif_precursor_density || 0) * 100);

              const heightPercent = Math.min(100, Math.max(10, (currentVal / maxVal) * 100));

              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2 group h-full justify-end">
                  <div className="relative w-full flex justify-center items-end flex-1">
                    <div
                      className={`w-full max-w-[36px] rounded-t-lg transition-all duration-300 group-hover:brightness-125 ${
                        selectedMetric === 'volume'
                          ? 'bg-blue-500/60 border-t-2 border-blue-400'
                          : selectedMetric === 'sif'
                          ? 'bg-amber-500/70 border-t-2 border-amber-400'
                          : 'bg-purple-500/70 border-t-2 border-purple-400'
                      }`}
                      style={{ height: `${heightPercent}%` }}
                    />
                    {/* Hover Tooltip */}
                    <div className="absolute bottom-full mb-2 hidden group-hover:flex flex-col items-center bg-slate-950 border border-slate-700 text-slate-200 text-[10px] p-2 rounded-lg shadow-xl z-20 whitespace-nowrap pointer-events-none">
                      <span className="font-bold text-amber-400">{t.period}</span>
                      <span>Total: {t.total_reports} reports</span>
                      <span>SIF-Potential: {t.sif_potential_count}</span>
                      <span>
                        Density:{' '}
                        {t.sif_precursor_density !== undefined
                          ? `${(t.sif_precursor_density * 100).toFixed(1)}% (${t.sif_potential_count}/${t.analyzed_reports || t.total_reports})`
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                  <span className="text-[10px] font-semibold text-slate-400 truncate max-w-[50px]">
                    {t.period}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
            <span className="flex items-center gap-1">
              <Info className="w-3.5 h-3.5 text-amber-400" />
              <span>
                {selectedMetric === 'density'
                  ? 'Density represents descriptive ratio of SIF-Potential reports to analyzed reports per period.'
                  : 'Observed empirical counts aggregated per period directly from Oil India database.'}
              </span>
            </span>
          </div>
        </div>
      ) : (
        /* Accessible Table View */
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 font-bold border-b border-slate-800 uppercase text-[10px]">
              <tr>
                <th className="p-3">Period</th>
                <th className="p-3">Total Reports</th>
                <th className="p-3">Analyzed Reports</th>
                <th className="p-3">SIF-Potential Count</th>
                <th className="p-3">Precursor Density (%)</th>
                <th className="p-3">Data Sufficiency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {trends.map((t, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-3 font-semibold text-slate-200">{t.period}</td>
                  <td className="p-3">{t.total_reports}</td>
                  <td className="p-3">{t.analyzed_reports ?? t.total_reports}</td>
                  <td className="p-3 font-bold text-amber-400">{t.sif_potential_count}</td>
                  <td className="p-3 font-bold text-purple-400">
                    {t.sif_precursor_density !== undefined
                      ? `${(t.sif_precursor_density * 100).toFixed(1)}%`
                      : 'N/A'}
                  </td>
                  <td className="p-3">
                    {(t.analyzed_reports ?? t.total_reports) < 5 ? (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        Low Sample Size
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Sufficient Data
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
