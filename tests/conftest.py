from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient
import pytest

from backend.core.database import get_mongo_db, get_neo4j_driver, get_pg_connection
from backend.core.exceptions import ConflictError, NotFoundError, ValidationDomainError
from backend.core.security import (
    ROLE_LABORATORIO,
    ROLE_PRODUCTOR,
    ROLE_QA,
    ROLE_RECEPCION,
    create_access_token,
    login_rate_limiter,
    recall_rate_limiter,
)
from backend.main import app


class FakePostgresRepo:
    """Repositorio relacional en memoria con semántica ACID y semillas del Entregable 4."""

    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state

    def get_parcela_with_productor(self, parcela_id: int) -> dict[str, Any] | None:
        pa = self.state["parcelas"].get(parcela_id)
        if not pa:
            return None
        pr = self.state["productores"][pa["productor_id"]]
        return {
            **pa,
            "rfc": pr["rfc"],
            "nombre_razon_social": pr["nombre_razon_social"],
            "telefono": pr["telefono"],
            "productor_activo": pr["activo"],
        }

    def get_lote_by_codigo(self, codigo_lote: str) -> dict[str, Any] | None:
        lote = self.state["lotes"].get(codigo_lote)
        if not lote:
            return None
        pa = self.state["parcelas"][lote["parcela_id"]]
        pr = self.state["productores"][pa["productor_id"]]
        return {
            **deepcopy(lote),
            "codigo_senasica": pa["codigo_senasica"],
            "nombre_huerta": pa["nombre_huerta"],
            "municipio": pa["municipio"],
            "productor_id": pr["productor_id"],
            "productor_rfc": pr["rfc"],
            "productor_nombre": pr["nombre_razon_social"],
        }

    def get_recepcion_by_lote_id(self, lote_id: int) -> dict[str, Any] | None:
        for rec in self.state["recepciones"].values():
            if rec["lote_id"] == lote_id:
                return deepcopy(rec)
        return None

    def get_incidentes_by_lote_id(self, lote_id: int) -> list[dict[str, Any]]:
        return [
            deepcopy(inc)
            for inc in self.state["incidentes_bitacora"]
            if inc["lote_id"] == lote_id
        ]

    def get_incidente_by_folio(self, folio_incidente: str) -> dict[str, Any] | None:
        for inc in self.state["incidentes_bitacora"]:
            if inc["folio_incidente"] == folio_incidente:
                return deepcopy(inc)
        return None

    def get_tienda_by_id(self, tienda_id: int) -> dict[str, Any] | None:
        t = self.state["tiendas"].get(tienda_id)
        return deepcopy(t) if t else None

    def list_lotes(self, productor_id: int | None = None, estado: str | None = None) -> list[dict[str, Any]]:
        rows = []
        for codigo in self.state["lotes"]:
            row = self.get_lote_by_codigo(codigo)
            assert row is not None
            if productor_id is not None and row["productor_id"] != productor_id:
                continue
            if estado is not None and row["estado"] != estado:
                continue
            rows.append(row)
        return rows

    def create_lote(
        self,
        *,
        codigo_lote: str,
        parcela_id: int,
        producto: str,
        fecha_cosecha: datetime,
        cuadrilla_cosecha: str,
        peso_inicial_kg: float,
    ) -> dict[str, Any]:
        if codigo_lote in self.state["lotes"]:
            raise ConflictError(
                f"Ya existe un lote registrado con el código '{codigo_lote}'.",
                error_code="LOTE_DUPLICADO",
            )
        if parcela_id not in self.state["parcelas"]:
            raise NotFoundError(
                f"La parcela {parcela_id} no existe en el catálogo maestro.",
                error_code="PARCELA_NO_ENCONTRADA",
            )
        self.state["seq_lote"] += 1
        now = datetime.now(timezone.utc)
        row = {
            "lote_id": self.state["seq_lote"],
            "codigo_lote": codigo_lote,
            "parcela_id": parcela_id,
            "producto": producto,
            "fecha_cosecha": fecha_cosecha,
            "cuadrilla_cosecha": cuadrilla_cosecha,
            "peso_inicial_kg": float(peso_inicial_kg),
            "saldo_kg": float(peso_inicial_kg),
            "estado": "Cosechado",
            "fecha_actualizacion": now,
        }
        self.state["lotes"][codigo_lote] = row
        return deepcopy(row)

    def create_recepcion(
        self,
        *,
        folio_recepcion: str,
        codigo_lote: str,
        placas_vehiculo: str,
        codigo_cuarto_frio: str,
        peso_recibido_kg: float,
        temperatura_llegada_c: float,
        dictamen_recepcion: str,
        nuevo_estado_lote: str,
        fecha_llegada: datetime,
    ) -> dict[str, Any]:
        lote = self.state["lotes"].get(codigo_lote)
        if lote is None:
            raise NotFoundError(f"El lote '{codigo_lote}' no existe.", error_code="LOTE_NO_ENCONTRADO")
        if lote["estado"] != "Cosechado":
            raise ConflictError(
                f"El lote '{codigo_lote}' está en estado '{lote['estado']}' y no puede recibirse nuevamente.",
                error_code="LOTE_ESTADO_INVALIDO_RECEPCION",
            )
        if folio_recepcion in self.state["recepciones"]:
            raise ConflictError(
                f"El folio '{folio_recepcion}' ya existe.",
                error_code="RECEPCION_DUPLICADA",
            )
        self.state["seq_rec"] += 1
        rec = {
            "recepcion_id": self.state["seq_rec"],
            "folio_recepcion": folio_recepcion,
            "lote_id": lote["lote_id"],
            "fecha_llegada": fecha_llegada,
            "placas_vehiculo": placas_vehiculo,
            "codigo_cuarto_frio": codigo_cuarto_frio,
            "peso_recibido_kg": float(peso_recibido_kg),
            "temperatura_llegada_c": float(temperatura_llegada_c),
            "dictamen_recepcion": dictamen_recepcion,
        }
        self.state["recepciones"][folio_recepcion] = rec
        lote["estado"] = nuevo_estado_lote
        lote["fecha_actualizacion"] = datetime.now(timezone.utc)
        return deepcopy(rec)

    def liberar_lote(
        self,
        *,
        codigo_lote: str,
        usuario_responsable: str,
        motivo: str,
        folio_evento: str,
    ) -> dict[str, Any]:
        lote = self.state["lotes"].get(codigo_lote)
        if lote is None:
            raise NotFoundError(f"El lote '{codigo_lote}' no existe.", error_code="LOTE_NO_ENCONTRADO")
        if lote["estado"] in ("Bloqueado", "Retirado"):
            raise ConflictError(
                f"No se puede liberar el lote '{codigo_lote}' porque está '{lote['estado']}'.",
                error_code="LOTE_BLOQUEADO_O_RETIRADO",
            )
        if lote["estado"] == "Liberado":
            raise ConflictError(
                f"El lote '{codigo_lote}' ya se encuentra en estado 'Liberado'.",
                error_code="LOTE_YA_LIBERADO",
            )
        estado_previo = lote["estado"]
        lote["estado"] = "Liberado"
        lote["fecha_actualizacion"] = datetime.now(timezone.utc)
        self.state["seq_inc"] += 1
        self.state["incidentes_bitacora"].append(
            {
                "incidente_id": self.state["seq_inc"],
                "folio_incidente": folio_evento,
                "lote_id": lote["lote_id"],
                "usuario_responsable": usuario_responsable,
                "motivo": motivo[:250],
                "estado_previo": estado_previo,
                "nuevo_estado": "Liberado",
                "fecha_evento": datetime.now(timezone.utc),
            }
        )
        return {
            "lote_id": lote["lote_id"],
            "codigo_lote": lote["codigo_lote"],
            "estado": lote["estado"],
            "saldo_kg": lote["saldo_kg"],
            "fecha_actualizacion": lote["fecha_actualizacion"],
            "estado_previo": estado_previo,
            "folio_evento": folio_evento,
        }

    def create_envio_fraccionado(
        self,
        *,
        codigo_envio: str,
        tienda_id: int,
        placas_vehiculo: str,
        detalles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if codigo_envio in self.state["envios"]:
            raise ConflictError(
                f"Ya existe un envío con código '{codigo_envio}'.",
                error_code="ENVIO_DUPLICADO",
            )
        tienda = self.state["tiendas"].get(tienda_id)
        if tienda is None:
            raise NotFoundError(f"La tienda {tienda_id} no existe.", error_code="TIENDA_NO_ENCONTRADA")
        if not tienda["activo"]:
            raise ConflictError(
                f"La tienda '{tienda['codigo_sucursal']}' está inactiva (RN-10).",
                error_code="TIENDA_INACTIVA",
            )

        # Validación atómica antes de mutar (simula ROLLBACK ACID ante cualquier error)
        staged: list[tuple[dict[str, Any], float]] = []
        total_kg = 0.0
        for item in detalles:
            code = item["codigo_lote"]
            qty = float(item["cantidad_kg"])
            lote = self.state["lotes"].get(code)
            if lote is None:
                raise NotFoundError(f"El lote '{code}' no existe.", error_code="LOTE_NO_ENCONTRADO")
            if lote["estado"] != "Liberado":
                raise ConflictError(
                    f"El lote {code} se encuentra en estado '{lote['estado']}' y no puede despacharse (RN-01).",
                    error_code="LOTE_NO_DISPONIBLE_PARA_DESPACHO",
                    extra={"codigo_lote": code},
                )
            if qty > lote["saldo_kg"]:
                raise ConflictError(
                    f"Saldo insuficiente en lote {code}: disponible {lote['saldo_kg']:.2f} kg, solicitado {qty:.2f} kg (RN-03).",
                    error_code="SALDO_INSUFICIENTE",
                    extra={"codigo_lote": code},
                )
            staged.append((lote, qty))
            total_kg += qty

        # Commit atómico
        self.state["seq_env"] += 1
        envio = {
            "envio_id": self.state["seq_env"],
            "codigo_envio": codigo_envio,
            "tienda_id": tienda_id,
            "placas_vehiculo": placas_vehiculo,
            "fecha_despacho": datetime.now(timezone.utc),
            "estado_envio": "Preparado",
        }
        self.state["envios"][codigo_envio] = envio
        saldos_actualizados = []
        for lote, qty in staged:
            lote["saldo_kg"] = round(lote["saldo_kg"] - qty, 2)
            lote["fecha_actualizacion"] = datetime.now(timezone.utc)
            saldos_actualizados.append(
                {"codigo_lote": lote["codigo_lote"], "saldo_kg_restante": lote["saldo_kg"]}
            )

        return {
            "envio": deepcopy(envio),
            "tienda": deepcopy(tienda),
            "total_kg": round(total_kg, 2),
            "saldos_actualizados": saldos_actualizados,
        }

    def bloquear_lotes_recall(
        self,
        *,
        folio_incidente: str,
        codigo_lote_origen: str,
        codigos_lotes_hermanos: list[str],
        usuario_responsable: str,
        motivo: str,
    ) -> dict[str, Any]:
        if codigo_lote_origen not in self.state["lotes"]:
            raise NotFoundError(
                f"El lote origen '{codigo_lote_origen}' no existe.",
                error_code="LOTE_NO_ENCONTRADO",
            )
        all_codes = sorted({codigo_lote_origen, *codigos_lotes_hermanos})
        bloqueados: dict[str, dict[str, Any]] = {}
        for code in all_codes:
            lote = self.state["lotes"].get(code)
            if lote is None:
                continue
            prev = lote["estado"]
            lote["estado"] = "Bloqueado"
            lote["fecha_actualizacion"] = datetime.now(timezone.utc)
            bloqueados[code] = {
                "lote_id": lote["lote_id"],
                "codigo_lote": code,
                "estado": "Bloqueado",
                "saldo_kg": lote["saldo_kg"],
                "estado_previo": prev,
            }

        self.state["seq_inc"] += 1
        bitacora = {
            "incidente_id": self.state["seq_inc"],
            "folio_incidente": folio_incidente,
            "lote_id": bloqueados[codigo_lote_origen]["lote_id"],
            "usuario_responsable": usuario_responsable,
            "motivo": motivo[:250],
            "estado_previo": bloqueados[codigo_lote_origen]["estado_previo"],
            "nuevo_estado": "Bloqueado",
            "fecha_evento": datetime.now(timezone.utc),
        }
        self.state["incidentes_bitacora"].append(bitacora)
        return {
            "bitacora": deepcopy(bitacora),
            "lote_origen": bloqueados[codigo_lote_origen],
            "lotes_bloqueados": bloqueados,
        }

    def registrar_cierre_incidente_bitacora(
        self,
        *,
        folio_cierre: str,
        lote_id: int,
        usuario_responsable: str,
        motivo: str,
        nuevo_estado: str = "Retirado",
    ) -> dict[str, Any]:
        target = None
        for lote in self.state["lotes"].values():
            if lote["lote_id"] == lote_id:
                target = lote
                break
        if target is None:
            raise NotFoundError("Lote asociado al incidente no encontrado.")
        prev = target["estado"]
        target["estado"] = nuevo_estado
        self.state["seq_inc"] += 1
        row = {
            "incidente_id": self.state["seq_inc"],
            "folio_incidente": folio_cierre,
            "lote_id": lote_id,
            "usuario_responsable": usuario_responsable,
            "motivo": motivo[:250],
            "estado_previo": prev,
            "nuevo_estado": nuevo_estado,
            "fecha_evento": datetime.now(timezone.utc),
        }
        self.state["incidentes_bitacora"].append(row)
        return deepcopy(row)

    def insert_reconciliation_event(
        self,
        *,
        destino_motor: str,
        tipo_operacion: str,
        llave_entidad: str,
        payload: dict[str, Any],
        ultimo_error: str | None = None,
    ) -> int:
        self.state["seq_outbox"] += 1
        ev = {
            "evento_id": self.state["seq_outbox"],
            "destino_motor": destino_motor,
            "tipo_operacion": tipo_operacion,
            "llave_entidad": llave_entidad,
            "payload_json": deepcopy(payload),
            "estado": "PENDIENTE",
            "intentos": 1,
            "ultimo_error": ultimo_error,
            "fecha_creacion": datetime.now(timezone.utc),
        }
        self.state["outbox"].append(ev)
        return ev["evento_id"]

    def get_pending_reconciliation_events(self, limit: int = 50) -> list[dict[str, Any]]:
        return [
            deepcopy(ev)
            for ev in self.state["outbox"]
            if ev["estado"] in ("PENDIENTE", "ERROR")
        ][:limit]

    def mark_reconciliation_event(
        self,
        *,
        evento_id: int,
        estado: str,
        ultimo_error: str | None = None,
    ) -> None:
        for ev in self.state["outbox"]:
            if ev["evento_id"] == evento_id:
                ev["estado"] = estado
                ev["intentos"] += 1
                ev["ultimo_error"] = ultimo_error
                break


class FakeMongoRepo:
    """Repositorio documental en memoria con versionado inmutable RN-05, $elemMatch y RN-09."""

    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state

    def _check_fail(self) -> None:
        if self.state.get("fail_mongo"):
            raise RuntimeError("Simulated MongoDB outage")

    def get_analisis_vigente(self, codigo_lote: str, tipo_estudio: str) -> dict[str, Any] | None:
        self._check_fail()
        for doc in self.state["analisis"]:
            if (
                doc["codigo_lote"] == codigo_lote
                and doc["tipo_estudio"] == tipo_estudio
                and doc["es_vigente"] is True
            ):
                return deepcopy(doc)
        return None

    def list_analisis_by_lote(
        self,
        codigo_lote: str,
        *,
        solo_vigentes: bool = False,
        solo_no_conformes: bool = False,
    ) -> list[dict[str, Any]]:
        self._check_fail()
        res = []
        for doc in self.state["analisis"]:
            if doc["codigo_lote"] != codigo_lote:
                continue
            if solo_vigentes and not doc["es_vigente"]:
                continue
            if solo_no_conformes:
                has_bad = any(
                    det.get("conforme") is False
                    for m in doc.get("muestras", [])
                    for det in m.get("determinaciones", [])
                )
                if not has_bad:
                    continue
            res.append(deepcopy(doc))
        return sorted(res, key=lambda d: (d["tipo_estudio"], -d["version"]))

    def insert_analisis_versionado(self, doc: dict[str, Any]) -> dict[str, Any]:
        self._check_fail()
        if any(a["folio_analisis"] == doc["folio_analisis"] for a in self.state["analisis"]):
            raise ConflictError(
                f"Ya existe un certificado de laboratorio con folio '{doc['folio_analisis']}'.",
                error_code="ANALISIS_FOLIO_DUPLICADO",
            )
        prev = None
        for existing in self.state["analisis"]:
            if (
                existing["codigo_lote"] == doc["codigo_lote"]
                and existing["tipo_estudio"] == doc["tipo_estudio"]
                and existing["es_vigente"] is True
            ):
                prev = existing
                break
        if prev is not None:
            if not doc.get("motivo_enmienda"):
                raise ValidationDomainError(
                    "Ya existe un análisis vigente para este lote y tipo de estudio; se requiere 'motivo_enmienda' para emitir una nueva versión (RN-05)."
                )
            doc["version"] = int(prev["version"]) + 1
            doc["folio_reemplazado"] = prev["folio_analisis"]
            prev["es_vigente"] = False
        else:
            doc["version"] = 1
            doc["folio_reemplazado"] = None

        doc["es_vigente"] = True
        self.state["analisis"].append(deepcopy(doc))
        return deepcopy(doc)

    def get_parametros_infractores_vigentes(self, codigo_lote: str) -> dict[str, Any] | None:
        self._check_fail()
        for doc in self.list_analisis_by_lote(codigo_lote, solo_vigentes=True, solo_no_conformes=True):
            infractores = [
                det
                for m in doc.get("muestras", [])
                for det in m.get("determinaciones", [])
                if det.get("conforme") is False
            ]
            return {
                "folio_analisis": doc["folio_analisis"],
                "laboratorio": doc.get("laboratorio", {}).get("nombre", ""),
                "parametros_infractores": infractores,
            }
        return None

    def insert_acta_recepcion(self, doc: dict[str, Any]) -> dict[str, Any]:
        self._check_fail()
        if doc["folio_recepcion"] in self.state["actas"]:
            return deepcopy(self.state["actas"][doc["folio_recepcion"]])
        self.state["actas"][doc["folio_recepcion"]] = deepcopy(doc)
        return deepcopy(doc)

    def get_acta_recepcion_by_lote(self, codigo_lote: str) -> dict[str, Any] | None:
        self._check_fail()
        for doc in self.state["actas"].values():
            if doc["codigo_lote"] == codigo_lote:
                return deepcopy(doc)
        return None

    def create_expediente_incidente(self, doc: dict[str, Any]) -> dict[str, Any]:
        self._check_fail()
        if doc["folio_incidente"] in self.state["expedientes"]:
            return deepcopy(self.state["expedientes"][doc["folio_incidente"]])
        self.state["expedientes"][doc["folio_incidente"]] = deepcopy(doc)
        return deepcopy(doc)

    def get_expediente_incidente(self, folio_incidente: str) -> dict[str, Any] | None:
        self._check_fail()
        doc = self.state["expedientes"].get(folio_incidente)
        return deepcopy(doc) if doc else None

    def list_expedientes_by_lote(self, codigo_lote: str) -> list[dict[str, Any]]:
        self._check_fail()
        return [
            deepcopy(doc)
            for doc in self.state["expedientes"].values()
            if codigo_lote in doc.get("lotes_afectados", [])
        ]

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
        self._check_fail()
        exp = self.state["expedientes"].get(folio_incidente)
        if exp is None:
            raise NotFoundError(
                f"No existe el expediente de incidente '{folio_incidente}'.",
                error_code="EXPEDIENTE_NO_ENCONTRADO",
            )
        if exp["estado_expediente"] == "Cerrado":
            raise ConflictError(
                f"El expediente '{folio_incidente}' ya se encuentra cerrado.",
                error_code="EXPEDIENTE_YA_CERRADO",
            )
        now = datetime.now(timezone.utc)
        exp["estado_expediente"] = "Cerrado"
        exp["fecha_cierre"] = now
        exp["causa_raiz"] = causa_raiz
        exp["acciones_correctivas"] = list(acciones_correctivas)
        exp["firmas_cierre"] = {
            "responsable_qa": responsable_qa,
            "aprobacion_gerencia": aprobacion_gerencia,
        }
        exp["linea_tiempo"].append(
            {
                "fecha_hora": now,
                "actor": actor,
                "descripcion": f"Cierre formal aprobado por QA ({responsable_qa}) y Gerencia ({aprobacion_gerencia}).",
            }
        )
        return deepcopy(exp)


class FakeNeo4jRepo:
    """Repositorio de grafos en memoria con semántica MERGE idempotente y recorridos Forward/Lateral."""

    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state

    def _check_fail(self) -> None:
        if self.state.get("fail_neo4j"):
            raise RuntimeError("Simulated Neo4j outage")

    def merge_lote_cosechado(self, **kwargs: Any) -> None:
        self._check_fail()
        code = kwargs["codigo_lote"]
        self.state["neo4j_lotes"][code] = {
            "codigo_lote": code,
            "producto": kwargs["producto"],
            "estado": kwargs["estado"],
            "parcela": deepcopy(kwargs["parcela"]),
            "cuadrilla_cosecha": kwargs["cuadrilla_cosecha"],
            "fecha_cosecha": kwargs["fecha_cosecha"].isoformat(),
        }

    def merge_recepcion_fisica(self, **kwargs: Any) -> None:
        self._check_fail()
        code = kwargs["codigo_lote"]
        self.state["neo4j_lotes"].setdefault(code, {"codigo_lote": code})["estado"] = kwargs["estado_lote"]
        self.state["neo4j_recepciones"][code] = {
            "folio_recepcion": kwargs["folio_recepcion"],
            "vehiculo_entrada": kwargs["placas_vehiculo"],
            "chofer_entrada": kwargs["nombre_chofer"],
            "codigo_cuarto_frio": kwargs["codigo_cuarto_frio"],
            "temperatura_llegada_c": kwargs["temperatura_llegada_c"],
            "fecha_llegada": kwargs["fecha_llegada"],
        }

    def merge_analisis_proyeccion(self, **kwargs: Any) -> None:
        self._check_fail()
        code = kwargs["codigo_lote"]
        entries = self.state["neo4j_analisis"].setdefault(code, [])
        if kwargs.get("folio_reemplazado"):
            for e in entries:
                if e["folio_analisis"] == kwargs["folio_reemplazado"]:
                    e["es_vigente"] = False
        # Idempotente por folio_analisis
        entries = [e for e in entries if e["folio_analisis"] != kwargs["folio_analisis"]]
        entries.append(
            {
                "laboratorio": kwargs["nombre_laboratorio"],
                "acreditacion_iso": kwargs["acreditacion_iso"],
                "folio_analisis": kwargs["folio_analisis"],
                "tipo_estudio": kwargs["tipo_estudio"],
                "dictamen_general": kwargs["dictamen_general"],
                "es_vigente": True,
                "fecha_emision": kwargs["fecha_emision"].isoformat(),
            }
        )
        self.state["neo4j_analisis"][code] = entries

    def merge_envio_proyeccion(self, **kwargs: Any) -> None:
        self._check_fail()
        tienda = kwargs["tienda"]
        for det in kwargs["detalles"]:
            code = det["codigo_lote"]
            envios = self.state["neo4j_envios"].setdefault(code, [])
            envios = [e for e in envios if e["codigo_envio"] != kwargs["codigo_envio"]]
            envios.append(
                {
                    "tienda_id": tienda["tienda_id"],
                    "codigo_sucursal": tienda["codigo_sucursal"],
                    "nombre_comercial": tienda["nombre_comercial"],
                    "ciudad": tienda.get("ciudad", ""),
                    "codigo_envio": kwargs["codigo_envio"],
                    "estado_envio": kwargs["estado_envio"],
                    "fecha_despacho": kwargs["fecha_despacho"].isoformat(),
                    "cantidad_kg": float(det["cantidad_kg"]),
                    "placas_vehiculo": kwargs["placas_vehiculo"],
                    "nombre_chofer": kwargs["nombre_chofer"],
                }
            )
            self.state["neo4j_envios"][code] = envios

    def update_lotes_estado(self, codigos_lotes: list[str], nuevo_estado: str) -> None:
        self._check_fail()
        for code in codigos_lotes:
            self.state["neo4j_lotes"].setdefault(code, {"codigo_lote": code})["estado"] = nuevo_estado

    def rastreo_adelante(self, codigo_lote: str) -> list[dict[str, Any]]:
        self._check_fail()
        return deepcopy(self.state["neo4j_envios"].get(codigo_lote, []))

    def rastreo_atras(self, codigo_lote: str) -> dict[str, Any] | None:
        self._check_fail()
        node = self.state["neo4j_lotes"].get(codigo_lote)
        if not node or "parcela" not in node:
            return None
        pa = node["parcela"]
        return {
            "codigo_lote": codigo_lote,
            "estado": node.get("estado"),
            "cuadrilla_cosecha": node.get("cuadrilla_cosecha"),
            "parcela_id": pa["parcela_id"],
            "codigo_senasica": pa["codigo_senasica"],
            "nombre_huerta": pa["nombre_huerta"],
            "municipio": pa["municipio"],
            "productor_id": pa["productor_id"],
            "rfc": pa["rfc"],
            "nombre_razon_social": pa["nombre_razon_social"],
        }

    def rastreo_lateral(self, codigo_lote: str, ventana_dias: int = 1) -> list[dict[str, Any]]:
        self._check_fail()
        origin_rec = self.state["neo4j_recepciones"].get(codigo_lote)
        if not origin_rec:
            return []
        hermanos = []
        for other_code, other_rec in self.state["neo4j_recepciones"].items():
            if other_code == codigo_lote:
                continue
            delta_days = abs((origin_rec["fecha_llegada"] - other_rec["fecha_llegada"]).days)
            if delta_days > ventana_dias:
                continue
            if origin_rec["vehiculo_entrada"] == other_rec["vehiculo_entrada"]:
                hermanos.append(
                    {
                        "codigo_lote": other_code,
                        "estado": self.state["neo4j_lotes"].get(other_code, {}).get("estado"),
                        "causa_vinculo": f"Vehículo {origin_rec['vehiculo_entrada']}",
                        "tipo_recurso": "Vehiculo",
                        "identificador_recurso": origin_rec["vehiculo_entrada"],
                    }
                )
            elif origin_rec["codigo_cuarto_frio"] == other_rec["codigo_cuarto_frio"]:
                hermanos.append(
                    {
                        "codigo_lote": other_code,
                        "estado": self.state["neo4j_lotes"].get(other_code, {}).get("estado"),
                        "causa_vinculo": f"Cuarto Frío {origin_rec['codigo_cuarto_frio']}",
                        "tipo_recurso": "CuartoFrio",
                        "identificador_recurso": origin_rec["codigo_cuarto_frio"],
                    }
                )
        return hermanos

    def get_red_lote_360(self, codigo_lote: str) -> dict[str, Any]:
        self._check_fail()
        rec = self.state["neo4j_recepciones"].get(codigo_lote)
        return {
            "logistica_entrada": {
                "vehiculo_entrada": rec["vehiculo_entrada"],
                "chofer_entrada": rec["chofer_entrada"],
                "temperatura_llegada_c": rec["temperatura_llegada_c"],
                "codigo_cuarto_frio": rec["codigo_cuarto_frio"],
            }
            if rec
            else None,
            "laboratorios": deepcopy(self.state["neo4j_analisis"].get(codigo_lote, [])),
            "envios_tiendas": self.rastreo_adelante(codigo_lote),
            "lotes_hermanos": self.rastreo_lateral(codigo_lote, ventana_dias=1),
        }


def _build_initial_state() -> dict[str, Any]:
    now = datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc)
    return {
        "fail_mongo": False,
        "fail_neo4j": False,
        "seq_lote": 10,
        "seq_rec": 10,
        "seq_env": 10,
        "seq_inc": 10,
        "seq_outbox": 0,
        "productores": {
            1: {
                "productor_id": 1,
                "rfc": "AUM180412H59",
                "nombre_razon_social": "Aguacateros Unidos de Michoacán S.P.R. de R.L.",
                "telefono": "452-523-8810",
                "activo": True,
            },
            2: {
                "productor_id": 2,
                "rfc": "HTI200905M14",
                "nombre_razon_social": "Huertas del Tancítaro S.A. de C.V.",
                "telefono": "452-519-4402",
                "activo": True,
            },
            3: {
                "productor_id": 3,
                "rfc": "ASP150219K81",
                "nombre_razon_social": "Agroexportadora San Pedro S.A. de C.V.",
                "telefono": "341-412-9077",
                "activo": False,
            },
        },
        "parcelas": {
            1: {
                "parcela_id": 1,
                "productor_id": 1,
                "codigo_senasica": "SENASICA-MICH-URU-014",
                "nombre_huerta": "Huerta La Escondida",
                "municipio": "Uruapan, Michoacán",
                "superficie_ha": 18.5,
            },
            3: {
                "parcela_id": 3,
                "productor_id": 2,
                "codigo_senasica": "SENASICA-MICH-TAN-018",
                "nombre_huerta": "Huerta Los Pinos",
                "municipio": "Tancítaro, Michoacán",
                "superficie_ha": 32.75,
            },
            4: {
                "parcela_id": 4,
                "productor_id": 3,
                "codigo_senasica": "SENASICA-JAL-ZAP-022",
                "nombre_huerta": "Huerta Santa Rosa",
                "municipio": "Zapotlán el Grande, Jalisco",
                "superficie_ha": 12.0,
            },
        },
        "tiendas": {
            1: {
                "tienda_id": 1,
                "codigo_sucursal": "SUC-MTY-04",
                "nombre_comercial": "Supermercados del Norte - Valle",
                "direccion": "Av. Vasconcelos 345",
                "ciudad": "Monterrey, N.L.",
                "activo": True,
            },
            4: {
                "tienda_id": 4,
                "codigo_sucursal": "SUC-QRO-01",
                "nombre_comercial": "Distribución Horeca Bajío",
                "direccion": "Blvd. Bernardo Quintana 4100",
                "ciudad": "Querétaro, Qro.",
                "activo": False,
            },
        },
        "lotes": {
            "AGU-P014-260312-01": {
                "lote_id": 1,
                "codigo_lote": "AGU-P014-260312-01",
                "parcela_id": 1,
                "producto": "Aguacate Hass",
                "fecha_cosecha": now,
                "cuadrilla_cosecha": "Cuadrilla Alfa-01",
                "peso_inicial_kg": 2000.0,
                "saldo_kg": 1150.0,
                "estado": "Bloqueado",
                "fecha_actualizacion": now,
            },
            "AGU-P018-260314-01": {
                "lote_id": 3,
                "codigo_lote": "AGU-P018-260314-01",
                "parcela_id": 3,
                "producto": "Aguacate Hass",
                "fecha_cosecha": now,
                "cuadrilla_cosecha": "Cuadrilla Tancítaro-03",
                "peso_inicial_kg": 3000.0,
                "saldo_kg": 2050.0,
                "estado": "Liberado",
                "fecha_actualizacion": now,
            },
        },
        "recepciones": {},
        "envios": {},
        "incidentes_bitacora": [],
        "outbox": [],
        "analisis": [],
        "actas": {},
        "expedientes": {},
        "neo4j_lotes": {},
        "neo4j_recepciones": {},
        "neo4j_analisis": {},
        "neo4j_envios": {},
    }


