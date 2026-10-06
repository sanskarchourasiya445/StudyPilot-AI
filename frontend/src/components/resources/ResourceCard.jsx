import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Video, Trash2, ArrowRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/Card';
import { ResourceStatusBadge } from './ResourceStatusBadge';

export function ResourceCard({ resource, onDelete }) {
  const navigate = useNavigate();
  const isPdf = resource.source_type === 'pdf';

  let metadata = {};
  if (resource.metadata_json) {
    try {
      metadata = typeof resource.metadata_json === 'string' ? JSON.parse(resource.metadata_json) : resource.metadata_json;
    } catch {
      metadata = {};
    }
  } else if (resource.metadata) {
    metadata = resource.metadata;
  }

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

  const displaySource =
    resource.display_source ||
    metadata.original_filename ||
    resource.title ||
    (resource.source ? resource.source.split(/[/\\]/).pop() : 'Document');

  return (
    <Card hoverable onClick={() => navigate(`/resources/${resource.resource_id}`)}>
      <CardHeader>
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 bg-blue-600/10 text-blue-400 border border-blue-500/20">
            <FileText className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1">
            <CardTitle className="truncate text-sm font-bold text-[#f5f7fa]">{resource.title || displaySource}</CardTitle>
            <CardDescription className="truncate text-xs text-[#9ca8ba]">{displaySource}</CardDescription>
          </div>
        </div>
        <ResourceStatusBadge status={resource.status} />
      </CardHeader>

      <CardContent>
        <div className="flex items-center gap-3 text-xs bg-[#07090d]/60 p-2.5 rounded-xl border border-white/[0.05] text-[#9ca8ba]">
          <div>
            <span className="font-semibold text-[#f5f7fa]">{pageCount}</span> pages
          </div>
          <span className="text-white/20">•</span>
          <div>
            <span className="font-semibold text-[#f5f7fa]">{chunkCount}</span> chunks
          </div>
          <span className="text-white/20">•</span>
          <span className="truncate">
            {new Date(resource.created_at).toLocaleDateString()}
          </span>
        </div>
      </CardContent>

      <CardFooter>
        {/* Quick Study Actions */}
        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => navigate(`/workspace?resource_id=${resource.resource_id}&tab=chat`)}
            className="px-2.5 py-1 rounded-lg bg-[#101827] border border-white/[0.08] hover:border-blue-500/40 text-xs font-semibold text-[#f5f7fa] hover:text-blue-400 transition-colors"
          >
            Chat
          </button>
          <button
            onClick={() => navigate(`/workspace?resource_id=${resource.resource_id}&tab=summary`)}
            className="px-2.5 py-1 rounded-lg bg-[#101827] border border-white/[0.08] hover:border-blue-500/40 text-xs font-semibold text-[#f5f7fa] hover:text-teal-400 transition-colors"
          >
            Summary
          </button>
          <button
            onClick={() => navigate(`/workspace?resource_id=${resource.resource_id}&tab=notes`)}
            className="px-2.5 py-1 rounded-lg bg-[#101827] border border-white/[0.08] hover:border-blue-500/40 text-xs font-semibold text-[#f5f7fa] hover:text-purple-400 transition-colors"
          >
            Notes
          </button>
          <button
            onClick={() => navigate(`/workspace?resource_id=${resource.resource_id}&tab=quiz`)}
            className="px-2.5 py-1 rounded-lg bg-[#101827] border border-white/[0.08] hover:border-blue-500/40 text-xs font-semibold text-[#f5f7fa] hover:text-amber-400 transition-colors"
          >
            Quiz
          </button>
        </div>

        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
          {onDelete && (
            <button
              onClick={() => onDelete(resource)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-white/[0.05] transition-colors"
              title="Delete Resource"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => navigate(`/resources/${resource.resource_id}`)}
            className="p-1.5 rounded-lg text-blue-400 hover:bg-blue-600/10 transition-colors flex items-center gap-1 text-xs font-semibold"
          >
            <span>Open</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </CardFooter>
    </Card>
  );
}
