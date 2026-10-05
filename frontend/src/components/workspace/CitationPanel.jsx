import React from 'react';
import { BookOpen, ExternalLink, X, FileText, Video } from 'lucide-react';

export function CitationPanel({ citations = [], onClose, selectedCitationIndex = null }) {
  if (!citations || citations.length === 0) {
    return (
      <div className="h-full bg-[#0a0f18] p-5 flex flex-col justify-between">
        <div className="flex flex-col items-center justify-center text-center my-auto">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/10 text-blue-400 flex items-center justify-center mb-3 border border-blue-500/20">
            <BookOpen className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-bold text-[#f5f7fa]">
            Grounded Sources
          </h4>
          <p className="text-xs text-[#9ca8ba] mt-1 max-w-xs leading-relaxed">
            These sources support the answer with verified content from your study material.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-[#0a0f18] flex flex-col justify-between">
      {/* Panel Header */}
      <div>
        <div className="p-4 border-b border-white/[0.07] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center font-bold">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-[#f5f7fa] uppercase tracking-wider">
                Grounded Sources
              </h3>
              <p className="text-[11px] text-[#9ca8ba] mt-0.5">
                Verified content from study material.
              </p>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Citations List */}
        <div className="overflow-y-auto no-scrollbar p-3 space-y-2.5 max-h-[calc(100vh-220px)]">
          {citations.map((source, idx) => {
            const isHighlighted = selectedCitationIndex === idx;
            const meta = source.metadata || {};
            const rawType = source.source_type || meta.source_type || meta.resource_type || '';
            const isYoutube = rawType === 'youtube' || 
              (typeof source.source === 'string' && (source.source.includes('youtube.com') || source.source.includes('youtu.be')));
            const isPdf = !isYoutube;

            let cleanSourceTitle = source.title || meta.title || source.source || meta.source || `Source ${idx + 1}`;
            if (cleanSourceTitle.includes('/') || cleanSourceTitle.includes('\\')) {
              cleanSourceTitle = cleanSourceTitle.split(/[/\\]/).pop();
            }

            const pageNum = source.page || meta.page || meta.page_number;
            const segmentNum = source.segment || meta.segment || (meta.chunk_index !== undefined ? (Number(meta.chunk_index) + 1) : null);
            const locationText = isPdf
              ? (pageNum ? `Page ${pageNum}` : 'Document Excerpt')
              : (segmentNum ? `Transcript Segment ${segmentNum}` : 'Video Transcript');

            return (
              <div
                key={idx}
                id={`citation-${idx}`}
                className={`p-3 rounded-xl border transition-all ${
                  isHighlighted
                    ? 'border-blue-500 bg-blue-600/15 ring-1 ring-blue-500/30'
                    : 'border-white/[0.07] bg-[#0d1420] hover:border-blue-500/40'
                }`}
              >
                {/* Header line with Blue Index Badge & Title */}
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-5 h-5 rounded-md bg-blue-600/20 text-blue-400 border border-blue-500/30 font-bold text-[11px] flex items-center justify-center shrink-0">
                      {idx + 1}
                    </span>
                    <span className="font-bold text-xs text-[#f5f7fa] truncate">
                      {cleanSourceTitle}
                    </span>
                  </div>
                  {isYoutube ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20 shrink-0">
                      <Video className="w-3 h-3" />
                      YouTube
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20 shrink-0">
                      <FileText className="w-3 h-3" />
                      PDF
                    </span>
                  )}
                </div>

                {/* Subtitle location badge */}
                <p className="text-[11px] text-[#9ca8ba] mb-1.5 font-medium">
                  {locationText}
                </p>

                {/* Snippet preview */}
                <p className="text-xs text-[#9ca8ba] leading-relaxed font-sans line-clamp-3 italic bg-[#07090d]/80 p-2.5 rounded-lg border border-white/[0.05]">
                  "{source.content || source.text}"
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
