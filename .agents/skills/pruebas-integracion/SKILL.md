---
name: pruebas-integracion
description: Estrategia, suite de pruebas y lineamientos de validación integral para TrazaAgro con pytest y httpx, cubriendo pruebas de conectividad, integridad por motor, integración multimotor, consistencia ante fallos parciales, errores negativos y evaluación de rendimiento según docs/guia-proyecto/guia-proyecto.md y docs/03-arquitectura.md.
---

# Guía de Estrategia de Pruebas e Integración: TrazaAgro

Esta skill define la arquitectura de pruebas, los tipos de validaciones requeridas y la suite de pruebas automatizadas con `pytest` y `httpx` para garantizar la calidad y el cumplimiento estricto de la Guía Oficial del Proyecto (`docs/guia-proyecto/guia-proyecto.md`, sección 9) y la arquitectura del sistema (`docs/03-arquitectura.md`).

## 1. Clasificación y Matriz Obligatoria de Pruebas

Conforme al estándar oficial del proyecto integrador, la suite de pruebas debe cubrir los siguientes siete ejes de validación:

### A. Pruebas de Conectividad
* **Propósito:** Verificar que el backend establece y mantiene conexiones activas hacia PostgreSQL, MongoDB y Neo4j utilizando credenciales seguras inyectadas por variables de entorno.
* **Alcance:** Endpoint `GET /api/v1/health` y métodos de inicialización del `db_manager`.
* **Criterio de éxito:** Respuesta HTTP `200 OK` con reporte de estado saludable (`healthy`) para los tres motores.

### B. Pruebas de Integridad por Motor
* **PostgreSQL (Relacional):**
  * Validación de restricciones de integridad referencial (claves foráneas entre lotes, productores, recepciones y envíos).
  * Validación de restricciones `CHECK` (por ejemplo, `saldo_kg >= 0`, `temperatura_llegada_c` válida, estados válidos).
  * Control de concurrencia y bloqueo pesimista (`SELECT ... FOR UPDATE`) al fraccionar lotes para evitar lecturas sucias o sobreventas (`RN-01`, `RN-03`).
* **MongoDB (Documental):**
  * Validación de documentos contra el esquema `$jsonSchema` en `analisis_laboratorio` y `actas_recepcion`.
  * Verificación de inmutabilidad analítica: confirmación de que no se permiten actualizaciones directas destructivas sobre análisis existentes (`RN-05`).
  * Consultas con `$elemMatch` sobre parámetros químicos y microbiológicos fuera de norma.
* **Neo4j (Grafos):**
  * Verificación de restricciones de unicidad (`codigo_lote`, `folio_recepcion`, `codigo_envio`, `placas`).
  * Integridad de relaciones y dirección (`[:COSECHADO_EN]`, `[:TRASLADADO_EN]`, `[:DIVIDIDO_EN]`).
  * Comprobación de que no existan nodos o aristas huérfanas tras registrar transacciones.

### C. Pruebas de Integración Multimotor (Flujos Completos)
* **Propósito:** Validar que una sola operación de la API coordina de forma coherente dos o tres motores de persistencia.
* **Flujos obligatorios:**
  1. **Alta de Cosecha:** Crea registro maestro en PostgreSQL y proyecta el nodo `(:Lote)` con arista `[:COSECHADO_EN]` en Neo4j.
  2. **Recepción en CEDIS (`RN-07`):** Registra pesaje y temperatura oficial en PostgreSQL, almacena acta física y fotos en MongoDB, y proyecta transporte/almacén en Neo4j.
  3. **Certificación y Liberación (`RN-02`, `RN-04`, `RN-05`):** Guarda certificado inmutable en MongoDB, proyecta `[:EMITIO_ANALISIS]` en Neo4j, valida conformidad y transiciona el lote a `Liberado` en PostgreSQL y Neo4j.
  4. **Despacho Fraccionado (`RN-01`, `RN-03`):** Descuenta `saldo_kg` con transacción ACID en PostgreSQL y proyecta nodos `(:Envio)` y relaciones de entrega en Neo4j.
  5. **Protocolo de Recall de Emergencia (`RN-08`):** Rastrea tiendas afectadas y lotes hermanos en Neo4j, bloquea atómicamente en PostgreSQL, crea el expediente `INC-...` en MongoDB y actualiza estados en Neo4j.
  6. **Expediente 360°:** Consolida datos de los tres motores en un único payload JSON coherente.

