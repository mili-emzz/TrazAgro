import React from 'react';
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import { getDefaultRouteForRole, useAuth } from './context/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { RoleGuard } from './components/layout/RoleGuard';
import { LoginPage } from './pages/auth/LoginPage';
import { ProductorPage } from './pages/productor/ProductorPage';
import { RecepcionCedisPage } from './pages/recepcion/RecepcionCedisPage';
import { LaboratorioPage } from './pages/laboratorio/LaboratorioPage';
import { QaRecallPage } from './pages/qa/QaRecallPage';
import { GerenciaPage } from './pages/qa/GerenciaPage';
import { NotFoundPage } from './pages/NotFoundPage';

const RootRedirect: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }
  return <Navigate to={getDefaultRouteForRole(user.role)} replace />;
};

export const App: React.FC = () => {
  return (
    <HashRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/productor"
            element={
              <RoleGuard allowedRoles={['Productor', 'QA']}>
                <ProductorPage />
              </RoleGuard>
            }
          />

          <Route
            path="/cedis"
            element={
              <RoleGuard allowedRoles={['Recepcion', 'QA']}>
                <RecepcionCedisPage />
              </RoleGuard>
            }
          />

          <Route
            path="/laboratorio"
            element={
              <RoleGuard allowedRoles={['Laboratorio', 'QA']}>
                <LaboratorioPage />
              </RoleGuard>
            }
          />

          <Route
            path="/qa/recall"
            element={
              <RoleGuard allowedRoles={['QA']}>
                <QaRecallPage />
              </RoleGuard>
            }
          />

          <Route
            path="/qa/gerencia"
            element={
              <RoleGuard allowedRoles={['QA']}>
                <GerenciaPage />
              </RoleGuard>
            }
          />

          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </HashRouter>
  );
};
