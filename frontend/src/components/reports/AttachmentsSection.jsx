import React, { useState } from 'react';
import {
  Paperclip,
  FileText,
  Image as ImageIcon,
  Download,
  ExternalLink,
  Eye,
  Trash2,
  X,
} from 'lucide-react';
import { reportsApi } from '../../api/reportsApi';

export const AttachmentsSection = ({ attachments = [], canDelete = false, onAttachmentDeleted }) => {
  const [activePreviewUrl, setActivePreviewUrl] = useState(null);
  const [activePreviewTitle, setActivePreviewTitle] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  if (!attachments || attachments.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
        <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider border-b border-slate-800 pb-2 flex items-center gap-2">
          <Paperclip className="w-4 h-4" />
          <span>Supporting File Attachments (0)</span>
        </h3>
        <p className="text-xs text-slate-500 italic">No supporting photos or permits attached to this safety report.</p>
      </div>
    );
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleDelete = async (attachmentId) => {
    if (!window.confirm('Are you sure you want to delete this file attachment?')) return;
    try {
      setDeletingId(attachmentId);
      await reportsApi.deleteAttachment(attachmentId);
      if (onAttachmentDeleted) {
        onAttachmentDeleted(attachmentId);
      }
    } catch (err) {
      alert(err.message || 'Failed to delete attachment.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <>
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
            <Paperclip className="w-4 h-4" />
            <span>Supporting File Attachments ({attachments.length})</span>
          </h3>
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Auditable Evidence
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {attachments.map((att) => {
            const isImage = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'].includes(
              att.mime_type.toLowerCase()
            ) || ['.jpg', '.jpeg', '.png', '.webp'].includes(att.file_extension.toLowerCase());

            const downloadUrl = reportsApi.getAttachmentDownloadUrl(att.id);
            const previewUrl = reportsApi.getAttachmentPreviewUrl(att.id);

            return (
              <div
                key={att.id}
                className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between space-y-3 hover:border-slate-700 transition"
              >
                <div className="flex items-start gap-3">
                  {/* Thumbnail / File Icon */}
                  {isImage ? (
                    <div
                      onClick={() => {
                        setActivePreviewUrl(previewUrl);
                        setActivePreviewTitle(att.original_filename);
                      }}
                      className="w-12 h-12 rounded-lg bg-slate-900 border border-slate-800 shrink-0 overflow-hidden cursor-pointer group relative flex items-center justify-center text-amber-400"
                    >
                      <img
                        src={previewUrl}
                        alt={att.original_filename}
                        className="w-full h-full object-cover group-hover:opacity-80 transition"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                      <ImageIcon className="w-5 h-5 absolute" />
                    </div>
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-slate-900 border border-slate-800 shrink-0 flex items-center justify-center text-amber-400">
                      <FileText className="w-6 h-6" />
                    </div>
                  )}

                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-slate-100 truncate" title={att.original_filename}>
                      {att.original_filename}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                      <span>{formatFileSize(att.file_size)}</span>
                      <span>•</span>
                      <span className="uppercase">{att.file_extension.replace('.', '')}</span>
                    </div>
                  </div>
                </div>

                {/* Actions Bar */}
                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between gap-2 text-xs">
                  <div className="flex items-center gap-2">
                    {isImage ? (
                      <button
                        type="button"
                        onClick={() => {
                          setActivePreviewUrl(previewUrl);
                          setActivePreviewTitle(att.original_filename);
                        }}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400 hover:text-amber-300"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Preview</span>
                      </button>
                    ) : (
                      <a
                        href={previewUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400 hover:text-amber-300"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>Open PDF</span>
                      </a>
                    )}

                    <a
                      href={downloadUrl}
                      download={att.original_filename}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-300 hover:text-white"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download</span>
                    </a>
                  </div>

                  {canDelete && (
                    <button
                      type="button"
                      disabled={deletingId === att.id}
                      onClick={() => handleDelete(att.id)}
                      className="text-rose-400 hover:text-rose-300 p-1 rounded hover:bg-rose-950/40 transition"
                      title="Delete attachment"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Image Preview Modal */}
      {activePreviewUrl && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md flex flex-col items-center justify-center p-4"
          onClick={() => setActivePreviewUrl(null)}
        >
          <div
            className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h4 className="text-xs font-bold text-amber-400 truncate">{activePreviewTitle}</h4>
              <button
                type="button"
                onClick={() => setActivePreviewUrl(null)}
                className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 flex-1 overflow-auto flex items-center justify-center bg-slate-950">
              <img
                src={activePreviewUrl}
                alt={activePreviewTitle}
                className="max-w-full max-h-[70vh] object-contain rounded-lg"
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
};
