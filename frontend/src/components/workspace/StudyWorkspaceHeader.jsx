import React, { useState } from 'react';
import {
  MoreVertical,
  Plus,
  Trash2,
  Copy,
  RefreshCw,
  Sparkles,
  PanelLeft,
  BookOpen,
} from 'lucide-react';
import { StudyResourceSelector } from './StudyResourceSelector';
import { StudyTabs } from './StudyTabs';
import { ConfirmDialog } from '../ui/ConfirmDialog';

export function StudyWorkspaceHeader({
  activeTab,
  resources = [],
  scope,
  onChangeScope,
  selectedResourceId,
  onSelectResource,
  onSelectTab,
  // Chat actions
  onNewChat,
  onDeleteConversation,
  activeConversation,
  // Summary / Notes / Quiz contextual actions
  onCopyContent,
  onRegenerateContent,
  onDeleteContent,
  isDeleteLoading = false,
  // Mobile drawer controls
  onToggleMobileSidebar,
  onToggleMobileCitations,
  activeCitationsCount = 0,
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  const getDeleteModalTitle = () => {
    switch (activeTab) {
      case 'chat':
        return 'Delete Chat Thread?';
      case 'summary':
        return 'Delete Summary?';
      case 'notes':
        return 'Delete Study Notes?';
      case 'quiz':
        return 'Delete Quiz?';
      default:
        return 'Delete Generated Content?';
    }
  };

  const getDeleteModalMessage = () => {
    switch (activeTab) {
      case 'chat':
        return 'This will permanently remove this chat conversation.';
      case 'summary':
        return 'This will permanently remove the generated summary for this resource. You can regenerate it anytime.';
      case 'notes':
        return 'This will permanently remove the generated notes for this resource.';
      case 'quiz':
        return 'This will permanently remove the generated quiz for this resource.';
      default:
        return 'This action will permanently delete this content.';
    }
  };

  const handleDeleteConfirm = async () => {
    if (activeTab === 'chat' && onDeleteConversation && activeConversation) {
      await onDeleteConversation(activeConversation);
    } else if (onDeleteContent) {
      await onDeleteContent();
    }
    setConfirmDeleteOpen(false);
    setMenuOpen(false);
  };

  return (
    <div className="h-16 px-4 bg-[#07090d] border-b border-white/[0.07] flex items-center justify-between gap-3 shrink-0">
      {/* Mobile Drawer Trigger & Resource Selector */}
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <button
          onClick={onToggleMobileSidebar}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white lg:hidden shrink-0"
          title="Toggle Navigation Sidebar"
        >
          <PanelLeft className="w-5 h-5" />
        </button>

        <StudyResourceSelector
          resources={resources}
          scope={scope}
          onChangeScope={onChangeScope}
          selectedResourceId={selectedResourceId}
          onSelectResource={onSelectResource}
        />
      </div>

      {/* Center/Right: Study Tabs, Mobile Citations & Context Actions */}
      <div className="flex items-center gap-2 shrink-0">
        <StudyTabs activeTab={activeTab} onSelectTab={onSelectTab} />

        {activeTab === 'chat' && onToggleMobileCitations && (
          <button
            onClick={onToggleMobileCitations}
            className="p-1.5 rounded-lg text-slate-400 hover:text-blue-400 xl:hidden flex items-center gap-1 font-semibold text-xs"
            title="Toggle Citations Drawer"
          >
            <BookOpen className="w-4 h-4" />
            <span className="hidden sm:inline">({activeCitationsCount})</span>
          </button>
        )}

        {/* Tab-Aware Contextual Action Menu [•••] */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-2 rounded-xl border border-white/[0.08] bg-[#0d1420] hover:bg-white/[0.05] text-slate-400 hover:text-white transition-colors"
            title="Context Actions & Management"
          >
            <MoreVertical className="w-4 h-4" />
          </button>

          {menuOpen && (
            <div className="absolute right-0 mt-2 w-52 bg-[#0d1420] rounded-xl border border-white/[0.08] shadow-2xl py-1.5 z-40 text-xs font-semibold">
              {/* Tab 1: Chat Menu Items */}
              {activeTab === 'chat' && (
                <>
                  <button
                    onClick={() => {
                      if (onNewChat) onNewChat();
                      setMenuOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 text-[#f5f7fa] hover:bg-white/[0.05] flex items-center gap-2"
                  >
                    <Plus className="w-3.5 h-3.5 text-blue-500" />
                    <span>New Chat Session</span>
                  </button>
                  {activeConversation && onDeleteConversation && (
                    <button
                      onClick={() => {
                        setConfirmDeleteOpen(true);
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 flex items-center gap-2 border-t border-slate-100 dark:border-slate-700/50 mt-1 pt-2"
                    >
                      <Trash2 className="w-3.5 h-3.5 text-red-500" />
                      <span>Delete Chat Thread</span>
                    </button>
                  )}
                </>
              )}

              {/* Tab 2: Summary Menu Items */}
              {activeTab === 'summary' && (
                <>
                  {onCopyContent && (
                    <button
                      onClick={() => {
                        onCopyContent();
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-[#f5f7fa] hover:bg-white/[0.05] flex items-center gap-2"
                    >
                      <Copy className="w-3.5 h-3.5 text-slate-400" />
                      <span>Copy Summary</span>
                    </button>
                  )}
                  {onRegenerateContent && (
                    <button
                      onClick={() => {
                        onRegenerateContent();
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-[#f5f7fa] hover:bg-white/[0.05] flex items-center gap-2"
                    >
                      <RefreshCw className="w-3.5 h-3.5 text-blue-500" />
                      <span>Regenerate Summary</span>
                    </button>
                  )}
                  {onDeleteContent && (
                    <button
                      onClick={() => {
                        setConfirmDeleteOpen(true);
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 flex items-center gap-2 border-t border-slate-100 dark:border-slate-700/50 mt-1 pt-2"
                    >
                      <Trash2 className="w-3.5 h-3.5 text-red-500" />
                      <span>Delete Summary</span>
                    </button>
                  )}
                </>
              )}

              {/* Tab 3: Notes Menu Items */}
              {activeTab === 'notes' && (
                <>
                  {onCopyContent && (
                    <button
                      onClick={() => {
                        onCopyContent();
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-[#f5f7fa] hover:bg-white/[0.05] flex items-center gap-2"
                    >
                      <Copy className="w-3.5 h-3.5 text-slate-400" />
                      <span>Copy Notes</span>
                    </button>
                  )}
                  {onRegenerateContent && (
                    <button
                      onClick={() => {
                        onRegenerateContent();
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-[#f5f7fa] hover:bg-white/[0.05] flex items-center gap-2"
                    >
                      <RefreshCw className="w-3.5 h-3.5 text-purple-500" />
                      <span>Regenerate Notes</span>
                    </button>
                  )}
                  {onDeleteContent && (
                    <button
                      onClick={() => {
                        setConfirmDeleteOpen(true);
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 flex items-center gap-2 border-t border-slate-100 dark:border-slate-700/50 mt-1 pt-2"
                    >
                      <Trash2 className="w-3.5 h-3.5 text-red-500" />
                      <span>Delete Notes</span>
                    </button>
                  )}
                </>
              )}

              {/* Tab 4: Quiz Menu Items */}
              {activeTab === 'quiz' && (
                <>
                  {onRegenerateContent && (
                    <button
                      onClick={() => {
                        onRegenerateContent();
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-[#f5f7fa] hover:bg-white/[0.05] flex items-center gap-2"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                      <span>Generate New Quiz</span>
                    </button>
                  )}
                  {onDeleteContent && (
                    <button
                      onClick={() => {
                        setConfirmDeleteOpen(true);
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 flex items-center gap-2 border-t border-slate-100 dark:border-slate-700/50 mt-1 pt-2"
                    >
                      <Trash2 className="w-3.5 h-3.5 text-red-500" />
                      <span>Delete Quiz</span>
                    </button>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      <ConfirmDialog
        isOpen={confirmDeleteOpen}
        onClose={() => setConfirmDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
        title={getDeleteModalTitle()}
        message={getDeleteModalMessage()}
        isLoading={isDeleteLoading}
      />
    </div>
  );
}
