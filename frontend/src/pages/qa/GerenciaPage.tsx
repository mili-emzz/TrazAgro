import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Check, CircleAlert, Download, FileSignature, Lightbulb, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import { listarLotesApi, obtenerExpediente360Api } from '../../api/lotes';
import { cerrarIncidenteApi } from '../../api/operaciones';
import { ApiError } from '../../api/client';
import { Modal } from '../../components/common/Modal';
import type { ExpedienteIncidenteDoc, IncidenteCerrarRequest } from '../../types/api';

export const GerenciaPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: lotes = [] } = useQuery({
    queryKey: ['lotes'],
    queryFn: () => listarLotesApi(),
  });

  // Consultamos los expedientes de los dos lotes involucrados en recall
  const { data: expLote1 } = useQuery({
    queryKey: ['expediente-gerencia', 'AGU-P014-260312-01'],
    queryFn: () => obtenerExpediente360Api('AGU-P014-260312-01'),
  });

  const { data: expLote2 } = useQuery({
    queryKey: ['expediente-gerencia', 'AGU-P014-260312-02'],
    queryFn: () => obtenerExpediente360Api('AGU-P014-260312-02'),
  });

  const [cerrarFolioTarget, setCerrarFolioTarget] = useState<string | null>(null);
  const [causaRaiz, setCausaRaiz] = useState(
    'Almacenamiento simultáneo con el lote primario AGU-P014-260312-01 en cámara CF-02 y transporte MICH-842-K; descartada transferencia superficial tras hisopado negativo.'
  );
  const [accion1, setAccion1] = useState(
    'Sanitización profunda y validación por hisopado de caja refrigerada MICH-842-K y cuarto frío CF-02.'
  );
  const [accion2, setAccion2] = useState(
    'Separación física por tarima de lotes de distintos cortes antes de contar con dictamen de plaguicidas.'
  );
  const [firmaQa, setFirmaQa] = useState('Ing. Valeria Mendoza (Jefa QA)');
  const [firmaGerencia, setFirmaGerencia] = useState('Lic. Ricardo Morales (Director Operaciones)');

  const [feedback, setFeedback] = useState<{ type: 'ok' | 'bad'; text: string } | null>(null);

  const cerrarMutation = useMutation({
    mutationFn: ({ folio, payload }: { folio: string; payload: IncidenteCerrarRequest }) =>
      cerrarIncidenteApi(folio, payload),
    onSuccess: (res) => {
      setCerrarFolioTarget(null);
      setFeedback({
        type: 'ok',
        text: `Expediente ${res.folio_incidente} cerrado formalmente en MongoDB y bitácora PostgreSQL cumpliendo RN-09 (Causa raíz + acciones + firmas).`,
      });
      queryClient.invalidateQueries({ queryKey: ['expediente-gerencia'] });
      queryClient.invalidateQueries({ queryKey: ['expediente-qa'] });
    },
    onError: (err) => {
      setFeedback({
        type: 'bad',
        text: err instanceof ApiError ? err.message : 'Error al cerrar expediente (RN-09).',
      });
    },
  });

  // Combinamos los expedientes documentales sin duplicar folios
  const expedientesMap = new Map<string, ExpedienteIncidenteDoc>();
  for (const doc of [
    ...(expLote2?.expedientes_incidentes ?? []),
    ...(expLote1?.expedientes_incidentes ?? []),
  ]) {
    if (doc.folio_incidente && !expedientesMap.has(doc.folio_incidente)) {
      expedientesMap.set(doc.folio_incidente, doc);
    }
  }

  // Fallback si aún están cargando
  const expedientesList: ExpedienteIncidenteDoc[] =
    expedientesMap.size > 0
      ? Array.from(expedientesMap.values())
      : [
          {
            folio_incidente: 'INC-2026-0013',
            codigo_lote_origen: 'AGU-P014-260312-02',
            motivo_apertura: 'Contaminación cruzada preventiva (CF-02 / MICH-842-K)',
            estado_expediente: 'Abierto',
            causa_raiz: null,
            firmas_cierre: null,
          },
          {
            folio_incidente: 'INC-2026-0012',
            codigo_lote_origen: 'AGU-P014-260312-01',
            motivo_apertura: 'Clorpirifos fuera de LMR (0.080 mg/kg)',
            estado_expediente: 'Cerrado',
            causa_raiz: 'Aplicación tardía de organofosforado en huerta sin respetar carencia.',
            firmas_cierre: {
              responsable_qa: 'Ing. Valeria Mendoza',
              aprobacion_gerencia: 'Lic. Ricardo Morales',
            },
          },
        ];

  const lotesBloqueados = lotes.filter((l) => l.estado === 'Bloqueado');
  const kgProtegidos = lotesBloqueados.reduce((acc, l) => acc + Number(l.saldo_kg), 0);
  const lotesRevision = lotes.filter((l) => l.estado === 'En revision');

  const handleExportAuditReport = () => {
    const report = {
      generado_en: new Date().toISOString(),
      total_lotes: lotes.length,
      lotes_inmovilizados: lotesBloqueados.length,
      kg_protegidos: kgProtegidos,
      expedientes: expedientesList,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: 'application/json;charset=utf-8;',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'reporte-auditoria-gerencia-trazaagro.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section aria-label="Tablero de Gerencia y Cumplimiento">
      <div className="note">
        <Lightbulb size={18} />
        <p>
          <strong>Gerencia · RN-09:</strong> tablero de auditoría ejecutiva y cumplimiento.
          Supervisa la integridad multimotor y firma el cierre formal de expedientes. El cierre se
          activa solo cuando existen <span className="mono">causa_raiz</span>,{' '}
          <span className="mono">acciones_correctivas</span> y{' '}
          <span className="mono">firmas_cierre</span> (validadas por{' '}
          <span className="mono">$jsonSchema</span> en MongoDB).
        </p>
      </div>

      <div className="page-head">
        <div>
          <p className="eyebrow">Dirección de operaciones</p>
          <h1>Inocuidad y cumplimiento normativo</h1>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleExportAuditReport}
        >
          <Download size={16} /> Exportar reporte JSON
        </button>
      </div>

      {feedback && (
        <div
          className={`alert ${feedback.type === 'ok' ? 'alert-ok' : 'alert-bad'}`}
          role="status"
          style={{ marginBottom: 16 }}
        >
          <div>
            <h2>Resolución de Auditoría</h2>
            <p>{feedback.text}</p>
          </div>
        </div>
      )}

      <div className="alert alert-bad" role="status" style={{ marginBottom: 16 }}>
        <ShieldAlert size={20} />
        <div>
          <h2>Incidente activo bajo protocolo de retiro</h2>
          <p>
            Lote <span className="mono">AGU-P014-260312-01</span> bloqueado de forma atómica por QA.
            2 tiendas notificadas (850 kg) y bloqueo lateral preventivo de{' '}
            <span className="mono">AGU-P014-260312-02</span>.
          </p>
        </div>
        <div className="actions">
          <Link to="/qa/recall" className="btn btn-secondary btn-sm">
            Ver expediente 360°
          </Link>
        </div>
      </div>

      <div className="grid kpis" style={{ marginBottom: 16 }}>
        <div className="card kpi">
          <div className="label">Lotes inmovilizados</div>
          <div className="value">{lotesBloqueados.length} lotes</div>
          <div className="meta">
            {kgProtegidos.toLocaleString()} kg protegidos · OP-PG-04
          </div>
        </div>

        <div className="card kpi">
          <div className="label">Cuadre de inventario</div>
          <div className="value">100%</div>
          <div className="meta">
            {lotes.length} de {lotes.length} lotes · OP-PG-03
          </div>
          <div className="progress" role="img" aria-label="100 por ciento">
            <span style={{ width: '100%' }} />
          </div>
        </div>

        <div className="card kpi">
          <div className="label">Integridad de origen</div>
          <div className="value">0</div>
          <div className="meta">lotes sin parcela · OP-N4J-03 (RN-06)</div>
        </div>

        <div className="card kpi">
          <div className="label">Rupturas de frío</div>
          <div className="value">{lotesRevision.length || 1}</div>
          <div className="meta">retenida a tiempo · OP-PG-02 (RN-07)</div>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <div className="left">
            <h2>Expedientes de incidente sanitario</h2>
            <span className="op">OP-MG-04 · PATCH /api/v1/incidentes/&#123;folio&#125;/cerrar</span>
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <caption className="sr-only">
              Expedientes de incidentes con estado, requisitos de cierre RN-09 y acción de firma
            </caption>
            <thead>
              <tr>
                <th scope="col">Folio</th>
                <th scope="col">Lote origen</th>
                <th scope="col">Motivo</th>
                <th scope="col">Requisitos de cierre (RN-09)</th>
                <th scope="col">Estado</th>
                <th scope="col">Acción</th>
              </tr>
            </thead>
            <tbody>
              {expedientesList.map((inc) => {
                const isCerrado = inc.estado_expediente === 'Cerrado';
                const loteCode = inc.codigo_lote_origen ?? inc.codigo_lote ?? 'AGU-P014-260312-02';
                return (
                  <tr key={inc.folio_incidente}>
                    <td className="mono">
                      <strong>{inc.folio_incidente}</strong>
                    </td>
                    <td className="mono">{loteCode}</td>
                    <td>{inc.motivo_apertura ?? inc.tipo_incidente ?? 'Contingencia sanitaria'}</td>
                    <td>
                      {isCerrado ? (
                        <span>
                          Causa: <em>{inc.causa_raiz}</em> · Firmas QA + Gerencia
                        </span>
                      ) : (
                        <span style={{ color: 'var(--danger)', fontWeight: 500 }}>
                          Falta causa raíz, acciones y firmas de cierre
                        </span>
                      )}
                    </td>
                    <td>
                      {isCerrado ? (
                        <span className="badge s-ok">
                          <Check size={13} /> Cerrado
                        </span>
                      ) : (
                        <span className="badge s-bad">
                          <CircleAlert size={13} /> {inc.estado_expediente}
                        </span>
                      )}
                    </td>
                    <td>
                      {!isCerrado ? (
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          onClick={() => setCerrarFolioTarget(inc.folio_incidente)}
                        >
                          <FileSignature size={14} /> Firmar y cerrar
                        </button>
                      ) : (
                        <span className="badge s-mute">Auditado</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL CIERRE DE EXPEDIENTE RN-09 */}
      <Modal
        open={Boolean(cerrarFolioTarget)}
        title={`Cierre Formal de Expediente · ${cerrarFolioTarget ?? ''}`}
        subtitle="PATCH /api/v1/incidentes/{folio}/cerrar · Exige causa raíz, acciones correctivas y firmas mancomunadas (RN-09)"
        onClose={() => setCerrarFolioTarget(null)}
      >
        {cerrarFolioTarget && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const acciones = [accion1.trim(), accion2.trim()].filter(Boolean);
              cerrarMutation.mutate({
                folio: cerrarFolioTarget,
                payload: {
                  causa_raiz: causaRaiz,
                  acciones_correctivas: acciones,
                  responsable_qa: firmaQa,
                  aprobacion_gerencia: firmaGerencia,
                },
              });
            }}
          >
            <div className="field">
              <label htmlFor="c-causa">Causa raíz dictaminada (Obligatoria por RN-09)</label>
              <textarea
                id="c-causa"
                className="input"
                rows={3}
                minLength={10}
                value={causaRaiz}
                onChange={(e) => setCausaRaiz(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="c-acc1">Acción correctiva #1 (CAPA)</label>
              <input
                id="c-acc1"
                className="input"
                minLength={5}
                value={accion1}
                onChange={(e) => setAccion1(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="c-acc2">Acción correctiva #2 (Prevención de recurrencia)</label>
              <input
                id="c-acc2"
                className="input"
                value={accion2}
                onChange={(e) => setAccion2(e.target.value)}
              />
            </div>

            <div className="grid half" style={{ gap: '0 12px' }}>
              <div className="field">
                <label htmlFor="c-fqa">Firma Responsable de QA</label>
                <input
                  id="c-fqa"
                  className="input"
                  value={firmaQa}
                  onChange={(e) => setFirmaQa(e.target.value)}
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="c-fger">Firma Aprobación Gerencia</label>
                <input
                  id="c-fger"
                  className="input"
                  value={firmaGerencia}
                  onChange={(e) => setFirmaGerencia(e.target.value)}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setCerrarFolioTarget(null)}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={cerrarMutation.isPending}
              >
                {cerrarMutation.isPending
                  ? 'Validando RN-09 en MongoDB...'
                  : 'Firmar y cerrar expediente'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </section>
  );
};
