import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, AlertTriangle, ShieldAlert, ArrowRight, X, ExternalLink, Info, CheckCircle2, AlertCircle } from 'lucide-react';
import { analyticsApi } from '../../api/analyticsApi';

export const AnalyticsEscalationSection = ({ escalationData, priorityData, filters, isLoading }) => {
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [entityDetail, setEntityDetail] = useState(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  if (isLoading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl animate-pulse h-48 flex items-center justify-center">
        <span className="text-xs text-slate-500">Evaluating Potential Risk Escalation & Risk Priority Index tiers...</span>
      </div>
    );
  }

  const escalationEntities = escalationData?.escalating_entities || [];
  const priorityItems = priorityData?.priorities || [];

  const handleOpenDetail = async (entityType, entityId) => {
    setSelectedEntity({ entityType, entityId });
    setIsDetailLoading(true);
    try {
      const res = await analyticsApi.getEscalationDetail(entityType, entityId, filters);
      setEntityDetail(res?.data || null);
    } catch (err) {
      console.error('Failed to load escalation detail:', err);
      setEntityDetail(null);
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
            <TrendingUp className="w-4 h-4 text-orange-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Potential Risk Escalation & Analytical Prioritization
            </h2>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Non-predictive evidence indicators supporting HSE review prioritization.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-orange-400 bg-orange-500/10 border border-orange-500/20 px-3 py-1 rounded-xl">
            Methodologies: RE_v1 & PRI_v1
          </span>
        </div>
      </div>

      {/* Methodology Disclaimer */}
      <div className="p-3.5 rounded-xl bg-orange-500/10 border border-orange-500/20 text-[11px] text-orange-300 flex items-start gap-2">
        <Info className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold">Non-Predictive Analytical Scope:</p>
          <p className="text-slate-300 mt-0.5">
            "Analytical Priority is a transparent evidence indicator intended to support HSE review. It is not a prediction of future fatalities, accidents, or SIF events."
          </p>
        </div>
      </div>

      {priorityItems.length === 0 && escalationEntities.length === 0 ? (
        <div className="p-8 text-center text-slate-400 space-y-2">
          <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500" />
          <p className="text-xs font-semibold">No active escalation indicators for selected filters.</p>
          <p className="text-[11px] text-slate-500">
            Escalation indicators require at least 3 precursor observations matching evidence criteria.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 font-bold border-b border-slate-800 uppercase text-[10px]">
              <tr>
                <th className="p-3">Entity Identifier</th>
                <th className="p-3">Priority Tier (PRI_v1)</th>
                <th className="p-3">Reports Count</th>
                <th className="p-3">SIF-Potential</th>
                <th className="p-3">Unresolved Issues</th>
                <th className="p-3">Active Indicators</th>
                <th className="p-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {priorityItems.map((item, idx) => {
                const entityId = item.entity_id || item.entity_name || 'Unspecified';
                const entityType = item.entity_type || item.dimension || 'equipment_id';
                const tier = item.priority_tier || item.tier || 'Low Priority Review';
                const reportCount = item.report_count || item.total_reports || 0;
                const sifCount = item.sif_potential_count || item.sif_count || 0;
                const unresolved = item.unresolved_count || 0;
                const indicators = item.indicators || item.evidence_indicators || [];

                return (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 font-semibold text-slate-100 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-orange-400 shrink-0" />
                      <span>{entityId}</span>
                    </td>
                    <td className="p-3">
                      {tier === 'High Priority Review' || tier === 'HIGH' ? (
                        <span className="px-2.5 py-0.5 rounded text-[10px] bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold uppercase">
                          High Priority Review
                        </span>
                      ) : tier === 'Medium Priority Review' || tier === 'MEDIUM' ? (
                        <span className="px-2.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold uppercase">
                          Medium Priority Review
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 font-medium uppercase">
                          Low Priority Review
                        </span>
                      )}
                    </td>
                    <td className="p-3 font-bold">{reportCount}</td>
                    <td className="p-3 font-bold text-amber-400">{sifCount}</td>
                    <td className="p-3 text-rose-400 font-bold">{unresolved}</td>
                    <td className="p-3">
                      <div className="flex flex-wrap gap-1">
                        {indicators.map((ind, i) => (
                          <span
                            key={i}
                            className="text-[9px] bg-slate-950 text-slate-300 px-1.5 py-0.5 rounded border border-slate-800"
                          >
                            • {ind.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="p-3">
                      <button
                        onClick={() => handleOpenDetail(entityType, entityId)}
                        className="inline-flex items-center gap-1 text-[11px] font-bold text-orange-400 hover:text-orange-300 px-2.5 py-1 rounded-lg bg-orange-500/10 border border-orange-500/20 transition-all"
                      >
                        <span>View Evidence</span>
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

      {/* Detail Modal */}
      {selectedEntity && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
              <div>
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-orange-400" />
                  <span>Risk Escalation Evidence: {selectedEntity.entityId}</span>
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Evidence payload, priority tier, and contributing safety reports.
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedEntity(null);
                  setEntityDetail(null);
                }}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-slate-100 transition-all"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              {isDetailLoading ? (
                <div className="p-12 text-center text-xs text-slate-500 animate-pulse">
                  Loading detailed risk escalation payload...
                </div>
              ) : !entityDetail ? (
                <div className="p-8 text-center text-slate-400">
                  <AlertCircle className="w-8 h-8 mx-auto text-slate-600 mb-2" />
                  <p className="text-xs font-semibold">Detail payload unavailable for this entity.</p>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Total Reports</p>
                      <p className="text-xl font-extrabold text-slate-100 mt-1">
                        {entityDetail.total_reports || entityDetail.report_count || 0}
                      </p>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      <p className="text-[10px] font-bold text-amber-400 uppercase">SIF-Potential</p>
                      <p className="text-xl font-extrabold text-amber-400 mt-1">
                        {entityDetail.sif_potential_count || entityDetail.sif_count || 0}
                      </p>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      <p className="text-[10px] font-bold text-rose-400 uppercase">Unresolved Issues</p>
                      <p className="text-xl font-extrabold text-rose-400 mt-1">
                        {entityDetail.unresolved_count || 0}
                      </p>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      <p className="text-[10px] font-bold text-orange-400 uppercase">Priority Tier</p>
                      <p className="text-xs font-extrabold text-orange-400 mt-2 uppercase">
                        {entityDetail.priority_tier || 'Low Priority Review'}
                      </p>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                    <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                      Observed Evidence Indicators
                    </h4>
                    <div className="flex flex-wrap gap-2 pt-1">
                      {(entityDetail.indicators || entityDetail.evidence_indicators || []).map((ind, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-orange-500/10 text-orange-300 border border-orange-500/20 text-xs font-medium"
                        >
                          ✓ {ind.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Related Reports Table */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                      Entity Contributing Reports
                    </h4>
                    {(!entityDetail.contributing_reports || entityDetail.contributing_reports.length === 0) ? (
                      <p className="text-xs text-slate-400 italic">No contributing reports listed.</p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs text-slate-300">
                          <thead className="bg-slate-950/80 text-slate-400 font-bold border-b border-slate-800 uppercase text-[10px]">
                            <tr>
                              <th className="p-3">Report Number</th>
                              <th className="p-3">Date</th>
                              <th className="p-3">SIF Classification</th>
                              <th className="p-3">Status</th>
                              <th className="p-3">Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60">
                            {entityDetail.contributing_reports.map((r, idx) => (
                              <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                                <td className="p-3 font-bold text-amber-400">
                                  {r.report_number || `#${r.id || r}`}
                                </td>
                                <td className="p-3 text-slate-400">{r.date || 'N/A'}</td>
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
                                <td className="p-3">{r.status || 'SUBMITTED'}</td>
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
                  setSelectedEntity(null);
                  setEntityDetail(null);
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
