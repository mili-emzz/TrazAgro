import React from 'react';
import { Link } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="card" style={{ maxWidth: 520, margin: '48px auto', textAlign: 'center' }}>
      <h1>404 · Ruta no encontrada</h1>
      <p className="lead" style={{ marginTop: 8 }}>
        La pantalla solicitada no existe dentro de TrazaAgro.
      </p>
      <div style={{ marginTop: 16 }}>
        <Link to="/" className="btn btn-primary">
          Volver al inicio
        </Link>
      </div>
    </div>
  );
};
