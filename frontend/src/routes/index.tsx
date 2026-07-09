import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom';

import { ProtectedRoute } from '@/components/auth/auth-guard';
import { DashboardLayout } from '@/components/layout/dashboard-layout';

const Home = lazy(() => import('./home'));
const LoginPage = lazy(() => import('./auth/login'));
const RegisterPage = lazy(() => import('./auth/register'));
const DashboardPage = lazy(() => import('./dashboard'));
const TasksPage = lazy(() => import('./dashboard/tasks'));
const SsoCallbackPage = lazy(() => import('./sso/callback'));
const SamlCallbackPage = lazy(() => import('./auth/saml/callback'));

function RouteFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>
  );
}

function ProtectedDashboardLayout() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <Outlet />
      </DashboardLayout>
    </ProtectedRoute>
  );
}

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/auth/login" element={<LoginPage />} />
          <Route path="/auth/register" element={<RegisterPage />} />
          <Route path="/sso/callback" element={<SsoCallbackPage />} />
          <Route path="/auth/saml/callback" element={<SamlCallbackPage />} />
          <Route path="/dashboard" element={<ProtectedDashboardLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="tasks" element={<TasksPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
