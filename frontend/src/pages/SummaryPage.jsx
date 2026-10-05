import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { BookOpen, Sparkles } from 'lucide-react';
import { useResources } from '../hooks/useResources';
import { useSummary, useGenerateSummary, useDeleteSummary } from '../hooks/useStudy';
import { AppLayout } from '../components/layout/AppLayout';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { StructuredSummaryViewer } from '../components/study/StructuredSummaryViewer';
import { ResourceStudyHeader } from '../components/study/ResourceStudyHeader';

export function SummaryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const queryResourceId = searchParams.get('resource_id') || '';
  const { data: resources = [], isLoading: isLoadingResources } = useResources();

  const [selectedResourceId, setSelectedResourceId] = useState(queryResourceId);

  useEffect(() => {
    if (!selectedResourceId && resources.length > 0) {
      setSelectedResourceId(resources[0].resource_id);
    }
  }, [resources, selectedResourceId]);

  const { data: summary, isLoading: isLoadingSummary } = useSummary(selectedResourceId);
  const generateSummaryMutation = useGenerateSummary();
  const deleteSummaryMutation = useDeleteSummary();

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

  const handleGenerate = async (forceRegenerate = false) => {
    if (!selectedResourceId) return;
    try {
      await generateSummaryMutation.mutateAsync({
        resourceId: selectedResourceId,
        forceRegenerate,
      });
    } catch {
      // Toast handles error
    }
  };

  const handleDeleteSummary = async () => {
    if (!selectedResourceId) return;
    try {
      await deleteSummaryMutation.mutateAsync(selectedResourceId);
    } catch {
      // Toast handles error
    }
  };

  const summaryText = summary?.summary || summary?.summary_text || '';

  return (
    <AppLayout title="Study Summary">
      {/* Resource Context & Navigation Header */}
      <ResourceStudyHeader
        activeTab="summary"
        selectedResource={selectedResource}
        onCopy={summaryText ? () => navigator.clipboard.writeText(summaryText) : null}
        onRegenerate={() => handleGenerate(true)}
        onDeleteContent={summaryText ? handleDeleteSummary : null}
        isDeleteLoading={deleteSummaryMutation.isPending}
        deleteTitle="Delete Generated Summary?"
        deleteMessage="This will permanently remove the generated summary for this resource. You can regenerate it anytime."
      />

      {/* Main Content Area */}
      {!selectedResourceId ? (
        <Card className="text-center py-12">
          <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 mx-auto flex items-center justify-center mb-3">
            <BookOpen className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">No Resource Selected</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
            Select a study material above or upload a PDF document from the resources page.
          </p>
          <Button variant="primary" size="sm" onClick={() => navigate('/resources')}>
            View Study Resources
          </Button>
        </Card>
      ) : isLoadingSummary || generateSummaryMutation.isPending ? (
        <Card className="p-8 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-500 animate-spin" />
              <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
                {generateSummaryMutation.isPending ? 'Generating Map-Reduce AI Summary...' : 'Loading Summary...'}
              </span>
            </div>
            <Skeleton className="h-6 w-24" />
          </div>
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-24 w-full" />
        </Card>
      ) : summaryText ? (
        <StructuredSummaryViewer
          summaryData={summary}
          resourceTitle={selectedResource?.title || selectedResource?.source}
          onRegenerate={handleGenerate}
          isRegenerating={generateSummaryMutation.isPending}
        />
      ) : (
        <Card className="text-center py-12">
          <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 mx-auto flex items-center justify-center mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
            No Summary Generated Yet
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-6 max-w-md mx-auto">
            Click below to run map-reduce chunk summarization on "{selectedResource?.title || selectedResource?.source}".
          </p>
          <Button
            variant="primary"
            size="md"
            icon={Sparkles}
            onClick={() => handleGenerate(false)}
            isLoading={generateSummaryMutation.isPending}
          >
            Generate AI Summary
          </Button>
        </Card>
      )}
    </AppLayout>
  );
}
