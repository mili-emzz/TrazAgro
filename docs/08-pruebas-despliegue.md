# Entregable 8: Pruebas, Documentación y Despliegue (TrazaAgro)

Este documento concentra la estrategia integral de validación, la evidencia de las pruebas obligatorias de integración, la evaluación de rendimiento en dos niveles de volumen con tres corridas independientes y el manual paso a paso de despliegue y ejecución de **TrazaAgro**, cumpliendo con las secciones 7.8, 9 y 11 de la guía oficial del proyecto (`docs/Guia_Proyecto_Final_Bases_Datos.pdf`).

## 1. Arquitectura de Validación y Cobertura de los 7 Ejes Obligatorios

Para demostrar que PostgreSQL 16, MongoDB 7 y Neo4j 5 operan como una sola solución coordinada por el backend en FastAPI y consumida por la aplicación de escritorio/web en React + TypeScript + Electron, la validación se estructuró en siete ejes complementarios:

```mermaid
flowchart TD
    subgraph SUITE["Suite Integral de Validación (Entregable 8)"]
        U["1. Unitarias y Componentes\ntests/unit/ (15 tests)"]
        I["2. Integridad por Motor\ndatabase/*/03_queries_and_tests + pytest"]
        C["3. Conectividad y PoLP\nGET /api/v1/health + trazaagro_app"]
        M["4. Integración Multimotor E2E\ntests/e2e/test_flujo_completo_mvp.py"]
        R["5. Consistencia y Outbox\ntests/integration/test_integrity_and_outbox.py"]
        N["6. Errores Negativos y Seguridad\ntests/integration/test_security_attacks.py"]
        P["7. Rendimiento (2 Niveles x 3 Corridas)\ntests/benchmark_rendimiento.py"]
    end

    subgraph STACK["Sistema TrazaAgro en Vivo"]
        UI["Frontend React 18 + Electron"]
        API["Backend FastAPI (14 Endpoints REST v1)"]
        PG[("PostgreSQL 16\nVerdad Transaccional ACID")]
        MG[("MongoDB 7\nExpedientes e Inmutabilidad")]
        N4J[("Neo4j 5\nGrafo Logístico y Recall")]
    end

    SUITE --> API
    UI --> API
    API --> PG
    API --> MG
    API --> N4J
```

### Matriz de Cumplimiento de Pruebas Obligatorias (Sección 9 de la Guía Oficial)

| Tipo de Prueba | Qué se Verifica en TrazaAgro | Archivo / Script de Evidencia | Resultado |
| :--- | :--- | :--- | :---: |
| **Conectividad** | El backend se conecta a PostgreSQL, MongoDB y Neo4j con configuración por variables de entorno, usuario de menor privilegio (`trazaagro_app`) y enmascaramiento de secretos en `/api/v1/health`. | `tests/smoke_frontend_api.py` y `tests/integration/test_routes_and_rbac.py` | **Aprobado (200 OK)** |
| **Unitarias y Componentes** | Esquemas Pydantic v2 (`extra="forbid"`, regex de códigos y folios, rangos térmicos y de peso), hashing `bcrypt`, firma y expiración JWT `HS256` (>= 256 bits), sanitización anti-XSS y bloqueo de operadores `$` NoSQL. | `tests/unit/test_schemas.py` y `tests/unit/test_security.py` | **Aprobado (15/15)** |
| **Integridad por Motor** | **PostgreSQL:** `PK/FK`, `CHECK` (`saldo_kg >= 0`, estados válidos), `SELECT ... FOR UPDATE`. **MongoDB:** validadores estrictos `$jsonSchema` e índice parcial único `uq_analisis_lote_estudio_vigente`. **Neo4j:** constraints de unicidad y ausencia de nodos huérfanos. | `database/*/03_queries_and_tests.*` y `tests/integration/test_integrity_and_outbox.py` | **Aprobado** |
| **Funcional e Integración Multimotor** | Flujo completo E2E desde alta de cosecha (PG + Neo4j), recepción con control térmico `RN-07` (PG + Mongo + Neo4j), análisis versionados `V1`/`V2` `RN-05` y liberación `RN-02`, despacho fraccionado `RN-01`/`RN-03`, Recall `RN-08`, cierre `RN-09` y Expediente 360°. | `tests/e2e/test_flujo_completo_mvp.py` y `tests/smoke_frontend_api.py` | **Aprobado** |
| **Consistencia y Reconciliación** | Ante caída parcial simulada de Neo4j o MongoDB tras `COMMIT` en PostgreSQL, la API no reporta éxito falso: devuelve estado `pendiente_reconciliacion`, registra el evento en `eventos_reconciliacion` y converge vía `MERGE` idempotente al ejecutar `/api/v1/admin/reconciliacion/ejecutar`. | `tests/integration/test_integrity_and_outbox.py` | **Aprobado** |
| **Errores Negativos y Seguridad** | Rechazo de despacho de lote bloqueado (`RN-01` -> `409`), saldo insuficiente con rollback (`RN-03` -> `409`), liberación con análisis no conforme (`RN-02` -> `409`), productor/tienda inactivos (`RN-10` -> `409`), RBAC (`RN-04` -> `403`), aislamiento BOLA entre productores (`RN-11` -> `403`), SQLi/NoSQLi/Cypher injection (`422`) y fuerza bruta (`429`). | `tests/integration/test_routes_and_rbac.py` y `tests/integration/test_security_attacks.py` | **Aprobado (38/38)** |
| **Rendimiento** | Medición de latencias (`Min`, `Promedio`, `Mediana`, `P95`, `Max`) en 3 corridas independientes comparando **Nivel 1 (Semilla Base)** vs. **Nivel 2 (Carga Operativa Media de 500 lotes sincronizados)**. | `tests/benchmark_rendimiento.py` y `docs/pruebas/benchmark_resultados.json` | **Aprobado (P95 bajo meta)** |

