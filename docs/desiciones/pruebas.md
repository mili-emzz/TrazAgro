# Reporte de Pruebas del Backend: TrazaAgro

Este documento concentra los resultados de la validación integral del backend de **TrazaAgro** (FastAPI + arquitectura políglota PostgreSQL, MongoDB y Neo4j) en la rama `feature/backend-api`. Las pruebas cubren los cuatro frentes críticos acordados: rutas y contratos REST, flujo de datos extremo a extremo, integridad y consistencia multimotor (incluyendo fallos parciales) y seguridad ofensiva/defensiva.

## Resumen Ejecutivo y Entorno de Ejecución

* **Suite automatizada (`pytest`):** **38 de 38 pruebas aprobadas (100%)**, sin advertencias de seguridad JWT tras actualizar la clave a 256 bits.
* **Validación en vivo contra Docker:** **100% operativa** contra los tres contenedores reales (`trazaagro-postgres`, `trazaagro-mongo` y `trazaagro-neo4j`) autenticados con el usuario PoLP `trazaagro_app`.
* **Comando reproducible:** `pytest tests/ -v` (configurado mediante `pytest.ini` en la raíz del repositorio).
* **Entorno:** Windows, Python `3.13.5`, FastAPI + Starlette `TestClient`, `pytest 8.4.2`, `PyJWT`, `bcrypt`, `Pydantic v2`, Docker Compose (`postgres:16-alpine` en puerto `5434`, `mongo:7` en `27017`, `neo4j:5-community` en `7687`).
* **Alcance de la corrida:** Combina pruebas unitarias, de integración de rutas/seguridad/Outbox y flujo E2E completo (38 tests deterministas con repositorios estatales en memoria + inspección de parametrización real), complementadas con una corrida en vivo sin mocks sobre las tres bases de datos en Docker.

## 1. Validación de Rutas y Contratos REST

Se verificó el esquema OpenAPI generado por `backend/main.py` y el comportamiento HTTP de los **14 endpoints oficiales** definidos en `docs/03-arquitectura.md` (más el listado auxiliar `GET /api/v1/lotes` con aislamiento por rol):

| Ruta y Método | Reglas / Rol Validado | Resultado |
| :--- | :--- | :--- |
| `GET /api/v1/health` | Público; enmascara errores internos y credenciales en estado `degradado` | Aprobada |
| `POST /api/v1/auth/login` | Emite JWT `HS256`, mensaje genérico `401`, rate limit `429` | Aprobada |
| `GET /api/v1/lotes` | Filtra por `productor_id` si el rol es `Productor` (`RN-11`) y valida `estado` | Aprobada |
| `POST /api/v1/lotes` | Roles `Productor`/`QA`, `RN-06`, `RN-10`, `RN-11`, proyección PG → Neo4j | Aprobada |
| `GET /api/v1/lotes/{codigo_lote}` | Expediente 360° fusionando PG + Mongo + Neo4j; `RN-11` | Aprobada |
| `PATCH /api/v1/lotes/{codigo_lote}/liberar` | Solo `QA` (`RN-04`), valida conformidad vigente en MongoDB (`RN-02`) | Aprobada |
| `POST /api/v1/recepciones` | Solo `Recepcion`, evalúa cadena de frío `4.0–8.0 °C` (`RN-07`) | Aprobada |
| `POST /api/v1/analisis` | Roles `Laboratorio`/`QA`, versionado inmutable (`RN-05`), sin `PUT`/`DELETE` | Aprobada |
| `GET /api/v1/analisis/{codigo_lote}` | Filtros `solo_vigentes` y `solo_no_conformes` (`$elemMatch`), `RN-11` | Aprobada |
| `POST /api/v1/envios` | Solo `Recepcion`, descuento ACID (`RN-01`, `RN-03`, `RN-10`) | Aprobada |
| `POST /api/v1/incidentes/recall` | Solo `QA` (`RN-04`), bloqueo atómico + hermanos (`RN-08`), rate limit `429` | Aprobada |
| `PATCH /api/v1/incidentes/{folio}/cerrar` | Solo `QA`, exige causa raíz, acciones correctivas y firmas (`RN-09`) | Aprobada |
| `GET /api/v1/trazabilidad/{codigo_lote}/adelante` | Solo `QA`, rastreo *Forward* hacia envíos y tiendas | Aprobada |
| `GET /api/v1/trazabilidad/{codigo_lote}/atras-lateral` | Solo `QA`, rastreo *Backward* (parcela/productor) y lateral (`RN-08`) | Aprobada |
| `POST /api/v1/admin/reconciliacion/ejecutar` | Solo `QA`, reprocesa `eventos_reconciliacion` de forma idempotente | Aprobada |

