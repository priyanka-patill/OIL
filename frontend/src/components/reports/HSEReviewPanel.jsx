import React, { useState } from 'react';
import { CheckCircle2, XCircle, Edit3, MessageSquare, AlertCircle, ShieldCheck, UserCheck } from 'lucide-react';

export const HSEReviewPanel = ({ report, onSubmitReview, isSubmitting }) => {
  const [decision, setDecision] = useState('ACCEPTED');
  const [comment, setComment] = useState('');
  const [modifiedClassification, setModifiedClassification] = useState(0);
  const [validationError, setValidationError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setValidationError('');

    if (decision === 'REJECTED' && !comment.trim()) {
      setValidationError('Please provide a mandatory review comment explaining the rejection decision.');
      return;
    }

    onSubmitReview({
      ai_prediction_accepted: decision === 'ACCEPTED',
      hse_decision: decision,
      modified_classification: decision === 'MODIFIED' ? parseInt(modifiedClassification, 10) : null,
      review_comment: comment.trim() || (decision === 'ACCEPTED' ? 'Validated by HSE Manager' : 'Reviewed by HSE Manager'),
    });
  };

  const isAlreadyValidated = report.status === 'HSE_VALIDATED' || report.status === 'REJECTED';

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <UserCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">HSE Human Validation Workflow</h3>
            <p className="text-xs text-slate-400">Human-in-the-loop review decision boundary</p>
          </div>
        </div>

        <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-950 text-slate-300 border border-slate-800">
          Status: {report.status}
        </span>
      </div>

      {validationError && (
        <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      {/* Visual Distinction Banner */}
      <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-slate-300">
            AI analysis provides decision support. Professional HSE validation is authoritative.
          </span>
        </div>
      </div>

      {/* Review Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            HSE Review Decision *
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button
              type="button"
              onClick={() => setDecision('ACCEPTED')}
              className={`p-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                decision === 'ACCEPTED'
                  ? 'bg-emerald-950/80 text-emerald-300 border-emerald-600 shadow-lg shadow-emerald-950/50 ring-1 ring-emerald-500'
                  : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:border-slate-700'
              }`}
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Accept AI Prediction</span>
            </button>

            <button
              type="button"
              onClick={() => setDecision('MODIFIED')}
              className={`p-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                decision === 'MODIFIED'
                  ? 'bg-amber-950/80 text-amber-300 border-amber-600 shadow-lg shadow-amber-950/50 ring-1 ring-amber-500'
                  : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:border-slate-700'
              }`}
            >
              <Edit3 className="w-4 h-4 text-amber-400" />
              <span>Modify Decision</span>
            </button>

            <button
              type="button"
              onClick={() => setDecision('REJECTED')}
              className={`p-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                decision === 'REJECTED'
                  ? 'bg-rose-950/80 text-rose-300 border-rose-600 shadow-lg shadow-rose-950/50 ring-1 ring-rose-500'
                  : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:border-slate-700'
              }`}
            >
              <XCircle className="w-4 h-4 text-rose-400" />
              <span>Reject Analysis</span>
            </button>
          </div>
        </div>

        {decision === 'MODIFIED' && (
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
            <label className="block text-xs font-semibold text-amber-300">
              Select Modified HSE Classification
            </label>
            <select
              value={modifiedClassification}
              onChange={(e) => setModifiedClassification(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-amber-500"
            >
              <option value={0}>0 — Non-SIF Observation</option>
              <option value={1}>1 — SIF-Potential Precursor</option>
            </select>
          </div>
        )}

        <div>
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
            HSE Validation Comment {decision === 'REJECTED' && <span className="text-rose-400">*</span>}
          </label>
          <textarea
            rows={3}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={
              decision === 'REJECTED'
                ? 'Mandatory: Enter technical justification for rejecting AI analysis...'
                : 'Enter optional manager review notes or corrective action plan details...'
            }
            className="w-full p-3 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 px-4 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-950 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 transition-all shadow-lg shadow-emerald-500/20"
        >
          {isSubmitting ? 'Recording HSE Validation...' : 'Submit HSE Validation Decision'}
        </button>
      </form>
    </div>
  );
};
