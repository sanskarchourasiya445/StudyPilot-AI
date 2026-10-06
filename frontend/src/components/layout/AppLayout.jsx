import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppLayout({
  children,
  title = 'Study Workspace',
  subtitle,
  rightSlot,
  fullBleed = false,
  hideTopbar = false,
  mobileSidebarOpen: controlledMobileSidebarOpen,
  setMobileSidebarOpen: controlledSetMobileSidebarOpen,
}) {
  const [internalMobileSidebarOpen, setInternalMobileSidebarOpen] = useState(false);
  const mobileSidebarOpen =
    controlledMobileSidebarOpen !== undefined
      ? controlledMobileSidebarOpen
      : internalMobileSidebarOpen;
  const setMobileSidebarOpen =
    controlledSetMobileSidebarOpen || setInternalMobileSidebarOpen;

  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem('studypilot_sidebar_collapsed') === 'true';
  });

  const toggleCollapse = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem('studypilot_sidebar_collapsed', String(next));
      return next;
    });
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#07090d] text-[#f5f7fa] flex selection:bg-blue-600 selection:text-white">
      {/* Sidebar Navigation */}
      <Sidebar
        isOpen={mobileSidebarOpen}
        onClose={() => setMobileSidebarOpen(false)}
        isCollapsed={isCollapsed}
        onToggleCollapse={toggleCollapse}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col h-full min-w-0 transition-[padding-left] duration-300 ease-in-out ${
          isCollapsed ? 'md:pl-20' : 'md:pl-64'
        }`}
      >
        {!hideTopbar && (
          <Topbar
            onOpenSidebar={() => setMobileSidebarOpen(true)}
            isCollapsed={isCollapsed}
            onToggleCollapse={toggleCollapse}
            title={title}
            subtitle={subtitle}
            rightSlot={rightSlot}
          />
        )}
        <main
          className={
            fullBleed
              ? 'flex-1 w-full h-full overflow-hidden flex flex-col'
              : 'flex-1 p-4 md:p-6 lg:p-8 max-w-6xl w-full mx-auto overflow-y-auto no-scrollbar'
          }
        >
          {children}
        </main>
      </div>
    </div>
  );
}
