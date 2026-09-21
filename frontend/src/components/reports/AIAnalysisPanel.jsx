import React from 'react';
import { Cpu, ShieldAlert, Sparkles, AlertTriangle, Info, CheckCircle2, Shield, Flame, Activity } from 'lucide-react';

export const AIAnalysisPanel = ({ analysis = null, onAnalyze = null, isAnalyzing = false }) => {
  if (!analysis) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold text-slate-100">AI Safety Intelligence Panel</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700">
                  AI Model Connected
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Run AI model engine to extract SIF risk probability, n-gram feature contributions, Life-Saving Rules, hazards & barrier concerns.
              </p>
            </div>
          </div>

          {onAnalyze && (
            <button
              onClick={onAnalyze}
              disabled={isAnalyzing}
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-950 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 transition-all shadow-lg shadow-amber-500/20 shrink-0"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isAnalyzing ? 'Executing AI Model...' : 'Analyze Safety Report'}</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  // Parse JSON data cleanly
  let explanationData = { explanation: [], human_readable: '', disclaimer: '' };
  try {
    explanationData = typeof analysis.explanation_json === 'string'
      ? JSON.parse(analysis.explanation_json)
      : (analysis.explanation_json || explanationData);
  } catch {}

  let lsrList = [];
  try {
    lsrList = typeof analysis.life_saving_rules_json === 'string'
      ? JSON.parse(analysis.life_saving_rules_json)
      : (analysis.life_saving_rules_json || []);
  } catch {}

  let hazardsList = [];
  try {
    hazardsList = typeof analysis.hazards_json === 'string'
      ? JSON.parse(analysis.hazards_json)
      : (analysis.hazards_json || []);
  } catch {}

  let barrierList = [];
  try {
    barrierList = typeof analysis.barrier_concerns_json === 'string'
      ? JSON.parse(analysis.barrier_concerns_json)
      : (analysis.barrier_concerns_json || []);
  } catch {}

  let similarReportsList = [];
  try {
    similarReportsList = typeof analysis.similar_reports_json === 'string'
      ? JSON.parse(analysis.similar_reports_json)
      : (analysis.similar_reports_json || []);
  } catch {}

  let riskExplanationList = [];
  try {
    riskExplanationList = typeof analysis.risk_explanation_json === 'string'
      ? JSON.parse(analysis.risk_explanation_json)
      : (analysis.risk_explanation_json || []);
  } catch {}

  const isSIF = analysis.classification === 1 || analysis.prediction === 'SIF-Potential';
  const prob = (analysis.probability_or_score * 100).toFixed(1);
  const thresh = (analysis.threshold * 100).toFixed(0);
  const calculatedRisk = (analysis.risk_level || 'MEDIUM').toUpperCase();
  const similarCount = analysis.previous_similar_reports_count ?? 0;

  const riskBadgeStyles = {
    CRITICAL: 'bg-rose-950/80 text-rose-300 border-rose-700 animate-pulse',
    HIGH: 'bg-amber-950/80 text-amber-300 border-amber-700',
    MEDIUM: 'bg-sky-950/80 text-sky-300 border-sky-700',
    LOW: 'bg-emerald-950/80 text-emerald-300 border-emerald-700',
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-100">Automated Safety Intelligence Analysis</h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-amber-500/10 text-amber-400 border border-amber-500/20">
                {analysis.model_version || 'sif_model_v1'}
              </span>
            </div>
            <p className="text-xs text-slate-400">System Analysis Executed & Persisted</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={`px-3.5 py-1.5 rounded-full text-xs font-extrabold tracking-wider border shadow-md ${
              isSIF
                ? 'bg-rose-950/80 text-rose-300 border-rose-700/80 animate-pulse'
                : 'bg-emerald-950/80 text-emerald-300 border-emerald-700/80'
            }`}
          >
            {analysis.prediction || (isSIF ? 'SIF-Potential' : 'Non-SIF')}
          </span>

          {onAnalyze && (
            <button
              onClick={onAnalyze}
              disabled={isAnalyzing}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-semibold"
              title="Re-run AI Analysis"
            >
              <Sparkles className="w-4 h-4 text-amber-400" />
            </button>
          )}
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: SIF Risk Probability */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            SIF Risk Probability
          </span>
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold ${isSIF ? 'text-rose-400' : 'text-emerald-400'}`}>
              {prob}%
            </span>
            <span className="text-xs text-slate-500">Cutoff {thresh}%</span>
          </div>
          <div className="w-full h-1.5 bg-slate-900 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full ${isSIF ? 'bg-rose-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(prob, 100)}%` }}
            />
          </div>
        </div>

        {/* Metric 2: Calculated Risk Level */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Calculated Risk Level
          </span>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`px-3 py-1 rounded-lg text-xs font-black uppercase tracking-wider border ${
                riskBadgeStyles[calculatedRisk] || riskBadgeStyles.MEDIUM
              }`}
            >
              {calculatedRisk} RISK
            </span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1.5">
            Methodology: {analysis.risk_methodology_version || 'RISK_EVAL_v1'}
          </p>
        </div>

        {/* Metric 3: Previous Similar Reports */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Previous Similar Reports
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-amber-400">{similarCount}</span>
            <span className="text-xs text-slate-400">Historical Matches</span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">
            {similarCount > 0 ? `${similarCount} similar report(s) identified` : 'No similar reports found'}
          </p>
        </div>

        {/* Metric 4: Analysis Status */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            System Analysis Status
          </span>
          <div className="flex items-center gap-2 mt-1">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span className="text-base font-bold text-slate-200">{analysis.analysis_status}</span>
          </div>
          <p className="text-[10px] text-slate-400 mt-1">Persisted in database</p>
        </div>
      </div>

      {/* SYSTEM RISK ASSESSMENT EVIDENCE BREAKDOWN */}
      {riskExplanationList.length > 0 && (
        <div className="space-y-3 pt-2 border-t border-slate-800/80">
          <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            <span>System Risk Level Assessment Breakdown ({calculatedRisk} RISK)</span>
          </h4>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
            <ul className="space-y-2 text-xs text-slate-200">
              {riskExplanationList.map((bullet, idx) => (
                <li key={idx} className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-900/60 border border-slate-800/60">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0 mt-1.5" />
                  <span className="font-medium text-slate-300">{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* PREVIOUS SIMILAR REPORTS DETAILED BREAKDOWN */}
      <div className="space-y-3 pt-2 border-t border-slate-800/80">
        <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
          <Activity className="w-4 h-4" />
          <span>Previous Similar Reports Analysis ({similarCount} Identified)</span>
        </h4>

        {similarReportsList.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {similarReportsList.map((sim, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-amber-400">{sim.report_number}</span>
                  {sim.similarity_score != null && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      Match: {(sim.similarity_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-400 space-y-0.5">
                  <p><strong className="text-slate-300">Date:</strong> {sim.date || 'N/A'} | <strong className="text-slate-300">Unit:</strong> {sim.refinery_unit || 'N/A'}</p>
                  <p><strong className="text-slate-300">Tag:</strong> {sim.equipment_id || 'N/A'} | <strong className="text-slate-300">Activity:</strong> {sim.activity || 'N/A'}</p>
                </div>
                {sim.description_snippet && (
                  <p className="text-[11px] text-slate-300 bg-slate-900/60 p-2 rounded border border-slate-800 line-clamp-2">
                    "{sim.description_snippet}"
                  </p>
                )}
                {sim.evidence_explanation && (
                  <p className="text-[10px] font-mono text-amber-400/90">
                    Evidence: {sim.evidence_explanation}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-400 italic">
            No similar historical reports detected in safety database matching this observation.
          </div>
        )}
      </div>

      {/* TF-IDF Feature Contributions */}
      {explanationData.explanation && explanationData.explanation.length > 0 && (
        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            <span>Key NLP Terms Driving Model Prediction</span>
          </h4>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
            {explanationData.human_readable && (
              <p className="text-xs font-semibold text-amber-200/90 bg-amber-950/30 p-2.5 rounded-lg border border-amber-900/40">
                {explanationData.human_readable}
              </p>
            )}

            <div className="space-y-2">
              {explanationData.explanation.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-900/60 border border-slate-800/60">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-amber-400">"{item.feature}"</span>
                  </div>
                  <div className="flex items-center gap-3 font-mono">
                    <span className="text-slate-400 text-[11px]">Weight: {item.weight}</span>
                    <span className={`font-bold px-2 py-0.5 rounded text-[11px] ${item.contribution > 0 ? 'bg-rose-950/60 text-rose-300 border border-rose-800/40' : 'bg-slate-800 text-slate-300'}`}>
                      Contrib: +{item.contribution}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Mapped Analysis Grid (LSR, Hazards, Barriers) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        {/* Potentially Relevant Life-Saving Rules */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
          <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-amber-400" />
            <span>Potentially Relevant Life-Saving Rules</span>
          </h4>
          {lsrList.length > 0 ? (
            <ul className="space-y-1.5 text-xs text-slate-200">
              {lsrList.map((rule, idx) => (
                <li key={idx} className="flex items-center gap-2 p-1.5 rounded bg-slate-900/60 border border-slate-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  <span className="font-medium">{rule}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-500 italic">No specific Life-Saving Rule triggered.</p>
          )}
        </div>

        {/* Potential Hazards */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
          <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
            <Flame className="w-4 h-4 text-rose-400" />
            <span>Potential Hazards Identified</span>
          </h4>
          {hazardsList.length > 0 ? (
            <ul className="space-y-1.5 text-xs text-slate-200">
              {hazardsList.map((haz, idx) => (
                <li key={idx} className="flex items-center gap-2 p-1.5 rounded bg-slate-900/60 border border-slate-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                  <span className="font-medium">{haz}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-500 italic">No specific hazards identified.</p>
          )}
        </div>

        {/* Potential Barrier Concerns */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
          <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-amber-400" />
            <span>Potential Barrier Concerns</span>
          </h4>
          {barrierList.length > 0 ? (
            <ul className="space-y-1.5 text-xs text-slate-200">
              {barrierList.map((bar, idx) => (
                <li key={idx} className="flex items-center gap-2 p-1.5 rounded bg-slate-900/60 border border-slate-800">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  <span className="font-medium">{bar}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-500 italic">No specific barrier concerns detected.</p>
          )}
        </div>
      </div>

      {/* Safety Context Disclaimer */}
      <div className="flex items-center gap-2 p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400">
        <Info className="w-4 h-4 text-slate-500 shrink-0" />
        <span>
          {explanationData.disclaimer || "AI analysis is decision-support intelligence and requires qualified HSE professional validation."}
        </span>
      </div>
    </div>
  );
};
