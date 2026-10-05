import React from 'react';
import { ConversationSidebar } from './ConversationSidebar';
import { ChatThread } from './ChatThread';
import { MessageComposer } from './MessageComposer';
import { CitationPanel } from './CitationPanel';

export function ChatTab({
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  resources = [],
  selectedResourceId,
  onSelectResource,
  messages,
  localMessages = [],
  isLoadingMessages = false,
  isSending = false,
  onSendMessage,
  citations,
  activeCitations = [],
  selectedCitationIndex,
  selectedCitationIdx,
  onSelectCitation,
  mobileSidebarOpen = false,
  onCloseMobileSidebar,
  setMobileSidebarOpen,
  mobileCitationsOpen = false,
  onCloseMobileCitations,
  setMobileCitationsOpen,
}) {
  const displayMessages = messages || localMessages;
  const displayCitations = citations || activeCitations;
  const displayCitationIdx = selectedCitationIndex !== undefined ? selectedCitationIndex : selectedCitationIdx;
  const handleCloseSidebar = onCloseMobileSidebar || (() => setMobileSidebarOpen && setMobileSidebarOpen(false));
  const handleCloseCitations = onCloseMobileCitations || (() => setMobileCitationsOpen && setMobileCitationsOpen(false));

  return (
    <div className="h-[calc(100vh-145px)] min-h-[500px] flex rounded-2xl border border-white/[0.07] bg-[#07090d] overflow-hidden shadow-xs relative">
      {/* Panel 1: Left Conversation History Sidebar (Desktop) */}
      <div className="hidden lg:block w-64 h-full shrink-0 border-r border-white/[0.07]">
        <ConversationSidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={onSelectConversation}
          onNewChat={onNewChat}
          onDeleteConversation={onDeleteConversation}
          resources={resources}
          selectedResourceId={selectedResourceId}
          onSelectResource={onSelectResource}
        />
      </div>

      {/* Panel 2: Center Chat Workspace Thread & Composer (Flexible) */}
      <div className="flex-1 h-full flex flex-col min-w-0 bg-[#07090d]">
        <div className="flex-1 min-h-0 overflow-y-auto">
          <ChatThread
            messages={displayMessages}
            isLoading={isSending || isLoadingMessages}
            onSelectCitation={onSelectCitation}
          />
        </div>

        <MessageComposer onSend={onSendMessage} isLoading={isSending} />
      </div>

      {/* Panel 3: Right Grounded Citations Drawer (Desktop) */}
      <div className="hidden xl:block w-72 h-full shrink-0 border-l border-white/[0.07]">
        <CitationPanel
          citations={displayCitations}
          selectedCitationIndex={displayCitationIdx}
        />
      </div>

      {/* Mobile Drawer Slide-outs */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm lg:hidden flex">
          <div className="w-80 h-full bg-[#0a0f18] border-r border-white/[0.08]">
            <ConversationSidebar
              conversations={conversations}
              activeConversationId={activeConversationId}
              onSelectConversation={(cId) => {
                onSelectConversation(cId);
                handleCloseSidebar();
              }}
              onNewChat={() => {
                onNewChat();
                handleCloseSidebar();
              }}
              onDeleteConversation={onDeleteConversation}
              resources={resources}
              selectedResourceId={selectedResourceId}
              onSelectResource={onSelectResource}
            />
          </div>
          <div className="flex-1" onClick={handleCloseSidebar} />
        </div>
      )}

      {mobileCitationsOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm xl:hidden flex justify-end">
          <div className="w-80 h-full bg-[#0a0f18] border-l border-white/[0.08]">
            <CitationPanel
              citations={displayCitations}
              selectedCitationIndex={displayCitationIdx}
              onClose={handleCloseCitations}
            />
          </div>
        </div>
      )}
    </div>
  );
}
