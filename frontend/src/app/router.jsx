import React from 'react';
import { createBrowserRouter, Navigate, useSearchParams } from 'react-router-dom';
import { ProtectedRoute, PublicOnlyRoute } from '../components/layout/ProtectedRoute';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { DashboardPage } from '../pages/DashboardPage';
import { ResourcesPage } from '../pages/ResourcesPage';
import { ResourceDetailPage } from '../pages/ResourceDetailPage';
import { WorkspacePage } from '../pages/WorkspacePage';
import { HistoryPage } from '../pages/HistoryPage';
import { SearchPage } from '../pages/SearchPage';
import { SettingsPage } from '../pages/SettingsPage';
import { NotFoundPage } from '../pages/NotFoundPage';

// Helper component to preserve resource_id & query params on legacy route redirects
function LegacyRouteRedirect({ tab }) {
  const [searchParams] = useSearchParams();
  const resId = searchParams.get('resource_id');
  const params = new URLSearchParams(searchParams);
  params.set('tab', tab);
  return <Navigate to={`/workspace?${params.toString()}`} replace />;
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/workspace" replace />,
  },

  // Public-only Routes (Auth)
  {
    element: <PublicOnlyRoute />,
    children: [
      {
        path: '/login',
        element: <LoginPage />,
      },
      {
        path: '/register',
        element: <RegisterPage />,
      },
    ],
  },

  // Protected Application Routes
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: '/workspace',
        element: <WorkspacePage />,
      },
      {
        path: '/dashboard',
        element: <Navigate to="/workspace" replace />,
      },
      {
        path: '/resources',
        element: <ResourcesPage />,
      },
      {
        path: '/resources/:id',
        element: <ResourceDetailPage />,
      },
      {
        path: '/summaries',
        element: <LegacyRouteRedirect tab="summary" />,
      },
      {
        path: '/notes',
        element: <LegacyRouteRedirect tab="notes" />,
      },
      {
        path: '/quizzes',
        element: <LegacyRouteRedirect tab="quiz" />,
      },
      {
        path: '/history',
        element: <HistoryPage />,
      },
      {
        path: '/conversations',
        element: <Navigate to="/history" replace />,
      },
      {
        path: '/search',
        element: <Navigate to="/resources" replace />,
      },
      {
        path: '/settings',
        element: <SettingsPage />,
      },
    ],
  },

  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
