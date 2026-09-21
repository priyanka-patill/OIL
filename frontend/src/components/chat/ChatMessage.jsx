import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, User, ExternalLink, ArrowRight, ShieldAlert } from 'lucide-react';

export const ChatMessage = ({ message, onActionClick }) => {
  const navigate = useNavigate();
  const isAssistant = message.sender === 'assistant';

  // Helper to safely render simple markdown-like formatting (bold, lists, headings)
  const renderFormattedContent = (content) => {
    if (!content) return null;

    const lines = content.split('\n');
    return lines.map((line, idx) => {
      // Headings
      if (line.startsWith('### ')) {
        return (
          <h4 key={idx} className="text-xs font-black text-amber-400 uppercase tracking-wide my-2">
            {line.replace('### ', '')}
          </h4>
        );
      }
      if (line.startsWith('**') && line.endsWith('**')) {
        return (
          <p key={idx} className="font-bold text-slate-100 my-1">
            {line.replace(/\*\*/g, '')}
          </p>
        );
      }
      // Bullet items
      if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
        const text = line.trim().replace(/^[-•]\s*/, '');
        return (
          <li key={idx} className="ml-3 list-disc text-slate-300 my-0.5 leading-relaxed">
            {formatInlineText(text)}
          </li>
        );
      }

      if (line.trim() === '') {
        return <div key={idx} className="h-1.5" />;
      }

      return (
        <p key={idx} className="my-1 leading-relaxed">
          {formatInlineText(line)}
        </p>
      );
    });
  };

  const formatInlineText = (text) => {
    // Basic inline bold **text** and code `text` parsing
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index} className="font-bold text-slate-100">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={index} className="px-1.5 py-0.5 rounded bg-slate-950 text-amber-300 font-mono text-[11px] border border-slate-800">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className={`flex gap-3 text-xs ${isAssistant ? 'justify-start' : 'justify-end'}`}>
      {/* Assistant Avatar */}
      {isAssistant && (
        <div className="w-7 h-7 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 shadow mt-0.5">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div className={`max-w-[85%] rounded-2xl p-3.5 space-y-2 shadow-lg ${
        isAssistant
          ? 'bg-slate-900/90 border border-slate-800 text-slate-200'
          : 'bg-amber-500 text-slate-950 font-medium'
      }`}>
        {/* Message Content */}
        <div className="text-xs space-y-1 overflow-x-auto">
          {renderFormattedContent(message.content)}
        </div>

        {/* Source Citations */}
        {isAssistant && message.sources && message.sources.length > 0 && (
          <div className="pt-2 border-t border-slate-800/80 space-y-1">
            <span className="text-[10px] font-bold text-slate-500 uppercase block">Sources:</span>
            <div className="flex flex-wrap gap-1.5">
              {message.sources.map((src, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    if (onActionClick) onActionClick();
                    navigate(src.path);
                  }}
                  className="px-2 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-amber-400 text-[10px] font-bold border border-slate-800 flex items-center gap-1 transition"
                >
                  <ExternalLink className="w-2.5 h-2.5" />
                  <span>{src.title}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {isAssistant && message.actions && message.actions.length > 0 && (
          <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-2">
            {message.actions.map((act, idx) => (
              <button
                key={idx}
                onClick={() => {
                  if (onActionClick) onActionClick();
                  navigate(act.path);
                }}
                className="px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[11px] font-bold transition flex items-center gap-1.5 shadow"
              >
                <span>{act.label}</span>
                <ArrowRight className="w-3 h-3 text-amber-400" />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* User Avatar */}
      {!isAssistant && (
        <div className="w-7 h-7 rounded-xl bg-slate-800 text-slate-300 flex items-center justify-center shrink-0 shadow mt-0.5 text-xs font-bold">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
};
