import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  BookOpen,
  HelpCircle,
  History,
  Settings,
  X,
  Compass,
  PanelLeftClose,
  PanelLeft,
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const navItems = [
  { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { name: 'Resources', to: '/resources', icon: FileText },
  { name: 'AI Chat', to: '/workspace?tab=chat', icon: MessageSquare, tab: 'chat' },
  { name: 'Notes', to: '/workspace?tab=notes', icon: BookOpen, tab: 'notes' },
  { name: 'Quizzes', to: '/workspace?tab=quiz', icon: HelpCircle, tab: 'quiz' },
  { name: 'Conversations', to: '/conversations', icon: History },
  { name: 'Settings', to: '/settings', icon: Settings },
];

export function Sidebar({ isOpen, onClose, isCollapsed = false, onToggleCollapse }) {
  const { user } = useAuth();
  const location = useLocation();
  const currentPath = location.pathname;
  const searchParams = new URLSearchParams(location.search);
  const currentTab = searchParams.get('tab') || 'chat';

  const checkIsActive = (item) => {
    if (item.tab) {
      return currentPath === '/workspace' && currentTab === item.tab;
    }
    if (item.to.startsWith('/workspace')) {
      return currentPath === '/workspace' && (!currentTab || currentTab === 'chat');
    }
    return currentPath === item.to || currentPath.startsWith(item.to + '/');
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  };

  const userInitials = getInitials(user?.name);

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm md:hidden transition-opacity duration-300"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full bg-[#0a0f18] border-r border-white/[0.07] flex flex-col justify-between transition-all duration-300 ease-out ${
          isOpen ? 'translate-x-0 w-64' : 'max-md:-translate-x-full'
        } ${isCollapsed ? 'md:w-20' : 'md:w-64'}`}
      >
        <div>
          {/* Brand Header */}
          <div className="h-16 border-b border-white/[0.07] flex items-center transition-all duration-300">
            {isCollapsed ? (
              <div className="h-full w-full hidden md:flex items-center justify-center">
                <button
                  onClick={onToggleCollapse}
                  className="p-2.5 rounded-xl bg-blue-600/10 text-blue-500 hover:bg-blue-600/20 transition-all"
                  title="Expand Sidebar"
                  aria-label="Expand Sidebar"
                >
                  <Compass className="w-5 h-5 text-blue-400" />
                </button>
              </div>
            ) : (
              <div className="h-full px-5 flex items-center justify-between w-full">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-sm shadow-blue-500/30">
                    <Compass className="w-4.5 h-4.5" />
                  </div>
                  <span className="font-extrabold text-base tracking-tight font-sans whitespace-nowrap text-[#f5f7fa]">
                    Study<span className="text-blue-500">Pilot</span> <span className="text-xs px-1.5 py-0.5 rounded-md bg-blue-500/10 text-blue-400 font-bold border border-blue-500/20 ml-1">AI</span>
                  </span>
                </div>

                <div className="flex items-center gap-1">
                  {onToggleCollapse && (
                    <button
                      onClick={onToggleCollapse}
                      className="hidden md:flex p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors"
                      title="Collapse Sidebar"
                      aria-label="Collapse Sidebar"
                    >
                      <PanelLeftClose className="w-4 h-4" />
                    </button>
                  )}

                  {/* Mobile Close Button */}
                  <button
                    onClick={onClose}
                    className="p-1 rounded-lg text-slate-400 hover:text-white md:hidden"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1.5 overflow-y-auto no-scrollbar max-h-[calc(100vh-160px)]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = checkIsActive(item);
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={`group relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-150 ${
                    isCollapsed ? 'md:justify-center md:px-0' : ''
                  } ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                      : 'text-[#9ca8ba] hover:text-[#f5f7fa] hover:bg-white/[0.04]'
                  }`}
                >
                  <Icon
                    className={`w-4.5 h-4.5 shrink-0 transition-transform duration-150 ${
                      isActive ? 'text-white' : 'text-[#9ca8ba] group-hover:text-white'
                    }`}
                  />

                  {/* Text Label */}
                  <span
                    className={`whitespace-nowrap transition-all duration-200 ${
                      isCollapsed ? 'md:hidden' : 'opacity-100'
                    }`}
                  >
                    {item.name}
                  </span>

                  {/* Tooltip when collapsed */}
                  {isCollapsed && (
                    <div className="hidden md:block opacity-0 group-hover:opacity-100 invisible group-hover:visible absolute left-full ml-3 px-3 py-1.5 bg-[#101827] text-[#f5f7fa] text-xs font-semibold rounded-lg shadow-xl border border-white/[0.08] whitespace-nowrap z-50 pointer-events-none transition-all">
                      {item.name}
                    </div>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Bottom User Card matching reference image */}
        <div className="p-3 border-t border-white/[0.07]">
          {isCollapsed ? (
            <div className="flex justify-center">
              <div className="w-9 h-9 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center shadow-sm shadow-blue-500/30">
                {userInitials}
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3 px-2 py-2 rounded-xl bg-white/[0.02] border border-white/[0.04]">
              <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-sm shadow-blue-500/30">
                {userInitials}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-bold text-[#f5f7fa] truncate">
                  {user?.name || 'Aarav Sharma'}
                </p>
                <p className="text-[11px] text-[#667085] truncate">
                  {user?.email || 'demo.student@studypilot.local'}
                </p>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
