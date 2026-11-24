import React from 'react';
import {
  AlertTriangle,
  Ban,
  Check,
  Clock,
  RefreshCw,
  Sprout,
  Truck,
  X,
} from 'lucide-react';

export const LoteStatusBadge: React.FC<{ estado: string }> = ({ estado }) => {
  switch (estado) {
    case 'Liberado':
      return (
        <span className="badge s-ok">
          <Check size={13} /> Liberado
        </span>
      );
    case 'Bloqueado':
    case 'Retirado':
      return (
        <span className="badge s-bad">
          <Ban size={13} /> {estado}
        </span>
      );
    case 'En revision':
      return (
        <span className="badge s-warn">
          <Clock size={13} /> En revisión
        </span>
      );
    case 'Recibido':
      return (
        <span className="badge s-info">
          <Truck size={13} /> Recibido
        </span>
      );
    case 'Cosechado':
    default:
      return (
        <span className="badge s-new">
          <Sprout size={13} /> {estado}
        </span>
      );
  }
};

export const DictamenBadge: React.FC<{ dictamen: string }> = ({ dictamen }) => {
  const lower = dictamen.toLowerCase();
  if (lower === 'conforme' || lower === 'cerrado') {
    return (
      <span className="badge s-ok">
        <Check size={13} /> {dictamen}
      </span>
    );
  }
  if (lower.includes('no conforme') || lower === 'abierto' || lower === 'retenido') {
    return (
      <span className="badge s-bad">
        <X size={13} /> {dictamen}
      </span>
    );
  }
  return (
    <span className="badge s-warn">
      <Clock size={13} /> {dictamen}
    </span>
  );
};

export const SyncBadge: React.FC<{ sincronizacion?: Record<string, string> | null }> = ({
  sincronizacion,
}) => {
  if (!sincronizacion) return null;
  const entries = Object.entries(sincronizacion);
  const hasPending = entries.some(([, val]) => val.includes('pendiente'));

  return (
    <span className={`badge ${hasPending ? 's-warn' : 's-ok'}`} title={JSON.stringify(sincronizacion)}>
      {hasPending ? <AlertTriangle size={13} /> : <RefreshCw size={13} />}
      {hasPending
        ? 'Sincronización parcial (pendiente reconciliación)'
        : 'PG + Mongo + Neo4j sincronizados'}
    </span>
  );
};
