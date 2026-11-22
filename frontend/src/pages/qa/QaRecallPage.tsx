import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  Download,
  Info,
  Lightbulb,
  Lock,
  OctagonAlert,
  RefreshCw,
  Search,
  Send,
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

  // Modal de confirmación de Recall (RN-04, RN-08)
  const [openRecallModal, setOpenRecallModal] = useState(false);
  const [recallLoteTarget, setRecallLoteTarget] = useState('AGU-P014-260312-01');
  const [recallMotivo, setRecallMotivo] = useState(
    'Alerta sanitaria por exceso de Clorpirifos (0.080 mg/kg > LMR 0.010 mg/kg) en certificado LAB-2026-AGU-0842-V1.'
  );
  const [incluirHermanos, setIncluirHermanos] = useState(true);
  const [ventanaDias, setVentanaDias] = useState(1);

  // Modal de liberación de lote (RN-02, RN-04)
  const [liberarTarget, setLiberarTarget] = useState<string | null>(null);
  const [liberarMotivo, setLiberarMotivo] = useState(
    'Liberación sanitaria aprobada tras verificación de análisis conformes vigentes e inspección de vida de anaquel (RN-02).'
  );

  const { data: lotes = [] } = useQuery({
    queryKey: ['lotes'],
    queryFn: () => listarLotesApi(),
  });

  const { data: expediente, isLoading } = useQuery({
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
      setCodigoLote(recallLoteTarget);
      setSearchInput(recallLoteTarget);
      const numHermanos = res.lotes_hermanos_bloqueados.length;
      const numTiendas = res.tiendas_afectadas.length;
      setFeedback({
        type: 'ok',
        text: `Protocolo de Recall ejecutado (${res.folio_incidente}): Lote ${recallLoteTarget} y ${numHermanos} lote(s) hermano(s) bloqueados en PostgreSQL, expediente abierto en MongoDB y ${numTiendas} tienda(s) identificada(s) en Neo4j.`,
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
      setFeedback({
        type: 'ok',
        text: `Lote ${res.codigo_lote} cambiado de '${res.estado_previo}' a '${res.estado_actual}' (${res.folio_evento}) tras validar certificados conformes (RN-02).`,
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
            : 'No se pudo liberar el lote (verifica RN-02: requiere análisis vigente Conforme).',
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
  const despachadoKg = lote ? Number(lote.peso_inicial_kg) - Number(lote.saldo_kg) : 850;
  const destinos =
    trazaAdelante?.tiendas_afectadas ?? expediente?.red_trazabilidad?.destinos ?? [];
  const hermanos =
    trazaAtrasLat?.lotes_hermanos ?? expediente?.red_trazabilidad?.lotes_hermanos ?? [];
  const colaDictamen = lotes.filter(
    (l) => l.estado === 'En revision' || l.estado === 'Recibido' || l.estado === 'Cosechado'
  );

  return (
    <section aria-label="Consola de Recall y Expediente 360 de QA">
      <div className="note">
        <Lightbulb size={18} />
        <p>
          <strong>QA · OP-INT-01 y OP-INT-02:</strong> el expediente 360° une PostgreSQL, MongoDB y
          Neo4j en una sola vista. El rastreo hacia adelante va primero porque es lo más urgente
          para retirar producto de anaquel. Bloquear el lote y sus hermanos por contagio lateral es
          una acción atómica (<span className="rn">RN-04</span>, <span className="rn">RN-08</span>).
        </p>
      </div>

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

      <div className="alert alert-bad" role="alert" style={{ marginBottom: 20 }}>
        <OctagonAlert size={22} />
        <div>
          <h2>
            Clorpirifos fuera de LMR · <span className="mono">{codigoLote}</span>
          </h2>
          <p>
            0.080 mg/kg (límite 0.010). {despachadoKg.toLocaleString()} kg despachados a{' '}
            {destinos.length} tienda(s) · {hermanos.length} lote(s) hermano(s) detectado(s) en
            recursos compartidos.
          </p>
        </div>
        <div className="actions">
          <button
            type="button"
            className="btn btn-danger"
            onClick={() => {
              setRecallLoteTarget(codigoLote);
              setOpenRecallModal(true);
            }}
          >
            <Lock size={16} /> Ejecutar recall y bloquear lotes
          </button>
        </div>
      </div>

      <div className="page-head">
        <div>
          <p className="eyebrow">Expediente 360° Consolidado (PG + Mongo + Neo4j)</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h1 className="mono" style={{ fontSize: 22 }}>
              {codigoLote}
            </h1>
            <SyncBadge sincronizacion={{ postgresql: 'ok', mongodb: 'ok', neo4j: 'ok' }} />
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
          <p className="lead">Ensamblando Expediente 360° desde PostgreSQL, MongoDB y Neo4j...</p>
        </div>
      ) : (
        <>
          <dl className="summary">
            <div>
              <dt>Estado Maestro (PG)</dt>
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
                <span className="op">OP-N4J-01</span>
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
                  className="btn btn-primary btn-sm"
                  disabled={destinos.length === 0}
                  onClick={() =>
                    setFeedback({
                      type: 'ok',
                      text: `Alerta sanitaria enviada a ${destinos.length} sucursal(es) para retiro inmediato de anaquel.`,
                    })
                  }
                >
                  <Send size={14} /> Notificar tiendas
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  disabled={destinos.length === 0}
                  onClick={handleExportTiendasCsv}
                >
                  <Download size={14} /> Exportar CSV
                </button>
              </div>
            </div>

            <div className="card back">
              <div className="card-head">
                <h2>2 · Hacia atrás (Origen)</h2>
                <span className="op">OP-INT-02</span>
              </div>
              <ul className="list">
                <li>
                  <div>
                    <div className="t">
                      {trazaAtrasLat?.origen?.productor_nombre ??
                        lote.productor_nombre ??
                        'Aguacateros Unidos de Michoacán'}
                    </div>
                    <div className="s mono">
                      {trazaAtrasLat?.origen?.codigo_senasica ??
                        lote.codigo_senasica ??
                        'SENASICA-MICH-URU-014'}
                    </div>
                  </div>
                </li>
                <li>
                  <div>
                    <div className="t">
                      {trazaAtrasLat?.origen?.nombre_huerta ??
                        lote.nombre_huerta ??
                        'Huerta La Escondida'}
                    </div>
                    <div className="s">
                      1 parcela · <span className="rn">RN-06</span> verificado
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
                <span className="op">OP-N4J-02</span>
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
                  <span className="rn">RN-08</span> Se incluye en el bloqueo preventivo de esta
                  misma acción.
                </span>
              </p>
            </div>
          </div>

          <div className="grid half" style={{ marginTop: 16 }}>
            <div className="card">
              <div className="card-head">
                <div className="left">
                  <h2>Cola de dictamen sanitario</h2>
                  <span className="op">OP-PG-02 · RN-02</span>
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
                <h2>Sincronización entre motores (Outbox)</h2>
                <p>
                  Bitácora técnica <span className="mono">eventos_reconciliacion</span>. Si Neo4j o
                  MongoDB fallan tras el <span className="mono">COMMIT</span>, el bloqueo en
                  PostgreSQL ya protege el inventario (<span className="rn">RN-01</span>).
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
        subtitle="POST /api/v1/incidentes/recall · Bloqueo atómico ACID + Contagio Lateral Neo4j + Expediente MongoDB (RN-04, RN-08)"
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
          <div className="field">
            <label htmlFor="rec-motivo">Motivo sanitario del retiro e inmovilización</label>
            <textarea
              id="rec-motivo"
              className="input"
              rows={3}
              minLength={10}
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
                  Bloquear también lotes hermanos (<span className="rn">RN-08</span>)
                </span>
              </label>
              <small>Rastrea camiones y cuartos fríos compartidos en Neo4j.</small>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
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
                ? 'Bloqueando en PG, Mongo y Neo4j...'
                : 'Confirmar Recall de Emergencia'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL 2: LIBERAR LOTE (RN-02) */}
      <Modal
        open={Boolean(liberarTarget)}
        title={`Liberación Sanitaria · ${liberarTarget ?? ''}`}
        subtitle="PATCH /api/v1/lotes/{codigo}/liberar · Valida análisis vigentes conformes en MongoDB (RN-02, RN-04)"
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
                value={liberarMotivo}
                onChange={(e) => setLiberarMotivo(e.target.value)}
                required
              />
              <small>
                El backend verificará la condición{' '}
                <span className="mono">
                  (∃ análisis vigente Conforme) ∧ (¬∃ análisis vigente No Conforme)
                </span>
                .
              </small>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
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
                {liberarMutation.isPending ? 'Verificando RN-02...' : 'Aprobar liberación'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </section>
  );
};
