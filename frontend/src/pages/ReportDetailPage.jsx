import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { reportsApi } from '../api/reportsApi';
import { useAuth } from '../context/AuthContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { ReportTypeBadge } from '../components/common/ReportTypeBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { AIAnalysisPanel } from '../components/reports/AIAnalysisPanel';
import { HSEReviewPanel } from '../components/reports/HSEReviewPanel';
import { RelatedSafetyIntelligence } from '../components/analytics/RelatedSafetyIntelligence';
import { InterventionPanel } from '../components/interventions/InterventionPanel';
import {
  FileText,
  ArrowLeft,
  Building2,
  Wrench,
  ShieldAlert,
  User,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
  Sparkles,
} from 'lucide-react';

import { AttachmentsSection } from '../components/reports/AttachmentsSection';

export const ReportDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, role } = useAuth();

  const [report, setReport] = useState(null);
  const [reviewHistory, setReviewHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);
  const [error, setError] = useState('');
  const [notification, setNotification] = useState('');

  const canReview = role === 'HSE_MANAGER' || role === 'ADMIN';

  const fetchReportData = async () => {
    try {
      setIsLoading(true);
      setError('');
      const response = await reportsApi.getReportById(id);
      if (response?.data) {
        setReport(response.data);
      }

      try {
        const revResponse = await reportsApi.getReviewHistory(id);
        if (revResponse?.data) {
          setReviewHistory(revResponse.data || []);
        }
      } catch {
        // Ignore if no review history
      }
    } catch (err) {
      setError(err.message || 'Failed to load safety report details.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, [id]);

  const handleRunAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      setError('');
      setNotification('');
      const response = await reportsApi.analyzeReport(id);
      if (response?.success) {
        setNotification('AI Safety Analysis executed successfully!');
        await fetchReportData();
      }
    } catch (err) {
      setError(err.message || 'Failed to execute AI Safety Analysis.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReviewSubmit = async (reviewPayload) => {
    try {
      setIsSubmittingReview(true);
      setError('');
      setNotification('');
      const response = await reportsApi.submitReview(id, reviewPayload);
      if (response?.success) {
        setNotification('HSE Validation review decision recorded successfully!');
        await fetchReportData();
      }
    } catch (err) {
      setError(err.message || 'Failed to submit review decision.');
    } finally {
      setIsSubmittingReview(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner label="Fetching safety report record from database..." />;
  }

  if (error && !report) {
    return (
      <div className="p-8 text-center space-y-4">
        <AlertCircle className="w-12 h-12 mx-auto text-rose-400" />
        <p className="text-base font-bold text-slate-100">{error}</p>
        <button
          onClick={() => navigate('/reports')}
          className="px-4 py-2 bg-slate-800 text-slate-200 rounded-xl text-xs font-semibold"
        >
          Return to Reports Directory
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Top Navigation Bar */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/reports')}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Directory</span>
        </button>

        <div className="flex items-center gap-2">
          <StatusBadge status={report.status} />
          <ReportTypeBadge type={report.report_type} />
        </div>
      </div>

      {notification && (
        <div className="p-4 rounded-xl bg-emerald-950/80 border border-emerald-800 text-emerald-200 text-xs font-semibold flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification('')} className="text-slate-400 hover:text-slate-200">
            ×
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-200 text-xs font-semibold">
          {error}
        </div>
      )}

      {/* Report Header Card */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-extrabold text-amber-400">{report.report_number}</h1>
            <span className="text-xs text-slate-400">ID #{report.id}</span>
          </div>
          <p className="text-xs text-slate-300 mt-1">
            Logged on <span className="font-semibold text-slate-100">{report.date}</span> at{' '}
            <span className="font-semibold text-slate-100">{report.site}</span>
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-400">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <User className="w-3.5 h-3.5 text-amber-500" />
            <span>Created by: {report.creator_name || `User #${report.created_by}`}</span>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Details & AI Intelligence */}
        <div className="lg:col-span-2 space-y-6">
          {/* Observation Details */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-slate-800 pb-2 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              <span>Safety Observation Details</span>
            </h3>
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {report.description}
            </p>
          </div>

          {/* Plant & Work Specifications */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-slate-800 pb-2 flex items-center gap-2">
              <Building2 className="w-4 h-4" />
              <span>Plant Unit & Work Environment</span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-slate-400 block mb-0.5">Refinery Site</span>
                <span className="font-semibold text-slate-100">{report.site}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Refinery Unit</span>
                <span className="font-semibold text-slate-100">{report.refinery_unit || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Location</span>
                <span className="font-semibold text-slate-100">{report.location || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Equipment Tag ID</span>
                <span className="font-semibold text-amber-400">{report.equipment_id || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Work Category</span>
                <span className="font-semibold text-slate-100">{report.work_type || 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-400 block mb-0.5">Department</span>
                <span className="font-semibold text-slate-100">{report.department || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Precursor Audit Flags */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-slate-800 pb-2 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" />
              <span>Safety Precursor Audit Flags</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className={`p-3 rounded-xl border flex items-center justify-between ${report.ppe_noncompliance ? 'bg-rose-950/40 border-rose-800 text-rose-300' : 'bg-slate-950/60 border-slate-800 text-slate-400'}`}>
                <span>PPE Non-Compliance</span>
                <span className="font-bold">{report.ppe_noncompliance ? 'YES' : 'NO'}</span>
              </div>
              <div className={`p-3 rounded-xl border flex items-center justify-between ${report.supervisor_negligence ? 'bg-rose-950/40 border-rose-800 text-rose-300' : 'bg-slate-950/60 border-slate-800 text-slate-400'}`}>
                <span>Supervisor / Permit Issue</span>
                <span className="font-bold">{report.supervisor_negligence ? 'YES' : 'NO'}</span>
              </div>
              <div className={`p-3 rounded-xl border flex items-center justify-between ${report.maintenance_delay_or_issue ? 'bg-rose-950/40 border-rose-800 text-rose-300' : 'bg-slate-950/60 border-slate-800 text-slate-400'}`}>
                <span>Maintenance Issue / Delay</span>
                <span className="font-bold">{report.maintenance_delay_or_issue ? 'YES' : 'NO'}</span>
              </div>
              <div className={`p-3 rounded-xl border flex items-center justify-between ${report.repeated_issue_ignored ? 'bg-rose-950/40 border-rose-800 text-rose-300' : 'bg-slate-950/60 border-slate-800 text-slate-400'}`}>
                <span>Repeated Issue Ignored</span>
                <span className="font-bold">{report.repeated_issue_ignored ? 'YES' : 'NO'}</span>
              </div>
            </div>
          </div>

          {/* Supporting File Attachments (Photos / Permits) */}
          <AttachmentsSection
            attachments={report.attachments || []}
            canDelete={user?.id === report.created_by || canReview}
            onAttachmentDeleted={fetchReportData}
          />

          {/* Real AI Analysis Panel */}
          <AIAnalysisPanel
            analysis={report.ai_analysis}
            onAnalyze={handleRunAnalysis}
            isAnalyzing={isAnalyzing}
          />

          {/* Related Safety Intelligence (Part 3E Integration) */}
          <RelatedSafetyIntelligence reportId={report.id} />

          {/* Part 4A Intervention Recommendations */}
          <InterventionPanel reportId={report.id} />
        </div>

        {/* Right Column: HSE Review Panel & History */}
        <div className="space-y-6">
          {/* HSE Review Panel for Manager & Admin */}
          {canReview && (
            <HSEReviewPanel
              report={report}
              onSubmitReview={handleReviewSubmit}
              isSubmitting={isSubmittingReview}
            />
          )}

          {/* Validation Audit History */}
          {reviewHistory.length > 0 && (
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
              <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-slate-800 pb-2 flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                <span>HSE Review Audit Trail</span>
              </h3>

              <div className="space-y-3">
                {reviewHistory.map((rev) => (
                  <div key={rev.id} className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-emerald-400">{rev.hse_decision}</span>
                      <span className="text-slate-500 text-[10px]">
                        {new Date(rev.reviewed_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-slate-300 leading-relaxed">{rev.review_comment}</p>
                    <p className="text-[10px] text-slate-500 pt-1 border-t border-slate-900">
                      Validated by Reviewer #{rev.reviewer_id}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* System Metadata Card */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              System Audit Metadata
            </h3>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Report Status:</span>
                <span className="font-semibold text-slate-100">{report.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Created At:</span>
                <span className="text-slate-200">
                  {new Date(report.created_at).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Last Updated:</span>
                <span className="text-slate-200">
                  {new Date(report.updated_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
