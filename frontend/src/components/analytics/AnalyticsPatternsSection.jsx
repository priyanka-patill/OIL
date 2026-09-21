import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Repeat, FileText, ArrowRight, X, ExternalLink, ShieldAlert, Calendar } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';

export const AnalyticsPatternsSection = ({ patternsData, isLoading }) => {
  const [selectedPattern, setSelectedPattern] = useState(null);

  if (isLoading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl animate-pulse h-48 flex items-center justify-center">
        <span className="text-xs text-slate-500">Extracting recurring safety patterns from analytics engine...</span>
      </div>
    );
  }

  const patterns = patternsData?.patterns || [];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Repeat className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Recurring Safety Patterns
            </h2>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Cross-report pattern mining identifying repeated factor combinations.
          </p>
        </div>
        <span className="text-xs font-semibold text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-3 py-1 rounded-xl">
          {patterns.length} Patterns Identified
        </span>
      </div>

      {patterns.length === 0 ? (
        <div className="p-8 text-center text-slate-400 space-y-2">
          <Repeat className="w-8 h-8 mx-auto text-slate-600" />
          <p className="text-xs font-semibold">No recurring patterns identified for selected filters.</p>
          <p className="text-[11px] text-slate-500">
            Patterns require at least 2 distinct observations matching a common factor set.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {patterns.map((p) => {
            const occurrences = p.occurrence_count || p.support_count || (p.contributing_reports?.length ?? 0);
            const sifCount = p.sif_potential_count || p.sif_count || 0;
            const openIssues = p.unresolved_count || p.open_issues || 0;
            const latestDate = p.latest_observed_date || p.latest_date || 'N/A';

            return (
              <div
                key={p.pattern_id}
                className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between space-y-4"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      ID: {p.pattern_id}
                    </span>
                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>{latestDate}</span>
                    </span>
                  </div>

                  <h3 className="text-xs font-bold text-slate-100 line-clamp-2">
                    {p.pattern_description || p.combination_name || 'Multi-factor Safety Pattern'}
                  </h3>

                  {/* Combination tags */}
                  <div className="flex flex-wrap gap-1 pt-1">
                    {p.work_type && (
                      <span className="text-[9px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">
                        {p.work_type}
                      </span>
                    )}
                    {p.equipment_id && (
                      <span className="text-[9px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">
                        {p.equipment_id}
                      </span>
                    )}
                    {p.barrier_category && (
                      <span className="text-[9px] bg-amber-500/10 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/20">
                        {p.barrier_category}
                      </span>
                    )}
                    {p.location && (
                      <span className="text-[9px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">
                        {p.location}
                      </span>
                    )}
                  </div>
                </div>

                {/* Metrics Footer */}
                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                  <div className="space-y-0.5">
                    <p className="text-slate-400 text-[10px]">
                      Occurrences: <strong className="text-slate-100">{occurrences}</strong>
                    </p>
                    <p className="text-slate-400 text-[10px]">
                      SIF-Potential: <strong className="text-amber-400">{sifCount}</strong>
                    </p>
                  </div>

                  <button
                    onClick={() => setSelectedPattern(p)}
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-cyan-400 hover:text-cyan-300 px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/20 transition-all"
                  >
                    <span>View Reports</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Drill-down Modal for Contributing Reports */}
      {selectedPattern && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <Repeat className="w-4 h-4 text-cyan-400" />
                  <span>Contributing Reports — Pattern {selectedPattern.pattern_id}</span>
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {selectedPattern.pattern_description || selectedPattern.combination_name}
                </p>
              </div>
              <button
                onClick={() => setSelectedPattern(null)}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-100 transition-all"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto flex-1 space-y-3">
              {(!selectedPattern.contributing_reports || selectedPattern.contributing_reports.length === 0) ? (
                <p className="text-xs text-slate-400 text-center py-6">
                  No individual report list payload available for this pattern.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-950/80 text-slate-400 font-bold border-b border-slate-800 uppercase text-[10px]">
                      <tr>
                        <th className="p-3">Report Number</th>
                        <th className="p-3">Date</th>
                        <th className="p-3">Site / Unit</th>
                        <th className="p-3">Activity</th>
                        <th className="p-3">SIF Classification</th>
                        <th className="p-3">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {selectedPattern.contributing_reports.map((rep, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                          <td className="p-3 font-bold text-amber-400">
                            {rep.report_number || `#${rep.id || rep}`}
                          </td>
                          <td className="p-3 text-slate-400">{rep.date || 'N/A'}</td>
                          <td className="p-3 truncate max-w-[140px]">{rep.site || 'N/A'}</td>
                          <td className="p-3 truncate max-w-[140px]">{rep.work_type || rep.activity || 'N/A'}</td>
                          <td className="p-3">
                            {rep.is_sif_potential || rep.sif_potential ? (
                              <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold">
                                SIF-Potential
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 font-medium">
                                Non-SIF
                              </span>
                            )}
                          </td>
                          <td className="p-3">
                            <Link
                              to={`/reports/${rep.id || rep}`}
                              target="_blank"
                              className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400 hover:underline"
                            >
                              <span>Inspect</span>
                              <ExternalLink className="w-3 h-3" />
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-950/40 text-right">
              <button
                onClick={() => setSelectedPattern(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-200 text-xs font-bold hover:bg-slate-700 transition-all"
              >
                Close Modal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
