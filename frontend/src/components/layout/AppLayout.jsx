import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppLayout({ children, title = 'Dashboard', subtitle, rightSlot }) {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
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
    <div className="min-h-screen bg-[#07090d] text-[#f5f7fa] flex selection:bg-blue-600 selection:text-white">
      {/* Sidebar Navigation */}
      <Sidebar
        isOpen={mobileSidebarOpen}
        onClose={() => setMobileSidebarOpen(false)}
        isCollapsed={isCollapsed}
        onToggleCollapse={toggleCollapse}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-[padding-left] duration-300 ease-in-out ${
          isCollapsed ? 'md:pl-20' : 'md:pl-64'
        }`}
      >
        <Topbar
          onOpenSidebar={() => setMobileSidebarOpen(true)}
          isCollapsed={isCollapsed}
          onToggleCollapse={toggleCollapse}
          title={title}
          subtitle={subtitle}
          rightSlot={rightSlot}
        />
        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
