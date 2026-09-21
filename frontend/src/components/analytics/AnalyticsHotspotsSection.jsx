import React, { useState, useEffect } from 'react';
import { MapPin, Building2, Wrench, Activity, Users, Flame, Info, AlertCircle } from 'lucide-react';
import { analyticsApi } from '../../api/analyticsApi';

export const DIMENSIONS = [
  { key: 'sites', label: 'Sites & Installations', icon: Building2, param: 'site' },
  { key: 'activities', label: 'Activities & Work Types', icon: Activity, param: 'activity' },
  { key: 'equipment', label: 'Equipment & Assets', icon: Wrench, param: 'equipment_id' },
  { key: 'locations', label: 'Locations & Units', icon: MapPin, param: 'location' },
  { key: 'departments', label: 'Departments', icon: Users, param: 'department' },
];

export const AnalyticsHotspotsSection = ({ filters, isLoading: parentLoading }) => {
  const [activeTab, setActiveTab] = useState('sites');
  const [dimensionData, setDimensionData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDimension = async () => {
      try {
        setIsLoading(true);
        setError(null);
        let res;
        if (activeTab === 'sites') res = await analyticsApi.getDimensionAnalytics('sites', filters);
        else if (activeTab === 'activities') res = await analyticsApi.getDimensionAnalytics('activities', filters);
        else if (activeTab === 'equipment') res = await analyticsApi.getDimensionAnalytics('equipment', filters);
        else if (activeTab === 'locations') res = await analyticsApi.getDimensionAnalytics('locations', filters);
        else if (activeTab === 'departments') res = await analyticsApi.getDimensionAnalytics('departments', filters);

        if (res?.data) {
          // Backend returns dimension dictionary or list under dimension name
          const items = res.data[activeTab] || res.data.items || res.data.results || [];
          setDimensionData(Array.isArray(items) ? items : Object.values(items));
        } else {
          setDimensionData([]);
        }
      } catch (err) {
        console.error('Failed to load dimension hotspots:', err);
        setError('Failed to load dimension analytical profiles');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDimension();
  }, [activeTab, filters]);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Flame className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              Dimensional Concentration & Hotspot Analysis
            </h2>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Objective concentration analysis across operational dimensions. Neutral descriptive metrics only.
          </p>
        </div>

        {/* Dimension Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto p-1 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-semibold">
          {DIMENSIONS.map((dim) => {
            const Icon = dim.icon;
            const isActive = activeTab === dim.key;
            return (
              <button
                key={dim.key}
                onClick={() => setActiveTab(dim.key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{dim.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {isLoading || parentLoading ? (
        <div className="p-8 text-center text-slate-500 text-xs animate-pulse">
          Loading dimensional analytical profile from backend...
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
          {error}
        </div>
      ) : dimensionData.length === 0 ? (
        <div className="p-8 text-center text-slate-400 space-y-2">
          <Info className="w-8 h-8 mx-auto text-slate-600" />
          <p className="text-xs font-semibold">No entries found for active filters.</p>
          <p className="text-[11px] text-slate-500">
            Adjust global filter parameters to view dimensional analytics.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 font-bold border-b border-slate-800 uppercase text-[10px]">
              <tr>
                <th className="p-3">Entity Name</th>
                <th className="p-3">Total Reports</th>
                <th className="p-3">Analyzed Reports</th>
                <th className="p-3">SIF-Potential Count</th>
                <th className="p-3">SIF Precursor Density</th>
                <th className="p-3">Recurring Patterns</th>
                <th className="p-3">Barrier Concerns</th>
                <th className="p-3">Sufficiency Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {dimensionData.map((item, idx) => {
                const name = item.name || item.entity_id || item.site || item.activity || item.department || item.location || 'Unspecified';
                const total = item.total_reports || item.report_count || 0;
                const analyzed = item.analyzed_reports ?? total;
                const sifCount = item.sif_potential_count ?? item.sif_count ?? 0;
                const density = item.sif_precursor_density !== undefined
                  ? (item.sif_precursor_density * 100).toFixed(1)
                  : analyzed > 0 ? ((sifCount / analyzed) * 100).toFixed(1) : '0.0';
                const patterns = item.recurring_patterns_count ?? item.patterns_count ?? 0;
                const barriers = item.recurring_barriers_count ?? item.barriers_count ?? 0;

                const isLowSample = analyzed < 5;

                return (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 font-semibold text-slate-100 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />
                      <span className="truncate max-w-[200px]">{name}</span>
                    </td>
                    <td className="p-3">{total}</td>
                    <td className="p-3">{analyzed}</td>
                    <td className="p-3 font-bold text-amber-400">{sifCount}</td>
                    <td className="p-3 font-bold text-purple-400">
                      {isLowSample ? (
                        <span className="text-slate-500 font-normal italic">Insufficient Data</span>
                      ) : (
                        `${density}%`
                      )}
                    </td>
                    <td className="p-3">{patterns}</td>
                    <td className="p-3">{barriers}</td>
                    <td className="p-3">
                      {isLowSample ? (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                          Low Sample Size (&lt;5)
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                          Sufficient Data
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
