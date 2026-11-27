# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Cuatro roles operativos dentro de la cadena de suministro y distribución de aguacate Hass en México, en contexto de operación en escritorio (Electron / navegador web) y demostración académica del sistema:

1. **Empacadora / Productor:** Registra la cosecha y crea lotes con código único, consultando únicamente sus propios lotes (`RN-11`).
2. **Recepción y Almacén en CEDIS:** Registra la entrada de transporte con control de temperatura, divide inventario en envíos y gestiona el despacho hacia destinos.
3. **Laboratorio Externo:** Carga y versiona de forma inmutable análisis químicos y microbiológicos con esquemas heterogéneos y anidados.
4. **QA e Inocuidad / Gerencia:** Ejecuta la liberación de producto, dispara el bloqueo atómico de emergencia ante contaminantes, realiza el rastreo de retiro (*recall*) hacia adelante, detecta contaminación cruzada lateral y audita expedientes 360°.

## Product Purpose

**TrazaAgro** es un sistema de trazabilidad integral políglota para distribución de alimentos frescos (caso de estudio: aguacate Hass en México). Su objetivo es unificar el control transaccional de inventario y estados maestros, los expedientes técnicos documentales de laboratorio y recepción, y la red viva de distribución física en grafos para garantizar inocuidad alimentaria y respuesta rápida ante incidentes (*recall* y contaminación cruzada).

El éxito del producto significa que cualquier actor autorizado puede completar su flujo operativo sin ambigüedad y que QA/Gerencia puede reconstruir un expediente 360° o aislar lotes y destinos afectados en segundos.

## Positioning

A diferencia de un ERP o sistema de inventario monolítico tradicional, TrazaAgro coordina tres paradigmas de base de datos con responsabilidades estrictas y complementarias:
- **PostgreSQL (Relacional):** Fuente de verdad y control transaccional ACID para inventario y estados maestros (`Liberado`, `Bloqueado`).
- **MongoDB (Documental):** Expedientes técnicos flexibles, actas de recepción y análisis de laboratorio con versionado inmutable y validación `$jsonSchema`.
- **Neo4j (Grafos):** Red viva de distribución física para rastreo en N saltos (tiendas/destinos afectados) y análisis de contagio cruzado por vehículos o cuartos fríos compartidos, con consistencia eventual coordinada mediante `MERGE` idempotente y tabla outbox `eventos_reconciliacion`.

## Operating Context

- **Entorno principal:** Demo y evaluación académica del proyecto integrador, así como operación en escritorio mediante aplicación nativa Electron (`frontend/electron/main.cjs`) y compatibilidad total con navegador web (SPA React 18 + Vite).
- **Vistas y flujos clave:** Login JWT con presets demo (sin auto-registro público), `RoleGuard` RBAC, 5 vistas operativas (Productor, Recepción CEDIS, Laboratorio, QA Consola Recall y Gerencia Auditoría), visor interactivo del grafo Neo4j y modales transaccionales.
- **Idioma operativo:** 100% en español.

## Capabilities and Constraints

- **Reglas de negocio obligatorias (`RN-01` a `RN-11`):** Deben preservarse íntegramente en toda la interfaz y flujos transaccionales, incluyendo aislamiento de productor (`RN-11`) y bloqueo atómico de emergencia.
- **Seguridad y acceso:** Autenticación JWT HS256 con RBAC estricto por rol; prohibido el auto-registro público en la interfaz.
- **Compatibilidad dual:** La interfaz web en `frontend/` debe seguir funcionando tanto empaquetada en Electron como en navegador web estándar sin dependencias exclusivas de un solo entorno que rompan el otro.
- **Contratos API:** Comunicación con 14 endpoints REST `/api/v1/*` en FastAPI; no inventar endpoints ni alterar contratos de datos sin respaldo del backend.

## Brand Commitments

- **Nombre oficial:** TrazaAgro (`TrazaAgro · Trazabilidad Políglota de Aguacate Hass`).
- **Idioma y tono:** Todo el copy de interfaz, etiquetas, mensajes de error y documentación operativa debe permanecer en español claro y técnico-operativo.

## Evidence on Hand

- Documentación del proyecto en `docs/00-Estado.md`, `docs/02-modelado-datos.md`, `docs/03-arquitectura.md`, `docs/04-implementacion-bases.md`, `docs/05-catalogo-consultas.md` y `docs/08-pruebas-despliegue.md`.
- Backend funcional en `backend/` con 38 pruebas automatizadas aprobadas en `pytest` y benchmark de rendimiento en `docs/pruebas/benchmark_resultados.json`.
- Frontend implementado en `frontend/src/` (React 18, TypeScript, Vite, TanStack Query, React Router, Lucide icons, Electron).
- No existen testimonios de clientes reales ni métricas de producción comercial; no deben fabricarse.

## Product Principles

1. **Integridad operativa sobre adorno:** Cada pantalla y modal responde a un rol y a reglas de negocio verificables (`RN-01` a `RN-11`), priorizando precisión transaccional y claridad de estado (`Liberado`, `Bloqueado`).
2. **Trazabilidad visible:** La relación entre lote, expediente técnico y red de distribución física debe ser comprensible de un vistazo para auditoría y respuesta rápida ante *recall*.
3. **Aislamiento y mínimo privilegio en UI:** Cada rol ve y ejecuta únicamente lo que le corresponde; sin rutas expuestas ni acciones ambiguas.
4. **Legibilidad bajo presión operativa:** Jerarquía clara y alto contraste para lectura rápida en escenarios de almacén, laboratorio y consola de emergencia QA.

## Accessibility & Inclusion

- Cumplir con contraste y legibilidad **WCAG AA** como base en toda la interfaz, priorizando lectura rápida y sin ambigüedad de estados críticos (alertas de temperatura, bloqueos atómicos y resultados de laboratorio) en operación de almacén/QA y escritorio.
