import React, { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('studypilot_theme') || 'dark';
    } catch {
      return 'dark';
    }
  });

  const [resolvedTheme, setResolvedTheme] = useState(() => {
    try {
      const saved = localStorage.getItem('studypilot_theme') || 'dark';
      if (saved === 'system') {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      return saved === 'light' ? 'light' : 'dark';
    } catch {
      return 'dark';
    }
  });

  useEffect(() => {
    const root = document.documentElement;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const updateTheme = () => {
      const isSystem = theme === 'system';
      const isDark = theme === 'dark' || (isSystem && mediaQuery.matches);
      const effective = isDark ? 'dark' : 'light';

      setResolvedTheme(effective);

      if (isDark) {
        root.classList.add('dark');
        root.setAttribute('data-theme', 'dark');
      } else {
        root.classList.remove('dark');
        root.setAttribute('data-theme', 'light');
      }
    };

    updateTheme();

    try {
      localStorage.setItem('studypilot_theme', theme);
    } catch (e) {
      console.error('Failed to save theme preference:', e);
    }

    const handleChange = () => {
      if (theme === 'system') {
        updateTheme();
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  const cycleTheme = () => {
    setTheme((current) => {
      if (current === 'dark') return 'light';
      if (current === 'light') return 'system';
      return 'dark';
    });
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme, isDark: resolvedTheme === 'dark', cycleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