@pytest.fixture()
def fake_state(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    state = _build_initial_state()
    login_rate_limiter.reset()
    recall_rate_limiter.reset()

    pg_factory = lambda _conn=None: FakePostgresRepo(state)
    mg_factory = lambda _db=None: FakeMongoRepo(state)
    n4j_factory = lambda _drv=None: FakeNeo4jRepo(state)

    # Parchear dependencias FastAPI para no abrir sockets reales
    app.dependency_overrides[get_pg_connection] = lambda: object()
    app.dependency_overrides[get_mongo_db] = lambda: object()
    app.dependency_overrides[get_neo4j_driver] = lambda: object()

    for mod_path in [
        "backend.controllers.lotes",
        "backend.controllers.recepciones",
        "backend.controllers.analisis",
        "backend.controllers.envios",
        "backend.controllers.incidentes",
        "backend.controllers.trazabilidad",
        "backend.controllers.reconciliacion",
    ]:
        monkeypatch.setattr(f"{mod_path}.PostgresRepository", pg_factory, raising=False)
        monkeypatch.setattr(f"{mod_path}.MongoRepository", mg_factory, raising=False)
        monkeypatch.setattr(f"{mod_path}.Neo4jRepository", n4j_factory, raising=False)

    yield state
    app.dependency_overrides.clear()


@pytest.fixture()
def client(fake_state: dict[str, Any]) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _auth_header(sub: str, username: str, nombre: str, role: str, productor_id: int | None = None) -> dict[str, str]:
    token, _ = create_access_token(
        sub=sub,
        username=username,
        nombre=nombre,
        role=role,
        productor_id=productor_id,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def headers_qa() -> dict[str, str]:
    return _auth_header("usr-qa-01", "qa_admin", "Ing. Valeria Mendoza (QA)", ROLE_QA)


@pytest.fixture()
def headers_recepcion() -> dict[str, str]:
    return _auth_header("usr-rec-01", "recepcion_cedis", "Carlos Herrera (CEDIS)", ROLE_RECEPCION)


@pytest.fixture()
def headers_lab() -> dict[str, str]:
    return _auth_header("usr-lab-01", "lab_agrobio", "Q.F.B. Sofía Ríos", ROLE_LABORATORIO)


@pytest.fixture()
def headers_productor_1() -> dict[str, str]:
    return _auth_header("usr-prod-01", "productor_michoacan", "Aguacateros Unidos", ROLE_PRODUCTOR, productor_id=1)


@pytest.fixture()
def headers_productor_2() -> dict[str, str]:
    return _auth_header("usr-prod-02", "productor_tancitaro", "Huertas del Tancítaro", ROLE_PRODUCTOR, productor_id=2)
