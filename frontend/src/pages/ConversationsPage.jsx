import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, Search, Trash2, ArrowRight, Clock, Layers, Plus } from 'lucide-react';
import { useConversations, useDeleteConversation } from '../hooks/useConversations';
import { useResources } from '../hooks/useResources';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Skeleton } from '../components/ui/Skeleton';
import { ConfirmDialog } from '../components/ui/ConfirmDialog';

export function ConversationsPage() {
  const navigate = useNavigate();
  const { data: conversations = [], isLoading: isLoadingConversations } = useConversations();
  const { data: resources = [] } = useResources();
  const deleteMutation = useDeleteConversation();

  const [searchQuery, setSearchQuery] = useState('');
  const [deletingConversation, setDeletingConversation] = useState(null);

  const filteredConversations = conversations.filter((c) =>
    (c.title || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDeleteConfirm = async () => {
    if (!deletingConversation) return;
    const targetId = deletingConversation.id || deletingConversation.conversation_id;
    try {
      await deleteMutation.mutateAsync(targetId);
      setDeletingConversation(null);
    } catch {
      // Toast handles error
    }
  };

  return (
    <AppLayout title="Saved Conversations">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-[#f5f7fa]">Study Chat Threads</h2>
          <p className="text-xs text-[#9ca8ba] mt-0.5">
            View, search, and continue saved RAG AI study assistant conversations.
          </p>
        </div>
        <Button variant="primary" size="sm" icon={Plus} onClick={() => navigate('/workspace')}>
          New Chat Thread
        </Button>
      </div>

      {/* Filter / Search Bar */}
      <Card className="mb-6">
        <Input
          type="text"
          placeholder="Filter conversation threads by title..."
          icon={Search}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </Card>

      {/* Conversations Grid / Loading / Empty */}
      {isLoadingConversations ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
        </div>
      ) : filteredConversations.length === 0 ? (
        <Card className="text-center py-12">
          <div className="w-12 h-12 rounded-2xl bg-white/[0.05] text-blue-400 border border-white/[0.08] mx-auto flex items-center justify-center mb-3">
            <MessageSquare className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-bold text-[#f5f7fa]">
            {conversations.length === 0 ? 'No saved conversations' : 'No matching conversations'}
          </h4>
          <p className="text-xs text-[#9ca8ba] mt-1 mb-4">
            {conversations.length === 0
              ? 'Start a new chat session in the Study Workspace to save conversations.'
              : 'Try clearing your filter search to see all saved threads.'}
          </p>
          {conversations.length === 0 && (
            <Button variant="primary" size="sm" icon={Plus} onClick={() => navigate('/workspace')}>
              Start First Chat
            </Button>
          )}
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredConversations.map((c, idx) => {
            const convId = c.id || c.conversation_id;
            const associatedResource = resources.find((r) => (r.resource_id || r.id) === c.resource_id);

            return (
              <Card
                key={convId || `conv-${idx}`}
                hoverable
                onClick={() => navigate(`/workspace?conversation_id=${convId}`)}
              >
                <CardHeader>
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-9 h-9 rounded-xl bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center shrink-0">
                      <MessageSquare className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <CardTitle className="truncate text-sm font-bold text-[#f5f7fa]">{c.title || 'Untitled Thread'}</CardTitle>
                      <CardDescription className="truncate text-xs text-[#9ca8ba]">
                        {associatedResource ? associatedResource.title || associatedResource.source : 'Global Context'}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>

                <CardFooter onClick={(e) => e.stopPropagation()}>
                  <span className="text-[11px] text-[#9ca8ba]">
                    {new Date(c.updated_at || c.created_at).toLocaleDateString()}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setDeletingConversation(c)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-white/[0.05] transition-colors"
                      title="Delete Thread"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => navigate(`/workspace?conversation_id=${convId}`)}
                      className="p-1.5 rounded-lg text-blue-400 hover:bg-blue-600/10 transition-colors flex items-center gap-1 text-xs font-semibold"
                    >
                      <span>Continue</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}

      <ConfirmDialog
        isOpen={!!deletingConversation}
        onClose={() => setDeletingConversation(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Conversation"
        message={`Are you sure you want to delete "${deletingConversation?.title}"?`}
        isLoading={deleteMutation.isPending}
      />
    </AppLayout>
  );
}
