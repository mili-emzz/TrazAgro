---
name: ciberseguridad-api
description: Directrices, patrones y medidas de ciberseguridad aplicables a la API REST de TrazaAgro (FastAPI), incluyendo autenticación JWT, RBAC estricto, prevención de inyecciones políglotas (SQL, NoSQL, Cypher), validación Pydantic, mitigación BOLA/IDOR, rate limiting y cabeceras seguras.
---

# Guía de Ciberseguridad para la API de TrazaAgro

Esta skill define los estándares y directrices de seguridad indispensables para proteger la API REST de TrazaAgro (FastAPI) y sus tres motores de datos (PostgreSQL, MongoDB y Neo4j). Su objetivo es prevenir vulnerabilidades críticas como inyecciones políglotas, accesos no autorizados (BOLA/IDOR), fuga de información sensible y denegación de servicio.

## 1. Autenticación y Gestión Segura de Credenciales

### Hash Seguro de Contraseñas
* Utilizar `bcrypt` con un factor de costo mínimo de 12 rondas.
* Nunca almacenar ni comparar contraseñas en texto claro.
* Emplear funciones de comparación en tiempo constante (`bcrypt.checkpw`) para evitar ataques de temporización (timing attacks).

### Tokens de Acceso JWT
* Algoritmo forzado: Utilizar exclusivamente `HS256` (o `RS256` con par de llaves asimétricas). Prohibir explícitamente algoritmos nulos (`alg: "none"`).
* Secreto criptográfico: `JWT_SECRET_KEY` debe generarse mediante generadores criptográficamente seguros (`secrets.token_urlsafe(32)`) con un mínimo de 256 bits de entropía. Prohibir valores por defecto en producción.
* Claims obligatorios del token:
  * `sub`: Identificador único del usuario (UUID o entero).
  * `role`: Rol del usuario en el sistema (`Productor`, `Recepcion`, `Laboratorio`, `QA`).
  * `productor_id`: ID del productor asignado (obligatorio si el rol es `Productor`, nulo para otros roles).
  * `exp`: Expiración finita y estricta (máximo 8 horas para turnos operativos, configurable en variables de entorno).
  * `iat`: Timestamp de emisión.
  * `jti`: Identificador único de token para control de revocación si fuera necesario.

## 2. Autorización RBAC y Prevención de BOLA / IDOR

### Control de Acceso por Rol (RBAC)
Cada endpoint debe aplicar dependencias de seguridad de FastAPI que validen el rol antes de transferir el control a la capa de servicios:
* **Solo QA / Gerencia (`RN-04`):**
  * `PATCH /api/v1/lotes/{codigo_lote}/liberar`
  * `POST /api/v1/incidentes/recall`
  * `PATCH /api/v1/incidentes/{folio}/cerrar`
  * `POST /api/v1/admin/reconciliacion/ejecutar`
* **Solo Recepción CEDIS:**
  * `POST /api/v1/recepciones`
  * `POST /api/v1/envios`
* **Solo Laboratorio Externo y QA:**
  * `POST /api/v1/analisis`
* **Solo Empacadora / Productor y QA:**
  * `POST /api/v1/lotes`

### Prevención de BOLA / IDOR (`RN-11`)
* Los productores solo pueden consultar lotes y expedientes que les pertenezcan legítimamente.
* En `GET /api/v1/lotes/{codigo_lote}` y `GET /api/v1/analisis/{codigo_lote}`:
  1. Extraer el `productor_id` verificado desde el JWT.
  2. Si el rol es `Productor`, validar contra la base de datos relacional que el lote pertenezca a ese `productor_id`.
  3. Si no coincide, responder `403 Forbidden` (o `404 Not Found` para evitar enumeración de recursos).
  4. Jamás confiar en parámetros de consulta o encabezados enviados por el cliente para filtrar por propietario.

## 3. Blindaje contra Inyecciones Políglotas

TrazaAgro coordina tres motores de persistencia con paradigmas distintos, por lo que cada uno requiere una barrera anti-inyección específica:

### PostgreSQL (SQL Injection)
* Queda terminantemente prohibido el uso de f-strings, concatenación (`+`) o formato de cadenas (`%`) para construir sentencias SQL.
* Utilizar siempre consultas 100% parametrizadas mediante el driver oficial `psycopg` (v3):
  `cursor.execute("SELECT * FROM lotes WHERE codigo_lote = %s", (codigo_lote,))`
* Principio de mínimo privilegio: El usuario de la base de datos de la API debe poseer permisos únicamente sobre las tablas de TrazaAgro, sin privilegios de superusuario ni permisos DDL en tiempo de ejecución.

### MongoDB (NoSQL / BSON Injection)
* Evitar que entradas del usuario se interpreten como objetos con operadores de MongoDB (`$gt`, `$ne`, `$where`, `$regex`).
* Toda entrada debe pasar previamente por un esquema Pydantic que fuerce tipos primitivos estrictos (`str`, `float`, `int`).
* No utilizar el operador `$where` con cadenas de JavaScript en ninguna consulta de la aplicación.
* Para búsquedas de texto, usar expresiones regulares compiladas con escapes seguros o coincidencias exactas por valor.

