import React, { createContext, useContext, useEffect, useState } from 'react';
import { AUTH_STORAGE_KEY } from '../api/client';
import { loginApi } from '../api/auth';
import type { AuthUser, LoginRequest, UserRole } from '../types/api';

export interface DemoAccountPreset {
  label: string;
  subtitle: string;
  username: string;
  password: string;
  role: UserRole;
  targetPath: string;
}

export const DEMO_ACCOUNTS: DemoAccountPreset[] = [
  {
    label: 'Productor Michoacán (P014)',
    subtitle: 'Aguacateros Unidos de Michoacán',
    username: 'productor_michoacan',
    password: 'TrazaProd1!',
    role: 'Productor',
    targetPath: '/productor',
  },
  {
    label: 'Productor Tancítaro (P018)',
    subtitle: 'Huertas del Tancítaro',
    username: 'productor_tancitaro',
    password: 'TrazaProd2!',
    role: 'Productor',
    targetPath: '/productor',
  },
  {
    label: 'Recepción y Almacén CEDIS',
    subtitle: 'Carlos Herrera · Recepción y despacho',
    username: 'recepcion_cedis',
    password: 'TrazaRec2026!',
    role: 'Recepcion',
    targetPath: '/cedis',
  },
  {
    label: 'Laboratorio Externo',
    subtitle: 'Q.F.B. Sofía Ríos · Lab AgroBio',
    username: 'lab_agrobio',
    password: 'TrazaLab2026!',
    role: 'Laboratorio',
    targetPath: '/laboratorio',
  },
  {
    label: 'QA · Consola Recall',
    subtitle: 'Ing. Valeria Mendoza · Calidad y retiros',
    username: 'qa_admin',
    password: 'TrazaQA2026!',
    role: 'QA',
    targetPath: '/qa/recall',
  },
  {
    label: 'Gerencia · Auditoría e Incidentes',
    subtitle: 'Supervisión Ejecutiva · Auditoría e incidentes',
    username: 'qa_admin',
    password: 'TrazaQA2026!',
    role: 'QA',
    targetPath: '/qa/gerencia',
  },
];

export function getDefaultRouteForRole(role: UserRole): string {
  switch (role) {
    case 'Productor':
      return '/productor';
    case 'Recepcion':
      return '/cedis';
    case 'Laboratorio':
      return '/laboratorio';
    case 'QA':
      return '/qa/recall';
  }
}

interface StoredSession {
  token: string;
  user: AuthUser;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readInitialSession(): StoredSession | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredSession;
    if (parsed.token && parsed.user) {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<StoredSession | null>(() => readInitialSession());

  useEffect(() => {
    const handleUnauthorized = () => {
      setSession(null);
    };
    window.addEventListener('trazaagro:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('trazaagro:unauthorized', handleUnauthorized);
  }, []);

  const login = async (credentials: LoginRequest): Promise<AuthUser> => {
    const resp = await loginApi(credentials);
    const nextSession: StoredSession = {
      token: resp.access_token,
      user: resp.user,
    };
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextSession));
    setSession(nextSession);
    return resp.user;
  };

  const logout = () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    setSession(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user: session?.user ?? null,
        token: session?.token ?? null,
        isAuthenticated: Boolean(session?.token && session?.user),
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth debe utilizarse dentro de un AuthProvider.');
  }
  return ctx;
}
