import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  Info,
  Lock,
  OctagonAlert,
  RefreshCw,
  Search,
} from 'lucide-react';
import { liberarLoteApi, listarLotesApi, obtenerExpediente360Api } from '../../api/lotes';
import {
  ejecutarRecallApi,
  ejecutarReconciliacionApi,
  trazabilidadAdelanteApi,
  trazabilidadAtrasLateralApi,
} from '../../api/operaciones';
import { ApiError } from '../../api/client';
import { DictamenBadge, LoteStatusBadge, SyncBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';
import { TraceGraphVisualizer } from '../../components/visualizer/TraceGraphVisualizer';
import type { RecallCreateRequest } from '../../types/api';

export const QaRecallPage: React.FC = () => {
  const queryClient = useQueryClient();

  const [codigoLote, setCodigoLote] = useState('AGU-P014-260312-01');
  const [searchInput, setSearchInput] = useState('AGU-P014-260312-01');
  const [feedback, setFeedback] = useState<{ type: 'ok' | 'warn' | 'bad'; text: string } | null>(
    null
  );
  const [lastSync, setLastSync] = useState<Record<string, string> | null>(null);

  // Modal de confirmación de Recall (RN-04, RN-08)
  const [openRecallModal, setOpenRecallModal] = useState(false);
  const [recallLoteTarget, setRecallLoteTarget] = useState('AGU-P014-260312-01');
  const [recallMotivo, setRecallMotivo] = useState('');
  const [incluirHermanos, setIncluirHermanos] = useState(true);
  const [ventanaDias, setVentanaDias] = useState(1);

  // Modal de liberación de lote (RN-02, RN-04)
  const [liberarTarget, setLiberarTarget] = useState<string | null>(null);
  const [liberarMotivo, setLiberarMotivo] = useState('');

  const {
    data: lotes = [],
    isError: isLotesError,
    error: lotesError,
    refetch: refetchLotes,
  } = useQuery({
    queryKey: ['lotes'],
    queryFn: () => listarLotesApi(),
  });

  const {
    data: expediente,
    isLoading,
    isError: isExpedienteError,
    error: expedienteError,
    refetch: refetchExpediente,
  } = useQuery({
    queryKey: ['expediente-qa', codigoLote],
    queryFn: () => obtenerExpediente360Api(codigoLote),
    enabled: Boolean(codigoLote),
  });

  const { data: trazaAdelante } = useQuery({
    queryKey: ['traza-adelante', codigoLote],
    queryFn: () => trazabilidadAdelanteApi(codigoLote),
    enabled: Boolean(codigoLote),
  });

  const { data: trazaAtrasLat } = useQuery({
    queryKey: ['traza-atras-lat', codigoLote],
    queryFn: () => trazabilidadAtrasLateralApi(codigoLote, 1),
    enabled: Boolean(codigoLote),
  });

  const recallMutation = useMutation({
    mutationFn: (payload: RecallCreateRequest) => ejecutarRecallApi(payload),
    onSuccess: (res) => {
      setOpenRecallModal(false);
      setRecallMotivo('');
      setLastSync(res.sincronizacion ?? null);
      setCodigoLote(recallLoteTarget);
      setSearchInput(recallLoteTarget);
      const numHermanos = res.lotes_hermanos_bloqueados.length;
      const numTiendas = res.tiendas_afectadas.length;
      setFeedback({
        type: 'ok',
        text: `Protocolo de Recall ejecutado (${res.folio_incidente}): Lote ${recallLoteTarget} y ${numHermanos} lote(s) hermano(s) bloqueados, expediente abierto y ${numTiendas} tienda(s) identificada(s).`,
      });
      queryClient.invalidateQueries({ queryKey: ['lotes'] });
      queryClient.invalidateQueries({ queryKey: ['expediente-qa'] });
      queryClient.invalidateQueries({ queryKey: ['traza-adelante'] });
      queryClient.invalidateQueries({ queryKey: ['traza-atras-lat'] });
    },
    onError: (err) => {
      setFeedback({
        type: 'bad',
        text: err instanceof ApiError ? err.message : 'Error al ejecutar protocolo de recall.',
      });
    },
  });

  const liberarMutation = useMutation({
    mutationFn: ({ codigo, motivo }: { codigo: string; motivo: string }) =>
      liberarLoteApi(codigo, { motivo }),
    onSuccess: (res) => {
      setLiberarTarget(null);
      setLiberarMotivo('');
      setLastSync(res.sincronizacion ?? null);
      setFeedback({
        type: 'ok',
        text: `Lote ${res.codigo_lote} cambiado de '${res.estado_previo}' a '${res.estado_actual}' (${res.folio_evento}) tras validar certificados conformes.`,
      });
      queryClient.invalidateQueries({ queryKey: ['lotes'] });
      queryClient.invalidateQueries({ queryKey: ['expediente-qa'] });
    },
    onError: (err) => {
      setLiberarTarget(null);
      setFeedback({
        type: 'bad',
        text:
          err instanceof ApiError
            ? err.message
            : 'No se pudo liberar el lote (requiere análisis vigente Conforme).',
      });
    },
  });

  const reconciliacionMutation = useMutation({
    mutationFn: () => ejecutarReconciliacionApi(50),
    onSuccess: (res) => {
      setFeedback({
        type: 'ok',
        text: `Reconciliación completada: ${res.total_pendientes} pendientes encontrados, ${res.procesados} sincronizados, ${res.fallidos} fallidos.`,
      });
    },
    onError: (err) => {
      setFeedback({
        type: 'bad',
        text: err instanceof ApiError ? err.message : 'Error al ejecutar reconciliación.',
      });
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setCodigoLote(searchInput.trim().toUpperCase());
    }
  };

  const handleExportTiendasCsv = () => {
    const tiendas =
      trazaAdelante?.tiendas_afectadas ?? expediente?.red_trazabilidad?.destinos ?? [];
    const header = 'Sucursal,Ciudad,Envio,Vehiculo,Kg_Entregados\n';
    const rows = tiendas
      .map(
        (t) =>
          `"${t.tienda ?? t.nombre_comercial ?? ''}","${t.ciudad ?? ''}","${t.codigo_envio}","${
            t.placas_vehiculo ?? t.vehiculo_reparto ?? ''
          }",${t.kg_entregados ?? t.cantidad_kg ?? 0}`
      )
      .join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `recall-tiendas-${codigoLote}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const lote = expediente?.lote;
  const rec = expediente?.recepcion_sql;
  const despachadoKg = lote ? Math.max(0, Number(lote.peso_inicial_kg) - Number(lote.saldo_kg)) : 0;
  const destinos =
    trazaAdelante?.tiendas_afectadas ?? expediente?.red_trazabilidad?.destinos ?? [];
  const hermanos =
    trazaAtrasLat?.lotes_hermanos ?? expediente?.red_trazabilidad?.lotes_hermanos ?? [];
  const colaDictamen = lotes.filter(
    (l) => l.estado === 'En revision' || l.estado === 'Recibido' || l.estado === 'Cosechado'
  );

  const analisisNoConforme = expediente?.analisis_laboratorio.find(
    (an) => an.es_vigente && an.dictamen_general.toLowerCase().includes('no conforme')
  );
  const incidenteActivo = expediente?.expedientes_incidentes.find(
    (inc) => inc.estado_expediente !== 'Cerrado'
  );
  const isBloqueado = lote?.estado === 'Bloqueado' || lote?.estado === 'Retirado';
  const isEnRevision = lote?.estado === 'En revision';
  const syncData =
    lote?.sincronizacion ??
    lastSync ??
    (expediente?.advertencias && expediente.advertencias.length > 0
      ? { sincronizacion: 'pendiente' }
      : null);

  return (
    <section aria-label="Consola de Recall y Expediente 360 de QA">
      {feedback && (
        <div
          className={`alert ${
            feedback.type === 'ok'
              ? 'alert-ok'
              : feedback.type === 'warn'
              ? 'alert-warn'
              : 'alert-bad'
          }`}
          role="alert"
          style={{ marginBottom: 16 }}
        >
          <div>
            <h2>Operación de Inocuidad QA</h2>
            <p>{feedback.text}</p>
          </div>
        </div>
      )}

      {(isLotesError || isExpedienteError) && (
        <div className="alert alert-bad" role="alert" style={{ marginBottom: 16 }}>
          <OctagonAlert size={20} />
          <div>
            <h2>No se pudo cargar la información del expediente</h2>
            <p>
              {(expedienteError instanceof ApiError && expedienteError.message) ||
                (lotesError instanceof ApiError && lotesError.message) ||
                'Verifica la conexión con la API e intenta nuevamente.'}
            </p>
          </div>
          <div className="actions">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                refetchLotes();
                refetchExpediente();
              }}
            >
              <RefreshCw size={14} /> Reintentar
            </button>
          </div>
        </div>
      )}

      {lote && (isBloqueado || Boolean(analisisNoConforme)) && (
        <div className="alert alert-bad" role="alert" style={{ marginBottom: 20 }}>
          <OctagonAlert size={22} />
          <div>
            <h2>
              {isBloqueado ? 'Lote bloqueado bajo alerta sanitaria' : 'Dictamen adverso detectado'} ·{' '}
              <span className="mono">{codigoLote}</span>
            </h2>
            <p>
              {incidenteActivo?.motivo_apertura ??
                (analisisNoConforme
                  ? `Análisis ${analisisNoConforme.folio_analisis} (${analisisNoConforme.tipo_estudio}): ${analisisNoConforme.dictamen_general}.`
                  : 'Lote inmovilizado por protocolo de inocuidad.')}{' '}
              {despachadoKg.toLocaleString()} kg despachados a {destinos.length} tienda(s) ·{' '}
              {hermanos.length} lote(s) hermano(s) en recursos compartidos.
            </p>
          </div>
          <div className="actions">
            <button
              type="button"
              className="btn btn-danger"
              onClick={() => {
                setRecallLoteTarget(codigoLote);
                setRecallMotivo('');
                setOpenRecallModal(true);
              }}
            >
              <Lock size={16} /> Ejecutar recall y bloquear lotes
            </button>
          </div>
        </div>
      )}

      {lote && !isBloqueado && !analisisNoConforme && isEnRevision && (
        <div className="alert alert-warn" role="status" style={{ marginBottom: 20 }}>
          <AlertTriangle size={22} />
          <div>
            <h2>
              Lote en revisión sanitaria · <span className="mono">{codigoLote}</span>
            </h2>
            <p>
              Saldo retenido de {Number(lote.saldo_kg).toLocaleString()} kg en espera de dictamen
              técnico de QA.
            </p>
          </div>
          <div className="actions">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setLiberarMotivo('');
                setLiberarTarget(codigoLote);
              }}
            >
              Liberar lote
            </button>
            <button
              type="button"
              className="btn btn-danger btn-sm"
              onClick={() => {
                setRecallLoteTarget(codigoLote);
                setRecallMotivo('');
                setOpenRecallModal(true);
              }}
            >
              <Lock size={14} /> Iniciar recall
            </button>
          </div>
        </div>
      )}

      {lote && !isBloqueado && !analisisNoConforme && !isEnRevision && (
        <div className="alert alert-ok" role="status" style={{ marginBottom: 20 }}>
          <CheckCircle2 size={20} />
          <div>
            <h2>
              Sin alertas sanitarias activas · <span className="mono">{codigoLote}</span>
            </h2>
            <p>
              Estado actual: <strong>{lote.estado}</strong> · {despachadoKg.toLocaleString()} kg
              despachados a {destinos.length} tienda(s).
            </p>
          </div>
          <div className="actions">
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              style={{ color: 'var(--danger)' }}
              onClick={() => {
                setRecallLoteTarget(codigoLote);
                setRecallMotivo('');
                setOpenRecallModal(true);
              }}
            >
              <Lock size={14} /> Iniciar recall preventivo
            </button>
          </div>
        </div>
      )}

      <div className="page-head">
        <div>
          <p className="eyebrow">Expediente 360° Consolidado</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h1 className="mono" style={{ fontSize: 22 }}>
              {codigoLote}
            </h1>
            <SyncBadge sincronizacion={syncData} />
          </div>
        </div>

        <form
          className="search"
          role="search"
          onSubmit={handleSearch}
          style={{ width: 'min(100%, 420px)' }}
        >
          <label htmlFor="q-lote" className="sr-only">
            Seleccionar o buscar código de lote
          </label>
          <select
            id="q-lote"
            className="input mono"
            value={searchInput}
            onChange={(e) => {
              setSearchInput(e.target.value);
              setCodigoLote(e.target.value);
            }}
          >
            {lotes.map((l) => (
              <option key={l.codigo_lote} value={l.codigo_lote}>
                {l.codigo_lote} ({l.estado})
              </option>
            ))}
          </select>
          <button type="submit" className="btn btn-primary" aria-label="Cargar expediente">
            <Search size={17} />
          </button>
        </form>
      </div>

      {isLoading || !expediente || !lote ? (
        <div className="card">
          <p className="lead">Cargando Expediente 360° del lote...</p>
        </div>
      ) : (
        <>
          <dl className="summary">
            <div>
              <dt>Estado Maestro</dt>
              <dd>
                <LoteStatusBadge estado={lote.estado} />
              </dd>
            </div>
            <div>
              <dt>Peso inicial</dt>
              <dd>{Number(lote.peso_inicial_kg).toLocaleString()} kg</dd>
            </div>
            <div>
              <dt>Saldo en CEDIS</dt>
              <dd>{Number(lote.saldo_kg).toLocaleString()} kg</dd>
            </div>
            <div>
              <dt>Despachado</dt>
              <dd>{despachadoKg.toLocaleString()} kg</dd>
            </div>
            <div>
              <dt>Recepción</dt>
              <dd className="mono" style={{ fontWeight: 500 }}>
                {rec ? `${rec.folio_recepcion} · ${rec.temperatura_llegada_c} °C` : 'En tránsito'}
              </dd>
            </div>
          </dl>

          <TraceGraphVisualizer expediente={expediente} />

          <div className="trace">
            <div className="card fwd">
              <div className="card-head">
                <h2>1 · Hacia adelante (Tiendas)</h2>
              </div>
              {destinos.length > 0 ? (
                <ul className="list">
                  {destinos.map((d, i) => (
                    <li key={`${d.codigo_envio}-${i}`}>
                      <div>
                        <div className="t">
                          {d.tienda ?? d.nombre_comercial ?? d.codigo_sucursal}
                        </div>
                        <div className="s">
                          {d.ciudad ?? 'Sucursal'} ·{' '}
                          <span className="mono">{d.codigo_envio}</span> ·{' '}
                          {d.placas_vehiculo ?? d.vehiculo_reparto ?? 'Reparto'}
                        </div>
                      </div>
                      <span className="mono">
                        {Number(d.kg_entregados ?? d.cantidad_kg ?? 0).toLocaleString()} kg
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="lead" style={{ fontSize: 13 }}>
                  Sin despachos hacia tiendas registrados para este lote.
                </p>
              )}
              <div
                style={{
                  display: 'flex',
                  gap: 8,
                  flexWrap: 'wrap',
                  marginTop: 10,
                }}
              >
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  disabled={destinos.length === 0}
                  onClick={handleExportTiendasCsv}
                >
                  <Download size={14} /> Exportar lista de tiendas (CSV)
                </button>
              </div>
            </div>

            <div className="card back">
              <div className="card-head">
                <h2>2 · Hacia atrás (Origen)</h2>
              </div>
              <ul className="list">
                <li>
                  <div>
                    <div className="t">
                      {trazaAtrasLat?.origen?.productor_nombre ??
                        lote.productor_nombre ??
                        'Sin productor registrado'}
                    </div>
                    <div className="s mono">
                      {trazaAtrasLat?.origen?.codigo_senasica ??
                        lote.codigo_senasica ??
                        'Sin código SENASICA'}
                    </div>
                  </div>
                </li>
                <li>
                  <div>
                    <div className="t">
                      {trazaAtrasLat?.origen?.nombre_huerta ??
                        lote.nombre_huerta ??
                        'Sin huerta registrada'}
                    </div>
                    <div className="s">
                      {trazaAtrasLat?.origen?.municipio ?? lote.municipio ?? 'Parcela de origen'}
                    </div>
                  </div>
                </li>
                {expediente.analisis_laboratorio.map((an) => (
                  <li key={an.folio_analisis}>
                    <div>
                      <div className="t">{an.tipo_estudio}</div>
                      <div className="s">
                        {an.laboratorio?.nombre} · <span className="mono">V{an.version}</span>
                      </div>
                    </div>
                    <DictamenBadge dictamen={an.dictamen_general} />
                  </li>
                ))}
              </ul>
            </div>

            <div className="card lat">
              <div className="card-head">
                <h2>3 · Lateral (Contagio)</h2>
              </div>
              {hermanos.length > 0 ? (
                <ul className="list">
                  {hermanos.map((h, idx) => {
                    const code = h.lote_hermano ?? h.codigo_lote ?? `Hermano-${idx}`;
                    const recurso =
                      h.recurso_compartido ??
                      `${h.tipo_recurso ?? 'Recurso'} ${h.identificador_recurso ?? ''}`;
                    return (
                      <li key={`${code}-${idx}`}>
                        <div>
                          <div className="t mono">{code}</div>
                          <div className="s">Compartió {recurso}</div>
                        </div>
                        <span className="badge s-warn">
                          <AlertTriangle size={13} /> Sospechoso
                        </span>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="lead" style={{ fontSize: 13 }}>
                  Sin lotes hermanos detectados en la ventana de contaminación.
                </p>
              )}
              <p className="lock">
                <Info size={14} />
                <span>
                  Se incluye en el bloqueo preventivo de esta misma acción.
                </span>
              </p>
            </div>
          </div>

          <div className="grid half" style={{ marginTop: 16 }}>
            <div className="card">
              <div className="card-head">
                <div className="left">
                  <h2>Cola de dictamen sanitario</h2>
                </div>
                <span className="badge s-warn">{colaDictamen.length} pendiente(s)</span>
              </div>
              <ul className="list">
                {colaDictamen.map((item) => (
                  <li key={item.codigo_lote}>
                    <div>
                      <div className="t mono">{item.codigo_lote}</div>
                      <div className="s">
                        Estado actual: <strong>{item.estado}</strong> ·{' '}
                        {Number(item.saldo_kg).toLocaleString()} kg
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => setLiberarTarget(item.codigo_lote)}
                      >
                        Liberar
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        style={{ color: 'var(--danger)' }}
                        onClick={() => {
                          setRecallLoteTarget(item.codigo_lote);
                          setOpenRecallModal(true);
                        }}
                      >
                        Bloquear
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div className="alert alert-info" role="status">
              <RefreshCw size={20} />
              <div>
                <h2>Sincronización del sistema</h2>
                <p>
                  Si algún módulo presenta retraso en la actualización tras un bloqueo, puedes
                  forzar la sincronización pendiente aquí.
                </p>
                <div style={{ marginTop: 10 }}>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    disabled={reconciliacionMutation.isPending}
                    onClick={() => reconciliacionMutation.mutate()}
                  >
                    <RefreshCw size={14} />
                    {reconciliacionMutation.isPending
                      ? 'Reconciliando motores...'
                      : 'Ejecutar reconciliación manual'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* MODAL 1: CONFIRMAR PROTOCOLO DE RECALL */}
      <Modal
        open={openRecallModal}
        title={`Ejecutar Protocolo de Recall · ${recallLoteTarget}`}
        subtitle="Bloqueo inmediato de inventario, rastreo de contagio lateral y apertura de expediente"
        onClose={() => setOpenRecallModal(false)}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            recallMutation.mutate({
              codigo_lote_origen: recallLoteTarget,
              motivo: recallMotivo,
              incluir_lotes_hermanos: incluirHermanos,
              ventana_dias_contaminacion: ventanaDias,
            });
          }}
        >
          <div
            className="alert alert-bad"
            style={{
              padding: '10px 14px',
              fontSize: 12.5,
              marginBottom: 14,
            }}
          >
            <div>
              <strong>Impacto inmediato de la acción:</strong>
              <ul style={{ margin: '4px 0 0 16px', padding: 0, lineHeight: 1.4 }}>
                <li><strong>Inventario:</strong> El lote pasa a <code>Bloqueado</code> y su saldo disponible queda congelado.</li>
                <li><strong>Trazabilidad:</strong> Se identifican las tiendas destino y se bloquean los lotes hermanos relacionados.</li>
                <li><strong>Expediente:</strong> Se abre un expediente formal de incidente para seguimiento y cierre.</li>
              </ul>
            </div>
          </div>

          <div className="field">
            <label htmlFor="rec-motivo">Motivo sanitario del retiro e inmovilización</label>
            <textarea
              id="rec-motivo"
              className="input"
              rows={3}
              minLength={10}
              placeholder="Ej. Alerta sanitaria por exceso de Clorpirifos (> LMR 0.010 mg/kg) en certificado vigente."
              value={recallMotivo}
              onChange={(e) => setRecallMotivo(e.target.value)}
              required
            />
          </div>

          <div className="grid half" style={{ gap: '0 12px' }}>
            <div className="field">
              <label htmlFor="rec-ventana">Ventana de contagio lateral (días)</label>
              <input
                id="rec-ventana"
                type="number"
                min={0}
                max={30}
                className="input mono"
                value={ventanaDias}
                onChange={(e) => setVentanaDias(Number(e.target.value))}
                required
              />
            </div>

            <div className="field" style={{ justifyContent: 'center' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={incluirHermanos}
                  onChange={(e) => setIncluirHermanos(e.target.checked)}
                />
                <span>
                  Bloquear también lotes hermanos
                </span>
              </label>
              <small>Rastrea camiones y cuartos fríos compartidos.</small>
            </div>
          </div>

          {recallMutation.isError && (
            <div
              className="alert alert-bad"
              style={{ margin: '14px 0 6px 0', padding: '10px 14px', fontSize: 13 }}
            >
              <strong>Error al ejecutar recall:</strong>{' '}
              {recallMutation.error instanceof ApiError
                ? recallMutation.error.message
                : 'Ocurrió un error al procesar el retiro del lote.'}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 14 }}>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setOpenRecallModal(false)}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn btn-danger"
              disabled={recallMutation.isPending}
            >
              {recallMutation.isPending
                ? 'Ejecutando protocolo de retiro...'
                : 'Confirmar Recall de Emergencia'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL 2: LIBERAR LOTE */}
      <Modal
        open={Boolean(liberarTarget)}
        title={`Liberación Sanitaria · ${liberarTarget ?? ''}`}
        subtitle="Valida que el lote cuente con análisis de laboratorio conformes vigentes"
        onClose={() => setLiberarTarget(null)}
      >
        {liberarTarget && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              liberarMutation.mutate({ codigo: liberarTarget, motivo: liberarMotivo });
            }}
          >
            <div className="field">
              <label htmlFor="lib-motivo">Justificación técnica de liberación</label>
              <textarea
                id="lib-motivo"
                className="input"
                rows={3}
                minLength={5}
                placeholder="Ej. Liberación sanitaria aprobada tras verificación de análisis conformes vigentes e inspección de vida de anaquel."
                value={liberarMotivo}
                onChange={(e) => setLiberarMotivo(e.target.value)}
                required
              />
              <small>
                Solo se aprobará si el lote cuenta con análisis vigentes conformes y sin dictámenes
                adversos.
              </small>
            </div>

            {liberarMutation.isError && (
              <div
                className="alert alert-bad"
                style={{ margin: '14px 0 6px 0', padding: '10px 14px', fontSize: 13 }}
              >
                <strong>No se pudo liberar el lote:</strong>{' '}
                {liberarMutation.error instanceof ApiError
                  ? liberarMutation.error.message
                  : 'Verifica que el lote cuente con dictamen favorable vigente.'}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 14 }}>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setLiberarTarget(null)}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={liberarMutation.isPending}
              >
                {liberarMutation.isPending ? 'Verificando dictamen...' : 'Aprobar liberación'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </section>
  );
};