## 2. Detalle de la Suite Automatizada (`pytest`)

Toda la batería automatizada del backend consta de **38 pruebas** distribuidas en tres niveles (`unit`, `integration` y `e2e`) y se ejecuta con un solo comando reproducible desde la raíz del proyecto:

```powershell
backend\.venv\Scripts\pytest.exe tests/ -v
```

### Desglose de Casos de Prueba Automatizados

#### A. Pruebas Unitarias (`tests/unit/`)
1. `test_lote_schema_valid_and_rejects_extra_fields`: Verifica que `LoteCreateRequest` acepte lotes válidos y rechace atributos no declarados (`extra="forbid"`).
2. `test_lote_schema_rejects_invalid_code_and_weight`: Valida la expresión regular `^AGU-[A-Z0-9]+-\d{6}-\d{2}$` y que `peso_inicial_kg > 0`.
3. `test_determinacion_rejects_nosql_dollar_operator_keys`: Bloquea llaves maliciosas como `$where` o `$gt` dentro de documentos dinámicos de laboratorio.
4. `test_evidencia_fotografica_rejects_javascript_uri`: Impide vectores XSS como `javascript:alert(1)` en URLs de evidencias fotográficas.
5. `test_envio_rejects_duplicate_lotes_in_same_request`: Garantiza que una misma orden de envío no duplique el mismo `codigo_lote`.
6. `test_incidente_cerrar_enforces_rn09_minimums`: Valida la regla `RN-09` exigiendo `causa_raiz` (>= 10 caracteres), al menos una acción correctiva y firmas de QA y Gerencia.
7. `test_recepcion_rejects_absurd_temperature`: Rechaza lecturas térmicas fuera del rango físico (`-10 °C` a `45 °C`).
8. `test_analisis_requires_valid_folio_regex`: Exige formato oficial `^LAB-\d{4}-[A-Z0-9-]+-V\d+$`.
9. `test_bcrypt_hash_and_verify`: Comprueba hashing seguro con `bcrypt` (12 rondas).
10. `test_jwt_create_and_decode_claims`: Valida emisión y lectura de claims `sub`, `role` y `productor_id`.
11. `test_jwt_rejects_alg_none`: Bloquea ataques de degradación de algoritmo (`alg: none`).
12. `test_jwt_rejects_expired_token`: Rechaza tokens expirados con `401 Unauthorized`.
13. `test_jwt_rejects_productor_without_productor_id`: Exige que todo token con rol `Productor` incluya su `productor_id` para hacer cumplir `RN-11`.
14. `test_sanitize_text_strips_html_and_script_tags`: Limpia etiquetas `<script>` y HTML peligroso antes de persistir.
15. `test_rate_limiter_blocks_after_threshold`: Verifica el bloqueo `429 Too Many Requests` al superar la ventana permitida.

