import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { actionsApi } from '../api/actionsApi';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck,
  Clock,
  AlertTriangle,
  CheckCircle2,
  FileText,
  RefreshCw,
  Filter,
  User,
  Building,
  Calendar,
  Layers,
  Sparkles,
  ArrowRight,
  ChevronRight,
  TrendingDown,
  TrendingUp,
  AlertOctagon,
  History,
  FileCheck,
  CheckSquare,
  Search
} from 'lucide-react';

export const HseActionCenterPage = () => {
  const { user, role } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // Global Filter State (Initialized from URL Query Params)
  const [siteFilter, setSiteFilter] = useState(searchParams.get('site') || '');
  const [deptFilter, setDeptFilter] = useState(searchParams.get('department') || '');
  const [prioFilter, setPrioFilter] = useState(searchParams.get('priority') || '');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || '');
  const [slaFilter, setSlaFilter] = useState(searchParams.get('sla_status') || '');

  // Data State
  const [summaryData, setSummaryData] = useState(null);
  const [sectionsData, setSectionsData] = useState(null);

  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingSections, setLoadingSections] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Active View Tab
  const [activeTab, setActiveTab] = useState('ALL'); // ALL, REVIEWS, ACTIONS, OVERDUE, VERIFICATION, IMPACT

  useEffect(() => {
    // Sync filters to URL query params
    const params = {};
    if (siteFilter) params.site = siteFilter;
    if (deptFilter) params.department = deptFilter;
    if (prioFilter) params.priority = prioFilter;
    if (statusFilter) params.status = statusFilter;
    if (slaFilter) params.sla_status = slaFilter;
    setSearchParams(params);

    fetchAllData();
  }, [siteFilter, deptFilter, prioFilter, statusFilter, slaFilter]);

  const fetchAllData = async () => {
    setError(null);
    const filterParams = {
      site: siteFilter || undefined,
      department: deptFilter || undefined,
      priority: prioFilter || undefined,
      status: statusFilter || undefined,
      sla_status: slaFilter || undefined
    };

    setLoadingSummary(true);
    setLoadingSections(true);

    try {
      const summaryRes = await actionsApi.getActionCenterSummary(filterParams);
      setSummaryData(summaryRes.data?.data || summaryRes.data);
    } catch (err) {
      console.error('Failed to fetch Action Center summary:', err);
      setError(err.response?.data?.message || err.message || 'Failed to load summary counts.');
    } finally {
      setLoadingSummary(false);
    }

    try {
      const sectionsRes = await actionsApi.getActionCenterSections(filterParams);
      setSectionsData(sectionsRes.data?.data || sectionsRes.data);
    } catch (err) {
      console.error('Failed to fetch Action Center sections:', err);
    } finally {
      setLoadingSections(false);
    }
  };

  const handleManualRefresh = async () => {
    setRefreshing(true);
    await fetchAllData();
    setRefreshing(false);
  };

  const resetFilters = () => {
    setSiteFilter('');
    setDeptFilter('');
    setPrioFilter('');
    setStatusFilter('');
    setSlaFilter('');
  };

  const summary = summaryData?.summary || {};
  const metadata = summaryData?.metadata || {};
  const sections = sectionsData || {};

  return (
    <div className="space-y-6">
      {/* Top Header Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-widest">
              <ShieldCheck className="w-4 h-4" />
              OIL HSE SAFETY INTELLIGENCE PLATFORM
            </div>
            <h1 className="text-2xl font-black text-white flex items-center gap-3">
              HSE ACTION CENTER
              <span className="text-xs px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono font-bold">
                Unified Operational Hub
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Operational view of HSE reviews, actions, SLA status, verification and intervention impact.
            </p>
          </div>

          <div className="flex items-center gap-3 self-start md:self-auto">
            <button
              onClick={handleManualRefresh}
              disabled={refreshing}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-bold flex items-center gap-2 transition border border-slate-700 shadow-md"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh Data
            </button>
          </div>
        </div>

        {/* Global Filters Control Bar */}
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5 text-amber-400" />
              Global Action Center Filters
            </span>
            {(siteFilter || deptFilter || prioFilter || statusFilter || slaFilter) && (
              <button
                onClick={resetFilters}
                className="text-[11px] text-amber-400 font-bold hover:underline"
              >
                Clear All Filters
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
            {/* Site Scope Filter */}
            <div>
              <label className="block text-[10px] text-slate-400 font-semibold mb-1">Site Scope</label>
              <select
                value={siteFilter}
                onChange={(e) => setSiteFilter(e.target.value)}
                disabled={role !== 'ADMIN' && user?.site}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-white font-medium focus:outline-none focus:border-amber-500/50"
              >
                <option value="">All Authorized Sites</option>
                <option value="Digboi Refinery">Digboi Refinery</option>
                <option value="Duliajan Field">Duliajan Field</option>
                <option value="Guwahati Refinery">Guwahati Refinery</option>
              </select>
            </div>

            {/* Department Filter */}
            <div>
              <label className="block text-[10px] text-slate-400 font-semibold mb-1">Department</label>
              <select
                value={deptFilter}
                onChange={(e) => setDeptFilter(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-white font-medium focus:outline-none focus:border-amber-500/50"
              >
                <option value="">All Departments</option>
                <option value="Maintenance">Maintenance</option>
                <option value="Operations">Operations</option>
                <option value="Safety">Safety</option>
                <option value="Drilling">Drilling</option>
              </select>
            </div>

            {/* Priority Filter */}
            <div>
              <label className="block text-[10px] text-slate-400 font-semibold mb-1">Priority</label>
              <select
                value={prioFilter}
                onChange={(e) => setPrioFilter(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-white font-medium focus:outline-none focus:border-amber-500/50"
              >
                <option value="">All Priorities</option>
                <option value="HIGH">HIGH Priority</option>
                <option value="MEDIUM">MEDIUM Priority</option>
                <option value="LOW">LOW Priority</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-[10px] text-slate-400 font-semibold mb-1">Action Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-white font-medium focus:outline-none focus:border-amber-500/50"
              >
                <option value="">All Statuses</option>
                <option value="ASSIGNED">ASSIGNED</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="COMPLETED">COMPLETED</option>
                <option value="VERIFICATION_PENDING">VERIFICATION_PENDING</option>
                <option value="VERIFIED">VERIFIED</option>
                <option value="REOPENED">REOPENED</option>
              </select>
            </div>

            {/* SLA Status Filter */}
            <div>
              <label className="block text-[10px] text-slate-400 font-semibold mb-1">SLA Status</label>
              <select
                value={slaFilter}
                onChange={(e) => setSlaFilter(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-white font-medium focus:outline-none focus:border-amber-500/50"
              >
                <option value="">All SLA States</option>
                <option value="ACTIVE">ACTIVE (On Track)</option>
                <option value="DUE_SOON">DUE SOON</option>
                <option value="OVERDUE">OVERDUE</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* 8 Primary KPI Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 text-xs">
        {/* 1. Pending Reviews */}
        <div
          onClick={() => setActiveTab('REVIEWS')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${
            activeTab === 'REVIEWS'
              ? 'bg-amber-500/10 border-amber-500/50 ring-1 ring-amber-500/50'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="text-slate-400 text-[10px] font-bold uppercase truncate">Pending Reviews</div>
          <div className="text-2xl font-black text-amber-400 mt-1">
            {loadingSummary ? '...' : summary.pending_reviews ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1 font-medium">Interventions</div>
        </div>

        {/* 2. Active Actions */}
        <div
          onClick={() => setActiveTab('ACTIONS')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${
            activeTab === 'ACTIONS'
              ? 'bg-blue-500/10 border-blue-500/50 ring-1 ring-blue-500/50'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="text-slate-400 text-[10px] font-bold uppercase truncate">Active Actions</div>
          <div className="text-2xl font-black text-blue-400 mt-1">
            {loadingSummary ? '...' : summary.active_actions ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1 font-medium">In Operations</div>
        </div>

        {/* 3. Due Soon */}
        <div
          onClick={() => setActiveTab('ACTIONS')}
          className="cursor-pointer p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/40 transition-all"
        >
          <div className="text-amber-400 text-[10px] font-bold uppercase truncate flex items-center gap-1">
            <Clock className="w-3 h-3 animate-pulse" />
            Due Soon
          </div>
          <div className="text-2xl font-black text-amber-300 mt-1">
            {loadingSummary ? '...' : summary.due_soon ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1 font-medium">Within Threshold</div>
        </div>

        {/* 4. Overdue */}
        <div
          onClick={() => setActiveTab('OVERDUE')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${
            activeTab === 'OVERDUE'
              ? 'bg-rose-500/10 border-rose-500/50 ring-1 ring-rose-500/50'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="text-rose-400 text-[10px] font-bold uppercase truncate flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 animate-pulse" />
            Overdue
          </div>
          <div className="text-2xl font-black text-rose-400 mt-1">
            {loadingSummary ? '...' : summary.overdue ?? 0}
          </div>
          <div className="text-[10px] text-rose-300/70 mt-1 font-medium">
            {summary.escalated_actions ? `${summary.escalated_actions} Escalated` : 'SLA Breached'}
          </div>
        </div>

        {/* 5. Completed */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
          <div className="text-slate-400 text-[10px] font-bold uppercase truncate">Completed</div>
          <div className="text-2xl font-black text-slate-200 mt-1">
            {loadingSummary ? '...' : summary.completed ?? 0}
          </div>
          <div className="text-[10px] text-emerald-400 mt-1 font-medium">
            {summary.completed_on_time ? `${summary.completed_on_time} On Time` : 'Work Finished'}
          </div>
        </div>

        {/* 6. Verification Pending */}
        <div
          onClick={() => setActiveTab('VERIFICATION')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${
            activeTab === 'VERIFICATION'
              ? 'bg-emerald-500/10 border-emerald-500/50 ring-1 ring-emerald-500/50'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="text-slate-400 text-[10px] font-bold uppercase truncate">Verification</div>
          <div className="text-2xl font-black text-emerald-400 mt-1">
            {loadingSummary ? '...' : summary.verification_pending ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1 font-medium">Awaiting HSE</div>
        </div>

        {/* 7. Impact Available */}
        <div
          onClick={() => setActiveTab('IMPACT')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${
            activeTab === 'IMPACT'
              ? 'bg-indigo-500/10 border-indigo-500/50 ring-1 ring-indigo-500/50'
              : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
          }`}
        >
          <div className="text-indigo-400 text-[10px] font-bold uppercase truncate">Impact Available</div>
          <div className="text-2xl font-black text-indigo-400 mt-1">
            {loadingSummary ? '...' : summary.impact_available ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1 font-medium">Sufficient Data</div>
        </div>

        {/* 8. Insufficient Data */}
        <div
          onClick={() => setActiveTab('IMPACT')}
          className="cursor-pointer p-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all"
        >
          <div className="text-slate-400 text-[10px] font-bold uppercase truncate">Insufficient Data</div>
          <div className="text-2xl font-black text-slate-400 mt-1">
            {loadingSummary ? '...' : summary.insufficient_data ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1 font-medium">Sample &lt; 2 Reports</div>
        </div>
      </div>

      {/* Navigation View Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2 text-xs font-bold overflow-x-auto">
        <button
          onClick={() => setActiveTab('ALL')}
          className={`px-4 py-2 rounded-xl transition ${
            activeTab === 'ALL'
              ? 'bg-amber-500 text-slate-950 shadow-md font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          All Operational View
        </button>
        <button
          onClick={() => setActiveTab('REVIEWS')}
          className={`px-4 py-2 rounded-xl transition flex items-center gap-1.5 ${
            activeTab === 'REVIEWS'
              ? 'bg-amber-500 text-slate-950 shadow-md font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          Pending Reviews ({summary.pending_reviews ?? 0})
        </button>
        <button
          onClick={() => setActiveTab('ACTIONS')}
          className={`px-4 py-2 rounded-xl transition flex items-center gap-1.5 ${
            activeTab === 'ACTIONS'
              ? 'bg-amber-500 text-slate-950 shadow-md font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          My & Active Actions ({summary.active_actions ?? 0})
        </button>
        <button
          onClick={() => setActiveTab('OVERDUE')}
          className={`px-4 py-2 rounded-xl transition flex items-center gap-1.5 ${
            activeTab === 'OVERDUE'
              ? 'bg-rose-500 text-white shadow-md font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          Overdue & Escalations ({summary.overdue ?? 0})
        </button>
        <button
          onClick={() => setActiveTab('VERIFICATION')}
          className={`px-4 py-2 rounded-xl transition flex items-center gap-1.5 ${
            activeTab === 'VERIFICATION'
              ? 'bg-emerald-500 text-slate-950 shadow-md font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          Verification Pending ({summary.verification_pending ?? 0})
        </button>
        <button
          onClick={() => setActiveTab('IMPACT')}
          className={`px-4 py-2 rounded-xl transition flex items-center gap-1.5 ${
            activeTab === 'IMPACT'
              ? 'bg-indigo-500 text-white shadow-md font-extrabold'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          Intervention Impact ({summary.impact_available ?? 0})
        </button>
      </div>

      {/* SECTION 1: Pending HSE Reviews */}
      {(activeTab === 'ALL' || activeTab === 'REVIEWS') && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-amber-400" />
              Pending HSE Interventions Needing Review ({sections.pending_reviews?.length ?? 0})
            </h3>
            <Link to="/interventions" className="text-xs text-amber-400 font-bold hover:underline flex items-center gap-1">
              View All Interventions <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loadingSections ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading Pending Reviews...</div>
          ) : !sections.pending_reviews || sections.pending_reviews.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 italic bg-slate-950/40 rounded-xl border border-slate-800">
              No interventions are currently awaiting HSE review.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 border-b border-slate-800 text-[11px] uppercase text-slate-400 font-bold">
                  <tr>
                    <th className="py-2.5 px-3">Intervention</th>
                    <th className="py-2.5 px-3">Barrier / Category</th>
                    <th className="py-2.5 px-3">Site</th>
                    <th className="py-2.5 px-3">Priority Suggestion</th>
                    <th className="py-2.5 px-3">Created</th>
                    <th className="py-2.5 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {sections.pending_reviews.map((rev) => (
                    <tr key={rev.id} className="hover:bg-slate-850/50 transition">
                      <td className="py-3 px-3">
                        <div className="font-bold text-white text-xs">{rev.title}</div>
                        <div className="font-mono text-[10px] text-amber-400">{rev.recommendation_number}</div>
                      </td>
                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px] font-semibold">
                          {rev.barrier_category}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-400">{rev.site || 'General Site'}</td>
                      <td className="py-3 px-3">
                        <span className="px-2.5 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-bold uppercase">
                          {rev.priority_suggestion}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-slate-500 text-[11px]">
                        {rev.created_at ? new Date(rev.created_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Link
                          to={`/interventions`}
                          className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-[11px] inline-flex items-center gap-1 transition"
                        >
                          Review <ArrowRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* SECTION 2: My Actions & Active Actions */}
      {(activeTab === 'ALL' || activeTab === 'ACTIONS') && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-amber-400" />
              My Assigned Operational Actions ({sections.my_actions?.length ?? 0})
            </h3>
            <Link to="/actions/my" className="text-xs text-amber-400 font-bold hover:underline flex items-center gap-1">
              View All My Actions <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {loadingSections ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading Actions...</div>
          ) : !sections.my_actions || sections.my_actions.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 italic bg-slate-950/40 rounded-xl border border-slate-800">
              No active operational actions are currently assigned to you.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sections.my_actions.map((act) => (
                <div key={act.id} className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3 flex flex-col justify-between hover:border-slate-700 transition">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-amber-400 font-bold text-xs">{act.action_number}</span>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold uppercase">
                        {act.status}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-white line-clamp-2">{act.title}</h4>
                    <p className="text-[11px] text-slate-400 line-clamp-2">{act.description}</p>
                  </div>

                  <div className="space-y-2 pt-2 border-t border-slate-800/80 text-[11px]">
                    <div className="flex items-center justify-between text-slate-400">
                      <span>Due Date: <strong className="text-white">{act.due_date}</strong></span>
                      <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-bold text-[10px]">
                        {act.priority} Priority
                      </span>
                    </div>

                    <Link
                      to={`/actions/${act.id}`}
                      className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-center font-bold text-xs block transition border border-slate-700"
                    >
                      Open Action Record →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SECTION 3: Overdue Actions & SLA Escalation Outbox */}
      {(activeTab === 'ALL' || activeTab === 'OVERDUE') && (
        <div className="bg-slate-900/90 border border-rose-500/30 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-rose-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 animate-pulse" />
              SLA Overdue Actions & Escalation Outbox ({sections.overdue_actions?.length ?? 0})
            </h3>
            <span className="text-xs text-slate-400 font-mono">SLA & Operational Tracking</span>
          </div>

          {loadingSections ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading Overdue Actions...</div>
          ) : !sections.overdue_actions || sections.overdue_actions.length === 0 ? (
            <div className="py-8 text-center text-xs text-emerald-400/90 italic bg-slate-950/40 rounded-xl border border-emerald-500/20 p-4">
              ✓ Excellent! No operational actions are currently overdue.
            </div>
          ) : (
            <div className="space-y-3">
              {sections.overdue_actions.map((act) => (
                <div key={act.id} className="p-4 rounded-xl bg-slate-950/90 border border-rose-500/30 space-y-3 text-xs">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-amber-400 font-bold">{act.action_number}</span>
                        <span className="px-2.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-black text-[10px] uppercase border border-rose-500/40">
                          {act.days_overdue} DAYS OVERDUE
                        </span>
                        {act.current_escalation_level > 0 && (
                          <span className="px-2.5 py-0.5 rounded bg-rose-500/30 text-white font-extrabold text-[10px] uppercase animate-pulse border border-rose-400">
                            LEVEL {act.current_escalation_level} ESCALATED
                          </span>
                        )}
                      </div>
                      <h4 className="text-xs font-bold text-white mt-1">{act.title}</h4>
                    </div>

                    <Link
                      to={`/actions/${act.id}`}
                      className="px-3.5 py-1.5 rounded-lg bg-rose-500 hover:bg-rose-400 text-white font-bold text-xs transition self-start md:self-auto"
                    >
                      View Action Record →
                    </Link>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-[11px] text-slate-300">
                    <div>Assignee: <strong className="text-white">{act.assigned_user_name}</strong></div>
                    <div>Department: <strong>{act.assigned_department || 'Operations'}</strong></div>
                    <div>Site: <strong>{act.site}</strong></div>
                    <div>Due Date: <strong className="text-rose-400">{act.due_date}</strong></div>
                  </div>

                  {act.latest_escalation && (
                    <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-500/20 text-[11px] text-rose-200 space-y-1">
                      <div className="font-bold flex items-center gap-1.5 text-rose-300">
                        <AlertOctagon className="w-3.5 h-3.5" />
                        Escalated to: {act.latest_escalation.recipient}
                      </div>
                      <p className="italic text-[10px]">{act.latest_escalation.reason}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SECTION 4: Verification Pending */}
      {(activeTab === 'ALL' || activeTab === 'VERIFICATION') && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Actions Completed & Awaiting HSE Verification ({sections.verification_pending?.length ?? 0})
            </h3>
            <span className="text-xs text-slate-400 font-mono">HSE Review & Verification</span>
          </div>

          {loadingSections ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading Verification Pending...</div>
          ) : !sections.verification_pending || sections.verification_pending.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 italic bg-slate-950/40 rounded-xl border border-slate-800">
              No completed actions are currently pending HSE verification.
            </div>
          ) : (
            <div className="space-y-3">
              {sections.verification_pending.map((act) => (
                <div key={act.id} className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 text-xs">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-amber-400 font-bold">{act.action_number}</span>
                        <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold text-[10px] uppercase">
                          VERIFICATION PENDING
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-white mt-1">{act.title}</h4>
                    </div>

                    <Link
                      to={`/actions/${act.id}`}
                      className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold text-xs transition self-start md:self-auto"
                    >
                      Inspect & Verify →
                    </Link>
                  </div>

                  <div className="text-slate-300 text-[11px]">
                    <strong>Completed By:</strong> {act.assigned_user_name} on {act.completion_date ? new Date(act.completion_date).toLocaleString() : 'N/A'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SECTION 5: Intervention Impact & Insufficient Data */}
      {(activeTab === 'ALL' || activeTab === 'IMPACT') && (
        <div className="bg-slate-900/90 border border-indigo-500/30 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-indigo-400 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Observational Before/After Intervention Impact Analyses ({sections.impact_analyses?.length ?? 0})
            </h3>
            <span className="text-xs text-slate-400 font-mono">impact_methodology_v1</span>
          </div>

          {loadingSections ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading Impact Analyses...</div>
          ) : !sections.impact_analyses || sections.impact_analyses.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 italic bg-slate-950/40 rounded-xl border border-slate-800">
              No observational impact analyses calculated yet. Verify completed actions to generate impact snapshots.
            </div>
          ) : (
            <div className="space-y-4">
              {sections.impact_analyses.map((imp) => (
                <div key={imp.id} className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3 text-xs">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-indigo-400 font-bold">Action #{imp.action_id}</span>
                        <span className={`px-2.5 py-0.5 rounded font-bold text-[10px] uppercase border ${
                          imp.data_sufficiency_status === 'SUFFICIENT' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        }`}>
                          {imp.data_sufficiency_status}
                        </span>
                        <span className="px-2.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                          Observed Trend: {imp.overall_observed_change}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        Barrier: <strong>{imp.barrier_id || 'General Barrier'}</strong> • Pattern: <strong>{imp.pattern_id || 'N/A'}</strong>
                      </div>
                    </div>

                    <Link
                      to={`/actions/${imp.action_id}`}
                      className="px-3.5 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 font-bold text-xs transition self-start md:self-auto"
                    >
                      View Impact Details →
                    </Link>
                  </div>

                  <div className="text-slate-300 text-[11px] leading-relaxed">
                    <strong>Sufficiency Rationale:</strong> {imp.data_sufficiency_reason}
                  </div>

                  {imp.metrics && (
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-400 italic">
                      <strong>Methodology Disclaimer:</strong> {imp.metrics.disclaimer}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SECTION 6: Recent Operational Activity Audit Stream */}
      {activeTab === 'ALL' && sections.recent_activity && sections.recent_activity.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <History className="w-4 h-4 text-amber-400" />
            Recent Operational Activity Stream ({sections.recent_activity.length})
          </h3>

          <div className="space-y-2">
            {sections.recent_activity.map((item) => (
              <div key={item.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
                <div className="space-y-0.5">
                  <span className="font-mono text-amber-400 font-bold text-[11px] uppercase">{item.action_type}</span>
                  <div className="text-slate-300 text-[11px]">
                    By <strong>{item.user_name}</strong> on {item.entity_type} #{item.entity_id}
                  </div>
                </div>
                <div className="text-[10px] text-slate-500 font-mono shrink-0">
                  {item.timestamp ? new Date(item.timestamp).toLocaleString() : ''}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
