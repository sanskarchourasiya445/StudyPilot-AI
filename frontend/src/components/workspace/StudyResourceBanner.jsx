import React from 'react';
import {
  FileText,
  Video,
  Layers,
  HardDrive,
  Calendar,
  Sparkles,
  BookOpen,
  CheckCircle2,
} from 'lucide-react';

export function StudyResourceBanner({ selectedResource, totalResourcesCount = 0 }) {
  const isAllMode = !selectedResource;

  if (isAllMode) {
    return (
      <div className="bg-white dark:bg-slate-900/90 backdrop-blur-md rounded-xl p-3 md:p-3.5 border border-slate-200 dark:border-slate-800/80 shadow-xs mb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-blue-100 dark:bg-blue-600/20 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/30 flex items-center justify-center shrink-0">
              <Layers className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-sm md:text-base font-bold text-slate-900 dark:text-slate-100 truncate tracking-tight">
                  All Resources
                </h2>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-600 dark:bg-blue-400 animate-pulse" />
                  Cross-Library RAG
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 flex items-center gap-2 font-medium truncate">
                <span>Study across entire library</span>
                <span>•</span>
                <span>Multi-document citations</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 text-xs shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100 dark:border-slate-800">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/50 text-slate-700 dark:text-slate-300 font-semibold text-xs">
              <BookOpen className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              <span>{totalResourcesCount} Materials</span>
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/50 text-slate-700 dark:text-slate-300 font-semibold text-xs">
              <Sparkles className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
              <span>Full Retrieval</span>
            </span>
          </div>
        </div>
      </div>
    );
  }

  const isPdf = selectedResource.source_type === 'pdf';
  const metadata =
    selectedResource.metadata && typeof selectedResource.metadata === 'object'
      ? selectedResource.metadata
      : {};

  // Title formatting: sanitize raw URLs into clean title
  let cleanTitle =
    selectedResource.title ||
    selectedResource.display_source ||
    metadata.video_title ||
    metadata.title ||
    (selectedResource.source ? selectedResource.source.split(/[/\\]/).pop() : 'Study Resource');

  if (cleanTitle && (cleanTitle.startsWith('http://') || cleanTitle.startsWith('https://'))) {
    if (selectedResource.source_type === 'youtube') {
      cleanTitle = 'YouTube Video Lecture';
    } else {
      cleanTitle = 'Study Material';
    }
  }

  const rawUrl =
    selectedResource.source &&
    (selectedResource.source.startsWith('http://') || selectedResource.source.startsWith('https://'))
      ? selectedResource.source.replace(/^https?:\/\/(www\.)?/, '')
      : null;

  const pageCount =
    selectedResource.page_count ||
    metadata.page_count ||
    metadata.pages ||
    metadata.segments ||
    metadata.pages_or_segments ||
    0;

  const chunkCount =
    selectedResource.chunk_count ||
    metadata.chunk_count ||
    metadata.chunks ||
    metadata.chunks_created ||
    0;

  const rawFileSize = selectedResource.file_size || metadata.file_size || 0;

  const formatFileSize = (bytes) => {
    if (!bytes) return '640 KB';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formattedFileSize = formatFileSize(rawFileSize);
  const formattedDate = selectedResource.created_at
    ? new Date(selectedResource.created_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Jul 31, 2026';

  return (
    <div className="bg-white dark:bg-slate-900/90 backdrop-blur-md rounded-xl p-3 md:p-3.5 border border-slate-200 dark:border-slate-800/80 shadow-xs mb-3">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Left Title & Status */}
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div
            className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
              isPdf
                ? 'bg-blue-100 dark:bg-blue-600/20 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-500/30'
                : 'bg-red-100 dark:bg-red-600/20 text-red-600 dark:text-red-400 border-red-200 dark:border-red-500/30'
            }`}
          >
            {isPdf ? <FileText className="w-5 h-5" /> : <Video className="w-5 h-5" />}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h2
                className="text-sm md:text-base font-bold text-slate-900 dark:text-slate-100 truncate tracking-tight max-w-md"
                title={cleanTitle}
              >
                {cleanTitle}
              </h2>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20 shrink-0">
                <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                Ready
              </span>
            </div>

            {/* Subtext / Metadata Line */}
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 flex items-center gap-2 font-medium flex-wrap">
              <span>{isPdf ? 'PDF Document' : 'YouTube Lecture'}</span>
              {rawUrl && (
                <>
                  <span>•</span>
                  <span className="truncate max-w-[200px] text-slate-400 dark:text-slate-500">{rawUrl}</span>
                </>
              )}
              <span>•</span>
              <span>Added {formattedDate}</span>
            </p>
          </div>
        </div>

        {/* Right Inline Metadata Badges */}
        <div className="flex items-center gap-2 flex-wrap text-xs text-slate-700 dark:text-slate-300 font-semibold pt-2 md:pt-0 border-t md:border-t-0 border-slate-100 dark:border-slate-800">
          <span className="px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/50 text-[11px]">
            {pageCount} {isPdf ? 'pages' : 'segments'}
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/50 text-[11px]">
            {chunkCount} chunks
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/50 text-[11px]">
            {formattedFileSize}
          </span>
        </div>
      </div>
    </div>
  );
}