Adicionalmente se comprobó que `POST /api/v1/analisis` **no expone métodos `PUT` ni `DELETE`**, blindando físicamente la inmutabilidad analítica (`RN-05`).

## 2. Validación de Flujo de Datos Extremo a Extremo (E2E)

La prueba `tests/e2e/test_flujo_completo_mvp.py` ejecuta el ciclo de vida completo del MVP coordinando los 4 actores:

1. **Cosecha (`Productor`):** Productor 1 registra dos lotes hermanos (`AGU-P014-260320-01` y `AGU-P014-260320-02`) con `estado = 'Cosechado'` y `saldo_kg = 2000.0`. Productor 2 registra `AGU-P018-260320-01`.
2. **Recepción CEDIS (`Recepcion` / `RN-07`):**
   * Los dos lotes hermanos arriban en el mismo camión (`MICH-842-K`) y se almacenan en `CF-02` a `5.8 °C` y `6.1 °C` → dictamen `Conforme`, estado `Recibido`, `alerta_cadena_frio = false`.
   * El lote de Productor 2 llega a `11.4 °C` (fuera de `4.0–8.0 °C`) → dictamen `Retenido`, estado `En revision`, `alerta_cadena_frio = true`.
3. **Certificación y Versionado (`Laboratorio` / `RN-05`) + Liberación (`QA` / `RN-02`):**
   * Se carga `V1` con dictamen `No Conforme` (Clorpirifos `0.08 > 0.01 mg/kg`). El intento de QA de liberar el lote es rechazado con `409 Conflict` (`RN-02`).
   * Se intenta emitir `V2` sin `motivo_enmienda` → rechazado con `400 Bad Request` (`RN-05`).
   * Se emite `V2` con `motivo_enmienda` y dictamen `Conforme` → `V1` se conserva inmutable con `es_vigente = false` y `V2` queda activa (`es_vigente = true`). QA libera exitosamente el lote (`Liberado`).
4. **Despacho Fraccionado (`Recepcion` / `RN-01`, `RN-03`):** Se envían `450.0 kg` a la tienda `SUC-MTY-04` (`ENV-2026-3001`), descontando el saldo en PostgreSQL de `2000.0 kg` a `1550.0 kg` y proyectando la entrega en Neo4j.
5. **Expediente 360° y Trazabilidad (`QA`):**
   * `GET /api/v1/lotes/{codigo}` consolida saldo SQL (`1550.0 kg`), acta de recepción Mongo, historial de 2 análisis y envíos Neo4j en menos de `200 ms`.
   * El rastreo *Forward* confirma `450.0 kg` en `SUC-MTY-04` y el rastreo lateral detecta al lote hermano `AGU-P014-260320-02` por vehículo compartido `MICH-842-K`.
6. **Protocolo de Recall Integrado (`QA` / `RN-08`) y Cierre (`RN-09`):**
   * `POST /api/v1/incidentes/recall` bloquea atómicamente el lote origen y su hermano, inmoviliza `1550.0 kg`, identifica la tienda afectada y abre el expediente `INC-2026-3001` en MongoDB (latencia `< 150 ms`).
   * Un intento posterior de despacho sobre el lote bloqueado es rechazado con `409 Conflict` (`RN-01`).
   * `PATCH /api/v1/incidentes/INC-2026-3001/cerrar` valida causa raíz, acciones correctivas y firmas QA/Gerencia, cerrando el expediente en MongoDB y transicionando los lotes a `Retirado` en PostgreSQL y Neo4j.

