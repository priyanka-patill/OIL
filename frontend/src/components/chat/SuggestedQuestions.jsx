import React from 'react';
import { HelpCircle, Sparkles, ShieldCheck, CheckSquare, FileText, AlertTriangle } from 'lucide-react';

export const SuggestedQuestions = ({ onSelectQuestion }) => {
  const suggestions = [
    { label: 'How many safety reports do we have?', icon: FileText },
    { label: 'What are the recurring safety patterns?', icon: Sparkles },
    { label: 'Show my overdue actions.', icon: CheckSquare },
    { label: 'Explain SIF-Potential classification.', icon: ShieldCheck },
    { label: 'What are common barrier concerns?', icon: AlertTriangle },
    { label: 'How do I submit a safety report?', icon: HelpCircle },
    { label: 'What is a near miss?', icon: HelpCircle },
  ];

  return (
    <div className="space-y-2 my-3">
      <p className="text-[10px] font-extrabold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
        <Sparkles className="w-3 h-3 text-amber-400" />
        Suggested Questions
      </p>
      <div className="flex flex-wrap gap-1.5">
        {suggestions.map((s, idx) => {
          const Icon = s.icon;
          return (
            <button
              key={idx}
              onClick={() => onSelectQuestion(s.label)}
              className="text-left text-[11px] px-2.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-amber-300 border border-slate-800 hover:border-amber-500/30 transition flex items-center gap-1.5 shadow-sm"
            >
              <Icon className="w-3 h-3 text-amber-400 shrink-0" />
              <span>{s.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
