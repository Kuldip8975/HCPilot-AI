import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { MainLayout } from './layouts/MainLayout';
import { ProtectedRoute } from './routes/ProtectedRoute';
import { PublicRoute } from './routes/PublicRoute';
import { Loading } from './components/common/Loading';
import { ROUTES } from './routes/RouteConstants';

// Lazy load pages
const HomePage = lazy(() => import('./pages/HomePage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const HCPListPage = lazy(() => import('./pages/HCPListPage'));
const HCPDetailsPage = lazy(() => import('./pages/HCPDetailsPage'));
const HCPFormPage = lazy(() => import('./pages/HCPFormPage'));
const LogInteractionPage = lazy(() => import('./pages/LogInteractionPage'));
const InteractionHistoryPage = lazy(() => import('./pages/InteractionHistoryPage'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));
const ChatPage = lazy(() => import('./pages/ChatPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const DoctorDashboardPage = lazy(() => import('./pages/DoctorDashboardPage'));
const ActivityLogPage = lazy(() => import('./pages/ActivityLogPage'));
const SmartSearchPage = lazy(() => import('./pages/SmartSearchPage'));
const PriorityDashboardPage = lazy(() => import('./pages/PriorityDashboardPage'));

const App = () => {
  return (
    <>
      <Suspense fallback={<Loading fullScreen message="Loading page..." />}>
        <Routes>
          {/* Home / Landing page - public, redirects to dashboard if already logged in */}
          <Route
            path={ROUTES.HOME}
            element={
              <PublicRoute>
                <HomePage />
              </PublicRoute>
            }
          />

          {/* Public Routes */}
          <Route
            path={ROUTES.LOGIN}
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path={ROUTES.REGISTER}
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            }
          />
          <Route
            path={ROUTES.FORGOT_PASSWORD}
            element={
              <PublicRoute>
                <ForgotPasswordPage />
              </PublicRoute>
            }
          />

          {/* Doctor dashboard - protected, but deliberately NOT inside
              MainLayout (that layout's sidebar is built for the sales-rep
              app: HCPs, Log Interaction, Analytics, etc., none of which a
              doctor account should see). It's just login-gated on its
              own; the page component itself only fetches doctor-scoped
              data, and the backend rejects a non-doctor token anyway. */}
          <Route
            path={ROUTES.DOCTOR_DASHBOARD}
            element={
              <ProtectedRoute>
                <DoctorDashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Protected Routes with MainLayout - pathless layout route so it doesn't claim "/" itself */}
          <Route
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            {/* Main Pages */}
            <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
            <Route path={ROUTES.HCPS} element={<HCPListPage />} />
            {/* Static "/hcps/create" and "/hcps/:id/edit" routes are
                registered alongside the dynamic "/hcps/:id" one - React
                Router v6 matches by specificity, not declaration order, so
                "create"/"...edit" never get swallowed by :id here. Without
                these two routes, "Add HCP"/"Edit Profile" had nowhere to
                go and "/hcps/create" was matching HCP_DETAILS instead,
                trying (and failing) to load an HCP literally named "create". */}
            <Route path={ROUTES.HCP_CREATE} element={<HCPFormPage />} />
            <Route path={ROUTES.HCP_EDIT} element={<HCPFormPage />} />
            <Route path={ROUTES.HCP_DETAILS} element={<HCPDetailsPage />} />

            <Route path={ROUTES.INTERACTIONS} element={<Navigate to={ROUTES.INTERACTION_NEW} replace />} />
            <Route path={ROUTES.INTERACTION_NEW} element={<LogInteractionPage />} />
            <Route path={ROUTES.INTERACTION_HISTORY} element={<InteractionHistoryPage />} />

            {/* Other Pages */}
            <Route path={ROUTES.ANALYTICS} element={<AnalyticsPage />} />
            <Route path={ROUTES.CHAT} element={<ChatPage />} />
            <Route path={ROUTES.ACTIVITY_LOG} element={<ActivityLogPage />} />
            <Route path={ROUTES.SMART_SEARCH} element={<SmartSearchPage />} />
            <Route path={ROUTES.PRIORITIES} element={<PriorityDashboardPage />} />
            <Route path={ROUTES.SETTINGS} element={<SettingsPage />} />
          </Route>

          {/* 404 - Redirect to Dashboard */}
          <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
        </Routes>
      </Suspense>

      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </>
  );
};

export default App;