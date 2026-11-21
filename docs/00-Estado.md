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
* Siguiente entregable inmediato: Entregable 4 (Implementación de las tres bases).

### Entregable 4: Implementación de las tres bases
* Estatus: Pendiente
* Objetivo: Scripts reproducibles de creación y carga de datos iniciales en PostgreSQL, MongoDB y Neo4j.

### Entregable 5: Catálogo de operaciones y consultas
* Estatus: Pendiente
* Objetivo: Pruebas y documentación de consultas funcionales individuales e integradas con casos límite.

### Entregable 6: Backend y API
* Estatus: Pendiente
* Objetivo: Implementación de controladores, servicios coordinadores y repositorios por motor.

### Entregable 7: Aplicación e integración (Frontend)
* Estatus: Pendiente
* Objetivo: Interfaz gráfica conectada al backend que demuestre el flujo completo del MVP.

### Entregable 8: Pruebas, documentación y despliegue
* Estatus: Pendiente
* Objetivo: Suite de pruebas de integración, docker-compose.yml y manual de despliegue.

## Fuentes y Referencias de Contexto
* Guía oficial del proyecto: docs/guia-proyecto/guia-proyecto.md
* Entrevista con el experto QA: docs/CONTEXTO/requerimientos/entrevista_trazaagro.json
* Estructura metodológica y checklist: docs/CONTEXTO/requerimientos/trazaagro-precontexto.json
* Carpeta compartida en Drive: https://drive.google.com/drive/folders/1YHEOl7tMI-agwDdv8EoKiLasRkV8jCyj

## Regla de Mantenimiento de este Archivo
Este archivo sirve como bitácora de continuidad entre sesiones y chats. Solo se actualiza cuando el usuario lo solicite expresamente al completar o redefinir hitos del proyecto.
