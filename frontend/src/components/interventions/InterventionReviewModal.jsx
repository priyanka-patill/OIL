import React, { useState } from 'react';
import { interventionsApi } from '../../api/interventionsApi';
import {
  X,
  CheckCircle2,
  Edit3,
  XCircle,
  AlertTriangle,
  Info,
  Sparkles,
  RefreshCw,
  Calendar,
  Building,
} from 'lucide-react';

const CATEGORY_OPTIONS = [
  'ENERGY_ISOLATION',
  'CONFINED_SPACE_CONTROL',
  'GAS_TESTING',
  'WORKING_AT_HEIGHT_CONTROL',
  'HOT_WORK_CONTROL',
  'LIFTING_CONTROL',
  'PPE_CONTROL',
  'PERMIT_CONTROL',
  'MAINTENANCE',
  'EQUIPMENT_GUARDING',
  'SUPERVISION',
  'PROCEDURE_REVIEW',
  'OTHER',
];

const PRIORITY_OPTIONS = ['HIGH', 'MEDIUM', 'LOW'];

export const InterventionReviewModal = ({ recommendation, isOpen, onClose, onReviewSubmitted }) => {
  if (!isOpen || !recommendation) return null;

  const [decision, setDecision] = useState('ACCEPT'); // ACCEPT, MODIFY, REJECT
  const [rejectionReason, setRejectionReason] = useState('');
  const [reviewComment, setReviewComment] = useState('');
  
  // Modification fields
  const [modifiedTitle, setModifiedTitle] = useState(recommendation.title || '');
  const [modifiedText, setModifiedText] = useState(recommendation.recommendation_text || '');
  const [modifiedCategory, setModifiedCategory] = useState(recommendation.category || 'OTHER');
  const [modifiedPriority, setModifiedPriority] = useState(recommendation.priority_suggestion || 'MEDIUM');
  const [proposedDept, setProposedDept] = useState(recommendation.department || '');
  const [proposedDueDate, setProposedDueDate] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (decision === 'REJECT' && !rejectionReason.trim()) {
      setError('A valid rejection reason is mandatory when rejecting an intervention recommendation.');
      return;
    }

    if (decision === 'MODIFY' && !modifiedText.trim()) {
      setError('Modified recommendation text cannot be empty.');
      return;
    }

    try {
      setIsSubmitting(true);
      const payload = {
        decision,
        rejection_reason: decision === 'REJECT' ? rejectionReason.trim() : null,
        review_comment: reviewComment.trim() || null,
        modified_title: decision === 'MODIFY' ? modifiedTitle.trim() : null,
        modified_recommendation_text: decision === 'MODIFY' ? modifiedText.trim() : null,
        modified_category: decision === 'MODIFY' ? modifiedCategory : null,
        modified_priority: decision === 'MODIFY' ? modifiedPriority : null,
        proposed_department: decision === 'MODIFY' && proposedDept ? proposedDept.trim() : null,
        proposed_due_date: decision === 'MODIFY' && proposedDueDate ? proposedDueDate.trim() : null,
      };

      const response = await interventionsApi.submitReview(recommendation.id, payload);
      if (response?.success) {
        if (onReviewSubmitted) {
          onReviewSubmitted(response.data);
        }
        onClose();
      }
    } catch (err) {
      setError(err.message || 'Failed to submit HSE review decision.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-2 text-amber-400">
            <Sparkles className="w-5 h-5" />
            <h3 className="text-sm font-extrabold tracking-wider uppercase">
              HSE Review & Validation
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-200 text-xs font-semibold flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Original AI Recommendation Preview (Immutability Display) */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-2 text-xs">
            <div className="flex items-center justify-between text-[10px] text-slate-400 border-b border-slate-800/60 pb-2">
              <span className="font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1">
                <Info className="w-3.5 h-3.5" />
                Original AI Recommendation (Preserved)
              </span>
              <span className="font-mono">Ref: {recommendation.recommendation_number}</span>
            </div>
            <div className="space-y-1">
              <h4 className="font-extrabold text-slate-100">{recommendation.title}</h4>
              <p className="text-slate-300 text-[11px] leading-relaxed bg-slate-900/60 p-3 rounded-lg border border-slate-800/60 whitespace-pre-wrap">
                {recommendation.recommendation_text}
              </p>
            </div>
            <div className="flex flex-wrap gap-2 text-[10px] pt-1">
              <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800">
                Category: <strong>{recommendation.category}</strong>
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-900 text-amber-400 border border-slate-800 font-bold">
                Suggested Priority: <strong>{recommendation.priority_suggestion}</strong>
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                Model: <strong>{recommendation.model_version}</strong>
              </span>
            </div>
          </div>

          {/* Decision Selection Toggle */}
          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-200 uppercase tracking-wider">
              Select HSE Validation Decision *
            </label>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setDecision('ACCEPT')}
                className={`p-3.5 rounded-xl border flex flex-col items-center gap-1.5 transition-all text-xs font-bold ${
                  decision === 'ACCEPT'
                    ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 ring-2 ring-emerald-500/30'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <CheckCircle2 className="w-5 h-5" />
                <span>ACCEPT</span>
              </button>

              <button
                type="button"
                onClick={() => setDecision('MODIFY')}
                className={`p-3.5 rounded-xl border flex flex-col items-center gap-1.5 transition-all text-xs font-bold ${
                  decision === 'MODIFY'
                    ? 'bg-amber-500/20 border-amber-500 text-amber-300 ring-2 ring-amber-500/30'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <Edit3 className="w-5 h-5" />
                <span>MODIFY</span>
              </button>

              <button
                type="button"
                onClick={() => setDecision('REJECT')}
                className={`p-3.5 rounded-xl border flex flex-col items-center gap-1.5 transition-all text-xs font-bold ${
                  decision === 'REJECT'
                    ? 'bg-rose-500/20 border-rose-500 text-rose-300 ring-2 ring-rose-500/30'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <XCircle className="w-5 h-5" />
                <span>REJECT</span>
              </button>
            </div>
          </div>

          {/* Form Fields: ACCEPT */}
          {decision === 'ACCEPT' && (
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-200 space-y-1">
              <p className="font-bold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Accept Recommendation without Modification</span>
              </p>
              <p className="text-[11px] text-emerald-300/80 leading-relaxed">
                You are approving this AI-suggested intervention recommendation for subsequent action planning. The original AI recommendation details remain preserved.
              </p>
            </div>
          )}

          {/* Form Fields: MODIFY */}
          {decision === 'MODIFY' && (
            <div className="space-y-4 p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 text-xs">
              <h4 className="font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5 text-[11px]">
                <Edit3 className="w-4 h-4" />
                <span>HSE Modified Recommendation Form</span>
              </h4>

              <div className="space-y-1.5">
                <label className="block font-semibold text-slate-300">Modified Title</label>
                <input
                  type="text"
                  value={modifiedTitle}
                  onChange={(e) => setModifiedTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block font-semibold text-slate-300">Modified Operational Text *</label>
                <textarea
                  rows={3}
                  value={modifiedText}
                  onChange={(e) => setModifiedText(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-amber-500"
                  required
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="block font-semibold text-slate-300">Modified Category</label>
                  <select
                    value={modifiedCategory}
                    onChange={(e) => setModifiedCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-amber-500"
                  >
                    {CATEGORY_OPTIONS.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="block font-semibold text-slate-300">Modified Priority</label>
                  <select
                    value={modifiedPriority}
                    onChange={(e) => setModifiedPriority(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-amber-500"
                  >
                    {PRIORITY_OPTIONS.map((pri) => (
                      <option key={pri} value={pri}>
                        {pri}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Action Planning Metadata (Not operational actions) */}
              <div className="pt-2 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-300 flex items-center gap-1">
                    <Building className="w-3.5 h-3.5 text-amber-400" />
                    <span>Proposed Department</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Operations, Electrical"
                    value={proposedDept}
                    onChange={(e) => setProposedDept(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="font-semibold text-slate-300 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-amber-400" />
                    <span>Proposed Due Date</span>
                  </label>
                  <input
                    type="date"
                    value={proposedDueDate}
                    onChange={(e) => setProposedDueDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-amber-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Form Fields: REJECT */}
          {decision === 'REJECT' && (
            <div className="space-y-3 p-4 rounded-xl bg-rose-950/20 border border-rose-800/40 text-xs">
              <h4 className="font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5 text-[11px]">
                <XCircle className="w-4 h-4" />
                <span>Rejection Justification *</span>
              </h4>

              <div className="space-y-1.5">
                <label className="block font-semibold text-slate-300">
                  Mandatory Rejection Reason *
                </label>
                <textarea
                  rows={3}
                  placeholder="Explain why this recommendation is being rejected (e.g. controls already verified in field, invalid premise)..."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-rose-500"
                  required
                />
              </div>
            </div>
          )}

          {/* Common HSE Reviewer Comments */}
          <div className="space-y-1.5 text-xs">
            <label className="block font-semibold text-slate-300">HSE Reviewer Audit Comments</label>
            <textarea
              rows={2}
              placeholder="Optional notes or justifications for the audit log..."
              value={reviewComment}
              onChange={(e) => setReviewComment(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-xs focus:outline-none focus:border-amber-500"
            />
          </div>

          {/* Immutability Disclaimer Footer */}
          <div className="pt-3 border-t border-slate-800 text-[10px] text-slate-400">
            <p>
              "Submitting an HSE decision records human validation. The original AI recommendation remains preserved in audit history."
            </p>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-semibold text-xs hover:bg-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`px-5 py-2 rounded-xl font-bold text-xs transition-all flex items-center gap-2 shadow-lg ${
                decision === 'ACCEPT'
                  ? 'bg-emerald-500 text-slate-950 hover:bg-emerald-400'
                  : decision === 'MODIFY'
                  ? 'bg-amber-500 text-slate-950 hover:bg-amber-400'
                  : 'bg-rose-500 text-slate-100 hover:bg-rose-400'
              }`}
            >
              {isSubmitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>{isSubmitting ? 'Submitting...' : `Confirm ${decision}`}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
