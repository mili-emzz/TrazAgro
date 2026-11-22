-- ============================================================================
-- PROYECTO: TrazaAgro - Sistema de Trazabilidad de Alimentos Frescos
-- ENTREGABLE 4: Implementación de la Base de Datos Relacional (PostgreSQL)
-- ARCHIVO: 01_schema.sql (Definición DDL de Tablas, Restricciones, Índices y Vistas)
-- ============================================================================

BEGIN;

-- Limpieza idempotente para reconstrucción desde cero
DROP VIEW IF EXISTS v_auditoria_cadena_frio;
DROP VIEW IF EXISTS v_lotes_listos_despacho;

DROP TABLE IF EXISTS eventos_reconciliacion CASCADE;
DROP TABLE IF EXISTS incidentes_bitacora CASCADE;
DROP TABLE IF EXISTS envios_detalle CASCADE;
DROP TABLE IF EXISTS envios CASCADE;
DROP TABLE IF EXISTS tiendas CASCADE;
DROP TABLE IF EXISTS recepciones_cedis CASCADE;
DROP TABLE IF EXISTS lotes CASCADE;
DROP TABLE IF EXISTS parcelas CASCADE;
DROP TABLE IF EXISTS productores CASCADE;

-- ============================================================================
-- 1. TABLAS DEL DOMINIO DE NEGOCIO (8 TABLAS PRINCIPALES)
-- ============================================================================

-- Tabla 1: productores
-- Catálogo maestro de proveedores agrícolas (RN-10: baja lógica con bandera activo)
CREATE TABLE productores (
    productor_id        SERIAL          PRIMARY KEY,
    rfc                 VARCHAR(13)     NOT NULL UNIQUE,
    nombre_razon_social VARCHAR(120)    NOT NULL,
    telefono            VARCHAR(15)     NOT NULL,
    activo              BOOLEAN         NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_productores_rfc_no_vacio CHECK (LENGTH(TRIM(rfc)) >= 12)
);

COMMENT ON TABLE productores IS 'Catálogo maestro de productores agrícolas titulares de huertas certificadas.';
COMMENT ON COLUMN productores.rfc IS 'Identificación fiscal única del productor; llave natural replicada en Neo4j.';

