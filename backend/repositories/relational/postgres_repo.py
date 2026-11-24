from datetime import datetime
from decimal import Decimal
import json
from typing import Any

from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation
from psycopg.rows import dict_row

from backend.core.exceptions import ConflictError, NotFoundError, ValidationDomainError


def _to_float(val: Any) -> Any:
    if isinstance(val, Decimal):
        return float(val)
    return val


def _normalize_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: _to_float(v) for k, v in row.items()}


class PostgresRepository:
    """Repositorio relacional con consultas SQL 100% parametrizadas sobre PostgreSQL."""

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    # ------------------------------------------------------------------
    # Catálogos y consultas de lectura
    # ------------------------------------------------------------------
    def get_parcela_with_productor(self, parcela_id: int) -> dict[str, Any] | None:
        sql = """
            SELECT
                pa.parcela_id,
                pa.productor_id,
                pa.codigo_senasica,
                pa.nombre_huerta,
                pa.municipio,
                pa.superficie_ha,
                pr.rfc,
                pr.nombre_razon_social,
                pr.telefono,
                pr.activo AS productor_activo
            FROM parcelas pa
            JOIN productores pr ON pa.productor_id = pr.productor_id
            WHERE pa.parcela_id = %s
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (parcela_id,))
            return _normalize_row(cur.fetchone())

    def get_lote_by_codigo(self, codigo_lote: str) -> dict[str, Any] | None:
        sql = """
            SELECT
                l.lote_id,
                l.codigo_lote,
                l.parcela_id,
                l.producto,
                l.fecha_cosecha,
                l.cuadrilla_cosecha,
                l.peso_inicial_kg,
                l.saldo_kg,
                l.estado,
                l.fecha_actualizacion,
                pa.codigo_senasica,
                pa.nombre_huerta,
                pa.municipio,
                pr.productor_id,
                pr.rfc AS productor_rfc,
                pr.nombre_razon_social AS productor_nombre
            FROM lotes l
            JOIN parcelas pa ON l.parcela_id = pa.parcela_id
            JOIN productores pr ON pa.productor_id = pr.productor_id
            WHERE l.codigo_lote = %s
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (codigo_lote,))
            return _normalize_row(cur.fetchone())

    def get_recepcion_by_lote_id(self, lote_id: int) -> dict[str, Any] | None:
        sql = """
            SELECT
                recepcion_id,
                folio_recepcion,
                lote_id,
                fecha_llegada,
                placas_vehiculo,
                codigo_cuarto_frio,
                peso_recibido_kg,
                temperatura_llegada_c,
                dictamen_recepcion
            FROM recepciones_cedis
            WHERE lote_id = %s
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (lote_id,))
            return _normalize_row(cur.fetchone())

    def get_incidentes_by_lote_id(self, lote_id: int) -> list[dict[str, Any]]:
        sql = """
            SELECT
                incidente_id,
                folio_incidente,
                lote_id,
                usuario_responsable,
                motivo,
                estado_previo,
                nuevo_estado,
                fecha_evento
            FROM incidentes_bitacora
            WHERE lote_id = %s
            ORDER BY fecha_evento DESC
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (lote_id,))
            return [_normalize_row(r) for r in cur.fetchall()]  # type: ignore[misc]

    def get_incidente_by_folio(self, folio_incidente: str) -> dict[str, Any] | None:
        sql = """
            SELECT
                ib.incidente_id,
                ib.folio_incidente,
                ib.lote_id,
                l.codigo_lote,
                ib.usuario_responsable,
                ib.motivo,
                ib.estado_previo,
                ib.nuevo_estado,
                ib.fecha_evento
            FROM incidentes_bitacora ib
            JOIN lotes l ON ib.lote_id = l.lote_id
            WHERE ib.folio_incidente = %s
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (folio_incidente,))
            return _normalize_row(cur.fetchone())

    def get_tienda_by_id(self, tienda_id: int) -> dict[str, Any] | None:
        sql = """
            SELECT tienda_id, codigo_sucursal, nombre_comercial, direccion, ciudad, activo
            FROM tiendas
            WHERE tienda_id = %s
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (tienda_id,))
            return _normalize_row(cur.fetchone())

    def get_lotes_listos_despacho(self) -> list[dict[str, Any]]:
        sql = """
            SELECT
                lote_id,
                codigo_lote,
                producto,
                fecha_cosecha,
                peso_inicial_kg,
                saldo_kg,
                codigo_senasica,
                nombre_huerta,
                municipio,
                productor
            FROM v_lotes_listos_despacho
            ORDER BY fecha_cosecha ASC
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql)
            return [_normalize_row(r) for r in cur.fetchall()]  # type: ignore[misc]

    def list_lotes(self, productor_id: int | None = None, estado: str | None = None) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if productor_id is not None:
            clauses.append("pr.productor_id = %s")
            params.append(productor_id)
        if estado is not None:
            clauses.append("l.estado = %s")
            params.append(estado)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT
                l.lote_id,
                l.codigo_lote,
                l.parcela_id,
                l.producto,
                l.fecha_cosecha,
                l.cuadrilla_cosecha,
                l.peso_inicial_kg,
                l.saldo_kg,
                l.estado,
                l.fecha_actualizacion,
                pa.nombre_huerta,
                pr.productor_id,
                pr.nombre_razon_social AS productor_nombre
            FROM lotes l
            JOIN parcelas pa ON l.parcela_id = pa.parcela_id
            JOIN productores pr ON pa.productor_id = pr.productor_id
            {where_sql}
            ORDER BY l.fecha_cosecha DESC
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, tuple(params))
            return [_normalize_row(r) for r in cur.fetchall()]  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Escrituras transaccionales ACID
    # ------------------------------------------------------------------
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
        sql = """
            INSERT INTO lotes (
                codigo_lote, parcela_id, producto, fecha_cosecha,
                cuadrilla_cosecha, peso_inicial_kg, saldo_kg, estado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Cosechado')
            RETURNING
                lote_id, codigo_lote, parcela_id, producto, fecha_cosecha,
                cuadrilla_cosecha, peso_inicial_kg, saldo_kg, estado, fecha_actualizacion
        """
        try:
            with self.conn.transaction():
                with self.conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        sql,
                        (
                            codigo_lote,
                            parcela_id,
                            producto,
                            fecha_cosecha,
                            cuadrilla_cosecha,
                            peso_inicial_kg,
                            peso_inicial_kg,
                        ),
                    )
                    row = cur.fetchone()
            return _normalize_row(row)  # type: ignore[return-value]
        except UniqueViolation as exc:
            raise ConflictError(
                f"Ya existe un lote registrado con el código '{codigo_lote}'.",
                error_code="LOTE_DUPLICADO",
            ) from exc
        except ForeignKeyViolation as exc:
            raise NotFoundError(
                f"La parcela {parcela_id} no existe en el catálogo maestro.",
                error_code="PARCELA_NO_ENCONTRADA",
            ) from exc

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
        try:
            with self.conn.transaction():
                with self.conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        "SELECT lote_id, estado FROM lotes WHERE codigo_lote = %s FOR UPDATE",
                        (codigo_lote,),
                    )
                    lote = cur.fetchone()
                    if lote is None:
                        raise NotFoundError(
                            f"El lote '{codigo_lote}' no existe.",
                            error_code="LOTE_NO_ENCONTRADO",
                        )
                    if lote["estado"] != "Cosechado":
                        raise ConflictError(
                            f"El lote '{codigo_lote}' está en estado '{lote['estado']}' y no puede recibirse nuevamente.",
                            error_code="LOTE_ESTADO_INVALIDO_RECEPCION",
                        )

                    cur.execute(
                        """
                        INSERT INTO recepciones_cedis (
                            folio_recepcion, lote_id, fecha_llegada, placas_vehiculo,
                            codigo_cuarto_frio, peso_recibido_kg, temperatura_llegada_c,
                            dictamen_recepcion
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING
                            recepcion_id, folio_recepcion, lote_id, fecha_llegada,
                            placas_vehiculo, codigo_cuarto_frio, peso_recibido_kg,
                            temperatura_llegada_c, dictamen_recepcion
                        """,
                        (
                            folio_recepcion,
                            lote["lote_id"],
                            fecha_llegada,
                            placas_vehiculo,
                            codigo_cuarto_frio,
                            peso_recibido_kg,
                            temperatura_llegada_c,
                            dictamen_recepcion,
                        ),
                    )
                    recepcion = cur.fetchone()

                    cur.execute(
                        """
                        UPDATE lotes
                        SET estado = %s, fecha_actualizacion = CURRENT_TIMESTAMP
                        WHERE lote_id = %s
                        """,
                        (nuevo_estado_lote, lote["lote_id"]),
                    )
            return _normalize_row(recepcion)  # type: ignore[return-value]
        except UniqueViolation as exc:
            raise ConflictError(
                f"El folio '{folio_recepcion}' o la recepción del lote '{codigo_lote}' ya existe.",
                error_code="RECEPCION_DUPLICADA",
            ) from exc

    def liberar_lote(
        self,
        *,
        codigo_lote: str,
        usuario_responsable: str,
        motivo: str,
        folio_evento: str,
    ) -> dict[str, Any]:
        with self.conn.transaction():
            with self.conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT lote_id, codigo_lote, estado, saldo_kg
                    FROM lotes
                    WHERE codigo_lote = %s
                    FOR UPDATE
                    """,
                    (codigo_lote,),
                )
                lote = cur.fetchone()
                if lote is None:
                    raise NotFoundError(
                        f"El lote '{codigo_lote}' no existe.",
                        error_code="LOTE_NO_ENCONTRADO",
                    )
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
                cur.execute(
                    """
                    UPDATE lotes
                    SET estado = 'Liberado', fecha_actualizacion = CURRENT_TIMESTAMP
                    WHERE lote_id = %s
                    RETURNING lote_id, codigo_lote, estado, saldo_kg, fecha_actualizacion
                    """,
                    (lote["lote_id"],),
                )
                updated = cur.fetchone()

                cur.execute(
                    """
                    INSERT INTO incidentes_bitacora (
                        folio_incidente, lote_id, usuario_responsable,
                        motivo, estado_previo, nuevo_estado
                    )
                    VALUES (%s, %s, %s, %s, %s, 'Liberado')
                    """,
                    (
                        folio_evento,
                        lote["lote_id"],
                        usuario_responsable,
                        motivo[:250],
                        estado_previo,
                    ),
                )
        result = _normalize_row(updated) or {}
        result["estado_previo"] = estado_previo
        result["folio_evento"] = folio_evento
        return result

    def create_envio_fraccionado(
        self,
        *,
        codigo_envio: str,
        tienda_id: int,
        placas_vehiculo: str,
        detalles: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Despacho ACID con SELECT ... FOR UPDATE validando RN-01 y RN-03."""
        if not detalles:
            raise ValidationDomainError("El envío debe incluir al menos un lote.")

        # Ordenar códigos para evitar deadlocks cuando concurren envíos con varios lotes
        ordered = sorted(detalles, key=lambda item: item["codigo_lote"])

        try:
            with self.conn.transaction():
                with self.conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        "SELECT tienda_id, codigo_sucursal, nombre_comercial, activo FROM tiendas WHERE tienda_id = %s",
                        (tienda_id,),
                    )
                    tienda = cur.fetchone()
                    if tienda is None:
                        raise NotFoundError(
                            f"La tienda {tienda_id} no existe.",
                            error_code="TIENDA_NO_ENCONTRADA",
                        )
                    if not tienda["activo"]:
                        raise ConflictError(
                            f"La tienda '{tienda['codigo_sucursal']}' está inactiva (RN-10).",
                            error_code="TIENDA_INACTIVA",
                        )

                    lotes_locked: list[tuple[dict[str, Any], float]] = []
                    total_kg = 0.0
                    for item in ordered:
                        codigo_lote = item["codigo_lote"]
                        cantidad_kg = float(item["cantidad_kg"])
                        cur.execute(
                            """
                            SELECT lote_id, codigo_lote, estado, saldo_kg
                            FROM lotes
                            WHERE codigo_lote = %s
                            FOR UPDATE
                            """,
                            (codigo_lote,),
                        )
                        lote = cur.fetchone()
                        if lote is None:
                            raise NotFoundError(
                                f"El lote '{codigo_lote}' no existe.",
                                error_code="LOTE_NO_ENCONTRADO",
                            )
                        if lote["estado"] != "Liberado":
                            raise ConflictError(
                                f"El lote {codigo_lote} se encuentra en estado '{lote['estado']}' y no puede despacharse (RN-01).",
                                error_code="LOTE_NO_DISPONIBLE_PARA_DESPACHO",
                                extra={"codigo_lote": codigo_lote},
                            )
                        saldo_actual = float(lote["saldo_kg"])
                        if cantidad_kg > saldo_actual:
                            raise ConflictError(
                                f"Saldo insuficiente en lote {codigo_lote}: disponible {saldo_actual:.2f} kg, solicitado {cantidad_kg:.2f} kg (RN-03).",
                                error_code="SALDO_INSUFICIENTE",
                                extra={"codigo_lote": codigo_lote},
                            )
                        lotes_locked.append((lote, cantidad_kg))
                        total_kg += cantidad_kg

                    cur.execute(
                        """
                        INSERT INTO envios (codigo_envio, tienda_id, placas_vehiculo, estado_envio)
                        VALUES (%s, %s, %s, 'Preparado')
                        RETURNING envio_id, codigo_envio, tienda_id, placas_vehiculo, fecha_despacho, estado_envio
                        """,
                        (codigo_envio, tienda_id, placas_vehiculo),
                    )
                    envio = cur.fetchone()

                    saldos_actualizados: list[dict[str, Any]] = []
                    for lote, cantidad_kg in lotes_locked:
                        cur.execute(
                            """
                            INSERT INTO envios_detalle (envio_id, lote_id, cantidad_kg)
                            VALUES (%s, %s, %s)
                            """,
                            (envio["envio_id"], lote["lote_id"], cantidad_kg),
                        )
                        cur.execute(
                            """
                            UPDATE lotes
                            SET saldo_kg = saldo_kg - %s, fecha_actualizacion = CURRENT_TIMESTAMP
                            WHERE lote_id = %s
                            RETURNING codigo_lote, saldo_kg
                            """,
                            (cantidad_kg, lote["lote_id"]),
                        )
                        upd = cur.fetchone()
                        saldos_actualizados.append(
                            {
                                "codigo_lote": upd["codigo_lote"],
                                "saldo_kg_restante": float(upd["saldo_kg"]),
                            }
                        )

            return {
                "envio": _normalize_row(envio),
                "tienda": _normalize_row(tienda),
                "total_kg": round(total_kg, 2),
                "saldos_actualizados": saldos_actualizados,
            }
        except UniqueViolation as exc:
            raise ConflictError(
                f"Ya existe un envío con código '{codigo_envio}' o lote duplicado en el detalle.",
                error_code="ENVIO_DUPLICADO",
            ) from exc

    def bloquear_lotes_recall(
        self,
        *,
        folio_incidente: str,
        codigo_lote_origen: str,
        codigos_lotes_hermanos: list[str],
        usuario_responsable: str,
        motivo: str,
    ) -> dict[str, Any]:
        """Bloquea atómicamente el lote origen y lotes hermanos y registra la bitácora QA."""
        all_codes = sorted({codigo_lote_origen, *codigos_lotes_hermanos})
        lotes_bloqueados: dict[str, dict[str, Any]] = {}

        with self.conn.transaction():
            with self.conn.cursor(row_factory=dict_row) as cur:
                for code in all_codes:
                    cur.execute(
                        """
                        SELECT lote_id, codigo_lote, estado, saldo_kg
                        FROM lotes
                        WHERE codigo_lote = %s
                        FOR UPDATE
                        """,
                        (code,),
                    )
                    lote = cur.fetchone()
                    if lote is None:
                        if code == codigo_lote_origen:
                            raise NotFoundError(
                                f"El lote origen '{codigo_lote_origen}' no existe.",
                                error_code="LOTE_NO_ENCONTRADO",
                            )
                        continue

                    estado_previo = lote["estado"]
                    cur.execute(
                        """
                        UPDATE lotes
                        SET estado = 'Bloqueado', fecha_actualizacion = CURRENT_TIMESTAMP
                        WHERE lote_id = %s
                        RETURNING lote_id, codigo_lote, estado, saldo_kg
                        """,
                        (lote["lote_id"],),
                    )
                    updated = _normalize_row(cur.fetchone()) or {}
                    updated["estado_previo"] = estado_previo
                    lotes_bloqueados[code] = updated

                lote_origen = lotes_bloqueados[codigo_lote_origen]
                cur.execute(
                    """
                    INSERT INTO incidentes_bitacora (
                        folio_incidente, lote_id, usuario_responsable,
                        motivo, estado_previo, nuevo_estado
                    )
                    VALUES (%s, %s, %s, %s, %s, 'Bloqueado')
                    RETURNING incidente_id, folio_incidente, fecha_evento
                    """,
                    (
                        folio_incidente,
                        lote_origen["lote_id"],
                        usuario_responsable,
                        motivo[:250],
                        lote_origen["estado_previo"],
                    ),
                )
                bitacora = _normalize_row(cur.fetchone())

        return {
            "bitacora": bitacora,
            "lote_origen": lotes_bloqueados[codigo_lote_origen],
            "lotes_bloqueados": lotes_bloqueados,
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
        with self.conn.transaction():
            with self.conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT lote_id, estado FROM lotes WHERE lote_id = %s FOR UPDATE",
                    (lote_id,),
                )
                lote = cur.fetchone()
                if lote is None:
                    raise NotFoundError("Lote asociado al incidente no encontrado.")
                estado_previo = lote["estado"]

                cur.execute(
                    """
                    UPDATE lotes
                    SET estado = %s, fecha_actualizacion = CURRENT_TIMESTAMP
                    WHERE lote_id = %s
                    """,
                    (nuevo_estado, lote_id),
                )
                cur.execute(
                    """
                    INSERT INTO incidentes_bitacora (
                        folio_incidente, lote_id, usuario_responsable,
                        motivo, estado_previo, nuevo_estado
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING incidente_id, folio_incidente, fecha_evento
                    """,
                    (
                        folio_cierre,
                        lote_id,
                        usuario_responsable,
                        motivo[:250],
                        estado_previo,
                        nuevo_estado,
                    ),
                )
                row = cur.fetchone()
        return _normalize_row(row)  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Outbox / Reconciliación (eventos_reconciliacion)
    # ------------------------------------------------------------------
    def insert_reconciliation_event(
        self,
        *,
        destino_motor: str,
        tipo_operacion: str,
        llave_entidad: str,
        payload: dict[str, Any],
        ultimo_error: str | None = None,
    ) -> int:
        sql = """
            INSERT INTO eventos_reconciliacion (
                destino_motor, tipo_operacion, llave_entidad,
                payload_json, estado, intentos, ultimo_error
            )
            VALUES (%s, %s, %s, %s::jsonb, 'PENDIENTE', 1, %s)
            RETURNING evento_id
        """
        with self.conn.transaction():
            with self.conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        destino_motor,
                        tipo_operacion,
                        llave_entidad,
                        json.dumps(payload, default=str),
                        ultimo_error[:1000] if ultimo_error else None,
                    ),
                )
                row = cur.fetchone()
        return int(row[0])  # type: ignore[index]

    def get_pending_reconciliation_events(self, limit: int = 50) -> list[dict[str, Any]]:
        sql = """
            SELECT
                evento_id,
                destino_motor,
                tipo_operacion,
                llave_entidad,
                payload_json,
                estado,
                intentos,
                ultimo_error,
                fecha_creacion
            FROM eventos_reconciliacion
            WHERE estado IN ('PENDIENTE', 'ERROR')
            ORDER BY fecha_creacion ASC
            LIMIT %s
        """
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (limit,))
            return [dict(r) for r in cur.fetchall()]

    def mark_reconciliation_event(
        self,
        *,
        evento_id: int,
        estado: str,
        ultimo_error: str | None = None,
    ) -> None:
        sql = """
            UPDATE eventos_reconciliacion
            SET
                estado = %s,
                intentos = intentos + 1,
                ultimo_error = %s,
                fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE evento_id = %s
        """
        with self.conn.transaction():
            with self.conn.cursor() as cur:
                cur.execute(
                    sql,
                    (estado, ultimo_error[:1000] if ultimo_error else None, evento_id),
                )
