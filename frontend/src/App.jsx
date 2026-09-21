import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute } from './components/layout/ProtectedRoute';

import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { SafetyIntelligencePage } from './pages/SafetyIntelligencePage';
import { DashboardPage } from './pages/DashboardPage';
import { ReportListPage } from './pages/ReportListPage';
import { ReportNewPage } from './pages/ReportNewPage';
import { ReportDetailPage } from './pages/ReportDetailPage';
import { AdminUsersPage } from './pages/AdminUsersPage';
import { AdminAuditLogsPage } from './pages/AdminAuditLogsPage';
import { MyActionsPage } from './pages/MyActionsPage';
import { AssignedActionsPage } from './pages/AssignedActionsPage';
import { ActionDetailPage } from './pages/ActionDetailPage';
import { HseActionCenterPage } from './pages/HseActionCenterPage';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          {/* Protected Application Shell */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/analytics" element={<SafetyIntelligencePage />} />
            <Route path="/action-center" element={<HseActionCenterPage />} />
            <Route path="/reports" element={<ReportListPage />} />
            <Route path="/reports/new" element={<ReportNewPage />} />
            <Route path="/reports/:id" element={<ReportDetailPage />} />

            {/* Action Management Routes */}
            <Route path="/actions/my" element={<MyActionsPage />} />
            <Route path="/actions/assigned" element={<AssignedActionsPage />} />
            <Route path="/actions/:id" element={<ActionDetailPage />} />

            {/* Admin Restricted Routes */}
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute allowedRoles={['ADMIN']}>
                  <AdminUsersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/audit-logs"
              element={
                <ProtectedRoute allowedRoles={['ADMIN']}>
                  <AdminAuditLogsPage />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* Fallback Redirect */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
