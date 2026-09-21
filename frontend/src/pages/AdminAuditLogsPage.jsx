import React, { useState, useEffect } from 'react';
import { adminApi } from '../api/adminApi';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Pagination } from '../components/common/Pagination';
import { History, Shield, Clock, FileText } from 'lucide-react';

export const AdminAuditLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchAuditLogs = async () => {
    try {
      setIsLoading(true);
      setError('');
      const response = await adminApi.getAuditLogs({ page, limit: pageSize });
      if (response?.data) {
        setLogs(response.data.logs || []);
        setTotal(response.data.total || 0);
        setTotalPages(response.data.total_pages || 1);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch audit log trail');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [page]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">System Audit Trail</h1>
        <p className="text-xs text-slate-400 mt-1">
          Append-only security log tracking system authentication, report creations, and HSE reviews.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
          {error}
        </div>
      )}

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {isLoading ? (
          <LoadingSpinner label="Fetching append-only audit trail logs..." />
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <History className="w-10 h-10 mx-auto text-slate-600 mb-2" />
            <p className="text-sm font-medium">No audit activity recorded yet.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-4">Log ID</th>
                    <th className="p-4">Timestamp</th>
                    <th className="p-4">Action</th>
                    <th className="p-4">User</th>
                    <th className="p-4">Target Resource</th>
                    <th className="p-4">Metadata</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/40 transition-colors font-mono">
                      <td className="p-4 font-bold text-slate-500">#{log.id}</td>
                      <td className="p-4 text-slate-400 whitespace-nowrap font-sans">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase font-sans">
                          {log.action}
                        </span>
                      </td>
                      <td className="p-4 font-sans text-slate-200">
                        {log.user_email || `User #${log.user_id}`}
                      </td>
                      <td className="p-4 font-sans text-slate-300">
                        {log.entity_type ? `${log.entity_type} #${log.entity_id || ''}` : 'N/A'}
                      </td>
                      <td className="p-4 text-[11px] text-slate-400 max-w-xs truncate">
                        {log.metadata_json || '{}'}
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
