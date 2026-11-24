# Estado del Proyecto: TrazaAgro

Documento de seguimiento del avance, decisiones tomadas y próximos pasos para el proyecto integrador de bases de datos.

## Resumen Ejecutivo del Proyecto
* Nombre: TrazaAgro
* Dominio: Sistema de trazabilidad integral para distribución de alimentos frescos (caso de estudio: Aguacate Hass en México).
* Alcance acordado para el MVP (4 actores clave):
  1. Empacadora / Productor: Registro de cosecha y creación de lote con código único.
  2. Recepción y Almacén en CEDIS: Entrada de transporte con control de temperatura, división de inventario en envíos y despacho.
  3. Laboratorio Externo: Carga y versionado inmutable de análisis químicos y microbiológicos con esquemas heterogéneos y anidados.
  4. QA e Inocuidad / Gerencia: Liberación de producto, bloqueo atómico de emergencia ante contaminantes, rastreo de retiro (recall) hacia adelante y detección lateral de contaminación cruzada.
* Motores y responsabilidades:
  * PostgreSQL (Relacional): Fuente de verdad, control transaccional ACID de inventario y estados maestros (`Liberado`, `Bloqueado`).
  * MongoDB (Documental): Expedientes técnicos flexibles, actas de recepción y análisis de laboratorio con atributos anidados y versionado inmutable.
  * Neo4j (Grafos): Red viva de distribución física, rastreo en N saltos (tiendas afectadas) y análisis de contagio cruzado (vehículos o cuartos fríos compartidos).

## Estatus de Entregables Oficiales

### Entregable 1: Propuesta de aplicación
* Estatus: Concluido
* Ubicación: Subido a Google Drive en la carpeta `proyecto-final-daas`
* Enlace directo: https://docs.google.com/document/d/1dekS2TeQEjmvbppHQO2VGMF2j9jEkYkDQJzDBAKq3S8/edit
* Contenido cubierto: Nombre, descripción, problemática real, usuarios y necesidades, objetivo, alcance y exclusiones del MVP, justificación profunda de los 3 paradigmas (con respuesta a la prueba de eliminación) y catálogo conceptual de operaciones por modelo y flujo integrado.

### Entregable 2: Modelado de datos
* Estatus: Concluido
* Ubicación actual: `docs/02-modelado-datos.md` (con documentos de respaldo por motor en `docs/decisiones/`)
* Avance completado: Modelo conceptual común del dominio (10 entidades y relaciones), modelo lógico relacional para PostgreSQL (8 tablas con PK/FK, restricciones e índices), modelo documental para MongoDB (`analisis_laboratorio` y `actas_recepcion` con versionado inmutable y `$jsonSchema`), modelo lógico de grafos para Neo4j (8 etiquetas de nodo incluyendo `:Laboratorio`, relaciones diferenciadas `[:TRASLADADO_EN]` y `[:DESPACHADO_EN]`, restricciones e índices), diccionario de datos unificado con fuente de verdad y matriz de reglas de negocio (`RN-01` a `RN-11`).

### Entregable 3: Arquitectura y selección tecnológica
* Estatus: Concluido
* Ubicación local: `docs/03-arquitectura.md`
* Ubicación en Drive: Subido a la carpeta `proyecto-final-daas`
* Enlace directo: https://docs.google.com/document/d/1e-fzkRqbar6NgudHrJxgtqc5TiCMQCHjyHV96D2a6BI/edit
* Contenido cubierto: Diagrama de arquitectura de componentes modular en capas, responsabilidades estrictas por capa (Frontend SPA, Routers FastAPI + Pydantic, Servicios coordinadores, Repositorios con drivers oficiales), selección tecnológica y matrices de comparación justificadas (FastAPI, React + TypeScript + Vite, API REST con OpenAPI, drivers oficiales `psycopg` v3, `pymongo`, `neo4j`), contratos de API REST (14 endpoints con roles, reglas `RN-01` a `RN-11` y códigos HTTP), diagramas de secuencia de flujos integrados (Protocolo de Recall y Expediente 360°), matriz unificada de fuente de verdad y estrategia de consistencia eventual coordinada con `MERGE` idempotente y tabla técnica outbox `eventos_reconciliacion` ante fallos parciales.

