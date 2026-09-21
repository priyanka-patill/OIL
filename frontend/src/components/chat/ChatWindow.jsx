import React, { useState, useEffect, useRef } from 'react';
import { chatApi } from '../../api/chatApi';
import { ChatMessage } from './ChatMessage';
import { SuggestedQuestions } from './SuggestedQuestions';
import {
  Flame,
  X,
  Send,
  Plus,
  RefreshCw,
  Sparkles,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';

export const ChatWindow = ({ onClose }) => {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      content:
        "Hello! I am the **OIL HSE Safety Assistant**.\n\nI can help you understand safety concepts, explore authorized safety reports and analytics, review assigned actions, and navigate the platform.\n\nWhat would you like to know today?",
      sources: [],
      actions: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend = null) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    setInput('');
    setError(null);

    // Optimistically append user message
    const userMsg = { id: `user-${Date.now()}`, sender: 'user', content: query };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await chatApi.sendMessage({
        message: query,
        conversation_id: conversationId
      });

      const data = res.data?.data || res.data;
      if (data) {
        if (data.conversation_id) setConversationId(data.conversation_id);
        const assistantMsg = {
          id: `asst-${Date.now()}`,
          sender: 'assistant',
          content: data.message,
          sources: data.sources || [],
          actions: data.actions || []
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch (err) {
      console.error('Chat API Error:', err);
      setError('AI assistant is temporarily unavailable. Please try again.');
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          content: '⚠️ Sorry, I could not process that request right now. Please check your connection or try again.'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setConversationId(null);
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        content:
          "Hello! I am the **OIL HSE Safety Assistant**.\n\nI can help you understand safety concepts, explore authorized safety reports and analytics, review assigned actions, and navigate the platform.\n\nWhat would you like to know today?",
        sources: [],
        actions: []
      }
    ]);
  };

  return (
    <div className="fixed bottom-20 right-4 sm:right-6 z-50 w-[92vw] sm:w-[420px] max-h-[82vh] h-[600px] bg-slate-950 border border-slate-800 rounded-3xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-bottom-5">
      {/* Header */}
      <div className="px-5 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-500 border border-amber-500/20 shadow">
            <Flame className="w-5 h-5 fill-amber-500/20" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-sm text-slate-100">OIL HSE Safety Assistant</h3>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <p className="text-[10px] text-amber-400 font-semibold tracking-wider uppercase">
              AI Safety Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleNewChat}
            title="New Chat Session"
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            title="Close Assistant"
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages Body */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-950/60">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} onActionClick={onClose} />
        ))}

        {/* Suggested Prompts when conversation is fresh */}
        {messages.length <= 2 && (
          <SuggestedQuestions onSelectQuestion={(promptText) => handleSend(promptText)} />
        )}

        {/* Typing Indicator */}
        {loading && (
          <div className="flex items-center gap-2.5 text-xs text-amber-400 font-medium py-2 px-3 bg-amber-500/10 border border-amber-500/20 rounded-2xl w-fit animate-pulse">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-amber-400" />
            Analyzing safety intelligence...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Composer Input Bar */}
      <div className="p-3 bg-slate-900 border-t border-slate-800 shrink-0 space-y-2">
        {error && (
          <div className="text-[11px] text-rose-400 bg-rose-500/10 border border-rose-500/20 p-2 rounded-xl flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about safety reports, metrics, or LOTO..."
            className="flex-1 bg-slate-950 border border-slate-800 focus:border-amber-500/50 text-xs text-white placeholder-slate-500 rounded-xl px-3.5 py-2.5 outline-none transition"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className={`p-2.5 rounded-xl font-bold text-xs flex items-center justify-center transition shadow ${
              loading || !input.trim()
                ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                : 'bg-amber-500 hover:bg-amber-400 text-slate-950'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
