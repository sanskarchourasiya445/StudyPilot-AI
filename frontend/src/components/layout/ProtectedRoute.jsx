import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { Loader2, Compass } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

export function ProtectedRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col items-center justify-center p-6 text-center">
        <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white mb-4 animate-bounce">
          <Compass className="w-6 h-6" />
        </div>
        <Loader2 className="w-6 h-6 animate-spin text-blue-600 dark:text-blue-400 mb-2" />
        <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Verifying session...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

export function PublicOnlyRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex flex-col items-center justify-center p-6 text-center">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600 dark:text-blue-400" />
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
