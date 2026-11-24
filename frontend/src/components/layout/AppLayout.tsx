import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  BarChart3,
  FlaskConical,
  LogOut,
  ShieldCheck,
  Sprout,
  Tractor,
  UserCheck,
  Warehouse,
} from 'lucide-react';
import { getHealthApi } from '../../api/auth';
import { DEMO_ACCOUNTS, useAuth } from '../../context/AuthContext';

export const AppLayout: React.FC = () => {
  const { user, isAuthenticated, login, logout } = useAuth();
  const navigate = useNavigate();
  const [switching, setSwitching] = useState(false);

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: getHealthApi,
    retry: 1,
    refetchInterval: 30000,
  });

  const handleQuickDemoSwitch = async (presetIndex: string) => {
    const idx = Number(presetIndex);
    const preset = DEMO_ACCOUNTS[idx];
    if (!preset) return;
    try {
      setSwitching(true);
      await login({ username: preset.username, password: preset.password });
      navigate(preset.targetPath);
    } finally {
      setSwitching(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      <a href="#main" className="skip">
        Saltar al contenido
      </a>

      <header className="topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
          <NavLink to="/" className="brand">
            <span className="brand-mark" aria-hidden="true">
              <Sprout size={19} />
            </span>
            <span>
              TrazaAgro
              <small>Trazabilidad políglota · PG + Mongo + Neo4j</small>
            </span>
          </NavLink>

          {health && (
            <span
              className={`badge ${health.status === 'ok' ? 's-ok' : 's-warn'}`}
              title={`PostgreSQL: ${health.engines?.postgresql} | MongoDB: ${health.engines?.mongodb} | Neo4j: ${health.engines?.neo4j}`}
            >
              <Activity size={13} />
              3 Motores: {health.status === 'ok' ? 'Online' : 'Degradado'}
            </span>
          )}
        </div>

        {isAuthenticated && user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <nav className="tabs" aria-label="Vistas del rol activo">
              {user.role === 'Productor' && (
                <NavLink
                  to="/productor"
                  className={({ isActive }) => `tab ${isActive ? 'active' : ''}`}
                >
                  <Tractor size={16} />
                  Productor ({user.productor_id === 1 ? 'P014' : `ID ${user.productor_id}`})
                </NavLink>
              )}

              {user.role === 'Recepcion' && (
                <NavLink
                  to="/cedis"
                  className={({ isActive }) => `tab ${isActive ? 'active' : ''}`}
                >
                  <Warehouse size={16} />
                  Recepción y Despacho CEDIS
                </NavLink>
              )}

              {user.role === 'Laboratorio' && (
                <NavLink
                  to="/laboratorio"
                  className={({ isActive }) => `tab ${isActive ? 'active' : ''}`}
                >
                  <FlaskConical size={16} />
                  Laboratorio Externo
                </NavLink>
              )}

              {user.role === 'QA' && (
                <>
                  <NavLink
                    to="/qa/recall"
                    className={({ isActive }) => `tab ${isActive ? 'active' : ''}`}
                  >
                    <ShieldCheck size={16} />
                    QA · Consola Recall
                  </NavLink>
                  <NavLink
                    to="/qa/gerencia"
                    className={({ isActive }) => `tab ${isActive ? 'active' : ''}`}
                  >
                    <BarChart3 size={16} />
                    Gerencia · Auditoría
                  </NavLink>
                </>
              )}
            </nav>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <label htmlFor="demo-role-switcher" className="sr-only">
                Cambiar cuenta operativa demo
              </label>
              <select
                id="demo-role-switcher"
                className="input"
                style={{
                  minHeight: 36,
                  padding: '4px 10px',
                  fontSize: 12.5,
                  width: 'auto',
                  background: 'var(--bg)',
                }}
                disabled={switching}
                value=""
                onChange={(e) => handleQuickDemoSwitch(e.target.value)}
              >
                <option value="" disabled>
                  ⚡ Cambiar actor demo ({user.role})
                </option>
                {DEMO_ACCOUNTS.map((acc, idx) => (
                  <option key={`${acc.username}-${acc.targetPath}`} value={idx}>
                    {acc.label}
                  </option>
                ))}
              </select>

              <span className="badge s-info" title={`Usuario JWT: ${user.username}`}>
                <UserCheck size={13} />
                {user.nombre}
              </span>

              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={handleLogout}
                title="Cerrar sesión"
              >
                <LogOut size={15} />
                Salir
              </button>
            </div>
          </div>
        )}
      </header>

      <main id="main">
        <Outlet />
      </main>
    </>
  );
};
