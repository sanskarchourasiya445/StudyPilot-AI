import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  Search,
  Trash2,
  ArrowRight,
  Clock,
  FileText,
  Video,
  Sparkles,
  Plus,
  RefreshCw,
  X,
  Layers,
} from 'lucide-react';
import { useConversations, useDeleteConversation } from '../hooks/useConversations';
import { useResources } from '../hooks/useResources';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';

function formatRelativeTime(dateInput) {
  if (!dateInput) return '';
  const date = new Date(dateInput);
  if (isNaN(date.getTime())) return '';

  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return 'Just now';
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours}h ago`;
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays === 1) return 'Yesterday';
  if (diffInDays < 7) return `${diffInDays}d ago`;

  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

function getTimeGroup(dateInput) {
  if (!dateInput) return 'Earlier';
  const date = new Date(dateInput);
  if (isNaN(date.getTime())) return 'Earlier';

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const compareDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

  if (compareDate.getTime() === today.getTime()) {
    return 'Today';
  } else if (compareDate.getTime() === yesterday.getTime()) {
    return 'Yesterday';
  } else {
    return 'Earlier';
  }
}

export function HistoryPage() {
  const navigate = useNavigate();
  const {
    data: conversations = [],
    isLoading: isLoadingConversations,
    isError,
    error,
    refetch,
    isFetching,
  } = useConversations();
  const { data: resources = [] } = useResources();
  const deleteMutation = useDeleteConversation();

  const [searchQuery, setSearchQuery] = useState('');
  const [deletingConversation, setDeletingConversation] = useState(null);

  // Quick lookup map for resources
  const resourceMap = useMemo(() => {
    const map = new Map();
    for (const r of resources) {
      const id = r.resource_id || r.id;
      if (id) map.set(id, r);
    }
    return map;
  }, [resources]);

  // Filter and sort conversations (newest first)
  const filteredAndSorted = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    const sorted = [...conversations].sort((a, b) => {
      const timeA = new Date(a.updated_at || a.created_at || 0).getTime();
      const timeB = new Date(b.updated_at || b.created_at || 0).getTime();
      return timeB - timeA;
    });

    if (!query) return sorted;

    return sorted.filter((c) => {
      const titleMatch = (c.title || '').toLowerCase().includes(query);
      if (titleMatch) return true;

      // Check resource names
      if (c.resource_id && resourceMap.has(c.resource_id)) {
        const res = resourceMap.get(c.resource_id);
        const name = (res.title || res.source || '').toLowerCase();
        if (name.includes(query)) return true;
      }

      if (c.resource_ids && Array.isArray(c.resource_ids)) {
        const matchesResource = c.resource_ids.some((id) => {
          const res = resourceMap.get(id);
          return res && (res.title || res.source || '').toLowerCase().includes(query);
        });
        if (matchesResource) return true;
      }

      return false;
    });
  }, [conversations, searchQuery, resourceMap]);

  // Group by Today, Yesterday, Earlier
  const groupedConversations = useMemo(() => {
    const groups = {
      Today: [],
      Yesterday: [],
      Earlier: [],
    };

    for (const conv of filteredAndSorted) {
      const groupKey = getTimeGroup(conv.updated_at || conv.created_at);
      if (groups[groupKey]) {
        groups[groupKey].push(conv);
      } else {
        groups.Earlier.push(conv);
      }
    }

    return groups;
  }, [filteredAndSorted]);

  const handleDeleteConfirm = async () => {
    if (!deletingConversation) return;
    const targetId = deletingConversation.id || deletingConversation.conversation_id;
    try {
      await deleteMutation.mutateAsync(targetId);
      setDeletingConversation(null);
    } catch {
      // Toast handles error in hook
    }
  };

  const handleOpenConversation = (conv) => {
    const convId = conv.id || conv.conversation_id;
    navigate(`/workspace?conversation_id=${convId}&tab=chat`);
  };

  const getResourceContext = (conv) => {
    if (conv.scope_mode === 'all' || (!conv.resource_id && (!conv.resource_ids || conv.resource_ids.length === 0))) {
      return {
        label: 'All Materials',
        icon: Layers,
        type: 'all',
      };
    }

    const ids = conv.resource_ids && conv.resource_ids.length > 0
      ? conv.resource_ids
      : conv.resource_id
      ? [conv.resource_id]
      : [];

    if (ids.length === 1) {
      const res = resourceMap.get(ids[0]);
      if (res) {
        const isPdf = res.source_type === 'pdf';
        return {
          label: res.title || res.source?.split(/[\/\\]/).pop() || 'Document',
          icon: isPdf ? FileText : Video,
          type: res.source_type || 'document',
        };
      }
      return {
        label: '1 Material',
        icon: FileText,
        type: 'document',
      };
    }

    if (ids.length > 1) {
      return {
        label: `${ids.length} Materials`,
        icon: Layers,
        type: 'multi',
      };
    }

    return {
      label: 'All Materials',
      icon: Layers,
      type: 'all',
    };
  };

  return (
    <AppLayout
      title="Study History"
      subtitle="Browse and continue your persisted AI study sessions and chat threads"
      rightSlot={
        <Button
          variant="primary"
          size="sm"
          icon={Plus}
          onClick={() => navigate('/workspace')}
        >
          New Session
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Search Bar */}
        <div className="flex items-center justify-between gap-3">
          <div className="relative flex-1 max-w-xl">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search conversations by topic, title, or resource..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#0a0f18] border border-white/[0.08] text-xs text-[#f5f7fa] placeholder-[#667085] pl-9.5 pr-8 py-2.5 rounded-xl focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/30 transition-all"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-[#f5f7fa] rounded-md transition-colors"
                title="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <button
            type="button"
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2.5 rounded-xl border border-white/[0.08] bg-[#0a0f18] text-slate-400 hover:text-[#f5f7fa] hover:bg-white/[0.04] transition-colors shrink-0 disabled:opacity-50"
            title="Refresh history"
            aria-label="Refresh history"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin text-blue-500' : ''}`} />
          </button>
        </div>

        {/* Loading State */}
        {isLoadingConversations && (
          <div className="space-y-4">
            <div className="h-4 w-24 bg-white/[0.05] rounded-md animate-pulse mb-3" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              <Skeleton className="h-28 rounded-2xl" />
              <Skeleton className="h-28 rounded-2xl" />
              <Skeleton className="h-28 rounded-2xl" />
              <Skeleton className="h-28 rounded-2xl" />
            </div>
          </div>
        )}

        {/* Error State */}
        {!isLoadingConversations && isError && (
          <Card className="text-center py-12 border-red-500/20 bg-red-950/10">
            <div className="w-12 h-12 rounded-2xl bg-red-500/10 text-red-400 border border-red-500/20 mx-auto flex items-center justify-center mb-3">
              <X className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-bold text-[#f5f7fa]">Failed to Load Conversation History</h4>
            <p className="text-xs text-[#9ca8ba] mt-1 mb-4 max-w-md mx-auto">
              {error?.message || 'A network error occurred while retrieving your persisted study sessions.'}
            </p>
            <Button variant="primary" size="sm" icon={RefreshCw} onClick={() => refetch()}>
              Try Again
            </Button>
          </Card>
        )}

        {/* Empty State: Zero Conversations Ever */}
        {!isLoadingConversations && !isError && conversations.length === 0 && (
          <Card className="text-center py-16 border-dashed border-white/[0.1]">
            <div className="w-14 h-14 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 mx-auto flex items-center justify-center mb-4">
              <Clock className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-[#f5f7fa]">No conversations yet</h3>
            <p className="text-xs text-[#9ca8ba] mt-1.5 mb-5 max-w-sm mx-auto leading-relaxed">
              Start a study session from your Workspace and your conversations will appear here.
            </p>
            <Button
              variant="primary"
              size="md"
              icon={Sparkles}
              onClick={() => navigate('/workspace')}
            >
              Start studying
            </Button>
          </Card>
        )}

        {/* Empty State: Filter Search Returned 0 Matches */}
        {!isLoadingConversations && !isError && conversations.length > 0 && filteredAndSorted.length === 0 && (
          <Card className="text-center py-12">
            <div className="w-12 h-12 rounded-2xl bg-white/[0.04] text-slate-400 border border-white/[0.07] mx-auto flex items-center justify-center mb-3">
              <Search className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-bold text-[#f5f7fa]">No matching conversations</h4>
            <p className="text-xs text-[#9ca8ba] mt-1 mb-4 max-w-md mx-auto">
              No conversations matched &quot;{searchQuery}&quot;. Try adjusting your search query or clear the filter.
            </p>
            <Button variant="secondary" size="sm" icon={X} onClick={() => setSearchQuery('')}>
              Clear Search
            </Button>
          </Card>
        )}

        {/* Grouped Conversation List */}
        {!isLoadingConversations && !isError && filteredAndSorted.length > 0 && (
          <div className="space-y-7">
            {['Today', 'Yesterday', 'Earlier'].map((groupTitle) => {
              const items = groupedConversations[groupTitle];
              if (!items || items.length === 0) return null;

              return (
                <div key={groupTitle} className="space-y-3">
                  {/* Group Section Header */}
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#9ca8ba]">
                      {groupTitle}
                    </span>
                    <div className="flex-1 h-px bg-white/[0.06]" />
                    <span className="text-[11px] font-medium text-[#667085]">
                      {items.length} {items.length === 1 ? 'session' : 'sessions'}
                    </span>
                  </div>

                  {/* Cards Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                    {items.map((conv) => {
                      const convId = conv.id || conv.conversation_id;
                      const resCtx = getResourceContext(conv);
                      const ResIcon = resCtx.icon;
                      const relativeTime = formatRelativeTime(conv.updated_at || conv.created_at);
                      const messageCount = conv.message_count || 0;

                      return (
                        <div
                          key={convId}
                          onClick={() => handleOpenConversation(conv)}
                          className="group relative flex flex-col justify-between p-4.5 rounded-2xl bg-[#0d1420] border border-white/[0.07] hover:border-blue-500/40 hover:bg-[#101827] cursor-pointer transition-all duration-150 shadow-xs hover:shadow-md"
                        >
                          <div>
                            {/* Card Top: Topic Title & Delete Button */}
                            <div className="flex items-start justify-between gap-3 mb-2.5">
                              <div className="flex items-center gap-2.5 min-w-0 flex-1">
                                <div className="w-8 h-8 rounded-xl bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center shrink-0 group-hover:bg-blue-600 group-hover:text-white transition-colors duration-150">
                                  <MessageSquare className="w-4 h-4" />
                                </div>
                                <h4 className="text-sm font-bold text-[#f5f7fa] group-hover:text-blue-400 transition-colors truncate">
                                  {conv.title || 'Untitled Session'}
                                </h4>
                              </div>

                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setDeletingConversation(conv);
                                }}
                                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors opacity-80 group-hover:opacity-100 shrink-0"
                                title="Delete Conversation"
                                aria-label="Delete Conversation"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>

                            {/* Card Middle: Resource Context Badge */}
                            <div className="flex items-center gap-2 mb-3">
                              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/[0.04] border border-white/[0.07] text-[11px] font-medium text-[#9ca8ba] truncate max-w-[280px]">
                                <ResIcon className="w-3 h-3 text-blue-400 shrink-0" />
                                <span className="truncate">{resCtx.label}</span>
                              </span>

                              <span className="text-[11px] text-[#667085]">·</span>

                              <span className="text-[11px] font-medium text-[#667085] whitespace-nowrap">
                                {messageCount} {messageCount === 1 ? 'message' : 'messages'}
                              </span>
                            </div>
                          </div>

                          {/* Card Footer: Timestamp & Action */}
                          <div className="pt-2.5 border-t border-white/[0.05] flex items-center justify-between text-xs">
                            <span className="text-[11px] text-[#667085]">
                              {relativeTime}
                            </span>

                            <div className="inline-flex items-center gap-1 text-xs font-semibold text-blue-400 group-hover:text-blue-300 group-hover:translate-x-0.5 transition-all">
                              <span>Continue</span>
                              <ArrowRight className="w-3.5 h-3.5" />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmDialog
        isOpen={!!deletingConversation}
        onClose={() => setDeletingConversation(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Study Conversation?"
        message={`Are you sure you want to permanently delete "${deletingConversation?.title || 'this conversation'}"? All persisted turns and cited sources will be removed.`}
        isLoading={deleteMutation.isPending}
      />
    </AppLayout>
  );
}
