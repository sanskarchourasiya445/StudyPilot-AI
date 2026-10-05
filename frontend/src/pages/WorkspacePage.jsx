import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useResources } from '../hooks/useResources';
import {
  useConversations,
  useConversationMessages,
  useDeleteConversation,
} from '../hooks/useConversations';
import { useSendMessage } from '../hooks/useChat';
import {
  useSummary,
  useGenerateSummary,
  useDeleteSummary,
  useNotes,
  useGenerateNotes,
  useDeleteNotes,
  useQuizzes,
  useGenerateQuiz,
  useDeleteQuizzes,
} from '../hooks/useStudy';
import { AppLayout } from '../components/layout/AppLayout';
import { StudyWorkspaceHeader } from '../components/workspace/StudyWorkspaceHeader';
import { ChatTab } from '../components/workspace/ChatTab';
import { SummaryTab } from '../components/workspace/SummaryTab';
import { NotesTab } from '../components/workspace/NotesTab';
import { QuizTab } from '../components/workspace/QuizTab';
import { useToast } from '../components/ui/Toast';

export function WorkspacePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { addToast } = useToast();

  // Extract query parameters
  const rawResourceId = searchParams.get('resource_id');
  const rawResourceIds = searchParams.get('resource_ids');
  const rawConversationId = searchParams.get('conversation_id');
  const rawTab = searchParams.get('tab') || 'chat';

  const queryResourceId =
    rawResourceId && rawResourceId !== 'undefined' && rawResourceId !== 'null'
      ? rawResourceId
      : null;
  const queryConversationId =
    rawConversationId && rawConversationId !== 'undefined' && rawConversationId !== 'null'
      ? rawConversationId
      : null;

  const validTabs = ['chat', 'summary', 'notes', 'quiz'];
  const activeTab = validTabs.includes(rawTab.toLowerCase()) ? rawTab.toLowerCase() : 'chat';

  // Scope State: { mode: 'all' | 'selected', resource_ids: string[] }
  const [scope, setScope] = useState(() => {
    if (rawResourceIds) {
      const ids = rawResourceIds.split(',').filter(Boolean);
      return { mode: 'selected', resource_ids: ids };
    }
    if (queryResourceId) {
      return { mode: 'selected', resource_ids: [queryResourceId] };
    }
    return { mode: 'all', resource_ids: [] };
  });

  const [activeConversationId, setActiveConversationId] = useState(queryConversationId);
  const [activeCitations, setActiveCitations] = useState([]);
  const [selectedCitationIdx, setSelectedCitationIdx] = useState(null);

  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [mobileCitationsOpen, setMobileCitationsOpen] = useState(false);

  // Local Chat message thread state
  const [localMessages, setLocalMessages] = useState([]);
  const [noteStyle, setNoteStyle] = useState('bullet');

  // Queries
  const { data: resources = [] } = useResources();
  const { data: conversations = [] } = useConversations();
  const { data: serverMessages = [], isLoading: isLoadingMessages } =
    useConversationMessages(activeConversationId);

  // Derive Single Resource for Summary/Notes/Quiz tools
  const singleResourceId =
    scope.mode === 'selected' && scope.resource_ids.length === 1
      ? scope.resource_ids[0]
      : null;

  const selectedResource = resources.find(
    (r) => (r.resource_id || r.id) === singleResourceId
  );

  // Study Tool Queries (only active when relevant and not known to be absent)
  const hasSummary = selectedResource ? selectedResource.has_summary : undefined;
  const hasNotes = selectedResource ? selectedResource.has_notes : undefined;
  const hasQuiz = selectedResource ? selectedResource.has_quiz : undefined;

  const shouldFetchSummary =
    !!singleResourceId &&
    hasSummary !== false &&
    (activeTab === 'summary' || hasSummary === true);

  const shouldFetchNotes =
    !!singleResourceId &&
    hasNotes !== false &&
    (activeTab === 'notes' || hasNotes === true);

  const shouldFetchQuizzes =
    !!singleResourceId &&
    hasQuiz !== false &&
    (activeTab === 'quiz' || hasQuiz === true);

  const { data: summary, isLoading: isLoadingSummary } = useSummary(singleResourceId, {
    enabled: shouldFetchSummary,
  });
  const { data: notes, isLoading: isLoadingNotes } = useNotes(singleResourceId, noteStyle, {
    enabled: shouldFetchNotes,
  });
  const { data: quizzes = [], isLoading: isLoadingQuizzes } = useQuizzes(singleResourceId, {
    enabled: shouldFetchQuizzes,
  });

  // Mutations
  const sendMessageMutation = useSendMessage();
  const deleteConversationMutation = useDeleteConversation();

  const generateSummaryMutation = useGenerateSummary();
  const deleteSummaryMutation = useDeleteSummary();

  const generateNotesMutation = useGenerateNotes();
  const deleteNotesMutation = useDeleteNotes();

  const generateQuizMutation = useGenerateQuiz();
  const deleteQuizzesMutation = useDeleteQuizzes();

  // Restore exact scope when switching or opening saved conversations
  useEffect(() => {
    if (activeConversationId && conversations && conversations.length > 0) {
      const conv = conversations.find(
        (c) => (c.id || c.conversation_id) === activeConversationId
      );
      if (conv) {
        if (conv.scope_mode === 'all') {
          setScope({ mode: 'all', resource_ids: [] });
        } else if (conv.resource_ids && conv.resource_ids.length > 0) {
          setScope({ mode: 'selected', resource_ids: conv.resource_ids });
        } else if (conv.resource_id) {
          setScope({ mode: 'selected', resource_ids: [conv.resource_id] });
        }
      }
    }
  }, [activeConversationId, conversations]);

  // Sync server messages into local thread when switching conversations
  useEffect(() => {
    if (activeConversationId && serverMessages && serverMessages.length > 0) {
      const formatted = serverMessages.map((m) => ({
        id: m.id,
        sender: m.role,
        content: m.content,
        sources: m.sources || [],
      }));
      setLocalMessages(formatted);

      const lastAssistantMsg = [...serverMessages]
        .reverse()
        .find((m) => m.role === 'assistant');
      if (lastAssistantMsg && lastAssistantMsg.sources) {
        setActiveCitations(lastAssistantMsg.sources);
      }
    } else if (!activeConversationId && localMessages.length > 0 && !sendMessageMutation.isPending) {
      setLocalMessages([]);
      setActiveCitations([]);
    }
  }, [serverMessages, activeConversationId]);

  // Handlers for Scope Change
  const handleChangeScope = (newScope) => {
    setScope(newScope);
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      if (newScope.mode === 'all') {
        p.delete('resource_id');
        p.delete('resource_ids');
      } else if (newScope.resource_ids.length === 1) {
        p.set('resource_id', newScope.resource_ids[0]);
        p.delete('resource_ids');
      } else if (newScope.resource_ids.length > 1) {
        p.set('resource_ids', newScope.resource_ids.join(','));
        p.delete('resource_id');
      } else {
        p.delete('resource_id');
        p.delete('resource_ids');
      }
      return p;
    });
  };

  const handleSelectTab = (tabId) => {
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      p.set('tab', tabId);
      return p;
    });
  };

  const handleSelectConversation = (convId) => {
    if (!convId || convId === 'undefined') return;
    setActiveConversationId(convId);
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      p.set('conversation_id', convId);
      return p;
    });
  };

  const handleNewChat = () => {
    setActiveConversationId(null);
    setLocalMessages([]);
    setActiveCitations([]);
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      p.delete('conversation_id');
      return p;
    });
  };

  const handleSendMessage = async (text) => {
    const userMsg = { sender: 'user', content: text };
    setLocalMessages((prev) => [...prev, userMsg]);

    try {
      const result = await sendMessageMutation.mutateAsync({
        message: text,
        scope: scope,
        resource_ids: scope.mode === 'selected' ? scope.resource_ids : [],
        resource_id: singleResourceId,
        conversation_id: activeConversationId,
      });

      const assistantMsg = {
        sender: 'assistant',
        content: result.answer,
        sources: result.sources || [],
      };
      setLocalMessages((prev) => [...prev, assistantMsg]);

      if (result.sources && result.sources.length > 0) {
        setActiveCitations(result.sources);
      }

      const newConvId = result.conversation_id || result.id;
      if (newConvId && newConvId !== activeConversationId) {
        setActiveConversationId(newConvId);
        setSearchParams((prev) => {
          const p = new URLSearchParams(prev);
          p.set('conversation_id', newConvId);
          return p;
        });
      }
    } catch {
      setLocalMessages((prev) => prev.slice(0, -1));
    }
  };

  const handleDeleteConversation = async (conv) => {
    if (!conv) return;
    const targetId = conv.id || conv.conversation_id;
    try {
      await deleteConversationMutation.mutateAsync(targetId);
      if (activeConversationId === targetId) {
        handleNewChat();
      }
    } catch {
      // Toast handles error
    }
  };

  const handleGenerateSummary = async (forceRegenerate = false) => {
    if (!singleResourceId) return;
    try {
      await generateSummaryMutation.mutateAsync({
        resourceId: singleResourceId,
        forceRegenerate,
      });
      addToast({
        type: 'success',
        title: 'Summary Generated',
        message: 'Map-reduce AI summary created successfully.',
      });
    } catch {
      // Error handled by mutation
    }
  };

  const handleGenerateNotes = async (style, forceRegenerate = false) => {
    if (!singleResourceId) return;
    try {
      await generateNotesMutation.mutateAsync({
        resourceId: singleResourceId,
        style,
        forceRegenerate,
      });
      addToast({
        type: 'success',
        title: 'Notes Generated',
        message: 'Structured study notes created successfully.',
      });
    } catch {
      // Error handled by mutation
    }
  };

  const handleGenerateQuiz = async ({ questionCount, difficulty }) => {
    if (!singleResourceId) return null;
    try {
      const res = await generateQuizMutation.mutateAsync({
        resourceId: singleResourceId,
        questionCount,
        difficulty,
      });
      addToast({
        type: 'success',
        title: 'Quiz Ready',
        message: 'Multiple-choice quiz generated successfully.',
      });
      return res;
    } catch {
      return null;
    }
  };

  const activeConversationObj = conversations.find(
    (c) => (c.id || c.conversation_id) === activeConversationId
  );

  return (
    <AppLayout hideMainScrollbar>
      <div className="flex flex-col h-full overflow-hidden bg-[#07090d]">
        {/* Compact Workspace Header */}
        <StudyWorkspaceHeader
          activeTab={activeTab}
          resources={resources}
          scope={scope}
          onChangeScope={handleChangeScope}
          selectedResourceId={singleResourceId}
          onSelectResource={(id) =>
            handleChangeScope(id ? { mode: 'selected', resource_ids: [id] } : { mode: 'all', resource_ids: [] })
          }
          onSelectTab={handleSelectTab}
          onNewChat={handleNewChat}
          onDeleteConversation={() => handleDeleteConversation(activeConversationObj)}
          activeConversation={activeConversationObj}
          onToggleMobileSidebar={() => setMobileSidebarOpen(!mobileSidebarOpen)}
          onToggleMobileCitations={() => setMobileCitationsOpen(!mobileCitationsOpen)}
          activeCitationsCount={activeCitations.length}
        />

        {/* Tab Canvas Area */}
        <div className="flex-1 overflow-hidden relative">
          {activeTab === 'chat' && (
            <ChatTab
              conversations={conversations}
              activeConversationId={activeConversationId}
              onSelectConversation={handleSelectConversation}
              onNewChat={handleNewChat}
              onDeleteConversation={handleDeleteConversation}
              messages={localMessages}
              isLoadingMessages={isLoadingMessages}
              isSending={sendMessageMutation.isPending}
              onSendMessage={handleSendMessage}
              citations={activeCitations}
              selectedCitationIndex={selectedCitationIdx}
              onSelectCitation={(source, idx) => setSelectedCitationIdx(idx)}
              mobileSidebarOpen={mobileSidebarOpen}
              onCloseMobileSidebar={() => setMobileSidebarOpen(false)}
              mobileCitationsOpen={mobileCitationsOpen}
              onCloseMobileCitations={() => setMobileCitationsOpen(false)}
            />
          )}

          {activeTab === 'summary' && (
            <div className="h-full overflow-y-auto no-scrollbar px-4 sm:px-6 md:px-8 max-w-5xl mx-auto">
              <SummaryTab
                selectedResource={selectedResource}
                summary={summary}
                isLoadingSummary={isLoadingSummary}
                isGenerating={generateSummaryMutation.isPending}
                onGenerateSummary={handleGenerateSummary}
              />
            </div>
          )}

          {activeTab === 'notes' && (
            <div className="h-full overflow-y-auto no-scrollbar px-4 sm:px-6 md:px-8 max-w-5xl mx-auto">
              <NotesTab
                selectedResource={selectedResource}
                notes={notes}
                isLoadingNotes={isLoadingNotes}
                isGenerating={generateNotesMutation.isPending}
                onGenerateNotes={handleGenerateNotes}
                noteStyle={noteStyle}
                setNoteStyle={setNoteStyle}
                onChangeStyle={setNoteStyle}
              />
            </div>
          )}

          {activeTab === 'quiz' && (
            <div className="h-full overflow-y-auto no-scrollbar px-4 sm:px-6 md:px-8 max-w-5xl mx-auto">
              <QuizTab
                selectedResource={selectedResource}
                quizzes={quizzes}
                isLoadingQuizzes={isLoadingQuizzes}
                isGenerating={generateQuizMutation.isPending}
                onGenerateQuiz={handleGenerateQuiz}
              />
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
