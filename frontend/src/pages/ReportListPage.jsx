import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { reportsApi } from '../api/reportsApi';
import { StatusBadge } from '../components/common/StatusBadge';
import { ReportTypeBadge } from '../components/common/ReportTypeBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Pagination } from '../components/common/Pagination';
import {
  FileText,
  Search,
  Filter,
  PlusCircle,
  X,
  ExternalLink,
  Building2,
  Calendar,
  Paperclip,
} from 'lucide-react';

export const ReportListPage = () => {
  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);

  const [search, setSearch] = useState('');
  const [siteFilter, setSiteFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchReports = async () => {
    try {
      setIsLoading(true);
      setError('');
      const params = {
        page,
        limit: pageSize,
      };
      if (search.trim()) params.search = search.trim();
      if (siteFilter) params.site = siteFilter;
      if (typeFilter) params.report_type = typeFilter;
      if (statusFilter) params.status = statusFilter;

      const response = await reportsApi.getReports(params);
      if (response?.data) {
        setReports(response.data.reports || []);
        setTotal(response.data.total || 0);
        setTotalPages(response.data.total_pages || 1);
      }
    } catch (err) {
      setError(err.message || 'Failed to load safety reports list');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [page, siteFilter, typeFilter, statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchReports();
  };

  const handleClearFilters = () => {
    setSearch('');
    setSiteFilter('');
    setTypeFilter('');
    setStatusFilter('');
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Safety Reports Directory</h1>
          <p className="text-xs text-slate-400 mt-1">
            Browse, search, and manage all logged near-misses, unsafe acts, and conditions.
          </p>
        </div>

        <Link
          to="/reports/new"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-950 bg-amber-500 hover:bg-amber-400 transition-all shadow-lg shadow-amber-500/20 shrink-0"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Safety Report</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 shadow-xl space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by report number, description, or keyword..."
              className="w-full pl-10 pr-4 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          <button
            type="submit"
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 border border-slate-700"
          >
            <Filter className="w-3.5 h-3.5 text-amber-500" />
            <span>Apply Search</span>
          </button>
        </form>

        {/* Dropdown Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-800/80">
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
              Report Type
            </label>
            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-1.5 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Observation Types</option>
              <option value="NEAR_MISS">Near Miss</option>
              <option value="UNSAFE_ACT">Unsafe Act</option>
              <option value="UNSAFE_CONDITION">Unsafe Condition</option>
              <option value="INCIDENT">Incident</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-1.5 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="PENDING_REVIEW">Pending Review</option>
              <option value="HSE_VALIDATED">HSE Validated</option>
              <option value="ACTION_REQUIRED">Action Required</option>
              <option value="REJECTED">Rejected</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
              Plant / Site
            </label>
            <select
              value={siteFilter}
              onChange={(e) => {
                setSiteFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-1.5 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            >
              <option value="">All Operational Sites</option>
              <option value="Digboi Refinery">Digboi Refinery</option>
              <option value="Duliajan Site">Duliajan Site</option>
              <option value="Guwahati Refinery">Guwahati Refinery</option>
              <option value="Bongaigaon Refinery">Bongaigaon Refinery</option>
            </select>
          </div>
        </div>

        {(search || siteFilter || typeFilter || statusFilter) && (
          <div className="flex justify-end pt-2">
            <button
              onClick={handleClearFilters}
              className="text-xs text-amber-400 hover:underline flex items-center gap-1 font-medium"
            >
              <X className="w-3.5 h-3.5" />
              <span>Reset All Filters</span>
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Reports Data Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {isLoading ? (
          <LoadingSpinner label="Loading reports from backend..." />
        ) : reports.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-3">
            <FileText className="w-12 h-12 mx-auto text-slate-600" />
            <p className="text-base font-semibold text-slate-200">No safety reports found</p>
            <p className="text-xs text-slate-400">
              Try adjusting your search criteria or clear active filters.
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-4">Report No.</th>
                    <th className="p-4">Type</th>
                    <th className="p-4">Site & Unit</th>
                    <th className="p-4">Work / Department</th>
                    <th className="p-4">Date</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {reports.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="p-4 font-bold text-amber-400">
                        <div className="flex items-center gap-2">
                          <Link to={`/reports/${r.id}`} className="hover:underline">
                            {r.report_number}
                          </Link>
                          {r.attachments && r.attachments.length > 0 && (
                            <span
                              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700 font-mono"
                              title={`${r.attachments.length} attachment(s)`}
                            >
                              <Paperclip className="w-3 h-3 text-amber-400" />
                              <span>{r.attachments.length}</span>
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        <ReportTypeBadge type={r.report_type} />
                      </td>
                      <td className="p-4">
                        <div className="font-medium text-slate-200">{r.site}</div>
                        {r.refinery_unit && (
                          <div className="text-[11px] text-slate-400">{r.refinery_unit}</div>
                        )}
                      </td>
                      <td className="p-4">
                        <div className="text-slate-300">{r.department || 'Operations'}</div>
                        {r.work_type && (
                          <div className="text-[11px] text-slate-500">{r.work_type}</div>
                        )}
                      </td>
                      <td className="p-4 text-slate-400 whitespace-nowrap">{r.date}</td>
                      <td className="p-4">
                        <StatusBadge status={r.status} />
                      </td>
                      <td className="p-4 text-right">
                        <Link
                          to={`/reports/${r.id}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium transition-colors"
                        >
                          <span>View</span>
                          <ExternalLink className="w-3.5 h-3.5 text-amber-400" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <Pagination
              currentPage={page}
              totalPages={totalPages}
              totalItems={total}
              pageSize={pageSize}
              onPageChange={(newPage) => setPage(newPage)}
            />
          </>
        )}
      </div>
    </div>
  );
};