### Neo4j (Cypher Injection)
* Prohibido concatenar parámetros del usuario dentro de sentencias Cypher.
* Todas las consultas Cypher deben ejecutarse pasando parámetros como diccionario:
  `session.run("MATCH (l:Lote {codigo_lote: $codigo}) RETURN l", {"codigo": codigo_lote})`
* Limitar siempre la profundidad de los recorridos de grafos para evitar ataques DoS por agotamiento de memoria o ciclos infinitos:
  Usar `[:DIVIDIDO_EN*1..5]` en lugar de recorridos sin límite `[:DIVIDIDO_EN*]`.

## 4. Validación Estricta de Entradas y Esquemas Pydantic

* Configuración restrictiva en Pydantic v2: En esquemas de mutación (`POST`, `PATCH`), configurar `model_config = ConfigDict(extra="forbid")` para evitar Parameter Tampering o asignación masiva de campos no esperados.
* Expresiones regulares de validación para códigos de negocio:
  * Código de lote: `^AGU-[A-Z0-9]+-\d{6}-\d{2}$`
  * Folio de recepción: `^REC-\d{4}-\d{4}$`
  * Folio de análisis: `^LAB-\d{4}-AGU-\d{4}-V\d+$`
  * Folio de incidente: `^INC-\d{4}-\d{4}$`
* Validación de rangos físicos:
  * Temperaturas de recepción: validar rangos reales (`ge=-5.0`, `le=40.0`).
  * Kilos despachados o cosechados: validar cantidades positivas no absurdas (`gt=0`, `le=100000`).
* Sanitización contra XSS en campos de texto libre:
  * Campos como observaciones sensoriales, motivos de rechazo o notas de recall deben limpiarse de caracteres de inyección HTML/Script antes de almacenarse o reflejarse.

## 5. Seguridad en Redes, Cabeceras HTTP y CORS

### Configuración de CORS
* Especificar explícitamente los orígenes permitidos mediante la variable `CORS_ORIGINS`.
* Prohibir el uso de `allow_origins=["*"]` cuando `allow_credentials=True`.
* Restringir métodos y encabezados a los estrictamente utilizados por la SPA.

### Cabeceras de Seguridad Obligatorias
Implementar un middleware en FastAPI que inyecte en todas las respuestas:
* `X-Content-Type-Options: nosniff` (previene interpretación errónea de tipos MIME).
* `X-Frame-Options: DENY` (mitiga ataques de clickjacking).
* `Strict-Transport-Security: max-age=31536000; includeSubDomains` (obliga al uso de HTTPS en producción).
* `Content-Security-Policy: default-src 'self'` (restringe fuentes de scripts y estilos).
* `Referrer-Policy: strict-origin-when-cross-origin`.

## 6. Limitación de Tasa (Rate Limiting) y Protección contra DoS

* **Endpoint `/api/v1/auth/login`:**
  * Límite estricto de intentos (e.g. 5 intentos por minuto por IP/usuario) para frenar ataques de fuerza bruta contra credenciales.
  * Respuestas genéricas ante credenciales inválidas ("Credenciales incorrectas") para no revelar si el usuario existe o no.
* **Operaciones críticas multimotor (`POST /api/v1/incidentes/recall`):**
  * Limitar tasa de ejecución para prevenir sobrecarga coordinada entre PostgreSQL, MongoDB y Neo4j.
* **Tamaño máximo de solicitudes:**
  * Configurar límite de tamaño en el body (e.g. 5 MB) para evitar desbordamiento de memoria ante envíos de imágenes o documentos en actas de recepción.

## 7. Manejo Seguro de Excepciones y Fuga de Información

* Desactivar el modo de depuración (`DEBUG = False`) en cualquier entorno que no sea desarrollo local.
* Manejador global de excepciones:
  * Capturar excepciones no controladas a nivel de aplicación.
  * Registrar el stack trace detallado únicamente en los logs internos del servidor (con nivel `ERROR`).
  * Responder al cliente con un formato estructurado y seguro, sin exponer nombres de tablas, columnas, consultas SQL/Cypher, cadenas de conexión ni versiones de software:
    ```json
    {
      "error": "INTERNAL_SERVER_ERROR",
      "mensaje": "Ocurrió un error interno al procesar la solicitud. Contacte al administrador.",
      "codigo_referencia": "a8f3b2c1"
    }
    ```
* El endpoint de salud (`GET /api/v1/health`) solo debe informar si los servicios están `operativos` o `degradados`, sin exponer credenciales, IPs internas ni versiones de motores a clientes no autenticados.

## 8. Inmutabilidad y Auditoría de Operaciones Críticas

* Cumplimiento de `RN-05`: Los análisis de laboratorio en MongoDB son inmutables. Queda prohibido implementar endpoints `DELETE` o `PUT` que sobreescriban resultados analíticos. Las correcciones solo proceden como nuevas versiones enmendadas (`V+1`) con registro de motivo.
* Auditoría de bloqueos y retiros (`RN-08`, `RN-09`):
  * Toda ejecución de recall debe registrar atómicamente el `usuario_id`, IP de origen, timestamp y motivo tanto en la tabla `incidentes_bitacora` de PostgreSQL como en `expedientes_incidentes` de MongoDB.
* La bitácora técnica de reconciliación (`eventos_reconciliacion`) debe auditar cualquier discrepancia o fallo secundario sin exponer datos confidenciales en texto plano.
