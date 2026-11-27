import React, { useState } from 'react';
import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Check,
  CheckCircle2,
  CircleAlert,
  Download,
  FileSignature,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { listarLotesApi, obtenerExpediente360Api } from '../../api/lotes';
import { cerrarIncidenteApi } from '../../api/operaciones';
import { ApiError } from '../../api/client';
import { Modal } from '../../components/common/Modal';
import type { ExpedienteIncidenteDoc, IncidenteCerrarRequest } from '../../types/api';

export const GerenciaPage: React.FC = () => {
  const queryClient = useQueryClient();

  const {
    data: lotes = [],
    isLoading: isLoadingLotes,
    isError: isLotesError,
    error: lotesError,
    refetch: refetchLotes,
  } = useQuery({
    queryKey: ['lotes'],
    queryFn: () => listarLotesApi(),
  });

  const lotesConSeguimiento = lotes.filter(
    (l) => l.estado === 'Bloqueado' || l.estado === 'Retirado' || l.estado === 'En revision'
  );

  const expedientesQueries = useQueries({
    queries: lotesConSeguimiento.map((l) => ({
      queryKey: ['expediente-gerencia', l.codigo_lote],
      queryFn: () => obtenerExpediente360Api(l.codigo_lote),
      enabled: Boolean(l.codigo_lote),
    })),
  });

  const isLoadingExpedientes =
    isLoadingLotes || expedientesQueries.some((q) => q.isLoading);

  const [cerrarFolioTarget, setCerrarFolioTarget] = useState<string | null>(null);
  const [causaRaiz, setCausaRaiz] = useState('');
  const [accion1, setAccion1] = useState('');
  const [accion2, setAccion2] = useState('');
  const [firmaQa, setFirmaQa] = useState('');
  const [firmaGerencia, setFirmaGerencia] = useState('');

  const [feedback, setFeedback] = useState<{ type: 'ok' | 'bad'; text: string } | null>(null);

  const resetCierreForm = () => {
    setCausaRaiz('');
    setAccion1('');
    setAccion2('');
    setFirmaQa('');
    setFirmaGerencia('');
  };

  const cerrarMutation = useMutation({
    mutationFn: ({ folio, payload }: { folio: string; payload: IncidenteCerrarRequest }) =>
      cerrarIncidenteApi(folio, payload),
    onSuccess: (res) => {
      setCerrarFolioTarget(null);
      resetCierreForm();
      setFeedback({
        type: 'ok',
        text: `Expediente ${res.folio_incidente} cerrado formalmente con causa raíz, acciones correctivas y firmas.`,
      });
      queryClient.invalidateQueries({ queryKey: ['expediente-gerencia'] });
      queryClient.invalidateQueries({ queryKey: ['expediente-qa'] });
    },
    onError: (err) => {
      setFeedback({
        type: 'bad',
        text: err instanceof ApiError ? err.message : 'Error al cerrar el expediente.',
      });
    },
  });

  // Combinamos los expedientes documentales reales sin duplicar folios
  const expedientesMap = new Map<string, ExpedienteIncidenteDoc>();
  for (const query of expedientesQueries) {
    for (const doc of query.data?.expedientes_incidentes ?? []) {
      if (doc.folio_incidente && !expedientesMap.has(doc.folio_incidente)) {
        expedientesMap.set(doc.folio_incidente, doc);
      }
    }
  }

  const expedientesList: ExpedienteIncidenteDoc[] = Array.from(expedientesMap.values());
  const expedientesAbiertos = expedientesList.filter(
    (inc) => inc.estado_expediente !== 'Cerrado'
  );

  const lotesBloqueados = lotes.filter(
    (l) => l.estado === 'Bloqueado' || l.estado === 'Retirado'
  );
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

      {isLotesError && (
        <div className="alert alert-bad" role="alert" style={{ marginBottom: 16 }}>
          <ShieldAlert size={20} />
          <div>
            <h2>No se pudieron cargar los lotes de auditoría</h2>
            <p>
              {lotesError instanceof ApiError
                ? lotesError.message
                : 'Verifica la conexión con la API e intenta nuevamente.'}
            </p>
          </div>
          <div className="actions">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => refetchLotes()}
            >
              <RefreshCw size={14} /> Reintentar
            </button>
          </div>
        </div>
      )}

      {!isLotesError && (lotesBloqueados.length > 0 || expedientesAbiertos.length > 0) ? (
        <div className="alert alert-bad" role="status" style={{ marginBottom: 16 }}>
          <ShieldAlert size={20} />
          <div>
            <h2>
              {lotesBloqueados.length > 0
                ? `${lotesBloqueados.length} lote(s) inmovilizado(s) bajo protocolo de retiro`
                : `${expedientesAbiertos.length} expediente(s) de incidente abierto(s)`}
            </h2>
            <p>
              {lotesBloqueados.length > 0 && (
                <>
                  Lotes:{' '}
                  <span className="mono">
                    {lotesBloqueados.map((l) => l.codigo_lote).join(', ')}
                  </span>{' '}
                  · {kgProtegidos.toLocaleString()} kg protegidos.{' '}
                </>
              )}
              {expedientesAbiertos.length} expediente(s) pendiente(s) de cierre formal.
            </p>
          </div>
          <div className="actions">
            <Link to="/qa/recall" className="btn btn-secondary btn-sm">
              Ver consola de recall
            </Link>
          </div>
        </div>
      ) : (
        !isLotesError &&
        !isLoadingLotes && (
          <div className="alert alert-ok" role="status" style={{ marginBottom: 16 }}>
            <CheckCircle2 size={20} />
            <div>
              <h2>Sin incidentes sanitarios activos</h2>
              <p>
                Ningún lote se encuentra bloqueado ni existen expedientes abiertos pendientes de
                cierre.
              </p>
            </div>
          </div>
        )
      )}

      <div className="grid kpis" style={{ marginBottom: 16 }}>
        <div className="card kpi">
          <div className="label">Lotes inmovilizados</div>
          <div className="value">{lotesBloqueados.length} lotes</div>
          <div className="meta">
            {kgProtegidos.toLocaleString()} kg protegidos
          </div>
        </div>

        <div className="card kpi">
          <div className="label">Cuadre de inventario</div>
          <div className="value">100%</div>
          <div className="meta">
            {lotes.length} de {lotes.length} lotes
          </div>
          <div className="progress" role="img" aria-label="100 por ciento">
            <span style={{ width: '100%' }} />
          </div>
        </div>

        <div className="card kpi">
          <div className="label">Integridad de origen</div>
          <div className="value">0</div>
          <div className="meta">lotes sin parcela asignada</div>
        </div>

        <div className="card kpi">
          <div className="label">Lotes en revisión</div>
          <div className="value">{lotesRevision.length}</div>
          <div className="meta">retenidos para verificación sanitaria</div>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <div className="left">
            <h2>Expedientes de incidente sanitario</h2>
          </div>
        </div>
        <div className="table-wrap">
          <table>
            <caption className="sr-only">
              Expedientes de incidentes con estado, requisitos de cierre y acción de firma
            </caption>
            <thead>
              <tr>
                <th scope="col">Folio</th>
                <th scope="col">Lote origen</th>
                <th scope="col">Motivo</th>
                <th scope="col">Requisitos de cierre</th>
                <th scope="col">Estado</th>
                <th scope="col">Acción</th>
              </tr>
            </thead>
            <tbody>
              {isLoadingExpedientes && expedientesList.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ color: 'var(--muted)' }}>
                    Consultando expedientes de incidentes sanitarios...
                  </td>
                </tr>
              ) : expedientesList.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ color: 'var(--muted)' }}>
                    No hay expedientes de incidente sanitario registrados.
                  </td>
                </tr>
              ) : (
                expedientesList.map((inc) => {
                  const isCerrado = inc.estado_expediente === 'Cerrado';
                  const loteCode = inc.codigo_lote_origen ?? inc.codigo_lote ?? 'Sin lote';
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
                            onClick={() => {
                              resetCierreForm();
                              setCerrarFolioTarget(inc.folio_incidente);
                            }}
                          >
                            <FileSignature size={14} /> Firmar y cerrar
                          </button>
                        ) : (
                          <span className="badge s-mute">Auditado</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL CIERRE DE EXPEDIENTE RN-09 */}
      <Modal
        open={Boolean(cerrarFolioTarget)}
        title={`Cierre Formal de Expediente · ${cerrarFolioTarget ?? ''}`}
        subtitle="Exige causa raíz, acciones correctivas y firmas mancomunadas de QA y Gerencia"
        onClose={() => {
          setCerrarFolioTarget(null);
          resetCierreForm();
        }}
      >
        {cerrarFolioTarget && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const acciones = [accion1.trim(), accion2.trim()].filter(Boolean);
              cerrarMutation.mutate({
                folio: cerrarFolioTarget,
                payload: {
                  causa_raiz: causaRaiz.trim(),
                  acciones_correctivas: acciones,
                  responsable_qa: firmaQa.trim(),
                  aprobacion_gerencia: firmaGerencia.trim(),
                },
              });
            }}
          >
            <div className="field">
              <label htmlFor="c-causa">Causa raíz dictaminada (Obligatoria)</label>
              <textarea
                id="c-causa"
                className="input"
                rows={3}
                minLength={10}
                placeholder="Describe la causa raíz verificada durante la investigación del incidente."
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
                placeholder="Ej. Sanitización y validación por hisopado de transporte y cuarto frío."
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
                placeholder="Ej. Separación física por tarima antes de dictamen de laboratorio (opcional)."
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
                  placeholder="Nombre y cargo de QA"
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
                  placeholder="Nombre y cargo de Gerencia"
                  value={firmaGerencia}
                  onChange={(e) => setFirmaGerencia(e.target.value)}
                  required
                />
              </div>
            </div>

            {cerrarMutation.isError && (
              <div
                className="alert alert-bad"
                style={{ margin: '14px 0 6px 0', padding: '10px 14px', fontSize: 13 }}
              >
                <strong>Error al cerrar expediente:</strong>{' '}
                {cerrarMutation.error instanceof ApiError
                  ? cerrarMutation.error.message
                  : 'Verifica que la causa raíz y las acciones correctivas estén completas.'}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 14 }}>
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
                  ? 'Validando y cerrando expediente...'
                  : 'Firmar y cerrar expediente'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </section>
  );
};