#### B. Pruebas de Integración, Consistencia Outbox y Seguridad (`tests/integration/`)
16. `test_rn01_cannot_dispatch_blocked_lote`: Confirma que un lote en estado `Bloqueado` no puede despacharse (`409 Conflict`).
17. `test_rn03_acid_rollback_on_insufficient_balance`: Verifica que intentar despachar más kilogramos que el `saldo_kg` disponible devuelve `409 SALDO_INSUFICIENTE` y conserva intacto el saldo en PostgreSQL.
18. `test_rn10_blocks_inactive_producer_and_inactive_store`: Impide registrar cosechas de productores dados de baja lógica o envíos hacia sucursales inactivas (`409`).
19. `test_outbox_reconciliation_recovers_neo4j_and_mongo_partial_failures`: Simula la caída de Neo4j durante el alta de un lote y la caída de MongoDB durante una recepción; comprueba que el backend registra los eventos pendientes en `eventos_reconciliacion`, informa el estado degradado en el campo `sincronizacion` y converge al 100% cuando se invoca `POST /api/v1/admin/reconciliacion/ejecutar`.
20. `test_real_repos_use_parameterized_queries_only`: Audita el código fuente de los repositorios para asegurar que solo se utilicen consultas parametrizadas (`%s` en SQL y `$param` en Cypher).
21. `test_mongo_down_on_analisis_aborts_with_503_without_touching_neo4j`: Verifica que si la fuente primaria de un flujo (`MongoDB` en alta de análisis) no está disponible, la operación aborta con `503` sin dejar proyecciones huérfanas en Neo4j.
22. `test_analisis_filter_solo_no_conformes_and_duplicate_reception_guard`: Valida el filtro `$elemMatch` de parámetros no conformes y la protección contra doble recepción del mismo lote.
23. `test_cerrar_incidente_nonexistent_returns_404`: Verifica respuesta `404` al intentar cerrar un folio inexistente.
24. `test_openapi_exposes_all_14_contract_endpoints`: Comprueba que los 14 endpoints REST estén publicados y que `/api/v1/analisis` no exponga métodos `PUT` ni `DELETE` (`RN-05`).
25. `test_health_endpoint_masks_internal_errors`: Garantiza que si un motor falla, `/api/v1/health` reporte `degradado` sin filtrar URIs ni contraseñas en la respuesta HTTP.
26. `test_security_headers_present_on_api_responses`: Verifica presencia de `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy` y `Referrer-Policy`.
27. `test_max_body_size_middleware_rejects_over_5mb`: Rechaza cargas mayores a 5 MB con `413 Payload Too Large`.
28. `test_rbac_blocks_unauthorized_roles`: Verifica que `Recepcion`, `Productor` y `Laboratorio` reciban `403 Forbidden` al intentar liberar lotes, detonar un recall o ejecutar la reconciliación administrativa (`RN-04`).
29. `test_bola_idor_rn11_isolates_productor_data`: Comprueba que el Productor 1 no puede listar, consultar ni cosechar en parcelas del Productor 2 (`403 Forbidden`, `RN-11`).
30. `test_unhandled_exception_returns_safe_500_without_leaks`: Confirma que errores inesperados devuelven un JSON estandarizado sin trazas internas.
31. `test_unauthenticated_requests_rejected_with_401`: Bloquea peticiones sin token JWT.
32. `test_tampered_jwt_rejected_with_401`: Rechaza tokens con firma alterada.
33. `test_sql_and_cypher_injection_in_path_rejected_by_regex`: Bloquea payloads como `' OR 1=1--` y `'}) MATCH (n) DETACH DELETE n`.
34. `test_nosql_injection_in_analisis_payload_rejected`: Rechaza operadores `$where` inyectados en determinaciones de laboratorio (`422`).
35. `test_xss_payload_is_sanitized_before_storage`: Verifica eliminación de `<script>alert(1)</script>` en campos de texto.
36. `test_login_rate_limiting_blocks_brute_force`: Verifica que tras 10 intentos fallidos de login, el intento 11 recibe `429 Too Many Requests`.
37. `test_recall_rate_limiting_protects_multimotor_endpoint`: Protege el endpoint multimotor `/api/v1/incidentes/recall` frente a abuso automatizado (`429`).

