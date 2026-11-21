// ============================================================================
// PROYECTO: TrazaAgro - Sistema de Trazabilidad de Alimentos Frescos
// ENTREGABLE 4: Implementación de la Base de Datos de Grafos (Neo4j)
// ARCHIVO: 03_queries_and_tests.cypher (Pruebas de humo, integridad, cardinalidad y consultas)
// ============================================================================

// ============================================================================
// PARTE 1: PRUEBAS DE HUMO (CONTEO DE NODOS Y RELACIONES)
// ============================================================================

// 1.1 Conteo de nodos por etiqueta
// Esperado: Productor(3), Parcela(4), Lote(6), Vehiculo(5), CuartoFrio(3), Laboratorio(2), Envio(4), Tienda(4) = 31 nodos
MATCH (n)
RETURN labels(n)[0] AS etiqueta, count(n) AS total_nodos
ORDER BY etiqueta;

// 1.2 Conteo de relaciones por tipo
// Esperado: PERTENECE_A(4), COSECHADO_EN(6), TRASLADADO_EN(5), ALMACENADO_EN(5),
//           EMITIO_ANALISIS(5), DIVIDIDO_EN(5), DESPACHADO_EN(4), ENTREGADO_A(4) = 38 relaciones
MATCH ()-[r]->()
RETURN type(r) AS tipo_relacion, count(r) AS total_relaciones
ORDER BY tipo_relacion;

// ============================================================================
// PARTE 2: PRUEBAS DE INTEGRIDAD Y CARDINALIDAD
// ============================================================================

// 2.1 Verificación RN-06: Todo :Lote debe conectarse exactamente a 1 :Parcela y 1 :Productor
// Resultado esperado: 0 filas (ningún lote incumple la cardinalidad 1:1 hacia su origen)
MATCH (l:Lote)
OPTIONAL MATCH (l)-[:COSECHADO_EN]->(pa:Parcela)-[:PERTENECE_A]->(pr:Productor)
WITH l, count(DISTINCT pa) AS num_parcelas, count(DISTINCT pr) AS num_productores
WHERE num_parcelas <> 1 OR num_productores <> 1
RETURN l.codigo_lote AS lote_invalido, num_parcelas, num_productores;

// 2.2 Verificación de cardinalidad de :Envio -> :Tienda (N:1) y :Envio -> :Vehiculo (N:1)
// Resultado esperado: 0 filas
MATCH (e:Envio)
OPTIONAL MATCH (e)-[:ENTREGADO_A]->(t:Tienda)
OPTIONAL MATCH (e)-[:DESPACHADO_EN]->(v:Vehiculo)
WITH e, count(DISTINCT t) AS num_tiendas, count(DISTINCT v) AS num_vehiculos
WHERE num_tiendas <> 1 OR num_vehiculos <> 1
RETURN e.codigo_envio AS envio_invalido, num_tiendas, num_vehiculos;

// 2.3 Verificación de consistencia de pesos en aristas [:DIVIDIDO_EN]
// La suma de cantidad_kg despachada nunca debe exceder peso_inicial_kg del lote
// Resultado esperado: 0 filas con exceso
MATCH (l:Lote)-[r:DIVIDIDO_EN]->(e:Envio)
WHERE e.estado_envio <> 'Cancelado'
WITH l, sum(r.cantidad_kg) AS total_despachado_kg
WHERE total_despachado_kg > l.peso_inicial_kg
RETURN l.codigo_lote, l.peso_inicial_kg, total_despachado_kg;

// 2.4 Detección de nodos operativos huérfanos (excluyendo catálogo inactivo RN-10 como SUC-QRO-01)
// Resultado esperado: 0 filas
MATCH (n)
WHERE NOT (n)--()
  AND coalesce(n.activo, true) = true
RETURN labels(n) AS etiquetas, properties(n) AS propiedades;