## 3. Validación de Integridad y Consistencia ante Fallos Parciales

Cubierto en `tests/integration/test_integrity_and_outbox.py`:

* **Reglas transaccionales y catálogos:** Se comprobó rechazo `409 Conflict` al despachar lotes bloqueados (`RN-01`), al solicitar kilos superiores al saldo disponible verificando que el saldo original permanezca intacto tras rollback (`RN-03`), al intentar operar con productores o tiendas inactivas (`RN-10`) y al recibir dos veces un mismo lote.
* **Aborto seguro ante caída de MongoDB en `/analisis`:** Cuando MongoDB no está disponible durante `POST /api/v1/analisis`, la API responde `503 Service Unavailable` y no deja proyecciones huérfanas en Neo4j ni eventos en el outbox.
* **Consistencia eventual con Patrón Outbox (`eventos_reconciliacion`):**
  * Se simuló la caída de Neo4j durante `POST /api/v1/lotes` y la caída simultánea de MongoDB + Neo4j durante `POST /api/v1/incidentes/recall`.
  * En ambos casos PostgreSQL confirmó la operación crítica (bloqueando el lote inmediatamente para proteger inocuidad), la API reportó transparentemente `"pendiente_reconciliacion"` y se generaron 3 eventos en `eventos_reconciliacion`.
  * Al restablecer los motores y llamar a `POST /api/v1/admin/reconciliacion/ejecutar`, los 3 eventos se reprocesaron con `0` fallos, convergiendo el nodo `:Lote` en Neo4j (`Bloqueado`) y el expediente `INC-2026-7777` en MongoDB.
* **Consultas 100% parametrizadas:** Se inspeccionaron las llamadas reales de `PostgresRepository` y `Neo4jRepository` ante entradas maliciosas confirmando separación estricta entre sentencia (`%s` / `$codigo_lote`) y parámetros.

## 4. Validación de Seguridad

Cubierto en `tests/unit/test_security.py`, `tests/unit/test_schemas.py`, `tests/integration/test_routes_and_rbac.py` y `tests/integration/test_security_attacks.py`:

* **Autenticación y criptografía:** Hash `bcrypt` con factor de costo `12` (`$2b$12$`), tokens JWT `HS256` con claims obligatorios (`sub`, `role`, `productor_id`, `iat`, `exp`, `jti`), rechazo explícito de `alg: "none"`, rechazo de tokens expirados, alterados o de `Productor` sin `productor_id` (`401 Unauthorized`).
* **RBAC (`RN-04`) y BOLA/IDOR (`RN-11`):**
  * Matriz de permisos verificada: `Recepcion` bloqueado (`403`) en liberación, recall y reconciliación; `Productor` bloqueado (`403`) en recepciones, envíos y análisis; `Laboratorio` bloqueado (`403`) en alta de lotes y cierre de incidentes.
  * Aislamiento `RN-11`: `Productor 1` accede a sus lotes (`200`), pero recibe `403 Forbidden` al consultar expediente, análisis o intentar crear lotes en parcelas de `Productor 2`.
* **Prevención de inyecciones y XSS:**
  * Payloads de SQL Injection y Cypher Injection en rutas son rechazados desde la capa de validación (`422`) y neutralizados por parametrización en repositorios.
  * Payloads de NoSQL Injection (`$where`, claves con `.`) en determinaciones polimórficas son rechazados con `422`.
  * Etiquetas `<script>` en texto libre se sanitizan antes de persistir; URLs `javascript:` en evidencias fotográficas son rechazadas con `422`.
  * Campos inesperados (`extra="forbid"`) y rangos físicos absurdos (temperaturas fuera de `-5..40 °C`, pesos negativos) son rechazados con `422`.
