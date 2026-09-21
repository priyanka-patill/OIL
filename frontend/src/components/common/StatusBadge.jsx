import React from 'react';

const STATUS_CONFIG = {
  DRAFT: { label: 'Draft', bg: 'bg-slate-700/60', text: 'text-slate-300', border: 'border-slate-600' },
  SUBMITTED: { label: 'Submitted', bg: 'bg-blue-950/60', text: 'text-blue-400', border: 'border-blue-800' },
  AI_ANALYZED: { label: 'AI Analyzed', bg: 'bg-indigo-950/60', text: 'text-indigo-400', border: 'border-indigo-800' },
  HSE_REVIEW_PENDING: { label: 'Pending Review', bg: 'bg-amber-950/60', text: 'text-amber-400', border: 'border-amber-800' },
  HSE_VALIDATED: { label: 'HSE Validated', bg: 'bg-emerald-950/60', text: 'text-emerald-400', border: 'border-emerald-800' },
  ACTION_REQUIRED: { label: 'Action Required', bg: 'bg-rose-950/60', text: 'text-rose-400', border: 'border-rose-800' },
  REJECTED: { label: 'Rejected', bg: 'bg-red-950/60', text: 'text-red-400', border: 'border-red-800' },
  CLOSED: { label: 'Closed', bg: 'bg-slate-800/60', text: 'text-slate-400', border: 'border-slate-700' },
};

export const StatusBadge = ({ status }) => {
  const config = STATUS_CONFIG[status] || {
    label: status || 'Unknown',
    bg: 'bg-slate-800',
    text: 'text-slate-400',
    border: 'border-slate-700',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.bg} ${config.text} ${config.border}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-75"></span>
      {config.label}
    </span>
  );
};
