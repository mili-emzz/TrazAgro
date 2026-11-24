export type UserRole = 'Productor' | 'Recepcion' | 'Laboratorio' | 'QA';

export interface AuthUser {
  sub: string;
  username: string;
  nombre: string;
  role: UserRole;
  productor_id: number | null;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export interface HealthResponse {
  status: string;
  engines: {
    postgresql: string;
    mongodb: string;
    neo4j: string;
  };
}

export type EstadoLote =
  | 'Cosechado'
  | 'Recibido'
  | 'En revision'
  | 'Liberado'
  | 'Bloqueado'
  | 'Retirado';

export interface LoteItem {
  lote_id: number;
  codigo_lote: string;
  parcela_id: number;
  producto: string;
  fecha_cosecha: string;
  cuadrilla_cosecha: string;
  peso_inicial_kg: number;
  saldo_kg: number;
  estado: EstadoLote;
  fecha_actualizacion: string;
  codigo_senasica?: string;
  nombre_huerta?: string;
  municipio?: string;
  productor_id?: number;
  productor_nombre?: string;
  sincronizacion?: Record<string, string>;
}

export interface LoteCreateRequest {
  codigo_lote: string;
  parcela_id: number;
  producto: string;
  fecha_cosecha: string;
  cuadrilla_cosecha: string;
  peso_inicial_kg: number;
}

export interface LoteLiberarRequest {
  motivo: string;
}

export interface LoteLiberarResponse {
  codigo_lote: string;
  estado_previo: string;
  estado_actual: string;
  saldo_kg: number;
  folio_evento: string;
  sincronizacion: Record<string, string>;
}

export interface EvaluacionSensorial {
  color_epidermis: string;
  firmeza_pulpa_lb?: number | null;
  materia_seca_estimada_pct?: number | null;
  calibre_predominante?: string | null;
  pedunculo_presente_pct?: number | null;
  olor_extrano: boolean;
}

export interface LecturaTemperaturaCaja {
  zona_contenedor: string;
  tarima?: string | null;
  temperatura_c: number;
}

export interface ActaRecepcionDoc {
  folio_recepcion: string;
  codigo_lote: string;
  fecha_hora_inspeccion?: string;
  inspector?: {
    usuario_id?: string;
    nombre?: string;
    turno?: string;
  };
  evaluacion_sensorial?: EvaluacionSensorial;
  monitoreo_temperatura_caja?: LecturaTemperaturaCaja[];
  observaciones_inspector?: string;
}

export interface DeterminacionItem {
  molecula?: string | null;
  parametro?: string | null;
  metodo_ensayo?: string | null;
  unidad?: string | null;
  resultado_mg_kg?: number | null;
  limite_maximo_mg_kg?: number | null;
  resultado_cualitativo?: string | null;
  criterio_normativo?: string | null;
  conforme: boolean;
}

export interface MuestraAnalisisItem {
  identificador_muestra: string;
  parte_analizada?: string | null;
  peso_gramos?: number | null;
  determinaciones: DeterminacionItem[];
}

export interface AnalisisDocumento {
  folio_analisis: string;
  codigo_lote: string;
  tipo_estudio: 'Residuos de Plaguicidas' | 'Microbiologico' | 'Materia Seca' | string;
  version: number;
  es_vigente: boolean;
  folio_reemplazado?: string | null;
  motivo_enmienda?: string | null;
  fecha_muestreo?: string;
  fecha_emision?: string;
  dictamen_general: 'Conforme' | 'No Conforme' | string;
  laboratorio?: {
    nombre: string;
    acreditacion_iso: string;
    contacto_correo?: string | null;
  };
  muestras?: MuestraAnalisisItem[];
}

export interface AnalisisCreateRequest {
  folio_analisis: string;
  codigo_lote: string;
  tipo_estudio: 'Residuos de Plaguicidas' | 'Microbiologico' | 'Materia Seca';
  fecha_muestreo: string;
  motivo_enmienda?: string | null;
  dictamen_general: 'Conforme' | 'No Conforme';
  laboratorio: {
    nombre: string;
    acreditacion_iso: string;
    contacto_correo?: string | null;
  };
  muestras: MuestraAnalisisItem[];
}

export interface AnalisisResponse {
  folio_analisis: string;
  codigo_lote: string;
  tipo_estudio: string;
  version: number;
  es_vigente: boolean;
  folio_reemplazado?: string | null;
  dictamen_general: string;
  sincronizacion: Record<string, string>;
}

export interface AnalisisListResponse {
  codigo_lote: string;
  total: number;
  analisis: AnalisisDocumento[];
}

export interface RecepcionCreateRequest {
  folio_recepcion: string;
  codigo_lote: string;
  placas_vehiculo: string;
  nombre_chofer: string;
  codigo_cuarto_frio: string;
  peso_recibido_kg: number;
  temperatura_llegada_c: number;
  turno: string;
  evaluacion_sensorial: EvaluacionSensorial;
  monitoreo_temperatura_caja: LecturaTemperaturaCaja[];
  observaciones_inspector?: string | null;
}

export interface RecepcionResponse {
  recepcion_id: number;
  folio_recepcion: string;
  codigo_lote: string;
  fecha_llegada: string;
  placas_vehiculo: string;
  codigo_cuarto_frio: string;
  peso_recibido_kg: number;
  temperatura_llegada_c: number;
  dictamen_recepcion: string;
  estado_lote_resultante: string;
  alerta_cadena_frio: boolean;
  sincronizacion: Record<string, string>;
}

export interface EnvioDetalleItem {
  codigo_lote: string;
  cantidad_kg: number;
}

export interface EnvioCreateRequest {
  codigo_envio: string;
  tienda_id: number;
  placas_vehiculo: string;
  nombre_chofer: string;
  detalles: EnvioDetalleItem[];
}

export interface EnvioCreateResponse {
  codigo_envio: string;
  estado_envio: string;
  tienda_id: number;
  total_kg: number;
  saldos_actualizados: {
    codigo_lote: string;
    saldo_kg_restante: number;
  }[];
  sincronizacion: Record<string, string>;
}

export interface TiendaAfectadaItem {
  codigo_sucursal?: string;
  tienda?: string;
  nombre_comercial?: string;
  ciudad?: string;
  direccion?: string;
  codigo_envio: string;
  placas_vehiculo?: string;
  vehiculo_reparto?: string;
  kg_entregados?: number;
  cantidad_kg?: number;
  estado_envio?: string;
}

export interface LoteHermanoItem {
  lote_hermano?: string;
  codigo_lote?: string;
  estado_actual?: string;
  estado?: string;
  recurso_compartido?: string;
  tipo_recurso?: string;
  identificador_recurso?: string;
  productor?: string;
}

export interface ExpedienteIncidenteDoc {
  folio_incidente: string;
  codigo_lote_origen?: string;
  codigo_lote?: string;
  tipo_incidente?: string;
  severidad?: string;
  estado_expediente: 'Abierto' | 'En Investigacion' | 'Cerrado' | string;
  motivo_apertura?: string;
  causa_raiz?: string | null;
  acciones_correctivas?: string[];
  firmas_cierre?: {
    responsable_qa?: string;
    aprobacion_gerencia?: string;
    fecha_firma?: string;
  } | null;
}

export interface Expediente360Response {
  lote: LoteItem;
  recepcion_sql: {
    recepcion_id: number;
    folio_recepcion: string;
    fecha_llegada: string;
    placas_vehiculo: string;
    codigo_cuarto_frio: string;
    peso_recibido_kg: number;
    temperatura_llegada_c: number;
    dictamen_recepcion: string;
  } | null;
  acta_recepcion: ActaRecepcionDoc | null;
  analisis_laboratorio: AnalisisDocumento[];
  incidentes_bitacora: {
    incidente_id: number;
    folio_incidente: string;
    usuario_responsable: string;
    motivo: string;
    estado_previo: string;
    nuevo_estado: string;
    fecha_evento: string;
  }[];
  expedientes_incidentes: ExpedienteIncidenteDoc[];
  red_trazabilidad: {
    origen?: {
      productor_nombre?: string;
      productor_rfc?: string;
      codigo_senasica?: string;
      nombre_huerta?: string;
      municipio?: string;
    } | null;
    transporte_entrada?: {
      placas?: string;
      temperatura_c?: number;
    } | null;
    cuarto_frio?: {
      codigo?: string;
    } | null;
    destinos?: TiendaAfectadaItem[];
    lotes_hermanos?: LoteHermanoItem[];
  } | null;
  advertencias: string[];
}

export interface RecallCreateRequest {
  folio_incidente?: string;
  codigo_lote_origen: string;
  motivo: string;
  incluir_lotes_hermanos: boolean;
  ventana_dias_contaminacion: number;
}

export interface RecallResponse {
  folio_incidente: string;
  lote_origen: Record<string, unknown>;
  evidencia_documental: Record<string, unknown> | null;
  lotes_hermanos_bloqueados: LoteHermanoItem[];
  tiendas_afectadas: TiendaAfectadaItem[];
  sincronizacion: Record<string, string>;
}

export interface IncidenteCerrarRequest {
  causa_raiz: string;
  acciones_correctivas: string[];
  responsable_qa: string;
  aprobacion_gerencia: string;
}

export interface IncidenteCerrarResponse {
  folio_incidente: string;
  estado_expediente: string;
  fecha_cierre: string;
  causa_raiz: string;
  acciones_correctivas: string[];
  firmas_cierre: Record<string, string>;
  sincronizacion: Record<string, string>;
}

export interface TrazabilidadAdelanteResponse {
  codigo_lote: string;
  total_envios: number;
  total_kg_despachados: number;
  tiendas_afectadas: TiendaAfectadaItem[];
}

export interface TrazabilidadAtrasLateralResponse {
  codigo_lote: string;
  ventana_dias: number;
  origen: {
    productor_nombre?: string;
    productor_rfc?: string;
    codigo_senasica?: string;
    nombre_huerta?: string;
    municipio?: string;
  } | null;
  lotes_hermanos: LoteHermanoItem[];
}

export interface ReconciliacionEjecucionResponse {
  total_pendientes: number;
  procesados: number;
  fallidos: number;
  detalle: Record<string, unknown>[];
}
