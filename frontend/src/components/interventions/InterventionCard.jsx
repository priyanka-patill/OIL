import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { InterventionReviewModal } from './InterventionReviewModal';
import { ActionCreateModal } from '../actions/ActionCreateModal';
import {
  Sparkles,
  Info,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Edit3,
  XCircle,
  Clock,
  Building,
  Calendar,
  UserCheck,
  PlusCircle,
} from 'lucide-react';

export const InterventionCard = ({ recommendation, onRecommendationUpdated }) => {
  const { role } = useAuth();
  const [showEvidence, setShowEvidence] = useState(false);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [isActionModalOpen, setIsActionModalOpen] = useState(false);
  const [recData, setRecData] = useState(recommendation);

  if (!recData) return null;

  const {
    recommendation_number,
    title,
    category,
    recommendation_text,
    rationale,
    priority_suggestion,
    evidence_summary,
    sif_classification,
    hazards,
    life_saving_rules,
    bdi_score,
    escalation_indicators,
    model_version,
    methodology_version,
    status,
    latest_review,
    validation_notice,
  } = recData;

  const canReview = role === 'HSE_MANAGER' || role === 'ADMIN' || role === 'HSE_USER';

  // Priority color styling
  const priorityStyles = {
    HIGH: 'bg-rose-500/10 text-rose-400 border-rose-500/20 font-bold',
    MEDIUM: 'bg-amber-500/10 text-amber-400 border-amber-500/20 font-bold',
    LOW: 'bg-blue-500/10 text-blue-400 border-blue-500/20 font-medium',
    INSUFFICIENT_DATA: 'bg-slate-800 text-slate-400 border-slate-700 font-medium',
  };

  // Status color styling
  const statusStyles = {
    PENDING_HSE_VALIDATION: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    ACCEPTED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-bold',
    MODIFIED: 'bg-purple-500/10 text-purple-400 border-purple-500/30 font-bold',
    REJECTED: 'bg-rose-500/10 text-rose-400 border-rose-500/30 font-bold',
  };

  const handleReviewSubmitted = (updatedResult) => {
    if (updatedResult?.intervention) {
      setRecData(updatedResult.intervention);
    }
    if (onRecommendationUpdated) {
      onRecommendationUpdated(updatedResult);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 relative">
      {/* Top Banner: Mandatory HSE Validation Notice & Status */}
      <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 font-extrabold uppercase tracking-wider text-amber-400">
          <Sparkles className="w-4 h-4 shrink-0 text-amber-400" />
          <span>{validation_notice || 'AI-Suggested Intervention — HSE Validation Required'}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] uppercase tracking-wider px-2.5 py-0.5 rounded border ${statusStyles[status] || statusStyles.PENDING_HSE_VALIDATION}`}>
            Status: {status.replace(/_/g, ' ')}
          </span>
          <span className="text-[10px] text-slate-400 font-mono">
            Ref: {recommendation_number}
          </span>
        </div>
      </div>

      {/* Main Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800">
              {category.replace(/_/g, ' ')}
            </span>
            <span className={`text-[10px] uppercase tracking-wider px-2.5 py-0.5 rounded border ${priorityStyles[priority_suggestion] || priorityStyles.MEDIUM}`}>
              Suggested Priority: {priority_suggestion.replace(/_/g, ' ')}
            </span>
            {sif_classification && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${sif_classification === 'SIF-Potential' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                {sif_classification}
              </span>
            )}
          </div>

          <h3 className="text-base font-extrabold text-slate-100">{title}</h3>
        </div>

        {/* Action & Review Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          {(status === 'ACCEPTED' || status === 'MODIFIED') && (
            <button
              onClick={() => setIsActionModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-500 text-slate-950 font-extrabold text-xs hover:bg-emerald-400 transition-all shadow-md"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create Operational Action</span>
            </button>
          )}

          {canReview && (
            <button
              onClick={() => setIsReviewModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-amber-500 text-slate-950 font-extrabold text-xs hover:bg-amber-400 transition-all shadow-md"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>{status === 'PENDING_HSE_VALIDATION' ? 'HSE Review / Validate' : 'Re-Review'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Original AI Recommendation Text Body */}
      <div className="space-y-2 text-xs">
        <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-slate-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />
            <span>Original AI-Suggested Operational Intervention</span>
          </span>
          <span className="text-[10px] text-slate-500 italic">Immutable Original</span>
        </h4>
        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
          {recommendation_text}
        </div>
      </div>

      {/* Part 4B HSE Review Decision Display (Separation of AI vs HSE) */}
      {latest_review && (
        <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-emerald-400" />
              <span className="font-extrabold uppercase tracking-wider text-slate-200 text-[11px]">
                HSE Human Validation Decision
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              Reviewed by {latest_review.reviewer_name} on {new Date(latest_review.reviewed_at).toLocaleString()}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-lg text-xs font-extrabold border uppercase tracking-wider ${
              latest_review.decision === 'ACCEPT'
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : latest_review.decision === 'MODIFY'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
            }`}>
              Decision: {latest_review.decision}
            </span>
          </div>

          {/* If MODIFIED: Show HSE Modified Recommendation details */}
          {latest_review.decision === 'MODIFY' && (
            <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-2 text-xs">
              <h5 className="font-bold text-amber-400 flex items-center gap-1.5 text-[11px] uppercase tracking-wider">
                <Edit3 className="w-3.5 h-3.5" />
                <span>HSE Modified Recommendation</span>
              </h5>
              <div className="space-y-1">
                <p className="font-bold text-slate-100">{latest_review.modified_title}</p>
                <p className="text-slate-300 bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-[11px] leading-relaxed whitespace-pre-wrap">
                  {latest_review.modified_recommendation_text}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3 text-[10px] text-slate-400 pt-1">
                {latest_review.modified_category && (
                  <span>Modified Category: <strong className="text-slate-200">{latest_review.modified_category.replace(/_/g, ' ')}</strong></span>
                )}
                {latest_review.modified_priority && (
                  <span>Modified Priority: <strong className="text-amber-400">{latest_review.modified_priority}</strong></span>
                )}
                {latest_review.proposed_department && (
                  <span className="flex items-center gap-1">
                    <Building className="w-3 h-3 text-slate-500" />
                    <span>Proposed Dept: <strong className="text-slate-200">{latest_review.proposed_department}</strong></span>
                  </span>
                )}
                {latest_review.proposed_due_date && (
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-slate-500" />
                    <span>Proposed Target Date: <strong className="text-amber-400">{latest_review.proposed_due_date}</strong></span>
                  </span>
                )}
              </div>
            </div>
          )}

          {/* If REJECTED: Show Mandatory Rejection Reason */}
          {latest_review.decision === 'REJECT' && latest_review.rejection_reason && (
            <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-800/40 space-y-1 text-xs">
              <h5 className="font-bold text-rose-400 flex items-center gap-1.5 text-[11px] uppercase tracking-wider">
                <XCircle className="w-3.5 h-3.5" />
                <span>Mandatory Rejection Justification</span>
              </h5>
              <p className="text-rose-200 bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-[11px] leading-relaxed">
                {latest_review.rejection_reason}
              </p>
            </div>
          )}

          {/* Audit Comment */}
          {latest_review.review_comment && (
            <div className="text-[11px] text-slate-300">
              <span className="text-slate-400 font-semibold">Reviewer Comment: </span>
              <span className="italic">{latest_review.review_comment}</span>
            </div>
          )}
        </div>
      )}

      {/* Why This Was Suggested (Rationale) */}
      <div className="space-y-1.5 text-xs">
        <h4 className="font-bold text-slate-300 uppercase tracking-wider text-[10px] flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-amber-400" />
          <span>Analytical Rationale & Evidence Basis</span>
        </h4>
        <p className="text-slate-300 bg-slate-950/40 p-3 rounded-xl border border-slate-800/60 text-[11px] leading-relaxed">
          {rationale}
        </p>
      </div>

      {/* Evidence Payload Drill-down Toggle */}
      <div className="pt-2">
        <button
          onClick={() => setShowEvidence(!showEvidence)}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-400 hover:text-amber-300 transition-colors"
        >
          <span>{showEvidence ? 'Hide Supporting Evidence' : 'View Traceable Evidence & Metadata'}</span>
          {showEvidence ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showEvidence && (
          <div className="mt-3 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-4 text-xs">
            <h5 className="font-bold text-slate-200 uppercase tracking-wider text-[10px] border-b border-slate-800 pb-2">
              Traceable Evidence Payload
            </h5>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px]">
              <div>
                <span className="text-slate-400 block mb-0.5">Evidence Summary:</span>
                <span className="text-slate-200 font-medium">{evidence_summary}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Primary Barrier Concern:</span>
                <span className="text-amber-400 font-bold">{recData.barrier_category || 'General'}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Life-Saving Rules Mapped:</span>
                <div className="flex flex-wrap gap-1 mt-0.5">
                  {life_saving_rules.length > 0 ? (
                    life_saving_rules.map((lsr, i) => (
                      <span key={i} className="text-[10px] bg-slate-900 text-slate-300 px-2 py-0.5 rounded border border-slate-800">
                        {lsr}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500 italic">None</span>
                  )}
                </div>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Hazards Identified:</span>
                <div className="flex flex-wrap gap-1 mt-0.5">
                  {hazards.length > 0 ? (
                    hazards.map((h, i) => (
                      <span key={i} className="text-[10px] bg-slate-900 text-slate-300 px-2 py-0.5 rounded border border-slate-800">
                        {h}
                      </span>
                    ))
                  ) : (
                    <span className="text-slate-500 italic">None</span>
                  )}
                </div>
              </div>
              {bdi_score !== null && bdi_score !== undefined && (
                <div>
                  <span className="text-slate-400 block mb-0.5">Barrier Degradation Index (BDI_v1):</span>
                  <span className="text-purple-400 font-bold">{bdi_score.toFixed(1)} / 100</span>
                </div>
              )}
              {escalation_indicators.length > 0 && (
                <div>
                  <span className="text-slate-400 block mb-0.5">Potential Escalation Indicators:</span>
                  <span className="text-orange-400 font-bold">{escalation_indicators.join(', ')}</span>
                </div>
              )}
            </div>

            {/* Version Metadata Footer */}
            <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-[10px] text-slate-500 gap-2">
              <span>Model Version: <strong className="text-slate-400">{model_version}</strong></span>
              <span>Analytics Version: <strong className="text-slate-400">{recData.analytics_version || 'safety_intelligence_v1'}</strong></span>
              <span>Recommendation Engine: <strong className="text-slate-400">{methodology_version}</strong></span>
            </div>
          </div>
        )}
      </div>

      {/* Mandatory Disclaimer Footer */}
      <div className="pt-3 border-t border-slate-800 text-[10px] text-slate-400">
        <p>
          "This recommendation is generated from available safety intelligence evidence. It is a suggestion only and requires HSE review before any operational action is created."
        </p>
      </div>

      {/* Review Modal */}
      <InterventionReviewModal
        recommendation={recData}
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        onReviewSubmitted={handleReviewSubmitted}
      />

      {/* Action Creation Modal */}
      <ActionCreateModal
        recommendation={recData}
        isOpen={isActionModalOpen}
        onClose={() => setIsActionModalOpen(false)}
        onActionCreated={(newAction) => {
          setIsActionModalOpen(false);
          alert(`Operational Action ${newAction.action_number} created successfully.`);
        }}
      />
    </div>
  );
};
