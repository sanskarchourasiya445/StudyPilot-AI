import React, { useState, useRef } from 'react';
import { Send, Sparkles } from 'lucide-react';

const SUGGESTED_PROMPTS = [
  'Summarize the key concepts in this material',
  'What are the main definitions and differences?',
  'Explain the core structure step by step',
  'What key questions might appear on an exam?',
];

export function MessageComposer({ onSend, isLoading = false, disabled = false }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

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
      {/* Suggested Prompts Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2.5 mb-2 no-scrollbar">
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
            className="px-3 py-1 rounded-full bg-[#0d1420] hover:bg-[#121c2b] text-[#9ca8ba] hover:text-[#f5f7fa] text-xs transition-colors shrink-0 border border-white/[0.08] hover:border-blue-500/40 font-medium"
          >
            {prompt}
          </button>
        ))}
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
