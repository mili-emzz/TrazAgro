const AUTH_STORAGE_KEY = 'trazaagro_auth_session';

export class ApiError extends Error {
  status: number;
  errorCode: string;
  details?: unknown;

  constructor(status: number, errorCode: string, message: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errorCode = errorCode;
    this.details = details;
  }
}

export function getStoredToken(): string | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { token?: string };
    return parsed.token ?? null;
  } catch {
    return null;
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const defaultBase =
    typeof window !== 'undefined' && window.location.protocol === 'file:'
      ? 'http://127.0.0.1:8000'
      : '';
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? defaultBase;
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && !path.includes('/auth/login')) {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    window.dispatchEvent(new Event('trazaagro:unauthorized'));
  }

  const contentType = response.headers.get('content-type') ?? '';
  const isJson = contentType.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    const errorCode =
      (data && typeof data === 'object' && 'error' in data && String(data.error)) ||
      `HTTP_${response.status}`;

    let message = 'Ocurrió un error al comunicarse con la API de TrazaAgro.';
    if (data && typeof data === 'object') {
      if ('mensaje' in data && typeof data.mensaje === 'string') {
        message = data.mensaje;
      } else if ('detail' in data) {
        if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          message = data.detail
            .map((item: { loc?: unknown[]; msg?: string }) => {
              const field = Array.isArray(item.loc) ? item.loc.slice(1).join('.') : 'campo';
              return `${field}: ${item.msg ?? 'valor inválido'}`;
            })
            .join(' · ');
        }
      }
    }

    throw new ApiError(response.status, errorCode, message, data);
  }

  return data as T;
}

export { AUTH_STORAGE_KEY };
