import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../services/authApi';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => {
    try {
      return localStorage.getItem('studypilot_token') || null;
    } catch {
      return null;
    }
  });
  const [isLoading, setIsLoading] = useState(true);

  // Restore Session on App Load
  useEffect(() => {
    let isMounted = true;
    const restoreSession = async () => {
      const storedToken = localStorage.getItem('studypilot_token');
      if (!storedToken) {
        if (isMounted) setIsLoading(false);
        return;
      }

      try {
        const userData = await authApi.getMe();
        if (isMounted) {
          setUser(userData);
          setToken(storedToken);
        }
      } catch (error) {
        console.error('Session restoration failed:', error);
        localStorage.removeItem('studypilot_token');
        if (isMounted) {
          setUser(null);
          setToken(null);
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    restoreSession();
    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await authApi.login({ email, password });
    const newToken = data.access_token;

    localStorage.setItem('studypilot_token', newToken);
    setToken(newToken);

    // Fetch Profile
    const userData = await authApi.getMe();
    setUser(userData);
    return userData;
  }, []);

  const register = useCallback(async (email, password, name) => {
    await authApi.register({ email, password, name });
    // Automatically log in after registration
    return await login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem('studypilot_token');
    setUser(null);
    setToken(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
