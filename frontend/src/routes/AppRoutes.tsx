import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '../layouts/MainLayout';
import { AuthLayout } from '../layouts/AuthLayout';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { DashboardPage } from '../pages/DashboardPage';
import { ProblemExplorerPage } from '../pages/ProblemExplorerPage';
import { ProblemDetailPage } from '../pages/ProblemDetailPage';
import { ProfilePage } from '../pages/ProfilePage';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { InterviewSetupPage } from '../pages/InterviewSetupPage';
import { InterviewSessionPage } from '../pages/InterviewSessionPage';
import { InterviewHistoryPage } from '../pages/InterviewHistoryPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { useAuth } from '../context/AuthContext';

export const AppRoutes: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      {/* Root redirect */}
      <Route
        path="/"
        element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />}
      />

      {/* Auth Routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Protected App Routes */}
      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/problems" element={<ProblemExplorerPage />} />
        <Route path="/problems/:slug" element={<ProblemDetailPage />} />
        <Route path="/interview" element={<InterviewSetupPage />} />
        <Route path="/interview/:sessionId" element={<InterviewSessionPage />} />
        <Route path="/interview/history" element={<InterviewHistoryPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>

      {/* 404 Route */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};
