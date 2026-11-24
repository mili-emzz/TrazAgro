import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Eye, EyeOff, Lightbulb, Plus } from 'lucide-react';
import { crearLoteApi, listarLotesApi, obtenerExpediente360Api } from '../../api/lotes';
import { consultarAnalisisApi } from '../../api/operaciones';
import { ApiError } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { DictamenBadge, LoteStatusBadge, SyncBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';
import type { LoteCreateRequest } from '../../types/api';

const PARCELAS_CATALOG = [
  {
    parcela_id: 1,
    productor_id: 1,
    codigo_senasica: 'SENASICA-MICH-URU-014',
    nombre_huerta: 'Huerta La Escondida · Parcela 1 (Uruapan)',
    prefijo_lote: 'P014',
  },
  {
    parcela_id: 2,
    productor_id: 1,
    codigo_senasica: 'SENASICA-MICH-PER-015',
    nombre_huerta: 'Huerta El Mirador · Parcela 2 (Peribán)',
    prefijo_lote: 'P015',
  },
  {
    parcela_id: 3,
    productor_id: 2,
    codigo_senasica: 'SENASICA-MICH-TAN-018',
    nombre_huerta: 'Huerta Los Pinos · Parcela 3 (Tancítaro)',
    prefijo_lote: 'P018',
  },
];

export const ProductorPage: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const misParcelas = useMemo(() => {
    if (!user?.productor_id) return PARCELAS_CATALOG;
    return PARCELAS_CATALOG.filter((p) => p.productor_id === user.productor_id);
  }, [user?.productor_id]);

  const [parcelaId, setParcelaId] = useState<number>(misParcelas[0]?.parcela_id ?? 1);
  const [fechaCosecha, setFechaCosecha] = useState('2026-03-20');
  const [pesoInicialKg, setPesoInicialKg] = useState('1800');
  const [cuadrilla, setCuadrilla] = useState('Cuadrilla Alfa-01');
  const [producto, setProducto] = useState('Aguacate Hass');
  const [consecutivo, setConsecutivo] = useState('01');
  const [feedback, setFeedback] = useState<{ type: 'ok' | 'bad'; text: string } | null>(null);
  const [selectedLoteModal, setSelectedLoteModal] = useState<string | null>(null);

  const { data: lotes = [], isLoading } = useQuery({
    queryKey: ['lotes', user?.username],
    queryFn: () => listarLotesApi(),
  });

  const loteConAnalisis = lotes[0]?.codigo_lote ?? 'AGU-P014-260312-01';
  const [loteAnalisisSeleccionado, setLoteAnalisisSeleccionado] = useState<string>('');
  const targetAnalisisLote = loteAnalisisSeleccionado || loteConAnalisis;

  const { data: analisisResp } = useQuery({
    queryKey: ['analisis-productor', targetAnalisisLote],
    queryFn: () => consultarAnalisisApi(targetAnalisisLote),
    enabled: Boolean(targetAnalisisLote && lotes.length > 0),
  });

  const { data: detalleModal } = useQuery({
    queryKey: ['expediente-productor', selectedLoteModal],
    queryFn: () => obtenerExpediente360Api(selectedLoteModal!),
    enabled: Boolean(selectedLoteModal),
  });

  const parcelaActiva =
    misParcelas.find((p) => p.parcela_id === parcelaId) ?? misParcelas[0] ?? PARCELAS_CATALOG[0];

  const codigoGenerado = useMemo(() => {
    const cleanDate = fechaCosecha.replace(/-/g, '').slice(2); // AAMMDD
    const seq = consecutivo.padStart(2, '0').slice(-2);
    return `AGU-${parcelaActiva.prefijo_lote}-${cleanDate || '260320'}-${seq}`;
  }, [parcelaActiva.prefijo_lote, fechaCosecha, consecutivo]);

  const crearMutation = useMutation({
    mutationFn: (payload: LoteCreateRequest) => crearLoteApi(payload),
    onSuccess: (created) => {
      setFeedback({
        type: 'ok',
        text: `Lote ${created.codigo_lote} registrado en PostgreSQL y proyectado en Neo4j con parcela #${created.parcela_id} (RN-06).`,
      });
      const nextSeq = String(Number(consecutivo) + 1).padStart(2, '0');
      setConsecutivo(nextSeq);
      queryClient.invalidateQueries({ queryKey: ['lotes'] });
    },
    onError: (err) => {
      const msg = err instanceof ApiError ? err.message : 'No se pudo registrar el lote.';
      setFeedback({ type: 'bad', text: msg });
    },
  });

  const handleCrearLote = (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);
    crearMutation.mutate({
      codigo_lote: codigoGenerado,
      parcela_id: parcelaActiva.parcela_id,
      producto,
      fecha_cosecha: `${fechaCosecha}T07:30:00Z`,
      cuadrilla_cosecha: cuadrilla,
      peso_inicial_kg: Number(pesoInicialKg),
    });
  };

  const totalKg = lotes.reduce((acc, l) => acc + Number(l.peso_inicial_kg || 0), 0);

  return (
    <section aria-label="Panel del Productor">
      <div className="note">
        <Lightbulb size={18} />
        <p>
          <strong>Productor · RN-11 y RN-06:</strong> vista móvil filtrada en el backend por{' '}
          <span className="mono">productor_id={user?.productor_id ?? 1}</span>. Solo consulta sus
          propios lotes, su estado y el dictamen de sus análisis. No tiene acceso a tiendas, precios
          ni otros productores. Cada lote exige una única parcela de origen.
        </p>
      </div>

      {feedback && (
        <div
          className={`alert ${feedback.type === 'ok' ? 'alert-ok' : 'alert-bad'}`}
          role="status"
          style={{ marginBottom: 18 }}
        >
          <div>
            <h2>{feedback.type === 'ok' ? 'Cosecha registrada' : 'Aviso de validación'}</h2>
            <p>{feedback.text}</p>
          </div>
        </div>
      )}

      <div className="device-wrap">
        <div className="device" aria-label="Vista móvil del productor">
          <p className="eyebrow">
            {parcelaActiva.nombre_huerta.split('·')[0]} · {parcelaActiva.prefijo_lote}
          </p>
          <h1>{user?.nombre ?? 'Aguacateros Unidos de Michoacán'}</h1>
          <p className="lead mono" style={{ fontSize: 13 }}>
            {parcelaActiva.codigo_senasica}
          </p>

          <a
            href="#form-cosecha"
            className="btn btn-primary btn-lg"
            style={{ margin: '16px 0' }}
          >
            <Plus size={18} /> Registrar cosecha
          </a>

          <div
            className="grid kpis"
            style={{ gridTemplateColumns: '1fr 1fr', margin: '16px 0' }}
          >
            <div className="card kpi">
              <div className="label">Mis lotes</div>
              <div className="value">{lotes.length}</div>
            </div>
            <div className="card kpi">
              <div className="label">Kg cosechados</div>
              <div className="value">{totalKg.toLocaleString()}</div>
            </div>
          </div>

          <div className="card">
            <div className="card-head">
              <h2>Mis lotes</h2>
              <span className="op">GET /api/v1/lotes</span>
            </div>
            {isLoading ? (
              <p className="lead">Cargando lotes del productor...</p>
            ) : (
              <ul className="list">
                {lotes.map((l) => (
                  <li key={l.codigo_lote}>
                    <div>
                      <div className="t mono">{l.codigo_lote}</div>
                      <div className="s">
                        {Number(l.peso_inicial_kg).toLocaleString()} kg ·{' '}
                        {new Date(l.fecha_cosecha).toLocaleDateString('es-MX', {
                          day: '2-digit',
                          month: 'short',
                        })}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <LoteStatusBadge estado={l.estado} />
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        title="Ver detalle del lote"
                        onClick={() => setSelectedLoteModal(l.codigo_lote)}
                      >
                        <Eye size={15} />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="stack">
          <form id="form-cosecha" className="card" onSubmit={handleCrearLote}>
            <div className="card-head">
              <h2>Registrar cosecha en origen</h2>
              <span className="op">POST /api/v1/lotes</span>
            </div>

            <div className="grid half" style={{ gap: '0 12px' }}>
              <div className="field">
                <label htmlFor="f-code">Código de lote generado</label>
                <input
                  id="f-code"
                  className="input mono"
                  value={codigoGenerado}
                  readOnly
                  aria-describedby="f-code-h"
                />
                <small id="f-code-h">
                  Estándar: producto · parcela · fecha · consecutivo.
                </small>
              </div>

              <div className="field">
                <label htmlFor="f-seq">Consecutivo del día</label>
                <input
                  id="f-seq"
                  className="input mono"
                  type="number"
                  min={1}
                  max={99}
                  value={consecutivo}
                  onChange={(e) => setConsecutivo(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="grid half" style={{ gap: '0 12px' }}>
              <div className="field">
                <label htmlFor="f-parc">Parcela de origen (obligatoria)</label>
                <select
                  id="f-parc"
                  className="input"
                  value={parcelaId}
                  onChange={(e) => setParcelaId(Number(e.target.value))}
                  required
                  aria-describedby="f-parc-h"
                >
                  {misParcelas.map((p) => (
                    <option key={p.parcela_id} value={p.parcela_id}>
                      {p.nombre_huerta}
                    </option>
                  ))}
                </select>
                <small id="f-parc-h">
                  <span className="rn">RN-06</span> Cardinalidad estricta: un lote, una parcela.
                </small>
              </div>

              <div className="field">
                <label htmlFor="f-kg">Peso inicial cosechado (kg)</label>
                <input
                  id="f-kg"
                  className="input"
                  type="number"
                  step="0.01"
                  min="1"
                  max="100000"
                  value={pesoInicialKg}
                  onChange={(e) => setPesoInicialKg(e.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="f-date">Fecha de cosecha</label>
                <input
                  id="f-date"
                  className="input"
                  type="date"
                  value={fechaCosecha}
                  onChange={(e) => setFechaCosecha(e.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="f-cuadrilla">Cuadrilla responsable</label>
                <input
                  id="f-cuadrilla"
                  className="input"
                  value={cuadrilla}
                  onChange={(e) => setCuadrilla(e.target.value)}
                  required
                  minLength={3}
                />
              </div>

              <div className="field">
                <label htmlFor="f-prod">Variedad / Producto</label>
                <select
                  id="f-prod"
                  className="input"
                  value={producto}
                  onChange={(e) => setProducto(e.target.value)}
                  required
                >
                  <option value="Aguacate Hass">Aguacate Hass</option>
                </select>
              </div>
            </div>

            {crearMutation.isError && (
              <div
                className="alert alert-bad"
                style={{ margin: '12px 0', padding: '10px 14px', fontSize: 13 }}
              >
                <strong>Error al registrar lote:</strong>{' '}
                {crearMutation.error instanceof ApiError
                  ? crearMutation.error.message
                  : 'No se pudo registrar el lote agrícola.'}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={crearMutation.isPending}
            >
              {crearMutation.isPending ? 'Guardando en PG y Neo4j...' : 'Guardar lote'}
            </button>
          </form>

          <div className="card">
            <div className="card-head">
              <div className="left">
                <h2>Dictamen de mis análisis</h2>
                <span className="op">GET /api/v1/analisis/&#123;lote&#125;</span>
              </div>
              <select
                className="input mono"
                style={{ width: 'auto', minHeight: 34, padding: '4px 10px', fontSize: 13 }}
                value={targetAnalisisLote}
                onChange={(e) => setLoteAnalisisSeleccionado(e.target.value)}
                aria-label="Seleccionar lote para ver dictamen"
              >
                {lotes.map((l) => (
                  <option key={l.codigo_lote} value={l.codigo_lote}>
                    {l.codigo_lote}
                  </option>
                ))}
              </select>
            </div>

            <ul className="list">
              {analisisResp && analisisResp.analisis.length > 0 ? (
                analisisResp.analisis.map((a) => (
                  <li key={a.folio_analisis}>
                    <div>
                      <div className="t mono">
                        {a.codigo_lote} · <span style={{ fontWeight: 400 }}>{a.folio_analisis}</span>
                      </div>
                      <div className="s">
                        {a.tipo_estudio} · {a.laboratorio?.nombre ?? 'Laboratorio Externo'} (V
                        {a.version})
                      </div>
                    </div>
                    <DictamenBadge dictamen={a.dictamen_general} />
                  </li>
                ))
              ) : (
                <li>
                  <div>
                    <div className="t mono">{targetAnalisisLote}</div>
                    <div className="s">Sin muestras de laboratorio registradas aún</div>
                  </div>
                  <span className="badge s-mute">Pendiente</span>
                </li>
              )}
            </ul>

            <p className="lock">
              <EyeOff size={15} />
              <span>
                <span className="rn">RN-11</span> Los destinos comerciales, precios y otros
                productores están ocultos por confidencialidad.
              </span>
            </p>
          </div>
        </div>
      </div>

      <Modal
        open={Boolean(selectedLoteModal)}
        title={`Ficha de Lote · ${selectedLoteModal ?? ''}`}
        subtitle="Resumen de estado de recepción y calidad para el productor (RN-11)"
        onClose={() => setSelectedLoteModal(null)}
      >
        {!detalleModal ? (
          <p className="lead">Consultando ficha del lote...</p>
        ) : (
          <div className="stack">
            <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
              <LoteStatusBadge estado={detalleModal.lote.estado} />
              <SyncBadge sincronizacion={{ postgresql: 'ok', mongodb: 'ok', neo4j: 'ok' }} />
            </div>

            <div className="grid half">
              <div className="card" style={{ background: 'var(--bg)' }}>
                <div className="eyebrow">Cosecha en Huerta</div>
                <div>
                  <strong>Huerta:</strong> {detalleModal.lote.nombre_huerta ?? `Parcela #${detalleModal.lote.parcela_id}`}
                </div>
                <div>
                  <strong>SENASICA:</strong>{' '}
                  <span className="mono">{detalleModal.lote.codigo_senasica ?? 'Verificado'}</span>
                </div>
                <div>
                  <strong>Cuadrilla:</strong> {detalleModal.lote.cuadrilla_cosecha}
                </div>
                <div>
                  <strong>Peso cosechado:</strong>{' '}
                  {Number(detalleModal.lote.peso_inicial_kg).toLocaleString()} kg
                </div>
              </div>

              <div className="card" style={{ background: 'var(--bg)' }}>
                <div className="eyebrow">Recepción en CEDIS</div>
                {detalleModal.recepcion_sql ? (
                  <>
                    <div>
                      <strong>Folio:</strong>{' '}
                      <span className="mono">{detalleModal.recepcion_sql.folio_recepcion}</span>
                    </div>
                    <div>
                      <strong>Temp. arribo:</strong> {detalleModal.recepcion_sql.temperatura_llegada_c} °C
                    </div>
                    <div>
                      <strong>Peso recibido:</strong>{' '}
                      {Number(detalleModal.recepcion_sql.peso_recibido_kg).toLocaleString()} kg
                    </div>
                    <div>
                      <strong>Dictamen:</strong>{' '}
                      <DictamenBadge dictamen={detalleModal.recepcion_sql.dictamen_recepcion} />
                    </div>
                  </>
                ) : (
                  <p className="lead" style={{ fontSize: 13 }}>
                    En tránsito hacia el CEDIS (sin acta de recepción aún).
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </section>
  );
};
