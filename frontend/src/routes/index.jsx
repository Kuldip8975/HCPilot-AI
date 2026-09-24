import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import { ProtectedRoute } from './ProtectedRoute';
import { PublicRoute } from './PublicRoute';
import { ROUTES } from './RouteConstants';
import { MainLayout } from '../layouts/MainLayout';
import { Loading } from '../components/common/Loading';

// Lazy load pages for code splitting
const LoginPage = lazy(() => import('../pages/LoginPage'));
const DashboardPage = lazy(() => import('../pages/DashboardPage'));
const HCPListPage = lazy(() => import('../pages/HCPListPage'));
const HCPDetailsPage = lazy(() => import('../pages/HCPDetailsPage'));
const LogInteractionPage = lazy(() => import('../pages/LogInteractionPage'));
const InteractionHistoryPage = lazy(() => import('../pages/InteractionHistoryPage'));
const AnalyticsPage = lazy(() => import('../pages/AnalyticsPage'));
const ChatPage = lazy(() => import('../pages/ChatPage'));
const SettingsPage = lazy(() => import('../pages/SettingsPage'));

/**
 * AppRoutes Component
 * Defines all application routes with authentication protection
 */
export const AppRoutes = () => {
  return (
    <Suspense fallback={<Loading fullScreen message="Loading page..." />}>
      <Routes>
        {/* Public Routes */}
        <Route
          path={ROUTES.LOGIN}
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />

        {/* Protected Routes */}
        <Route
          path={ROUTES.HOME}
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          {/* Dashboard */}
          <Route index element={<Navigate to={ROUTES.DASHBOARD} replace />} />
          <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />

          {/* HCP Management */}
          <Route path={ROUTES.HCPS} element={<HCPListPage />} />
          <Route path={ROUTES.HCP_DETAILS} element={<HCPDetailsPage />} />

          {/* Interaction Management */}
          <Route path={ROUTES.INTERACTION_NEW} element={<LogInteractionPage />} />
          <Route path={ROUTES.INTERACTION_HISTORY} element={<InteractionHistoryPage />} />

          {/* Chat */}
          <Route path={ROUTES.CHAT} element={<ChatPage />} />

          {/* Analytics */}
          <Route path={ROUTES.ANALYTICS} element={<AnalyticsPage />} />

          {/* Settings */}
          <Route path={ROUTES.SETTINGS} element={<SettingsPage />} />
        </Route>

        {/* 404 Not Found - Redirect to dashboard */}
        <Route path={ROUTES.NOT_FOUND} element={<Navigate to={ROUTES.DASHBOARD} replace />} />
      </Routes>
    </Suspense>
  );
};

export default AppRoutes;