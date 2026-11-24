from typing import Any

from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.envios import EnvioCreateRequest
from backend.services.reconciliacion_service import ReconciliacionService


class DespachosService:
    """Ejecuta despachos fraccionados ACID en PostgreSQL (RN-01, RN-03) y proyecta en Neo4j."""

    def __init__(
        self,
        pg_repo: PostgresRepository,
        mongo_repo: MongoRepository,
        neo4j_repo: Neo4jRepository,
    ) -> None:
        self.pg_repo = pg_repo
        self.mongo_repo = mongo_repo
        self.neo4j_repo = neo4j_repo
        self.reconciliacion = ReconciliacionService(pg_repo, mongo_repo, neo4j_repo)

    def registrar_envio(self, data: EnvioCreateRequest) -> dict[str, Any]:
        detalles_dict = [d.model_dump() for d in data.detalles]

        # 1. Transacción ACID con SELECT ... FOR UPDATE en PostgreSQL
        pg_result = self.pg_repo.create_envio_fraccionado(
            codigo_envio=data.codigo_envio,
            tienda_id=data.tienda_id,
            placas_vehiculo=data.placas_vehiculo,
            detalles=detalles_dict,
        )
        envio = pg_result["envio"]
        tienda = pg_result["tienda"]

        # 2. Proyección idempotente en Neo4j (o registro en outbox ante fallo parcial)
        sincronizacion = {"neo4j": "sincronizado"}
        try:
            self.neo4j_repo.merge_envio_proyeccion(
                codigo_envio=envio["codigo_envio"],
                estado_envio=envio["estado_envio"],
                fecha_despacho=envio["fecha_despacho"],
                placas_vehiculo=data.placas_vehiculo,
                nombre_chofer=data.nombre_chofer,
                tienda=tienda,
                detalles=detalles_dict,
            )
        except Exception as exc:
            self.reconciliacion.registrar_pendiente(
                destino_motor="neo4j",
                tipo_operacion="MERGE_ENVIO",
                llave_entidad=envio["codigo_envio"],
                payload={
                    "codigo_envio": envio["codigo_envio"],
                    "estado_envio": envio["estado_envio"],
                    "fecha_despacho": envio["fecha_despacho"].isoformat(),
                    "placas_vehiculo": data.placas_vehiculo,
                    "nombre_chofer": data.nombre_chofer,
                    "tienda": tienda,
                    "detalles": detalles_dict,
                },
                error=exc,
            )
            sincronizacion["neo4j"] = "pendiente_reconciliacion"

        return {
            "codigo_envio": envio["codigo_envio"],
            "estado_envio": envio["estado_envio"],
            "tienda_id": envio["tienda_id"],
            "total_kg": pg_result["total_kg"],
            "saldos_actualizados": pg_result["saldos_actualizados"],
            "sincronizacion": sincronizacion,
        }
