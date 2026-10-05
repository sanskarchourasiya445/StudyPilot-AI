import React from 'react';
import { Compass, Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export function AuthLayout({ children, title, subtitle }) {
  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    if (theme === 'light') setTheme('dark');
    else if (theme === 'dark') setTheme('system');
    else setTheme('light');
  };

  return (
    <div className="min-h-screen bg-[#07090d] flex flex-col justify-center items-center p-4 sm:p-6 relative transition-colors">
      {/* Upper Theme Toggle */}
      <div className="absolute top-4 right-4">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-xl border border-white/[0.08] bg-[#0d1420] text-slate-400 hover:text-white transition-colors"
          title={`Theme: ${theme.toUpperCase()}`}
          aria-label="Toggle Theme"
        >
          {theme === 'light' ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-blue-400" />
          )}
        </button>
      </div>

      {/* Main Auth Card Container */}
      <div className="max-w-md w-full bg-[#0d1420] border border-white/[0.07] rounded-2xl p-6 sm:p-8 shadow-2xl transition-all">
        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white mx-auto mb-3 shadow-lg shadow-blue-600/30">
            <Compass className="w-6 h-6" />
          </div>
          <span className="font-extrabold text-2xl tracking-tight">
            <span className="text-[#f5f7fa]">Study</span>
            <span className="text-blue-400">Pilot</span>
          </span>
          <h1 className="text-lg font-bold text-[#f5f7fa] mt-2">{title}</h1>
          {subtitle && (
            <p className="text-xs text-[#9ca8ba] mt-1">{subtitle}</p>
          )}
        </div>

        {children}
      </div>

      {/* Footer info */}
      <p className="text-xs text-slate-500 mt-6 text-center">
        StudyPilot AI &copy; 2026. Academic Study Assistant Platform.
      </p>
    </div>
  );
}
