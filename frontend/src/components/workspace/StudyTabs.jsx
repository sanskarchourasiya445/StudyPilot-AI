import React from 'react';
import { MessageSquare, BookOpen, NotebookPen, HelpCircle } from 'lucide-react';

export function StudyTabs({ activeTab, onSelectTab }) {
  const tabs = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'summary', label: 'Summary', icon: BookOpen },
    { id: 'notes', label: 'Notes', icon: NotebookPen },
    { id: 'quiz', label: 'Quiz', icon: HelpCircle },
  ];

  return (
    <div className="flex items-center gap-1 bg-[#0a0f18] p-1 rounded-xl border border-white/[0.08] shrink-0">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onSelectTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              isActive
                ? 'bg-blue-600 text-white shadow-blue-600/20'
                : 'text-[#9ca8ba] hover:text-[#f5f7fa]'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
