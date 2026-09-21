import React, { useRef, useState } from 'react';
import {
  Paperclip,
  UploadCloud,
  X,
  FileText,
  Image as ImageIcon,
  AlertCircle,
  FileCheck,
} from 'lucide-react';

const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.pdf'];
const DISALLOWED_EXTENSIONS = [
  '.exe', '.bat', '.cmd', '.sh', '.js', '.msi', '.dll', '.py', '.vbs', '.ps1'
];
const MAX_SIZE_MB = 10;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export const FileUploadDropzone = ({ selectedFiles = [], setSelectedFiles }) => {
  const fileInputRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState('');

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const processFiles = (newFiles) => {
    setValidationError('');
    const validFiles = [];
    let errorMsg = '';

    Array.from(newFiles).forEach((file) => {
      const ext = '.' + file.name.split('.').pop().toLowerCase();

      if (DISALLOWED_EXTENSIONS.includes(ext)) {
        errorMsg = `Security Violation: Executable file '${file.name}' is forbidden.`;
        return;
      }

      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        errorMsg = `Unsupported file type for '${file.name}'. Please upload JPG, JPEG, PNG, WEBP, or PDF.`;
        return;
      }

      if (file.size > MAX_SIZE_BYTES) {
        errorMsg = `File '${file.name}' (${formatFileSize(file.size)}) exceeds maximum allowed size of ${MAX_SIZE_MB} MB.`;
        return;
      }

      // Check if file is already added
      const isDuplicate = selectedFiles.some(
        (f) => f.name === file.name && f.size === file.size
      );
      if (!isDuplicate) {
        validFiles.push(file);
      }
    });

    if (errorMsg) {
      setValidationError(errorMsg);
    }

    if (validFiles.length > 0) {
      setSelectedFiles((prev) => [...prev, ...validFiles]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
      e.target.value = ''; // Reset input to allow re-selecting same file if removed
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const removeFile = (indexToRemove) => {
    setSelectedFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider">
          <Paperclip className="w-4 h-4" />
          <span>File Attachments (Photos / Permits)</span>
        </div>
        <span className="text-[10px] font-semibold text-slate-400 bg-slate-900 border border-slate-800 px-2.5 py-0.5 rounded uppercase">
          Optional Attachment
        </span>
      </div>

      {/* Validation Warning Alert */}
      {validationError && (
        <div className="p-3 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs flex items-center justify-between gap-2 shadow-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{validationError}</span>
          </div>
          <button
            type="button"
            onClick={() => setValidationError('')}
            className="text-slate-400 hover:text-slate-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`p-6 rounded-2xl border-2 border-dashed transition-all cursor-pointer text-center flex flex-col items-center justify-center gap-2 ${
          isDragOver
            ? 'border-amber-400 bg-amber-500/10'
            : 'border-slate-800 bg-slate-950/50 hover:border-slate-700 hover:bg-slate-950/80'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.webp,.pdf"
          onChange={handleFileSelect}
          className="hidden"
        />

        <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 mb-1">
          <UploadCloud className="w-6 h-6" />
        </div>

        <div>
          <p className="text-xs font-bold text-slate-200">
            Click to browse or drag & drop files here
          </p>
          <p className="text-[11px] text-slate-400 mt-1">
            Supported formats: <strong className="text-amber-400">JPG, JPEG, PNG, WEBP, PDF</strong> (Max {MAX_SIZE_MB} MB per file)
          </p>
        </div>
      </div>

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold px-1">
            <span>Selected Files ({selectedFiles.length})</span>
            <button
              type="button"
              onClick={() => setSelectedFiles([])}
              className="text-amber-400 hover:underline text-[11px]"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
            {selectedFiles.map((file, idx) => {
              const isPdf = file.name.toLowerCase().endsWith('.pdf');
              return (
                <div
                  key={`${file.name}-${idx}`}
                  className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-amber-400 shrink-0">
                      {isPdf ? <FileText className="w-4 h-4" /> : <ImageIcon className="w-4 h-4" />}
                    </div>
                    <div className="min-w-0">
                      <p className="font-semibold text-slate-200 truncate text-xs">{file.name}</p>
                      <p className="text-[10px] text-slate-400">{formatFileSize(file.size)}</p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(idx);
                    }}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 border border-transparent hover:border-rose-900/50 transition shrink-0"
                    title="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