#### C. Prueba de Extremo a Extremo del MVP (`tests/e2e/test_flujo_completo_mvp.py`)
38. `test_flujo_completo_mvp_cosecha_a_cierre_recall`: Recorre el ciclo de vida completo en una sola prueba encadenada:
    * Alta de 3 lotes (`AGU-P014-260320-01`, `AGU-P014-260320-02` y `AGU-P018-260320-01`).
    * Recepción en CEDIS donde dos lotes comparten el camión `MICH-842-K` y cuarto frío `CF-02` dentro de rango (`5.8 °C` y `6.1 °C`), mientras el tercero llega a `11.4 °C` activando automáticamente la retención por ruptura de cadena de frío (`RN-07`).
    * Carga de análisis `V1` (`No Conforme`), intento de liberación rechazado por `RN-02` (`409`), carga de contramuestra `V2` (`Conforme`) verificando que `V1` pase a `es_vigente: false` (`RN-05`), y liberación exitosa por QA.
    * Despacho fraccionado de `450 kg` y `400 kg` hacia dos tiendas, verificando el descuento ACID de `saldo_kg` a `1150 kg` (`RN-01`, `RN-03`).
    * Ejecución del **Protocolo de Recall de Emergencia (`RN-08`)**, comprobando que el lote pase a `Bloqueado`, Neo4j identifique las 2 tiendas destino y el lote hermano por contaminación cruzada, y MongoDB cree el expediente legal `INC-...`.
    * Intento de despacho posterior rechazado (`409`) y cierre formal del expediente con causa raíz, acciones correctivas y firmas duales (`RN-09`).

### Evidencia de Ejecución de `pytest` y Smoke Test en Vivo

```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-8.4.2, pluggy-1.7.0
rootdir: C:\Users\Emilia\OneDrive\Documentos\Emilia\UP\DaaS\proyecto-final
configfile: pytest.ini
collected 38 items

tests/e2e/test_flujo_completo_mvp.py::test_flujo_completo_mvp_cosecha_a_cierre_recall PASSED [  2%]
tests/integration/test_integrity_and_outbox.py::test_rn01_cannot_dispatch_blocked_lote PASSED [  5%]
tests/integration/test_integrity_and_outbox.py::test_rn03_acid_rollback_on_insufficient_balance PASSED [  7%]
tests/integration/test_integrity_and_outbox.py::test_rn10_blocks_inactive_producer_and_inactive_store PASSED [ 10%]
tests/integration/test_integrity_and_outbox.py::test_outbox_reconciliation_recovers_neo4j_and_mongo_partial_failures PASSED [ 13%]
...
tests/unit/test_security.py::test_rate_limiter_blocks_after_threshold PASSED [100%]

======================== 38 passed in 6.67s ========================
```

Evidencia del script de validación en vivo contra los contenedores Docker reales (`tests/smoke_frontend_api.py`):

```text
1. HEALTH: 200 operativo {'postgresql': {'status': 'operativo', 'detail': None}, 'mongodb': {'status': 'operativo', 'detail': None}, 'neo4j': {'status': 'operativo', 'detail': None}}
2. LOGIN qa_admin: 200 OK | Rol: QA | ProductorID: None
2. LOGIN recepcion_cedis: 200 OK | Rol: Recepcion | ProductorID: None
2. LOGIN lab_agrobio: 200 OK | Rol: Laboratorio | ProductorID: None
2. LOGIN productor_michoacan: 200 OK | Rol: Productor | ProductorID: 1
2. LOGIN productor_tancitaro: 200 OK | Rol: Productor | ProductorID: 2
3. PRODUCTOR LOTES COUNT: 4
4. CEDIS LOTES COUNT: 6
5. QA EXPEDIENTE 360 (/api/v1/lotes/{codigo}): 200 LOTE: AGU-P014-260312-01
   QA RED ADELANTE (/api/v1/trazabilidad/{codigo}/adelante): 200 TIENDAS: 2
   QA RED ATRAS/LATERAL (/api/v1/trazabilidad/{codigo}/atras-lateral): 200 CONTAMINACION CRUZADA: 0
6. LAB ANALISIS LOTE (/api/v1/analisis/{codigo}): 200 DOCUMENTOS: 2
```