-- Tabla 2: parcelas
-- Unidades físicas de cultivo certificadas ante SENASICA asociadas a un productor
CREATE TABLE parcelas (
    parcela_id          SERIAL          PRIMARY KEY,
    productor_id        INTEGER         NOT NULL,
    codigo_senasica     VARCHAR(30)     NOT NULL UNIQUE,
    nombre_huerta       VARCHAR(100)    NOT NULL,
    municipio           VARCHAR(60)     NOT NULL,
    superficie_ha       NUMERIC(6,2)    NULL,
    CONSTRAINT fk_parcelas_productor
        FOREIGN KEY (productor_id) REFERENCES productores(productor_id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_parcelas_superficie_positiva
        CHECK (superficie_ha IS NULL OR superficie_ha > 0)
);

COMMENT ON TABLE parcelas IS 'Huertas o unidades de tierra agrícola con registro fitosanitario SENASICA.';

-- Tabla 3: lotes
-- Fuente de verdad transaccional del inventario en kilogramos y del estado sanitario
CREATE TABLE lotes (
    lote_id             SERIAL          PRIMARY KEY,
    codigo_lote         VARCHAR(30)     NOT NULL UNIQUE,
    parcela_id          INTEGER         NOT NULL,
    producto            VARCHAR(60)     NOT NULL,
    fecha_cosecha       TIMESTAMP       NOT NULL,
    cuadrilla_cosecha   VARCHAR(50)     NOT NULL,
    peso_inicial_kg     NUMERIC(10,2)   NOT NULL,
    saldo_kg            NUMERIC(10,2)   NOT NULL,
    estado              VARCHAR(20)     NOT NULL,
    fecha_actualizacion TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lotes_parcela
        FOREIGN KEY (parcela_id) REFERENCES parcelas(parcela_id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_lotes_peso_inicial_positivo
        CHECK (peso_inicial_kg > 0),
    CONSTRAINT chk_lotes_saldo_valido
        CHECK (saldo_kg >= 0 AND saldo_kg <= peso_inicial_kg),
    CONSTRAINT chk_lotes_estado_valido
        CHECK (estado IN ('Cosechado', 'Recibido', 'En revision', 'Liberado', 'Bloqueado', 'Retirado'))
);

COMMENT ON TABLE lotes IS 'Entidad central de trazabilidad: controla saldo contable ACID y estado maestro del lote.';
COMMENT ON COLUMN lotes.codigo_lote IS 'Llave natural puente universal hacia MongoDB y Neo4j (ej. AGU-P014-260312-01).';

-- Tabla 4: recepciones_cedis
-- Registro físico y térmico de arribo del lote al Centro de Distribución (relación 1:0..1 con lotes)
CREATE TABLE recepciones_cedis (
    recepcion_id            SERIAL          PRIMARY KEY,
    folio_recepcion         VARCHAR(25)     NOT NULL UNIQUE,
    lote_id                 INTEGER         NOT NULL UNIQUE,
    fecha_llegada           TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    placas_vehiculo         VARCHAR(15)     NOT NULL,
    codigo_cuarto_frio      VARCHAR(15)     NOT NULL,
    peso_recibido_kg        NUMERIC(10,2)   NOT NULL,
    temperatura_llegada_c   NUMERIC(4,1)    NOT NULL,
    dictamen_recepcion      VARCHAR(20)     NOT NULL,
    CONSTRAINT fk_recepciones_lote
        FOREIGN KEY (lote_id) REFERENCES lotes(lote_id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_recepciones_peso_positivo
        CHECK (peso_recibido_kg > 0),
    CONSTRAINT chk_recepciones_dictamen_valido
        CHECK (dictamen_recepcion IN ('Conforme', 'Retenido', 'Rechazado'))
);

COMMENT ON TABLE recepciones_cedis IS 'Control de entrada física y cadena de frío al arribar el transporte al CEDIS.';
COMMENT ON COLUMN recepciones_cedis.folio_recepcion IS 'Llave natural puente 1:1 hacia la colección actas_recepcion en MongoDB.';

-- Tabla 5: tiendas
-- Catálogo de sucursales comerciales, supermercados o puntos de venta destino (RN-10)
CREATE TABLE tiendas (
    tienda_id           SERIAL          PRIMARY KEY,
    codigo_sucursal     VARCHAR(20)     NOT NULL UNIQUE,
    nombre_comercial    VARCHAR(100)    NOT NULL,
    direccion           VARCHAR(200)    NOT NULL,
    ciudad              VARCHAR(60)     NOT NULL,
    activo              BOOLEAN         NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE tiendas IS 'Puntos de venta o sucursales destino de los envíos comerciales.';

-- Tabla 6: envios
-- Cabecera de órdenes de salida y despacho desde el CEDIS hacia una tienda
CREATE TABLE envios (
    envio_id            SERIAL          PRIMARY KEY,
    codigo_envio        VARCHAR(30)     NOT NULL UNIQUE,
    tienda_id           INTEGER         NOT NULL,
    placas_vehiculo     VARCHAR(15)     NOT NULL,
    fecha_despacho      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_envio        VARCHAR(20)     NOT NULL,
    CONSTRAINT fk_envios_tienda
        FOREIGN KEY (tienda_id) REFERENCES tiendas(tienda_id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_envios_estado_valido
        CHECK (estado_envio IN ('Preparado', 'En transito', 'Entregado', 'Cancelado'))
);

COMMENT ON TABLE envios IS 'Órdenes de despacho logístico desde el CEDIS hacia una sucursal comercial.';

-- Tabla 7: envios_detalle
-- Desglose N:M de los kilogramos fraccionados de cada lote dentro de un envío
CREATE TABLE envios_detalle (
    detalle_id          SERIAL          PRIMARY KEY,
    envio_id            INTEGER         NOT NULL,
    lote_id             INTEGER         NOT NULL,
    cantidad_kg         NUMERIC(10,2)   NOT NULL,
    CONSTRAINT fk_envios_detalle_envio
        FOREIGN KEY (envio_id) REFERENCES envios(envio_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_envios_detalle_lote
        FOREIGN KEY (lote_id) REFERENCES lotes(lote_id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_envios_detalle_cantidad_positiva
        CHECK (cantidad_kg > 0),
    CONSTRAINT uq_envios_detalle_envio_lote
        UNIQUE (envio_id, lote_id)
);

COMMENT ON TABLE envios_detalle IS 'Fraccionamiento exacto en kilogramos de cada lote incluido en una orden de envío.';

-- Tabla 8: incidentes_bitacora
-- Pista de auditoría inalterable de liberaciones, bloqueos y retiros ejecutados por QA
CREATE TABLE incidentes_bitacora (
    incidente_id        SERIAL          PRIMARY KEY,
    folio_incidente     VARCHAR(30)     NOT NULL UNIQUE,
    lote_id             INTEGER         NOT NULL,
    usuario_responsable VARCHAR(60)     NOT NULL,
    motivo              VARCHAR(250)    NOT NULL,
    estado_previo       VARCHAR(20)     NOT NULL,
    nuevo_estado        VARCHAR(20)     NOT NULL,
    fecha_evento        TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_incidentes_lote
        FOREIGN KEY (lote_id) REFERENCES lotes(lote_id)
        ON DELETE RESTRICT,
    CONSTRAINT chk_incidentes_estado_previo_valido
        CHECK (estado_previo IN ('Cosechado', 'Recibido', 'En revision', 'Liberado', 'Bloqueado', 'Retirado')),
    CONSTRAINT chk_incidentes_nuevo_estado_valido
        CHECK (nuevo_estado IN ('Cosechado', 'Recibido', 'En revision', 'Liberado', 'Bloqueado', 'Retirado'))
);

COMMENT ON TABLE incidentes_bitacora IS 'Bitácora legal de cambios críticos de estado sanitario ejecutados por QA.';
COMMENT ON COLUMN incidentes_bitacora.folio_incidente IS 'Llave puente 1:1 hacia expedientes_incidentes en MongoDB.';

-- ============================================================================
-- 2. TABLA TÉCNICA DE ARQUITECTURA (PATRÓN OUTBOX / RECONCILIACIÓN)
-- ============================================================================

-- Tabla 9: eventos_reconciliacion
-- Registra operaciones pendientes o fallidas hacia MongoDB o Neo4j para consistencia eventual
CREATE TABLE eventos_reconciliacion (
    evento_id           SERIAL          PRIMARY KEY,
    destino_motor       VARCHAR(20)     NOT NULL,
    tipo_operacion      VARCHAR(50)     NOT NULL,
    llave_entidad       VARCHAR(40)     NOT NULL,
    payload_json        JSONB           NOT NULL,
    estado              VARCHAR(20)     NOT NULL DEFAULT 'PENDIENTE',
    intentos            INTEGER         NOT NULL DEFAULT 0,
    ultimo_error        TEXT            NULL,
    fecha_creacion      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_reconciliacion_destino_valido
        CHECK (destino_motor IN ('mongodb', 'neo4j')),
    CONSTRAINT chk_reconciliacion_estado_valido
        CHECK (estado IN ('PENDIENTE', 'PROCESADO', 'ERROR')),
    CONSTRAINT chk_reconciliacion_intentos_no_negativos
        CHECK (intentos >= 0)
);

COMMENT ON TABLE eventos_reconciliacion IS 'Tabla técnica outbox para reconciliar escrituras secundarias ante fallos parciales en MongoDB o Neo4j.';

-- ============================================================================
-- 3. ÍNDICES ESTRATÉGICOS (B-TREE)
-- ============================================================================

-- Índices sobre llaves foráneas y patrones de acceso frecuentes
CREATE INDEX idx_parcelas_productor        ON parcelas(productor_id);
CREATE INDEX idx_lotes_parcela             ON lotes(parcela_id);
CREATE INDEX idx_lotes_estado_producto     ON lotes(estado, producto);
CREATE INDEX idx_lotes_fecha_cosecha       ON lotes(fecha_cosecha);
CREATE INDEX idx_recepciones_temperatura   ON recepciones_cedis(temperatura_llegada_c);
CREATE INDEX idx_envios_tienda             ON envios(tienda_id);
CREATE INDEX idx_envios_fecha_estado       ON envios(fecha_despacho, estado_envio);
CREATE INDEX idx_envios_detalle_lote       ON envios_detalle(lote_id);
CREATE INDEX idx_incidentes_lote_fecha     ON incidentes_bitacora(lote_id, fecha_evento DESC);
CREATE INDEX idx_reconciliacion_pendientes ON eventos_reconciliacion(estado, fecha_creacion);

-- ============================================================================
-- 4. VISTAS OPERATIVAS
-- ============================================================================

-- Vista 1: Inventario disponible que cumple RN-01 y RN-03 (estado Liberado y saldo > 0)
CREATE VIEW v_lotes_listos_despacho AS
SELECT
    l.lote_id,
    l.codigo_lote,
    l.producto,
    l.fecha_cosecha,
    l.peso_inicial_kg,
    l.saldo_kg,
    pa.codigo_senasica,
    pa.nombre_huerta,
    pa.municipio,
    pr.nombre_razon_social AS productor
FROM lotes l
JOIN parcelas pa ON l.parcela_id = pa.parcela_id
JOIN productores pr ON pa.productor_id = pr.productor_id
WHERE l.estado = 'Liberado'
  AND l.saldo_kg > 0;

COMMENT ON VIEW v_lotes_listos_despacho IS 'Lotes con estado Liberado y saldo disponible en kg listos para ser surtidos por Almacén.';

-- Vista 2: Auditoría de cadena de frío (recepciones fuera del rango 4.0 a 8.0 °C en transporte)
CREATE VIEW v_auditoria_cadena_frio AS
SELECT
    l.codigo_lote,
    l.producto,
    l.estado AS estado_lote,
    r.folio_recepcion,
    r.fecha_llegada,
    r.temperatura_llegada_c,
    r.dictamen_recepcion,
    r.placas_vehiculo,
    r.codigo_cuarto_frio
FROM lotes l
JOIN recepciones_cedis r ON l.lote_id = r.lote_id
WHERE r.temperatura_llegada_c < 4.0
   OR r.temperatura_llegada_c > 8.0;

COMMENT ON VIEW v_auditoria_cadena_frio IS 'Detecta lotes cuya recepción en CEDIS registró temperaturas fuera del rango permitido (4.0 a 8.0 °C).';

-- ============================================================================
-- 5. USUARIO DEDICADO DE APLICACIÓN CON PRIVILEGIOS MÍNIMOS (PoLP)
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'trazaagro_app') THEN
        CREATE ROLE trazaagro_app WITH LOGIN PASSWORD 'trazaagro_app_pass';
    ELSE
        ALTER ROLE trazaagro_app WITH PASSWORD 'trazaagro_app_pass';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE trazaagro TO trazaagro_app;
GRANT USAGE ON SCHEMA public TO trazaagro_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO trazaagro_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO trazaagro_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO trazaagro_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO trazaagro_app;

COMMIT;
