# Entregable 6: Backend y API (TrazaAgro)

Este documento describe la implementación de la capa de servidor y la API REST de **TrazaAgro**, cumpliendo con los requisitos de la sección 7.6 de la guía oficial (`docs/guia-proyecto/guia-proyecto.md`) y los contratos definidos en `docs/03-arquitectura.md`.

## 1. Estilo de API y Justificación Tecnológica

La comunicación entre la aplicación cliente (escritorio Electron / web SPA) y los tres motores de bases de datos se centraliza en una **API REST v1** bajo `/api/v1/*`, implementada con **Python 3.13 + FastAPI + Pydantic v2** sobre servidor ASGI (`Uvicorn`).

* **Por qué API REST sobre GraphQL:** Los flujos críticos de TrazaAgro (recepción térmica en CEDIS, despacho fraccionado ACID, protocolo de recall de emergencia y cierre de expedientes) tienen contratos transaccionales bien definidos por caso de uso y códigos de estado HTTP semánticos (`201`, `403`, `409`, `422`, `429`, `503`). REST permite mapear directamente estas reglas de negocio, aplicar *rate limiting* granular por endpoint (`/auth/login`, `/incidentes/recall`) y exponer documentación interactiva OpenAPI 3.1 en `/docs`.
* **Aislamiento total de la interfaz:** El frontend nunca conoce credenciales, puertos ni consultas SQL, BSON o Cypher; toda lectura y escritura multimotor ocurre exclusivamente en el backend.

## 2. Arquitectura Modular en Capas y Archivos Reales

El directorio `backend/` separa estrictamente el transporte HTTP, la coordinación de reglas de negocio y el acceso nativo a cada motor de persistencia:

```text
backend/
├── main.py                                # App ASGI, lifespan de conexiones, CORS, middlewares y handlers globales
├── core/
│   ├── config.py                          # Carga de variables desde .env mediante pydantic-settings
│   ├── database.py                        # DatabaseManager: pool PostgreSQL, cliente MongoDB y driver Neo4j
│   ├── exceptions.py                      # Jerarquía de excepciones de dominio (400, 401, 403, 404, 409, 429, 503)
│   ├── middleware.py                      # SecurityHeadersMiddleware y MaxBodySizeMiddleware (límite 5 MB)
│   └── security.py                        # JWT HS256, bcrypt, sanitización XSS y rate limiters en memoria
├── controllers/                           # 9 routers FastAPI (HTTP, validación Pydantic, JWT y RBAC)
│   ├── auth.py                            # POST /api/v1/auth/login
│   ├── health.py                          # GET /api/v1/health
│   ├── lotes.py                           # POST /api/v1/lotes, GET /api/v1/lotes, GET/PATCH /api/v1/lotes/{codigo}
│   ├── recepciones.py                     # POST /api/v1/recepciones
│   ├── analisis.py                        # POST /api/v1/analisis, GET /api/v1/analisis/{codigo}
│   ├── envios.py                          # POST /api/v1/envios
│   ├── incidentes.py                      # POST /api/v1/incidentes/recall, PATCH /api/v1/incidentes/{folio}/cerrar
│   ├── trazabilidad.py                    # GET /api/v1/trazabilidad/{codigo}/adelante y /atras-lateral
│   └── reconciliacion.py                  # POST /api/v1/admin/reconciliacion/ejecutar
├── schemas/                               # Contratos Pydantic v2 (extra="forbid", regex y validadores de seguridad)
│   ├── auth.py, health.py, lotes.py, recepciones.py, analisis.py,
│   └── envios.py, incidentes.py, trazabilidad.py, reconciliacion.py
├── services/                              # Orquestación multimotor, outbox y reglas RN-01 a RN-11
│   ├── auth_service.py                    # Catálogo de perfiles semilla, bcrypt.checkpw y emisión JWT
│   ├── lotes_service.py                   # Alta de cosecha, recepción RN-07, listado BOLA RN-11 y Expediente 360°
│   ├── laboratorio_service.py             # Versionado inmutable RN-05 y liberación sanitaria RN-02
│   ├── despachos_service.py               # Despacho fraccionado ACID RN-01 / RN-03 / RN-10
│   ├── trazabilidad_qa_service.py         # Recall 360° RN-08, cierre RN-09 y consultas de grafo Neo4j
│   └── reconciliacion_service.py          # Reprocesamiento idempotente de eventos_reconciliacion
└── repositories/                          # Acceso directo con drivers oficiales por paradigma
    ├── relational/postgres_repo.py        # Consultas SQL parametrizadas (%s) con psycopg v3
    ├── document/mongo_repo.py             # Operaciones BSON y agregaciones con pymongo
    └── graph/neo4j_repo.py                # Sentencias Cypher parametrizadas ($param) y MERGE con neo4j
```

