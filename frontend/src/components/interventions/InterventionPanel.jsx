import React, { useState, useEffect } from 'react';
import { interventionsApi } from '../../api/interventionsApi';
import { InterventionCard } from './InterventionCard';
import { Sparkles, RefreshCw, ShieldCheck, AlertCircle } from 'lucide-react';

export const InterventionPanel = ({ reportId }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');

  const fetchRecommendations = async () => {
    if (!reportId) return;
    try {
      setIsLoading(true);
      setError('');
      const response = await interventionsApi.getInterventionsForReport(reportId);
      if (response?.data) {
        setRecommendations(response.data);
      }
    } catch (err) {
      setError(err.message || 'Failed to load intervention recommendations.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [reportId]);

  const handleGenerate = async () => {
    try {
      setIsGenerating(true);
      setError('');
      const response = await interventionsApi.generateIntervention(reportId);
      if (response?.success) {
        await fetchRecommendations();
      }
    } catch (err) {
      setError(err.message || 'Failed to generate intervention recommendation.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>AI-Suggested Intervention Recommendations</span>
          </h3>
          <p className="text-[11px] text-slate-400 mt-1">
            Evidence-based recommendations derived from safety report data and cross-report intelligence.
          </p>
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs hover:bg-amber-400 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
          <span>{isGenerating ? 'Generating...' : 'Generate AI Recommendation'}</span>
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-200 text-xs font-semibold flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="py-8 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
          <span>Checking database for intervention recommendations...</span>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="p-6 rounded-xl bg-slate-950/40 border border-slate-800 text-center space-y-2">
          <ShieldCheck className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-xs text-slate-300 font-semibold">No Intervention Recommendations Generated Yet</p>
          <p className="text-[11px] text-slate-500 max-w-md mx-auto">
            Click "Generate AI Recommendation" to convert report safety findings and barrier evidence into structured, evidence-backed intervention suggestions for HSE validation.
          </p>
        </div>
      ) : (
        <div className="space-y-4 pt-2">
          {recommendations.map((rec) => (
            <InterventionCard key={rec.id} recommendation={rec} />
          ))}
        </div>
      )}
    </div>
  );
};
