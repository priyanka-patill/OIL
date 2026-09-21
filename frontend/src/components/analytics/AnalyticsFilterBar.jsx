import React from 'react';
import { Filter, RotateCcw, Calendar, MapPin, Building, Activity, Wrench, Shield, AlertTriangle } from 'lucide-react';

export const DATE_PRESETS = [
  { label: 'Last 7 Days', value: '7d' },
  { label: 'Last 30 Days', value: '30d' },
  { label: 'Last 90 Days', value: '90d' },
  { label: 'Last 6 Months', value: '6m' },
  { label: 'Last 12 Months', value: '12m' },
  { label: 'Custom Range', value: 'custom' },
];

export const SITES = ['Digboi Refinery', 'Guwahati Refinery', 'Bongaigaon Refinery', 'Duliajan HQ', 'Jorhat Field Office'];
export const DEPARTMENTS = ['Maintenance', 'Operations', 'Safety', 'Inspection', 'Electrical', 'Instrumentation', 'Logistics'];
export const ACTIVITIES = ['Hot Work', 'Confined Space Entry', 'Height Work', 'Equipment Maintenance', 'Electrical Isolation', 'Lifting Operations', 'Pipe Flange Break'];
export const BARRIERS = ['Energy Isolation', 'Permit to Work', 'Atmospheric Testing', 'Personal Protective Equipment', 'Barrier & Barricading', 'Bypass & Override Controls', 'Gas Detection System'];
export const SIF_CLASSES = ['SIF-Potential', 'Non-SIF-Potential'];

export const AnalyticsFilterBar = ({ filters, onFilterChange, onReset }) => {
  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-amber-400" />
          <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
            Global Analytics Filters
          </h2>
        </div>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-all border border-slate-700/60"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Filters</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-3">
        {/* Date Preset */}
        <div>
          <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
            Date Range
          </label>
          <select
            value={filters.date_preset || '90d'}
            onChange={(e) => handleChange('date_preset', e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500/60"
          >
            {DATE_PRESETS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        {/* Custom Start / End Dates if custom preset */}
        {filters.date_preset === 'custom' && (
          <>
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={filters.start_date || ''}
                onChange={(e) => handleChange('start_date', e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500/60"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                End Date
              </label>
              <input
                type="date"
                value={filters.end_date || ''}
                onChange={(e) => handleChange('end_date', e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500/60"
              />
            </div>
          </>
        )}

        {/* Site Filter */}
        <div>
          <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
            Site / Location
          </label>
          <select
            value={filters.site || ''}
            onChange={(e) => handleChange('site', e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500/60"
          >
            <option value="">All Sites</option>
            {SITES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Department Filter */}
        <div>
          <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
            Department
          </label>
          <select
            value={filters.department || ''}
            onChange={(e) => handleChange('department', e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500/60"
          >
            <option value="">All Departments</option>
            {DEPARTMENTS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        {/* Activity Filter */}
        <div>
          <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
            Activity / Work Type
          </label>
          <select
            value={filters.work_type || ''}
            onChange={(e) => handleChange('work_type', e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500/60"
          >
            <option value="">All Activities</option>
            {ACTIVITIES.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>

        {/* Barrier Filter */}
        <div>
          <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
            Safety Barrier
          </label>
          <select
            value={filters.barrier || ''}
            onChange={(e) => handleChange('barrier', e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500/60"
          >
            <option value="">All Barriers</option>
            {BARRIERS.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </div>

        {/* SIF Classification Filter */}
        <div>
          <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
            SIF Classification
          </label>
          <select
            value={filters.sif_class || ''}
            onChange={(e) => handleChange('sif_class', e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500/60"
          >
            <option value="">All Classifications</option>
            {SIF_CLASSES.map((sc) => (
              <option key={sc} value={sc}>
                {sc}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};