// ============================================================================
// PARTE 3: CONSULTAS FUNCIONALES DEL DOMINIO (CU-GRF-01 a CU-GRF-04)
// ============================================================================

// 3.1 CU-GRF-01 (Rastreo hacia adelante / Recall en N saltos)
// Dado el lote contaminado AGU-P014-260312-01, localizar todas las tiendas afectadas y kg exactos
MATCH (l:Lote {codigo_lote: 'AGU-P014-260312-01'})-[d:DIVIDIDO_EN]->(e:Envio)-[:ENTREGADO_A]->(t:Tienda)
OPTIONAL MATCH (e)-[:DESPACHADO_EN]->(v:Vehiculo)
RETURN l.codigo_lote AS lote_origen,
       l.estado AS estado_lote,
       e.codigo_envio AS envio,
       e.estado_envio AS estado_envio,
       v.placas AS unidad_reparto,
       t.codigo_sucursal AS sucursal,
       t.nombre_comercial AS tienda,
       t.ciudad AS ciudad,
       d.cantidad_kg AS kg_entregados
ORDER BY kg_entregados DESC;

// 3.2 CU-GRF-02 (Rastreo hacia atrás / Origen agronómico desde un envío o tienda)
// Dada una alerta en el envío ENV-2026-1052, caminar en reversa hasta huerta y productor
MATCH (t:Tienda)<-[:ENTREGADO_A]-(e:Envio {codigo_envio: 'ENV-2026-1052'})<-[d:DIVIDIDO_EN]-(l:Lote)
MATCH (l)-[c:COSECHADO_EN]->(pa:Parcela)-[:PERTENECE_A]->(pr:Productor)
RETURN e.codigo_envio AS envio,
       t.nombre_comercial AS tienda_destino,
       l.codigo_lote AS lote,
       d.cantidad_kg AS kg_en_envio,
       c.cuadrilla_cosecha AS cuadrilla,
       pa.codigo_senasica AS registro_senasica,
       pa.nombre_huerta AS huerta,
       pa.municipio AS municipio,
       pr.nombre_razon_social AS productor,
       pr.telefono AS telefono_emergencia;

// 3.3 CU-GRF-03 (Contaminación cruzada lateral - RN-08)
// Detectar lotes hermanos que compartieron camión refrigerado (:Vehiculo) o cámara (:CuartoFrio)
// con el lote bloqueado AGU-P014-260312-01
MATCH (lote_origen:Lote {codigo_lote: 'AGU-P014-260312-01'})-[r1:TRASLADADO_EN|ALMACENADO_EN]->(recurso)<-[r2:TRASLADADO_EN|ALMACENADO_EN]-(lote_hermano:Lote)
WHERE lote_origen <> lote_hermano
RETURN lote_origen.codigo_lote AS lote_contaminado,
       lote_hermano.codigo_lote AS lote_sospechoso,
       lote_hermano.estado AS estado_actual_hermano,
       labels(recurso)[0] AS tipo_recurso_compartido,
       coalesce(recurso.placas, recurso.codigo_cuarto_frio) AS identificador_recurso,
       type(r1) AS tipo_vinculo
ORDER BY lote_hermano.codigo_lote, tipo_recurso_compartido;

// 3.4 CU-GRF-04 (Detección de patrones por :Laboratorio)
// Analizar actividad de laboratorios, dictámenes No Conformes y versiones enmendadas
MATCH (lab:Laboratorio)-[a:EMITIO_ANALISIS]->(l:Lote)
RETURN lab.nombre AS laboratorio,
       lab.acreditacion_iso AS acreditacion,
       count(a) AS total_certificados,
       count(DISTINCT l) AS lotes_evaluados,
       sum(CASE WHEN a.dictamen_general = 'No Conforme' THEN 1 ELSE 0 END) AS dictamenes_no_conformes,
       sum(CASE WHEN a.es_vigente = false THEN 1 ELSE 0 END) AS versiones_enmendadas
ORDER BY dictamenes_no_conformes DESC;
