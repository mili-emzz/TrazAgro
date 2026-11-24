import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, KeyRound, Lock, ShieldCheck, Sprout } from 'lucide-react';
import {
  DEMO_ACCOUNTS,
  type DemoAccountPreset,
  getDefaultRouteForRole,
  useAuth,
} from '../../context/AuthContext';
import { ApiError } from '../../api/client';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('qa_admin');
  const [password, setPassword] = useState('TrazaQA2026!');
  const [targetOverride, setTargetOverride] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);
    try {
      const loggedUser = await login({ username, password });
      const destination = targetOverride ?? getDefaultRouteForRole(loggedUser.role);
      navigate(destination, { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg('No se pudo conectar con el servidor FastAPI en /api/v1/auth/login.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDemo = async (preset: DemoAccountPreset) => {
    setUsername(preset.username);
    setPassword(preset.password);
    setTargetOverride(preset.targetPath);
    setErrorMsg(null);
    setLoading(true);
    try {
      await login({ username: preset.username, password: preset.password });
      navigate(preset.targetPath, { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg('Verifica que el backend FastAPI esté corriendo en el puerto 8000.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="login-box">
        <div className="card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <span className="brand-mark">
              <Sprout size={20} />
            </span>
            <div>
              <p className="eyebrow" style={{ margin: 0 }}>
                Acceso Operativo RBAC
              </p>
              <h1 style={{ fontSize: 21 }}>Iniciar sesión en TrazaAgro</h1>
            </div>
          </div>

          <p className="lead" style={{ fontSize: 13.5, marginBottom: 18 }}>
            Autenticación centralizada con token <strong>JWT HS256</strong> (
            <span className="op">POST /api/v1/auth/login</span>). El sistema asigna tus permisos y
            alcance de productor (<span className="rn">RN-04</span>,{' '}
            <span className="rn">RN-11</span>).
          </p>

          {errorMsg && (
            <div className="alert alert-bad" role="alert" style={{ marginBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: 14 }}>Error de autenticación</h2>
                <p>{errorMsg}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="login-user">Usuario operativo</label>
              <input
                id="login-user"
                className="input mono"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setTargetOverride(null);
                }}
                required
                autoComplete="username"
              />
            </div>

            <div className="field">
              <label htmlFor="login-pass">Contraseña</label>
              <input
                id="login-pass"
                type="password"
                className="input mono"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setTargetOverride(null);
                }}
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={loading}
              style={{ marginTop: 8 }}
            >
              <KeyRound size={17} />
              {loading ? 'Autenticando con JWT...' : 'Entrar al sistema'}
            </button>
          </form>

          <p className="lock" style={{ marginTop: 16 }}>
            <Lock size={14} />
            <span>
              Sin auto-registro público: las cuentas son aprovisionadas por seguridad alimentaria
              para impedir suplantación de rol QA.
            </span>
          </p>
        </div>

        <div className="card" style={{ padding: 24 }}>
          <div className="card-head">
            <div className="left">
              <h2>Acceso rápido por actor (Cuentas Semilla)</h2>
              <span className="badge s-ok">
                <ShieldCheck size={13} /> 5 Vistas del MVP
              </span>
            </div>
          </div>
          <p className="lead" style={{ fontSize: 13, marginBottom: 14 }}>
            Haz clic en cualquiera de los perfiles configurados en{' '}
            <span className="mono">AuthService</span> para iniciar sesión instantáneamente con su
            JWT real:
          </p>

          <div className="stack" style={{ gap: 10 }}>
            {DEMO_ACCOUNTS.map((preset) => (
              <button
                key={`${preset.username}-${preset.targetPath}`}
                type="button"
                className="demo-card"
                disabled={loading}
                onClick={() => handleSelectDemo(preset)}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--ink)' }}>
                    {preset.label}
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>{preset.subtitle}</div>
                  <div className="mono" style={{ fontSize: 11.5, color: 'var(--secondary)', marginTop: 2 }}>
                    usuario: {preset.username} · rol JWT: {preset.role}
                  </div>
                </div>
                <ArrowRight size={16} color="var(--primary)" />
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
