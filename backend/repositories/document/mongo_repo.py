from datetime import datetime, timezone
from typing import Any

from pymongo import DESCENDING
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, WriteError

from backend.core.exceptions import ConflictError, NotFoundError, ValidationDomainError


def _strip_object_id(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if doc is None:
        return None
    cleaned = dict(doc)
    cleaned.pop("_id", None)
    return cleaned


class MongoRepository:
    """Repositorio documental sobre MongoDB 7 (analisis_laboratorio, actas_recepcion, expedientes_incidentes)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # 1. analisis_laboratorio (versionado inmutable RN-05)
    # ------------------------------------------------------------------
    def get_analisis_vigente(self, codigo_lote: str, tipo_estudio: str) -> dict[str, Any] | None:
        doc = self.db.analisis_laboratorio.find_one(
            {
                "codigo_lote": str(codigo_lote),
                "tipo_estudio": str(tipo_estudio),
                "es_vigente": True,
            },
            {"_id": 0},
        )
        return doc

    def list_analisis_by_lote(
        self,
        codigo_lote: str,
        *,
        solo_vigentes: bool = False,
        solo_no_conformes: bool = False,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {"codigo_lote": str(codigo_lote)}
        if solo_vigentes:
            query["es_vigente"] = True
        if solo_no_conformes:
            query["muestras"] = {
                "$elemMatch": {
                    "determinaciones": {"$elemMatch": {"conforme": False}},
                }
            }
        cursor = (
            self.db.analisis_laboratorio.find(query, {"_id": 0})
            .sort([("tipo_estudio", 1), ("version", DESCENDING)])
        )
        return list(cursor)

    def insert_analisis_versionado(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Inserta versión 1 o enmienda V+1 desactivando la versión previa sin modificar sus resultados."""
        codigo_lote = str(doc["codigo_lote"])
        tipo_estudio = str(doc["tipo_estudio"])

        previo = self.get_analisis_vigente(codigo_lote, tipo_estudio)
        if previo is not None:
            if not doc.get("motivo_enmienda"):
                raise ValidationDomainError(
                    "Ya existe un análisis vigente para este lote y tipo de estudio; se requiere 'motivo_enmienda' para emitir una nueva versión (RN-05)."
                )
            doc["version"] = int(previo["version"]) + 1
            doc["folio_reemplazado"] = previo["folio_analisis"]
            # Desactivar vigencia de la versión previa (sin alterar datos analíticos)
            self.db.analisis_laboratorio.update_one(
                {"folio_analisis": previo["folio_analisis"], "es_vigente": True},
                {"$set": {"es_vigente": False}},
            )
        else:
            doc["version"] = int(doc.get("version", 1))
            doc["folio_reemplazado"] = None

        doc["es_vigente"] = True
        try:
            self.db.analisis_laboratorio.insert_one(doc)
        except DuplicateKeyError as exc:
            # Restaurar vigencia previa si el folio nuevo colisionó
            if previo is not None:
                self.db.analisis_laboratorio.update_one(
                    {"folio_analisis": previo["folio_analisis"]},
                    {"$set": {"es_vigente": True}},
                )
            raise ConflictError(
                f"Ya existe un certificado de laboratorio con folio '{doc['folio_analisis']}'.",
                error_code="ANALISIS_FOLIO_DUPLICADO",
            ) from exc
        except WriteError as exc:
            if previo is not None:
                self.db.analisis_laboratorio.update_one(
                    {"folio_analisis": previo["folio_analisis"]},
                    {"$set": {"es_vigente": True}},
                )
            raise ValidationDomainError(
                "El documento de análisis no cumple con el esquema $jsonSchema de MongoDB."
            ) from exc

        return _strip_object_id(doc) or {}

    def get_parametros_infractores_vigentes(self, codigo_lote: str) -> dict[str, Any] | None:
        """Obtiene el primer análisis vigente con determinaciones no conformes ($elemMatch)."""
        doc = self.db.analisis_laboratorio.find_one(
            {
                "codigo_lote": str(codigo_lote),
                "es_vigente": True,
                "muestras": {
                    "$elemMatch": {
                        "determinaciones": {"$elemMatch": {"conforme": False}},
                    }
                },
            },
            {"_id": 0},
        )
        if doc is None:
            return None

        infractores: list[dict[str, Any]] = []
        for muestra in doc.get("muestras", []):
            for det in muestra.get("determinaciones", []):
                if det.get("conforme") is False:
                    infractores.append(det)

        return {
            "folio_analisis": doc["folio_analisis"],
            "laboratorio": doc.get("laboratorio", {}).get("nombre", ""),
            "parametros_infractores": infractores,
        }

    # ------------------------------------------------------------------
    # 2. actas_recepcion
    # ------------------------------------------------------------------
    def insert_acta_recepcion(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Inserta acta de recepción de forma idempotente por folio_recepcion."""
        existing = self.db.actas_recepcion.find_one(
            {"folio_recepcion": str(doc["folio_recepcion"])},
            {"_id": 0},
        )
        if existing is not None:
            return existing
        try:
            self.db.actas_recepcion.insert_one(doc)
        except DuplicateKeyError as exc:
            raise ConflictError(
                f"Ya existe un acta de recepción con folio '{doc['folio_recepcion']}'.",
                error_code="ACTA_RECEPCION_DUPLICADA",
            ) from exc
        except WriteError as exc:
            raise ValidationDomainError(
                "El acta de recepción no cumple con las reglas $jsonSchema de MongoDB."
            ) from exc
        return _strip_object_id(doc) or {}

    def get_acta_recepcion_by_lote(self, codigo_lote: str) -> dict[str, Any] | None:
        return self.db.actas_recepcion.find_one(
            {"codigo_lote": str(codigo_lote)},
            {"_id": 0},
        )

    # ------------------------------------------------------------------
    # 3. expedientes_incidentes (RN-09)
    # ------------------------------------------------------------------
    def create_expediente_incidente(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Crea un expediente de incidente/recall de manera idempotente por folio_incidente."""
        existing = self.db.expedientes_incidentes.find_one(
            {"folio_incidente": str(doc["folio_incidente"])},
            {"_id": 0},
        )
        if existing is not None:
            return existing
        try:
            self.db.expedientes_incidentes.insert_one(doc)
        except WriteError as exc:
            raise ValidationDomainError(
                "El expediente de incidente no cumple con el esquema $jsonSchema."
            ) from exc
        return _strip_object_id(doc) or {}

    def get_expediente_incidente(self, folio_incidente: str) -> dict[str, Any] | None:
        return self.db.expedientes_incidentes.find_one(
            {"folio_incidente": str(folio_incidente)},
            {"_id": 0},
        )

    def list_expedientes_by_lote(self, codigo_lote: str) -> list[dict[str, Any]]:
        cursor = self.db.expedientes_incidentes.find(
            {"lotes_afectados": str(codigo_lote)},
            {"_id": 0},
        ).sort("fecha_apertura", DESCENDING)
        return list(cursor)

    def cerrar_expediente_incidente(
        self,
        *,
        folio_incidente: str,
        causa_raiz: str,
        acciones_correctivas: list[str],
        responsable_qa: str,
        aprobacion_gerencia: str,
        actor: str,
    ) -> dict[str, Any]:
        existing = self.get_expediente_incidente(folio_incidente)
        if existing is None:
            raise NotFoundError(
                f"No existe el expediente de incidente '{folio_incidente}'.",
                error_code="EXPEDIENTE_NO_ENCONTRADO",
            )
        if existing.get("estado_expediente") == "Cerrado":
            raise ConflictError(
                f"El expediente '{folio_incidente}' ya se encuentra cerrado.",
                error_code="EXPEDIENTE_YA_CERRADO",
            )

        now = datetime.now(timezone.utc)
        evento_cierre = {
            "fecha_hora": now,
            "actor": actor,
            "descripcion": f"Cierre formal de expediente aprobado por QA ({responsable_qa}) y Gerencia ({aprobacion_gerencia}).",
        }

        try:
            self.db.expedientes_incidentes.update_one(
                {"folio_incidente": str(folio_incidente)},
                {
                    "$set": {
                        "estado_expediente": "Cerrado",
                        "fecha_cierre": now,
                        "causa_raiz": causa_raiz,
                        "acciones_correctivas": acciones_correctivas,
                        "firmas_cierre": {
                            "responsable_qa": responsable_qa,
                            "aprobacion_gerencia": aprobacion_gerencia,
                        },
                    },
                    "$push": {"linea_tiempo": evento_cierre},
                },
            )
        except WriteError as exc:
            raise ValidationDomainError(
                "El cierre del expediente incumple la regla RN-09 en MongoDB."
            ) from exc

        return self.get_expediente_incidente(folio_incidente) or {}