## 3. Evaluación Básica de Rendimiento con Condiciones Documentadas

De acuerdo con las secciones 7.8 y 9 de la guía del proyecto, se realizó una evaluación de rendimiento midiendo tiempos de respuesta reales contra la API REST conectada a los tres contenedores en Docker (`tests/benchmark_rendimiento.py`), cuyo reporte crudo queda respaldado en `docs/pruebas/benchmark_resultados.json`.

### 3.1 Condiciones Documentadas del Entorno de Prueba

* **Equipo Host:** Procesador Intel Core 5 210H (12 núcleos lógicos, arquitectura `AMD64`) con 15.6 GB de memoria RAM física.
* **Sistema Operativo y Contenedorización:** Windows 11 (Build `10.0.26200`) ejecutando Docker Desktop `v29.9.2` sobre motor Linux (WSL2).
* **Motores de Bases de Datos en Contenedores:**
  * **Relacional:** `postgres:16-alpine` (`trazaagro-postgres`, puerto host `5434` -> `5432` configurado en `.env` local durante el benchmark; el valor por defecto en `docker-compose.yml` y `.env.example` es `5433`).
  * **Documental:** `mongo:7` (`trazaagro-mongo`, puerto host `27017`).
  * **Grafos:** `neo4j:5-community` (`trazaagro-neo4j`, puertos host `7474` HTTP y `7687` Bolt).
* **Backend y Cliente de Medición:** Python `3.13.5`, FastAPI + Uvicorn en `http://127.0.0.1:8000` (1 worker asíncrono, conexión local *loopback* con cuenta de menor privilegio `trazaagro_app`), cliente HTTP `httpx`.
* **Metodología de Muestreo (3 Corridas Independientes):**
  * Antes de iniciar la medición se ejecutan **3 peticiones de calentamiento (*warmup*)** descartadas para inicializar pools y planes de ejecución en caché.
  * Se ejecutan **3 corridas independientes** de **25 iteraciones medidas** cada una (75 peticiones medidas por endpoint en cada nivel de volumen), calculando latencia mínima, promedio, mediana, percentil 95 (`P95`) y máxima en milisegundos.

### 3.2 Declaración del Volumen de Datos Evaluado por Motor

Para comprobar tanto el desempeño sobre el estado semilla inicial como la escalabilidad real de los índices relacionales, documentales y de grafos, el script evalúa dos niveles de volumen y restaura automáticamente las semillas originales al finalizar:

| Motor / Estructura | Nivel 1: Semilla Base (Entregable 4) | Nivel 2: Carga Operativa Media (Simulación Mensual) | Factor de Escala |
| :--- | :--- | :--- | :---: |
| **PostgreSQL 16 (Total filas)** | **39 filas** (6 lotes, 5 recepciones, 4 envíos, 5 detalles, 3 productores, 4 parcelas, 4 tiendas, 6 incidentes, 2 reconciliaciones) | **2,194 filas** (500 lotes, 450 recepciones, 400 envíos, 797 líneas de detalle, 3 productores, 4 parcelas, 4 tiendas, 34 incidentes, 2 reconciliaciones) | **56x más filas** |
| **MongoDB 7 (Total documentos)** | **12 documentos** (5 `actas_recepcion`, 5 `analisis_laboratorio`, 2 `expedientes_incidentes`) | **1,080 documentos** (450 `actas_recepcion`, 600 `analisis_laboratorio` con historial `V1`/`V2` y arreglos anidados, 30 `expedientes_incidentes`) | **90x más documentos** |
| **Neo4j 5 (Grafo físico)** | **31 nodos y 38 relaciones** | **921 nodos y 3,601 relaciones** (`:COSECHADO_EN`, `:TRASLADADO_EN`, `:ALMACENADO_EN`, `:EMITIO_ANALISIS`, `:DIVIDIDO_EN`, `:DESPACHADO_EN`, `:ENTREGADO_A`) | **95x más relaciones** |

*Nota de rendimiento de escritura masiva:* La inyección coordinada de los 494 lotes adicionales y sus recepciones, análisis, envíos y subgrafo completo en los tres motores tomó únicamente **`1,126.86 ms` (1.12 segundos)**.

