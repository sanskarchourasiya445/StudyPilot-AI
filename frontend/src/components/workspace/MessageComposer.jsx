import React, { useState, useRef } from 'react';
import { Send, Sparkles, Layers, FileText, Video } from 'lucide-react';

const SUGGESTED_PROMPTS = [
  'Summarize the key concepts in this material',
  'What are the main definitions and differences?',
  'Explain the core structure step by step',
  'What key questions might appear on an exam?',
];

export function MessageComposer({
  onSend,
  isLoading = false,
  disabled = false,
  scope = { mode: 'all', resource_ids: [] },
  resources = [],
}) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  // Compute grounding label and icon
  const isAllMode = scope?.mode === 'all' || (!scope?.resource_ids?.length);
  let scopeLabel = `All Resources (${resources.length})`;
  let ScopeIcon = Layers;

  if (!isAllMode && scope?.resource_ids?.length > 0) {
    if (scope.resource_ids.length === 1) {
      const targetRes = resources.find(
        (r) => (r.resource_id || r.id) === scope.resource_ids[0]
      );
      let name = targetRes?.title || targetRes?.display_source || targetRes?.source || 'Study Material';
      if (name.includes('/') || name.includes('\\')) {
        name = name.split(/[/\\]/).pop();
      }
      scopeLabel = name;
      ScopeIcon = targetRes?.source_type === 'youtube' ? Video : FileText;
    } else {
      scopeLabel = `${scope.resource_ids.length} Selected Resources`;
      ScopeIcon = Layers;
    }
  }

  const handleSubmit = (e) => {
    e?.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || isLoading || disabled) return;
    onSend(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handlePromptClick = (prompt) => {
    onSend(prompt);
  };

  return (
    <div className="p-3 md:p-4 border-t border-white/[0.07] bg-[#0a0f18]">
      {/* Grounding Scope Indicator & Suggested Prompts Pills */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 mb-1 border-b border-white/[0.04]">
        <div className="flex items-center gap-1.5 text-[11px] text-[#9ca8ba] shrink-0">
          <span className="text-slate-500 font-semibold">Grounded in:</span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#0d1420] border border-white/[0.08] text-blue-400 font-medium max-w-[220px] sm:max-w-xs truncate">
            <ScopeIcon className="w-3 h-3 shrink-0" />
            <span className="truncate">{scopeLabel}</span>
          </span>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
          <div className="flex items-center gap-1 text-[11px] font-bold text-slate-500 uppercase tracking-wider shrink-0">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Prompts:</span>
          </div>
          {SUGGESTED_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePromptClick(prompt)}
              disabled={isLoading || disabled}
              className="px-2.5 py-0.5 rounded-full bg-[#0d1420] hover:bg-[#121c2b] text-[#9ca8ba] hover:text-[#f5f7fa] text-[11px] transition-colors shrink-0 border border-white/[0.08] hover:border-blue-500/40 font-medium"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2.5 relative">
        <div className="flex-1 relative bg-[#07090d] border border-white/[0.08] rounded-2xl focus-within:border-blue-500/60 focus-within:ring-1 focus-within:ring-blue-500/30 transition-all">
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              e.target.style.height = 'auto';
              e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your study material..."
            disabled={isLoading || disabled}
            className="w-full bg-transparent px-4 py-3 text-xs md:text-sm text-[#f5f7fa] placeholder:text-slate-500 focus:outline-none resize-none min-h-[44px] max-h-[120px]"
          />
        </div>

        <button
          type="submit"
          data-testid="send-message-button"
          disabled={!text.trim() || isLoading || disabled}
          className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 transition-all shadow-xs ${
            !text.trim() || isLoading || disabled
              ? 'bg-[#0d1420] text-slate-500 cursor-not-allowed border border-white/[0.08]'
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/30'
          }`}
          title="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
