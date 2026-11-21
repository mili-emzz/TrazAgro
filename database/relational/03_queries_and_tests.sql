-- ============================================================================
-- PROYECTO: TrazaAgro - Sistema de Trazabilidad de Alimentos Frescos
-- ENTREGABLE 4: Implementación de la Base de Datos Relacional (PostgreSQL)
-- ARCHIVO: 03_queries_and_tests.sql (Consultas representativas y pruebas ACID / Integridad)
-- ============================================================================

-- ============================================================================
-- PARTE 1: CONSULTAS REPRESENTATIVAS DEL DOMINIO
-- ============================================================================

-- 1.1 Consulta de inventario disponible para despacho (Vista v_lotes_listos_despacho)
-- Muestra únicamente lotes con estado = 'Liberado' y saldo_kg > 0 (RN-01 y RN-03)
SELECT
    codigo_lote,
    producto,
    peso_inicial_kg,
    saldo_kg,
    nombre_huerta,
    productor
FROM v_lotes_listos_despacho
ORDER BY fecha_cosecha ASC;

-- 1.2 Auditoría de cadena de frío en recepciones CEDIS (Vista v_auditoria_cadena_frio)
-- Detecta recepciones fuera del rango permitido de 4.0 a 8.0 °C (RN-07)
SELECT
    codigo_lote,
    folio_recepcion,
    temperatura_llegada_c,
    dictamen_recepcion,
    estado_lote,
    placas_vehiculo,
    codigo_cuarto_frio
FROM v_auditoria_cadena_frio;

-- 1.3 Cuadre contable de inventario por lote (peso_inicial_kg - saldo_kg = total_despachado_kg)
-- Verifica que ningún lote tenga descuadres entre su saldo actual y la suma de envíos activos
SELECT
    l.codigo_lote,
    l.estado,
    l.peso_inicial_kg AS cosechado_kg,
    l.saldo_kg,
    (l.peso_inicial_kg - l.saldo_kg) AS diferencia_inventario_kg,
    COALESCE(SUM(CASE WHEN e.estado_envio <> 'Cancelado' THEN ed.cantidad_kg ELSE 0 END), 0.00) AS total_despachado_kg,
    (l.peso_inicial_kg - l.saldo_kg) = COALESCE(SUM(CASE WHEN e.estado_envio <> 'Cancelado' THEN ed.cantidad_kg ELSE 0 END), 0.00) AS cuadre_exacto
FROM lotes l
LEFT JOIN envios_detalle ed ON l.lote_id = ed.lote_id
LEFT JOIN envios e ON ed.envio_id = e.envio_id
GROUP BY l.lote_id, l.codigo_lote, l.estado, l.peso_inicial_kg, l.saldo_kg
ORDER BY l.lote_id;

-- 1.4 Rastreabilidad administrativa de envíos y sucursales por lote
-- Identifica qué tiendas recibieron cajas del lote contaminado AGU-P014-260312-01 y cuántos kilos
SELECT
    l.codigo_lote,
    l.estado AS estado_actual_lote,
    e.codigo_envio,
    e.fecha_despacho,
    e.estado_envio,
    t.codigo_sucursal,
    t.nombre_comercial,
    t.ciudad,
    ed.cantidad_kg
FROM envios_detalle ed
JOIN lotes l ON ed.lote_id = l.lote_id
JOIN envios e ON ed.envio_id = e.envio_id
JOIN tiendas t ON e.tienda_id = t.tienda_id
WHERE l.codigo_lote = 'AGU-P014-260312-01'
ORDER BY e.fecha_despacho;

-- 1.5 Historial de bitácora de incidentes de QA por lote
-- Muestra la trazabilidad legal de quién liberó o bloqueó cada lote y por qué motivo (RN-04)
SELECT
    ib.folio_incidente,
    l.codigo_lote,
    ib.estado_previo,
    ib.nuevo_estado,
    ib.usuario_responsable,
    ib.fecha_evento,
    ib.motivo
FROM incidentes_bitacora ib
JOIN lotes l ON ib.lote_id = l.lote_id
ORDER BY ib.fecha_evento ASC;

-- 1.6 Verificación de seguridad sanitaria: detección de despachos posteriores a un bloqueo (RN-01)
-- Resultado esperado: 0 filas (ningún envío puede salir después de que el lote fue bloqueado)
SELECT
    l.codigo_lote,
    ib.folio_incidente,
    ib.fecha_evento AS fecha_bloqueo,
    e.codigo_envio,
    e.fecha_despacho
FROM lotes l
JOIN incidentes_bitacora ib ON l.lote_id = ib.lote_id
JOIN envios_detalle ed ON l.lote_id = ed.lote_id
JOIN envios e ON ed.envio_id = e.envio_id
WHERE ib.nuevo_estado IN ('Bloqueado', 'En revision', 'Retirado')
  AND e.estado_envio <> 'Cancelado'
  AND e.fecha_despacho > ib.fecha_evento;

-- ============================================================================
-- PARTE 2: PRUEBA DE TRANSACCIÓN ACID DE DESPACHO FRACCIONADO (CU-REL-03)
-- ============================================================================

