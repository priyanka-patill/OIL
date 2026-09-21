import React, { useState, useEffect } from 'react';
import { actionsApi } from '../../api/actionsApi';
import { adminApi } from '../../api/adminApi';
import {
  X,
  CheckCircle2,
  AlertCircle,
  Building,
  User,
  Calendar,
  Shield,
  FileText,
  Clock,
  Sparkles
} from 'lucide-react';

export const ActionCreateModal = ({ isOpen, onClose, recommendation, onActionCreated }) => {
  if (!isOpen || !recommendation) return null;

  const latestReview = recommendation.latest_review || {};

  // Prefill logic
  const defaultTitle = latestReview.modified_title || recommendation.title || '';
  const defaultDescription = latestReview.modified_recommendation_text || recommendation.recommendation_text || '';
  const defaultDept = latestReview.proposed_department || recommendation.report?.department || 'Operations';
  const defaultPriority = latestReview.modified_priority || recommendation.priority_suggestion || 'MEDIUM';
  const defaultDueDate = latestReview.proposed_due_date || new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0];
  const defaultOwnerId = latestReview.proposed_owner_id || '';

  const [title, setTitle] = useState(defaultTitle);
  const [description, setDescription] = useState(defaultDescription);
  const [assignedUserId, setAssignedUserId] = useState(defaultOwnerId);
  const [department, setDepartment] = useState(defaultDept);
  const [priority, setPriority] = useState(defaultPriority);
  const [dueDate, setDueDate] = useState(defaultDueDate);
  const [initialComment, setInitialComment] = useState('');

  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const res = await adminApi.getUsers();
      const list = res.data?.data || res.data || [];
      setUsers(list.filter((u) => u.is_active));
      if (!assignedUserId && list.length > 0) {
        setAssignedUserId(list[0].id);
      }
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handlePreSubmit = (e) => {
    e.preventDefault();
    if (!assignedUserId) {
      setError('Please select an assigned user.');
      return;
    }
    if (!title.trim() || !description.trim()) {
      setError('Title and Description are required.');
      return;
    }
    setError(null);
    setShowConfirmation(true);
  };

  const handleConfirmSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        intervention_id: recommendation.id,
        assigned_user_id: parseInt(assignedUserId),
        assigned_department: department,
        title: title.trim(),
        description: description.trim(),
        priority: priority,
        due_date: dueDate,
        initial_comment: initialComment.trim() || undefined,
      };

      const response = await actionsApi.createAction(payload);
      if (onActionCreated) {
        onActionCreated(response.data?.data || response.data);
      }
      onClose();
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Failed to create action.');
      setShowConfirmation(false);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 font-bold">
              ACT
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                Create Operational Action
              </h3>
              <p className="text-xs text-slate-400">
                Convert HSE Approved Intervention into Organizational Action
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handlePreSubmit} className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center gap-3 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Source Intervention Card */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-400">Source Recommendation:</span>
              <span className="font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                {recommendation.recommendation_number}
              </span>
            </div>
            <div className="text-white font-medium">{recommendation.title}</div>
            <div className="flex flex-wrap gap-3 text-[11px] text-slate-400 pt-1">
              <span>HSE Decision: <strong className="text-emerald-400">{recommendation.status}</strong></span>
              {recommendation.report_id && <span>Report: <strong>#{recommendation.report_id}</strong></span>}
              {recommendation.barrier_category && <span>Barrier: <strong>{recommendation.barrier_category}</strong></span>}
            </div>
          </div>

          {/* Action Details */}
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Action Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500/50"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Action Description *
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500/50"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Assigned User *
                </label>
                <select
                  value={assignedUserId}
                  onChange={(e) => setAssignedUserId(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500/50"
                  required
                >
                  <option value="">-- Select Active User --</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name} ({u.role} - {u.department || 'Operations'})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Assigned Department *
                </label>
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500/50"
                  placeholder="e.g. Operations, Maintenance"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Action Priority *
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500/50"
                >
                  <option value="HIGH">HIGH Priority</option>
                  <option value="MEDIUM">MEDIUM Priority</option>
                  <option value="LOW">LOW Priority</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Operational Due Date *
                </label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500/50"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Initial Action Comment (Optional)
              </label>
              <input
                type="text"
                value={initialComment}
                onChange={(e) => setInitialComment(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-amber-500/50"
                placeholder="Add initial assignment note..."
              />
            </div>
          </div>

          {/* Footer Action Buttons */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 text-xs font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition shadow-lg shadow-amber-500/10 flex items-center gap-1.5"
            >
              Review & Create Action
            </button>
          </div>
        </form>

        {/* Confirmation Modal Overlay */}
        {showConfirmation && (
          <div className="absolute inset-0 bg-slate-950/90 backdrop-blur-sm flex items-center justify-center p-6 z-20">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full space-y-4 text-center">
              <div className="w-12 h-12 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h4 className="text-base font-bold text-white">
                Create Operational Action?
              </h4>
              <div className="text-xs text-slate-300 text-left bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                <div><strong>Title:</strong> {title}</div>
                <div><strong>Assignee:</strong> User #{assignedUserId}</div>
                <div><strong>Department:</strong> {department}</div>
                <div><strong>Priority:</strong> <span className="text-amber-400 font-bold">{priority}</span></div>
                <div><strong>Due Date:</strong> {dueDate}</div>
              </div>
              <p className="text-[11px] text-slate-400">
                This will create an organizational action. SLA monitoring and escalation will be handled separately.
              </p>
              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  onClick={() => setShowConfirmation(false)}
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl border border-slate-700 text-slate-300 text-xs font-medium hover:bg-slate-800"
                >
                  Edit Details
                </button>
                <button
                  onClick={handleConfirmSubmit}
                  disabled={submitting}
                  className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-2"
                >
                  {submitting ? 'Creating Action...' : 'Confirm Action Creation'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
