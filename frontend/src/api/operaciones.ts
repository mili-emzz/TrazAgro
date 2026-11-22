import { apiRequest } from './client';
import type {
  AnalisisCreateRequest,
  AnalisisListResponse,
  AnalisisResponse,
  EnvioCreateRequest,
  EnvioCreateResponse,
  IncidenteCerrarRequest,
  IncidenteCerrarResponse,
  RecallCreateRequest,
  RecallResponse,
  RecepcionCreateRequest,
  RecepcionResponse,
  ReconciliacionEjecucionResponse,
  TrazabilidadAdelanteResponse,
  TrazabilidadAtrasLateralResponse,
} from '../types/api';

export function registrarRecepcionApi(payload: RecepcionCreateRequest): Promise<RecepcionResponse> {
  return apiRequest<RecepcionResponse>('/api/v1/recepciones', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function registrarEnvioApi(payload: EnvioCreateRequest): Promise<EnvioCreateResponse> {
  return apiRequest<EnvioCreateResponse>('/api/v1/envios', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function consultarAnalisisApi(
  codigoLote: string,
  opts?: { soloVigentes?: boolean; soloNoConformes?: boolean }
): Promise<AnalisisListResponse> {
  const params = new URLSearchParams();
  if (opts?.soloVigentes) params.set('solo_vigentes', 'true');
  if (opts?.soloNoConformes) params.set('solo_no_conformes', 'true');
  const qs = params.toString() ? `?${params.toString()}` : '';
  return apiRequest<AnalisisListResponse>(
    `/api/v1/analisis/${encodeURIComponent(codigoLote)}${qs}`
  );
}

export function registrarAnalisisApi(payload: AnalisisCreateRequest): Promise<AnalisisResponse> {
  return apiRequest<AnalisisResponse>('/api/v1/analisis', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function trazabilidadAdelanteApi(codigoLote: string): Promise<TrazabilidadAdelanteResponse> {
  return apiRequest<TrazabilidadAdelanteResponse>(
    `/api/v1/trazabilidad/${encodeURIComponent(codigoLote)}/adelante`
  );
}

export function trazabilidadAtrasLateralApi(
  codigoLote: string,
  ventanaDias = 1
): Promise<TrazabilidadAtrasLateralResponse> {
  return apiRequest<TrazabilidadAtrasLateralResponse>(
    `/api/v1/trazabilidad/${encodeURIComponent(codigoLote)}/atras-lateral?ventana_dias=${ventanaDias}`
  );
}

export function ejecutarRecallApi(payload: RecallCreateRequest): Promise<RecallResponse> {
  return apiRequest<RecallResponse>('/api/v1/incidentes/recall', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function cerrarIncidenteApi(
  folio: string,
  payload: IncidenteCerrarRequest
): Promise<IncidenteCerrarResponse> {
  return apiRequest<IncidenteCerrarResponse>(
    `/api/v1/incidentes/${encodeURIComponent(folio)}/cerrar`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }
  );
}

export function ejecutarReconciliacionApi(limit = 50): Promise<ReconciliacionEjecucionResponse> {
  return apiRequest<ReconciliacionEjecucionResponse>(
    `/api/v1/admin/reconciliacion/ejecutar?limit=${limit}`,
    {
      method: 'POST',
    }
  );
}