-- Simula un despacho concurrente con SELECT ... FOR UPDATE sobre el lote AGU-P018-260316-01
-- Se ejecuta dentro de una transacción que verifica el descuento y aplica ROLLBACK al final
-- para mantener intacto el estado semilla reproducible.
BEGIN;

SELECT lote_id, codigo_lote, saldo_kg, estado
FROM lotes
WHERE codigo_lote = 'AGU-P018-260316-01'
FOR UPDATE;

UPDATE lotes
SET saldo_kg = saldo_kg - 300.00,
    fecha_actualizacion = CURRENT_TIMESTAMP
WHERE codigo_lote = 'AGU-P018-260316-01'
  AND estado = 'Liberado';

INSERT INTO envios (codigo_envio, tienda_id, placas_vehiculo, estado_envio)
VALUES ('ENV-2026-9999', 3, 'TRK-884-A', 'Preparado');

INSERT INTO envios_detalle (envio_id, lote_id, cantidad_kg)
VALUES (
    (SELECT envio_id FROM envios WHERE codigo_envio = 'ENV-2026-9999'),
    (SELECT lote_id FROM lotes WHERE codigo_lote = 'AGU-P018-260316-01'),
    300.00
);

-- Verificación dentro de la transacción: el saldo bajó de 2000.00 a 1700.00 kg
SELECT codigo_lote, peso_inicial_kg, saldo_kg, estado
FROM lotes
WHERE codigo_lote = 'AGU-P018-260316-01';

ROLLBACK;

-- ============================================================================
-- PARTE 3: PRUEBAS AUTOMATIZADAS DE INTEGRIDAD Y RESTRICCIONES (CASOS NEGATIVOS)
-- ============================================================================

-- Prueba 3.1: Intento de descontar más saldo del disponible (RN-03: chk_lotes_saldo_valido)
DO $$
BEGIN
    UPDATE lotes
    SET saldo_kg = -50.00
    WHERE codigo_lote = 'AGU-P018-260314-01';

    RAISE EXCEPTION 'FALLO: La base permitió un saldo_kg negativo.';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'PRUEBA 3.1 EXITOSA (RN-03): PostgreSQL rechazó saldo_kg negativo con check_violation (%).', SQLERRM;
END $$;

-- Prueba 3.2: Intento de asignar un saldo mayor al peso inicial cosechado (chk_lotes_saldo_valido)
DO $$
BEGIN
    UPDATE lotes
    SET saldo_kg = peso_inicial_kg + 100.00
    WHERE codigo_lote = 'AGU-P018-260314-01';

    RAISE EXCEPTION 'FALLO: La base permitió un saldo_kg superior al peso_inicial_kg.';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'PRUEBA 3.2 EXITOSA (RN-03): PostgreSQL rechazó saldo_kg > peso_inicial_kg (%).', SQLERRM;
END $$;

-- Prueba 3.3: Intento de registrar un estado inválido en lotes (chk_lotes_estado_valido)
DO $$
BEGIN
    UPDATE lotes
    SET estado = 'Destruido'
    WHERE codigo_lote = 'AGU-P014-260312-01';

    RAISE EXCEPTION 'FALLO: La base permitió un estado fuera del dominio.';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'PRUEBA 3.3 EXITOSA: PostgreSQL rechazó estado fuera del CHECK (%).', SQLERRM;
END $$;

-- Prueba 3.4: Intento de registrar una segunda recepción para un lote ya recibido (Relación 1:0..1)
DO $$
BEGIN
    INSERT INTO recepciones_cedis (
        folio_recepcion, lote_id, placas_vehiculo, codigo_cuarto_frio,
        peso_recibido_kg, temperatura_llegada_c, dictamen_recepcion
    ) VALUES (
        'REC-2026-DUPLICADA', 1, 'MICH-842-K', 'CF-02', 1900.00, 6.0, 'Conforme'
    );

    RAISE EXCEPTION 'FALLO: La base permitió dos recepciones para el mismo lote_id.';
EXCEPTION
    WHEN unique_violation THEN
        RAISE NOTICE 'PRUEBA 3.4 EXITOSA (1:0..1): PostgreSQL rechazó doble recepción para el mismo lote (%).', SQLERRM;
END $$;

-- Prueba 3.5: Intento de duplicar el mismo lote dentro del mismo envío (uq_envios_detalle_envio_lote)
DO $$
BEGIN
    INSERT INTO envios_detalle (envio_id, lote_id, cantidad_kg)
    VALUES (1, 1, 100.00);

    RAISE EXCEPTION 'FALLO: La base permitió duplicar el par (envio_id, lote_id).';
EXCEPTION
    WHEN unique_violation THEN
        RAISE NOTICE 'PRUEBA 3.5 EXITOSA: PostgreSQL rechazó línea duplicada (envio_id, lote_id) (%).', SQLERRM;
END $$;

-- Prueba 3.6: Intento de borrado físico de un productor o lote con historial (RN-10: ON DELETE RESTRICT)
DO $$
BEGIN
    DELETE FROM lotes WHERE codigo_lote = 'AGU-P014-260312-01';

    RAISE EXCEPTION 'FALLO: La base permitió eliminar físicamente un lote con recepciones, envíos e incidentes.';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'PRUEBA 3.6 EXITOSA (RN-10): PostgreSQL impidió el borrado físico del lote por ON DELETE RESTRICT (%).', SQLERRM;
END $$;
