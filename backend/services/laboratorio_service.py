from datetime import datetime, timezone
from typing import Any

from backend.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationDomainError,
)
from backend.core.security import ROLE_PRODUCTOR, CurrentUser
from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.analisis import AnalisisCreateRequest
from backend.services.reconciliacion_service import ReconciliacionService


class LaboratorioService:
    """Gestiona certificados de laboratorio versionados (RN-05) y consulta con control RN-11."""

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

    def registrar_analisis(self, data: AnalisisCreateRequest) -> dict[str, Any]:
        # 1. Validación previa en PostgreSQL (fuente de verdad) para evitar documentos huérfanos
        lote = self.pg_repo.get_lote_by_codigo(data.codigo_lote)
        if lote is None:
            raise NotFoundError(
                f"El lote '{data.codigo_lote}' no existe en PostgreSQL.",
                error_code="LOTE_NO_ENCONTRADO",
            )

        fecha_emision = data.fecha_emision or datetime.now(timezone.utc)
        doc: dict[str, Any] = {
            "folio_analisis": data.folio_analisis,
            "codigo_lote": data.codigo_lote,
            "tipo_estudio": data.tipo_estudio,
            "fecha_muestreo": data.fecha_muestreo,
            "fecha_emision": fecha_emision,
            "version": 1,
            "es_vigente": True,
            "folio_reemplazado": None,
            "motivo_enmienda": data.motivo_enmienda,
            "dictamen_general": data.dictamen_general,
            "laboratorio": data.laboratorio.model_dump(exclude_none=True),
            "muestras": [m.model_dump(exclude_none=True) for m in data.muestras],
        }
        if data.firma_digital is not None:
            doc["firma_digital"] = data.firma_digital.model_dump(exclude_none=True)

        # 2. Escritura inmutable en MongoDB (si falla MongoDB, se aborta sin tocar Neo4j)
        try:
            inserted = self.mongo_repo.insert_analisis_versionado(doc)
        except (ConflictError, ValidationDomainError):
            raise
        except Exception as exc:
            raise ServiceUnavailableError(
                "No fue posible almacenar el certificado en MongoDB; la operación fue abortada."
            ) from exc

        # 3. Proyección ligera en Neo4j (:Laboratorio)-[:EMITIO_ANALISIS]->(:Lote)
        sincronizacion = {"mongodb": "confirmado", "neo4j": "sincronizado"}
        try:
            self.neo4j_repo.merge_analisis_proyeccion(
                codigo_lote=data.codigo_lote,
                acreditacion_iso=data.laboratorio.acreditacion_iso,
                nombre_laboratorio=data.laboratorio.nombre,
                folio_analisis=inserted["folio_analisis"],
                tipo_estudio=data.tipo_estudio,
                dictamen_general=data.dictamen_general,
                fecha_emision=fecha_emision,
                folio_reemplazado=inserted.get("folio_reemplazado"),
            )
        except Exception as exc:
            self.reconciliacion.registrar_pendiente(
                destino_motor="neo4j",
                tipo_operacion="MERGE_ANALISIS",
                llave_entidad=inserted["folio_analisis"],
                payload={
                    "codigo_lote": data.codigo_lote,
                    "acreditacion_iso": data.laboratorio.acreditacion_iso,
                    "nombre_laboratorio": data.laboratorio.nombre,
                    "folio_analisis": inserted["folio_analisis"],
                    "tipo_estudio": data.tipo_estudio,
                    "dictamen_general": data.dictamen_general,
                    "fecha_emision": fecha_emision.isoformat(),
                    "folio_reemplazado": inserted.get("folio_reemplazado"),
                },
                error=exc,
            )
            sincronizacion["neo4j"] = "pendiente_reconciliacion"

        return {
            "folio_analisis": inserted["folio_analisis"],
            "codigo_lote": inserted["codigo_lote"],
            "tipo_estudio": inserted["tipo_estudio"],
            "version": inserted["version"],
            "es_vigente": inserted["es_vigente"],
            "folio_reemplazado": inserted.get("folio_reemplazado"),
            "dictamen_general": inserted["dictamen_general"],
            "sincronizacion": sincronizacion,
        }

    def consultar_analisis(
        self,
        codigo_lote: str,
        user: CurrentUser,
        *,
        solo_vigentes: bool = False,
        solo_no_conformes: bool = False,
    ) -> dict[str, Any]:
        # Validación de existencia y BOLA/IDOR (RN-11) contra PostgreSQL
        lote = self.pg_repo.get_lote_by_codigo(codigo_lote)
        if lote is None:
            raise NotFoundError(
                f"El lote '{codigo_lote}' no existe.",
                error_code="LOTE_NO_ENCONTRADO",
            )
        if user.role == ROLE_PRODUCTOR and lote["productor_id"] != user.productor_id:
            raise ForbiddenError(
                "No tienes permiso para consultar análisis de lotes de otro productor (RN-11)."
            )

        analisis = self.mongo_repo.list_analisis_by_lote(
            codigo_lote,
            solo_vigentes=solo_vigentes,
            solo_no_conformes=solo_no_conformes,
        )
        return {
            "codigo_lote": codigo_lote,
            "total": len(analisis),
            "analisis": analisis,
        }
