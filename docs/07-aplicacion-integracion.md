# Entregable 7: Aplicación e Integración (TrazaAgro)

Este documento describe la interfaz gráfica unificada de **TrazaAgro** y la forma en que integra los flujos de **PostgreSQL 16**, **MongoDB 7** y **Neo4j 5** a través de la API REST del backend, dando cumplimiento a la sección 7.7 de la guía oficial (`docs/Guia_Proyecto_Final_Bases_Datos.pdf`).

## 1. Arquitectura de la Aplicación Cliente (Escritorio Electron + Web)

La interfaz de usuario está construida como una aplicación **React 18 + TypeScript + Vite + TanStack Query v5** empaquetada también como aplicación nativa de escritorio mediante **Electron** (`frontend/electron/main.cjs` y `preload.cjs`).

* **Desacoplamiento absoluto de las bases de datos:** El cliente no contiene drivers de PostgreSQL, MongoDB ni Neo4j, ni conoce credenciales de red. Toda operación viaja exclusivamente por HTTP hacia `http://127.0.0.1:8000/api/v1` mediante `frontend/src/api/client.ts` adjuntando el token JWT `Bearer`.
* **Enrutamiento y Seguridad en Escritorio:** Utiliza `HashRouter` (`frontend/src/App.tsx`) para compatibilidad dual entre navegador web y protocolo `file://` de Electron, con aislamiento de contexto habilitado (`contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`).
* **Sincronización y Caché Reactiva:** Los hooks de TanStack Query invalidan automáticamente las consultas afectadas tras cada mutación (`crearLote`, `registrarRecepcion`, `emitirAnalisis`, `liberarLote`, `crearEnvio`, `ejecutarRecall`, `cerrarIncidente`), asegurando que la vista refleje de inmediato el estado consolidado del backend.

## 2. Interfaz Funcional por Actor y Control RBAC

La aplicación inicia en una pantalla de autenticación cerrada (`LoginPage.tsx`) conectada a `POST /api/v1/auth/login` (sin auto-registro público para proteger la integridad de los privilegios sanitarios), e incluye tarjetas de acceso rápido demo para los 4 roles oficiales del dominio. El componente `RoleGuard` (`frontend/src/components/layout/RoleGuard.tsx`) protege las 5 vistas operativas:

| Ruta | Vista | Roles Autorizados | Operaciones Principales |
| :--- | :--- | :--- | :--- |
| `/productor` | `ProductorPage.tsx` | `Productor`, `QA` | Alta de lotes cosechados y consulta aislada a las huertas del productor autenticado (`RN-11`). |
| `/cedis` | `RecepcionCedisPage.tsx` | `Recepcion`, `QA` | Registro de entrada física con control térmico (`RN-07`), captura de acta sensorial y despacho fraccionado a tiendas (`RN-01`, `RN-03`). |
| `/laboratorio` | `LaboratorioPage.tsx` | `Laboratorio`, `QA` | Emisión de certificados multirresiduos/microbiológicos y carga de enmiendas versionadas inmutables (`V1`, `V2`, `RN-05`). |
| `/qa/recall` | `QaRecallPage.tsx` | `QA` | Liberación sanitaria (`RN-02`), visor interactivo de red de distribución, ejecución del protocolo de Recall (`RN-08`) y cierre formal de incidentes (`RN-09`). |
| `/qa/gerencia` | `GerenciaPage.tsx` | `QA` | Tablero ejecutivo de inventario global, auditoría de incidentes y ejecución manual de reconciliación outbox (`/api/v1/admin/reconciliacion/ejecutar`). |

## 3. Participación Demostrable de los Tres Motores en la Aplicación

Cada paradigma de base de datos tiene una participación visible y diferenciada dentro de la misma interfaz:

1. **Participación de PostgreSQL 16 (Relacional / ACID):**
   * Alimenta las tablas de inventario de `ProductorPage`, `RecepcionCedisPage` y `GerenciaPage` con el `saldo_kg` exacto y el estado maestro (`Cosechado`, `Recibido`, `En revision`, `Liberado`, `Bloqueado`, `Retirado`).
   * En el modal de **Despacho Fraccionado** (`RecepcionCedisPage`), solo habilita lotes `Liberado` con saldo positivo (`RN-01`) y valida el descuento atómico evitando sobreventas (`RN-03`).
2. **Participación de MongoDB 7 (Documental / Inmutable):**
   * En `RecepcionCedisPage`, el formulario de recepción captura la evaluación sensorial anidada, el arreglo de monitoreo térmico por zona de caja y las evidencias fotográficas almacenadas en `actas_recepcion`.
   * En `LaboratorioPage`, el historial muestra todas las versiones inmutables (`V1`, `V2`) de `analisis_laboratorio`, destacando el certificado vigente (`es_vigente: true`), las moléculas fuera de norma detectadas y el motivo técnico de enmienda (`RN-05`).
3. **Participación de Neo4j 5 (Grafos / Trazabilidad):**
   * En `QaRecallPage`, el componente `TraceGraphVisualizer.tsx` renderiza de forma visual e interactiva la topología recuperada desde Neo4j: el nodo `:Lote` origen, su `:Parcela`, el `:Vehiculo` y `:CuartoFrio` de ingreso, los lotes hermanos en riesgo de contaminación cruzada (`/atras-lateral`) y la cadena `(:Lote)-[:DIVIDIDO_EN]->(:Envio)-[:ENTREGADO_A]->(:Tienda)` (`/adelante`).

## 4. Flujo Integrado Multimotor Demostrado (Protocolo de Recall y Expediente 360°)

La solución demuestra la coordinación real entre las tres bases de datos en dos flujos centrales operados desde la misma aplicación:

1. **Consulta de Expediente 360° (`GET /api/v1/lotes/{codigo_lote}`):**
   * Al seleccionar cualquier lote en la consola QA, la interfaz dispara una sola consulta al backend. El servicio coordinador obtiene los datos maestros y saldo contable desde **PostgreSQL**, adjunta el acta de recepción y el historial de certificados desde **MongoDB**, y suma el mapa de envíos, tiendas y lotes hermanos desde **Neo4j**, presentándolo en un único panel unificado.
2. **Protocolo de Recall de Emergencia (`POST /api/v1/incidentes/recall`, `RN-08`):**
   * Al detonar una alerta sanitaria desde `QaRecallPage`, **Neo4j** identifica las tiendas destino y lotes hermanos contaminados; **PostgreSQL** bloquea atómicamente el inventario del lote y registra la bitácora legal; y **MongoDB** genera el expediente vivo `INC-...` con su línea de tiempo para seguimiento y posterior cierre con firmas duales (`RN-09`).

## 5. Evidencia de Consistencia en la Interfaz

* **Transacciones rechazadas con retroalimentación clara:** Si un operador intenta despachar un lote bloqueado (`RN-01`), liberar un lote con análisis `No Conforme` (`RN-02`) o exceder el saldo (`RN-03`), la UI captura el error `409 Conflict` devuelto por el backend y muestra la alerta exacta sin alterar el estado local.
* **Visibilidad de consistencia eventual (Outbox):** Cuando ocurre un fallo parcial en un motor secundario tras confirmar en PostgreSQL, la respuesta del backend incluye el campo `sincronizacion` con el estado `pendiente_reconciliacion`, y el tablero `GerenciaPage` permite ejecutar `POST /api/v1/admin/reconciliacion/ejecutar` para converger los tres motores en vivo.
