import React from 'react';
import { BookOpen, Sparkles, FileText, Layers } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Skeleton } from '../ui/Skeleton';
import { StructuredSummaryViewer } from '../study/StructuredSummaryViewer';

export function SummaryTab({
  selectedResource,
  summary,
  isLoadingSummary,
  isGenerating,
  onGenerateSummary,
}) {
  const summaryText = summary?.summary || summary?.summary_text || '';

  if (!selectedResource) {
    return (
      <div className="text-center py-16 my-4 p-8 rounded-2xl bg-[#0d1420] border border-white/[0.07]">
        <div className="w-12 h-12 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 mx-auto flex items-center justify-center mb-3.5">
          <Layers className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-[#f5f7fa]">
          Select a Single Resource
        </h3>
        <p className="text-xs text-[#9ca8ba] mt-1.5 mb-2 max-w-md mx-auto leading-relaxed">
          AI Summarization generates an in-depth map-reduce digest for an individual document or video. Please select a specific resource from the top selector.
        </p>
      </div>
    );
  }

  if (isLoadingSummary || isGenerating) {
    return (
      <div className="p-8 my-4 space-y-4 rounded-2xl bg-[#0d1420] border border-white/[0.07]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-blue-400 animate-spin" />
            <span className="text-sm font-bold text-[#f5f7fa]">
              {isGenerating
                ? 'Synthesizing Map-Reduce AI Summary...'
                : 'Loading Stored Summary...'}
            </span>
          </div>
          <Skeleton className="h-6 w-24 bg-white/[0.05]" />
        </div>
        <Skeleton className="h-4 w-full bg-white/[0.05]" />
        <Skeleton className="h-4 w-full bg-white/[0.05]" />
        <Skeleton className="h-4 w-3/4 bg-white/[0.05]" />
        <Skeleton className="h-32 w-full bg-white/[0.05] rounded-xl" />
      </div>
    );
  }

  if (summaryText) {
    return (
      <div className="my-4">
        <StructuredSummaryViewer
          summaryData={summary}
          resourceTitle={selectedResource.title || selectedResource.display_source}
          onRegenerate={() => onGenerateSummary(true)}
          isRegenerating={isGenerating}
        />
      </div>
    );
  }

  return (
    <div className="text-center py-16 my-4 p-8 rounded-2xl bg-[#0d1420] border border-white/[0.07]">
      <div className="w-12 h-12 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 mx-auto flex items-center justify-center mb-3.5">
        <Sparkles className="w-6 h-6" />
      </div>
      <h3 className="text-base font-bold text-[#f5f7fa]">
        No Summary Generated Yet
      </h3>
      <p className="text-xs text-[#9ca8ba] mt-1.5 mb-6 max-w-md mx-auto leading-relaxed">
        Run map-reduce summarization on &ldquo;{selectedResource.title || selectedResource.display_source}&rdquo; to extract key concepts, technical takeaways, and executive insights.
      </p>
      <Button
        variant="primary"
        size="md"
        icon={Sparkles}
        onClick={() => onGenerateSummary(false)}
        isLoading={isGenerating}
      >
        Generate AI Summary
      </Button>
    </div>
  );
}
