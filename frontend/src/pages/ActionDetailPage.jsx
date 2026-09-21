import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { actionsApi } from '../api/actionsApi';
import { adminApi } from '../api/adminApi';
import { useAuth } from '../context/AuthContext';
import {
  ArrowLeft,
  Calendar,
  Building,
  User,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  MessageSquare,
  History,
  Shield,
  Tag,
  Edit3,
  UserCheck,
  RotateCcw,
  XCircle,
  FileText
} from 'lucide-react';

export const ActionDetailPage = () => {
  const { id } = useParams();
  const { user, role } = useAuth();

  const [action, setAction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Users list for reassign
  const [users, setUsers] = useState([]);

  // Modals state
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [targetStatus, setTargetStatus] = useState('');
  const [statusComment, setStatusComment] = useState('');

  const [reassignModalOpen, setReassignModalOpen] = useState(false);
  const [reassignUserId, setReassignUserId] = useState('');
  const [reassignDept, setReassignDept] = useState('');
  const [reassignComment, setReassignComment] = useState('');

  const [editPrioModalOpen, setEditPrioModalOpen] = useState(false);
  const [newPriority, setNewPriority] = useState('');

  const [editDueDateModalOpen, setEditDueDateModalOpen] = useState(false);
  const [newDueDate, setNewDueDate] = useState('');

  const [newCommentText, setNewCommentText] = useState('');

  // Part 4E Form State
  const [compComment, setCompComment] = useState('');
  const [compEvFileName, setCompEvFileName] = useState('');
  const [compEvFilePath, setCompEvFilePath] = useState('');
  const [compEvDesc, setCompEvDesc] = useState('');

  const [verifyDecision, setVerifyDecision] = useState('VERIFY');
  const [verifyComment, setVerifyComment] = useState('');
  const [recalculatingImpact, setRecalculatingImpact] = useState(false);

  const [actionSubmitting, setActionSubmitting] = useState(false);
  const [slaDetail, setSlaDetail] = useState(null);
  const [slaHistory, setSlaHistory] = useState([]);
  const [evaluatingSla, setEvaluatingSla] = useState(false);

  const handleCompletionSubmit = async (e) => {
    e.preventDefault();
    if (!compComment.trim()) return;
    setActionSubmitting(true);
    try {
      const res = await actionsApi.completeAction(id, {
        completion_comment: compComment.trim(),
        evidence_file_name: compEvFileName.trim() || undefined,
        evidence_file_path: compEvFilePath.trim() || undefined,
        evidence_description: compEvDesc.trim() || undefined
      });
      setAction(res.data?.data || res.data);
      setCompComment('');
      setCompEvFileName('');
      setCompEvFilePath('');
      setCompEvDesc('');
      alert('Action completion report submitted successfully for HSE Verification.');
      await fetchActionData();
    } catch (err) {
      alert(err.response?.data?.message || err.message || 'Action completion submission failed.');
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleVerificationSubmit = async (e) => {
    e.preventDefault();
    if (!verifyComment.trim()) return;
    setActionSubmitting(true);
    try {
      const res = await actionsApi.verifyAction(id, {
        decision: verifyDecision,
        comment: verifyComment.trim()
      });
      setAction(res.data?.data || res.data);
      setVerifyComment('');
      alert(`Action successfully ${verifyDecision === 'VERIFY' ? 'VERIFIED' : 'REOPENED'}.`);
      await fetchActionData();
    } catch (err) {
      alert(err.response?.data?.message || err.message || 'HSE Verification decision failed.');
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleRecalculateImpact = async () => {
    setRecalculatingImpact(true);
    try {
      await actionsApi.recalculateImpact(id);
      await fetchActionData();
    } catch (err) {
      alert(err.response?.data?.message || err.message || 'Failed to recalculate impact.');
    } finally {
      setRecalculatingImpact(false);
    }
  };

  useEffect(() => {
    fetchActionData();
    fetchUsersList();
  }, [id]);

  const fetchActionData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await actionsApi.getActionById(id);
      const data = res.data?.data || res.data;
      setAction(data);

      // Fetch SLA detail and history if available
      try {
        const slaRes = await actionsApi.getSlaDetail(id);
        setSlaDetail(slaRes.data?.data || slaRes.data);
      } catch (e) {
        setSlaDetail(data?.sla || null);
      }

      try {
        const histRes = await actionsApi.getSlaHistory(id);
        setSlaHistory(histRes.data?.data || histRes.data || []);
      } catch (e) {
        setSlaHistory([]);
      }
    } catch (err) {
      console.error('Failed to load action details:', err);
      setError(err.response?.data?.message || err.message || 'Action not found.');
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluateSla = async () => {
    setEvaluatingSla(true);
    try {
      await actionsApi.evaluateSla(id);
      await fetchActionData();
    } catch (err) {
      alert(err.response?.data?.message || err.message || 'Failed to re-evaluate SLA status.');
    } finally {
      setEvaluatingSla(false);
    }
  };

  const fetchUsersList = async () => {
    try {
      const res = await adminApi.getUsers();
      const list = res.data?.data || res.data || [];
      setUsers(list.filter((u) => u.is_active));
    } catch (err) {
      console.error('Failed to fetch users:', err);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
        <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
        Loading Action Details...
      </div>
    );
  }

  if (error || !action) {
    return (
      <div className="py-16 space-y-4 text-center">
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs max-w-md mx-auto flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-rose-400" />
          <span>{error || 'Action not found.'}</span>
        </div>
        <Link to="/actions/my" className="inline-flex items-center gap-1.5 text-xs text-amber-400 font-bold hover:underline">
          <ArrowLeft className="w-4 h-4" /> Back to My Actions
        </Link>
      </div>
    );
  }

  const {
    action_number,
    title,
    description,
    assigned_user_id,
    assigned_user_name,
    assigned_department,
    site,
    priority,
    due_date,
    status,
    created_by,
    creator_name,
    created_at,
    start_date,
    completion_date,
    verified_at,
    reopened_at,
    cancelled_at,
    report_id,
    intervention_id,
    pattern_id,
    barrier_id,
    evidence_snapshot = {},
    comments = [],
    history = []
  } = action;

  // Next status allowed transitions based on Rule 21 state matrix
  const validNextStatesMap = {
    APPROVED: ['ASSIGNED', 'CANCELLED'],
    ASSIGNED: ['IN_PROGRESS', 'ON_HOLD', 'CANCELLED'],
    IN_PROGRESS: ['ON_HOLD', 'COMPLETED', 'CANCELLED'],
    ON_HOLD: ['IN_PROGRESS', 'CANCELLED'],
    COMPLETED: ['VERIFICATION_PENDING', 'VERIFIED', 'REOPENED', 'CANCELLED'],
    VERIFICATION_PENDING: ['VERIFIED', 'REOPENED', 'CANCELLED'],
    VERIFIED: ['REOPENED'],
    REOPENED: ['IN_PROGRESS', 'ASSIGNED', 'CANCELLED'],
    CANCELLED: ['REOPENED']
  };

  const nextAllowed = validNextStatesMap[status] || [];

  const handleOpenStatusModal = (nextSt) => {
    setTargetStatus(nextSt);
    setStatusComment('');
    setStatusModalOpen(true);
  };

  const handleStatusSubmit = async (e) => {
    e.preventDefault();
    setActionSubmitting(true);
    try {
      const res = await actionsApi.updateStatus(id, {
        status: targetStatus,
        comment: statusComment.trim() || undefined
      });
      setAction(res.data?.data || res.data);
      setStatusModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.message || err.message || 'Status transition failed.');
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleReassignSubmit = async (e) => {
    e.preventDefault();
    if (!reassignUserId) return;
    setActionSubmitting(true);
    try {
      const res = await actionsApi.reassign(id, {
        assigned_user_id: parseInt(reassignUserId),
        assigned_department: reassignDept || undefined,
        comment: reassignComment.trim() || undefined
      });
      setAction(res.data?.data || res.data);
      setReassignModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.message || err.message || 'Reassignment failed.');
    } finally {
      setActionSubmitting(false);
    }
  };

  const handlePrioritySubmit = async (e) => {
    e.preventDefault();
    if (!newPriority) return;
    setActionSubmitting(true);
    try {
      const res = await actionsApi.updatePriority(id, { priority: newPriority });
      setAction(res.data?.data || res.data);
      setEditPrioModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.message || err.message || 'Priority update failed.');
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleDueDateSubmit = async (e) => {
    e.preventDefault();
    if (!newDueDate) return;
    setActionSubmitting(true);
    try {
      const res = await actionsApi.updateDueDate(id, { due_date: newDueDate });
      setAction(res.data?.data || res.data);
      setEditDueDateModalOpen(false);
    } catch (err) {
      alert(err.response?.data?.message || err.message || 'Due date update failed.');
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newCommentText.trim()) return;
    try {
      await actionsApi.addComment(id, { comment: newCommentText.trim() });
      setNewCommentText('');
      fetchActionData();
    } catch (err) {
      alert(err.response?.data?.message || err.message || 'Failed to add comment.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Back Link */}
      <div className="flex items-center justify-between">
        <Link to="/actions/my" className="inline-flex items-center gap-1.5 text-xs text-amber-400 font-bold hover:underline">
          <ArrowLeft className="w-4 h-4" /> Back to My Actions
        </Link>
        <div className="text-xs text-slate-500 font-mono">
          System ID: #{id}
        </div>
      </div>

      {/* Main Header Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-sm px-3 py-1 rounded-lg bg-slate-950 border border-slate-800 text-amber-400 font-bold">
                {action_number}
              </span>
              <span className="px-3 py-1 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-400 text-xs font-bold uppercase">
                {priority} Priority
              </span>
              <span className="px-3 py-1 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-bold uppercase">
                Status: {status}
              </span>
            </div>
            <h1 className="text-xl font-black text-white pt-1">
              {title}
            </h1>
          </div>

          {/* Quick Action Control Buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setReassignModalOpen(true)}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 transition border border-slate-700"
            >
              <UserCheck className="w-3.5 h-3.5 text-amber-400" />
              Reassign
            </button>
            <button
              onClick={() => { setNewPriority(priority); setEditPrioModalOpen(true); }}
              className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition border border-slate-700"
            >
              Edit Priority
            </button>
            <button
              onClick={() => { setNewDueDate(due_date); setEditDueDateModalOpen(true); }}
              className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition border border-slate-700"
            >
              Edit Due Date
            </button>
          </div>
        </div>

        {/* Action Description */}
        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
            Action Description
          </h4>
          <p className="text-sm text-slate-200 bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 leading-relaxed">
            {description}
          </p>
        </div>

        {/* Operational Lifecycle Transition Bar */}
        {nextAllowed.length > 0 && (
          <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <span className="text-xs font-bold text-white block">Status Transition Control</span>
              <span className="text-[11px] text-slate-400">Current status is <strong>{status}</strong>. Select valid next workflow state:</span>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {nextAllowed.map((st) => (
                <button
                  key={st}
                  onClick={() => handleOpenStatusModal(st)}
                  className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold transition flex items-center gap-1"
                >
                  Move to {st}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Metadata Details Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs pt-2">
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-500 block text-[11px]">Assigned User</span>
            <span className="text-slate-200 font-bold flex items-center gap-1.5 mt-0.5">
              <User className="w-3.5 h-3.5 text-amber-400" />
              {assigned_user_name || `User #${assigned_user_id}`}
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-500 block text-[11px]">Department</span>
            <span className="text-slate-200 font-bold flex items-center gap-1.5 mt-0.5">
              <Building className="w-3.5 h-3.5 text-slate-400" />
              {assigned_department || 'Operations'}
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-500 block text-[11px]">Operational Due Date</span>
            <span className="text-slate-200 font-bold flex items-center gap-1.5 mt-0.5">
              <Calendar className="w-3.5 h-3.5 text-amber-400" />
              {due_date}
            </span>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-500 block text-[11px]">Site Scope</span>
            <span className="text-slate-200 font-bold flex items-center gap-1.5 mt-0.5">
              <Shield className="w-3.5 h-3.5 text-slate-400" />
              {site}
            </span>
          </div>
        </div>
      </div>

      {/* Lifecycle Timestamps */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
          <Clock className="w-4 h-4 text-amber-400" />
          Server-Managed Lifecycle Timestamps
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
          <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-500 text-[10px] block">Created At</span>
            <span className="text-slate-300 font-medium">{created_at ? new Date(created_at).toLocaleString() : 'N/A'}</span>
          </div>
          <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-500 text-[10px] block">Work Started</span>
            <span className="text-slate-300 font-medium">{start_date ? new Date(start_date).toLocaleString() : 'Not Started'}</span>
          </div>
          <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-500 text-[10px] block">Completed At</span>
            <span className="text-slate-300 font-medium">{completion_date ? new Date(completion_date).toLocaleString() : 'Pending'}</span>
          </div>
          <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-500 text-[10px] block">Verified At</span>
            <span className="text-slate-300 font-medium">{verified_at ? new Date(verified_at).toLocaleString() : 'Not Verified'}</span>
          </div>
          <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800">
            <span className="text-slate-500 text-[10px] block">Reopened / Cancelled</span>
            <span className="text-slate-300 font-medium">
              {reopened_at ? `Reopened: ${new Date(reopened_at).toLocaleDateString()}` : cancelled_at ? `Cancelled: ${new Date(cancelled_at).toLocaleDateString()}` : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* PART 4D — SLA Monitoring & Escalation Panel */}
      {slaDetail && (
        <div className="bg-slate-900/90 border border-amber-500/30 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-widest mb-1">
                <Clock className="w-4 h-4" />
                SLA MONITORING & ESCALATION ENGINE
              </div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                SLA Status & Automated Escalations
              </h3>
            </div>
            <button
              onClick={handleEvaluateSla}
              disabled={evaluatingSla}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-bold flex items-center gap-2 transition border border-slate-700 self-start md:self-auto"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${evaluatingSla ? 'animate-spin' : ''}`} />
              Re-evaluate SLA Status
            </button>
          </div>

          {/* SLA Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-500 text-[11px] block">SLA Status</span>
              <span className="font-bold flex items-center gap-1.5">
                {slaDetail.sla_status === 'ACTIVE' && <span className="text-blue-400 font-bold uppercase">ACTIVE (On Track)</span>}
                {slaDetail.sla_status === 'DUE_SOON' && <span className="text-amber-400 font-bold uppercase animate-pulse">DUE SOON</span>}
                {slaDetail.sla_status === 'OVERDUE' && <span className="text-rose-400 font-extrabold uppercase">OVERDUE</span>}
                {slaDetail.sla_status === 'COMPLETED' && <span className="text-emerald-400 font-bold uppercase">COMPLETED</span>}
                {slaDetail.sla_status === 'CANCELLED' && <span className="text-slate-400 font-medium uppercase">CANCELLED</span>}
              </span>
            </div>

            <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-500 text-[11px] block">Countdown / Overdue</span>
              <span className="font-bold text-white">
                {slaDetail.sla_status === 'OVERDUE'
                  ? `${slaDetail.overdue_hours} hours OVERDUE`
                  : slaDetail.hours_remaining !== null
                  ? `${slaDetail.hours_remaining} hours remaining`
                  : 'N/A'}
              </span>
            </div>

            <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-500 text-[11px] block">Current Escalation Level</span>
              <span className={`font-bold ${slaDetail.current_escalation_level > 0 ? 'text-rose-400 font-extrabold' : 'text-slate-300'}`}>
                {slaDetail.current_escalation_level > 0
                  ? `Level ${slaDetail.current_escalation_level} Escalated`
                  : 'None (Level 0)'}
              </span>
            </div>

            <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-500 text-[11px] block">Completion Timing</span>
              <span className="font-bold">
                {slaDetail.completion_timing === 'COMPLETED_ON_TIME' && <span className="text-emerald-400">On Time</span>}
                {slaDetail.completion_timing === 'COMPLETED_LATE' && <span className="text-yellow-400">Late</span>}
                {slaDetail.completion_timing === 'NOT_COMPLETED' && <span className="text-slate-400 font-normal">Pending Completion</span>}
              </span>
            </div>
          </div>

          {/* SLA Timeline & Escalation Outbox History */}
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <History className="w-3.5 h-3.5 text-amber-400" />
              SLA Reminders & Escalations Outbox Timeline ({slaHistory.length})
            </h4>

            {slaHistory.length === 0 ? (
              <p className="text-xs text-slate-500 italic bg-slate-950/50 p-3 rounded-xl border border-slate-800">
                No SLA reminder or escalation outbox events generated yet.
              </p>
            ) : (
              <div className="space-y-2">
                {slaHistory.map((item, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between text-xs">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        {item.type === 'REMINDER' ? (
                          <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-bold">
                            REMINDER
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[10px] font-extrabold">
                            LEVEL {item.escalation_level} ESCALATION
                          </span>
                        )}
                        <span className="text-slate-300 font-medium">To: {item.target_role || item.recipient_role || 'Assigned User & HSE'}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-normal">{item.message || item.reason}</p>
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono shrink-0">
                      {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Source Traceability Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <FileText className="w-4 h-4 text-amber-400" />
          Upstream Source Traceability
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
            <span className="text-slate-400 font-semibold block">Originating Intervention:</span>
            <div className="font-mono text-amber-400 font-bold">Intervention #{intervention_id}</div>
            {evidence_snapshot.original_ai_title && (
              <div className="text-slate-300 text-[11px]">
                Original AI Title: <em>"{evidence_snapshot.original_ai_title}"</em>
              </div>
            )}
            {evidence_snapshot.hse_decision && (
              <div className="text-slate-300 text-[11px]">
                HSE Decision: <strong className="text-emerald-400">{evidence_snapshot.hse_decision}</strong>
              </div>
            )}
            <div className="pt-1">
              <Link to={`/interventions`} className="text-amber-400 hover:underline text-[11px] font-bold">
                View Intervention Recommendation →
              </Link>
            </div>
          </div>

          <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-2">
            <span className="text-slate-400 font-semibold block">Source Safety Precursor Report:</span>
            <div className="font-mono text-amber-400 font-bold">
              {report_id ? `Report #${report_id}` : 'General / Multi-report'}
            </div>
            {evidence_snapshot.report_number && (
              <div className="text-slate-300 text-[11px]">
                Report Number: <strong>{evidence_snapshot.report_number}</strong>
              </div>
            )}
            {barrier_id && (
              <div className="text-slate-300 text-[11px]">
                Barrier Category: <strong>{barrier_id}</strong>
              </div>
            )}
            {report_id && (
              <div className="pt-1">
                <Link to={`/reports/${report_id}`} className="text-amber-400 hover:underline text-[11px] font-bold">
                  View Precursor Safety Report →
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Assignee Action Completion Panel */}
      {(status === 'IN_PROGRESS' || status === 'REOPENED' || status === 'ASSIGNED') && (
        <div className="bg-slate-900/90 border border-amber-500/40 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-widest">
            <CheckCircle2 className="w-4 h-4" />
            ASSIGNEE ACTION COMPLETION WORKFLOW
          </div>
          <h3 className="text-base font-bold text-white">
            Mark Action Completed & Submit for HSE Verification
          </h3>
          <p className="text-xs text-slate-400">
            Submit your operational completion report and optional verification evidence. Server timestamp will be recorded.
          </p>

          <form onSubmit={handleCompletionSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1">
                Completion Comment / Work Execution Report *
              </label>
              <textarea
                value={compComment}
                onChange={(e) => setCompComment(e.target.value)}
                rows={3}
                required
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
                placeholder="Describe work completed, technical inspections passed, and gasket/equipment replacements..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Evidence File Name (Optional)</label>
                <input
                  type="text"
                  value={compEvFileName}
                  onChange={(e) => setCompEvFileName(e.target.value)}
                  placeholder="e.g. pressure_test_cert.pdf"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Evidence Path / URL (Optional)</label>
                <input
                  type="text"
                  value={compEvFilePath}
                  onChange={(e) => setCompEvFilePath(e.target.value)}
                  placeholder="e.g. /uploads/docs/cert_102.pdf"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Evidence Description (Optional)</label>
                <input
                  type="text"
                  value={compEvDesc}
                  onChange={(e) => setCompEvDesc(e.target.value)}
                  placeholder="e.g. 100 PSI hydrostatic test report"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={actionSubmitting || !compComment.trim()}
                className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-xs transition shadow-lg flex items-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4" />
                {actionSubmitting ? 'Submitting Completion...' : 'Submit Action Completion'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* HSE Verification & Reopen Panel */}
      {(status === 'VERIFICATION_PENDING' || status === 'COMPLETED') && (
        <div className="bg-slate-900/90 border border-emerald-500/40 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-widest">
            <Shield className="w-4 h-4" />
            HSE REVIEWER VERIFICATION & REOPEN PANEL
          </div>
          <h3 className="text-base font-bold text-white">
            HSE Inspection & Verification Decision
          </h3>
          <p className="text-xs text-slate-400">
            Review completed work evidence. Approve to verify action and trigger Impact Analysis, or Reopen if audit findings require further correction.
          </p>

          <form onSubmit={handleVerificationSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">HSE Verification Decision *</label>
                <select
                  value={verifyDecision}
                  onChange={(e) => setVerifyDecision(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white font-bold"
                >
                  <option value="VERIFY">VERIFY (Approve Completion & Close Action)</option>
                  <option value="REOPEN">REOPEN (Reject & Send Back to Assignee for Audit)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">
                  {verifyDecision === 'REOPEN' ? 'Mandatory Reopen Reason *' : 'HSE Verification Comment *'}
                </label>
                <input
                  type="text"
                  value={verifyComment}
                  onChange={(e) => setVerifyComment(e.target.value)}
                  required
                  placeholder={verifyDecision === 'REOPEN' ? 'State missing evidence or safety audit deficiencies...' : 'State onsite inspection findings and approval rationale...'}
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={actionSubmitting || !verifyComment.trim()}
                className={`px-5 py-2.5 rounded-xl font-extrabold text-xs transition shadow-lg flex items-center gap-2 ${
                  verifyDecision === 'REOPEN'
                    ? 'bg-rose-500 hover:bg-rose-400 text-white'
                    : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950'
                }`}
              >
                {verifyDecision === 'REOPEN' ? <RotateCcw className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                {actionSubmitting ? 'Processing Decision...' : verifyDecision === 'REOPEN' ? 'Reopen Action for Re-work' : 'Approve & Verify Action'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Multi-Cycle Completion History Timeline */}
      {action.completion_history && action.completion_history.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <History className="w-4 h-4 text-amber-400" />
            Multi-Cycle Completion & Verification Audit Trail ({action.completion_history.length})
          </h3>

          <div className="space-y-3">
            {action.completion_history.map((cycle) => (
              <div key={cycle.id} className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/30 font-bold font-mono text-[11px]">
                      Cycle #{cycle.cycle_number}
                    </span>
                    <span className={`px-2.5 py-0.5 rounded-md font-bold text-[10px] uppercase border ${
                      cycle.verification_status === 'VERIFIED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                      cycle.verification_status === 'REOPENED' ? 'bg-rose-500/10 text-rose-400 border-rose-500/30' :
                      'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'
                    }`}>
                      {cycle.verification_status}
                    </span>
                  </div>
                  <span className="text-slate-500 text-[11px]">
                    Completed: {cycle.completed_at ? new Date(cycle.completed_at).toLocaleString() : ''}
                  </span>
                </div>

                <div className="text-slate-300">
                  <strong>Completed By:</strong> {cycle.completed_by_name || `User #${cycle.completed_by}`}
                  <p className="mt-1 p-2 rounded-lg bg-slate-900/90 text-slate-200 border border-slate-800/80 italic">
                    "{cycle.completion_comment}"
                  </p>
                </div>

                {cycle.verified_at && (
                  <div className="text-emerald-300 text-[11px] pt-1">
                    <strong>Verified By:</strong> {cycle.verified_by_name} at {new Date(cycle.verified_at).toLocaleString()}
                    {cycle.verification_comment && <span className="block text-slate-400 italic">Note: "{cycle.verification_comment}"</span>}
                  </div>
                )}

                {cycle.reopened_at && (
                  <div className="text-rose-300 text-[11px] pt-1">
                    <strong>Reopened By:</strong> {cycle.reopened_by_name} at {new Date(cycle.reopened_at).toLocaleString()}
                    <p className="mt-1 p-2 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/20 italic">
                      Reopen Reason: "{cycle.reopen_reason}"
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Observational Before/After Impact Tracking Panel */}
      {action.impact_analysis && (
        <div className="bg-slate-900/90 border border-indigo-500/40 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-widest mb-1">
                <FileText className="w-4 h-4" />
                OBSERVATIONAL BEFORE/AFTER IMPACT ENGINE
              </div>
              <h3 className="text-lg font-bold text-white flex items-center gap-3">
                Precursor Recurrence & Safety Indicators Comparison
                <span className={`px-3 py-1 rounded-lg text-xs font-bold uppercase border ${
                  action.impact_analysis.data_sufficiency_status === 'SUFFICIENT'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }`}>
                  {action.impact_analysis.data_sufficiency_status}
                </span>
              </h3>
            </div>

            <button
              onClick={handleRecalculateImpact}
              disabled={recalculatingImpact}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-400 text-xs font-bold flex items-center gap-2 transition border border-slate-700 self-start md:self-auto"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${recalculatingImpact ? 'animate-spin' : ''}`} />
              Recalculate Impact
            </button>
          </div>

          {/* Observation Windows Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-slate-500 text-[11px] block font-semibold">BEFORE Observation Window (90 Days)</span>
              <span className="text-slate-200 font-mono font-bold">
                {action.impact_analysis.before_period?.start} to {action.impact_analysis.before_period?.end}
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-slate-500 text-[11px] block font-semibold">AFTER Observation Window (90 Days)</span>
              <span className="text-slate-200 font-mono font-bold">
                {action.impact_analysis.after_period?.start} to {action.impact_analysis.after_period?.end}
              </span>
            </div>
          </div>

          {/* Data Sufficiency Rationale */}
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300">
            <strong>Data Sufficiency Evaluation:</strong> {action.impact_analysis.data_sufficiency_reason}
          </div>

          {/* 5 Safety Indicators Table */}
          {action.impact_analysis.metrics && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                5 Safety Indicators Comparison Breakdown
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950 border-b border-slate-800 text-[11px] uppercase text-slate-400 font-bold">
                    <tr>
                      <th className="py-2.5 px-3">Safety Indicator</th>
                      <th className="py-2.5 px-3 text-center">Before Period</th>
                      <th className="py-2.5 px-3 text-center">After Period</th>
                      <th className="py-2.5 px-3 text-center">Observed Trend</th>
                      <th className="py-2.5 px-3">Descriptive Summary</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {/* 1. Related Report Recurrence */}
                    {action.impact_analysis.metrics.related_report_recurrence && (
                      <tr>
                        <td className="py-3 px-3 font-semibold text-white">1. Related Report Recurrence</td>
                        <td className="py-3 px-3 text-center font-mono">{action.impact_analysis.metrics.related_report_recurrence.before} reports</td>
                        <td className="py-3 px-3 text-center font-mono">{action.impact_analysis.metrics.related_report_recurrence.after} reports</td>
                        <td className="py-3 px-3 text-center font-bold">
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono ${
                            action.impact_analysis.metrics.related_report_recurrence.status === 'OBSERVED_DECREASE' ? 'bg-emerald-500/10 text-emerald-400' :
                            action.impact_analysis.metrics.related_report_recurrence.status === 'OBSERVED_INCREASE' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {action.impact_analysis.metrics.related_report_recurrence.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-400 text-[11px]">{action.impact_analysis.metrics.related_report_recurrence.description}</td>
                      </tr>
                    )}

                    {/* 2. SIF-Potential Reports */}
                    {action.impact_analysis.metrics.sif_potential_reports && (
                      <tr>
                        <td className="py-3 px-3 font-semibold text-white">2. SIF-Potential Precursors</td>
                        <td className="py-3 px-3 text-center font-mono">
                          {action.impact_analysis.metrics.sif_potential_reports.before_count} / {action.impact_analysis.metrics.sif_potential_reports.before_denominator}
                        </td>
                        <td className="py-3 px-3 text-center font-mono">
                          {action.impact_analysis.metrics.sif_potential_reports.after_count} / {action.impact_analysis.metrics.sif_potential_reports.after_denominator}
                        </td>
                        <td className="py-3 px-3 text-center font-bold">
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono ${
                            action.impact_analysis.metrics.sif_potential_reports.status === 'OBSERVED_DECREASE' ? 'bg-emerald-500/10 text-emerald-400' :
                            action.impact_analysis.metrics.sif_potential_reports.status === 'OBSERVED_INCREASE' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {action.impact_analysis.metrics.sif_potential_reports.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-400 text-[11px]">{action.impact_analysis.metrics.sif_potential_reports.description}</td>
                      </tr>
                    )}

                    {/* 3. Barrier Recurrence */}
                    {action.impact_analysis.metrics.barrier_recurrence && (
                      <tr>
                        <td className="py-3 px-3 font-semibold text-white">
                          3. Barrier Recurrence ({action.impact_analysis.metrics.barrier_recurrence.barrier_category})
                        </td>
                        <td className="py-3 px-3 text-center font-mono">{action.impact_analysis.metrics.barrier_recurrence.before} occurrences</td>
                        <td className="py-3 px-3 text-center font-mono">{action.impact_analysis.metrics.barrier_recurrence.after} occurrences</td>
                        <td className="py-3 px-3 text-center font-bold">
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono ${
                            action.impact_analysis.metrics.barrier_recurrence.status === 'OBSERVED_DECREASE' ? 'bg-emerald-500/10 text-emerald-400' :
                            action.impact_analysis.metrics.barrier_recurrence.status === 'OBSERVED_INCREASE' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {action.impact_analysis.metrics.barrier_recurrence.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-400 text-[11px]">{action.impact_analysis.metrics.barrier_recurrence.description}</td>
                      </tr>
                    )}

                    {/* 4. SIF Precursor Density */}
                    {action.impact_analysis.metrics.sif_precursor_density && (
                      <tr>
                        <td className="py-3 px-3 font-semibold text-white">4. SIF Precursor Density</td>
                        <td className="py-3 px-3 text-center font-mono">
                          {action.impact_analysis.metrics.sif_precursor_density.before_density_pct !== null
                            ? `${action.impact_analysis.metrics.sif_precursor_density.before_density_pct}%`
                            : 'N/A'}
                        </td>
                        <td className="py-3 px-3 text-center font-mono">
                          {action.impact_analysis.metrics.sif_precursor_density.after_density_pct !== null
                            ? `${action.impact_analysis.metrics.sif_precursor_density.after_density_pct}%`
                            : 'N/A'}
                        </td>
                        <td className="py-3 px-3 text-center font-bold">
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono ${
                            action.impact_analysis.metrics.sif_precursor_density.status === 'OBSERVED_DECREASE' ? 'bg-emerald-500/10 text-emerald-400' :
                            action.impact_analysis.metrics.sif_precursor_density.status === 'OBSERVED_INCREASE' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {action.impact_analysis.metrics.sif_precursor_density.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-400 text-[11px]">{action.impact_analysis.metrics.sif_precursor_density.description}</td>
                      </tr>
                    )}

                    {/* 5. Pattern Frequency */}
                    {action.impact_analysis.metrics.pattern_frequency && (
                      <tr>
                        <td className="py-3 px-3 font-semibold text-white">
                          5. Pattern Frequency ({action.impact_analysis.metrics.pattern_frequency.pattern_id})
                        </td>
                        <td className="py-3 px-3 text-center font-mono">{action.impact_analysis.metrics.pattern_frequency.before} occurrences</td>
                        <td className="py-3 px-3 text-center font-mono">{action.impact_analysis.metrics.pattern_frequency.after} occurrences</td>
                        <td className="py-3 px-3 text-center font-bold">
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-mono ${
                            action.impact_analysis.metrics.pattern_frequency.status === 'OBSERVED_DECREASE' ? 'bg-emerald-500/10 text-emerald-400' :
                            action.impact_analysis.metrics.pattern_frequency.status === 'OBSERVED_INCREASE' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {action.impact_analysis.metrics.pattern_frequency.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-400 text-[11px]">{action.impact_analysis.metrics.pattern_frequency.description}</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Non-Causal Methodological Disclaimer */}
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 italic">
            <strong>Non-Causal Methodology Disclaimer:</strong> {action.impact_analysis.metrics?.disclaimer || 'These comparisons describe observed changes between the defined before and after periods. They do not establish that the intervention caused the observed change.'}
          </div>
        </div>
      )}

      {/* Comments Thread Section */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-amber-400" />
          Action Comments & Discussion ({comments.length})
        </h3>

        {/* Add Comment Form */}
        <form onSubmit={handleAddComment} className="flex gap-3">
          <input
            type="text"
            value={newCommentText}
            onChange={(e) => setNewCommentText(e.target.value)}
            placeholder="Add operational update or note..."
            className="flex-1 px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
          />
          <button
            type="submit"
            className="px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition"
          >
            Post Comment
          </button>
        </form>

        {/* Comment Thread List */}
        <div className="space-y-3 pt-2">
          {comments.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No comments posted yet.</p>
          ) : (
            comments.map((c) => (
              <div key={c.id} className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-bold text-amber-400">{c.user_name}</span>
                  <span className="text-slate-500">{c.created_at ? new Date(c.created_at).toLocaleString() : ''}</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed">{c.comment}</p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Audit History Timeline */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <History className="w-4 h-4 text-amber-400" />
          Action Audit History ({history.length})
        </h3>

        <div className="space-y-2">
          {history.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No audit history recorded.</p>
          ) : (
            history.map((h) => (
              <div key={h.id} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
                <div className="space-y-0.5">
                  <div className="font-bold text-slate-300 font-mono text-[11px] uppercase">
                    {h.action_type}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    By <strong>{h.user_name}</strong> {h.metadata ? `• ${JSON.stringify(h.metadata)}` : ''}
                  </div>
                </div>
                <div className="text-[11px] text-slate-500 shrink-0">
                  {h.timestamp ? new Date(h.timestamp).toLocaleString() : ''}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Status Transition Modal */}
      {statusModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full space-y-4">
            <h4 className="text-base font-bold text-white">
              Confirm Status Transition to {targetStatus}
            </h4>
            <p className="text-xs text-slate-400">
              Move action {action_number} from status <strong>{status}</strong> to <strong>{targetStatus}</strong>.
            </p>
            <form onSubmit={handleStatusSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Status Transition Comment / Note
                </label>
                <textarea
                  value={statusComment}
                  onChange={(e) => setStatusComment(e.target.value)}
                  rows={3}
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500/50"
                  placeholder="Explain status change reason..."
                />
              </div>
              <div className="flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setStatusModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-700 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionSubmitting}
                  className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs"
                >
                  {actionSubmitting ? 'Updating...' : `Confirm ${targetStatus}`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reassign Modal */}
      {reassignModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full space-y-4">
            <h4 className="text-base font-bold text-white">Reassign Operational Action</h4>
            <form onSubmit={handleReassignSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Select Active User *</label>
                <select
                  value={reassignUserId}
                  onChange={(e) => setReassignUserId(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                  required
                >
                  <option value="">-- Select Active User --</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>{u.name} ({u.role} - {u.department || 'Operations'})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Department</label>
                <input
                  type="text"
                  value={reassignDept}
                  onChange={(e) => setReassignDept(e.target.value)}
                  placeholder="e.g. Operations, Maintenance"
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Reassignment Comment</label>
                <input
                  type="text"
                  value={reassignComment}
                  onChange={(e) => setReassignComment(e.target.value)}
                  placeholder="Reason for reassignment..."
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                />
              </div>
              <div className="flex items-center justify-end gap-3">
                <button type="button" onClick={() => setReassignModalOpen(false)} className="px-4 py-2 rounded-xl border border-slate-700 text-slate-300 text-xs">Cancel</button>
                <button type="submit" disabled={actionSubmitting} className="px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs">Reassign Action</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Priority Modal */}
      {editPrioModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-sm w-full space-y-4">
            <h4 className="text-base font-bold text-white">Modify Action Priority</h4>
            <form onSubmit={handlePrioritySubmit} className="space-y-4">
              <select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
              >
                <option value="HIGH">HIGH Priority</option>
                <option value="MEDIUM">MEDIUM Priority</option>
                <option value="LOW">LOW Priority</option>
              </select>
              <div className="flex items-center justify-end gap-3">
                <button type="button" onClick={() => setEditPrioModalOpen(false)} className="px-4 py-2 rounded-xl border border-slate-700 text-slate-300 text-xs">Cancel</button>
                <button type="submit" disabled={actionSubmitting} className="px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs">Save Priority</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Due Date Modal */}
      {editDueDateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-sm w-full space-y-4">
            <h4 className="text-base font-bold text-white">Modify Operational Due Date</h4>
            <form onSubmit={handleDueDateSubmit} className="space-y-4">
              <input
                type="date"
                value={newDueDate}
                onChange={(e) => setNewDueDate(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white"
                required
              />
              <div className="flex items-center justify-end gap-3">
                <button type="button" onClick={() => setEditDueDateModalOpen(false)} className="px-4 py-2 rounded-xl border border-slate-700 text-slate-300 text-xs">Cancel</button>
                <button type="submit" disabled={actionSubmitting} className="px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs">Save Due Date</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
