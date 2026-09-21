import React from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  Building,
  User,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Shield,
  Tag
} from 'lucide-react';

export const ActionCard = ({ action }) => {
  if (!action) return null;

  const {
    id,
    action_number,
    title,
    description,
    assigned_user_name,
    assigned_department,
    site,
    priority,
    due_date,
    status,
    report_id,
    intervention_id,
    created_at
  } = action;

  // Status Styling
  const statusStyles = {
    APPROVED: 'bg-blue-500/10 text-blue-400 border-blue-500/30 font-semibold',
    ASSIGNED: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30 font-semibold',
    IN_PROGRESS: 'bg-amber-500/10 text-amber-400 border-amber-500/30 font-bold',
    ON_HOLD: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30 font-semibold',
    COMPLETED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-bold',
    VERIFICATION_PENDING: 'bg-purple-500/10 text-purple-400 border-purple-500/30 font-semibold',
    VERIFIED: 'bg-teal-500/10 text-teal-400 border-teal-500/30 font-extrabold',
    REOPENED: 'bg-orange-500/10 text-orange-400 border-orange-500/30 font-bold',
    CANCELLED: 'bg-rose-500/10 text-rose-400 border-rose-500/30 font-medium line-through'
  };

  // Priority Styling
  const priorityStyles = {
    HIGH: 'bg-rose-500/10 text-rose-400 border-rose-500/20 font-bold',
    MEDIUM: 'bg-amber-500/10 text-amber-400 border-amber-500/20 font-semibold',
    LOW: 'bg-blue-500/10 text-blue-400 border-blue-500/20 font-medium'
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl hover:border-slate-700 transition flex flex-col justify-between space-y-4">
      <div className="space-y-3">
        {/* Header Badges */}
        <div className="flex items-center justify-between gap-2 flex-wrap text-xs">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-amber-400 font-bold">
              {action_number}
            </span>
            <span className={`px-2.5 py-1 rounded-lg border text-[11px] uppercase tracking-wider ${priorityStyles[priority] || priorityStyles.MEDIUM}`}>
              {priority} Priority
            </span>
          </div>

          <span className={`px-2.5 py-1 rounded-lg border text-[11px] uppercase tracking-wider ${statusStyles[status] || statusStyles.ASSIGNED}`}>
            {status}
          </span>
        </div>

        {/* Title & Description */}
        <div>
          <h3 className="text-base font-bold text-white line-clamp-2 leading-snug">
            {title}
          </h3>
          <p className="text-xs text-slate-400 line-clamp-2 mt-1.5 leading-relaxed">
            {description}
          </p>
        </div>

        {/* Meta Info Grid */}
        <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-800/80 text-slate-400">
          <div className="flex items-center gap-1.5 truncate">
            <User className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="truncate">{assigned_user_name || 'Unassigned'}</span>
          </div>
          <div className="flex items-center gap-1.5 truncate">
            <Building className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="truncate">{assigned_department || 'Operations'}</span>
          </div>
          <div className="flex items-center gap-1.5 truncate">
            <Calendar className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span>Due: <strong>{due_date}</strong></span>
          </div>
          <div className="flex items-center gap-1.5 truncate">
            <Shield className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="truncate">{site}</span>
          </div>
        </div>
      </div>

        {/* SLA Status & Countdown Banner */}
        {action.sla && (
          <div className="flex items-center justify-between gap-2 text-xs pt-1">
            <div className="flex items-center gap-1.5 flex-wrap">
              {action.sla.sla_status === 'ACTIVE' && (
                <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] font-semibold flex items-center gap-1">
                  <Clock className="w-3 h-3 text-blue-400" />
                  SLA Active ({action.sla.hours_remaining !== null ? `${action.sla.hours_remaining}h left` : 'On Track'})
                </span>
              )}
              {action.sla.sla_status === 'DUE_SOON' && (
                <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-bold flex items-center gap-1 animate-pulse">
                  <AlertTriangle className="w-3 h-3 text-amber-400" />
                  Due Soon ({action.sla.hours_remaining}h left)
                </span>
              )}
              {action.sla.sla_status === 'OVERDUE' && (
                <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[10px] font-bold flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-rose-400" />
                  OVERDUE ({action.sla.overdue_hours}h overdue)
                </span>
              )}
              {action.sla.sla_status === 'COMPLETED' && (
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 ${
                  action.sla.completion_timing === 'COMPLETED_ON_TIME'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
                }`}>
                  <CheckCircle2 className="w-3 h-3" />
                  {action.sla.completion_timing === 'COMPLETED_ON_TIME' ? 'Completed On Time' : 'Completed Late'}
                </span>
              )}

              {/* Escalation Level Badge */}
              {action.sla.current_escalation_level > 0 && (
                <span className="px-2 py-0.5 rounded bg-rose-950/80 text-rose-300 border border-rose-500/40 text-[10px] font-extrabold flex items-center gap-1">
                  <Tag className="w-3 h-3 text-rose-400" />
                  L{action.sla.current_escalation_level} Escalated
                </span>
              )}
            </div>
          </div>
        )}

        {/* Footer Link */}
        <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            {report_id && <span>Report #{report_id}</span>}
            {intervention_id && <span>• Interv #{intervention_id}</span>}
          </div>
          <Link
            to={`/actions/${id}`}
            className="inline-flex items-center gap-1 text-xs font-bold text-amber-400 hover:text-amber-300 transition"
          >
            View Action Details
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    );
  };
