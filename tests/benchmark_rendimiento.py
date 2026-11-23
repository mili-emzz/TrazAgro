"""Script de evaluación básica de rendimiento (Benchmark) para TrazaAgro.

Mide tiempos de respuesta reales (min, promedio, mediana, p95 y max en ms)
contra la API REST FastAPI conectada a los 3 contenedores Docker reales
(PostgreSQL 16, MongoDB 7 y Neo4j 5), conforme a la sección 7.8 y 9 de
docs/guia-proyecto/guia-proyecto.md.

Uso:
    python tests/benchmark_rendimiento.py
    python tests/benchmark_rendimiento.py --iteraciones 30 --url http://127.0.0.1:8000/api/v1
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
import platform
import statistics
import sys
import time
from typing import Any

import httpx


DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
LOTE_SEMILLA = "AGU-P014-260312-01"

# Umbrales objetivo definidos en .agents/skills/pruebas-integracion/SKILL.md
UMBRALES_MS: dict[str, float] = {
    "health_check_3_motores": 100.0,
    "listado_lotes_postgresql": 100.0,
    "analisis_lote_mongodb": 100.0,
    "trazabilidad_adelante_neo4j": 150.0,
    "trazabilidad_atras_lateral_neo4j": 150.0,
    "expediente_360_multimotor": 200.0,
}


def calcular_percentil(valores: list[float], percentil: float) -> float:
    """Calcula el percentil (ej. 95) por interpolación lineal simple."""
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    k = (len(ordenados) - 1) * (percentil / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return ordenados[int(k)]
    return ordenados[f] * (c - k) + ordenados[c] * (k - f)


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


def obtener_info_entorno(base_url: str, health_data: dict[str, Any]) -> dict[str, Any]:
    """Recopila metadatos reproducibles del entorno de ejecución."""
    return {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "sistema_operativo": f"{platform.system()} {platform.release()} ({platform.version()})",
        "arquitectura": platform.machine(),
        "procesador": platform.processor() or "No reportado",
        "nucleos_cpu_logicos": os.cpu_count(),
        "python": platform.python_version(),
        "endpoint_base": base_url,
        "estado_motores": health_data.get("databases", {}),
    }


def ejecutar_benchmark(base_url: str, iteraciones: int, guardar_json: str | None) -> int:
    """Corre la batería completa de mediciones contra la API en vivo."""
    timeout = httpx.Timeout(15.0, connect=5.0)
    try:
        with httpx.Client(base_url=base_url, timeout=timeout) as client:
            # 1. Verificar conectividad contra los 3 motores
            health_resp = client.get("/health")
            health_resp.raise_for_status()
            health_data = health_resp.json()

            if health_data.get("status") not in ("ok", "operativo"):
                print(
                    f"[ADVERTENCIA] /health reportó estado '{health_data.get('status')}': "
                    f"{health_data.get('databases')}"
                )

            # 2. Autenticación como QA (permisos de lectura global y trazabilidad) y Laboratorio
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

            # 3. Escenarios de prueba (individuales por motor + integrados multimotor)
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
                    f"/analisis/{LOTE_SEMILLA}",
                    headers_lab,
                ),
                (
                    "trazabilidad_adelante_neo4j",
                    "Trazabilidad Adelante / Recall (Neo4j N-saltos)",
                    "GET",
                    f"/trazabilidad/{LOTE_SEMILLA}/adelante",
                    headers_qa,
                ),
                (
                    "trazabilidad_atras_lateral_neo4j",
                    "Trazabilidad Atrás + Contaminación Cruzada (Neo4j)",
                    "GET",
                    f"/trazabilidad/{LOTE_SEMILLA}/atras-lateral?ventana_dias=1",
                    headers_qa,
                ),
                (
                    "expediente_360_multimotor",
                    "Expediente 360° Consolidado (PG + Mongo + Neo4j)",
                    "GET",
                    f"/lotes/{LOTE_SEMILLA}",
                    headers_qa,
                ),
            ]

            resultados: dict[str, Any] = {}
            print("\n=== EVALUACION DE RENDIMIENTO: TRAZAAGRO ===")
            print(f"Base URL     : {base_url}")
            print(f"Iteraciones  : {iteraciones} (+ 3 warmup por endpoint)")
            print(f"Lote semilla : {LOTE_SEMILLA}\n")

            encabezado = (
                f"{'Escenario':<50} | {'Min':>7} | {'Prom':>7} | {'P95':>7} | {'Max':>7} | {'Meta':>7} | {'Estado'}"
            )
            print(encabezado)
            print("-" * len(encabezado))

            todos_ok = True
            for clave, descripcion, metodo, ruta, headers in escenarios:
                metricas = medir_endpoint(client, metodo, ruta, headers, iteraciones=iteraciones)
                umbral = UMBRALES_MS[clave]
                cumple = metricas["p95_ms"] <= umbral
                if not cumple:
                    todos_ok = False
                estado = "OK" if cumple else "EXCEDE"

                resultados[clave] = {
                    "descripcion": descripcion,
                    "metodo": metodo,
                    "ruta": ruta,
                    "umbral_p95_ms": umbral,
                    "cumple_umbral": cumple,
                    **metricas,
                }
                print(
                    f"{descripcion:<50} | "
                    f"{metricas['min_ms']:>6.2f}ms | "
                    f"{metricas['promedio_ms']:>6.2f}ms | "
                    f"{metricas['p95_ms']:>6.2f}ms | "
                    f"{metricas['max_ms']:>6.2f}ms | "
                    f"<{umbral:>5.0f}ms | {estado}"
                )

            reporte = {
                "entorno": obtener_info_entorno(base_url, health_data),
                "parametros": {
                    "iteraciones_por_endpoint": iteraciones,
                    "warmup_por_endpoint": 3,
                    "lote_semilla": LOTE_SEMILLA,
                },
                "resultados": resultados,
                "aprobado": todos_ok,
            }

            if guardar_json:
                with open(guardar_json, "w", encoding="utf-8") as f:
                    json.dump(reporte, f, indent=2, ensure_ascii=False)
                print(f"\nReporte JSON guardado en: {guardar_json}")

            print("\nResumen final:", "APROBADO (todos los P95 bajo meta)" if todos_ok else "CON OBSERVACIONES")
            return 0 if todos_ok else 2

    except httpx.ConnectError:
        print(
            f"[ERROR] No se pudo conectar con la API en {base_url}.\n"
            "Asegúrate de levantar los contenedores (`docker compose up -d`) "
            "y el servidor FastAPI (`uvicorn backend.main:app --port 8000`) antes de correr el benchmark."
        )
        return 1
    except Exception as exc:
        print(f"[ERROR] Fallo inesperado durante el benchmark: {exc}")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark de rendimiento para la API de TrazaAgro.")
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help=f"URL base de la API v1 (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--iteraciones",
        type=int,
        default=25,
        help="Número de iteraciones medidas por endpoint (default: 25)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Ruta opcional para guardar los resultados en JSON (ej. docs/pruebas/benchmark_resultados.json)",
    )
    args = parser.parse_args()
    sys.exit(ejecutar_benchmark(args.url, args.iteraciones, args.output))


if __name__ == "__main__":
    main()