* **Protección HTTP y DoS:**
  * Cabeceras obligatorias confirmadas en respuestas: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Content-Security-Policy` y `Referrer-Policy`.
  * Límite de tamaño de payload de `5 MB` devuelve `413 Payload Too Large`.
  * Rate limiting activo devuelve `429 Too Many Requests` tras exceder intentos en `/api/v1/auth/login` y `/api/v1/incidentes/recall`.
  * Manejador global de excepciones no controladas responde `500` con `codigo_referencia` de 8 caracteres sin filtrar trazas, nombres de tablas ni credenciales.

## 5. Hallazgos Detectados y Remediados Durante las Pruebas

Durante la auditoría y ejecución de la suite se detectaron cinco oportunidades reales de endurecimiento que quedaron corregidas en el commit `814a725`:

1. **Inyección de operadores NoSQL en determinaciones polimórficas:** `DeterminacionSchema` permitía campos extra (`extra="allow"`) para acomodar distintos estudios de laboratorio; se añadió un validador que rechaza cualquier llave que inicie con `$` o contenga `.`.
2. **Esquemas de URL peligrosos en evidencias fotográficas:** `EvidenciaFotograficaSchema.url_archivo` ahora exige prefijos seguros (`https://`, `http://` o `/`), bloqueando esquemas `javascript:` o `data:`.
3. **Lotes duplicados dentro de un mismo envío:** Se agregó validación en `EnvioCreateRequest` para rechazar lotes repetidos en `detalles` desde la capa Pydantic (`422`), complementando el candado `UNIQUE` de PostgreSQL.
4. **Filtro `estado` no acotado en `GET /api/v1/lotes`:** Se restringió el parámetro de consulta a `Literal` con los 6 estados oficiales del dominio.
5. **Longitud de clave JWT (`InsecureKeyLengthWarning`):** La clave por defecto en `backend/core/config.py`, `.env.example` y `.env` tenía 31 bytes (menor a los 32 bytes / 256 bits recomendados por RFC 7518). Fue corregida en los tres archivos y revalidada en `pytest` con cero advertencias de PyJWT.
6. **Colisión de puerto 5433 y roles PoLP en volúmenes Docker:** Los servicios locales de PostgreSQL en Windows (`postgresql-x64-17`/`18`) interceptaban el puerto `5433`, y los volúmenes previos de Docker no contenían el usuario `trazaagro_app`. Se mapeó `trazaagro-postgres` al puerto `5434` en `.env` y se aprovisionó `trazaagro_app` en PostgreSQL y MongoDB.

## 6. Validación en Vivo contra Contenedores Docker (PostgreSQL + MongoDB + Neo4j)

Una vez levantados los tres contenedores y resuelto el puerto `5434`, se ejecutó `TestClient(app)` **sin mocks ni overrides** directo contra la infraestructura real:

| Endpoint Evaluado | Resultado HTTP | Evidencia Real Observada |
| :--- | :--- | :--- |
| `GET /api/v1/health` | `200 OK` | `status: "operativo"` en `postgresql`, `mongodb` y `neo4j` (`detail: null`) |
| `POST /api/v1/auth/login` | `200 OK` | Emisión de JWT `HS256` para `qa_admin` sin warnings |
| `GET /api/v1/lotes` | `200 OK` | `6` lotes maestros consultados desde PostgreSQL (`trazaagro_app`) |
| `GET /api/v1/lotes/AGU-P014-260312-01` | `200 OK` | Expediente 360° completo: `estado = Bloqueado`, `2` análisis (Mongo), `2` envíos y `2` vínculos hermanos (Neo4j), `advertencias = []` |
| `GET /api/v1/trazabilidad/AGU-P014-260312-01/adelante` | `200 OK` (`58.8 ms`) | `2` envíos, `850.0 kg` despachados en Neo4j |
| `GET /api/v1/trazabilidad/AGU-P014-260312-01/atras-lateral` | `200 OK` (`266.1 ms`) | Detección de lote hermano `AGU-P014-260312-02` por vehículo y cuarto frío compartidos |
| `GET /api/v1/analisis/AGU-P014-260312-01?solo_no_conformes=true` | `200 OK` | `1` certificado infractor recuperado con `$elemMatch` (`LAB-2026-AGU-0842-V1`) |

Con la suite automatizada en verde (`38/38`) y la validación en vivo aprobada sobre los tres motores reales, el backend queda listo para integrarse con el frontend.