### 3.3 Resultados de las 3 Corridas — Nivel 1: Semilla Base (6 Lotes / 38 Relaciones)

Lote evaluado: `AGU-P014-260312-01` (25 iteraciones por corrida = 75 peticiones por endpoint).

| Escenario Evaluado | Motor(es) | Corrida 1 (P95) | Corrida 2 (P95) | Corrida 3 (P95) | Min Global | Promedio Global | P95 Global | Meta P95 | Estado |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /api/v1/health` | PG + Mongo + Neo4j | 22.53 ms | 15.04 ms | 12.69 ms | 6.52 ms | 11.56 ms | **16.75 ms** | < 100 ms | **OK** |
| `GET /api/v1/lotes` | PostgreSQL 16 | 10.62 ms | 7.51 ms | 8.12 ms | 5.08 ms | 7.08 ms | **8.75 ms** | < 100 ms | **OK** |
| `GET /api/v1/analisis/{lote}` | MongoDB 7 | 18.49 ms | 10.20 ms | 12.69 ms | 7.87 ms | 10.21 ms | **13.79 ms** | < 100 ms | **OK** |
| `GET /api/v1/trazabilidad/{lote}/adelante` | Neo4j 5 (N-saltos) | 17.36 ms | 15.52 ms | 29.98 ms | 9.99 ms | 14.99 ms | **20.95 ms** | < 150 ms | **OK** |
| `GET /api/v1/trazabilidad/{lote}/atras-lateral` | Neo4j 5 (Lateral) | 24.33 ms | 43.23 ms | 31.90 ms | 12.81 ms | 21.22 ms | **33.15 ms** | < 150 ms | **OK** |
| `GET /api/v1/lotes/{lote}` (Expediente 360°) | PG + Mongo + Neo4j | 53.50 ms | 70.52 ms | 60.04 ms | 27.09 ms | 41.07 ms | **61.35 ms** | < 200 ms | **OK** |

### 3.4 Resultados de las 3 Corridas — Nivel 2: Carga Operativa Media (500 Lotes / 3,601 Relaciones)

Lote evaluado: `AGU-PERF1-260401-02` (25 iteraciones por corrida = 75 peticiones por endpoint).

| Escenario Evaluado | Motor(es) | Corrida 1 (P95) | Corrida 2 (P95) | Corrida 3 (P95) | Min Global | Promedio Global | P95 Global | Meta P95 | Estado |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /api/v1/health` | PG + Mongo + Neo4j | 9.71 ms | 26.37 ms | 11.40 ms | 6.88 ms | 12.27 ms | **15.83 ms** | < 100 ms | **OK** |
| `GET /api/v1/lotes` (500 lotes) | PostgreSQL 16 | 22.79 ms | 28.98 ms | 26.40 ms | 11.13 ms | 16.46 ms | **26.06 ms** | < 100 ms | **OK** |
| `GET /api/v1/analisis/{lote}` (1,080 docs) | MongoDB 7 | 11.66 ms | 15.03 ms | 21.81 ms | 7.87 ms | 11.99 ms | **16.17 ms** | < 100 ms | **OK** |
| `GET /api/v1/trazabilidad/{lote}/adelante` | Neo4j 5 (N-saltos) | 12.88 ms | 24.65 ms | 21.84 ms | 9.02 ms | 15.02 ms | **19.79 ms** | < 150 ms | **OK** |
| `GET /api/v1/trazabilidad/{lote}/atras-lateral` | Neo4j 5 (3,601 rels) | 100.51 ms | 52.43 ms | 50.65 ms | 21.13 ms | 42.47 ms | **67.86 ms** | < 150 ms | **OK** |
| `GET /api/v1/lotes/{lote}` (Expediente 360°) | PG + Mongo + Neo4j | 100.03 ms | 73.04 ms | 58.70 ms | 34.07 ms | 52.73 ms | **77.26 ms** | < 200 ms | **OK** |

### 3.5 Análisis Técnico de Resultados y Comparación entre Corridas

