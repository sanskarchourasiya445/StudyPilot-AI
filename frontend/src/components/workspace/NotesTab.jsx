import React, { useState, useEffect } from 'react';
import {
  NotebookPen,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  List,
  LayoutGrid,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Skeleton } from '../ui/Skeleton';

export function NotesTab({
  selectedResource,
  notes,
  isLoadingNotes,
  isGenerating,
  noteStyle,
  setNoteStyle,
  onChangeStyle,
  onGenerateNotes,
  isResourceProcessing = false,
  isResourceFailed = false,
  isResourceReady = true,
}) {
  const [copied, setCopied] = useState(false);
  const updateStyle = onChangeStyle || setNoteStyle;

  // Reset copy feedback when resource switches
  useEffect(() => {
    setCopied(false);
  }, [selectedResource?.resource_id || selectedResource?.id]);

  const noteText = notes?.content || notes?.notes_content || '';

  const handleCopy = () => {
    if (!noteText) return;
    navigator.clipboard.writeText(noteText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  let parsedCornell = null;
  if (notes && notes.style === 'cornell' && noteText) {
    try {
      parsedCornell =
        typeof noteText === 'string' && noteText.startsWith('{')
          ? JSON.parse(noteText)
          : noteText;
    } catch {
      parsedCornell = null;
    }
  }

  if (!selectedResource) {
    return (
      <Card className="text-center py-12 my-4">
        <div className="w-12 h-12 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 mx-auto flex items-center justify-center mb-3">
          <NotebookPen className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-[#f5f7fa]">
          Single Resource Required
        </h3>
        <p className="text-xs text-[#9ca8ba] mt-1 mb-4 max-w-md mx-auto">
          Study Notes generation requires selecting a single study resource. Please select a specific resource from the top picker.
        </p>
      </Card>
    );
  }

  if (isResourceProcessing) {
    return (
      <Card className="text-center py-16 my-4 bg-[#0a0f18] border-white/[0.08]">
        <div className="w-12 h-12 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 mx-auto flex items-center justify-center mb-3.5">
          <Sparkles className="w-6 h-6 text-blue-400 animate-spin" />
        </div>
        <h3 className="text-base font-bold text-[#f5f7fa]">
          Resource is Still Processing
        </h3>
        <p className="text-xs text-[#9ca8ba] mt-1.5 mb-4 max-w-md mx-auto leading-relaxed">
          &ldquo;{selectedResource.title || selectedResource.display_source || 'Study Material'}&rdquo; is being parsed and indexed into the vector store. Notes generation will become available immediately once processing is complete.
        </p>
        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-600/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
          Processing Ingestion...
        </span>
      </Card>
    );
  }

  if (isResourceFailed) {
    return (
      <Card className="text-center py-16 my-4 bg-[#0a0f18] border-red-500/20">
        <div className="w-12 h-12 rounded-2xl bg-red-600/10 text-red-400 border border-red-500/20 mx-auto flex items-center justify-center mb-3.5">
          <NotebookPen className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-red-400">
          Resource Processing Failed
        </h3>
        <p className="text-xs text-[#9ca8ba] mt-1.5 mb-2 max-w-md mx-auto leading-relaxed">
          Ingestion for &ldquo;{selectedResource.title || selectedResource.display_source}&rdquo; encountered an error during parsing. Please check or re-upload the document.
        </p>
      </Card>
    );
  }

  const hasNotesForCurrentStyle =
    notes && notes.style === noteStyle && Boolean(noteText);

  return (
    <div className="space-y-4 my-4">
      {/* Note Style Switcher Bar */}
      <Card className="p-4 bg-[#0a0f18] border-white/[0.08]">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-bold text-[#9ca8ba] uppercase tracking-wider">
              Note Style:
            </span>
            <div className="flex bg-[#07090d] p-1 rounded-xl border border-white/[0.08]">
              <button
                type="button"
                onClick={() => updateStyle?.('bullet')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  noteStyle === 'bullet'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-[#9ca8ba] hover:text-[#f5f7fa]'
                }`}
              >
                <List className="w-3.5 h-3.5" />
                <span>Bullet Points</span>
              </button>

              <button
                type="button"
                onClick={() => updateStyle?.('cornell')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  noteStyle === 'cornell'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-[#9ca8ba] hover:text-[#f5f7fa]'
                }`}
              >
                <LayoutGrid className="w-3.5 h-3.5" />
                <span>Cornell Format</span>
              </button>
            </div>
          </div>

          {hasNotesForCurrentStyle && (
            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
              <Button
                variant="outline"
                size="sm"
                icon={copied ? Check : Copy}
                onClick={handleCopy}
              >
                {copied ? 'Copied' : 'Copy Notes'}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                icon={RefreshCw}
                onClick={() => onGenerateNotes(noteStyle, true)}
                isLoading={isGenerating}
              >
                Regenerate
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Content Render Area */}
      {isLoadingNotes || isGenerating ? (
        <Card className="p-8 space-y-4 bg-[#0a0f18] border-white/[0.08]">
          <div className="flex items-center gap-2.5 mb-2">
            <Sparkles className="w-4 h-4 text-blue-400 animate-spin" />
            <span className="text-xs font-bold text-[#f5f7fa]">
              {isGenerating ? 'Structuring study notes with AI Engine...' : 'Loading cached study notes...'}
            </span>
          </div>
          <Skeleton className="h-4 w-full bg-white/[0.05]" />
          <Skeleton className="h-4 w-full bg-white/[0.05]" />
          <Skeleton className="h-4 w-2/3 bg-white/[0.05]" />
        </Card>
      ) : hasNotesForCurrentStyle ? (
        notes.style === 'cornell' && parsedCornell ? (
          /* Cornell 2-Column Grid Layout */
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Left Column: Cues & Key Concepts (1 col) */}
              <div className="md:col-span-1 rounded-2xl p-4 bg-[#0a0f18] border border-white/[0.08] border-l-2 border-l-blue-500">
                <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-3">
                  Recall Cues / Questions
                </h4>
                <ul className="space-y-2 text-xs font-medium text-[#f5f7fa]">
                  {parsedCornell.cues?.map((cue, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-blue-500 font-bold">&bull;</span>
                      <span>{cue}</span>
                    </li>
                  )) || <li className="text-[#9ca8ba]">No cues defined</li>}
                </ul>
              </div>

              {/* Right Column: Main Notes & Explanations (2 cols) */}
              <div className="md:col-span-2 rounded-2xl p-5 bg-[#0a0f18] border border-white/[0.08]">
                <h4 className="text-xs font-bold text-[#9ca8ba] uppercase tracking-wider mb-3">
                  Lecture & Reading Notes
                </h4>
                <div className="text-xs md:text-sm text-[#f5f7fa] leading-relaxed whitespace-pre-wrap font-sans">
                  {parsedCornell.notes || noteText}
                </div>
              </div>
            </div>

            {/* Bottom Summary Row */}
            <div className="rounded-2xl p-4 bg-[#0a0f18] border border-white/[0.08] border-t-2 border-t-blue-500">
              <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-1.5">
                Summary & Synthesis
              </h4>
              <p className="text-xs text-[#9ca8ba] font-sans leading-relaxed">
                {parsedCornell.summary || 'Summary synthesized from study material.'}
              </p>
            </div>
          </div>
        ) : (
          /* Bullet Points Layout */
          <div className="p-6 md:p-8 rounded-2xl bg-[#0a0f18] border border-white/[0.08]">
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.07] mb-6">
              <div>
                <h3 className="text-base font-bold text-[#f5f7fa]">
                  {selectedResource.title || selectedResource.display_source}
                </h3>
                <span className="text-[11px] text-[#9ca8ba]">
                  Bullet Point Study Guide
                </span>
              </div>
            </div>
            <div className="max-w-none text-xs md:text-sm text-[#f5f7fa] leading-relaxed whitespace-pre-wrap font-sans">
              {noteText}
            </div>
          </div>
        )
      ) : (
        <Card className="text-center py-16 bg-[#0a0f18] border-white/[0.08]">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 mx-auto flex items-center justify-center mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-[#f5f7fa]">
            No {noteStyle === 'bullet' ? 'Bullet Point' : 'Cornell'} Notes Generated Yet
          </h3>
          <p className="text-xs text-[#9ca8ba] mt-1 mb-6 max-w-md mx-auto leading-relaxed">
            Click below to generate structured{' '}
            {noteStyle === 'bullet' ? 'Bullet Point' : 'Cornell Format'} notes for &ldquo;
            {selectedResource.title || selectedResource.display_source}&rdquo;.
          </p>
          <Button
            variant="primary"
            size="md"
            icon={Sparkles}
            onClick={() => onGenerateNotes(noteStyle, false)}
            isLoading={isGenerating}
          >
            Generate {noteStyle === 'bullet' ? 'Bullet Notes' : 'Cornell Notes'}
          </Button>
        </Card>
      )}
    </div>
  );
}
