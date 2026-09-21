import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Repeat, Shield, TrendingUp, FileText, ArrowRight, ExternalLink } from 'lucide-react';
import { analyticsApi } from '../../api/analyticsApi';

export const RelatedSafetyIntelligence = ({ reportId }) => {
  const [relatedData, setRelatedData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!reportId) return;

    const fetchRelated = async () => {
      try {
        setIsLoading(true);
        const res = await analyticsApi.getRelatedReports(reportId, { max_results: 5 });
        setRelatedData(res?.data || null);
      } catch (err) {
        console.error('Failed to load related safety intelligence:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRelated();
  }, [reportId]);

  if (isLoading) {
    return (
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 animate-pulse text-xs text-slate-500">
        Cross-referencing related safety intelligence across Oil India database...
      </div>
    );
  }

  const relatedReports = relatedData?.related_reports || relatedData?.items || [];
  const primaryReport = relatedData?.primary_report || {};

  return (
    <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Related Safety Intelligence
          </h2>
        </div>
        <Link
          to="/analytics"
          className="text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1"
        >
          <span>Safety Intelligence Dashboard</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        {/* Card 1: Barrier Context */}
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-amber-400 font-bold">
            <Shield className="w-3.5 h-3.5" />
            <span>Barrier Recurrence</span>
          </div>
          <p className="text-slate-300 text-[11px] pt-1">
            {primaryReport.barrier_category ? (
              <>
                Mapped to barrier category:{' '}
                <strong className="text-slate-100">{primaryReport.barrier_category}</strong>
              </>
            ) : (
              'No specific barrier category mapped.'
            )}
          </p>
        </div>

        {/* Card 2: Pattern Context */}
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-cyan-400 font-bold">
            <Repeat className="w-3.5 h-3.5" />
            <span>Pattern Membership</span>
          </div>
          <p className="text-slate-300 text-[11px] pt-1">
            Associated with operational context ({primaryReport.work_type || 'General Work'} on {primaryReport.equipment_id || 'Asset'}).
          </p>
        </div>

        {/* Card 3: Escalation Status */}
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-orange-400 font-bold">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Risk Escalation</span>
          </div>
          <p className="text-slate-300 text-[11px] pt-1">
            Precursor indicators evaluated against risk escalation analytical criteria.
          </p>
        </div>
      </div>

      {/* Related Reports List */}
      {relatedReports.length > 0 && (
        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
            Analytically Related Safety Reports ({relatedReports.length})
          </h3>
          <div className="divide-y divide-slate-800/80 border border-slate-800 rounded-xl overflow-hidden bg-slate-950/40">
            {relatedReports.map((item, idx) => {
              const rep = item.report || item;
              const reason = item.relationship_reason || item.evidence_summary || 'Shared operational dimension / barrier concern';

              return (
                <div key={idx} className="p-3.5 flex items-center justify-between hover:bg-slate-800/40 transition-colors">
                  <div className="space-y-0.5 min-w-0 pr-3">
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/reports/${rep.id}`}
                        className="font-bold text-amber-400 hover:underline text-xs"
                      >
                        {rep.report_number || `#${rep.id}`}
                      </Link>
                      <span className="text-[10px] text-slate-400">• {rep.date || 'N/A'}</span>
                      <span className="text-[10px] text-slate-400">• {rep.site || 'N/A'}</span>
                    </div>
                    <p className="text-[11px] text-slate-300 truncate">{reason}</p>
                  </div>

                  <Link
                    to={`/reports/${rep.id}`}
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400 hover:text-amber-300 shrink-0"
                  >
                    <span>View Report</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
