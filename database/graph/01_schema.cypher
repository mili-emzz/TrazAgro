// ============================================================================
// PROYECTO: TrazaAgro - Sistema de Trazabilidad de Alimentos Frescos
// ENTREGABLE 4: Implementación de la Base de Datos de Grafos (Neo4j)
// ARCHIVO: 01_schema.cypher (Restricciones de unicidad e índices por etiqueta)
// ============================================================================

// Restricciones de unicidad (Constraints) para las 8 etiquetas de nodo
CREATE CONSTRAINT productor_id_unique IF NOT EXISTS
FOR (p:Productor) REQUIRE p.productor_id IS UNIQUE;

CREATE CONSTRAINT productor_rfc_unique IF NOT EXISTS
FOR (p:Productor) REQUIRE p.rfc IS UNIQUE;

CREATE CONSTRAINT parcela_id_unique IF NOT EXISTS
FOR (pa:Parcela) REQUIRE pa.parcela_id IS UNIQUE;

CREATE CONSTRAINT parcela_senasica_unique IF NOT EXISTS
FOR (pa:Parcela) REQUIRE pa.codigo_senasica IS UNIQUE;

CREATE CONSTRAINT lote_codigo_unique IF NOT EXISTS
FOR (l:Lote) REQUIRE l.codigo_lote IS UNIQUE;

CREATE CONSTRAINT vehiculo_placas_unique IF NOT EXISTS
FOR (v:Vehiculo) REQUIRE v.placas IS UNIQUE;

CREATE CONSTRAINT cuarto_codigo_unique IF NOT EXISTS
FOR (c:CuartoFrio) REQUIRE c.codigo_cuarto_frio IS UNIQUE;

CREATE CONSTRAINT laboratorio_iso_unique IF NOT EXISTS
FOR (lab:Laboratorio) REQUIRE lab.acreditacion_iso IS UNIQUE;

CREATE CONSTRAINT envio_codigo_unique IF NOT EXISTS
FOR (e:Envio) REQUIRE e.codigo_envio IS UNIQUE;

CREATE CONSTRAINT tienda_id_unique IF NOT EXISTS
FOR (t:Tienda) REQUIRE t.tienda_id IS UNIQUE;

CREATE CONSTRAINT tienda_sucursal_unique IF NOT EXISTS
FOR (t:Tienda) REQUIRE t.codigo_sucursal IS UNIQUE;

// Índices de búsqueda rápida para alertas sanitarias y segmentación geográfica
CREATE INDEX lote_estado_idx IF NOT EXISTS
FOR (l:Lote) ON (l.estado);

CREATE INDEX tienda_ciudad_idx IF NOT EXISTS
FOR (t:Tienda) ON (t.ciudad);
