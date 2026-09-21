import React from 'react';

const TYPE_CONFIG = {
  NEAR_MISS: { label: 'Near Miss', bg: 'bg-amber-900/40 text-amber-300 border-amber-700/50' },
  UNSAFE_ACT: { label: 'Unsafe Act', bg: 'bg-orange-900/40 text-orange-300 border-orange-700/50' },
  UNSAFE_CONDITION: { label: 'Unsafe Condition', bg: 'bg-red-900/40 text-red-300 border-red-700/50' },
  INCIDENT: { label: 'Incident', bg: 'bg-rose-900/40 text-rose-300 border-rose-700/50' },
};

export const ReportTypeBadge = ({ type }) => {
  const config = TYPE_CONFIG[type] || {
    label: type || 'Report',
    bg: 'bg-slate-800 text-slate-300 border-slate-700',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${config.bg}`}
    >
      {config.label}
    </span>
  );
};
