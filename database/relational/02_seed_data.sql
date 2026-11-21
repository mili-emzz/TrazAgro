-- ============================================================================
-- PROYECTO: TrazaAgro - Sistema de Trazabilidad de Alimentos Frescos
-- ENTREGABLE 4: Implementación de la Base de Datos Relacional (PostgreSQL)
-- ARCHIVO: 02_seed_data.sql (Carga reproducible de datos semilla coherentes)
-- ============================================================================

BEGIN;

-- Limpieza previa de datos conservando estructura
TRUNCATE TABLE
    eventos_reconciliacion,
    incidentes_bitacora,
    envios_detalle,
    envios,
    tiendas,
    recepciones_cedis,
    lotes,
    parcelas,
    productores
RESTART IDENTITY CASCADE;

-- ============================================================================
-- 1. PRODUCTORES (3 registros: 2 activos y 1 inactivo por RN-10)
-- ============================================================================
INSERT INTO productores (productor_id, rfc, nombre_razon_social, telefono, activo) VALUES
(1, 'AUM180412H59', 'Aguacateros Unidos de Michoacán S.P.R. de R.L.', '452-523-8810', TRUE),
(2, 'HTI200905M14', 'Huertas del Tancítaro S.A. de C.V.',             '452-519-4402', TRUE),
(3, 'ASP150219K81', 'Agroexportadora San Pedro S.A. de C.V.',         '341-412-9077', FALSE);

-- ============================================================================
-- 2. PARCELAS (4 huertas con registro fitosanitario SENASICA)
-- ============================================================================
INSERT INTO parcelas (parcela_id, productor_id, codigo_senasica, nombre_huerta, municipio, superficie_ha) VALUES
(1, 1, 'SENASICA-MICH-URU-014', 'Huerta La Escondida', 'Uruapan, Michoacán',           18.50),
(2, 1, 'SENASICA-MICH-PER-015', 'Huerta El Mirador',   'Peribán, Michoacán',           24.00),
(3, 2, 'SENASICA-MICH-TAN-018', 'Huerta Los Pinos',    'Tancítaro, Michoacán',         32.75),
(4, 3, 'SENASICA-JAL-ZAP-022',  'Huerta Santa Rosa',   'Zapotlán el Grande, Jalisco',  12.00);

-- ============================================================================
-- 3. LOTES (6 lotes que cubren todos los escenarios operativos y de recall)
-- ============================================================================
INSERT INTO lotes (
    lote_id, codigo_lote, parcela_id, producto, fecha_cosecha,
    cuadrilla_cosecha, peso_inicial_kg, saldo_kg, estado, fecha_actualizacion
) VALUES
-- Lote 1: Despachado parcialmente (850 kg) y luego BLOQUEADO por plaguicida Clorpirifos No Conforme
(1, 'AGU-P014-260312-01', 1, 'Aguacate Hass', '2026-03-12 07:30:00',
    'Cuadrilla Alfa-01', 2000.00, 1150.00, 'Bloqueado', '2026-03-13 17:10:00'),

-- Lote 2: Lote hermano BLOQUEADO preventivamente (RN-08) por compartir camión MICH-842-K y cuarto frío CF-02
(2, 'AGU-P014-260312-02', 1, 'Aguacate Hass', '2026-03-12 09:00:00',
    'Cuadrilla Alfa-02', 1500.00, 1500.00, 'Bloqueado', '2026-03-13 17:12:00'),

-- Lote 3: LIBERADO tras enmienda V2 de laboratorio (RN-05), despachado parcialmente (950 kg) y con saldo disponible
(3, 'AGU-P018-260314-01', 3, 'Aguacate Hass', '2026-03-14 06:45:00',
    'Cuadrilla Tancítaro-03', 3000.00, 2050.00, 'Liberado', '2026-03-16 08:30:00'),

-- Lote 4: EN REVISION por ruptura de cadena de frío en recepción (11.4 °C > 8.0 °C, RN-07)
(4, 'AGU-P015-260315-01', 2, 'Aguacate Hass', '2026-03-15 08:00:00',
    'Cuadrilla Beta-01', 1800.00, 1800.00, 'En revision', '2026-03-15 16:25:00'),

-- Lote 5: LIBERADO con amplio saldo disponible (2000 kg restantes) para despachos
(5, 'AGU-P018-260316-01', 3, 'Aguacate Hass', '2026-03-16 07:15:00',
    'Cuadrilla Tancítaro-01', 2200.00, 2000.00, 'Liberado', '2026-03-16 08:30:00'),

