import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { NotebookPen, Sparkles, Copy, Check, RefreshCw, List, LayoutGrid, FileText } from 'lucide-react';
import { useResources } from '../hooks/useResources';
import { useNotes, useGenerateNotes, useDeleteNotes } from '../hooks/useStudy';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { ResourceStudyHeader } from '../components/study/ResourceStudyHeader';

export function NotesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const queryResourceId = searchParams.get('resource_id') || '';
  const { data: resources = [], isLoading: isLoadingResources } = useResources();

  const [selectedResourceId, setSelectedResourceId] = useState(queryResourceId);
  const [noteStyle, setNoteStyle] = useState('bullet'); // 'bullet' | 'cornell'
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!selectedResourceId && resources.length > 0) {
      setSelectedResourceId(resources[0].resource_id);
    }
  }, [resources, selectedResourceId]);

  const { data: notes, isLoading: isLoadingNotes } = useNotes(selectedResourceId, noteStyle);
  const generateNotesMutation = useGenerateNotes();
  const deleteNotesMutation = useDeleteNotes();

  const selectedResource = resources.find((r) => r.resource_id === selectedResourceId);

  const handleSelectResource = (resId) => {
    setSelectedResourceId(resId);
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      if (resId) p.set('resource_id', resId);
      else p.delete('resource_id');
      return p;
    });
  };

  const handleGenerate = async (styleToUse = noteStyle) => {
    if (!selectedResourceId) return;
    try {
      await generateNotesMutation.mutateAsync({
        resourceId: selectedResourceId,
        style: styleToUse,
      });
    } catch {
      // Toast handles error
    }
  };

  const handleDeleteNotes = async () => {
    if (!selectedResourceId) return;
    try {
      await deleteNotesMutation.mutateAsync({
        resourceId: selectedResourceId,
        style: noteStyle,
      });
    } catch {
      // Toast handles error
    }
  };

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
      parsedCornell = typeof noteText === 'string' && noteText.startsWith('{') ? JSON.parse(noteText) : noteText;
    } catch {
      parsedCornell = null;
    }
  }

  return (
    <AppLayout title="Study Notes">
      {/* Resource Context & Navigation Header */}
      <ResourceStudyHeader
        activeTab="notes"
        selectedResource={selectedResource}
        onCopy={noteText ? handleCopy : null}
        onRegenerate={() => handleGenerate(noteStyle)}
        onDeleteContent={noteText ? handleDeleteNotes : null}
        isDeleteLoading={deleteNotesMutation.isPending}
        deleteTitle="Delete Generated Notes?"
        deleteMessage={`This will permanently remove the generated ${noteStyle} notes for this resource. You can regenerate them anytime.`}
      />

      {/* Note Style Switcher Bar */}
      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              Note Style:
            </span>
            <div className="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
              <button
                onClick={() => {
                  setNoteStyle('bullet');
                  if (notes && notes.style !== 'bullet') handleGenerate('bullet');
                }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                  noteStyle === 'bullet'
                    ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
                }`}
              >
                <List className="w-3.5 h-3.5" />
                <span>Bullet Points</span>
              </button>

              <button
                onClick={() => {
                  setNoteStyle('cornell');
                  if (notes && notes.style !== 'cornell') handleGenerate('cornell');
                }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                  noteStyle === 'cornell'
                    ? 'bg-white dark:bg-slate-800 text-purple-600 dark:text-purple-400 shadow-sm'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
                }`}
              >
                <LayoutGrid className="w-3.5 h-3.5" />
                <span>Cornell Format</span>
              </button>
            </div>
          </div>

          {notes && (
            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
              <Button variant="outline" size="sm" icon={copied ? Check : Copy} onClick={handleCopy}>
                {copied ? 'Copied' : 'Copy Notes'}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                icon={RefreshCw}
                onClick={() => handleGenerate(noteStyle)}
                isLoading={generateNotesMutation.isPending}
              >
                Regenerate Notes
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Render Note Views */}
      {!selectedResourceId ? (
        <Card className="text-center py-12">
          <div className="w-12 h-12 rounded-2xl bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 mx-auto flex items-center justify-center mb-3">
            <NotebookPen className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">No Resource Selected</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
            Select a study resource to view or generate structured notes.
          </p>
          <Button variant="primary" size="sm" onClick={() => navigate('/resources')}>
            View Resources
          </Button>
        </Card>
      ) : isLoadingNotes || generateNotesMutation.isPending ? (
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

            {/* Bottom Summary & Key Takeaways Row */}
            <Card className="border-t-4 border-t-blue-500 bg-blue-50/20 dark:bg-blue-950/20">
              <CardHeader>
                <CardTitle className="text-xs font-bold text-blue-700 dark:text-blue-300 uppercase tracking-wider">
                  Summary & Key Takeaways
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-800 dark:text-slate-200 font-sans leading-relaxed">
                  {parsedCornell.summary || 'Summary generated from study material notes.'}
                </p>
              </CardContent>
            </Card>
          </div>
        ) : (
          /* Bullet Points Layout */
          <Card className="p-6 md:p-8">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-700/50 mb-6">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                Bullet Study Notes ({selectedResource?.title || selectedResource?.source})
              </h3>
            </div>
            <div className="prose dark:prose-invert max-w-none text-sm text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
              {noteText}
            </div>
          </Card>
        )
      ) : (
        <Card className="text-center py-12">
          <div className="w-12 h-12 rounded-2xl bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400 mx-auto flex items-center justify-center mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
            No Notes Generated Yet
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-6 max-w-md mx-auto">
            Click below to generate structured {noteStyle === 'bullet' ? 'Bullet Point' : 'Cornell Format'} notes from your study material.
          </p>
          <Button
            variant="primary"
            size="md"
            icon={Sparkles}
            onClick={() => handleGenerate(noteStyle)}
            isLoading={generateNotesMutation.isPending}
          >
            Generate Study Notes
          </Button>
        </Card>
      )}
    </AppLayout>
  );
}
