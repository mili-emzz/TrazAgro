import { apiRequest } from './client';
import type {
  EstadoLote,
  Expediente360Response,
  LoteCreateRequest,
  LoteItem,
  LoteLiberarRequest,
  LoteLiberarResponse,
} from '../types/api';

export function listarLotesApi(estado?: EstadoLote): Promise<LoteItem[]> {
  const qs = estado ? `?estado=${encodeURIComponent(estado)}` : '';
  return apiRequest<LoteItem[]>(`/api/v1/lotes${qs}`);
}

export function crearLoteApi(payload: LoteCreateRequest): Promise<LoteItem> {
  return apiRequest<LoteItem>('/api/v1/lotes', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function obtenerExpediente360Api(codigoLote: string): Promise<Expediente360Response> {
  return apiRequest<Expediente360Response>(`/api/v1/lotes/${encodeURIComponent(codigoLote)}`);
}

export function liberarLoteApi(
  codigoLote: string,
  payload: LoteLiberarRequest
): Promise<LoteLiberarResponse> {
  return apiRequest<LoteLiberarResponse>(
    `/api/v1/lotes/${encodeURIComponent(codigoLote)}/liberar`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }
  );
}