## 3. Drivers Oficiales y Configuración Externa Segura

El componente `DatabaseManager` (`backend/core/database.py`) administra el ciclo de vida de los tres clientes oficiales durante el `lifespan` de FastAPI:

* **PostgreSQL 16 (`psycopg` v3 + `psycopg_pool`):** Pool de conexiones (`min_size=1`, `max_size=10`) utilizando exclusivamente el rol de menor privilegio `trazaagro_app` (solo permisos DML `SELECT`, `INSERT`, `UPDATE`, `DELETE`, sin DDL).
* **MongoDB 7 (`pymongo`):** Cliente `MongoClient` conectado a la base `trazaagro` con el usuario acotado `trazaagro_app` (`readWrite`, sin privilegios administrativos de clúster).
* **Neo4j 5 (`neo4j`):** Driver oficial sobre protocolo binario Bolt (`bolt://localhost:7687`).
* **Cero credenciales en código:** Toda URI y clave secreta se inyecta desde `.env` mediante `Settings` (`pydantic-settings` en `backend/core/config.py`), manteniendo `.env.example` libre de secretos de producción.

## 4. Validación de Entradas, Parametrización y Seguridad

1. **Contratos estrictos en Pydantic v2 (`backend/schemas/`):**
   * Todos los esquemas de entrada prohíben atributos extra (`extra="forbid"`).
   * Validación por expresiones regulares de identificadores puente (`^AGU-[A-Z0-9]+-\d{6}-\d{2}$` para lotes, `^LAB-\d{4}-[A-Z0-9-]+-V\d+$` para certificados).
   * Protección anti-NoSQLi en `DeterminacionSchema`: rechaza cualquier clave dinámica que inicie con `$` o contenga `.`.
   * Protección anti-XSS: validación de esquema de URLs en evidencias fotográficas (`https://`, `http://` o `/`) y sanitización de cadenas de texto libres antes de persistir.
2. **Consultas 100% parametrizadas:**
   * PostgreSQL utiliza placeholders `%s` en `postgres_repo.py`.
   * Neo4j utiliza parámetros `$codigo_lote`, `$folio_recepcion`, etc., en `neo4j_repo.py` con `MERGE` idempotente.
   * MongoDB utiliza diccionarios tipados y filtros `$elemMatch` sin evaluación de JavaScript en servidor.
3. **Autenticación, Autorización y Defensa Perimetral:**
   * **JWT `HS256` (`backend/core/security.py`):** Tokens firmados con clave >= 32 bytes (256 bits) incluyendo `sub`, `role` y `productor_id`.
   * **Control RBAC (`RN-04`) y BOLA/IDOR (`RN-11`):** Cada endpoint exige explícitamente los roles autorizados (`Productor`, `Recepcion`, `Laboratorio`, `QA`), y cuando el usuario es `Productor`, `LotesService` filtra y valida la propiedad por `productor_id`.
   * **Middlewares y Rate Limiting:** `SecurityHeadersMiddleware` inyecta `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Content-Security-Policy` y `Referrer-Policy`; `MaxBodySizeMiddleware` rechaza cuerpos mayores a 5 MB (`413`); y los limitadores de tasa protegen `/auth/login` y `/incidentes/recall` (`429`).

## 5. Manejo de Errores y Consistencia Multimotor

La jerarquía `TrazaAgroError` (`backend/core/exceptions.py`) traduce fallos de dominio en respuestas JSON uniformes (`{"error": "...", "mensaje": "..."}`) sin exponer trazas internas ni cadenas de conexión:

