from datetime import datetime, timezone
from typing import Any
import uuid

from backend.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from backend.core.security import ROLE_PRODUCTOR, CurrentUser
from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.lotes import LoteCreateRequest, LoteLiberarRequest
from backend.schemas.recepciones import RecepcionCreateRequest
from backend.services.reconciliacion_service import ReconciliacionService

TEMP_MIN_CADENA_FRIO = 4.0
TEMP_MAX_CADENA_FRIO = 8.0


class LotesService:
    """Coordina creación de lotes (RN-06), recepción en CEDIS (RN-07) y liberación QA (RN-02, RN-04)."""

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

    def crear_lote(self, data: LoteCreateRequest, user: CurrentUser) -> dict[str, Any]:
        parcela = self.pg_repo.get_parcela_with_productor(data.parcela_id)
        if parcela is None:
            raise NotFoundError(
                f"La parcela {data.parcela_id} no existe.",
                error_code="PARCELA_NO_ENCONTRADA",
            )
        if not parcela["productor_activo"]:
            raise ConflictError(
                "El productor titular de la parcela se encuentra inactivo (RN-10).",
                error_code="PRODUCTOR_INACTIVO",
            )
        if user.role == ROLE_PRODUCTOR and parcela["productor_id"] != user.productor_id:
            raise ForbiddenError(
                "No puedes registrar lotes en una parcela que pertenece a otro productor (RN-11)."
            )

        lote = self.pg_repo.create_lote(
            codigo_lote=data.codigo_lote,
            parcela_id=data.parcela_id,
            producto=data.producto,
            fecha_cosecha=data.fecha_cosecha,
            cuadrilla_cosecha=data.cuadrilla_cosecha,
            peso_inicial_kg=data.peso_inicial_kg,
        )

        sincronizacion = {"postgresql": "confirmado", "neo4j": "sincronizado"}
        try:
            self.neo4j_repo.merge_lote_cosechado(
                codigo_lote=lote["codigo_lote"],
                producto=lote["producto"],
                fecha_cosecha=lote["fecha_cosecha"],
                peso_inicial_kg=lote["peso_inicial_kg"],
                estado=lote["estado"],
                cuadrilla_cosecha=lote["cuadrilla_cosecha"],
                parcela=parcela,
            )
        except Exception as exc:
            self.reconciliacion.registrar_pendiente(
                destino_motor="neo4j",
                tipo_operacion="MERGE_LOTE",
                llave_entidad=lote["codigo_lote"],
                payload={
                    "codigo_lote": lote["codigo_lote"],
                    "producto": lote["producto"],
                    "fecha_cosecha": lote["fecha_cosecha"].isoformat(),
                    "peso_inicial_kg": lote["peso_inicial_kg"],
                    "estado": lote["estado"],
                    "cuadrilla_cosecha": lote["cuadrilla_cosecha"],
                    "parcela": parcela,
                },
                error=exc,
            )
            sincronizacion["neo4j"] = "pendiente_reconciliacion"

        lote["sincronizacion"] = sincronizacion
        return lote

    def registrar_recepcion(self, data: RecepcionCreateRequest, user: CurrentUser) -> dict[str, Any]:
        # Regla RN-07: rango óptimo térmico 4.0 a 8.0 °C
        fuera_de_rango = (
            data.temperatura_llegada_c < TEMP_MIN_CADENA_FRIO
            or data.temperatura_llegada_c > TEMP_MAX_CADENA_FRIO
        )
        dictamen = "Retenido" if fuera_de_rango else "Conforme"
        nuevo_estado = "En revision" if fuera_de_rango else "Recibido"
        fecha_llegada = datetime.now(timezone.utc)

        recepcion = self.pg_repo.create_recepcion(
            folio_recepcion=data.folio_recepcion,
            codigo_lote=data.codigo_lote,
            placas_vehiculo=data.placas_vehiculo,
            codigo_cuarto_frio=data.codigo_cuarto_frio,
            peso_recibido_kg=data.peso_recibido_kg,
            temperatura_llegada_c=data.temperatura_llegada_c,
            dictamen_recepcion=dictamen,
            nuevo_estado_lote=nuevo_estado,
            fecha_llegada=fecha_llegada,
        )

        sincronizacion = {
            "postgresql": "confirmado",
            "mongodb": "sincronizado",
            "neo4j": "sincronizado",
        }

        acta_doc: dict[str, Any] = {
            "folio_recepcion": data.folio_recepcion,
            "codigo_lote": data.codigo_lote,
            "fecha_hora_inspeccion": fecha_llegada,
            "inspector": {
                "usuario_id": user.sub,
                "nombre": user.nombre,
                "turno": data.turno,
            },
            "evaluacion_sensorial": data.evaluacion_sensorial.model_dump(exclude_none=True),
            "defectos_detectados": [d.model_dump() for d in data.defectos_detectados],
            "monitoreo_temperatura_caja": [
                m.model_dump(exclude_none=True) for m in data.monitoreo_temperatura_caja
            ],
            "evidencias_fotograficas": [
                e.model_dump(exclude_none=True) for e in data.evidencias_fotograficas
            ],
            "observaciones_inspector": data.observaciones_inspector,
        }

        try:
            self.mongo_repo.insert_acta_recepcion(dict(acta_doc))
        except Exception as exc:
            payload_mongo = dict(acta_doc)
            payload_mongo["fecha_hora_inspeccion"] = fecha_llegada.isoformat()
            self.reconciliacion.registrar_pendiente(
                destino_motor="mongodb",
                tipo_operacion="INSERT_ACTA_RECEPCION",
                llave_entidad=data.folio_recepcion,
                payload=payload_mongo,
                error=exc,
            )
            sincronizacion["mongodb"] = "pendiente_reconciliacion"

        try:
            self.neo4j_repo.merge_recepcion_fisica(
                codigo_lote=data.codigo_lote,
                estado_lote=nuevo_estado,
                folio_recepcion=data.folio_recepcion,
                placas_vehiculo=data.placas_vehiculo,
                codigo_cuarto_frio=data.codigo_cuarto_frio,
                nombre_chofer=data.nombre_chofer,
                peso_recibido_kg=data.peso_recibido_kg,
                temperatura_llegada_c=data.temperatura_llegada_c,
                dictamen_recepcion=dictamen,
                fecha_llegada=fecha_llegada,
            )
        except Exception as exc:
            self.reconciliacion.registrar_pendiente(
                destino_motor="neo4j",
                tipo_operacion="MERGE_RECEPCION",
                llave_entidad=data.folio_recepcion,
                payload={
                    "codigo_lote": data.codigo_lote,
                    "estado_lote": nuevo_estado,
                    "folio_recepcion": data.folio_recepcion,
                    "placas_vehiculo": data.placas_vehiculo,
                    "codigo_cuarto_frio": data.codigo_cuarto_frio,
                    "nombre_chofer": data.nombre_chofer,
                    "peso_recibido_kg": data.peso_recibido_kg,
                    "temperatura_llegada_c": data.temperatura_llegada_c,
                    "dictamen_recepcion": dictamen,
                    "fecha_llegada": fecha_llegada.isoformat(),
                },
                error=exc,
            )
            sincronizacion["neo4j"] = "pendiente_reconciliacion"

        return {
            "recepcion_id": recepcion["recepcion_id"],
            "folio_recepcion": recepcion["folio_recepcion"],
            "codigo_lote": data.codigo_lote,
            "fecha_llegada": recepcion["fecha_llegada"],
            "placas_vehiculo": recepcion["placas_vehiculo"],
            "codigo_cuarto_frio": recepcion["codigo_cuarto_frio"],
            "peso_recibido_kg": recepcion["peso_recibido_kg"],
            "temperatura_llegada_c": recepcion["temperatura_llegada_c"],
            "dictamen_recepcion": dictamen,
            "estado_lote_resultante": nuevo_estado,
            "alerta_cadena_frio": fuera_de_rango,
            "sincronizacion": sincronizacion,
        }

    def liberar_lote(
        self,
        codigo_lote: str,
        data: LoteLiberarRequest,
        user: CurrentUser,
    ) -> dict[str, Any]:
        # Regla RN-02: (∃ análisis vigente Conforme) ∧ (¬∃ análisis vigente No Conforme)
        vigentes = self.mongo_repo.list_analisis_by_lote(codigo_lote, solo_vigentes=True)
        tiene_conforme = any(a.get("dictamen_general") == "Conforme" for a in vigentes)
        tiene_no_conforme = any(a.get("dictamen_general") == "No Conforme" for a in vigentes)

        if not tiene_conforme or tiene_no_conforme:
            raise ConflictError(
                f"El lote '{codigo_lote}' no cumple RN-02 para liberación: requiere al menos un análisis vigente 'Conforme' y cero análisis vigentes 'No Conforme'.",
                error_code="REQUISITO_ANALISIS_NO_CUMPLIDO",
                extra={"codigo_lote": codigo_lote},
            )

        folio_evento = f"LIB-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:6].upper()}"
        updated = self.pg_repo.liberar_lote(
            codigo_lote=codigo_lote,
            usuario_responsable=user.nombre,
            motivo=data.motivo,
            folio_evento=folio_evento,
        )

        sincronizacion = {"postgresql": "confirmado", "neo4j": "sincronizado"}
        try:
            self.neo4j_repo.update_lotes_estado([codigo_lote], "Liberado")
        except Exception as exc:
            self.reconciliacion.registrar_pendiente(
                destino_motor="neo4j",
                tipo_operacion="UPDATE_LOTES_ESTADO",
                llave_entidad=codigo_lote,
                payload={"codigos_lotes": [codigo_lote], "nuevo_estado": "Liberado"},
                error=exc,
            )
            sincronizacion["neo4j"] = "pendiente_reconciliacion"

        return {
            "codigo_lote": codigo_lote,
            "estado_previo": updated["estado_previo"],
            "estado_actual": updated["estado"],
            "saldo_kg": updated["saldo_kg"],
            "folio_evento": updated["folio_evento"],
            "sincronizacion": sincronizacion,
        }
