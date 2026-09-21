import React, { useState, useEffect } from 'react';
import { actionsApi } from '../api/actionsApi';
import { adminApi } from '../api/adminApi';
import { ActionCard } from '../components/actions/ActionCard';
import {
  Building2,
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
  Inbox,
  Shield,
  User
} from 'lucide-react';

export const AssignedActionsPage = () => {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [siteFilter, setSiteFilter] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const [slaFilter, setSlaFilter] = useState('');
  const [slaSummary, setSlaSummary] = useState(null);

  const [users, setUsers] = useState([]);

  useEffect(() => {
    fetchActions();
    fetchUsersList();
    fetchSlaSummary();
  }, [siteFilter, deptFilter, statusFilter, priorityFilter]);

  const fetchSlaSummary = async () => {
    try {
      const res = await actionsApi.getSlaSummary();
      setSlaSummary(res.data?.data || res.data);
    } catch (e) {
      console.error('Failed to load SLA summary metrics:', e);
    }
  };

  const fetchUsersList = async () => {
    try {
      const res = await adminApi.getUsers();
      setUsers(res.data?.data || res.data || []);
    } catch (err) {
      console.error('Failed to load user list:', err);
    }
  };

  const fetchActions = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (siteFilter) params.site = siteFilter;
      if (deptFilter) params.department = deptFilter;
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;
      if (searchQuery) params.search = searchQuery;

      const res = await actionsApi.getAssignedActions(params);
      const list = res.data?.data || res.data || [];
      setActions(list);
    } catch (err) {
      console.error('Failed to fetch assigned actions:', err);
      setError(err.response?.data?.message || err.message || 'Failed to load organizational actions.');
    } finally {
      setLoading(false);
    }
  };

  const filteredActions = actions.filter((a) => {
    if (slaFilter) {
      if (slaFilter === 'ACTIVE' && a.sla?.sla_status !== 'ACTIVE') return false;
      if (slaFilter === 'DUE_SOON' && a.sla?.sla_status !== 'DUE_SOON') return false;
      if (slaFilter === 'OVERDUE' && a.sla?.sla_status !== 'OVERDUE') return false;
      if (slaFilter === 'COMPLETED_ON_TIME' && a.sla?.completion_timing !== 'COMPLETED_ON_TIME') return false;
      if (slaFilter === 'COMPLETED_LATE' && a.sla?.completion_timing !== 'COMPLETED_LATE') return false;
    }
    return true;
  });

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchActions();
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-widest mb-1">
            <Building2 className="w-4 h-4" />
            ACTION MANAGEMENT & MONITORING
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Assigned Actions & SLA Oversight
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Oversight of operational actions and SLA compliance resulting from HSE-approved interventions across sites and departments.
          </p>
        </div>
        <button
          onClick={() => { fetchActions(); fetchSlaSummary(); }}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-2 transition border border-slate-700 self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Actions List
        </button>
      </div>

      {/* SLA Summary Header Cards */}
      {slaSummary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div
            onClick={() => setSlaFilter(slaFilter === 'ACTIVE' ? '' : 'ACTIVE')}
            className={`p-4 rounded-2xl border transition cursor-pointer ${
              slaFilter === 'ACTIVE'
                ? 'bg-blue-500/20 border-blue-400 shadow-lg'
                : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
            }`}
          >
            <span className="text-slate-400 text-[11px] font-semibold block uppercase">Active SLAs</span>
            <span className="text-2xl font-black text-blue-400">{slaSummary.active_actions_under_sla}</span>
          </div>

          <div
            onClick={() => setSlaFilter(slaFilter === 'DUE_SOON' ? '' : 'DUE_SOON')}
            className={`p-4 rounded-2xl border transition cursor-pointer ${
              slaFilter === 'DUE_SOON'
                ? 'bg-amber-500/20 border-amber-400 shadow-lg'
                : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
            }`}
          >
            <span className="text-slate-400 text-[11px] font-semibold block uppercase">Due Soon</span>
            <span className="text-2xl font-black text-amber-400">{slaSummary.due_soon_count}</span>
          </div>

          <div
            onClick={() => setSlaFilter(slaFilter === 'OVERDUE' ? '' : 'OVERDUE')}
            className={`p-4 rounded-2xl border transition cursor-pointer ${
              slaFilter === 'OVERDUE'
                ? 'bg-rose-500/20 border-rose-400 shadow-lg'
                : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
            }`}
          >
            <span className="text-slate-400 text-[11px] font-semibold block uppercase">Overdue</span>
            <span className="text-2xl font-black text-rose-400">{slaSummary.overdue_count}</span>
          </div>

          <div
            onClick={() => setSlaFilter(slaFilter === 'COMPLETED_ON_TIME' ? '' : 'COMPLETED_ON_TIME')}
            className={`p-4 rounded-2xl border transition cursor-pointer ${
              slaFilter === 'COMPLETED_ON_TIME'
                ? 'bg-emerald-500/20 border-emerald-400 shadow-lg'
                : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
            }`}
          >
            <span className="text-slate-400 text-[11px] font-semibold block uppercase">On Time</span>
            <span className="text-2xl font-black text-emerald-400">{slaSummary.completed_on_time_count}</span>
          </div>

          <div
            onClick={() => setSlaFilter(slaFilter === 'COMPLETED_LATE' ? '' : 'COMPLETED_LATE')}
            className={`p-4 rounded-2xl border transition cursor-pointer ${
              slaFilter === 'COMPLETED_LATE'
                ? 'bg-yellow-500/20 border-yellow-400 shadow-lg'
                : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
            }`}
          >
            <span className="text-slate-400 text-[11px] font-semibold block uppercase">Completed Late</span>
            <span className="text-2xl font-black text-yellow-400">{slaSummary.completed_late_count}</span>
          </div>
        </div>
      )}

      {/* Backend Filter Controls */}
      <form onSubmit={handleSearchSubmit} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col lg:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full lg:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search action #, title..."
            className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
          />
        </div>

        {/* Dropdowns */}
        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-medium">SLA Status:</span>
            <select
              value={slaFilter}
              onChange={(e) => setSlaFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500/50"
            >
              <option value="">All SLA Statuses</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="DUE_SOON">DUE SOON</option>
              <option value="OVERDUE">OVERDUE</option>
              <option value="COMPLETED_ON_TIME">COMPLETED ON TIME</option>
              <option value="COMPLETED_LATE">COMPLETED LATE</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={siteFilter}
              onChange={(e) => setSiteFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500/50"
            >
              <option value="">All Sites</option>
              <option value="Digboi Refinery">Digboi Refinery</option>
              <option value="Duliajan HC">Duliajan HC</option>
              <option value="Guwahati Refinery">Guwahati Refinery</option>
              <option value="Bongaigaon Refinery">Bongaigaon Refinery</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-medium">Department:</span>
            <input
              type="text"
              value={deptFilter}
              onChange={(e) => setDeptFilter(e.target.value)}
              placeholder="e.g. Operations"
              className="w-28 px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500/50"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500/50"
            >
              <option value="">All Statuses</option>
              <option value="ASSIGNED">ASSIGNED</option>
              <option value="IN_PROGRESS">IN_PROGRESS</option>
              <option value="ON_HOLD">ON_HOLD</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="VERIFICATION_PENDING">VERIFICATION_PENDING</option>
              <option value="VERIFIED">VERIFIED</option>
              <option value="REOPENED">REOPENED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400 font-medium">Priority:</span>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500/50"
            >
              <option value="">All Priorities</option>
              <option value="HIGH">HIGH Priority</option>
              <option value="MEDIUM">MEDIUM Priority</option>
              <option value="LOW">LOW Priority</option>
            </select>
          </div>

          <button
            type="submit"
            className="px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition"
          >
            Apply
          </button>
        </div>
      </form>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-3">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Action Cards Grid */}
      {loading ? (
        <div className="py-16 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
          Loading organizational actions...
        </div>
      ) : filteredActions.length === 0 ? (
        <div className="py-20 text-center bg-slate-900/40 border border-slate-800 rounded-2xl p-8 space-y-3">
          <Inbox className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-slate-300">No Organizational Actions Found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            No actions match the selected site, department, status, SLA, or search filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredActions.map((action) => (
            <ActionCard key={action.id} action={action} />
          ))}
        </div>
      )}
    </div>
  );
};