-- Lote 6: COSECHADO en huerta, aún en tránsito hacia el CEDIS (demuestra relación 1:0..1 con recepciones)
(6, 'AGU-P014-260318-01', 1, 'Aguacate Hass', '2026-03-18 07:00:00',
    'Cuadrilla Alfa-01', 1600.00, 1600.00, 'Cosechado', '2026-03-18 07:00:00');

-- ============================================================================
-- 4. RECEPCIONES EN CEDIS (5 recepciones para los lotes 1 al 5)
-- ============================================================================
INSERT INTO recepciones_cedis (
    recepcion_id, folio_recepcion, lote_id, fecha_llegada,
    placas_vehiculo, codigo_cuarto_frio, peso_recibido_kg, temperatura_llegada_c, dictamen_recepcion
) VALUES
(1, 'REC-2026-0104', 1, '2026-03-12 18:15:00', 'MICH-842-K', 'CF-02', 1995.00,  5.9, 'Conforme'),
(2, 'REC-2026-0105', 2, '2026-03-12 18:40:00', 'MICH-842-K', 'CF-02', 1498.50,  6.1, 'Conforme'),
(3, 'REC-2026-0106', 3, '2026-03-14 17:20:00', 'MICH-910-B', 'CF-01', 2992.00,  5.5, 'Conforme'),
(4, 'REC-2026-0107', 4, '2026-03-15 16:20:00', 'JAL-405-C',  'CF-03', 1796.00, 11.4, 'Retenido'),
(5, 'REC-2026-0108', 5, '2026-03-16 15:10:00', 'MICH-910-B', 'CF-01', 2198.00,  5.8, 'Conforme');

-- ============================================================================
-- 5. TIENDAS (4 sucursales destino: 3 activas y 1 inactiva por RN-10)
-- ============================================================================
INSERT INTO tiendas (tienda_id, codigo_sucursal, nombre_comercial, direccion, ciudad, activo) VALUES
(1, 'SUC-MTY-04',  'Supermercados del Norte - Valle', 'Av. Vasconcelos 345, Col. Del Valle', 'Monterrey, N.L.',    TRUE),
(2, 'SUC-CDMX-01', 'Selecto Chedraui - Polanco',      'Av. Moliere 222, Col. Polanco',       'Ciudad de México',   TRUE),
(3, 'SUC-GDL-02',  'Fresko La Comer - Providencia',   'Av. Rubén Darío 1109, Providencia',   'Guadalajara, Jal.',  TRUE),
(4, 'SUC-QRO-01',  'Distribución Horeca Bajío',       'Blvd. Bernardo Quintana 4100',        'Querétaro, Qro.',    FALSE);

-- ============================================================================
-- 6. ENVÍOS (4 órdenes de despacho desde el CEDIS)
-- ============================================================================
INSERT INTO envios (envio_id, codigo_envio, tienda_id, placas_vehiculo, fecha_despacho, estado_envio) VALUES
-- Envíos 1 y 2 salieron el 13 de marzo por la mañana (antes de que llegara el análisis de plaguicidas No Conforme a las 16:45)
(1, 'ENV-2026-1052', 1, 'TRK-884-A', '2026-03-13 09:00:00', 'Entregado'),
(2, 'ENV-2026-1053', 2, 'TRK-902-C', '2026-03-13 10:30:00', 'Entregado'),
-- Envío 3 del Lote 3 hacia Guadalajara
(3, 'ENV-2026-1054', 3, 'TRK-884-A', '2026-03-15 14:00:00', 'Entregado'),
-- Envío 4 consolidado (mezcla cajas del Lote 3 y del Lote 5 hacia Monterrey)
(4, 'ENV-2026-1055', 1, 'TRK-902-C', '2026-03-16 08:30:00', 'En transito');

-- ============================================================================
-- 7. DETALLE DE ENVÍOS (Fraccionamiento exacto que cuadra con peso_inicial - saldo)
-- ============================================================================
INSERT INTO envios_detalle (detalle_id, envio_id, lote_id, cantidad_kg) VALUES
-- Lote 1: 450 + 400 = 850 kg despachados (2000 - 850 = 1150 kg de saldo)
(1, 1, 1, 450.00),
(2, 2, 1, 400.00),
-- Lote 3: 600 + 350 = 950 kg despachados (3000 - 950 = 2050 kg de saldo)
(3, 3, 3, 600.00),
(4, 4, 3, 350.00),
-- Lote 5: 200 kg despachados en el envío consolidado ENV-2026-1055 (2200 - 200 = 2000 kg de saldo)
(5, 4, 5, 200.00);

