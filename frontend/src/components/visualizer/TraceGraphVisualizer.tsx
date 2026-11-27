import React, { useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  FlaskConical,
  Snowflake,
  Store,
  Tractor,
  Truck,
} from 'lucide-react';
import type { Expediente360Response } from '../../types/api';

interface TraceGraphVisualizerProps {
  expediente: Expediente360Response;
}

interface GraphNodeInfo {
  id: string;
  label: string;
  category: string;
  variant: 'origin' | 'hot' | 'store' | 'lab' | 'default';
  details: Record<string, string | number>;
}

function getVariantStatusLabel(variant: GraphNodeInfo['variant']): string {
  switch (variant) {
    case 'hot':
      return 'Riesgo';
    case 'origin':
      return 'Validado';
    case 'lab':
      return 'Lab';
    case 'store':
      return 'Destino';
    default:
      return 'Operativo';
  }
}

export const TraceGraphVisualizer: React.FC<TraceGraphVisualizerProps> = ({ expediente }) => {
  const { lote, recepcion_sql, red_trazabilidad, analisis_laboratorio } = expediente;
  const [selectedNode, setSelectedNode] = useState<GraphNodeInfo | null>(null);

  const huertaName =
    red_trazabilidad?.origen?.nombre_huerta ?? lote.nombre_huerta ?? `Parcela #${lote.parcela_id}`;
  const productorName =
    red_trazabilidad?.origen?.productor_nombre ?? lote.productor_nombre ?? 'Productor certificado';
  const senasicaCode =
    red_trazabilidad?.origen?.codigo_senasica ?? lote.codigo_senasica ?? 'SENASICA-VERIFICADO';

  const placasEntrada =
    red_trazabilidad?.transporte_entrada?.placas ??
    recepcion_sql?.placas_vehiculo ??
    'En tránsito';
  const cuartoFrio =
    red_trazabilidad?.cuarto_frio?.codigo ?? recepcion_sql?.codigo_cuarto_frio ?? 'Sin asignar';

  const destinos = red_trazabilidad?.destinos ?? [];
  const hermanos = red_trazabilidad?.lotes_hermanos ?? [];
  const hasSiblings = hermanos.length > 0;
  const vigenteAnalisis = analisis_laboratorio.find((a) => a.es_vigente) ?? analisis_laboratorio[0];

  const nodes: GraphNodeInfo[] = [
    {
      id: 'parcela',
      label: huertaName,
      category: 'Parcela y productor',
      variant: 'origin',
      details: {
        Productor: productorName,
        'Código SENASICA': senasicaCode,
        Origen: 'Parcela única verificada',
      },
    },
    {
      id: 'lote',
      label: lote.codigo_lote,
      category: 'Lote maestro',
      variant: lote.estado === 'Bloqueado' ? 'hot' : 'origin',
      details: {
        Estado: lote.estado,
        'Peso inicial': `${lote.peso_inicial_kg.toLocaleString()} kg`,
        'Saldo actual': `${lote.saldo_kg.toLocaleString()} kg`,
        Cuadrilla: lote.cuadrilla_cosecha,
      },
    },
    {
      id: 'vehiculo',
      label: placasEntrada,
      category: 'Transporte de entrada',
      variant: hasSiblings ? 'hot' : 'default',
      details: {
        Placas: placasEntrada,
        'Temperatura arribo': recepcion_sql ? `${recepcion_sql.temperatura_llegada_c} °C` : 'N/A',
        'Riesgo lateral': hasSiblings
          ? `Compartido con ${hermanos.length} lote(s) hermano(s)`
          : 'Sin cruce detectado',
      },
    },
    {
      id: 'cuarto',
      label: cuartoFrio,
      category: 'Cámara frigorífica',
      variant: hasSiblings ? 'hot' : 'default',
      details: {
        'Cámara frigorífica': cuartoFrio,
        'Folio recepción': recepcion_sql?.folio_recepcion ?? 'Pendiente',
        Dictamen: recepcion_sql?.dictamen_recepcion ?? 'En espera',
      },
    },
  ];

  if (vigenteAnalisis) {
    nodes.push({
      id: 'lab',
      label: `${vigenteAnalisis.folio_analisis}`,
      category: 'Laboratorio',
      variant: vigenteAnalisis.dictamen_general === 'No Conforme' ? 'hot' : 'lab',
      details: {
        Laboratorio: vigenteAnalisis.laboratorio?.nombre ?? 'Laboratorio Acreditado',
        Estudio: vigenteAnalisis.tipo_estudio,
        Dictamen: vigenteAnalisis.dictamen_general,
        Versión: `V${vigenteAnalisis.version}`,
      },
    });
  }

  if (destinos.length > 0) {
    const enviosCodes = destinos.map((d) => d.codigo_envio).join(' / ');
    nodes.push({
      id: 'envios',
      label: enviosCodes,
      category: 'Órdenes de envío',
      variant: 'default',
      details: {
        'Órdenes de envío': enviosCodes,
        'Total envíos': destinos.length,
        'Kg despachados': `${(lote.peso_inicial_kg - lote.saldo_kg).toLocaleString()} kg`,
      },
    });
    nodes.push({
      id: 'tiendas',
      label: `${destinos.length} tienda(s) destino`,
      category: 'Puntos de venta',
      variant: lote.estado === 'Bloqueado' ? 'hot' : 'store',
      details: {
        Sucursales: destinos
          .map((d) => d.tienda ?? d.nombre_comercial ?? d.codigo_sucursal ?? 'Sucursal')
          .join(', '),
        'Acción de retiro':
          lote.estado === 'Bloqueado' ? 'Notificación prioritaria de Recall' : 'Distribución normal',
      },
    });
  }

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-head">
        <div className="left">
          <h2>Ruta física del lote</h2>
        </div>
        <span style={{ fontSize: 12, color: 'var(--muted)' }}>
          Haz clic en cualquier nodo para inspeccionar sus propiedades
        </span>
      </div>

      <div
        className="flow"
        role="region"
        aria-label={`Grafo de trazabilidad del lote ${lote.codigo_lote}`}
      >
        {nodes.map((node, idx) => {
          const statusLabel = getVariantStatusLabel(node.variant);
          return (
            <React.Fragment key={node.id}>
              <button
                type="button"
                onClick={() => setSelectedNode(node)}
                aria-pressed={selectedNode?.id === node.id}
                aria-label={`${node.category}: ${node.label} (${statusLabel})`}
                className={`node ${node.variant === 'default' ? '' : node.variant} mono`}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  outline: selectedNode?.id === node.id ? '2px solid var(--secondary)' : undefined,
                }}
              >
                {node.id === 'parcela' && <Tractor size={14} aria-hidden="true" />}
                {node.id === 'vehiculo' && <Truck size={14} aria-hidden="true" />}
                {node.id === 'cuarto' && <Snowflake size={14} aria-hidden="true" />}
                {node.id === 'lab' && <FlaskConical size={14} aria-hidden="true" />}
                {node.id === 'tiendas' && <Store size={14} aria-hidden="true" />}
                <span>{node.label}</span>
                {node.variant === 'hot' && (
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 3,
                      fontSize: 11,
                      fontFamily: 'Geist, system-ui, sans-serif',
                    }}
                  >
                    <AlertTriangle size={12} aria-hidden="true" /> Riesgo
                  </span>
                )}
                {node.variant === 'origin' && (
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 3,
                      fontSize: 11,
                      fontFamily: 'Geist, system-ui, sans-serif',
                    }}
                  >
                    <CheckCircle2 size={12} aria-hidden="true" /> Validado
                  </span>
                )}
              </button>
              {idx < nodes.length - 1 && <ArrowRight size={15} aria-hidden="true" />}
            </React.Fragment>
          );
        })}
      </div>

      <p className="lead" style={{ fontSize: 12, marginTop: 8 }}>
        Etiqueta <strong>Riesgo</strong> (carmesí): nodos con alerta sanitaria o recursos
        compartidos. Etiqueta <strong>Validado</strong> (verde): origen fitosanitario verificado.
      </p>

      {selectedNode && (
        <div
          style={{
            marginTop: 12,
            padding: '10px 14px',
            borderRadius: 10,
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            fontSize: 13,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 6,
            }}
          >
            <strong>
              {selectedNode.label}{' '}
              <span className="op" style={{ marginLeft: 6 }}>
                {selectedNode.category}
              </span>
            </strong>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setSelectedNode(null)}
            >
              Cerrar ficha
            </button>
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: 8,
            }}
          >
            {Object.entries(selectedNode.details).map(([k, v]) => (
              <div key={k}>
                <span style={{ color: 'var(--muted)' }}>{k}: </span>
                <strong className="mono">{v}</strong>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
