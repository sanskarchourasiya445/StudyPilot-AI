import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileText,
  Video,
  MessageSquare,
  Trash2,
  ArrowLeft,
  ExternalLink,
  BookOpen,
} from 'lucide-react';
import { useResource, useDeleteResource } from '../hooks/useResources';
import { AppLayout } from '../components/layout/AppLayout';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { ResourceStatusBadge } from '../components/resources/ResourceStatusBadge';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';

export function ResourceDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: resource, isLoading, error } = useResource(id);
  const deleteMutation = useDeleteResource();

  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  if (isLoading) {
    return (
      <AppLayout title="Resource Details">
        <Skeleton className="h-8 w-48 mb-6" />
        <Skeleton className="h-44 w-full mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </AppLayout>
    );
  }

  if (error || !resource) {
    return (
      <AppLayout title="Resource Details">
        <Card className="text-center py-12">
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
            Resource Not Found
          </h3>
          <p className="text-xs text-slate-500 mt-1 mb-4">
            The requested study resource could not be found or you do not have permission.
          </p>
          <Button variant="primary" size="sm" icon={ArrowLeft} onClick={() => navigate('/resources')}>
            Back to Resources
          </Button>
        </Card>
      </AppLayout>
    );
  }

  const isPdf = resource.source_type === 'pdf';
  const metadata = (resource.metadata && typeof resource.metadata === 'object') ? resource.metadata : {};

  // Extract real page count, chunk count, and file size
  const pageCount =
    resource.page_count ||
    metadata.page_count ||
    metadata.pages ||
    metadata.segments ||
    metadata.pages_or_segments ||
    0;

  const chunkCount =
    resource.chunk_count ||
    metadata.chunk_count ||
    metadata.chunks ||
    metadata.chunks_created ||
    0;

  const rawFileSize = resource.file_size || metadata.file_size || 0;

  const formatFileSize = (bytes) => {
    if (!bytes) return null;
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formattedFileSize = formatFileSize(rawFileSize);

  // Clean user-safe display source (No internal C:\ server filesystem paths!)
  const displaySource =
    resource.display_source ||
    metadata.original_filename ||
    resource.title ||
    (resource.source ? resource.source.split(/[/\\]/).pop() : 'Document');

  const handleDeleteConfirm = async () => {
    try {
      await deleteMutation.mutateAsync(resource.resource_id);
      navigate('/resources');
    } catch {
      // Toast handles error
    }
  };

  return (
    <AppLayout title="Resource Details">
      {/* Back Link */}
      <button
        onClick={() => navigate('/resources')}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 mb-4 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Resources</span>
      </button>

      {/* Main Metadata Overview Banner */}
      <Card className="mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 bg-blue-600/10 text-blue-400 border border-blue-500/20">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-xl font-bold text-[#f5f7fa]">
                  {resource.title || displaySource}
                </h2>
                <ResourceStatusBadge status={resource.status} />
              </div>
              <p className="text-xs text-[#9ca8ba] mt-1 break-all flex items-center gap-1">
                <span className="font-medium text-[#f5f7fa]">
                  {displaySource}
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="primary"
              size="md"
              icon={MessageSquare}
              onClick={() => navigate(`/workspace?resource_id=${resource.resource_id}`)}
            >
              Open Study Workspace
            </Button>
            <Button
              variant="destructive"
              size="md"
              icon={Trash2}
              onClick={() => setConfirmDeleteOpen(true)}
            >
              Delete Resource
            </Button>
          </div>
        </div>

        {/* Real Ingestion Metadata Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-5 border-t border-white/[0.07] text-xs">
          <div className="bg-[#07090d]/60 p-3.5 rounded-xl border border-white/[0.05]">
            <span className="text-[#9ca8ba] block text-[11px] font-semibold uppercase tracking-wider">
              Source Format
            </span>
            <span className="font-bold text-[#f5f7fa] mt-0.5 block">
              PDF Document
            </span>
          </div>

          <div className="bg-[#07090d]/60 p-3.5 rounded-xl border border-white/[0.05]">
            <span className="text-[#9ca8ba] block text-[11px] font-semibold uppercase tracking-wider">
              Total Pages
            </span>
            <span className="font-extrabold text-blue-400 mt-0.5 block text-base">
              {pageCount}
            </span>
          </div>

          <div className="bg-[#07090d]/60 p-3.5 rounded-xl border border-white/[0.05]">
            <span className="text-[#9ca8ba] block text-[11px] font-semibold uppercase tracking-wider">
              Vector Chunks
            </span>
            <span className="font-extrabold text-blue-400 mt-0.5 block text-base">
              {chunkCount}
            </span>
          </div>

          <div className="bg-[#07090d]/60 p-3.5 rounded-xl border border-white/[0.05]">
            <span className="text-[#9ca8ba] block text-[11px] font-semibold uppercase tracking-wider">
              {formattedFileSize ? 'File Size' : 'Ingested Date'}
            </span>
            <span className="font-bold text-[#f5f7fa] mt-0.5 block">
              {formattedFileSize || new Date(resource.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </Card>

      {/* Detailed Technical Resource Breakdown */}
      <Card className="p-6">
        <h4 className="text-sm font-bold text-[#f5f7fa] mb-4 pb-3 border-b border-white/[0.07]">
          Resource Technical Breakdown
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="space-y-3">
            <div className="flex justify-between py-1 border-b border-white/[0.05]">
              <span className="text-slate-500">Resource File Name:</span>
              <span className="font-semibold text-[#f5f7fa]">{displaySource}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/[0.05]">
              <span className="text-slate-500">Resource Type:</span>
              <span className="font-semibold text-[#f5f7fa] uppercase">{resource.source_type}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/[0.05]">
              <span className="text-slate-500">Ingestion Status:</span>
              <span className="font-semibold text-emerald-400 uppercase">{resource.status}</span>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between py-1 border-b border-white/[0.05]">
              <span className="text-slate-500">Unique Resource ID:</span>
              <span className="font-mono text-[11px] font-semibold text-[#f5f7fa]">{resource.resource_id}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/[0.05]">
              <span className="text-slate-500">Ingestion Timestamp:</span>
              <span className="font-semibold text-[#f5f7fa]">
                {new Date(resource.created_at).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/[0.05]">
              <span className="text-slate-500">Vector Store Status:</span>
              <span className="font-semibold text-emerald-400">Indexed ({chunkCount} chunks)</span>
            </div>
          </div>
        </div>
      </Card>

      <ConfirmDialog
        isOpen={confirmDeleteOpen}
        onClose={() => setConfirmDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Resource"
        message={`Are you sure you want to delete "${displaySource}"? This will purge vector store embeddings and DB records.`}
        isLoading={deleteMutation.isPending}
      />
    </AppLayout>
  );
}
