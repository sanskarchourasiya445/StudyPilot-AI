import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  MessageSquare,
  BookOpen,
  HelpCircle,
  Plus,
  ArrowRight,
  Sparkles,
  Clock,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useResources } from '../hooks/useResources';
import { useConversations } from '../hooks/useConversations';
import { AppLayout } from '../components/layout/AppLayout';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';
import { ResourceUploadModal } from '../components/resources/ResourceUploadModal';

function formatRelativeTime(dateString) {
  if (!dateString) return 'Recently';
  const date = new Date(dateString);
  const now = new Date();
  const diffMinutes = Math.floor((now - date) / (1000 * 60));

  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data: rawResources = [], isLoading: isLoadingResources } = useResources();
  const resources = Array.isArray(rawResources) ? rawResources : [];

  const { data: rawConversations = [], isLoading: isLoadingConversations } = useConversations();
  const conversations = Array.isArray(rawConversations) ? rawConversations : [];

  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  const readyCount = resources.filter((r) => r.status === 'ready').length;

  const getCleanTitle = (res) => {
    if (!res) return 'Study Material';
    let clean = res.title || res.display_source;
    if (!clean || clean.startsWith('http://') || clean.startsWith('https://')) {
      if (res.source) clean = res.source.split(/[/\\]/).pop();
      else clean = 'Study Material';
    }
    return clean;
  };

  const sortedConversations = [...conversations].sort((a, b) => {
    const tA = new Date(a.updated_at || a.created_at || 0).getTime();
    const tB = new Date(b.updated_at || b.created_at || 0).getTime();
    return tB - tA;
  });

  const firstName = user?.name ? user.name.split(' ')[0] : 'Student';

  return (
    <AppLayout title="Dashboard">
      <div className="space-y-6 max-w-7xl mx-auto pb-8">
        {/* 1. Welcome Banner */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white p-6 sm:p-8 shadow-sm">
          <div className="relative z-10 max-w-2xl">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/20 text-white backdrop-blur-md mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              AI Learning Workspace
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Welcome back, {firstName} 👋
            </h1>
            <p className="mt-2 text-sm sm:text-base text-blue-100/90 font-medium">
              Upload your study material and use AI to understand, summarize, take notes, and practice.
            </p>
          </div>
          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-radial from-white/10 to-transparent pointer-events-none" />
        </div>

        {/* 2. Key Metrics Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                Study Materials
              </p>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                {isLoadingResources ? <Skeleton className="h-8 w-12" /> : resources.length}
              </h3>
            </div>
            <div className="w-11 h-11 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
          </Card>

          <Card className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                Ready for AI Study
              </p>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                {isLoadingResources ? <Skeleton className="h-8 w-12" /> : readyCount}
              </h3>
            </div>
            <div className="w-11 h-11 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </Card>

          <Card className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                Active Chat Threads
              </p>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
                {isLoadingConversations ? <Skeleton className="h-8 w-12" /> : conversations.length}
              </h3>
            </div>
            <div className="w-11 h-11 rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center">
              <MessageSquare className="w-5 h-5" />
            </div>
          </Card>
        </div>

        {/* 3. Quick Actions */}
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <button
              onClick={() => setUploadModalOpen(true)}
              className="text-left p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-md transition-all group flex flex-col justify-between"
            >
              <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Plus className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                  Add Resource
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Upload PDF course materials
                </p>
              </div>
            </button>

            <button
              onClick={() => navigate('/workspace?tab=chat')}
              className="text-left p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 hover:border-indigo-400 dark:hover:border-indigo-500 hover:shadow-md transition-all group flex flex-col justify-between"
            >
              <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                  Start AI Study
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Ask grounded questions with citations
                </p>
              </div>
            </button>

            <button
              onClick={() => navigate('/workspace?tab=notes')}
              className="text-left p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 hover:border-purple-400 dark:hover:border-purple-500 hover:shadow-md transition-all group flex flex-col justify-between"
            >
              <div className="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                  Generate Notes
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Structured bullet & Cornell study notes
                </p>
              </div>
            </button>

            <button
              onClick={() => navigate('/workspace?tab=quiz')}
              className="text-left p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 hover:border-amber-400 dark:hover:border-amber-500 hover:shadow-md transition-all group flex flex-col justify-between"
            >
              <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <HelpCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                  Generate Quiz
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Practice interactive multiple-choice tests
                </p>
              </div>
            </button>
          </div>
        </div>

        {/* 4. Two Columns: Recent Resources & Recent Conversations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Resources */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Recent Resources
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Your uploaded study materials
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                icon={ArrowRight}
                onClick={() => navigate('/resources')}
              >
                View All
              </Button>
            </div>

            {isLoadingResources ? (
              <div className="space-y-3">
                <Skeleton className="h-16 w-full rounded-xl" />
                <Skeleton className="h-16 w-full rounded-xl" />
                <Skeleton className="h-16 w-full rounded-xl" />
              </div>
            ) : resources.length === 0 ? (
              <div className="text-center py-8 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
                <FileText className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  No resources uploaded yet
                </p>
                <p className="text-xs text-slate-500 mt-1 mb-4">
                  Upload a PDF to start studying with AI.
                </p>
                <Button
                  variant="primary"
                  size="sm"
                  icon={Plus}
                  onClick={() => setUploadModalOpen(true)}
                >
                  Upload Material
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {resources.slice(0, 4).map((res) => {
                  const title = getCleanTitle(res);
                  const rid = res.resource_id || res.id;
                  return (
                    <div
                      key={rid}
                      className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-700/60 bg-slate-50/50 dark:bg-slate-900/40 hover:bg-slate-100/70 dark:hover:bg-slate-700/40 transition-colors flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-lg bg-blue-100 dark:bg-blue-950/80 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                          <FileText className="w-4.5 h-4.5" />
                        </div>
                        <div className="min-w-0">
                          <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">
                            {title}
                          </h4>
                          <div className="flex items-center gap-2 mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                            <span className="inline-flex items-center gap-1 font-medium text-emerald-600 dark:text-emerald-400">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                              Ready
                            </span>
                            <span>•</span>
                            <span>{formatRelativeTime(res.created_at)}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        <button
                          onClick={() => navigate(`/workspace?resource_id=${rid}&tab=chat`)}
                          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors"
                          title="Chat with this resource"
                        >
                          Chat
                        </button>
                        <button
                          onClick={() => navigate(`/workspace?resource_id=${rid}&tab=notes`)}
                          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400 hover:bg-purple-100 dark:hover:bg-purple-900 transition-colors hidden sm:inline-block"
                          title="View notes"
                        >
                          Notes
                        </button>
                        <button
                          onClick={() => navigate(`/workspace?resource_id=${rid}&tab=quiz`)}
                          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900 transition-colors hidden sm:inline-block"
                          title="Practice quiz"
                        >
                          Quiz
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Recent Conversations */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Recent Conversations
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Your AI study sessions with source citations
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                icon={ArrowRight}
                onClick={() => navigate('/conversations')}
              >
                View All
              </Button>
            </div>

            {isLoadingConversations ? (
              <div className="space-y-3">
                <Skeleton className="h-16 w-full rounded-xl" />
                <Skeleton className="h-16 w-full rounded-xl" />
                <Skeleton className="h-16 w-full rounded-xl" />
              </div>
            ) : sortedConversations.length === 0 ? (
              <div className="text-center py-8 border border-dashed border-slate-200 dark:border-slate-700 rounded-xl">
                <MessageSquare className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  No study conversations yet
                </p>
                <p className="text-xs text-slate-500 mt-1 mb-4">
                  Ask a question about your study materials to start learning.
                </p>
                <Button
                  variant="primary"
                  size="sm"
                  icon={MessageSquare}
                  onClick={() => navigate('/workspace?tab=chat')}
                >
                  Start First Chat
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {sortedConversations.slice(0, 4).map((conv) => {
                  const cid = conv.id || conv.conversation_id;
                  const messageCount = conv.message_count || conv.messages?.length || 0;
                  return (
                    <div
                      key={cid}
                      onClick={() => navigate(`/workspace?conversation_id=${cid}&tab=chat`)}
                      className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-700/60 bg-slate-50/50 dark:bg-slate-900/40 hover:bg-blue-50/50 dark:hover:bg-slate-700/40 hover:border-blue-200 dark:hover:border-blue-800 transition-all cursor-pointer flex items-center justify-between gap-3 group"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-9 h-9 rounded-lg bg-indigo-100 dark:bg-indigo-950/80 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                          <MessageSquare className="w-4.5 h-4.5" />
                        </div>
                        <div className="min-w-0">
                          <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                            {conv.title || 'Untitled Conversation'}
                          </h4>
                          <div className="flex items-center gap-2 mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                            {messageCount > 0 && (
                              <>
                                <span>{messageCount} messages</span>
                                <span>•</span>
                              </>
                            )}
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3 inline" />
                              {formatRelativeTime(conv.updated_at || conv.created_at)}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors shrink-0">
                        <ArrowRight className="w-4 h-4" />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      </div>

      <ResourceUploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
      />
    </AppLayout>
  );
}
