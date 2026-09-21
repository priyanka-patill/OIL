import React, { useState } from 'react';
import { ChatWindow } from './ChatWindow';
import { Sparkles, MessageSquare, X } from 'lucide-react';

export const ChatbotLauncher = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Floating Launcher Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        title="Open OIL HSE Safety Assistant"
        className="fixed bottom-5 right-5 z-50 p-3.5 rounded-full bg-gradient-to-r from-amber-500 to-amber-400 text-slate-950 shadow-2xl hover:scale-105 active:scale-95 transition-all duration-200 border-2 border-amber-300 flex items-center gap-2 group"
      >
        {isOpen ? (
          <X className="w-6 h-6 text-slate-950" />
        ) : (
          <>
            <div className="relative">
              <Sparkles className="w-6 h-6 text-slate-950 animate-pulse" />
            </div>
            <span className="max-w-0 overflow-hidden group-hover:max-w-xs transition-all duration-300 whitespace-nowrap text-xs font-black tracking-wide pr-1">
              Safety Assistant
            </span>
          </>
        )}
      </button>

      {/* Floating Chat Modal Panel */}
      {isOpen && <ChatWindow onClose={() => setIsOpen(false)} />}
    </>
  );
};
