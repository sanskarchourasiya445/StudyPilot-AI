import React from 'react';
import { MessageSquare, Plus, Trash2 } from 'lucide-react';
import { Button } from '../ui/Button';

export function ConversationSidebar({
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
}) {
  return (
    <div className="h-full flex flex-col bg-[#0a0f18] w-full">
      {/* Header & New Chat CTA */}
      <div className="p-3.5 border-b border-white/[0.07]">
        <Button
          variant="primary"
          size="sm"
          icon={Plus}
          onClick={onNewChat}
          className="w-full justify-center shadow-blue-600/20"
        >
          New Chat Thread
        </Button>
      </div>

      {/* Section Subheader */}
      <div className="px-4 pt-3 pb-2 flex items-center justify-between">
        <span className="text-[11px] font-extrabold uppercase tracking-wider text-slate-500">
          Recent Conversations
        </span>
        <span className="text-[11px] font-bold text-slate-400 bg-white/[0.05] px-2 py-0.5 rounded-full border border-white/[0.08]">
          {conversations.length}
        </span>
      </div>

      {/* Thread History List */}
      <div className="flex-1 overflow-y-auto no-scrollbar p-2 space-y-1">
        {conversations.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500">
            No recent study conversations.
          </div>
        ) : (
          conversations.map((c, idx) => {
            const convId = c.conversation_id || c.id;
            const isActive = convId === activeConversationId;
            return (
              <div
                key={convId || `conv-${idx}`}
                onClick={() => onSelectConversation(convId)}
                className={`group flex items-center justify-between gap-2 px-3 py-2.5 rounded-xl text-xs cursor-pointer transition-all duration-150 ${
                  isActive
                    ? 'bg-[#101827] text-blue-400 font-bold border border-blue-500/20'
                    : 'text-slate-400 hover:bg-white/[0.03] hover:text-[#f5f7fa]'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{c.title || 'Untitled Conversation'}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(c);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 transition-opacity"
                  title="Delete Thread"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