-- ============================================================================
-- 8. BITÁCORA DE INCIDENTES Y CAMBIOS DE ESTADO DE QA
-- ============================================================================
INSERT INTO incidentes_bitacora (
    incidente_id, folio_incidente, lote_id, usuario_responsable,
    motivo, estado_previo, nuevo_estado, fecha_evento
) VALUES
(1, 'INC-2026-0011', 1, 'Ing. Laura Méndez (QA)',
    'Liberación inicial tras certificado microbiológico y de materia seca LAB-2026-AGU-0845-V1 Conforme.',
    'Recibido', 'Liberado', '2026-03-13 08:00:00'),

(2, 'INC-2026-0012', 1, 'Ing. Laura Méndez (QA)',
    'Bloqueo de emergencia y activación de Recall por residuo de Clorpirifos (0.08 mg/kg) en certificado LAB-2026-AGU-0842-V1.',
    'Liberado', 'Bloqueado', '2026-03-13 17:10:00'),

(3, 'INC-2026-0013', 2, 'Ing. Laura Méndez (QA)',
    'Bloqueo preventivo por contaminación cruzada lateral (RN-08): compartió unidad MICH-842-K y cuarto frío CF-02 con lote AGU-P014-260312-01.',
    'Recibido', 'Bloqueado', '2026-03-13 17:12:00'),

(4, 'INC-2026-0014', 3, 'Ing. Laura Méndez (QA)',
    'Liberación autorizada tras certificado enmendado LAB-2026-AGU-0910-V2 Conforme para Abamectina.',
    'Recibido', 'Liberado', '2026-03-15 11:45:00'),

(5, 'INC-2026-0015', 4, 'Sistema Automático / Carlos Mendoza (Recepción)',
    'Retención automática por ruptura de cadena de frío en arribo REC-2026-0107 (11.4 °C excede límite de 8.0 °C, RN-07).',
    'Cosechado', 'En revision', '2026-03-15 16:25:00'),

(6, 'INC-2026-0016', 5, 'Ing. Laura Méndez (QA)',
    'Liberación sanitaria tras análisis multirresiduos LAB-2026-AGU-0925-V1 Conforme.',
    'Recibido', 'Liberado', '2026-03-16 08:00:00');

-- ============================================================================
-- 9. EVENTOS DE RECONCILIACIÓN (Evidencia de patrón Outbox inter-motores)
-- ============================================================================
INSERT INTO eventos_reconciliacion (
    evento_id, destino_motor, tipo_operacion, llave_entidad,
    payload_json, estado, intentos, ultimo_error, fecha_creacion, fecha_actualizacion
) VALUES
(1, 'neo4j', 'SYNC_BLOQUEO_LOTE', 'AGU-P014-260312-01',
    '{"codigo_lote": "AGU-P014-260312-01", "nuevo_estado": "Bloqueado", "folio_incidente": "INC-2026-0012"}'::jsonb,
    'PROCESADO', 1, NULL, '2026-03-13 17:10:02', '2026-03-13 17:10:03'),

(2, 'mongodb', 'ACTUALIZAR_EXPEDIENTE_RECALL', 'INC-2026-0012',
    '{"folio_incidente": "INC-2026-0012", "lotes_afectados": ["AGU-P014-260312-01", "AGU-P014-260312-02"]}'::jsonb,
    'PROCESADO', 1, NULL, '2026-03-13 17:12:05', '2026-03-13 17:12:06');

-- Sincronización de secuencias SERIAL tras inserción con IDs explícitos
SELECT setval(pg_get_serial_sequence('productores', 'productor_id'), (SELECT MAX(productor_id) FROM productores));
SELECT setval(pg_get_serial_sequence('parcelas', 'parcela_id'), (SELECT MAX(parcela_id) FROM parcelas));
SELECT setval(pg_get_serial_sequence('lotes', 'lote_id'), (SELECT MAX(lote_id) FROM lotes));
SELECT setval(pg_get_serial_sequence('recepciones_cedis', 'recepcion_id'), (SELECT MAX(recepcion_id) FROM recepciones_cedis));
SELECT setval(pg_get_serial_sequence('tiendas', 'tienda_id'), (SELECT MAX(tienda_id) FROM tiendas));
SELECT setval(pg_get_serial_sequence('envios', 'envio_id'), (SELECT MAX(envio_id) FROM envios));
SELECT setval(pg_get_serial_sequence('envios_detalle', 'detalle_id'), (SELECT MAX(detalle_id) FROM envios_detalle));
SELECT setval(pg_get_serial_sequence('incidentes_bitacora', 'incidente_id'), (SELECT MAX(incidente_id) FROM incidentes_bitacora));
SELECT setval(pg_get_serial_sequence('eventos_reconciliacion', 'evento_id'), (SELECT MAX(evento_id) FROM eventos_reconciliacion));

COMMIT;
