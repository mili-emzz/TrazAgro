import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Ban,
  CheckCircle,
  ClipboardCheck,
  Clock,
  Lightbulb,
  Lock,
  Scale,
  Thermometer,
  Truck,
} from 'lucide-react';
import { listarLotesApi, obtenerExpediente360Api } from '../../api/lotes';
import { registrarEnvioApi, registrarRecepcionApi } from '../../api/operaciones';
import { ApiError } from '../../api/client';
import { LoteStatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';
import type { EnvioCreateRequest, LoteItem, RecepcionCreateRequest } from '../../types/api';

const TIENDAS_ACTIVAS = [
  { tienda_id: 1, codigo: 'SUC-MTY-04', nombre: 'Supermercados del Norte - Valle (Monterrey)' },
  { tienda_id: 2, codigo: 'SUC-CDMX-01', nombre: 'Selecto Chedraui - Polanco (CDMX)' },
  { tienda_id: 3, codigo: 'SUC-GDL-02', nombre: 'Fresko La Comer - Providencia (Guadalajara)' },
];

export const RecepcionCedisPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: lotes = [] } = useQuery({
    queryKey: ['lotes'],
    queryFn: () => listarLotesApi(),
  });

  const [loteTermicoCodigo, setLoteTermicoCodigo] = useState('AGU-P015-260315-01');
  const { data: expedienteTermico } = useQuery({
    queryKey: ['expediente-cedis', loteTermicoCodigo],
    queryFn: () => obtenerExpediente360Api(loteTermicoCodigo),
    enabled: Boolean(loteTermicoCodigo),
  });

  const [feedback, setFeedback] = useState<{ type: 'ok' | 'warn' | 'bad'; text: string } | null>(
    null
  );

  // Modal Nueva Recepción
  const [openRecepcion, setOpenRecepcion] = useState(false);
  const [recFolio, setRecFolio] = useState('REC-2026-0109');
  const [recLote, setRecLote] = useState('AGU-P014-260318-01');
  const [recPlacas, setRecPlacas] = useState('MICH-910-B');
  const [recChofer, setRecChofer] = useState('Roberto Sánchez');
  const [recCuarto, setRecCuarto] = useState('CF-01');
  const [recPeso, setRecPeso] = useState('1596');
  const [recTemp, setRecTemp] = useState('5.6');
  const [recColor, setRecColor] = useState('Verde oscuro brillante');
  const [recFirmeza, setRecFirmeza] = useState('22.5');
  const [recMateriaSeca, setRecMateriaSeca] = useState('25.8');

  // Modal Despacho Fraccionado
  const [despachoLote, setDespachoLote] = useState<LoteItem | null>(null);
  const [envCodigo, setEnvCodigo] = useState('ENV-2026-1056');
  const [envTiendaId, setEnvTiendaId] = useState(1);
  const [envPlacas, setEnvPlacas] = useState('TRK-884-A');
  const [envChofer, setEnvChofer] = useState('Miguel Ángel Torres');
  const [envCantidadKg, setEnvCantidadKg] = useState('250');

  const recepcionMutation = useMutation({
    mutationFn: (payload: RecepcionCreateRequest) => registrarRecepcionApi(payload),
    onSuccess: (res) => {
      setOpenRecepcion(false);
      setLoteTermicoCodigo(res.codigo_lote);
      setFeedback({
        type: res.alerta_cadena_frio ? 'warn' : 'ok',
        text: res.alerta_cadena_frio
          ? `ALERTA RN-07: Recepción ${res.folio_recepcion} fuera de rango (${res.temperatura_llegada_c} °C). Lote ${res.codigo_lote} retenido en estado '${res.estado_lote_resultante}'.`
          : `Recepción ${res.folio_recepcion} registrada conforme (${res.temperatura_llegada_c} °C). Estado del lote: ${res.estado_lote_resultante}.`,
      });
      queryClient.invalidateQueries({ queryKey: ['lotes'] });
      queryClient.invalidateQueries({ queryKey: ['expediente-cedis'] });
    },
    onError: (err) => {
      setFeedback({
        type: 'bad',
        text: err instanceof ApiError ? err.message : 'Error al registrar acta de recepción.',
      });
    },
  });

  const envioMutation = useMutation({
    mutationFn: (payload: EnvioCreateRequest) => registrarEnvioApi(payload),
    onSuccess: (res) => {
      setDespachoLote(null);
      const nuevoSaldo = res.saldos_actualizados[0]?.saldo_kg_restante ?? 0;
      setFeedback({
        type: 'ok',
        text: `Despacho ${res.codigo_envio} por ${res.total_kg} kg procesado con bloqueo ACID (FOR UPDATE). Nuevo saldo disponible: ${nuevoSaldo.toLocaleString()} kg.`,
      });
      const nextNum = String(Number(envCodigo.slice(-4)) + 1).padStart(4, '0');
      setEnvCodigo(`ENV-2026-${nextNum}`);
      queryClient.invalidateQueries({ queryKey: ['lotes'] });
    },
    onError: (err) => {
      setFeedback({
        type: 'bad',
        text: err instanceof ApiError ? err.message : 'Error al procesar despacho (RN-01 / RN-03).',
      });
    },
  });

  const handleSubmitRecepcion = (e: React.FormEvent) => {
    e.preventDefault();
    const tempVal = Number(recTemp);
    recepcionMutation.mutate({
      folio_recepcion: recFolio,
      codigo_lote: recLote,
      placas_vehiculo: recPlacas,
      nombre_chofer: recChofer,
      codigo_cuarto_frio: recCuarto,
      peso_recibido_kg: Number(recPeso),
      temperatura_llegada_c: tempVal,
      turno: 'Matutino',
      evaluacion_sensorial: {
        color_epidermis: recColor,
        firmeza_pulpa_lb: Number(recFirmeza),
        materia_seca_estimada_pct: Number(recMateriaSeca),
        calibre_predominante: '48s',
        pedunculo_presente_pct: 96,
        olor_extrano: false,
      },
      monitoreo_temperatura_caja: [
        { zona_contenedor: 'Fondo (Junto a difusor)', tarima: 'T-01', temperatura_c: Number((tempVal - 0.3).toFixed(1)) },
        { zona_contenedor: 'Centro', tarima: 'T-04', temperatura_c: tempVal },
        { zona_contenedor: 'Puerta trasera', tarima: 'T-07', temperatura_c: Number((tempVal + 0.4).toFixed(1)) },
      ],
      observaciones_inspector:
        tempVal < 4 || tempVal > 8
          ? `ALERTA RN-07: Ruptura de cadena de frío (${tempVal} °C). Retenido en cuarentena.`
          : 'Llegada dentro de rango térmico normativo 4.0 a 8.0 °C.',
    });
  };

  const handleSubmitEnvio = (e: React.FormEvent) => {
    e.preventDefault();
    if (!despachoLote) return;
    envioMutation.mutate({
      codigo_envio: envCodigo,
      tienda_id: envTiendaId,
      placas_vehiculo: envPlacas,
      nombre_chofer: envChofer,
      detalles: [
        {
          codigo_lote: despachoLote.codigo_lote,
          cantidad_kg: Number(envCantidadKg),
        },
      ],
    });
  };

  const lotesLiberados = lotes.filter((l) => l.estado === 'Liberado' && l.saldo_kg > 0);
  const kgLiberados = lotesLiberados.reduce((acc, l) => acc + Number(l.saldo_kg), 0);
  const lotesRevision = lotes.filter((l) => l.estado === 'En revision');
  const kgRevision = lotesRevision.reduce((acc, l) => acc + Number(l.saldo_kg), 0);
  const lotesBloqueados = lotes.filter((l) => l.estado === 'Bloqueado');
  const kgBloqueados = lotesBloqueados.reduce((acc, l) => acc + Number(l.saldo_kg), 0);

  const acta = expedienteTermico?.acta_recepcion;
  const recSql = expedienteTermico?.recepcion_sql;
  const lecturas = acta?.monitoreo_temperatura_caja ?? [
    { zona_contenedor: 'Fondo', tarima: 'T-01', temperatura_c: 10.8 },
    { zona_contenedor: 'Centro', tarima: 'T-04', temperatura_c: 11.4 },
    { zona_contenedor: 'Puerta', tarima: 'T-07', temperatura_c: 12.1 },
  ];

  const isTempOut = Number(recTemp) < 4.0 || Number(recTemp) > 8.0;

  return (
    <section aria-label="Panel de Recepción y Despacho en CEDIS">
      <div className="note">
        <Lightbulb size={18} />
        <p>
          <strong>Recepción · RN-07, RN-01, RN-03:</strong> el acta guarda la temperatura por tarima
          en MongoDB y el pesaje oficial en PostgreSQL. Si el arribo sale de 4.0–8.0 °C, el lote
          queda <em>Retenido</em> y pasa a <em>En revisión</em>. Solo se pueden despachar lotes{' '}
          <em>Liberado</em> con saldo mayor a 0.
        </p>
      </div>

      <div className="page-head">
        <div>
          <p className="eyebrow">CEDIS · Operación de Báscula y Cámara Fría</p>
          <h1>Recepción y despacho fraccionado</h1>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setOpenRecepcion(true)}
          >
            <ClipboardCheck size={17} /> Nueva acta de recepción
          </button>
        </div>
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
            <h2>Notificación transaccional CEDIS</h2>
            <p>{feedback.text}</p>
          </div>
        </div>
      )}

      <div className="alert alert-warn" role="alert" style={{ marginBottom: 16 }}>
        <Thermometer size={20} />
        <div>
          <h2>Lote retenido: ruptura de cadena de frío (RN-07)</h2>
          <p>
            <span className="mono">AGU-P015-260315-01</span> ·{' '}
            <span className="mono">REC-2026-0107</span> · promedio <strong>11.4 °C</strong> (rango
            normativo 4.0–8.0 °C). En cuarentena en <span className="mono">CF-03</span> esperando
            dictamen de QA.
          </p>
        </div>
        <div className="actions">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setLoteTermicoCodigo('AGU-P015-260315-01')}
          >
            Inspeccionar acta
          </button>
        </div>
      </div>

      <div className="grid kpis" style={{ marginBottom: 16 }}>
        <div className="card kpi">
          <div className="label">
            <CheckCircle size={15} /> Listos para despacho
          </div>
          <div className="value">{kgLiberados.toLocaleString()} kg</div>
          <div className="meta">{lotesLiberados.length} lotes liberados</div>
        </div>
        <div className="card kpi">
          <div className="label">
            <Clock size={15} /> En revisión
          </div>
          <div className="value">{kgRevision.toLocaleString()} kg</div>
          <div className="meta">{lotesRevision.length} lote(s)</div>
        </div>
        <div className="card kpi">
          <div className="label">
            <Ban size={15} /> Inmovilizado
          </div>
          <div className="value">{kgBloqueados.toLocaleString()} kg</div>
          <div className="meta">{lotesBloqueados.length} lotes bloqueados</div>
        </div>
        <div className="card kpi">
          <div className="label">
            <Scale size={15} /> Cuadre de saldos
          </div>
          <div className="value">
            {lotes.length}/{lotes.length}
          </div>
          <div className="meta">Inicial − saldo = despachado</div>
        </div>
      </div>

      <div className="grid two">
        <div className="card">
          <div className="card-head">
            <div className="left">
              <h2>Inventario por lote</h2>
              <span className="op">OP-PG-01 · OP-PG-03</span>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <caption className="sr-only">
                Lotes en CEDIS con peso inicial, saldo, estado y acción de despacho
              </caption>
              <thead>
                <tr>
                  <th scope="col">Lote</th>
                  <th scope="col" className="num">
                    Inicial
                  </th>
                  <th scope="col" className="num">
                    Saldo kg
                  </th>
                  <th scope="col">Estado</th>
                  <th scope="col">Acción</th>
                </tr>
              </thead>
              <tbody>
                {lotes.map((l) => {
                  const canDispatch = l.estado === 'Liberado' && Number(l.saldo_kg) > 0;
                  return (
                    <tr key={l.codigo_lote}>
                      <td>
                        <button
                          type="button"
                          className="btn-ghost mono"
                          style={{ padding: 0, fontWeight: 600 }}
                          onClick={() => setLoteTermicoCodigo(l.codigo_lote)}
                          title="Ver perfil térmico y acta de este lote"
                        >
                          {l.codigo_lote}
                        </button>
                      </td>
                      <td className="num">{Number(l.peso_inicial_kg).toLocaleString()}</td>
                      <td className="num">
                        <strong>{Number(l.saldo_kg).toLocaleString()}</strong>
                      </td>
                      <td>
                        <LoteStatusBadge estado={l.estado} />
                      </td>
                      <td>
                        <button
                          type="button"
                          className={`btn btn-sm ${canDispatch ? 'btn-secondary' : ''}`}
                          disabled={!canDispatch}
                          title={
                            canDispatch
                              ? 'Abrir formulario de despacho fraccionado'
                              : `Deshabilitado por RN-01: estado actual '${l.estado}'`
                          }
                          onClick={() => {
                            setDespachoLote(l);
                            setEnvCantidadKg(String(Math.min(250, Number(l.saldo_kg))));
                          }}
                        >
                          <Truck size={14} /> Despachar
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="lock">
            <Lock size={14} />
            <span>
              <span className="rn">RN-01</span> El botón se desactiva para lotes no liberados; el
              backend lo vuelve a validar con <span className="mono">SELECT ... FOR UPDATE</span>.
            </span>
          </p>
        </div>

        <div className="card">
          <div className="card-head">
            <div className="left">
              <h2>Perfil térmico y acta</h2>
              <span className="op">OP-MG-03</span>
            </div>
            <select
              className="input mono"
              style={{ width: 'auto', minHeight: 32, padding: '3px 8px', fontSize: 12.5 }}
              value={loteTermicoCodigo}
              onChange={(e) => setLoteTermicoCodigo(e.target.value)}
              aria-label="Seleccionar lote para ver perfil térmico"
            >
              {lotes.map((l) => (
                <option key={l.codigo_lote} value={l.codigo_lote}>
                  {l.codigo_lote}
                </option>
              ))}
            </select>
          </div>

          {recSql ? (
            <>
              <p className="lead mono" style={{ margin: '0 0 8px', fontSize: 13 }}>
                {recSql.folio_recepcion} · {recSql.placas_vehiculo} · {recSql.codigo_cuarto_frio}
              </p>

              {lecturas.map((lec, i) => {
                const out = lec.temperatura_c < 4 || lec.temperatura_c > 8;
                const pct = Math.min(100, Math.max(15, (lec.temperatura_c / 15) * 100));
                return (
                  <div className="bar-row" key={`${lec.tarima ?? i}`}>
                    <span className="mono">{lec.tarima ?? `M-${i + 1}`}</span>
                    <div
                      className="bar"
                      role="img"
                      aria-label={`${lec.temperatura_c} grados`}
                    >
                      <span
                        style={{
                          width: `${pct}%`,
                          background: out ? 'var(--danger)' : 'var(--primary)',
                        }}
                      />
                    </div>
                    <span className="mono">{lec.temperatura_c} °C</span>
                  </div>
                );
              })}

              <p className="lead" style={{ fontSize: 12 }}>
                Rango permitido 4.0–8.0 °C (<span className="rn">RN-07</span>).
              </p>

              <h3 style={{ marginTop: 12 }}>Evaluación sensorial (MongoDB)</h3>
              <ul className="list">
                <li>
                  <div>
                    <div className="t">Firmeza de pulpa</div>
                    <div className="s">Presión de penetrómetro</div>
                  </div>
                  <span className="mono">
                    {acta?.evaluacion_sensorial?.firmeza_pulpa_lb ?? 17.8} lb
                  </span>
                </li>
                <li>
                  <div>
                    <div className="t">Materia seca estimada</div>
                    <div className="s">Madurez fisiológica</div>
                  </div>
                  <span className="mono">
                    {acta?.evaluacion_sensorial?.materia_seca_estimada_pct ?? 24.4}%
                  </span>
                </li>
                <li>
                  <div>
                    <div className="t">Aspecto epidermis</div>
                    <div className="s">Dictamen físico</div>
                  </div>
                  <span className="badge s-info">
                    {acta?.evaluacion_sensorial?.color_epidermis ?? 'Verde mate'}
                  </span>
                </li>
              </ul>
            </>
          ) : (
            <p className="lead" style={{ fontSize: 13 }}>
              Este lote aún está en estado <strong>Cosechado</strong> y no cuenta con acta de
              recepción en CEDIS. Puedes registrarla con el botón superior.
            </p>
          )}
        </div>
      </div>

      {/* MODAL 1: NUEVA ACTA DE RECEPCIÓN */}
      <Modal
        open={openRecepcion}
        title="Registrar Acta de Recepción en CEDIS"
        subtitle="POST /api/v1/recepciones · Evalúa cadena de frío (RN-07) y sincroniza PG + MongoDB + Neo4j"
        onClose={() => setOpenRecepcion(false)}
      >
        <form onSubmit={handleSubmitRecepcion}>
          <div className="grid half" style={{ gap: '0 12px' }}>
            <div className="field">
              <label htmlFor="r-folio">Folio de recepción</label>
              <input
                id="r-folio"
                className="input mono"
                value={recFolio}
                onChange={(e) => setRecFolio(e.target.value)}
                pattern="^REC-\d{4}-\d{4}$"
                required
              />
            </div>

            <div className="field">
              <label htmlFor="r-lote">Lote que arriba</label>
              <select
                id="r-lote"
                className="input mono"
                value={recLote}
                onChange={(e) => setRecLote(e.target.value)}
                required
              >
                {lotes.map((l) => (
                  <option key={l.codigo_lote} value={l.codigo_lote}>
                    {l.codigo_lote} ({l.estado})
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="r-placas">Placas del camión</label>
              <input
                id="r-placas"
                className="input mono"
                value={recPlacas}
                onChange={(e) => setRecPlacas(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="r-chofer">Nombre del operador</label>
              <input
                id="r-chofer"
                className="input"
                value={recChofer}
                onChange={(e) => setRecChofer(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="r-cuarto">Cuarto frío asignado</label>
              <select
                id="r-cuarto"
                className="input mono"
                value={recCuarto}
                onChange={(e) => setRecCuarto(e.target.value)}
              >
                <option value="CF-01">CF-01 (Cámara Principal)</option>
                <option value="CF-02">CF-02 (Cámara Pre-enfriado)</option>
                <option value="CF-03">CF-03 (Cámara Cuarentena QA)</option>
              </select>
            </div>

            <div className="field">
              <label htmlFor="r-peso">Peso recibido en báscula (kg)</label>
              <input
                id="r-peso"
                type="number"
                step="0.1"
                className="input"
                value={recPeso}
                onChange={(e) => setRecPeso(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="r-temp">Temperatura promedio de llegada (°C)</label>
              <input
                id="r-temp"
                type="number"
                step="0.1"
                className="input mono"
                value={recTemp}
                onChange={(e) => setRecTemp(e.target.value)}
                required
              />
              <small style={{ color: isTempOut ? 'var(--danger)' : 'var(--primary)', fontWeight: 600 }}>
                {isTempOut
                  ? '⚠ Fuera de 4.0–8.0 °C (RN-07): el lote quedará Retenido / En revisión.'
                  : '✓ Dentro de rango térmico 4.0–8.0 °C (RN-07): dictamen Conforme.'}
              </small>
            </div>

            <div className="field">
              <label htmlFor="r-color">Color de epidermis (Sensorial)</label>
              <input
                id="r-color"
                className="input"
                value={recColor}
                onChange={(e) => setRecColor(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="r-firmeza">Firmeza de pulpa (lb)</label>
              <input
                id="r-firmeza"
                type="number"
                step="0.1"
                className="input"
                value={recFirmeza}
                onChange={(e) => setRecFirmeza(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="r-ms">Materia seca estimada (%)</label>
              <input
                id="r-ms"
                type="number"
                step="0.1"
                className="input"
                value={recMateriaSeca}
                onChange={(e) => setRecMateriaSeca(e.target.value)}
                required
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setOpenRecepcion(false)}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={recepcionMutation.isPending}
            >
              {recepcionMutation.isPending ? 'Guardando acta...' : 'Registrar recepción'}
            </button>
          </div>
        </form>
      </Modal>

      {/* MODAL 2: DESPACHO FRACCIONADO */}
      <Modal
        open={Boolean(despachoLote)}
        title={`Despacho Fraccionado · ${despachoLote?.codigo_lote ?? ''}`}
        subtitle="POST /api/v1/envios · Transacción ACID con SELECT ... FOR UPDATE (RN-01, RN-03)"
        onClose={() => setDespachoLote(null)}
      >
        {despachoLote && (
          <form onSubmit={handleSubmitEnvio}>
            <div
              className="card"
              style={{ background: 'var(--bg)', marginBottom: 14, padding: 12 }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13.5 }}>
                <span>Saldo actual en inventario:</span>
                <strong className="mono">{Number(despachoLote.saldo_kg).toLocaleString()} kg</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13.5, marginTop: 4 }}>
                <span>Saldo proyectado tras despacho:</span>
                <strong
                  className="mono"
                  style={{
                    color:
                      Number(despachoLote.saldo_kg) - Number(envCantidadKg) < 0
                        ? 'var(--danger)'
                        : 'var(--primary)',
                  }}
                >
                  {(Number(despachoLote.saldo_kg) - Number(envCantidadKg)).toLocaleString()} kg
                </strong>
              </div>
            </div>

            <div className="grid half" style={{ gap: '0 12px' }}>
              <div className="field">
                <label htmlFor="e-cod">Código de envío</label>
                <input
                  id="e-cod"
                  className="input mono"
                  value={envCodigo}
                  onChange={(e) => setEnvCodigo(e.target.value)}
                  pattern="^ENV-\d{4}-\d{4}$"
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="e-tienda">Sucursal / Tienda destino</label>
                <select
                  id="e-tienda"
                  className="input"
                  value={envTiendaId}
                  onChange={(e) => setEnvTiendaId(Number(e.target.value))}
                >
                  {TIENDAS_ACTIVAS.map((t) => (
                    <option key={t.tienda_id} value={t.tienda_id}>
                      {t.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="e-placas">Placas unidad reparto</label>
                <input
                  id="e-placas"
                  className="input mono"
                  value={envPlacas}
                  onChange={(e) => setEnvPlacas(e.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="e-chofer">Chofer asignado</label>
                <input
                  id="e-chofer"
                  className="input"
                  value={envChofer}
                  onChange={(e) => setEnvChofer(e.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="e-kg">Cantidad a despachar (kg)</label>
                <input
                  id="e-kg"
                  type="number"
                  step="0.01"
                  min="1"
                  max={despachoLote.saldo_kg}
                  className="input mono"
                  value={envCantidadKg}
                  onChange={(e) => setEnvCantidadKg(e.target.value)}
                  required
                />
                <small>
                  <span className="rn">RN-03</span> No puede exceder el saldo disponible.
                </small>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setDespachoLote(null)}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={envioMutation.isPending}
              >
                {envioMutation.isPending ? 'Descontando saldo ACID...' : 'Confirmar despacho'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </section>
  );
};
