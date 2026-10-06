import React, { useState } from 'react';
import { User, Sun, Moon, Monitor, LogOut, Check, Sliders, Shield } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../context/ThemeContext';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';

export function SettingsPage() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const { addToast } = useToast();

  const [activeSection, setActiveSection] = useState('profile'); // 'profile' | 'appearance' | 'preferences' | 'account'

  // Local-only study preferences stored in localStorage ('studypilot_preferences')
  const [preferences, setPreferences] = useState(() => {
    try {
      const saved = localStorage.getItem('studypilot_preferences');
      return saved ? JSON.parse(saved) : { quizQuestionCount: 5, quizDifficulty: 'medium' };
    } catch {
      return { quizQuestionCount: 5, quizDifficulty: 'medium' };
    }
  });

  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSavePreferences = (e) => {
    e.preventDefault();
    try {
      localStorage.setItem('studypilot_preferences', JSON.stringify(preferences));
      setSavedSuccess(true);
      addToast('Study preferences saved locally.', 'success');
      setTimeout(() => setSavedSuccess(false), 2000);
    } catch (err) {
      addToast('Failed to save preferences.', 'error');
    }
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
    <AppLayout title="Settings" subtitle="Manage your StudyPilot account and workspace preferences">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Left Sub-navigation Bar */}
        <div className="md:col-span-1 space-y-1">
          <button
            onClick={() => setActiveSection('profile')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
              activeSection === 'profile'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-[#9ca8ba] hover:bg-white/[0.04] hover:text-[#f5f7fa]'
            }`}
          >
            <User className="w-4 h-4" />
            <span>Profile</span>
          </button>

          <button
            onClick={() => setActiveSection('appearance')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
              activeSection === 'appearance'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-[#9ca8ba] hover:bg-white/[0.04] hover:text-[#f5f7fa]'
            }`}
          >
            <Sun className="w-4 h-4" />
            <span>Appearance</span>
          </button>

          <button
            onClick={() => setActiveSection('preferences')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
              activeSection === 'preferences'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-[#9ca8ba] hover:bg-white/[0.04] hover:text-[#f5f7fa]'
            }`}
          >
            <Sliders className="w-4 h-4" />
            <span>Study Preferences</span>
          </button>

          <button
            onClick={() => setActiveSection('account')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
              activeSection === 'account'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-[#9ca8ba] hover:bg-white/[0.04] hover:text-[#f5f7fa]'
            }`}
          >
            <Shield className="w-4 h-4" />
            <span>Account</span>
          </button>
        </div>

        {/* Right Content Panels */}
        <div className="md:col-span-3">
          {/* Section 1: Profile */}
          {activeSection === 'profile' && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-blue-600/20 text-blue-400 flex items-center justify-center font-extrabold text-sm border border-blue-500/30">
                    {getInitials(user?.name)}
                  </div>
                  <div>
                    <CardTitle className="text-[#f5f7fa]">{user?.name || 'Student User'}</CardTitle>
                    <CardDescription className="text-[#9ca8ba]">Academic Account Profile Overview</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                      Full Name (Read-Only)
                    </label>
                    <input
                      type="text"
                      readOnly
                      value={user?.name || 'Student User'}
                      className="w-full bg-[#0a0f18] border border-white/[0.08] text-[#f5f7fa] text-xs rounded-xl p-3 font-semibold cursor-not-allowed"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                      Email Address (Read-Only)
                    </label>
                    <input
                      type="text"
                      readOnly
                      value={user?.email || 'student@example.com'}
                      className="w-full bg-[#0a0f18] border border-white/[0.08] text-[#f5f7fa] text-xs rounded-xl p-3 font-semibold cursor-not-allowed"
                    />
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#0a0f18] border border-white/[0.07] flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#f5f7fa]">Account Status</span>
                  <span className="inline-flex items-center gap-1 font-bold text-emerald-400 bg-emerald-500/15 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Active Academic Member
                  </span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Section 2: Appearance */}
          {activeSection === 'appearance' && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                    <Sun className="w-5 h-5" />
                  </div>
                  <div>
                    <CardTitle>Appearance & Theme</CardTitle>
                    <CardDescription>Select your preferred visual interface style</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {/* Light Mode Preview Card */}
                  <button
                    type="button"
                    onClick={() => setTheme('light')}
                    className={`p-4 rounded-2xl border text-left transition-all relative overflow-hidden flex flex-col justify-between ${
                      theme === 'light'
                        ? 'border-blue-500 bg-blue-600/10 ring-1 ring-blue-500/30 shadow-sm'
                        : 'border-white/[0.08] bg-[#0a0f18] hover:border-blue-500/30'
                    }`}
                  >
                    <div className="w-full h-20 bg-white border border-slate-200 rounded-xl p-2.5 mb-3 shadow-2xs flex flex-col justify-between">
                      <div className="h-2 w-12 bg-slate-900 rounded-full" />
                      <div className="space-y-1">
                        <div className="h-1.5 w-full bg-slate-200 rounded-full" />
                        <div className="h-1.5 w-3/4 bg-blue-500 rounded-full" />
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <Sun className="w-4 h-4 text-amber-500" />
                          <span className="text-xs font-bold text-[#f5f7fa]">Light Mode</span>
                        </div>
                        {theme === 'light' && <Check className="w-4 h-4 text-blue-500" />}
                      </div>
                      <p className="text-[11px] text-[#9ca8ba]">Clean, crisp daytime interface</p>
                    </div>
                  </button>

                  {/* Dark Mode Preview Card */}
                  <button
                    type="button"
                    onClick={() => setTheme('dark')}
                    className={`p-4 rounded-2xl border text-left transition-all relative overflow-hidden flex flex-col justify-between ${
                      theme === 'dark'
                        ? 'border-blue-500 bg-blue-600/10 ring-1 ring-blue-500/30 shadow-sm'
                        : 'border-white/[0.08] bg-[#0a0f18] hover:border-blue-500/30'
                    }`}
                  >
                    <div className="w-full h-20 bg-[#07090d] border border-white/[0.08] rounded-xl p-2.5 mb-3 shadow-2xs flex flex-col justify-between">
                      <div className="h-2 w-12 bg-slate-100 rounded-full" />
                      <div className="space-y-1">
                        <div className="h-1.5 w-full bg-slate-800 rounded-full" />
                        <div className="h-1.5 w-3/4 bg-blue-400 rounded-full" />
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <Moon className="w-4 h-4 text-blue-400" />
                          <span className="text-xs font-bold text-[#f5f7fa]">Dark Mode</span>
                        </div>
                        {theme === 'dark' && <Check className="w-4 h-4 text-blue-500" />}
                      </div>
                      <p className="text-[11px] text-[#9ca8ba]">Focused obsidian & navy palette</p>
                    </div>
                  </button>

                  {/* System Preference Preview Card */}
                  <button
                    type="button"
                    onClick={() => setTheme('system')}
                    className={`p-4 rounded-2xl border text-left transition-all relative overflow-hidden flex flex-col justify-between ${
                      theme === 'system'
                        ? 'border-blue-500 bg-blue-600/10 ring-1 ring-blue-500/30 shadow-sm'
                        : 'border-white/[0.08] bg-[#0a0f18] hover:border-blue-500/30'
                    }`}
                  >
                    <div className="w-full h-20 bg-gradient-to-r from-slate-200 to-[#07090d] border border-white/[0.08] rounded-xl p-2.5 mb-3 shadow-2xs flex flex-col justify-between">
                      <div className="h-2 w-12 bg-blue-500 rounded-full" />
                      <div className="space-y-1">
                        <div className="h-1.5 w-full bg-slate-400/50 rounded-full" />
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <Monitor className="w-4 h-4 text-emerald-500" />
                          <span className="text-xs font-bold text-[#f5f7fa]">System Mode</span>
                        </div>
                        {theme === 'system' && <Check className="w-4 h-4 text-blue-500" />}
                      </div>
                      <p className="text-[11px] text-[#9ca8ba]">Follows your operating system</p>
                    </div>
                  </button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Section 3: Study Preferences */}
          {activeSection === 'preferences' && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-blue-600/10 text-blue-400 border border-blue-500/20 flex items-center justify-center">
                    <Sliders className="w-5 h-5" />
                  </div>
                  <div>
                    <CardTitle className="text-[#f5f7fa]">Study Preferences</CardTitle>
                    <CardDescription className="text-[#9ca8ba]">Configure local defaults for quiz generation</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSavePreferences} className="space-y-4 max-w-md">
                  <div>
                    <label className="text-[11px] font-bold uppercase tracking-wider text-[#9ca8ba] block mb-1.5">
                      Default Quiz Questions
                    </label>
                    <select
                      value={preferences.quizQuestionCount}
                      onChange={(e) =>
                        setPreferences((prev) => ({ ...prev, quizQuestionCount: Number(e.target.value) }))
                      }
                      className="w-full bg-[#0a0f18] border border-white/[0.08] text-xs text-[#f5f7fa] rounded-xl p-3 font-semibold focus:outline-none focus:border-blue-500"
                    >
                      <option value={3}>3 Questions</option>
                      <option value={5}>5 Questions</option>
                      <option value={10}>10 Questions</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[11px] font-bold uppercase tracking-wider text-[#9ca8ba] block mb-1.5">
                      Default Quiz Difficulty
                    </label>
                    <select
                      value={preferences.quizDifficulty}
                      onChange={(e) =>
                        setPreferences((prev) => ({ ...prev, quizDifficulty: e.target.value }))
                      }
                      className="w-full bg-[#0a0f18] border border-white/[0.08] text-xs text-[#f5f7fa] rounded-xl p-3 font-semibold focus:outline-none focus:border-blue-500"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>

                  <p className="text-[11px] text-slate-500 italic">
                    Note: Study preferences are saved locally in your browser storage.
                  </p>

                  <Button type="submit" variant="primary" size="sm" icon={savedSuccess ? Check : null}>
                    {savedSuccess ? 'Preferences Saved' : 'Save Preferences'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Section 4: Account */}
          {activeSection === 'account' && (
            <Card className="border-red-900/30 bg-[#0d1420]">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-red-600/10 text-red-400 border border-red-500/20 flex items-center justify-center">
                    <Shield className="w-5 h-5" />
                  </div>
                  <div>
                    <CardTitle className="text-red-400">Account Session & Security</CardTitle>
                    <CardDescription className="text-[#9ca8ba]">Sign out of your StudyPilot academic workspace</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-xs text-[#9ca8ba] leading-relaxed">
                  Signing out will end your active JWT session on this device. Your ingested materials, vector embeddings, and conversation history will remain securely saved.
                </p>
                <Button variant="destructive" size="sm" icon={LogOut} onClick={logout}>
                  Sign Out of StudyPilot
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
