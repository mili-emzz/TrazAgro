import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Check, FileUp, GitBranchPlus, Lightbulb, Shield, X } from 'lucide-react';
import { listarLotesApi } from '../../api/lotes';
import { consultarAnalisisApi, registrarAnalisisApi } from '../../api/operaciones';
import { ApiError } from '../../api/client';
import { DictamenBadge } from '../../components/common/StatusBadge';
import type { AnalisisCreateRequest, DeterminacionItem } from '../../types/api';

export const LaboratorioPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: lotes = [] } = useQuery({
    queryKey: ['lotes'],
    queryFn: () => listarLotesApi(),
  });

  const [selectedLote, setSelectedLote] = useState('AGU-P014-260312-01');
  const { data: analisisList } = useQuery({
    queryKey: ['analisis-lab', selectedLote],
    queryFn: () => consultarAnalisisApi(selectedLote),
    enabled: Boolean(selectedLote),
  });

  // Formulario polimórfico POST /api/v1/analisis
  const [formLote, setFormLote] = useState('AGU-P015-260315-01');
  const [formFolio, setFormFolio] = useState('LAB-2026-AGU-0925-V1');
  const [formTipo, setFormTipo] = useState<
    'Residuos de Plaguicidas' | 'Microbiologico' | 'Materia Seca'
  >('Residuos de Plaguicidas');
  const [formMotivoEnmienda, setFormMotivoEnmienda] = useState('');
  const [isEnmiendaMode, setIsEnmiendaMode] = useState(false);

  // Campos dinámicos según tipo de estudio
  const [molecula, setMolecula] = useState('Clorpirifos');
  const [metodo, setMetodo] = useState('AOAC 2007.01 GC-MS/MS');
  const [resultadoMgKg, setResultadoMgKg] = useState('0.004');
  const [lmrMgKg, setLmrMgKg] = useState('0.010');

  const [parametroMicro, setParametroMicro] = useState('Salmonella spp.');
  const [resultadoCualitativo, setResultadoCualitativo] = useState('Ausente en 25 g');
  const [criterioNormativo, setCriterioNormativo] = useState('NOM-210-SSA1 / Ausencia');
  const [microConforme, setMicroConforme] = useState(true);

  const [feedback, setFeedback] = useState<{ type: 'ok' | 'bad'; text: string } | null>(null);

  const analisisMutation = useMutation({
    mutationFn: (payload: AnalisisCreateRequest) => registrarAnalisisApi(payload),
    onSuccess: (res) => {
      setFeedback({
        type: 'ok',
        text: `Certificado ${res.folio_analisis} (V${res.version}) guardado inmutablemente en MongoDB y proyectado en Neo4j. ${
          res.folio_reemplazado
            ? `Reemplazó a la versión histórica ${res.folio_reemplazado} (RN-05).`
            : ''
        }`,
      });
      setSelectedLote(res.codigo_lote);
      setIsEnmiendaMode(false);
      setFormMotivoEnmienda('');
      queryClient.invalidateQueries({ queryKey: ['analisis-lab'] });
    },
    onError: (err) => {
      setFeedback({
        type: 'bad',
        text: err instanceof ApiError ? err.message : 'Error al registrar certificado.',
      });
    },
  });

  const handlePrepareEnmienda = () => {
    const docs = analisisList?.analisis ?? [];
    const vigente = docs.find((d) => d.es_vigente) ?? docs[0];
    const nextVersion = vigente ? vigente.version + 1 : 2;
    const baseFolio = vigente
      ? vigente.folio_analisis.replace(/-V\d+$/, '')
      : 'LAB-2026-AGU-0910';

    setFormLote(selectedLote);
    setFormFolio(`${baseFolio}-V${nextVersion}`);
    if (
      vigente?.tipo_estudio === 'Residuos de Plaguicidas' ||
      vigente?.tipo_estudio === 'Microbiologico' ||
      vigente?.tipo_estudio === 'Materia Seca'
    ) {
      setFormTipo(vigente.tipo_estudio);
    }
    setIsEnmiendaMode(true);
    setFormMotivoEnmienda(
      'Reanálisis de contramuestra por ajuste en curva de calibración cromatográfica (RN-05).'
    );
    document.getElementById('form-certificado')?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmitAnalisis = (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);

    let determinacion: DeterminacionItem;
    let dictamen: 'Conforme' | 'No Conforme';

    if (formTipo === 'Residuos de Plaguicidas') {
      const resVal = Number(resultadoMgKg);
      const limVal = Number(lmrMgKg);
      const isOk = resVal <= limVal;
      dictamen = isOk ? 'Conforme' : 'No Conforme';
      determinacion = {
        molecula,
        metodo_ensayo: metodo,
        unidad: 'mg/kg',
        resultado_mg_kg: resVal,
        limite_maximo_mg_kg: limVal,
        conforme: isOk,
      };
    } else {
      dictamen = microConforme ? 'Conforme' : 'No Conforme';
      determinacion = {
        parametro: parametroMicro,
        metodo_ensayo: formTipo === 'Microbiologico' ? 'NOM-210-SSA1-2014' : 'AOAC 934.01 Horno',
        resultado_cualitativo: resultadoCualitativo,
        criterio_normativo: criterioNormativo,
        conforme: microConforme,
      };
    }

    analisisMutation.mutate({
      folio_analisis: formFolio,
      codigo_lote: formLote,
      tipo_estudio: formTipo,
      fecha_muestreo: new Date().toISOString(),
      motivo_enmienda: formMotivoEnmienda.trim() ? formMotivoEnmienda.trim() : null,
      dictamen_general: dictamen,
      laboratorio: {
        nombre: 'Lab AgroBio S.A. de C.V.',
        acreditacion_iso: 'EMA-ISA-17025-2024',
        contacto_correo: 'resultados@agrobio.mx',
      },
      muestras: [
        {
          identificador_muestra: `M-${formLote.slice(-2)}A`,
          parte_analizada: 'Pulpa y cáscara entera',
          peso_gramos: 500,
          determinaciones: [determinacion],
        },
      ],
    });
  };

  const docs = analisisList?.analisis ?? [];
  const docPrincipal = docs.find((d) => d.es_vigente) ?? docs[0];
  const determinaciones =
    docPrincipal?.muestras?.flatMap((m) => m.determinaciones) ?? [];

  return (
    <section aria-label="Panel de Laboratorio Externo">
      <div className="note">
        <Lightbulb size={18} />
        <p>
          <strong>Laboratorio · RN-05, RN-02:</strong> los parámetros cambian según el tipo de
          estudio (<span className="mono">DeterminacionSchema</span> polimórfico). No existe botón
          de editar ni sobrescritura destructiva: toda corrección crea una versión nueva (
          <span className="mono">V+1</span>) que exige <span className="mono">motivo_enmienda</span>{' '}
          y enlaza la anterior con <span className="mono">folio_reemplazado</span>.
        </p>
      </div>

      <div className="page-head">
        <div>
          <p className="eyebrow">Lab AgroBio S.A. de C.V. · EMA-ISA-17025</p>
          <h1>Certificados de análisis</h1>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <label htmlFor="sel-lab-lote" style={{ fontSize: 13, fontWeight: 600 }}>
            Inspeccionar lote:
          </label>
          <select
            id="sel-lab-lote"
            className="input mono"
            style={{ width: 'auto', minHeight: 38 }}
            value={selectedLote}
            onChange={(e) => setSelectedLote(e.target.value)}
          >
            {lotes.map((l) => (
              <option key={l.codigo_lote} value={l.codigo_lote}>
                {l.codigo_lote}
              </option>
            ))}
          </select>
          <a href="#form-certificado" className="btn btn-primary">
            <FileUp size={17} /> Cargar certificado
          </a>
        </div>
      </div>

      {feedback && (
        <div
          className={`alert ${feedback.type === 'ok' ? 'alert-ok' : 'alert-bad'}`}
          role="status"
          style={{ marginBottom: 16 }}
        >
          <div>
            <h2>Bitácora documental MongoDB</h2>
            <p>{feedback.text}</p>
          </div>
        </div>
      )}

      <div className="grid two">
        <div className="card">
          <div className="card-head">
            <div className="left">
              <h2>Determinaciones analíticas</h2>
              <span className="op">OP-MG-01</span>
            </div>
            {docPrincipal && <DictamenBadge dictamen={docPrincipal.dictamen_general} />}
          </div>

          {docPrincipal ? (
            <>
              <p className="lead" style={{ margin: '0 0 8px' }}>
                <span className="mono">{docPrincipal.folio_analisis}</span> ·{' '}
                <span className="mono">{docPrincipal.codigo_lote}</span> ·{' '}
                {docPrincipal.tipo_estudio}
              </p>
              <div className="table-wrap">
                <table>
                  <caption className="sr-only">
                    Parámetros o moléculas analizadas con resultado, límite máximo y dictamen
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Molécula / Parámetro</th>
                      <th scope="col">Método</th>
                      <th scope="col" className="num">
                        Resultado
                      </th>
                      <th scope="col" className="num">
                        LMR / Criterio
                      </th>
                      <th scope="col">Dictamen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {determinaciones.map((det, idx) => (
                      <tr key={idx}>
                        <td>
                          <strong>{det.molecula ?? det.parametro}</strong>
                        </td>
                        <td className="mono" style={{ fontSize: 12 }}>
                          {det.metodo_ensayo ?? 'ISO 17025'}
                        </td>
                        <td className="num mono">
                          <strong>
                            {det.resultado_mg_kg !== undefined && det.resultado_mg_kg !== null
                              ? `${det.resultado_mg_kg} ${det.unidad ?? 'mg/kg'}`
                              : det.resultado_cualitativo}
                          </strong>
                        </td>
                        <td className="num mono">
                          {det.limite_maximo_mg_kg !== undefined && det.limite_maximo_mg_kg !== null
                            ? `${det.limite_maximo_mg_kg} mg/kg`
                            : det.criterio_normativo ?? 'Norma'}
                        </td>
                        <td>
                          {det.conforme ? (
                            <span className="badge s-ok">
                              <Check size={13} /> Conforme
                            </span>
                          ) : (
                            <span className="badge s-bad">
                              <X size={13} /> Fuera de límite
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <p className="lead">
              No hay certificados registrados para <span className="mono">{selectedLote}</span>.
            </p>
          )}
        </div>

        <div className="card">
          <div className="card-head">
            <div className="left">
              <h2>Historial de versiones</h2>
              <span className="op">OP-MG-02 · RN-05</span>
            </div>
          </div>
          <p className="lead mono" style={{ margin: '0 0 12px', fontSize: 13 }}>
            {selectedLote}
          </p>

          {docs.length > 0 ? (
            <ol className="timeline">
              {docs.map((doc) => (
                <li key={doc.folio_analisis} className={doc.es_vigente ? '' : 'muted'}>
                  <time>{doc.es_vigente ? 'Vigente (Activa)' : 'Histórica · solo lectura'}</time>
                  <strong className="mono">{doc.folio_analisis}</strong>{' '}
                  <DictamenBadge dictamen={doc.dictamen_general} />
                  <br />
                  <span style={{ fontSize: 12.5, color: 'var(--muted)' }}>
                    {doc.tipo_estudio} · V{doc.version}
                    {doc.motivo_enmienda ? ` — "${doc.motivo_enmienda}"` : ''}
                  </span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="lead" style={{ fontSize: 13 }}>
              Sin versiones registradas.
            </p>
          )}

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ marginTop: 8 }}
            onClick={handlePrepareEnmienda}
          >
            <GitBranchPlus size={15} /> Emitir corrección (Nueva versión V+1)
          </button>
        </div>
      </div>

      <form
        id="form-certificado"
        className="card"
        style={{ marginTop: 16 }}
        onSubmit={handleSubmitAnalisis}
      >
        <div className="card-head">
          <div className="left">
            <h2>
              {isEnmiendaMode
                ? 'Emitir enmienda versionada (RN-05)'
                : 'Cargar nuevo certificado analítico'}
            </h2>
            <span className="op">POST /api/v1/analisis</span>
          </div>
          {isEnmiendaMode && (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => {
                setIsEnmiendaMode(false);
                setFormMotivoEnmienda('');
                setFormFolio('LAB-2026-AGU-0925-V1');
              }}
            >
              Cambiar a emisión inicial V1
            </button>
          )}
        </div>

        <div className="grid half" style={{ gap: '0 12px' }}>
          <div className="field">
            <label htmlFor="l-folio">Folio del certificado</label>
            <input
              id="l-folio"
              className="input mono"
              value={formFolio}
              onChange={(e) => setFormFolio(e.target.value)}
              pattern="^LAB-\d{4}-AGU-\d{4}-V\d+$"
              required
            />
            <small>Formato: LAB-AAAA-AGU-NNNN-V1 (o V2, V3 para enmiendas).</small>
          </div>

          <div className="field">
            <label htmlFor="l-lote">Código de lote</label>
            <select
              id="l-lote"
              className="input mono"
              value={formLote}
              onChange={(e) => setFormLote(e.target.value)}
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
            <label htmlFor="l-tipo">Tipo de estudio (Polimórfico)</label>
            <select
              id="l-tipo"
              className="input"
              value={formTipo}
              onChange={(e) =>
                setFormTipo(
                  e.target.value as
                    | 'Residuos de Plaguicidas'
                    | 'Microbiologico'
                    | 'Materia Seca'
                )
              }
            >
              <option value="Residuos de Plaguicidas">Residuos de Plaguicidas (Químico LMR)</option>
              <option value="Microbiologico">Microbiológico (Patógenos / UFC)</option>
              <option value="Materia Seca">Materia Seca (Madurez Comercial)</option>
            </select>
          </div>

          <div className="field">
            <label htmlFor="l-motivo">
              Motivo de enmienda {isEnmiendaMode ? '(Obligatorio en V2+ por RN-05)' : '(Opcional en V1)'}
            </label>
            <input
              id="l-motivo"
              className="input"
              placeholder="Ej. Reanálisis de contramuestra por ajuste de calibración..."
              value={formMotivoEnmienda}
              onChange={(e) => setFormMotivoEnmienda(e.target.value)}
              required={isEnmiendaMode}
            />
          </div>
        </div>

        {formTipo === 'Residuos de Plaguicidas' ? (
          <div className="grid half" style={{ gap: '0 12px', marginTop: 4 }}>
            <div className="field">
              <label htmlFor="l-mol">Molécula activa</label>
              <input
                id="l-mol"
                className="input"
                value={molecula}
                onChange={(e) => setMolecula(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="l-met">Método cromatográfico</label>
              <input
                id="l-met"
                className="input mono"
                value={metodo}
                onChange={(e) => setMetodo(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="l-res">Resultado cuantificado (mg/kg)</label>
              <input
                id="l-res"
                type="number"
                step="0.001"
                min="0"
                className="input mono"
                value={resultadoMgKg}
                onChange={(e) => setResultadoMgKg(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="l-lmr">Límite Máximo de Residuos LMR (mg/kg)</label>
              <input
                id="l-lmr"
                type="number"
                step="0.001"
                min="0"
                className="input mono"
                value={lmrMgKg}
                onChange={(e) => setLmrMgKg(e.target.value)}
                required
              />
              <small
                style={{
                  fontWeight: 600,
                  color: Number(resultadoMgKg) > Number(lmrMgKg) ? 'var(--danger)' : 'var(--primary)',
                }}
              >
                {Number(resultadoMgKg) > Number(lmrMgKg)
                  ? '⚠ Excede LMR -> Dictamen automático: No Conforme'
                  : '✓ Dentro de LMR -> Dictamen automático: Conforme'}
              </small>
            </div>
          </div>
        ) : (
          <div className="grid half" style={{ gap: '0 12px', marginTop: 4 }}>
            <div className="field">
              <label htmlFor="l-param">Parámetro evaluado</label>
              <input
                id="l-param"
                className="input"
                value={parametroMicro}
                onChange={(e) => setParametroMicro(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="l-cual">Resultado obtenido</label>
              <input
                id="l-cual"
                className="input"
                value={resultadoCualitativo}
                onChange={(e) => setResultadoCualitativo(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="l-crit">Criterio normativo</label>
              <input
                id="l-crit"
                className="input"
                value={criterioNormativo}
                onChange={(e) => setCriterioNormativo(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="l-conf">Evaluación de conformidad</label>
              <select
                id="l-conf"
                className="input"
                value={microConforme ? 'true' : 'false'}
                onChange={(e) => setMicroConforme(e.target.value === 'true')}
              >
                <option value="true">Conforme con la norma</option>
                <option value="false">No Conforme (Presencia / Fuera de rango)</option>
              </select>
            </div>
          </div>
        )}

        {analisisMutation.isError && (
          <div
            className="alert alert-bad"
            style={{ margin: '12px 0', padding: '10px 14px', fontSize: 13 }}
          >
            <strong>Error al registrar certificado:</strong>{' '}
            {analisisMutation.error instanceof ApiError
              ? analisisMutation.error.message
              : 'Error al registrar análisis en MongoDB.'}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginTop: 8 }}>
          <p className="lock" style={{ margin: 0 }}>
            <Shield size={15} />
            <span>
              Índice único parcial en MongoDB: solo una versión vigente por lote y tipo de estudio.
            </span>
          </p>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={analisisMutation.isPending}
          >
            {analisisMutation.isPending ? 'Registrando en MongoDB...' : 'Emitir certificado inmutable'}
          </button>
        </div>
      </form>
    </section>
  );
};
