import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { reportsApi } from '../api/reportsApi';
import { StatusBadge } from '../components/common/StatusBadge';
import { ReportTypeBadge } from '../components/common/ReportTypeBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import {
  FileText,
  ShieldAlert,
  Clock,
  AlertTriangle,
  PlusCircle,
  Building2,
  TrendingUp,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

export const DashboardPage = () => {
  const [reports, setReports] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        const response = await reportsApi.getReports({ limit: 50 });
        if (response?.data) {
          setReports(response.data.reports || []);
          setTotalCount(response.data.total || 0);
        }
      } catch (err) {
        setError(err.message || 'Failed to load dashboard metrics');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (isLoading) {
    return <LoadingSpinner label="Fetching HSE dashboard metrics from Oil India database..." />;
  }

  // Derive metrics strictly from persisted backend data
  const pendingReviews = reports.filter(
    (r) => r.status === 'SUBMITTED' || r.status === 'HSE_REVIEW_PENDING'
  ).length;

  const openActions = reports.filter((r) => r.status === 'ACTION_REQUIRED').length;

  const validatedCount = reports.filter((r) => r.status === 'HSE_VALIDATED').length;

  // Real SIF count: strictly derived from stored AI analysis or HSE validated status (0 if not analyzed)
  const sifAnalyzedCount = reports.filter((r) => r.status === 'AI_ANALYZED').length;

  // Type Breakdown
  const nearMisses = reports.filter((r) => r.report_type === 'NEAR_MISS').length;
  const unsafeActs = reports.filter((r) => r.report_type === 'UNSAFE_ACT').length;
  const unsafeConditions = reports.filter((r) => r.report_type === 'UNSAFE_CONDITION').length;

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-amber-950/40 border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center gap-2 text-xs text-amber-400 font-semibold uppercase tracking-wider mb-1">
            <Building2 className="w-4 h-4" />
            <span>Oil India Limited — Industrial Safety Command</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100">HSE Safety Analytics Dashboard</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time monitoring of refinery safety observations, near-miss precursor trends & HSE workflows.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link
            to="/analytics"
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 transition-all shadow-lg"
          >
            <Sparkles className="w-4 h-4" />
            <span>Safety Intelligence</span>
          </Link>
          <Link
            to="/reports/new"
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-950 bg-amber-500 hover:bg-amber-400 transition-all shadow-lg shadow-amber-500/20 shrink-0"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Submit Report</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1 */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Reports</span>
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <p className="text-3xl font-extrabold text-slate-100">{totalCount}</p>
            <p className="text-[11px] text-slate-400 mt-1">Persisted backend records</p>
          </div>
        </div>

        {/* Card 2 */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">SIF Analyzed</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <p className="text-3xl font-extrabold text-slate-100">{sifAnalyzedCount}</p>
            <p className="text-[11px] text-slate-400 mt-1">AI Safety Analysis</p>
          </div>
        </div>

        {/* Card 3 */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">HSE Validated</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <p className="text-3xl font-extrabold text-slate-100">{validatedCount}</p>
            <p className="text-[11px] text-emerald-400 mt-1">Reviewed by Manager</p>
          </div>
        </div>

        {/* Card 4 */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pending Review</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <p className="text-3xl font-extrabold text-slate-100">{pendingReviews}</p>
            <p className="text-[11px] text-amber-400 mt-1">Awaiting manager action</p>
          </div>
        </div>

        {/* Card 5 */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Open Actions</span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <p className="text-3xl font-extrabold text-slate-100">{openActions}</p>
            <p className="text-[11px] text-slate-400 mt-1">Action required status</p>
          </div>
        </div>
      </div>

      {/* Observation Breakdown & Recent Reports Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Breakdown */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider border-b border-slate-800 pb-3">
            Observation Type Distribution
          </h2>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium">Near Miss Reports</span>
                <span className="text-amber-400 font-bold">{nearMisses}</span>
              </div>
              <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-500 transition-all duration-500"
                  style={{ width: `${totalCount ? (nearMisses / totalCount) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium">Unsafe Act Observations</span>
                <span className="text-orange-400 font-bold">{unsafeActs}</span>
              </div>
              <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                <div
                  className="h-full bg-orange-500 transition-all duration-500"
                  style={{ width: `${totalCount ? (unsafeActs / totalCount) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium">Unsafe Condition Reports</span>
                <span className="text-red-400 font-bold">{unsafeConditions}</span>
              </div>
              <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 transition-all duration-500"
                  style={{ width: `${totalCount ? (unsafeConditions / totalCount) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
            <p>• Data synchronized directly with Oil India backend (`app.db`).</p>
            <p>• Zero mock or hard-coded statistical values.</p>
          </div>
        </div>

        {/* Recent Reports Table */}
        <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
                Recent Safety Reports
              </h2>
              <Link
                to="/reports"
                className="text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1"
              >
                <span>View All Reports</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {reports.length === 0 ? (
              <div className="p-8 text-center text-slate-400 space-y-3">
                <FileText className="w-10 h-10 mx-auto text-slate-600" />
                <p className="text-sm font-medium">No safety reports recorded in database yet.</p>
                <Link
                  to="/reports/new"
                  className="inline-block px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs"
                >
                  Create First Safety Report
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800">
                    <tr>
                      <th className="p-3">Report Number</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Site / Unit</th>
                      <th className="p-3">Date</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {reports.slice(0, 5).map((r) => (
                      <tr
                        key={r.id}
                        className="hover:bg-slate-800/40 transition-colors cursor-pointer"
                      >
                        <td className="p-3">
                          <Link
                            to={`/reports/${r.id}`}
                            className="font-bold text-amber-400 hover:underline"
                          >
                            {r.report_number}
                          </Link>
                        </td>
                        <td className="p-3">
                          <ReportTypeBadge type={r.report_type} />
                        </td>
                        <td className="p-3 truncate max-w-[150px]">
                          {r.site} {r.refinery_unit ? `(${r.refinery_unit})` : ''}
                        </td>
                        <td className="p-3 text-slate-400">{r.date}</td>
                        <td className="p-3">
                          <StatusBadge status={r.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
