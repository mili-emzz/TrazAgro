from datetime import datetime
from typing import Any

from neo4j import Driver


def _serialize_neo4j_value(val: Any) -> Any:
    """Convierte tipos temporales de Neo4j a ISO-8601 para serialización JSON segura."""
    if hasattr(val, "iso_format"):
        return val.iso_format()
    if isinstance(val, dict):
        return {k: _serialize_neo4j_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_serialize_neo4j_value(v) for v in val]
    return val


class Neo4jRepository:
    """Repositorio de grafos con consultas Cypher 100% parametrizadas e idempotentes (MERGE)."""

    def __init__(self, driver: Driver) -> None:
        self.driver = driver

    # ------------------------------------------------------------------
    # Proyecciones de escritura idempotentes (MERGE)
    # ------------------------------------------------------------------
    def merge_lote_cosechado(
        self,
        *,
        codigo_lote: str,
        producto: str,
        fecha_cosecha: datetime,
        peso_inicial_kg: float,
        estado: str,
        cuadrilla_cosecha: str,
        parcela: dict[str, Any],
    ) -> None:
        cypher = """
            MERGE (pr:Productor {productor_id: $productor_id})
            SET pr.rfc = $rfc,
                pr.nombre_razon_social = $nombre_razon_social,
                pr.telefono = $telefono,
                pr.activo = $productor_activo
            MERGE (pa:Parcela {parcela_id: $parcela_id})
            SET pa.codigo_senasica = $codigo_senasica,
                pa.nombre_huerta = $nombre_huerta,
                pa.municipio = $municipio,
                pa.superficie_ha = $superficie_ha
            MERGE (pa)-[:PERTENECE_A]->(pr)
            MERGE (l:Lote {codigo_lote: $codigo_lote})
            SET l.producto = $producto,
                l.fecha_cosecha = datetime($fecha_cosecha),
                l.peso_inicial_kg = $peso_inicial_kg,
                l.estado = $estado
            MERGE (l)-[r:COSECHADO_EN]->(pa)
            SET r.cuadrilla_cosecha = $cuadrilla_cosecha,
                r.fecha_cosecha = datetime($fecha_cosecha)
        """
        params = {
            "productor_id": int(parcela["productor_id"]),
            "rfc": str(parcela["rfc"]),
            "nombre_razon_social": str(parcela["nombre_razon_social"]),
            "telefono": str(parcela["telefono"]),
            "productor_activo": bool(parcela["productor_activo"]),
            "parcela_id": int(parcela["parcela_id"]),
            "codigo_senasica": str(parcela["codigo_senasica"]),
            "nombre_huerta": str(parcela["nombre_huerta"]),
            "municipio": str(parcela["municipio"]),
            "superficie_ha": float(parcela["superficie_ha"]) if parcela.get("superficie_ha") is not None else None,
            "codigo_lote": codigo_lote,
            "producto": producto,
            "fecha_cosecha": fecha_cosecha.isoformat(),
            "peso_inicial_kg": float(peso_inicial_kg),
            "estado": estado,
            "cuadrilla_cosecha": cuadrilla_cosecha,
        }
        with self.driver.session() as session:
            session.run(cypher, params).consume()

    def merge_recepcion_fisica(
        self,
        *,
        codigo_lote: str,
        estado_lote: str,
        folio_recepcion: str,
        placas_vehiculo: str,
        codigo_cuarto_frio: str,
        nombre_chofer: str,
        peso_recibido_kg: float,
        temperatura_llegada_c: float,
        dictamen_recepcion: str,
        fecha_llegada: datetime,
    ) -> None:
        cypher = """
            MERGE (l:Lote {codigo_lote: $codigo_lote})
            SET l.estado = $estado_lote
            MERGE (v:Vehiculo {placas: $placas_vehiculo})
            MERGE (cf:CuartoFrio {codigo_cuarto_frio: $codigo_cuarto_frio})
            MERGE (l)-[t:TRASLADADO_EN {folio_recepcion: $folio_recepcion}]->(v)
            SET t.fecha_llegada = datetime($fecha_llegada),
                t.nombre_chofer = $nombre_chofer,
                t.peso_recibido_kg = $peso_recibido_kg,
                t.temperatura_llegada_c = $temperatura_llegada_c
            MERGE (l)-[a:ALMACENADO_EN {folio_recepcion: $folio_recepcion}]->(cf)
            SET a.fecha_ingreso = datetime($fecha_llegada),
                a.dictamen_recepcion = $dictamen_recepcion
        """
        params = {
            "codigo_lote": codigo_lote,
            "estado_lote": estado_lote,
            "folio_recepcion": folio_recepcion,
            "placas_vehiculo": placas_vehiculo,
            "codigo_cuarto_frio": codigo_cuarto_frio,
            "nombre_chofer": nombre_chofer,
            "peso_recibido_kg": float(peso_recibido_kg),
            "temperatura_llegada_c": float(temperatura_llegada_c),
            "dictamen_recepcion": dictamen_recepcion,
            "fecha_llegada": fecha_llegada.isoformat(),
        }
        with self.driver.session() as session:
            session.run(cypher, params).consume()

    def merge_analisis_proyeccion(
        self,
        *,
        codigo_lote: str,
        acreditacion_iso: str,
        nombre_laboratorio: str,
        folio_analisis: str,
        tipo_estudio: str,
        dictamen_general: str,
        fecha_emision: datetime,
        folio_reemplazado: str | None = None,
    ) -> None:
        cypher = """
            MERGE (lab:Laboratorio {acreditacion_iso: $acreditacion_iso})
            SET lab.nombre = $nombre_laboratorio
            MERGE (l:Lote {codigo_lote: $codigo_lote})
            MERGE (lab)-[r:EMITIO_ANALISIS {folio_analisis: $folio_analisis}]->(l)
            SET r.tipo_estudio = $tipo_estudio,
                r.dictamen_general = $dictamen_general,
                r.fecha_emision = datetime($fecha_emision),
                r.es_vigente = true
        """
        params = {
            "acreditacion_iso": acreditacion_iso,
            "nombre_laboratorio": nombre_laboratorio,
            "codigo_lote": codigo_lote,
            "folio_analisis": folio_analisis,
            "tipo_estudio": tipo_estudio,
            "dictamen_general": dictamen_general,
            "fecha_emision": fecha_emision.isoformat(),
        }
        with self.driver.session() as session:
            if folio_reemplazado:
                session.run(
                    """
                    MATCH ()-[prev:EMITIO_ANALISIS {folio_analisis: $folio_reemplazado}]->(:Lote {codigo_lote: $codigo_lote})
                    SET prev.es_vigente = false
                    """,
                    {"folio_reemplazado": folio_reemplazado, "codigo_lote": codigo_lote},
                ).consume()
            session.run(cypher, params).consume()

    def merge_envio_proyeccion(
        self,
        *,
        codigo_envio: str,
        estado_envio: str,
        fecha_despacho: datetime,
        placas_vehiculo: str,
        nombre_chofer: str,
        tienda: dict[str, Any],
        detalles: list[dict[str, Any]],
    ) -> None:
        cypher = """
            MERGE (e:Envio {codigo_envio: $codigo_envio})
            SET e.estado_envio = $estado_envio,
                e.fecha_despacho = datetime($fecha_despacho)
            MERGE (v:Vehiculo {placas: $placas_vehiculo})
            MERGE (e)-[d:DESPACHADO_EN]->(v)
            SET d.fecha_despacho = datetime($fecha_despacho),
                d.nombre_chofer = $nombre_chofer
            MERGE (t:Tienda {tienda_id: $tienda_id})
            SET t.codigo_sucursal = $codigo_sucursal,
                t.nombre_comercial = $nombre_comercial,
                t.direccion = $direccion,
                t.ciudad = $ciudad,
                t.activo = $tienda_activo
            MERGE (e)-[:ENTREGADO_A]->(t)
            WITH e
            UNWIND $detalles AS det
            MERGE (l:Lote {codigo_lote: det.codigo_lote})
            MERGE (l)-[div:DIVIDIDO_EN]->(e)
            SET div.cantidad_kg = toFloat(det.cantidad_kg)
        """
        params = {
            "codigo_envio": codigo_envio,
            "estado_envio": estado_envio,
            "fecha_despacho": fecha_despacho.isoformat(),
            "placas_vehiculo": placas_vehiculo,
            "nombre_chofer": nombre_chofer,
            "tienda_id": int(tienda["tienda_id"]),
            "codigo_sucursal": str(tienda["codigo_sucursal"]),
            "nombre_comercial": str(tienda["nombre_comercial"]),
            "direccion": str(tienda.get("direccion", "")),
            "ciudad": str(tienda.get("ciudad", "")),
            "tienda_activo": bool(tienda.get("activo", True)),
            "detalles": detalles,
        }
        with self.driver.session() as session:
            session.run(cypher, params).consume()

    def update_lotes_estado(self, codigos_lotes: list[str], nuevo_estado: str) -> None:
        if not codigos_lotes:
            return
        cypher = """
            UNWIND $codigos AS codigo
            MERGE (l:Lote {codigo_lote: codigo})
            SET l.estado = $nuevo_estado
        """
        with self.driver.session() as session:
            session.run(
                cypher,
                {"codigos": codigos_lotes, "nuevo_estado": nuevo_estado},
            ).consume()

    # ------------------------------------------------------------------
    # Consultas de trazabilidad (Forward, Backward, Lateral y 360°)
    # ------------------------------------------------------------------
    def rastreo_adelante(self, codigo_lote: str) -> list[dict[str, Any]]:
        """OP-N4J-01: Envios, vehículos de reparto y tiendas alcanzadas por un lote."""
        cypher = """
            MATCH (l:Lote {codigo_lote: $codigo_lote})-[div:DIVIDIDO_EN]->(e:Envio)-[ent:ENTREGADO_A]->(t:Tienda)
            OPTIONAL MATCH (e)-[desp:DESPACHADO_EN]->(v:Vehiculo)
            RETURN
                t.tienda_id AS tienda_id,
                t.codigo_sucursal AS codigo_sucursal,
                t.nombre_comercial AS nombre_comercial,
                t.ciudad AS ciudad,
                e.codigo_envio AS codigo_envio,
                e.estado_envio AS estado_envio,
                e.fecha_despacho AS fecha_despacho,
                div.cantidad_kg AS cantidad_kg,
                v.placas AS placas_vehiculo,
                desp.nombre_chofer AS nombre_chofer,
                ent.fecha_entrega AS fecha_entrega
            ORDER BY e.fecha_despacho ASC
        """
        with self.driver.session() as session:
            result = session.run(cypher, {"codigo_lote": codigo_lote})
            return [_serialize_neo4j_value(dict(rec)) for rec in result]

    def rastreo_atras(self, codigo_lote: str) -> dict[str, Any] | None:
        """Origen agrícola del lote: Parcela y Productor."""
        cypher = """
            MATCH (l:Lote {codigo_lote: $codigo_lote})-[c:COSECHADO_EN]->(pa:Parcela)-[:PERTENECE_A]->(pr:Productor)
            RETURN
                l.codigo_lote AS codigo_lote,
                l.estado AS estado,
                c.cuadrilla_cosecha AS cuadrilla_cosecha,
                c.fecha_cosecha AS fecha_cosecha,
                pa.parcela_id AS parcela_id,
                pa.codigo_senasica AS codigo_senasica,
                pa.nombre_huerta AS nombre_huerta,
                pa.municipio AS municipio,
                pr.productor_id AS productor_id,
                pr.rfc AS rfc,
                pr.nombre_razon_social AS nombre_razon_social
        """
        with self.driver.session() as session:
            rec = session.run(cypher, {"codigo_lote": codigo_lote}).single()
            return _serialize_neo4j_value(dict(rec)) if rec else None

    def rastreo_lateral(
        self,
        codigo_lote: str,
        ventana_dias: int = 1,
    ) -> list[dict[str, Any]]:
        """OP-N4J-02: Detección de lotes hermanos que compartieron vehículo o cuarto frío (RN-08)."""
        cypher = """
            MATCH (origen:Lote {codigo_lote: $codigo_lote})-[r1:TRASLADADO_EN|ALMACENADO_EN]->(recurso)<-[r2:TRASLADADO_EN|ALMACENADO_EN]-(hermano:Lote)
            WHERE hermano.codigo_lote <> origen.codigo_lote
              AND (
                r1.fecha_llegada IS NULL OR r2.fecha_llegada IS NULL
                OR abs(duration.inDays(r1.fecha_llegada, r2.fecha_llegada).days) <= $ventana_dias
              )
              AND (
                r1.fecha_ingreso IS NULL OR r2.fecha_ingreso IS NULL
                OR abs(duration.inDays(r1.fecha_ingreso, r2.fecha_ingreso).days) <= $ventana_dias
              )
            RETURN DISTINCT
                hermano.codigo_lote AS codigo_lote,
                hermano.estado AS estado,
                CASE
                    WHEN recurso:Vehiculo THEN 'Vehículo ' + recurso.placas
                    WHEN recurso:CuartoFrio THEN 'Cuarto Frío ' + recurso.codigo_cuarto_frio
                    ELSE 'Recurso compartido'
                END AS causa_vinculo,
                labels(recurso)[0] AS tipo_recurso,
                coalesce(recurso.placas, recurso.codigo_cuarto_frio) AS identificador_recurso
            ORDER BY hermano.codigo_lote ASC
        """
        with self.driver.session() as session:
            result = session.run(
                cypher,
                {"codigo_lote": codigo_lote, "ventana_dias": int(ventana_dias)},
            )
            return [_serialize_neo4j_value(dict(rec)) for rec in result]

    def get_red_lote_360(self, codigo_lote: str) -> dict[str, Any]:
        """Obtiene el contexto topológico completo del lote para el Expediente 360°."""
        cypher_logistica = """
            MATCH (l:Lote {codigo_lote: $codigo_lote})
            OPTIONAL MATCH (l)-[t:TRASLADADO_EN]->(v:Vehiculo)
            OPTIONAL MATCH (l)-[a:ALMACENADO_EN]->(cf:CuartoFrio)
            RETURN
                v.placas AS vehiculo_entrada,
                t.nombre_chofer AS chofer_entrada,
                t.temperatura_llegada_c AS temperatura_llegada_c,
                cf.codigo_cuarto_frio AS codigo_cuarto_frio,
                cf.nombre_cuarto AS nombre_cuarto
            LIMIT 1
        """
        cypher_labs = """
            MATCH (lab:Laboratorio)-[r:EMITIO_ANALISIS]->(l:Lote {codigo_lote: $codigo_lote})
            RETURN
                lab.nombre AS laboratorio,
                lab.acreditacion_iso AS acreditacion_iso,
                r.folio_analisis AS folio_analisis,
                r.tipo_estudio AS tipo_estudio,
                r.dictamen_general AS dictamen_general,
                r.es_vigente AS es_vigente,
                r.fecha_emision AS fecha_emision
            ORDER BY r.fecha_emision DESC
        """
        with self.driver.session() as session:
            log_rec = session.run(cypher_logistica, {"codigo_lote": codigo_lote}).single()
            labs_res = session.run(cypher_labs, {"codigo_lote": codigo_lote})
            laboratorios = [_serialize_neo4j_value(dict(r)) for r in labs_res]

        return {
            "logistica_entrada": _serialize_neo4j_value(dict(log_rec)) if log_rec else None,
            "laboratorios": laboratorios,
            "envios_tiendas": self.rastreo_adelante(codigo_lote),
            "lotes_hermanos": self.rastreo_lateral(codigo_lote, ventana_dias=1),
        }