### Entregable 4: Implementación de las tres bases
* Estatus: Concluido
* Ubicación local: `docs/04-implementacion-bases.md`
* Ubicación en Drive: Subido a la carpeta `proyecto-final-daas`
* Contenido cubierto: Scripts reproducibles DDL y validadores `$jsonSchema`, datos semilla y suite de validación de integridad para PostgreSQL, MongoDB y Neo4j en contenedores Docker Compose.

### Entregable 5: Catálogo de operaciones y consultas
* Estatus: Concluido
* Ubicación local: `docs/05-catalogo-consultas.md`
* Contenido cubierto: Catálogo completo de operaciones individuales por motor (PostgreSQL, MongoDB, Neo4j) y operaciones integradas multimotor (Protocolo de Recall y Expediente 360°), con parámetros, reglas del negocio (`RN-01` a `RN-11`), casos límite y evidencias de ejecución directa en Docker.
* Siguiente entregable inmediato: Entregable 8 (Pruebas finales, documentación y despliegue).

### Entregable 6: Backend y API
* Estatus: Concluido
* Ubicación local: `backend/` (routers en `controllers/`, servicios coordinadores en `services/`, repositorios con drivers directos en `repositories/` y esquemas Pydantic v2 en `schemas/`).
* Contenido cubierto: 14 endpoints REST `/api/v1/*` con autenticación JWT HS256, control RBAC por rol, aislamiento de productor (`RN-11`), validaciones anti-NoSQLi/XSS, principio de menor privilegio (`trazaagro_app`), reconciliación outbox y suite de 38 pruebas automatizadas aprobadas en `pytest` + validación en vivo contra Docker.

### Entregable 7: Aplicación e integración (Escritorio / Web)
* Estatus: Concluido
* Ubicación local: `frontend/` (React 18 + TypeScript + Vite + TanStack Query + Electron).
* Contenido cubierto: Aplicación de escritorio nativa con Electron (compatible también con navegador web), Login JWT con presets demo sin auto-registro público, `RoleGuard` RBAC, 5 vistas operativas (Productor, Recepción CEDIS, Laboratorio, QA Consola Recall y Gerencia Auditoría), visor interactivo del grafo Neo4j y modales transaccionales para todas las reglas `RN-01` a `RN-11`. Compilación `tsc -b && vite build` aprobada y validada en vivo contra contenedores Docker.

### Entregable 8: Pruebas, documentación y despliegue
* Estatus: Concluido
* Ubicación local: `docs/08-pruebas-despliegue.md`, `tests/benchmark_rendimiento.py`, `docs/pruebas/benchmark_resultados.json` y `README.md`.
* Contenido cubierto: Validación integral de los 7 ejes de la guía oficial, suite de 38 pruebas automatizadas aprobadas con `pytest` (unitarias, integración, outbox y E2E), prueba smoke en vivo contra Docker (`tests/smoke_frontend_api.py`), evaluación de rendimiento documentada en 2 niveles de volumen (Semilla Base vs. Carga Operativa Media de 500 lotes / 3,601 relaciones) con 3 corridas independientes cada uno, manual paso a paso de despliegue en Windows (Docker Compose, carga de semillas, backend FastAPI y app de escritorio con Electron) y actualización completa del `README.md`.

## Fuentes y Referencias de Contexto
* Guía oficial del proyecto: docs/guia-proyecto/guia-proyecto.md
* Entrevista con el experto QA: docs/CONTEXTO/requerimientos/entrevista_trazaagro.json
* Estructura metodológica y checklist: docs/CONTEXTO/requerimientos/trazaagro-precontexto.json
* Carpeta compartida en Drive: https://drive.google.com/drive/folders/1YHEOl7tMI-agwDdv8EoKiLasRkV8jCyj

## Regla de Mantenimiento de este Archivo
Este archivo sirve como bitácora de continuidad entre sesiones y chats. Solo se actualiza cuando el usuario lo solicite expresamente al completar o redefinir hitos del proyecto.
