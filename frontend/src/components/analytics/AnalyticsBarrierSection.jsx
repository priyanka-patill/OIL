import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Shield, Info, ArrowRight, X, ExternalLink, AlertCircle, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { analyticsApi } from '../../api/analyticsApi';

export const AnalyticsBarrierSection = ({ barrierData, bdiData, filters, isLoading }) => {
  const [selectedBarrier, setSelectedBarrier] = useState(null);
  const [barrierDetail, setBarrierDetail] = useState(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  if (isLoading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl animate-pulse h-48 flex items-center justify-center">
        <span className="text-xs text-slate-500">Loading Barrier Intelligence & Barrier Degradation Index scores...</span>
      </div>
    );
  }

  const barriers = barrierData?.barriers || [];
  const bdiScores = bdiData?.bdi_scores || {};

  const handleOpenDetail = async (barrierCategory) => {
    setSelectedBarrier(barrierCategory);
    setIsDetailLoading(true);
    try {
      const res = await analyticsApi.getBarrierDetail(barrierCategory, filters);
      setBarrierDetail(res?.data || null);
    } catch (err) {
      console.error('Failed to load barrier detail:', err);
      setBarrierDetail(null);
    } finally {
      setIsDetailLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Barrier Intelligence & Degradation Index (BDI)
            </h2>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Systematic tracking of barrier recurrence, persistence, and evidence-backed degradation indicators.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-xl">
            Methodology: BDI_v1
          </span>
        </div>
      </div>

      {/* Methodology Disclaimer */}
      <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300 flex items-start gap-2">
        <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          BDI (Barrier Degradation Index) measures structural barrier health on a scale of 0–100 based on occurrence frequency, SIF risk involvement, and unresolved action ratio.
        </div>
      </div>

      {barriers.length === 0 ? (
        <div className="p-8 text-center text-slate-400 space-y-2">
          <Shield className="w-8 h-8 mx-auto text-slate-600" />
          <p className="text-xs font-semibold">No barrier observations recorded for active filters.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 font-bold border-b border-slate-800 uppercase text-[10px]">
              <tr>
                <th className="p-3">Safety Barrier Category</th>
                <th className="p-3">Occurrences</th>
                <th className="p-3">Unique Reports</th>
                <th className="p-3">SIF Association</th>
                <th className="p-3">Unresolved Count</th>
                <th className="p-3">BDI Score (0-100)</th>
                <th className="p-3">Status / Trend</th>
                <th className="p-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {barriers.map((b, idx) => {
                const bdiInfo = bdiScores[b.barrier_category] || {};
                const bdiScore = bdiInfo.bdi_score ?? b.bdi_score;
                const sifCount = b.sif_potential_count || b.sif_count || 0;
                const unresolved = b.unresolved_count || b.open_count || 0;

                return (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 font-semibold text-slate-100 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />
                      <span>{b.barrier_category}</span>
                    </td>
                    <td className="p-3 font-bold">{b.recurrence_count || b.occurrence_count}</td>
                    <td className="p-3">{b.unique_report_count || b.reports_count}</td>
                    <td className="p-3 font-bold text-amber-400">{sifCount}</td>
                    <td className="p-3 text-rose-400 font-bold">{unresolved}</td>
                    <td className="p-3 font-extrabold text-amber-400">
                      {bdiScore !== undefined && bdiScore !== null ? (
                        <span className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400">
                          {bdiScore.toFixed(1)} / 100
                        </span>
                      ) : (
                        <span className="text-slate-500 font-normal italic">Insufficient Data</span>
                      )}
                    </td>
                    <td className="p-3">
                      {b.trend === 'INCREASING' || b.trend === 'UP' ? (
                        <span className="text-rose-400 font-bold text-[10px] uppercase">↑ Increasing</span>
                      ) : b.trend === 'DECREASING' || b.trend === 'DOWN' ? (
                        <span className="text-emerald-400 font-bold text-[10px] uppercase">↓ Decreasing</span>
                      ) : (
                        <span className="text-slate-400 font-medium text-[10px] uppercase">→ Stable</span>
                      )}
                    </td>
                    <td className="p-3">
                      <button
                        onClick={() => handleOpenDetail(b.barrier_category)}
                        className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-400 hover:text-amber-300 px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 transition-all"
                      >
                        <span>Inspect Detail</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Barrier Detail Modal */}
      {selectedBarrier && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-amber-400" />
                  <span>Barrier Intelligence Profile: {selectedBarrier}</span>
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Auditable evidence payload and Barrier Degradation Index metrics.
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedBarrier(null);
                  setBarrierDetail(null);
                }}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-100 transition-all"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              {isDetailLoading ? (
                <div className="p-12 text-center text-xs text-slate-500 animate-pulse">
                  Fetching detailed barrier profile and evidence payload...
                </div>
              ) : !barrierDetail ? (
                <div className="p-8 text-center text-slate-400">
                  <AlertCircle className="w-8 h-8 mx-auto text-slate-600 mb-2" />
                  <p className="text-xs font-semibold">Detailed payload unavailable for this barrier.</p>
                </div>
              ) : (
                <>
                  {/* Summary Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Recurrence Count</p>
                      <p className="text-xl font-extrabold text-slate-100 mt-1">
                        {barrierDetail.recurrence_count || barrierDetail.occurrence_count || 0}
                      </p>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      <p className="text-[10px] font-bold text-amber-400 uppercase">SIF Precursors</p>
                      <p className="text-xl font-extrabold text-amber-400 mt-1">
                        {barrierDetail.sif_potential_count || barrierDetail.sif_count || 0}
                      </p>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      <p className="text-[10px] font-bold text-rose-400 uppercase">Unresolved Issues</p>
                      <p className="text-xl font-extrabold text-rose-400 mt-1">
                        {barrierDetail.unresolved_count || 0}
                      </p>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      <p className="text-[10px] font-bold text-purple-400 uppercase">BDI Score (BDI_v1)</p>
                      <p className="text-xl font-extrabold text-purple-400 mt-1">
                        {barrierDetail.bdi_score !== undefined
                          ? `${barrierDetail.bdi_score.toFixed(1)} / 100`
                          : 'Insufficient Data'}
                      </p>
                    </div>
                  </div>

                  {/* BDI Evidence Breakdown */}
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
                    <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider border-b border-slate-800 pb-2">
                      BDI Evidence & Multi-Factor Drivers
                    </h4>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-slate-400">First Observed Date:</span>{' '}
                        <strong className="text-slate-200">{barrierDetail.first_observed_date || 'N/A'}</strong>
                      </div>
                      <div>
                        <span className="text-slate-400">Latest Observed Date:</span>{' '}
                        <strong className="text-slate-200">{barrierDetail.latest_observed_date || 'N/A'}</strong>
                      </div>
                      <div>
                        <span className="text-slate-400">Persistence Days:</span>{' '}
                        <strong className="text-slate-200">{barrierDetail.persistence_days ?? 'N/A'}</strong>
                      </div>
                      <div>
                        <span className="text-slate-400">Affected Sites Count:</span>{' '}
                        <strong className="text-slate-200">{barrierDetail.affected_sites_count ?? 'N/A'}</strong>
                      </div>
                    </div>

                    {barrierDetail.bdi_evidence && (
                      <div className="p-3 rounded-lg bg-slate-900 border border-slate-800/80 text-[11px] text-slate-300 space-y-1">
                        <p className="font-bold text-amber-400">BDI Formula Drivers:</p>
                        <p>• Recurrence Support Weight: {barrierDetail.bdi_evidence.recurrence_weight ?? 'N/A'}</p>
                        <p>• SIF Association Weight: {barrierDetail.bdi_evidence.sif_weight ?? 'N/A'}</p>
                        <p>• Unresolved Weight: {barrierDetail.bdi_evidence.unresolved_weight ?? 'N/A'}</p>
                        <p>• Trend Weight: {barrierDetail.bdi_evidence.trend_weight ?? 'N/A'}</p>
                      </div>
                    )}
                  </div>

                  {/* Contributing Reports Table */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                      Contributing Barrier Reports
                    </h4>
                    {(!barrierDetail.contributing_reports || barrierDetail.contributing_reports.length === 0) ? (
                      <p className="text-xs text-slate-400 italic">No contributing report payload listed.</p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs text-slate-300">
                          <thead className="bg-slate-950/80 text-slate-400 font-bold border-b border-slate-800 uppercase text-[10px]">
                            <tr>
                              <th className="p-3">Report Number</th>
                              <th className="p-3">Date</th>
                              <th className="p-3">Site / Unit</th>
                              <th className="p-3">SIF Classification</th>
                              <th className="p-3">Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60">
                            {barrierDetail.contributing_reports.map((r, idx) => (
                              <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                                <td className="p-3 font-bold text-amber-400">
                                  {r.report_number || `#${r.id || r}`}
                                </td>
                                <td className="p-3 text-slate-400">{r.date || 'N/A'}</td>
                                <td className="p-3 truncate max-w-[150px]">{r.site || 'N/A'}</td>
                                <td className="p-3">
                                  {r.is_sif_potential || r.sif_potential ? (
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
                                    to={`/reports/${r.id || r}`}
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
                </>
              )}
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-950/40 text-right">
              <button
                onClick={() => {
                  setSelectedBarrier(null);
                  setBarrierDetail(null);
                }}
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