* `401 Unauthorized`: Credenciales incorrectas, token faltante, alterado o expirado.
* `403 Forbidden`: Rol sin privilegios (`RN-04`) o intento de acceso a lote de otro productor (`RN-11`).
* `404 Not Found`: Lote o folio de incidente inexistente.
* `409 Conflict`: Violación de reglas sanitarias o de inventario (`RN-01` lote no liberado, `RN-02` análisis no conforme, `RN-03` saldo insuficiente con `ROLLBACK`, `RN-09` cierre incompleto, `RN-10` productor o tienda inactivos).
* `422 Unprocessable Entity`: Error de esquema o intento de inyección en parámetros.
* `503 Service Unavailable`: Motor primario requerido no disponible antes de confirmar escritura.
* **Estrategia Outbox ante fallos parciales:** Cuando PostgreSQL confirma (`COMMIT`) y falla la proyección secundaria hacia Neo4j o MongoDB, el servicio inserta el evento en `eventos_reconciliacion` y responde con el campo estructurado `sincronizacion: { "<motor>": "pendiente_reconciliacion" }` para posterior recuperación idempotente mediante `POST /api/v1/admin/reconciliacion/ejecutar`.

## 6. Catálogo de Endpoints REST v1 (Contrato Oficial)

| # | Método | Ruta | Roles Permitidos | Reglas / Motores Coordinados |
| :-: | :--- | :--- | :--- | :--- |
| 1 | `GET` | `/api/v1/health` | Público | Verifica conectividad real con PG + Mongo + Neo4j (enmascarando detalles internos). |
| 2 | `POST` | `/api/v1/auth/login` | Público | Valida contraseña con `bcrypt` y emite JWT `HS256` con rol y `productor_id`. |
| 3 | `POST` | `/api/v1/lotes` | `Productor`, `QA` | `RN-10`, `RN-11`. Registra cosecha en PG y proyecta `(:Lote)-[:COSECHADO_EN]->(:Parcela)` en Neo4j. |
| 4 | `GET` | `/api/v1/lotes` | Todos | `RN-11`. Consulta inventario en PostgreSQL (aislado por `productor_id` si es `Productor`). |
| 5 | `GET` | `/api/v1/lotes/{codigo_lote}` | Todos | `RN-11`. **Expediente 360°**: consolida PG + MongoDB + Neo4j en una respuesta única. |
| 6 | `POST` | `/api/v1/recepciones` | `Recepcion`, `QA` | `RN-07`. Control térmico en PG, acta sensorial/fotos en MongoDB y grafo en Neo4j. |
| 7 | `POST` | `/api/v1/analisis` | `Laboratorio`, `QA` | `RN-05`. Crea certificado versionado inmutable (`V1`, `V2`) en MongoDB y proyecta en Neo4j. |
| 8 | `GET` | `/api/v1/analisis/{codigo_lote}` | `Laboratorio`, `QA` | Consulta historial de versiones e identifica parámetros fuera de norma con `$elemMatch`. |
| 9 | `PATCH` | `/api/v1/lotes/{codigo_lote}/liberar` | `QA` | `RN-02`, `RN-04`. Valida análisis conformes vigentes en MongoDB, actualiza PG y Neo4j. |
| 10 | `POST` | `/api/v1/envios` | `Recepcion`, `QA` | `RN-01`, `RN-03`, `RN-10`. Bloqueo pesimista `SELECT ... FOR UPDATE` en PG y proyección en Neo4j. |
| 11 | `POST` | `/api/v1/incidentes/recall` | `QA` | `RN-04`, `RN-08`. Rastrea tiendas y lotes hermanos en Neo4j, bloquea PG y abre expediente `INC-` en MongoDB. |
| 12 | `PATCH` | `/api/v1/incidentes/{folio}/cerrar` | `QA` | `RN-04`, `RN-09`. Cierra expediente en MongoDB validando causa raíz, acciones y firmas duales. |
| 13 | `GET` | `/api/v1/trazabilidad/{codigo}/adelante` | `QA` | Recorrido N-saltos en Neo4j hacia envíos, vehículos de reparto y tiendas afectadas. |
| 14 | `GET` | `/api/v1/trazabilidad/{codigo}/atras-lateral` | `QA` | Detección en Neo4j de origen (huerta) y contaminación cruzada en camión o cuarto frío. |
| 15 | `POST` | `/api/v1/admin/reconciliacion/ejecutar` | `QA` | Reprocesa eventos pendientes en `eventos_reconciliacion` hacia MongoDB y Neo4j. |

*(Nota: Las rutas de negocio son 14 endpoints sobre los 15 paths incluyendo `/health`, manteniendo inmutabilidad en `/api/v1/analisis` al no existir métodos `PUT` ni `DELETE` conforme a `RN-05`).*
