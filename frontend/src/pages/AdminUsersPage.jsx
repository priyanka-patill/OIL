import React, { useState, useEffect } from 'react';
import { adminApi } from '../api/adminApi';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Users, Shield, CheckCircle, XCircle, Search, Edit3, Save } from 'lucide-react';

export const AdminUsersPage = () => {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [editingUser, setEditingUser] = useState(null);
  const [editRole, setEditRole] = useState('HSE_USER');

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      setError('');
      const response = await adminApi.getUsers();
      if (response?.data) {
        setUsers(response.data || []);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch user list');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleUpdateRole = async (userId) => {
    try {
      await adminApi.updateUser(userId, { role: editRole });
      setEditingUser(null);
      fetchUsers();
    } catch (err) {
      setError(err.message || 'Failed to update user role');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">User Management System</h1>
        <p className="text-xs text-slate-400 mt-1">
          Manage system users, assign role-based access privileges (ADMIN only).
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
          {error}
        </div>
      )}

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {isLoading ? (
          <LoadingSpinner label="Fetching user accounts from database..." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="p-4">User ID</th>
                  <th className="p-4">Name</th>
                  <th className="p-4">Email</th>
                  <th className="p-4">Role</th>
                  <th className="p-4">Site & Department</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-4 font-bold text-slate-400">#{u.id}</td>
                    <td className="p-4 font-semibold text-slate-100">{u.name}</td>
                    <td className="p-4 text-slate-300">{u.email}</td>
                    <td className="p-4">
                      {editingUser === u.id ? (
                        <select
                          value={editRole}
                          onChange={(e) => setEditRole(e.target.value)}
                          className="px-2 py-1 bg-slate-950 border border-amber-500 rounded text-xs text-slate-100"
                        >
                          <option value="HSE_USER">HSE_USER</option>
                          <option value="HSE_MANAGER">HSE_MANAGER</option>
                          <option value="ADMIN">ADMIN</option>
                        </select>
                      ) : (
                        <span className="px-2.5 py-1 rounded text-[10px] font-extrabold uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          {u.role}
                        </span>
                      )}
                    </td>
                    <td className="p-4">
                      <div>{u.site || 'Digboi Refinery'}</div>
                      <div className="text-[11px] text-slate-500">{u.department || 'Operations'}</div>
                    </td>
                    <td className="p-4">
                      <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold">
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>Active</span>
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      {editingUser === u.id ? (
                        <button
                          onClick={() => handleUpdateRole(u.id)}
                          className="px-3 py-1 bg-amber-500 text-slate-950 rounded text-xs font-bold flex items-center gap-1 ml-auto"
                        >
                          <Save className="w-3.5 h-3.5" /> Save
                        </button>
                      ) : (
                        <button
                          onClick={() => {
                            setEditingUser(u.id);
                            setEditRole(u.role);
                          }}
                          className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-xs flex items-center gap-1 ml-auto"
                        >
                          <Edit3 className="w-3.5 h-3.5" /> Edit Role
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