1. **Efecto de estabilización entre la Corrida 1 y las Corridas 2 y 3:**
   * En el **Nivel 2** (con 921 nodos y 3,601 relaciones recién insertadas), la **Corrida 1** del análisis de contaminación cruzada (`/atras-lateral`) registró un `P95` de `100.51 ms` y el Expediente 360° un `P95` de `100.03 ms` mientras Neo4j y PostgreSQL poblaban sus cachés de páginas con el nuevo grafo denso.
   * Para las **Corridas 2 y 3**, una vez estabilizado el plan de ejecución en memoria, la latencia `P95` de contaminación cruzada descendió a **`52.43 ms` y `50.65 ms`** (reducción del ~50%), y el Expediente 360° bajó de `100.03 ms` a **`73.04 ms` y `58.70 ms`**. Esto confirma la importancia de evaluar múltiples corridas para distinguir la latencia en frío de la latencia operativa estable.
2. **Escalabilidad logarítmica gracias a los índices por motor:**
   * **MongoDB:** Al pasar de 12 a **1,080 documentos** (90x más volumen), la consulta de historial de análisis (`GET /api/v1/analisis/{lote}`) mantuvo su `P95` prácticamente constante (**13.79 ms** en Nivel 1 vs. **16.17 ms** en Nivel 2) gracias al índice compuesto `idx_analisis_historial_versiones` (`{ codigo_lote: 1, tipo_estudio: 1, version: -1 }`).
   * **Neo4j:** En el recorrido hacia adelante (`/adelante`) para localizar tiendas afectadas por un recall, el `P95` global fue de **19.79 ms** sobre 3,601 relaciones (idéntico a los **20.95 ms** del Nivel 1), porque Neo4j parte del constraint único `codigo_lote` y solo atraviesa las aristas conectadas al lote origen (*index-free adjacency*), sin importar cuántos miles de lotes adicionales existan en el grafo.
   * **Consolidación Multimotor (Expediente 360°):** Consultar los tres motores en una misma petición HTTP y ensamblar la respuesta unificada promedió **52.73 ms** (`P95` de **77.26 ms**) bajo carga operativa media, cumpliendo holgadamente la meta de `< 200 ms`.

## 4. Guía Completa de Instalación, Configuración, Carga y Despliegue

Cualquier evaluador o desarrollador puede levantar el ecosistema completo desde cero siguiendo estos pasos en orden.

### 4.1 Requisitos Previos
* **Docker Desktop** (con Docker Compose v2 activo).
* **Python 3.11 o superior** (validado en Python `3.13.5`).
* **Node.js 20 o superior** y `npm`.
* **Git**.

No se requiere instalar PostgreSQL, MongoDB ni Neo4j localmente en el sistema operativo anfitrión.

### 4.2 Configuración de Variables de Entorno (`.env`)

Desde la raíz del repositorio, copia la plantilla de ejemplo `.env.example` (que no contiene credenciales reales sensibles de producción) hacia `.env`:

```powershell
Copy-Item .env.example .env
```

> **Nota sobre el puerto de PostgreSQL en Windows:** Por defecto `.env.example` utiliza `POSTGRES_PORT=5433`. Si tienes una instalación local de PostgreSQL en Windows ocupando `5432` o `5433`, puedes cambiar `POSTGRES_PORT=5434` en tu archivo `.env` y actualizar el puerto en `POSTGRES_URI=postgresql://trazaagro_app:trazaagro_app_pass@localhost:5434/trazaagro`.

### 4.3 Despliegue de Contenedores y Carga Reproducible de las 3 Bases

1. **Levantar los tres contenedores esperando confirmación de sus healthchecks:**

```powershell
docker compose up -d --wait
```

2. **Ejecutar los scripts DDL, datos semilla y pruebas de integridad de PostgreSQL 16:**

```powershell
docker exec trazaagro-postgres psql -v ON_ERROR_STOP=1 -U trazaagro -d trazaagro -f /scripts/01_schema.sql
docker exec trazaagro-postgres psql -v ON_ERROR_STOP=1 -U trazaagro -d trazaagro -f /scripts/02_seed_data.sql
docker exec trazaagro-postgres psql -v ON_ERROR_STOP=1 -U trazaagro -d trazaagro -f /scripts/03_queries_and_tests.sql
```

3. **Ejecutar los validadores `$jsonSchema`, semillas y pruebas de MongoDB 7:**

