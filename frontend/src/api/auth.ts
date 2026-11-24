import { apiRequest } from './client';
import type { HealthResponse, LoginRequest, LoginResponse } from '../types/api';

export function loginApi(payload: LoginRequest): Promise<LoginResponse> {
  return apiRequest<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getHealthApi(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>('/api/v1/health');
}
