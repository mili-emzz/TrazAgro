import React from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { getDefaultRouteForRole, useAuth } from '../../context/AuthContext';
import type { UserRole } from '../../types/api';

interface RoleGuardProps {
  allowedRoles: UserRole[];
  children: React.ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ allowedRoles, children }) => {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    const safeRoute = getDefaultRouteForRole(user.role);
    return (
      <div className="card" style={{ maxWidth: 580, margin: '40px auto', textAlign: 'center' }}>
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            background: 'var(--danger-tint)',
            color: 'var(--danger)',
            display: 'grid',
            placeItems: 'center',
            margin: '0 auto 12px',
          }}
        >
          <ShieldAlert size={24} />
        </div>
        <h2>Acceso restringido</h2>
        <p className="lead" style={{ marginTop: 8 }}>
          Tu sesión actual tiene el rol <strong>{user.role}</strong> ({user.nombre}). Esta vista
          requiere permisos de <strong>{allowedRoles.join(' o ')}</strong>.
        </p>
        <div style={{ marginTop: 18 }}>
          <Link to={safeRoute} className="btn btn-primary">
            Ir a mi panel autorizado
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
