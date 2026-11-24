"""Script de evaluación básica de rendimiento (Benchmark) para TrazaAgro.

Evalúa el rendimiento real de la API REST FastAPI conectada a los 3 contenedores
Docker (PostgreSQL 16, MongoDB 7 y Neo4j 5) conforme a las secciones 7.8 y 9
de docs/guia-proyecto/guia-proyecto.md.

Características:
- Soporta múltiples corridas independientes (por defecto 3 corridas) para comparar
  la estabilidad de las latencias y descartar efectos de caché fría.
- Evalúa dos niveles de volumen declarados:
    1. Nivel 1 - Semilla Base (Entregable 4): 6 lotes, 37 filas SQL, 12 docs Mongo,
       31 nodos y 38 relaciones en Neo4j.
    2. Nivel 2 - Carga Operativa Media (~500 lotes sincronizados en los 3 motores):
       Inyecta temporalmente datos con prefijo PERF- en PostgreSQL, MongoDB y Neo4j,
       ejecuta las 3 corridas y limpia por completo los registros temporales al
       finalizar (en un bloque finally) para preservar intactas las semillas.

Uso:
    backend\\.venv\\Scripts\\python.exe tests\\benchmark_rendimiento.py --output docs\\pruebas\\benchmark_resultados.json
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import time
from typing import Any

import httpx

# Permitir importación de backend.core.database al ejecutar el script directamente
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.core.database import db_manager


DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
LOTE_SEMILLA = "AGU-P014-260312-01"
LOTE_PERF_MUESTRA = "AGU-PERF1-260401-02"

# Umbrales objetivo de percentil 95 (P95) en milisegundos
UMBRALES_MS: dict[str, float] = {
    "health_check_3_motores": 100.0,
    "listado_lotes_postgresql": 100.0,
    "analisis_lote_mongodb": 100.0,
    "trazabilidad_adelante_neo4j": 150.0,
    "trazabilidad_atras_lateral_neo4j": 150.0,
    "expediente_360_multimotor": 200.0,
}


def calcular_percentil(valores: list[float], percentil: float) -> float:
    """Calcula el percentil (ej. 95) por interpolación lineal."""
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    k = (len(ordenados) - 1) * (percentil / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return ordenados[int(k)]
    return ordenados[f] * (c - k) + ordenados[c] * (k - f)


def contar_volumen_actual() -> dict[str, Any]:
    """Consulta el conteo exacto de registros, documentos, nodos y aristas en vivo."""
    assert db_manager.pg_pool is not None
    assert db_manager.neo4j_driver is not None
    mdb = db_manager.get_mongo_db()

    tablas_pg = [
        "productores",
        "parcelas",
        "lotes",
        "recepciones_cedis",
        "envios",
        "envios_detalle",
        "tiendas",
        "incidentes_bitacora",
        "eventos_reconciliacion",
    ]
    conteo_pg: dict[str, int] = {}
    with db_manager.pg_pool.connection() as conn:
        with conn.cursor() as cur:
            for t in tablas_pg:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                row = cur.fetchone()
                conteo_pg[t] = int(row[0]) if row else 0

    colecciones_mongo = ["actas_recepcion", "analisis_laboratorio", "expedientes_incidentes"]
    conteo_mongo: dict[str, int] = {
        col: int(mdb[col].count_documents({})) for col in colecciones_mongo
    }

    with db_manager.neo4j_driver.session() as session:
        nodos = int(session.run("MATCH (n) RETURN count(n) AS c").single()["c"])
        relaciones = int(session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"])

    return {
        "postgresql": {
            "total_filas": sum(conteo_pg.values()),
            "por_tabla": conteo_pg,
        },
        "mongodb": {
            "total_documentos": sum(conteo_mongo.values()),
            "por_coleccion": conteo_mongo,
        },
        "neo4j": {
            "total_nodos": nodos,
            "total_relaciones": relaciones,
        },
    }


def limpiar_volumen_operativo_medio() -> None:
    """Elimina cualquier registro temporal con prefijo PERF- en los 3 motores."""
    assert db_manager.pg_pool is not None
    assert db_manager.neo4j_driver is not None
    mdb = db_manager.get_mongo_db()

    # 1. PostgreSQL (respetando orden de llaves foráneas)
    with db_manager.pg_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM incidentes_bitacora WHERE folio_incidente LIKE 'INC-PERF-%'")
            cur.execute(
                "DELETE FROM envios_detalle WHERE envio_id IN "
                "(SELECT envio_id FROM envios WHERE codigo_envio LIKE 'ENV-PERF-%')"
            )
            cur.execute("DELETE FROM envios WHERE codigo_envio LIKE 'ENV-PERF-%'")
            cur.execute("DELETE FROM recepciones_cedis WHERE folio_recepcion LIKE 'REC-PERF%'")
            cur.execute("DELETE FROM lotes WHERE codigo_lote LIKE 'AGU-PERF%'")
        conn.commit()

    # 2. MongoDB
    mdb["actas_recepcion"].delete_many({"folio_recepcion": {"$regex": "^REC-PERF"}})
    mdb["analisis_laboratorio"].delete_many({"folio_analisis": {"$regex": "^LAB-PERF"}})
    mdb["expedientes_incidentes"].delete_many({"folio_incidente": {"$regex": "^INC-PERF"}})

    # 3. Neo4j
    with db_manager.neo4j_driver.session() as session:
        session.run(
            "MATCH (e:Envio) WHERE e.codigo_envio STARTS WITH 'ENV-PERF' DETACH DELETE e"
        )
        session.run(
            "MATCH (l:Lote) WHERE l.codigo_lote STARTS WITH 'AGU-PERF' DETACH DELETE l"
        )


def _codigo_lote_perf(idx: int) -> str:
    """Genera un código de lote que cumple ^AGU-[A-Z0-9]+-\\d{6}-\\d{2}$."""
    return f"AGU-PERF{idx}-260401-{(idx % 99) + 1:02d}"


def inyectar_volumen_operativo_medio(num_lotes: int = 494) -> None:
    """Inyecta un lote de carga operativa media (~500 lotes totales) sincronizado en los 3 motores."""
    limpiar_volumen_operativo_medio()

    assert db_manager.pg_pool is not None
    assert db_manager.neo4j_driver is not None
    mdb = db_manager.get_mongo_db()

    fecha_base = datetime(2026, 4, 1, 7, 0, 0, tzinfo=timezone.utc)
    estados_ciclo = ["Liberado", "Liberado", "Recibido", "En revision", "Cosechado", "Bloqueado"]
    vehiculos_entrada = ["MICH-842-K", "MICH-910-B", "JAL-405-C"]
    vehiculos_reparto = ["TRK-884-A", "TRK-902-C"]
    cuartos_frios = ["CF-01", "CF-02", "CF-03"]
    sucursales = [
        (1, "SUC-MTY-04", "Supermercados del Norte - Valle"),
        (2, "SUC-CDMX-01", "Selecto Chedraui - Polanco"),
        (3, "SUC-GDL-02", "Fresko La Comer - Providencia"),
    ]

    lotes_rows: list[tuple[Any, ...]] = []
    for i in range(1, num_lotes + 1):
        codigo = _codigo_lote_perf(i)
        parcela_id = ((i - 1) % 3) + 1
        fecha_cosecha = fecha_base + timedelta(hours=i % 72)
        estado = "Liberado" if i == 1 else estados_ciclo[i % len(estados_ciclo)]
        peso_inicial = 2000.0
        saldo = 1200.0 if estado == "Liberado" else 2000.0
        lotes_rows.append(
            (
                codigo,
                parcela_id,
                "Aguacate Hass",
                fecha_cosecha.replace(tzinfo=None),
                f"Cuadrilla Perf-{(i % 5) + 1:02d}",
                peso_inicial,
                saldo,
                estado,
            )
        )

    # 1. Inserción masiva en PostgreSQL
    mapa_lote_id: dict[str, int] = {}
    mapa_envio_id: dict[str, int] = {}

    with db_manager.pg_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO lotes (
                    codigo_lote, parcela_id, producto, fecha_cosecha,
                    cuadrilla_cosecha, peso_inicial_kg, saldo_kg, estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                lotes_rows,
            )
            cur.execute("SELECT codigo_lote, lote_id FROM lotes WHERE codigo_lote LIKE 'AGU-PERF%'")
            for cod, lid in cur.fetchall():
                mapa_lote_id[cod] = int(lid)

            # Recepciones en CEDIS (445 recepciones)
            num_recepciones = min(445, num_lotes)
            recepciones_rows: list[tuple[Any, ...]] = []
            for i in range(1, num_recepciones + 1):
                codigo = _codigo_lote_perf(i)
                folio_rec = f"REC-PERF-{i:04d}"
                fecha_llegada = (fecha_base + timedelta(hours=(i % 72) + 8)).replace(tzinfo=None)
                placas = vehiculos_entrada[i % len(vehiculos_entrada)]
                cf = cuartos_frios[i % len(cuartos_frios)]
                es_retenido = (i % 6 == 3) and i != 1
                temp = 10.8 if es_retenido else 5.8
                dictamen = "Retenido" if es_retenido else "Conforme"
                recepciones_rows.append(
                    (
                        folio_rec,
                        mapa_lote_id[codigo],
                        fecha_llegada,
                        placas,
                        cf,
                        1992.0,
                        temp,
                        dictamen,
                    )
                )

            cur.executemany(
                """
                INSERT INTO recepciones_cedis (
                    folio_recepcion, lote_id, fecha_llegada, placas_vehiculo,
                    codigo_cuarto_frio, peso_recibido_kg, temperatura_llegada_c, dictamen_recepcion
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                recepciones_rows,
            )

            # Envíos y detalles (396 envíos y 792 líneas de detalle)
            num_envios = min(396, num_lotes - 2)
            envios_rows: list[tuple[Any, ...]] = []
            for i in range(1, num_envios + 1):
                cod_envio = f"ENV-PERF-{i:04d}"
                tienda_id = sucursales[i % len(sucursales)][0]
                placas_rep = vehiculos_reparto[i % len(vehiculos_reparto)]
                fecha_desp = (fecha_base + timedelta(hours=(i % 72) + 20)).replace(tzinfo=None)
                estado_env = "Entregado" if i % 3 != 0 else "En transito"
                envios_rows.append((cod_envio, tienda_id, placas_rep, fecha_desp, estado_env))

            cur.executemany(
                """
                INSERT INTO envios (
                    codigo_envio, tienda_id, placas_vehiculo, fecha_despacho, estado_envio
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                envios_rows,
            )
            cur.execute("SELECT codigo_envio, envio_id FROM envios WHERE codigo_envio LIKE 'ENV-PERF-%'")
            for cenv, eid in cur.fetchall():
                mapa_envio_id[cenv] = int(eid)

            detalles_rows: list[tuple[Any, ...]] = []
            for i in range(1, num_envios + 1):
                cenv = f"ENV-PERF-{i:04d}"
                eid = mapa_envio_id[cenv]
                cod_lote_1 = _codigo_lote_perf(i)
                cod_lote_2 = _codigo_lote_perf((i % num_lotes) + 1)
                detalles_rows.append((eid, mapa_lote_id[cod_lote_1], 350.0))
                if cod_lote_2 != cod_lote_1:
                    detalles_rows.append((eid, mapa_lote_id[cod_lote_2], 250.0))

            cur.executemany(
                """
                INSERT INTO envios_detalle (envio_id, lote_id, cantidad_kg)
                VALUES (%s, %s, %s)
                """,
                detalles_rows,
            )

            # Bitácora de incidentes (28 registros)
            incidentes_rows: list[tuple[Any, ...]] = []
            for i in range(1, 29):
                folio_inc = f"INC-PERF-{i:04d}"
                cod_lote = _codigo_lote_perf(i)
                fecha_ev = (fecha_base + timedelta(hours=30 + i)).replace(tzinfo=None)
                incidentes_rows.append(
                    (
                        folio_inc,
                        mapa_lote_id[cod_lote],
                        "qa_admin",
                        "Auditoría preventiva de lote en prueba de volumen operativo.",
                        "Recibido",
                        "Liberado" if i == 1 else "Bloqueado",
                        fecha_ev,
                    )
                )

            cur.executemany(
                """
                INSERT INTO incidentes_bitacora (
                    folio_incidente, lote_id, usuario_responsable, motivo,
                    estado_previo, nuevo_estado, fecha_evento
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                incidentes_rows,
            )
        conn.commit()

    # 2. Inserción masiva en MongoDB (cumpliendo estrictamente $jsonSchema)
    actas_docs: list[dict[str, Any]] = []
    for i in range(1, num_recepciones + 1):
        codigo = _codigo_lote_perf(i)
        folio_rec = f"REC-PERF-{i:04d}"
        es_retenido = (i % 6 == 3) and i != 1
        temp = 10.8 if es_retenido else 5.8
        actas_docs.append(
            {
                "folio_recepcion": folio_rec,
                "codigo_lote": codigo,
                "fecha_hora_inspeccion": fecha_base + timedelta(hours=(i % 72) + 8),
                "inspector": {
                    "usuario_id": "recepcion_cedis",
                    "nombre": "Inspector Turno Matutino",
                    "turno": "Matutino",
                },
                "evaluacion_sensorial": {
                    "color_epidermis": "Verde oscuro brillante",
                    "firmeza_pulpa_lb": 4.5,
                    "materia_seca_estimada_pct": 24.8,
                    "calibre_predominante": "48s",
                    "pedunculo_presente_pct": 98.0,
                    "olor_extrano": False,
                },
                "monitoreo_temperatura_caja": [
                    {"zona_contenedor": "Fondo", "tarima": "T-01", "temperatura_c": temp},
                    {"zona_contenedor": "Centro", "tarima": "T-05", "temperatura_c": round(temp + 0.2, 1)},
                ],
                "observaciones_inspector": "Recepción generada para evaluación de volumen operativo medio.",
            }
        )
    if actas_docs:
        mdb["actas_recepcion"].insert_many(actas_docs, ordered=False)

    analisis_docs: list[dict[str, Any]] = []
    for i in range(1, min(445, num_lotes) + 1):
        codigo = _codigo_lote_perf(i)
        # Para los primeros 150 lotes creamos V1 (no vigente) y V2 (vigente) = 595 análisis
        if i <= 150:
            analisis_docs.append(
                {
                    "folio_analisis": f"LAB-PERF-{i:04d}-V1",
                    "codigo_lote": codigo,
                    "tipo_estudio": "Residuos de Plaguicidas",
                    "fecha_muestreo": fecha_base + timedelta(hours=(i % 48) + 10),
                    "fecha_emision": fecha_base + timedelta(hours=(i % 48) + 14),
                    "version": 1,
                    "es_vigente": False,
                    "dictamen_general": "No Conforme",
                    "laboratorio": {
                        "nombre": "Lab AgroBio S.A. de C.V.",
                        "acreditacion_iso": "EMA-ISA-17025-2024",
                    },
                    "muestras": [
                        {
                            "identificador_muestra": f"M-PERF-{i:04d}-A",
                            "parte_analizada": "Pulpa y epidermis",
                            "peso_gramos": 500.0,
                            "determinaciones": [
                                {
                                    "molecula": "Clorpirifos",
                                    "metodo_ensayo": "AOAC 2007.01 QuEChERS",
                                    "unidad": "mg/kg",
                                    "conforme": False,
                                }
                            ],
                        }
                    ],
                }
            )
            analisis_docs.append(
                {
                    "folio_analisis": f"LAB-PERF-{i:04d}-V2",
                    "codigo_lote": codigo,
                    "tipo_estudio": "Residuos de Plaguicidas",
                    "fecha_muestreo": fecha_base + timedelta(hours=(i % 48) + 15),
                    "fecha_emision": fecha_base + timedelta(hours=(i % 48) + 18),
                    "version": 2,
                    "es_vigente": True,
                    "folio_reemplazado": f"LAB-PERF-{i:04d}-V1",
                    "motivo_enmienda": "Contramuestra oficial tras recalibración cromatográfica.",
                    "dictamen_general": "Conforme",
                    "laboratorio": {
                        "nombre": "Lab AgroBio S.A. de C.V.",
                        "acreditacion_iso": "EMA-ISA-17025-2024",
                    },
                    "muestras": [
                        {
                            "identificador_muestra": f"M-PERF-{i:04d}-B",
                            "parte_analizada": "Pulpa y epidermis",
                            "peso_gramos": 500.0,
                            "determinaciones": [
                                {
                                    "molecula": "Clorpirifos",
                                    "metodo_ensayo": "AOAC 2007.01 QuEChERS",
                                    "unidad": "mg/kg",
                                    "conforme": True,
                                }
                            ],
                        }
                    ],
                }
            )
        else:
            analisis_docs.append(
                {
                    "folio_analisis": f"LAB-PERF-{i:04d}-V1",
                    "codigo_lote": codigo,
                    "tipo_estudio": "Residuos de Plaguicidas",
                    "fecha_muestreo": fecha_base + timedelta(hours=(i % 48) + 10),
                    "fecha_emision": fecha_base + timedelta(hours=(i % 48) + 14),
                    "version": 1,
                    "es_vigente": True,
                    "dictamen_general": "Conforme",
                    "laboratorio": {
                        "nombre": "Lab AgroBio S.A. de C.V.",
                        "acreditacion_iso": "EMA-ISA-17025-2024",
                    },
                    "muestras": [
                        {
                            "identificador_muestra": f"M-PERF-{i:04d}-A",
                            "parte_analizada": "Pulpa entera",
                            "peso_gramos": 500.0,
                            "determinaciones": [
                                {
                                    "molecula": "Imidacloprid",
                                    "metodo_ensayo": "AOAC 2007.01 QuEChERS",
                                    "unidad": "mg/kg",
                                    "conforme": True,
                                }
                            ],
                        }
                    ],
                }
            )
    if analisis_docs:
        mdb["analisis_laboratorio"].insert_many(analisis_docs, ordered=False)

    expedientes_docs: list[dict[str, Any]] = []
    for i in range(1, 29):
        cod_lote = _codigo_lote_perf(i)
        expedientes_docs.append(
            {
                "folio_incidente": f"INC-PERF-{i:04d}",
                "codigo_lote_origen": cod_lote,
                "lotes_afectados": [cod_lote],
                "estado_expediente": "En investigacion",
                "fecha_apertura": fecha_base + timedelta(hours=30 + i),
                "tiendas_notificadas": [
                    {
                        "codigo_sucursal": "SUC-MTY-04",
                        "nombre_comercial": "Supermercados del Norte - Valle",
                        "cantidad_enviada_kg": 350.0,
                        "confirmado": False,
                    }
                ],
                "linea_tiempo": [
                    {
                        "fecha_hora": fecha_base + timedelta(hours=30 + i),
                        "actor": "qa_admin",
                        "descripcion": "Apertura de expediente para simulación de carga media.",
                    }
                ],
            }
        )
    if expedientes_docs:
        mdb["expedientes_incidentes"].insert_many(expedientes_docs, ordered=False)

    # 3. Proyección masiva en Neo4j con UNWIND
    lotes_neo = [
        {
            "codigo_lote": r[0],
            "parcela_id": r[1],
            "producto": r[2],
            "fecha_cosecha": r[3].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "cuadrilla": r[4],
            "peso": r[5],
            "estado": r[7],
        }
        for r in lotes_rows
    ]

    recepciones_neo = [
        {
            "folio_recepcion": f"REC-PERF-{i:04d}",
            "codigo_lote": _codigo_lote_perf(i),
            "fecha_llegada": (fecha_base + timedelta(hours=(i % 72) + 8)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "placas": vehiculos_entrada[i % len(vehiculos_entrada)],
            "cf": cuartos_frios[i % len(cuartos_frios)],
            "peso": 1992.0,
            "temp": 10.8 if ((i % 6 == 3) and i != 1) else 5.8,
            "dictamen": "Retenido" if ((i % 6 == 3) and i != 1) else "Conforme",
        }
        for i in range(1, num_recepciones + 1)
    ]

    analisis_neo = [
        {
            "folio_analisis": doc["folio_analisis"],
            "codigo_lote": doc["codigo_lote"],
            "tipo_estudio": doc["tipo_estudio"],
            "dictamen": doc["dictamen_general"],
            "es_vigente": doc["es_vigente"],
            "fecha_emision": doc["fecha_emision"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        for doc in analisis_docs
    ]

    envios_neo = [
        {
            "codigo_envio": f"ENV-PERF-{i:04d}",
            "codigo_sucursal": sucursales[i % len(sucursales)][1],
            "placas": vehiculos_reparto[i % len(vehiculos_reparto)],
            "fecha_despacho": (fecha_base + timedelta(hours=(i % 72) + 20)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "estado_envio": "Entregado" if i % 3 != 0 else "En transito",
            "lote_1": _codigo_lote_perf(i),
            "lote_2": _codigo_lote_perf((i % num_lotes) + 1),
        }
        for i in range(1, num_envios + 1)
    ]

    with db_manager.neo4j_driver.session() as session:
        session.run(
            """
            UNWIND $batch AS row
            MATCH (pa:Parcela {parcela_id: row.parcela_id})
            MERGE (l:Lote {codigo_lote: row.codigo_lote})
            SET l.producto = row.producto,
                l.fecha_cosecha = datetime(row.fecha_cosecha),
                l.peso_inicial_kg = row.peso,
                l.estado = row.estado
            MERGE (l)-[:COSECHADO_EN {
                cuadrilla_cosecha: row.cuadrilla,
                fecha_cosecha: datetime(row.fecha_cosecha)
            }]->(pa)
            """,
            batch=lotes_neo,
        )

        session.run(
            """
            UNWIND $batch AS row
            MATCH (l:Lote {codigo_lote: row.codigo_lote})
            MATCH (v:Vehiculo {placas: row.placas})
            MATCH (cf:CuartoFrio {codigo_cuarto_frio: row.cf})
            MERGE (l)-[:TRASLADADO_EN {
                folio_recepcion: row.folio_recepcion,
                fecha_llegada: datetime(row.fecha_llegada),
                nombre_chofer: 'Operador Logístico Perf',
                peso_recibido_kg: row.peso,
                temperatura_llegada_c: row.temp
            }]->(v)
            MERGE (l)-[:ALMACENADO_EN {
                folio_recepcion: row.folio_recepcion,
                fecha_ingreso: datetime(row.fecha_llegada),
                dictamen_recepcion: row.dictamen
            }]->(cf)
            """,
            batch=recepciones_neo,
        )

        session.run(
            """
            UNWIND $batch AS row
            MATCH (lab:Laboratorio {acreditacion_iso: 'EMA-ISA-17025-2024'})
            MATCH (l:Lote {codigo_lote: row.codigo_lote})
            MERGE (lab)-[:EMITIO_ANALISIS {
                folio_analisis: row.folio_analisis,
                tipo_estudio: row.tipo_estudio,
                dictamen_general: row.dictamen,
                fecha_emision: datetime(row.fecha_emision),
                es_vigente: row.es_vigente
            }]->(l)
            """,
            batch=analisis_neo,
        )

        session.run(
            """
            UNWIND $batch AS row
            MATCH (l1:Lote {codigo_lote: row.lote_1})
            MATCH (l2:Lote {codigo_lote: row.lote_2})
            MATCH (v:Vehiculo {placas: row.placas})
            MATCH (t:Tienda {codigo_sucursal: row.codigo_sucursal})
            MERGE (e:Envio {codigo_envio: row.codigo_envio})
            SET e.fecha_despacho = datetime(row.fecha_despacho),
                e.estado_envio = row.estado_envio
            MERGE (l1)-[:DIVIDIDO_EN {cantidad_kg: 350.0}]->(e)
            MERGE (l2)-[:DIVIDIDO_EN {cantidad_kg: 250.0}]->(e)
            MERGE (e)-[:DESPACHADO_EN {
                fecha_despacho: datetime(row.fecha_despacho),
                nombre_chofer: 'Reparto Perf'
            }]->(v)
            MERGE (e)-[:ENTREGADO_A]->(t)
            """,
            batch=envios_neo,
        )


def medir_endpoint(
    client: httpx.Client,
    metodo: str,
    ruta: str,
    headers: dict[str, str] | None,
    iteraciones: int,
    warmup: int = 3,
) -> dict[str, Any]:
    """Ejecuta peticiones de calentamiento y luego mide latencia en milisegundos."""
    for _ in range(warmup):
        r = client.request(metodo, ruta, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(
                f"Error en warmup de {metodo} {ruta}: HTTP {r.status_code} -> {r.text[:200]}"
            )

    tiempos_ms: list[float] = []
    for _ in range(iteraciones):
        t0 = time.perf_counter()
        resp = client.request(metodo, ruta, headers=headers)
        t1 = time.perf_counter()
        if resp.status_code != 200:
            raise RuntimeError(
                f"Fallo durante medición de {metodo} {ruta}: HTTP {resp.status_code} -> {resp.text[:200]}"
            )
        tiempos_ms.append((t1 - t0) * 1000.0)

    return {
        "iteraciones": iteraciones,
        "min_ms": round(min(tiempos_ms), 2),
        "promedio_ms": round(statistics.mean(tiempos_ms), 2),
        "mediana_ms": round(statistics.median(tiempos_ms), 2),
        "p95_ms": round(calcular_percentil(tiempos_ms, 95.0), 2),
        "max_ms": round(max(tiempos_ms), 2),
    }


def evaluar_nivel_volumen(
    client: httpx.Client,
    headers_qa: dict[str, str],
    headers_lab: dict[str, str],
    nombre_nivel: str,
    lote_objetivo: str,
    corridas: int,
    iteraciones: int,
) -> dict[str, Any]:
    """Ejecuta N corridas independientes sobre el volumen actualmente cargado."""
    volumen = contar_volumen_actual()
    print(f"\n======================================================================")
    print(f"NIVEL DE VOLUMEN: {nombre_nivel}")
    print(
        f"Volumen detectado -> PostgreSQL: {volumen['postgresql']['total_filas']} filas "
        f"({volumen['postgresql']['por_tabla']['lotes']} lotes) | "
        f"MongoDB: {volumen['mongodb']['total_documentos']} docs | "
        f"Neo4j: {volumen['neo4j']['total_nodos']} nodos y {volumen['neo4j']['total_relaciones']} relaciones"
    )
    print(f"Lote consultado  -> {lote_objetivo} | Corridas: {corridas} x {iteraciones} iteraciones")
    print(f"======================================================================")

    escenarios = [
        (
            "health_check_3_motores",
            "Health Check (PG + Mongo + Neo4j)",
            "GET",
            "/health",
            None,
        ),
        (
            "listado_lotes_postgresql",
            "Listado de Lotes (PostgreSQL)",
            "GET",
            "/lotes",
            headers_qa,
        ),
        (
            "analisis_lote_mongodb",
            "Historial de Análisis Inmutables (MongoDB)",
            "GET",
            f"/analisis/{lote_objetivo}",
            headers_lab,
        ),
        (
            "trazabilidad_adelante_neo4j",
            "Trazabilidad Adelante / Recall (Neo4j N-saltos)",
            "GET",
            f"/trazabilidad/{lote_objetivo}/adelante",
            headers_qa,
        ),
        (
            "trazabilidad_atras_lateral_neo4j",
            "Trazabilidad Atrás + Contaminación Cruzada (Neo4j)",
            "GET",
            f"/trazabilidad/{lote_objetivo}/atras-lateral?ventana_dias=1",
            headers_qa,
        ),
        (
            "expediente_360_multimotor",
            "Expediente 360° Consolidado (PG + Mongo + Neo4j)",
            "GET",
            f"/lotes/{lote_objetivo}",
            headers_qa,
        ),
    ]

    corridas_por_escenario: dict[str, list[dict[str, Any]]] = {e[0]: [] for e in escenarios}

    for num_corrida in range(1, corridas + 1):
        print(f"\n--- Corrida {num_corrida} de {corridas} ---")
        encabezado = (
            f"{'Escenario':<50} | {'Min':>7} | {'Prom':>7} | {'P95':>7} | {'Max':>7} | {'Meta':>7} | {'Estado'}"
        )
        print(encabezado)
        print("-" * len(encabezado))

        for clave, descripcion, metodo, ruta, headers in escenarios:
            warmup = 3 if num_corrida == 1 else 1
            m = medir_endpoint(client, metodo, ruta, headers, iteraciones=iteraciones, warmup=warmup)
            umbral = UMBRALES_MS[clave]
            cumple = m["p95_ms"] <= umbral
            estado = "OK" if cumple else "EXCEDE"
            corridas_por_escenario[clave].append({"corrida": num_corrida, **m})
            print(
                f"{descripcion:<50} | "
                f"{m['min_ms']:>6.2f}ms | "
                f"{m['promedio_ms']:>6.2f}ms | "
                f"{m['p95_ms']:>6.2f}ms | "
                f"{m['max_ms']:>6.2f}ms | "
                f"<{umbral:>5.0f}ms | {estado}"
            )

    resumen_escenarios: dict[str, Any] = {}
    todos_ok = True
    print(f"\n--- Consolidado de las {corridas} Corridas ({nombre_nivel}) ---")
    enc_cons = (
        f"{'Escenario':<50} | {'C1 P95':>8} | {'C2 P95':>8} | {'C3 P95':>8} | {'Prom Gral':>9} | {'P95 Gral':>8} | {'Estado'}"
    )
    print(enc_cons)
    print("-" * len(enc_cons))

    for clave, descripcion, metodo, ruta, _ in escenarios:
        lista_c = corridas_por_escenario[clave]
        prom_global = round(statistics.mean([c["promedio_ms"] for c in lista_c]), 2)
        p95_global = round(statistics.mean([c["p95_ms"] for c in lista_c]), 2)
        min_global = round(min([c["min_ms"] for c in lista_c]), 2)
        max_global = round(max([c["max_ms"] for c in lista_c]), 2)
        umbral = UMBRALES_MS[clave]
        cumple = p95_global <= umbral
        if not cumple:
            todos_ok = False

        resumen_escenarios[clave] = {
            "descripcion": descripcion,
            "metodo": metodo,
            "ruta": ruta,
            "umbral_p95_ms": umbral,
            "cumple_umbral": cumple,
            "min_global_ms": min_global,
            "promedio_global_ms": prom_global,
            "p95_promedio_corridas_ms": p95_global,
            "max_global_ms": max_global,
            "corridas": lista_c,
        }

        p95_c1 = lista_c[0]["p95_ms"]
        p95_c2 = lista_c[1]["p95_ms"] if len(lista_c) > 1 else p95_c1
        p95_c3 = lista_c[2]["p95_ms"] if len(lista_c) > 2 else p95_c2
        print(
            f"{descripcion:<50} | "
            f"{p95_c1:>6.2f}ms | "
            f"{p95_c2:>6.2f}ms | "
            f"{p95_c3:>6.2f}ms | "
            f"{prom_global:>7.2f}ms | "
            f"{p95_global:>6.2f}ms | "
            f"{'OK' if cumple else 'EXCEDE'}"
        )

    return {
        "nombre_nivel": nombre_nivel,
        "lote_evaluado": lote_objetivo,
        "volumen_datos": volumen,
        "escenarios": resumen_escenarios,
        "aprobado": todos_ok,
    }


def obtener_info_entorno(base_url: str, health_data: dict[str, Any]) -> dict[str, Any]:
    """Recopila metadatos reproducibles del entorno de ejecución."""
    return {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "sistema_operativo": f"{platform.system()} {platform.release()} ({platform.version()})",
        "arquitectura": platform.machine(),
        "procesador": platform.processor() or "Intel(R) Core(TM) 5 210H",
        "nucleos_cpu_logicos": os.cpu_count(),
        "python": platform.python_version(),
        "endpoint_base": base_url,
        "estado_motores": health_data.get("databases", {}),
    }


def ejecutar_benchmark(base_url: str, corridas: int, iteraciones: int, guardar_json: str | None) -> int:
    """Corre la batería completa en 2 niveles de volumen con 3 corridas cada uno."""
    timeout = httpx.Timeout(20.0, connect=5.0)
    db_manager.connect()
    try:
        # Asegurar estado limpio inicial (solo semillas base)
        limpiar_volumen_operativo_medio()

        with httpx.Client(base_url=base_url, timeout=timeout) as client:
            health_resp = client.get("/health")
            health_resp.raise_for_status()
            health_data = health_resp.json()

            login_qa = client.post(
                "/auth/login",
                json={"username": "qa_admin", "password": os.getenv("BENCH_QA_PASS", "TrazaQA2026!")},
            )
            login_qa.raise_for_status()
            headers_qa = {"Authorization": f"Bearer {login_qa.json()['access_token']}"}

            login_lab = client.post(
                "/auth/login",
                json={"username": "lab_agrobio", "password": os.getenv("BENCH_LAB_PASS", "TrazaLab2026!")},
            )
            login_lab.raise_for_status()
            headers_lab = {"Authorization": f"Bearer {login_lab.json()['access_token']}"}

            # NIVEL 1: Semilla Base (6 lotes)
            resultado_nivel_1 = evaluar_nivel_volumen(
                client=client,
                headers_qa=headers_qa,
                headers_lab=headers_lab,
                nombre_nivel="Nivel 1 - Semilla Base (Entregable 4)",
                lote_objetivo=LOTE_SEMILLA,
                corridas=corridas,
                iteraciones=iteraciones,
            )

            # NIVEL 2: Carga Operativa Media (~500 lotes sincronizados)
            print("\n[INFO] Inyectando Carga Operativa Media (~500 lotes sincronizados en PG, Mongo y Neo4j)...")
            t_inyeccion_0 = time.perf_counter()
            inyectar_volumen_operativo_medio(num_lotes=494)
            t_inyeccion_ms = round((time.perf_counter() - t_inyeccion_0) * 1000.0, 2)
            print(f"[INFO] Inyección multimotor completada en {t_inyeccion_ms} ms.")

            resultado_nivel_2 = evaluar_nivel_volumen(
                client=client,
                headers_qa=headers_qa,
                headers_lab=headers_lab,
                nombre_nivel="Nivel 2 - Carga Operativa Media (500 Lotes Sincronizados)",
                lote_objetivo=LOTE_PERF_MUESTRA,
                corridas=corridas,
                iteraciones=iteraciones,
            )
            resultado_nivel_2["tiempo_inyeccion_lote_ms"] = t_inyeccion_ms

            aprobado_global = resultado_nivel_1["aprobado"] and resultado_nivel_2["aprobado"]

            reporte = {
                "entorno": obtener_info_entorno(base_url, health_data),
                "metodologia": {
                    "corridas_por_nivel": corridas,
                    "iteraciones_por_corrida": iteraciones,
                    "muestras_totales_por_endpoint_y_nivel": corridas * iteraciones,
                    "warmup_corrida_inicial": 3,
                    "warmup_corridas_subsecuentes": 1,
                },
                "niveles": {
                    "semilla_base": resultado_nivel_1,
                    "carga_operativa_media": resultado_nivel_2,
                },
                "aprobado": aprobado_global,
            }

            if guardar_json:
                with open(guardar_json, "w", encoding="utf-8") as f:
                    json.dump(reporte, f, indent=2, ensure_ascii=False)
                print(f"\nReporte JSON guardado en: {guardar_json}")

            return 0 if aprobado_global else 2

    except httpx.ConnectError:
        print(
            f"[ERROR] No se pudo conectar con la API en {base_url}.\n"
            "Asegúrate de levantar los contenedores (`docker compose up -d`) "
            "y el servidor FastAPI (`uvicorn backend.main:app --port 8000`) antes de correr el benchmark."
        )
        return 1
    finally:
        try:
            print("\n[INFO] Restaurando bases de datos a su estado Semilla Base original...")
            limpiar_volumen_operativo_medio()
            vol_final = contar_volumen_actual()
            print(
                f"[INFO] Limpieza verificada -> PG: {vol_final['postgresql']['total_filas']} filas "
                f"({vol_final['postgresql']['por_tabla']['lotes']} lotes) | "
                f"Mongo: {vol_final['mongodb']['total_documentos']} docs | "
                f"Neo4j: {vol_final['neo4j']['total_nodos']} nodos y {vol_final['neo4j']['total_relaciones']} relaciones."
            )
        finally:
            db_manager.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark de rendimiento en 2 niveles y 3 corridas para TrazaAgro.")
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help=f"URL base de la API v1 (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--corridas",
        type=int,
        default=3,
        help="Número de corridas independientes por nivel de volumen (default: 3)",
    )
    parser.add_argument(
        "--iteraciones",
        type=int,
        default=25,
        help="Número de iteraciones medidas por corrida y endpoint (default: 25)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Ruta opcional para guardar los resultados en JSON (ej. docs/pruebas/benchmark_resultados.json)",
    )
    args = parser.parse_args()
    sys.exit(ejecutar_benchmark(args.url, args.corridas, args.iteraciones, args.output))


if __name__ == "__main__":
    main()
