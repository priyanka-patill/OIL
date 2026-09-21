import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { reportsApi } from '../api/reportsApi';
import {
  FileText,
  Building2,
  Wrench,
  AlertOctagon,
  ShieldAlert,
  ArrowLeft,
  CheckCircle,
  AlertCircle,
  Paperclip,
  Sparkles,
} from 'lucide-react';

import { FileUploadDropzone } from '../components/reports/FileUploadDropzone';

export const ReportNewPage = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    report_type: 'NEAR_MISS',
    date: new Date().toISOString().split('T')[0],
    site: 'Digboi Refinery',
    refinery_unit: 'Hydrogen Unit',
    location: 'Process Area Block-3',
    equipment_id: 'P-305',
    work_type: 'Preventive Maintenance',
    activity: 'Pump Overhaul & Gasket Replacement',
    department: 'Operations',
    description: '',
    ppe_noncompliance: false,
    supervisor_negligence: false,
    maintenance_delay_or_issue: false,
    repeated_issue_ignored: false,
    immediate_cause: '',
    potential_consequence: '',
    corrective_action: '',
    action_status: 'Pending',
  });

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatusText, setSubmitStatusText] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.description || formData.description.trim().length < 10) {
      setError('Description must be at least 10 characters detailing the safety observation.');
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitStatusText('Submitting Safety Report & Executing System Analysis...');
      const payload = {
        ...formData,
      };

      const response = await reportsApi.createReport(payload);
      if (response?.success && response?.data) {
        const reportId = response.data.id;

        if (selectedFiles.length > 0) {
          setSubmitStatusText(`Uploading ${selectedFiles.length} file attachment(s)...`);
          try {
            await reportsApi.uploadAttachments(reportId, selectedFiles);
          } catch (attErr) {
            console.error('Attachment upload error:', attErr);
            // Non-fatal: Report was created successfully, notify user but navigate to detail page
          }
        }

        navigate(`/reports/${reportId}`);
      }
    } catch (err) {
      setError(err.message || 'Failed to submit safety report.');
    } finally {
      setIsSubmitting(false);
      setSubmitStatusText('');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Directory</span>
        </button>

        <span className="text-xs text-amber-400 font-semibold uppercase tracking-wider">
          Standard HSE Form
        </span>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Submit New Safety Observation Report</h1>
          <p className="text-xs text-slate-400 mt-1">
            Log an unsafe act, unsafe condition, or near-miss observation for site HSE review.
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* SECTION 1: REPORT & LOCATION INFO */}
          <div className="space-y-4 pt-2">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              <Building2 className="w-4 h-4" />
              <span>Section 1: Report & Plant Location</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Observation Type *
                </label>
                <select
                  name="report_type"
                  value={formData.report_type}
                  onChange={handleChange}
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                >
                  <option value="NEAR_MISS">Near Miss</option>
                  <option value="UNSAFE_ACT">Unsafe Act</option>
                  <option value="UNSAFE_CONDITION">Unsafe Condition</option>
                  <option value="INCIDENT">Incident</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Date of Incident *</label>
                <input
                  type="date"
                  name="date"
                  required
                  value={formData.date}
                  onChange={handleChange}
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Refinery Site *</label>
                <input
                  type="text"
                  name="site"
                  required
                  value={formData.site}
                  onChange={handleChange}
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Refinery Unit</label>
                <input
                  type="text"
                  name="refinery_unit"
                  value={formData.refinery_unit}
                  onChange={handleChange}
                  placeholder="e.g. Hydrogen Unit"
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Specific Location</label>
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="e.g. Pump House No. 2"
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Department</label>
                <input
                  type="text"
                  name="department"
                  value={formData.department}
                  onChange={handleChange}
                  placeholder="e.g. Operations / Maintenance"
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>
          </div>

          {/* SECTION 2: WORK & EQUIPMENT DETAILS */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              <Wrench className="w-4 h-4" />
              <span>Section 2: Work Activity & Equipment Identification</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Equipment Tag ID</label>
                <input
                  type="text"
                  name="equipment_id"
                  value={formData.equipment_id}
                  onChange={handleChange}
                  placeholder="e.g. P-305 / V-102"
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Work Type</label>
                <input
                  type="text"
                  name="work_type"
                  value={formData.work_type}
                  onChange={handleChange}
                  placeholder="e.g. Preventive Maintenance"
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Activity Description</label>
                <input
                  type="text"
                  name="activity"
                  value={formData.activity}
                  onChange={handleChange}
                  placeholder="e.g. Line Flange Opening"
                  className="w-full px-3 py-2 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-amber-500"
                />
              </div>
            </div>
          </div>

          {/* SECTION 3: SAFETY OBSERVATION DESCRIPTION */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              <FileText className="w-4 h-4" />
              <span>Section 3: Detailed Safety Observation *</span>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Near-Miss / Unsafe Observation Text *
              </label>
              <textarea
                name="description"
                required
                rows={4}
                value={formData.description}
                onChange={handleChange}
                placeholder="Describe what happened, what unsafe act or unsafe condition was observed, the activity being performed, equipment involved, and potential consequences..."
                className="w-full p-3.5 bg-slate-950/80 border border-slate-700/80 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Please provide full context. Keep safety negations and hazard terminology intact.
              </p>
            </div>
          </div>

          {/* SECTION 4: SIF PRECURSOR FLAGS & CONTEXT */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              <ShieldAlert className="w-4 h-4" />
              <span>Section 4: Safety Precursors & Consequence Analysis</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 cursor-pointer hover:border-slate-700">
                <input
                  type="checkbox"
                  name="ppe_noncompliance"
                  checked={formData.ppe_noncompliance}
                  onChange={handleChange}
                  className="w-4 h-4 rounded border-slate-700 text-amber-500 focus:ring-amber-500 bg-slate-900"
                />
                <span className="text-xs text-slate-200 font-medium">PPE Non-Compliance Observed</span>
              </label>

              <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 cursor-pointer hover:border-slate-700">
                <input
                  type="checkbox"
                  name="supervisor_negligence"
                  checked={formData.supervisor_negligence}
                  onChange={handleChange}
                  className="w-4 h-4 rounded border-slate-700 text-amber-500 focus:ring-amber-500 bg-slate-900"
                />
                <span className="text-xs text-slate-200 font-medium">Supervisor Negligence / Permit Defect</span>
              </label>

              <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 cursor-pointer hover:border-slate-700">
                <input
                  type="checkbox"
                  name="maintenance_delay_or_issue"
                  checked={formData.maintenance_delay_or_issue}
                  onChange={handleChange}
                  className="w-4 h-4 rounded border-slate-700 text-amber-500 focus:ring-amber-500 bg-slate-900"
                />
                <span className="text-xs text-slate-200 font-medium">Maintenance Delay / Equipment Issue</span>
              </label>

              <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 cursor-pointer hover:border-slate-700">
                <input
                  type="checkbox"
                  name="repeated_issue_ignored"
                  checked={formData.repeated_issue_ignored}
                  onChange={handleChange}
                  className="w-4 h-4 rounded border-slate-700 text-amber-500 focus:ring-amber-500 bg-slate-900"
                />
                <span className="text-xs text-slate-200 font-medium">Repeated Hazard Previously Reported</span>
              </label>
            </div>

            {/* AUTOMATED SAFETY INTELLIGENCE DISPLAY */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span>Automated System Analysis (Calculated Upon Submission)</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-0.5">Previous Similar Reports</span>
                  <span className="text-amber-300 font-medium text-[11px]">
                    Calculated automatically by similarity engine from historical safety database
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                  <span className="text-slate-400 font-semibold block mb-0.5">Risk Level Assessment</span>
                  <span className="text-amber-300 font-medium text-[11px]">
                    Evaluated automatically by SIF ML model & risk assessment engine
                  </span>
                </div>
              </div>
            </div>

            {/* Interactive File Attachment Upload Dropzone */}
            <FileUploadDropzone
              selectedFiles={selectedFiles}
              setSelectedFiles={setSelectedFiles}
            />
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/reports')}
              className="px-5 py-2.5 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800 border border-slate-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-950 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 transition-all shadow-lg shadow-amber-500/20"
            >
              {isSubmitting ? (submitStatusText || 'Submitting Report...') : 'Submit Safety Observation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
