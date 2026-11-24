from datetime import datetime, timezone
import random
from typing import Any

from backend.core.exceptions import ForbiddenError, NotFoundError
from backend.core.security import ROLE_PRODUCTOR, CurrentUser
from backend.repositories.document.mongo_repo import MongoRepository
from backend.repositories.graph.neo4j_repo import Neo4jRepository
from backend.repositories.relational.postgres_repo import PostgresRepository
from backend.schemas.incidentes import IncidenteCerrarRequest, RecallCreateRequest
from backend.services.reconciliacion_service import ReconciliacionService


class TrazabilidadQAService:
    """Coordina Expediente 360°, Recall integrado (RN-08), cierre de incidentes (RN-09) y trazabilidad."""

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

    def obtener_expediente_360(self, codigo_lote: str, user: CurrentUser) -> dict[str, Any]:
        # 1. PostgreSQL: ficha maestra + validación BOLA/IDOR (RN-11)
        lote = self.pg_repo.get_lote_by_codigo(codigo_lote)
        if lote is None:
            raise NotFoundError(
                f"El lote '{codigo_lote}' no existe.",
                error_code="LOTE_NO_ENCONTRADO",
            )
        if user.role == ROLE_PRODUCTOR and lote["productor_id"] != user.productor_id:
            raise ForbiddenError(
                "No tienes permiso para consultar el expediente de un lote de otro productor (RN-11)."
            )

        recepcion_sql = self.pg_repo.get_recepcion_by_lote_id(lote["lote_id"])
        incidentes_sql = self.pg_repo.get_incidentes_by_lote_id(lote["lote_id"])

        advertencias: list[str] = []
        acta_recepcion = None
        analisis_lab: list[dict[str, Any]] = []
        expedientes_inc: list[dict[str, Any]] = []
        red_trazabilidad = None

        # 2. MongoDB: acta de recepción, análisis e incidentes
        try:
            acta_recepcion = self.mongo_repo.get_acta_recepcion_by_lote(codigo_lote)
            analisis_lab = self.mongo_repo.list_analisis_by_lote(codigo_lote)
            expedientes_inc = self.mongo_repo.list_expedientes_by_lote(codigo_lote)
        except Exception:
            advertencias.append("MongoDB temporalmente no disponible; se omiten documentos técnicos.")

        # 3. Neo4j: contexto físico y rutas
        try:
            red_trazabilidad = self.neo4j_repo.get_red_lote_360(codigo_lote)
        except Exception:
            advertencias.append("Neo4j temporalmente no disponible; se omite red topológica.")

        return {
            "lote": lote,
            "recepcion_sql": recepcion_sql,
            "acta_recepcion": acta_recepcion,
            "analisis_laboratorio": analisis_lab,
            "incidentes_bitacora": incidentes_sql,
            "expedientes_incidentes": expedientes_inc,
            "red_trazabilidad": red_trazabilidad,
            "advertencias": advertencias,
        }

    def ejecutar_recall(
        self,
        data: RecallCreateRequest,
        user: CurrentUser,
        client_ip: str = "unknown",
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        folio_incidente = (
            data.folio_incidente or f"INC-{now.year}-{random.randint(1000, 9999)}"
        )

        # 1. Evidencia documental en MongoDB (si existe análisis infractor vigente)
        evidencia_documental = None
        try:
            evidencia_documental = self.mongo_repo.get_parametros_infractores_vigentes(
                data.codigo_lote_origen
            )
        except Exception:
            evidencia_documental = None

        # 2. Rastreo lateral y hacia adelante en Neo4j
        lotes_hermanos: list[dict[str, Any]] = []
        tiendas_afectadas: list[dict[str, Any]] = []
        neo4j_lectura_ok = True
        try:
            if data.incluir_lotes_hermanos:
                lotes_hermanos = self.neo4j_repo.rastreo_lateral(
                    data.codigo_lote_origen,
                    ventana_dias=data.ventana_dias_contaminacion,
                )
            tiendas_afectadas = self.neo4j_repo.rastreo_adelante(data.codigo_lote_origen)
        except Exception:
            neo4j_lectura_ok = False

        codigos_hermanos = [h["codigo_lote"] for h in lotes_hermanos]
        lotes_afectados_codigos = sorted({data.codigo_lote_origen, *codigos_hermanos})

        # 3. Bloqueo atómico ACID en PostgreSQL (fuente de verdad)
        motivo_auditoria = f"{data.motivo} [IP:{client_ip}]"
        pg_block = self.pg_repo.bloquear_lotes_recall(
            folio_incidente=folio_incidente,
            codigo_lote_origen=data.codigo_lote_origen,
            codigos_lotes_hermanos=codigos_hermanos,
            usuario_responsable=user.nombre,
            motivo=motivo_auditoria,
        )
        lote_origen_pg = pg_block["lote_origen"]

        sincronizacion = {
            "postgresql": "confirmado",
            "mongodb": "expediente_creado",
            "neo4j": "estados_actualizados" if neo4j_lectura_ok else "pendiente_reconciliacion",
        }

        # 4. Apertura de expediente en MongoDB (con respaldo outbox si falla)
        tiendas_notificadas = [
            {
                "codigo_sucursal": t["codigo_sucursal"],
                "nombre_comercial": t["nombre_comercial"],
                "cantidad_enviada_kg": float(t.get("cantidad_kg") or 0.0),
                "cantidad_retirada_kg": 0.0,
                "confirmado": False,
                "fecha_confirmacion": None,
            }
            for t in tiendas_afectadas
            if t.get("codigo_sucursal")
        ]

        expediente_doc: dict[str, Any] = {
            "folio_incidente": folio_incidente,
            "codigo_lote_origen": data.codigo_lote_origen,
            "lotes_afectados": lotes_afectados_codigos,
            "estado_expediente": "Abierto",
            "fecha_apertura": now,
            "fecha_cierre": None,
            "causa_raiz": None,
            "acciones_correctivas": [],
            "tiendas_notificadas": tiendas_notificadas,
            "linea_tiempo": [
                {
                    "fecha_hora": now,
                    "actor": f"{user.nombre} ({user.sub}, IP {client_ip})",
                    "descripcion": f"Activación de protocolo Recall: {data.motivo}",
                }
            ],
            "firmas_cierre": None,
        }

        try:
            self.mongo_repo.create_expediente_incidente(dict(expediente_doc))
        except Exception as exc:
            payload_mongo = dict(expediente_doc)
            payload_mongo["fecha_apertura"] = now.isoformat()
            payload_mongo["linea_tiempo"] = [
                {**item, "fecha_hora": now.isoformat()}
                for item in expediente_doc["linea_tiempo"]
            ]
            self.reconciliacion.registrar_pendiente(
                destino_motor="mongodb",
                tipo_operacion="CREATE_EXPEDIENTE_INCIDENTE",
                llave_entidad=folio_incidente,
                payload=payload_mongo,
                error=exc,
            )
            sincronizacion["mongodb"] = "pendiente_reconciliacion"

        # 5. Sincronización de estado 'Bloqueado' en nodos :Lote de Neo4j
        try:
            self.neo4j_repo.update_lotes_estado(lotes_afectados_codigos, "Bloqueado")
            sincronizacion["neo4j"] = "estados_actualizados"
        except Exception as exc:
            self.reconciliacion.registrar_pendiente(
                destino_motor="neo4j",
                tipo_operacion="UPDATE_LOTES_ESTADO",
                llave_entidad=folio_incidente,
                payload={
                    "codigos_lotes": lotes_afectados_codigos,
                    "nuevo_estado": "Bloqueado",
                },
                error=exc,
            )
            sincronizacion["neo4j"] = "pendiente_reconciliacion"

        return {
            "folio_incidente": folio_incidente,
            "lote_origen": {
                "codigo_lote": lote_origen_pg["codigo_lote"],
                "estado_actual": lote_origen_pg["estado"],
                "saldo_inmovilizado_kg": lote_origen_pg["saldo_kg"],
            },
            "evidencia_documental": evidencia_documental,
            "lotes_hermanos_bloqueados": [
                {
                    "codigo_lote": h["codigo_lote"],
                    "causa_vinculo": h["causa_vinculo"],
                }
                for h in lotes_hermanos
            ],
            "tiendas_afectadas": [
                {
                    "codigo_sucursal": t["codigo_sucursal"],
                    "nombre_comercial": t["nombre_comercial"],
                    "codigo_envio": t["codigo_envio"],
                    "cantidad_kg": t["cantidad_kg"],
                }
                for t in tiendas_afectadas
            ],
            "sincronizacion": sincronizacion,
        }

    def cerrar_incidente(
        self,
        folio: str,
        data: IncidenteCerrarRequest,
        user: CurrentUser,
    ) -> dict[str, Any]:
        # 1. Cierre validado en MongoDB (RN-09)
        cerrado = self.mongo_repo.cerrar_expediente_incidente(
            folio_incidente=folio,
            causa_raiz=data.causa_raiz,
            acciones_correctivas=data.acciones_correctivas,
            responsable_qa=data.responsable_qa,
            aprobacion_gerencia=data.aprobacion_gerencia,
            actor=user.nombre,
        )

        # 2. Registro de cierre en PostgreSQL
        sincronizacion = {"mongodb": "cerrado", "postgresql": "confirmado", "neo4j": "sincronizado"}
        incidente_pg = self.pg_repo.get_incidente_by_folio(folio)
        if incidente_pg is not None:
            folio_cierre = f"{folio}-CLS"[:30]
            self.pg_repo.registrar_cierre_incidente_bitacora(
                folio_cierre=folio_cierre,
                lote_id=incidente_pg["lote_id"],
                usuario_responsable=user.nombre,
                motivo=f"Cierre de incidente {folio}: {data.causa_raiz[:180]}",
                nuevo_estado="Retirado",
            )

        # 3. Sincronización de estado 'Retirado' en Neo4j
        lotes_afectados = cerrado.get("lotes_afectados", [])
        try:
            self.neo4j_repo.update_lotes_estado(lotes_afectados, "Retirado")
        except Exception as exc:
            self.reconciliacion.registrar_pendiente(
                destino_motor="neo4j",
                tipo_operacion="UPDATE_LOTES_ESTADO",
                llave_entidad=folio,
                payload={"codigos_lotes": lotes_afectados, "nuevo_estado": "Retirado"},
                error=exc,
            )
            sincronizacion["neo4j"] = "pendiente_reconciliacion"

        return {
            "folio_incidente": folio,
            "estado_expediente": cerrado["estado_expediente"],
            "fecha_cierre": cerrado.get("fecha_cierre"),
            "causa_raiz": cerrado["causa_raiz"],
            "acciones_correctivas": cerrado["acciones_correctivas"],
            "firmas_cierre": cerrado["firmas_cierre"],
            "sincronizacion": sincronizacion,
        }

    def rastreo_adelante(self, codigo_lote: str) -> dict[str, Any]:
        lote = self.pg_repo.get_lote_by_codigo(codigo_lote)
        if lote is None:
            raise NotFoundError(
                f"El lote '{codigo_lote}' no existe.",
                error_code="LOTE_NO_ENCONTRADO",
            )
        tiendas = self.neo4j_repo.rastreo_adelante(codigo_lote)
        total_kg = round(sum(float(t.get("cantidad_kg") or 0.0) for t in tiendas), 2)
        return {
            "codigo_lote": codigo_lote,
            "total_envios": len(tiendas),
            "total_kg_despachados": total_kg,
            "tiendas_afectadas": tiendas,
        }

    def rastreo_atras_lateral(self, codigo_lote: str, ventana_dias: int = 1) -> dict[str, Any]:
        lote = self.pg_repo.get_lote_by_codigo(codigo_lote)
        if lote is None:
            raise NotFoundError(
                f"El lote '{codigo_lote}' no existe.",
                error_code="LOTE_NO_ENCONTRADO",
            )
        origen = self.neo4j_repo.rastreo_atras(codigo_lote)
        hermanos = self.neo4j_repo.rastreo_lateral(codigo_lote, ventana_dias=ventana_dias)
        return {
            "codigo_lote": codigo_lote,
            "ventana_dias": ventana_dias,
            "origen": origen,
            "lotes_hermanos": hermanos,
        }
