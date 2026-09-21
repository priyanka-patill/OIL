import React, { useEffect } from 'react';
import { AlertCircle, CheckCircle, Info, X } from 'lucide-react';

export const NotificationToast = ({ type = 'info', message, onClose, duration = 4000 }) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  if (!message) return null;

  const styles = {
    success: 'bg-emerald-950 border-emerald-700 text-emerald-200 icon-emerald-400',
    error: 'bg-rose-950 border-rose-700 text-rose-200 icon-rose-400',
    info: 'bg-blue-950 border-blue-700 text-blue-200 icon-blue-400',
    warning: 'bg-amber-950 border-amber-700 text-amber-200 icon-amber-400',
  }[type] || 'bg-slate-900 border-slate-700 text-slate-200';

  const icons = {
    success: <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />,
    error: <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />,
    info: <Info className="w-5 h-5 text-blue-400 shrink-0" />,
    warning: <AlertCircle className="w-5 h-5 text-amber-400 shrink-0" />,
  };

  return (
    <div
      className={`fixed bottom-5 right-5 z-50 flex items-center gap-3 max-w-md p-4 rounded-xl border shadow-xl backdrop-blur-md transition-all duration-300 animate-slide-up ${styles}`}
    >
      {icons[type]}
      <p className="text-sm font-medium flex-1">{message}</p>
      <button
        onClick={onClose}
        className="p-1 rounded-lg hover:bg-white/10 text-slate-400 hover:text-slate-100 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