### D. Pruebas de Consistencia y Reconciliación ante Fallos Parciales
* **Propósito:** Comprobar que el sistema no oculta fallos secundarios ni genera datos contradictorios silenciosos.
* **Escenario de prueba:**
  1. Simular la caída controlada de Neo4j o MongoDB tras un `COMMIT` exitoso en PostgreSQL (mediante mocks o desconexión temporal).
  2. Verificar que la API no retorne éxito absoluto ficticio, sino un estado estructurado (`"sincronizacion": { "neo4j": "pendiente_reconciliacion" }`).
  3. Verificar que se inserte un registro pendiente en la tabla `eventos_reconciliacion` de PostgreSQL.
  4. Reactivar el motor secundario y ejecutar `ReconciliacionService.reprocesar_pendientes()` (o `POST /api/v1/admin/reconciliacion/ejecutar`).
  5. Confirmar que la proyección en Neo4j o MongoDB converge al estado esperado gracias a la idempotencia de las operaciones (`MERGE` y claves únicas).

### E. Pruebas Negativas y Manejo de Errores
* Intentar despachar un lote en estado `Bloqueado` -> esperar `409 Conflict` (`RN-01`).
* Intentar despachar más kilos de los disponibles en `saldo_kg` -> esperar `409 Conflict` (`RN-03`).
* Intentar liberar un lote con análisis no conformes vigentes -> esperar `409 Conflict` (`RN-02`).
* Usuario con rol `Recepcion` intentando ejecutar recall -> esperar `403 Forbidden` (`RN-04`).
* Productor intentando consultar un lote ajeno a su `productor_id` -> esperar `403 Forbidden` (`RN-11`).
* Enviar solicitudes con payloads incompletos o tipos incompatibles -> esperar `422 Unprocessable Entity`.
* Intentar autenticarse con credenciales inválidas -> esperar `401 Unauthorized`.

### F. Evaluación Básica de Rendimiento
* Mediciones de tiempo de respuesta (latencia media y percentil 95) en los flujos más complejos:
  * Expediente 360° consolidado (< 200 ms en entorno de pruebas).
  * Recorrido de Recall en Neo4j con búsqueda de lotes hermanos y tiendas (< 150 ms).
* Documentar las condiciones del entorno de prueba (versión de Docker, especificaciones del equipo y volumen de datos de prueba).

## 2. Organización del Directorio de Pruebas (`tests/`)

```text
tests/
├── conftest.py              # Fixtures compartidos: TestClient de FastAPI, tokens JWT por rol, mocks
├── unit/                    # Pruebas unitarias de componentes aislados
│   ├── test_schemas.py      # Validación estricta de Pydantic
│   ├── test_security.py     # Hashing bcrypt y generación/validación de JWT
│   └── test_domain_rules.py # Reglas de cálculo y rangos térmicos
├── integration/             # Pruebas de integración con bases de datos
│   ├── test_connectivity.py # Health check de los 3 motores
│   ├── test_postgres.py     # Transacciones, restricciones e inventario
│   ├── test_mongo.py        # Inmutabilidad, $jsonSchema y $elemMatch
│   ├── test_neo4j.py        # Grafo, unicidad y recorridos N-saltos
│   └── test_reconciliation.py # Simulación de fallos parciales y outbox
└── e2e/                     # Pruebas de extremo a extremo de flujos de negocio
    ├── test_flujo_cosecha_recepcion.py
    ├── test_flujo_analisis_liberacion.py
    ├── test_flujo_despacho_fraccionado.py
    └── test_flujo_recall_emergencia.py
```

## 3. Patrones de Implementación con Pytest y HTTPX

### Fixtures Clave en `conftest.py`
* `client`: Instancia de `TestClient(app)` o `httpx.AsyncClient` para invocar endpoints sin levantar el servidor uvicorn.
* `auth_headers_qa`: Token JWT pre-firmado con rol `QA`.
* `auth_headers_productor`: Token JWT con rol `Productor` y `productor_id=1`.
* `auth_headers_recepcion`: Token JWT con rol `Recepcion`.
* `auth_headers_laboratorio`: Token JWT con rol `Laboratorio`.

### Reglas de Ejecución y Aislamiento
* **Aislamiento de datos de prueba:** Las pruebas deben utilizar prefijos reconocibles (por ejemplo `TEST-AGU-...`, `TEST-ENV-...`) o una base de datos de pruebas configurada en un archivo `.env.test`.
* **Limpieza de estado:** Si una prueba inserta registros temporales, debe limpiarlos al finalizar o trabajar en transacciones que ejecuten `ROLLBACK` al término de cada test case para no corromper las semillas del Entregable 4.
* **Ejecución reproducible:** Toda la suite debe ejecutarse con un único comando:
  `pytest tests/ -v`