```powershell
$mongoUri = "mongodb://trazaagro:trazaagro_dev_pass@localhost:27017/trazaagro?authSource=admin"
docker exec trazaagro-mongo mongosh $mongoUri --file /scripts/01_setup_collections.js
docker exec trazaagro-mongo mongosh $mongoUri --file /scripts/02_seed_data.js
docker exec trazaagro-mongo mongosh $mongoUri --file /scripts/03_queries_and_tests.js
```

4. **Ejecutar los constraints, grafo semilla y consultas de validación de Neo4j 5:**

```powershell
docker exec trazaagro-neo4j cypher-shell -u neo4j -p trazaagro_dev_pass -f /scripts/01_schema.cypher
docker exec trazaagro-neo4j cypher-shell -u neo4j -p trazaagro_dev_pass -f /scripts/02_seed_data.cypher
docker exec trazaagro-neo4j cypher-shell -u neo4j -p trazaagro_dev_pass -f /scripts/03_queries_and_tests.cypher
```

### 4.4 Instalación y Ejecución del Backend (FastAPI)

Desde la raíz del proyecto, crea el entorno virtual, instala las dependencias e inicia el servidor:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

* **Endpoint de salud multimotor:** `http://127.0.0.1:8000/api/v1/health`
* **Documentación interactiva OpenAPI (Swagger UI):** `http://127.0.0.1:8000/docs`

### 4.5 Instalación y Ejecución del Frontend (Escritorio Electron y Web)

En una nueva terminal, instala las dependencias de `frontend/`:

```powershell
cd frontend
npm install
```

Puedes ejecutar la aplicación en cualquiera de sus dos modalidades oficiales:

* **Opción A — Aplicación Nativa de Escritorio (Electron + Vite):**
  ```powershell
  npm run desktop
  ```
* **Opción B — Navegador Web (SPA en `http://localhost:5173`):**
  ```powershell
  npm run dev
  ```

### 4.6 Cuentas Semilla para Demostración Funcional por Rol

En la pantalla de inicio de sesión puedes hacer clic directo en las tarjetas de **Acceso Rápido Demo** o ingresar cualquiera de las siguientes credenciales oficiales:

| Rol RBAC | Usuario | Contraseña | Vistas y Operaciones Autorizadas |
| :--- | :--- | :--- | :--- |
| **QA / Gerencia** | `qa_admin` | `TrazaQA2026!` | Consola Recall 360° (`/qa/recall`), Tablero Ejecutivo Gerencia (`/qa/gerencia`), liberación (`RN-02`), recall (`RN-08`), cierre (`RN-09`) y reconciliación outbox. |
| **Recepción CEDIS** | `recepcion_cedis` | `TrazaRec2026!` | Panel CEDIS (`/cedis`), registro de recepción térmica (`RN-07`), acta documental y despacho fraccionado a tiendas (`RN-01`, `RN-03`). |
| **Laboratorio Externo** | `lab_agrobio` | `TrazaLab2026!` | Panel Laboratorio (`/laboratorio`), emisión de certificados y enmiendas versionadas inmutables (`V1`, `V2`, `RN-05`). |
| **Productor 1 (Michoacán)** | `productor_michoacan` | `TrazaProd1!` | Panel Productor (`/productor`), alta de cosecha y consulta exclusiva de sus propios lotes (`RN-11`). |
| **Productor 2 (Tancítaro)** | `productor_tancitaro` | `TrazaProd2!` | Panel Productor (`/productor`), alta de cosecha y consulta aislada a sus huertas (`RN-11`). |

### 4.7 Comandos Rápidos para Reproducir Todas las Pruebas

Con los contenedores Docker y el servidor FastAPI activos en el puerto `8000`, ejecuta desde la raíz del repositorio:

```powershell
# 1. Suite automatizada completa (38 pruebas unitarias, integración, seguridad y E2E)
backend\.venv\Scripts\pytest.exe tests/ -v

# 2. Prueba de humo en vivo de todos los flujos del frontend contra Docker
backend\.venv\Scripts\python.exe tests\smoke_frontend_api.py

# 3. Benchmark de rendimiento en 2 niveles de volumen y 3 corridas independientes
backend\.venv\Scripts\python.exe tests\benchmark_rendimiento.py --output docs\pruebas\benchmark_resultados.json
```
