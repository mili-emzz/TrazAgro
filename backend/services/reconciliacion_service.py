from datetime import datetime
import logging
from typing import Any

from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository

logger = logging.getLogger("trazaagro.reconciliacion")


def _parse_dt(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val
    return datetime.fromisoformat(str(val))


class ReconciliacionService:
    """Gestiona el patrón Outbox ligero (eventos_reconciliacion) para consistencia eventual."""

    def __init__(
        self,
        pg_repo: PostgresRepository,
        mongo_repo: MongoRepository,
        neo4j_repo: Neo4jRepository,
    ) -> None:
        self.pg_repo = pg_repo
        self.mongo_repo = mongo_repo
        self.neo4j_repo = neo4j_repo

    def registrar_pendiente(
        self,
        *,
        destino_motor: str,
        tipo_operacion: str,
        llave_entidad: str,
        payload: dict[str, Any],
        error: Exception,
    ) -> int:
        logger.warning(
            "Fallo secundario en %s (%s / %s): %s. Registrando en eventos_reconciliacion.",
            destino_motor,
            tipo_operacion,
            llave_entidad,
            error,
        )
        return self.pg_repo.insert_reconciliation_event(
            destino_motor=destino_motor,
            tipo_operacion=tipo_operacion,
            llave_entidad=llave_entidad,
            payload=payload,
            ultimo_error=str(error),
        )

    def ejecutar_pendientes(self, limit: int = 50) -> dict[str, Any]:
        pendientes = self.pg_repo.get_pending_reconciliation_events(limit=limit)
        procesados = 0
        fallidos = 0
        detalle: list[dict[str, Any]] = []

        for ev in pendientes:
            evento_id = ev["evento_id"]
            op = ev["tipo_operacion"]
            payload = ev["payload_json"]
            try:
                self._replay_event(ev["destino_motor"], op, payload)
                self.pg_repo.mark_reconciliation_event(
                    evento_id=evento_id,
                    estado="PROCESADO",
                    ultimo_error=None,
                )
                procesados += 1
                detalle.append({"evento_id": evento_id, "tipo_operacion": op, "estado": "PROCESADO"})
            except Exception as exc:
                self.pg_repo.mark_reconciliation_event(
                    evento_id=evento_id,
                    estado="ERROR",
                    ultimo_error=str(exc),
                )
                fallidos += 1
                detalle.append(
                    {
                        "evento_id": evento_id,
                        "tipo_operacion": op,
                        "estado": "ERROR",
                        "error": str(exc)[:200],
                    }
                )

        return {
            "total_pendientes": len(pendientes),
            "procesados": procesados,
            "fallidos": fallidos,
            "detalle": detalle,
        }

    def _replay_event(self, destino: str, op: str, payload: dict[str, Any]) -> None:
        if destino == "neo4j":
            if op == "MERGE_LOTE":
                self.neo4j_repo.merge_lote_cosechado(
                    codigo_lote=payload["codigo_lote"],
                    producto=payload["producto"],
                    fecha_cosecha=_parse_dt(payload["fecha_cosecha"]),
                    peso_inicial_kg=payload["peso_inicial_kg"],
                    estado=payload["estado"],
                    cuadrilla_cosecha=payload["cuadrilla_cosecha"],
                    parcela=payload["parcela"],
                )
            elif op == "MERGE_RECEPCION":
                self.neo4j_repo.merge_recepcion_fisica(
                    codigo_lote=payload["codigo_lote"],
                    estado_lote=payload["estado_lote"],
                    folio_recepcion=payload["folio_recepcion"],
                    placas_vehiculo=payload["placas_vehiculo"],
                    codigo_cuarto_frio=payload["codigo_cuarto_frio"],
                    nombre_chofer=payload["nombre_chofer"],
                    peso_recibido_kg=payload["peso_recibido_kg"],
                    temperatura_llegada_c=payload["temperatura_llegada_c"],
                    dictamen_recepcion=payload["dictamen_recepcion"],
                    fecha_llegada=_parse_dt(payload["fecha_llegada"]),
                )
            elif op == "MERGE_ANALISIS":
                self.neo4j_repo.merge_analisis_proyeccion(
                    codigo_lote=payload["codigo_lote"],
                    acreditacion_iso=payload["acreditacion_iso"],
                    nombre_laboratorio=payload["nombre_laboratorio"],
                    folio_analisis=payload["folio_analisis"],
                    tipo_estudio=payload["tipo_estudio"],
                    dictamen_general=payload["dictamen_general"],
                    fecha_emision=_parse_dt(payload["fecha_emision"]),
                    folio_reemplazado=payload.get("folio_reemplazado"),
                )
            elif op == "MERGE_ENVIO":
                self.neo4j_repo.merge_envio_proyeccion(
                    codigo_envio=payload["codigo_envio"],
                    estado_envio=payload["estado_envio"],
                    fecha_despacho=_parse_dt(payload["fecha_despacho"]),
                    placas_vehiculo=payload["placas_vehiculo"],
                    nombre_chofer=payload["nombre_chofer"],
                    tienda=payload["tienda"],
                    detalles=payload["detalles"],
                )
            elif op == "UPDATE_LOTES_ESTADO":
                self.neo4j_repo.update_lotes_estado(
                    codigos_lotes=payload["codigos_lotes"],
                    nuevo_estado=payload["nuevo_estado"],
                )
            else:
                raise ValueError(f"Operación Neo4j no soportada: {op}")
        elif destino == "mongodb":
            if op == "INSERT_ACTA_RECEPCION":
                doc = dict(payload)
                doc["fecha_hora_inspeccion"] = _parse_dt(doc["fecha_hora_inspeccion"])
                self.mongo_repo.insert_acta_recepcion(doc)
            elif op == "CREATE_EXPEDIENTE_INCIDENTE":
                doc = dict(payload)
                doc["fecha_apertura"] = _parse_dt(doc["fecha_apertura"])
                for item in doc.get("linea_tiempo", []):
                    item["fecha_hora"] = _parse_dt(item["fecha_hora"])
                self.mongo_repo.create_expediente_incidente(doc)
            else:
                raise ValueError(f"Operación MongoDB no soportada: {op}")
        else:
            raise ValueError(f"Motor destino no soportado: {destino}")
