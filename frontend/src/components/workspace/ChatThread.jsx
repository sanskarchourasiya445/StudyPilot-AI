import React, { useState } from 'react';
import { Bot, User, Copy, Check, ThumbsUp, ThumbsDown, BookOpen, Loader2 } from 'lucide-react';

export function ChatThread({ messages = [], isLoading = false, onSelectCitation }) {
  const [copiedIdx, setCopiedIdx] = useState(null);
  const [feedbackState, setFeedbackState] = useState({});

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const handleFeedback = (idx, type) => {
    setFeedbackState((prev) => ({
      ...prev,
      [idx]: prev[idx] === type ? null : type,
    }));
  };

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center">
        <div className="w-14 h-14 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center mb-4 shadow-sm">
          <Bot className="w-7 h-7 text-blue-400" />
        </div>
        <h3 className="text-lg font-bold text-[#f5f7fa]">
          StudyPilot AI Workspace
        </h3>
        <p className="text-xs text-[#9ca8ba] mt-1 max-w-md">
          Ask questions about your uploaded materials. Answers are grounded in retrieved source chunks with verified citations.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto no-scrollbar p-4 md:p-6 space-y-6">
      {messages.map((msg, idx) => {
        const isUser = msg.sender === 'user' || msg.role === 'user';
        const sources = msg.sources || (msg.metadata_json && msg.metadata_json.sources) || [];

        return (
          <div
            key={idx}
            className={`flex items-start gap-3 max-w-3xl ${
              isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
            }`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 ${
                isUser
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'bg-blue-600/10 text-blue-400 border border-blue-500/20'
              }`}
            >
              {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4.5 h-4.5" />}
            </div>

            {/* Bubble Container */}
            <div className="space-y-1.5 max-w-[88%]">
              <div
                className={`p-4 rounded-2xl text-xs md:text-sm leading-relaxed shadow-xs relative ${
                  isUser
                    ? 'bg-blue-600 text-white rounded-tr-none shadow-blue-600/20'
                    : 'bg-[#0d1420] text-[#f5f7fa] border border-white/[0.07] rounded-tl-none'
                }`}
              >
                {/* Assistant Header Action Buttons (Copy, Like, Dislike) */}
                {!isUser && (
                  <div className="flex items-center justify-end gap-2 mb-2 pb-1 border-b border-white/[0.05]">
                    <button
                      onClick={() => handleCopy(msg.content || msg.answer, idx)}
                      className="p-1 rounded text-slate-400 hover:text-white transition-colors"
                      title="Copy response"
                    >
                      {copiedIdx === idx ? <Check className="w-3.5 h-3.5 text-blue-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      onClick={() => handleFeedback(idx, 'up')}
                      className={`p-1 rounded transition-colors ${
                        feedbackState[idx] === 'up' ? 'text-blue-400' : 'text-slate-400 hover:text-white'
                      }`}
                      title="Helpful"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleFeedback(idx, 'down')}
                      className={`p-1 rounded transition-colors ${
                        feedbackState[idx] === 'down' ? 'text-red-400' : 'text-slate-400 hover:text-white'
                      }`}
                      title="Not helpful"
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                <div className="whitespace-pre-wrap font-sans text-xs md:text-sm">
                  {msg.content || msg.answer || msg.text}
                </div>

                {/* Citation Pills at Bottom of Message */}
                {!isUser && sources.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-3 mt-3 border-t border-white/[0.05]">
                    {sources.map((source, sIdx) => {
                      let cleanTitle = source.title || source.source || 'Doc';
                      if (cleanTitle.includes('/') || cleanTitle.includes('\\')) {
                        cleanTitle = cleanTitle.split(/[/\\]/).pop();
                      }
                      const pageNum = source.page ? ` · p.${source.page}` : '';

                      return (
                        <button
                          key={sIdx}
                          onClick={() => onSelectCitation && onSelectCitation(sIdx, sources)}
                          className="px-2.5 py-1 rounded-lg bg-[#101827] hover:bg-[#121c2b] border border-white/[0.08] hover:border-blue-500/40 text-slate-300 text-[11px] font-medium transition-colors flex items-center gap-1.5"
                        >
                          <span className="w-4 h-4 rounded bg-blue-600/20 font-bold text-[10px] text-blue-400 flex items-center justify-center">
                            {sIdx + 1}
                          </span>
                          <span>{cleanTitle}{pageNum}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Timestamp */}
              <div className={`text-[10px] text-slate-500 font-medium ${isUser ? 'text-right' : 'text-left'}`}>
                Active Study Session
              </div>
            </div>
          </div>
        );
      })}

      {/* Assistant Thinking Loading State */}
      {isLoading && (
        <div className="flex items-start gap-3 mr-auto max-w-xl">
          <div className="w-8 h-8 rounded-xl bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center font-bold text-xs shrink-0 shadow-xs animate-pulse">
            <Bot className="w-4.5 h-4.5" />
          </div>
          <div className="p-4 rounded-2xl bg-[#0d1420] border border-white/[0.07] rounded-tl-none shadow-xs flex items-center gap-2 text-xs text-[#9ca8ba]">
            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
            <span>Analyzing study materials & retrieving RAG citations...</span>
          </div>
        </div>
      )}
    </div>
  );
}
