import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  MessageSquare,
  BookOpen,
  NotebookPen,
  HelpCircle,
  MoreVertical,
  Trash2,
  Copy,
  RefreshCw,
  FileText,
  Video,
} from 'lucide-react';
import { ConfirmDialog } from '../ui/ConfirmDialog';

export function ResourceStudyHeader({
  activeTab, // 'chat' | 'summary' | 'notes' | 'quiz'
  selectedResource,
  onCopy,
  onRegenerate,
  onDeleteContent,
  isDeleteLoading = false,
  deleteTitle = '',
  deleteMessage = '',
  variant = 'card', // 'card' | 'inline'
}) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [menuOpen, setMenuOpen] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  const resourceId = selectedResource?.resource_id || selectedResource?.id || searchParams.get('resource_id') || '';
  const isPdf = selectedResource?.source_type === 'pdf';

  let cleanTitle = selectedResource?.title || selectedResource?.display_source;
  if (!cleanTitle || cleanTitle.startsWith('http://') || cleanTitle.startsWith('https://')) {
    if (selectedResource?.source_type === 'youtube') cleanTitle = 'YouTube Video Lecture';
    else if (selectedResource?.source) cleanTitle = selectedResource.source.split(/[/\\]/).pop();
    else cleanTitle = 'Selected Material';
  }

  const tabs = [
    { id: 'chat', label: 'Chat', icon: MessageSquare, path: `/workspace?resource_id=${resourceId}&tab=chat` },
    { id: 'summary', label: 'Summary', icon: BookOpen, path: `/workspace?resource_id=${resourceId}&tab=summary` },
    { id: 'notes', label: 'Notes', icon: NotebookPen, path: `/workspace?resource_id=${resourceId}&tab=notes` },
    { id: 'quiz', label: 'Quiz', icon: HelpCircle, path: `/workspace?resource_id=${resourceId}&tab=quiz` },
  ];

  const handleTabClick = (tab) => {
    navigate(tab.path);
  };

  const handleDeleteConfirm = async () => {
    if (onDeleteContent) {
      await onDeleteContent();
    }
    setConfirmDeleteOpen(false);
    setMenuOpen(false);
  };

  if (variant === 'inline') {
    return (
      <div className="flex items-center justify-between gap-2 shrink-0 w-full">
        {/* Resource Badge & Title */}
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
              isPdf
                ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400'
                : 'bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400'
            }`}
          >
            {isPdf ? <FileText className="w-3.5 h-3.5" /> : <Video className="w-3.5 h-3.5" />}
          </div>
          <span className="font-bold text-xs text-slate-800 dark:text-slate-200 truncate max-w-[150px] sm:max-w-[240px] md:max-w-[320px]">
            {cleanTitle}
          </span>
        </div>

        {/* Compact Segmented Tabs */}
        <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-900 p-1 rounded-xl border border-slate-200/80 dark:border-slate-700/80 shrink-0">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabClick(tab)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                  isActive
                    ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-200 dark:border-slate-700/80 shadow-sm mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Resource Context Info */}
        <div className="flex items-center gap-3 min-w-0">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              isPdf
                ? 'bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400'
                : 'bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400'
            }`}
          >
            {isPdf ? <FileText className="w-5 h-5" /> : <Video className="w-5 h-5" />}
          </div>
          <div className="min-w-0">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Study Context Resource
            </div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate">
              {cleanTitle}
            </h3>
          </div>
        </div>

        {/* Contextual Nav Tabs & Actions Menu */}
        <div className="flex items-center justify-between md:justify-end gap-2 shrink-0">
          <div className="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-xl border border-slate-200/80 dark:border-slate-700/80">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabClick(tab)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                    isActive
                      ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Context Actions Dropdown [•••] */}
          {onDeleteContent && (
            <div className="relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors"
                title="More Resource Tools & Actions"
              >
                <MoreVertical className="w-4 h-4" />
              </button>

              {menuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-lg py-1.5 z-30 text-xs font-semibold">
                  {onCopy && (
                    <button
                      onClick={() => {
                        onCopy();
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/60 flex items-center gap-2"
                    >
                      <Copy className="w-3.5 h-3.5 text-slate-400" />
                      <span>Copy Content</span>
                    </button>
                  )}

                  {onRegenerate && (
                    <button
                      onClick={() => {
                        onRegenerate();
                        setMenuOpen(false);
                      }}
                      className="w-full text-left px-3 py-2 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/60 flex items-center gap-2"
                    >
                      <RefreshCw className="w-3.5 h-3.5 text-blue-500" />
                      <span>Regenerate Fresh</span>
                    </button>
                  )}

                  {onCopy || onRegenerate ? <div className="my-1 border-t border-slate-100 dark:border-slate-700/50" /> : null}

                  <button
                    onClick={() => {
                      setConfirmDeleteOpen(true);
                      setMenuOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 flex items-center gap-2"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-red-500" />
                    <span>Delete {activeTab.toUpperCase()}</span>
                  </button>
                </div>
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
        title={deleteTitle || `Delete ${activeTab.toUpperCase()}?`}
        message={
          deleteMessage ||
          `This will permanently remove the generated ${activeTab} for this resource. You can regenerate it anytime.`
        }
        isLoading={isDeleteLoading}
      />
    </div>
  );
}
