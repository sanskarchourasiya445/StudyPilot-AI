import React, { useState, useMemo } from 'react';
import { Plus, Search, Filter, LayoutGrid, List as ListIcon, FileText } from 'lucide-react';
import { useResources, useDeleteResource } from '../hooks/useResources';
import { AppLayout } from '../components/layout/AppLayout';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Skeleton } from '../components/ui/Skeleton';
import { ResourceCard } from '../components/resources/ResourceCard';
import { ResourceTable } from '../components/resources/ResourceTable';
import { ResourceUploadModal } from '../components/resources/ResourceUploadModal';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';

export function ResourcesPage() {
  const { data: resources = [], isLoading } = useResources();
  const deleteMutation = useDeleteResource();

  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all'); // 'all' | 'pdf' | 'youtube'
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'ready' | 'processing' | 'failed'
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'table'

  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [deletingResource, setDeletingResource] = useState(null);

  const filteredResources = useMemo(() => {
    return resources.filter((resource) => {
      const matchesSearch =
        !searchQuery ||
        (resource.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (resource.source || '').toLowerCase().includes(searchQuery.toLowerCase());

      const matchesType = typeFilter === 'all' || resource.source_type === typeFilter;
      const matchesStatus = statusFilter === 'all' || (resource.status || '').toLowerCase() === statusFilter;

      return matchesSearch && matchesType && matchesStatus;
    });
  }, [resources, searchQuery, typeFilter, statusFilter]);

  const handleDeleteConfirm = async () => {
    if (!deletingResource) return;
    try {
      await deleteMutation.mutateAsync(deletingResource.resource_id);
      setDeletingResource(null);
    } catch {
      // Toast handles error
    }
  };

  return (
    <AppLayout title="Study Resources">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-[#f5f7fa]">Study Materials</h2>
          <p className="text-xs text-[#9ca8ba] mt-0.5">
            Manage textbooks, notes, and study materials for AI processing and RAG chat.
          </p>
        </div>
        <Button variant="primary" size="sm" icon={Plus} onClick={() => setUploadModalOpen(true)}>
          Add Resource
        </Button>
      </div>

      {/* Filter Controls Bar */}
      <Card className="mb-6">
        <div className="flex flex-col md:flex-row items-center gap-3">
          {/* Text Search */}
          <div className="w-full md:flex-1">
            <Input
              type="text"
              placeholder="Search resources by title or filename..."
              icon={Search}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Filter Pills and Dropdowns */}
          <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto no-scrollbar">
            <div className="flex items-center gap-1 bg-[#0a0f18] p-1 rounded-xl border border-white/[0.08] shrink-0">
              <button
                onClick={() => setTypeFilter('all')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                  typeFilter === 'all'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-[#9ca8ba] hover:text-[#f5f7fa]'
                }`}
              >
                All ({resources.length})
              </button>
              <button
                onClick={() => setTypeFilter('pdf')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                  typeFilter === 'pdf'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-[#9ca8ba] hover:text-[#f5f7fa]'
                }`}
              >
                PDF ({resources.filter(r => r.source_type === 'pdf').length})
              </button>
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-[#0a0f18] border border-white/[0.08] text-[#f5f7fa] text-xs rounded-xl px-3 py-1.5 focus:outline-none focus:border-blue-500 shrink-0"
            >
              <option value="all">All Statuses</option>
              <option value="ready">Ready</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>

            {/* View Mode Switcher */}
            <div className="flex border border-white/[0.08] bg-[#0a0f18] rounded-xl overflow-hidden shrink-0 ml-auto md:ml-0">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 ${
                  viewMode === 'grid'
                    ? 'bg-blue-600 text-white font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Grid View"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`p-1.5 ${
                  viewMode === 'table'
                    ? 'bg-blue-600 text-white font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
                title="Table View"
              >
                <ListIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* Content Rendering: Loading / Empty / Data */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-44" />
          <Skeleton className="h-44" />
          <Skeleton className="h-44" />
          <Skeleton className="h-44" />
        </div>
      ) : filteredResources.length === 0 ? (
        <Card className="text-center py-12">
          <div className="w-12 h-12 rounded-2xl bg-white/[0.05] text-blue-400 border border-white/[0.08] mx-auto flex items-center justify-center mb-3">
            <FileText className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-bold text-[#f5f7fa]">
            {resources.length === 0 ? 'No study resources yet' : 'No matching resources found'}
          </h4>
          <p className="text-xs text-[#9ca8ba] mt-1 mb-4 max-w-sm mx-auto">
            {resources.length === 0
              ? 'Upload a PDF textbook or study material to start studying with AI.'
              : 'Try clearing your search query or filter selection to view all materials.'}
          </p>
          {resources.length === 0 && (
            <Button variant="primary" size="sm" icon={Plus} onClick={() => setUploadModalOpen(true)}>
              Upload First Material
            </Button>
          )}
        </Card>
      ) : viewMode === 'table' ? (
        <ResourceTable
          resources={filteredResources}
          onDelete={(r) => setDeletingResource(r)}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredResources.map((resource) => (
            <ResourceCard
              key={resource.id}
              resource={resource}
              onDelete={(r) => setDeletingResource(r)}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      <ResourceUploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
      />

      <ConfirmDialog
        isOpen={!!deletingResource}
        onClose={() => setDeletingResource(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Resource"
        message={`Are you sure you want to delete "${deletingResource?.title || deletingResource?.source}"? This will purge vector store chunks.`}
        isLoading={deleteMutation.isPending}
      />
    </AppLayout>
  );
}
