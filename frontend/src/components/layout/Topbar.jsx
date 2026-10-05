import React from 'react';
import { Menu, Sun, Moon, Monitor, Search, LogOut, Compass } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { useAuth } from '../../hooks/useAuth';

export function Topbar({
  onOpenSidebar,
  isCollapsed = false,
  onToggleCollapse,
  title = 'Dashboard',
  subtitle,
  rightSlot,
}) {
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();

  const toggleTheme = () => {
    if (theme === 'light') setTheme('dark');
    else if (theme === 'dark') setTheme('system');
    else setTheme('light');
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

  return (
    <header className="h-16 bg-[#07090d]/80 backdrop-blur-md border-b border-white/[0.07] sticky top-0 z-30 px-4 md:px-6 flex items-center justify-between transition-colors">
      {/* Left: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-2 md:gap-3 min-w-0">
        <button
          onClick={onOpenSidebar}
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/[0.05] md:hidden"
          aria-label="Open Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="min-w-0">
          <h1 className="text-base md:text-lg font-bold text-[#f5f7fa] tracking-tight truncate">
            {title}
          </h1>
          {subtitle && (
            <p className="text-[11px] text-[#9ca8ba] font-medium truncate -mt-0.5">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      {/* Center: Search Bar */}
      <div className="hidden md:flex items-center flex-1 max-w-md mx-6">
        <div className="w-full relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search resources, topics, conversations..."
            className="w-full bg-[#0d1420] border border-white/[0.08] rounded-xl pl-9 pr-4 py-2 text-xs text-[#f5f7fa] placeholder:text-slate-500 focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/30 transition-all"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.target.value.trim()) {
                window.location.href = `/resources?search=${encodeURIComponent(e.target.value.trim())}`;
              }
            }}
          />
        </div>
      </div>

      {/* Right: Slot, Theme Toggle, Profile */}
      <div className="flex items-center gap-2 md:gap-3 shrink-0">
        {rightSlot}

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-xl border border-white/[0.08] bg-[#0d1420] text-slate-400 hover:text-white hover:bg-white/[0.05] transition-colors"
          title={`Theme: ${theme.toUpperCase()}`}
          aria-label="Toggle Theme"
        >
          {theme === 'light' ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-blue-400" />
          )}
        </button>

        {/* User Profile Pill */}
        {user && (
          <div className="flex items-center gap-2.5 border-l border-white/[0.08] pl-2 md:pl-3">
            <a
              href="/settings"
              className="flex items-center gap-2 group"
              title={user.email}
            >
              <div className="w-8 h-8 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center font-bold text-xs group-hover:ring-2 group-hover:ring-blue-500/50 transition-all">
                {getInitials(user.name)}
              </div>
              <span className="hidden lg:inline text-xs font-semibold text-[#f5f7fa] max-w-[120px] truncate group-hover:text-blue-400 transition-colors">
                {user.name}
              </span>
            </a>
            <button
              onClick={logout}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-white/[0.05] transition-colors"
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
