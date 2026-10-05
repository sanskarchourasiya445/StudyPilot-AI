import React, { useState } from 'react';
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
}) {
  const [copied, setCopied] = useState(false);
  const updateStyle = onChangeStyle || setNoteStyle;

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

  return (
    <div className="space-y-4 my-4">
      {/* Note Style Switcher Bar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[#9ca8ba] uppercase tracking-wider">
              Note Style:
            </span>
            <div className="flex bg-[#0a0f18] p-1 rounded-xl border border-white/[0.08]">
              <button
                onClick={() => {
                  updateStyle?.('bullet');
                  if (!notes || notes.style !== 'bullet') onGenerateNotes('bullet');
                }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  noteStyle === 'bullet'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-[#9ca8ba] hover:text-[#f5f7fa]'
                }`}
              >
                <List className="w-3.5 h-3.5" />
                <span>Bullet Points</span>
              </button>

              <button
                onClick={() => {
                  updateStyle?.('cornell');
                  if (!notes || notes.style !== 'cornell') onGenerateNotes('cornell');
                }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
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

          {notes && (
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
                onClick={() => onGenerateNotes(noteStyle)}
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
        <Card className="p-8 space-y-4">
          <Skeleton className="h-6 w-48 mb-4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </Card>
      ) : notes ? (
        notes.style === 'cornell' && parsedCornell ? (
          /* Cornell 2-Column Grid Layout */
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Left Column: Cues & Key Concepts (1 col) */}
              <Card className="md:col-span-1 border-l-4 border-l-purple-500 bg-purple-50/20 dark:bg-purple-950/20">
                <CardHeader>
                  <CardTitle className="text-xs font-bold text-purple-700 dark:text-purple-300 uppercase tracking-wider">
                    Cue Column / Key Concepts
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-xs font-semibold text-slate-800 dark:text-slate-200">
                    {parsedCornell.cues?.map((cue, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-purple-600 font-bold">&bull;</span>
                        <span>{cue}</span>
                      </li>
                    )) || <li>No cues defined</li>}
                  </ul>
                </CardContent>
              </Card>

              {/* Right Column: Main Notes & Explanations (2 cols) */}
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Detailed Notes & Explanations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose dark:prose-invert max-w-none text-xs text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
                    {parsedCornell.notes || noteText}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Bottom Summary Row */}
            <Card className="border-t-4 border-t-blue-500 bg-blue-50/20 dark:bg-blue-950/20">
              <CardHeader>
                <CardTitle className="text-xs font-bold text-blue-700 dark:text-blue-300 uppercase tracking-wider">
                  Summary & Key Takeaways
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-800 dark:text-slate-200 font-sans leading-relaxed">
                  {parsedCornell.summary ||
                    'Summary generated from study material notes.'}
                </p>
              </CardContent>
            </Card>
          </div>
        ) : (
          /* Bullet Points Layout */
          <Card className="p-6 md:p-8">
            <div className="flex items-center justify-between pb-4 border-b border-white/[0.07] mb-6">
              <h3 className="text-lg font-bold text-[#f5f7fa]">
                Study Notes: {selectedResource.title || selectedResource.display_source}
              </h3>
            </div>
            <div className="max-w-none text-sm text-[#f5f7fa] leading-relaxed whitespace-pre-wrap font-sans">
              {noteText}
            </div>
          </Card>
        )
      ) : (
        <Card className="text-center py-12">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 mx-auto flex items-center justify-center mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-[#f5f7fa]">
            No Notes Generated Yet
          </h3>
          <p className="text-xs text-[#9ca8ba] mt-1 mb-6 max-w-md mx-auto">
            Click below to generate structured{' '}
            {noteStyle === 'bullet' ? 'Bullet Point' : 'Cornell Format'} notes from "
            {selectedResource.title || selectedResource.display_source}".
          </p>
          <Button
            variant="primary"
            size="md"
            icon={Sparkles}
            onClick={() => onGenerateNotes(noteStyle)}
            isLoading={isGenerating}
          >
            Generate Study Notes
          </Button>
        </Card>
      )}
    </div>
  );
}
