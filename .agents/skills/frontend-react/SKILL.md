---
name: frontend-react
description: Guía de arquitectura, patrones y buenas prácticas para el desarrollo de la interfaz de usuario de TrazaAgro con React, TypeScript, Vite, Tailwind CSS y TanStack Query, basada en los contratos y roles de docs/03-arquitectura.md.
---

# Guía de Desarrollo Frontend: React + TypeScript en TrazaAgro

Esta skill establece las directrices de arquitectura, organización de componentes, consumo de API y experiencia de usuario para el frontend de TrazaAgro, conforme a lo establecido en la arquitectura del proyecto (`docs/03-arquitectura.md`).

## 1. Principios Fundamentales de la Capa de Presentación

* **Desacoplamiento total:** La aplicación web es una SPA pura (Single Page Application) creada con React 18+, TypeScript y Vite. Jamás se conecta directamente a PostgreSQL, MongoDB ni Neo4j, ni expone credenciales internas. Toda interacción se realiza a través de la API REST del backend (`/api/v1`).
* **Tipado estricto:** Todos los modelos de datos, solicitudes y respuestas de la API deben contar con interfaces o tipos de TypeScript equivalentes a los esquemas Pydantic del backend. Prohibido el uso de `any`.
* **Manejo de estado asíncrono con TanStack Query:** Las consultas y mutaciones deben gestionarse mediante TanStack Query v5 para asegurar caché eficiente, invalidación oportuna de estados tras mutaciones y feedback visual de carga/error.
* **Transparencia en sincronización:** Si la API devuelve un estado de sincronización parcial (`"sincronizacion": { "neo4j": "pendiente_reconciliacion" }`), la interfaz debe reflejarlo claramente mediante badges o alertas de advertencia, sin bloquear la experiencia del usuario.

## 2. Estructura de Carpetas Recomendada (`frontend/src/`)

```text
frontend/src/
├── api/             # Clientes HTTP (Axios / Fetch), interceptores JWT y funciones de API
│   ├── auth.ts
│   ├── lotes.ts
│   ├── recepciones.ts
│   ├── analisis.ts
│   ├── envios.ts
│   ├── trazabilidad.ts
│   └── incidentes.ts
├── assets/          # Íconos, imágenes y recursos estáticos
├── components/      # Componentes reutilizables
│   ├── common/      # Botones, modales, badges de estado, inputs, spinners
│   ├── forms/       # Formularios especializados con validación
│   ├── layout/      # Navbar, sidebar por rol, footer, contenedor principal
│   └── visualizer/  # Visor interactivo de grafos de trazabilidad (React Flow / Cytoscape)
├── context/         # AuthContext (almacenamiento de token JWT, datos del usuario y rol)
├── hooks/           # Hooks personalizados y queries de TanStack Query
├── pages/           # Vistas principales adaptadas a cada rol
│   ├── auth/        # Login
│   ├── productor/   # Registro de cosecha y mis lotes (RN-11)
│   ├── recepcion/   # Control térmico de entrada y actas sensoriales (RN-07)
│   ├── despachos/   # Despacho fraccionado a sucursales (RN-01, RN-03)
│   ├── laboratorio/ # Carga y versionado inmutable de certificados (RN-05)
│   ├── qa/          # Expediente 360°, liberación de lotes (RN-02) y Consola Recall (RN-08)
│   └── NotFound.tsx
├── types/           # Definiciones TypeScript de entidades y contratos REST
├── utils/           # Formateadores de fecha, kilos, temperaturas y helpers
├── App.tsx          # Enrutamiento principal (React Router v6+) y guardias de rol
└── main.tsx         # Punto de entrada y proveedores globales (QueryClient, AuthProvider)
```

## 3. Gestión de Autenticación, JWT y Rutas Protegidas

### Interceptor de API
* Configurar un cliente centralizado de HTTP que adjunte automáticamente el encabezado `Authorization: Bearer <token>` en cada solicitud protegida.
* Capturar errores `401 Unauthorized` para limpiar el estado de sesión y redirigir al usuario a `/login`.
* Decodificar el token JWT para almacenar en memoria el usuario actual, rol asignado (`Productor`, `Recepcion`, `Laboratorio`, `QA`) y `productor_id` si aplica.

### Rutas Protegidas por Rol (`RoleGuard`)
* Implementar un componente de orden superior o wrapper de ruta que verifique los permisos antes de renderizar la vista:
  * Si el rol no coincide con el permitido para esa sección (por ejemplo, un Productor intentando entrar a la Consola de Recall de QA), denegar el paso y mostrar un mensaje de acceso restringido (`403 Forbidden`).

## 4. Vistas y Casos de Uso por Rol

### A. Vista Productor / Empacadora
* **Formulario de Cosecha:** Captura de parcela de origen, fecha de corte y peso inicial en kilogramos (`POST /api/v1/lotes`).
* **Mis Lotes (`RN-11`):** Tabla con los lotes cosechados por el productor logueado. Debe filtrar y mostrar únicamente sus propios lotes, con su estado actual (`Cosechado`, `En_Recepcion`, `Liberado`, `Bloqueado`).

### B. Vista Recepción CEDIS y Almacén
* **Control de Entrada y Descarga (`RN-07`):**
  * Formulario de ingreso de camión con placas, chofer, pesaje verificado y termómetro digital.
  * Validación visual inmediata del rango térmico oficial (`4.0 °C` a `8.0 °C`). Si la lectura está fuera de rango, alertar antes del envío.
  * Carga de acta sensorial (apariencia, firmeza, maduración) y fotografías de evidencia hacia `POST /api/v1/recepciones`.
* **Despacho Fraccionado a Tiendas (`RN-01`, `RN-03`):**
  * Formulario con selección de tienda de destino, vehículo y asignación de kilogramos a descontar de uno o varios lotes en estado `Liberado`.
  * Cálculo dinámico del saldo restante en pantalla.
  * Manejo de error `409 Conflict` si el saldo disponible en PostgreSQL es insuficiente o el lote no está liberado.

### C. Vista Laboratorio Externo
* **Carga de Certificados Analíticos (`RN-05`):**
  * Formulario dinámico según tipo de estudio: Químico (plaguicidas, límites LMR, metales pesados) o Microbiológico (Salmonella, E. coli, Listeria).
  * Soporte para emisión inicial (`V1`) o emisión de enmiendas (`V2`, `V3`) con captura obligatoria del motivo de corrección.
  * Indicador automático de conformidad de cada parámetro frente a la norma.

### D. Vista QA e Inocuidad / Gerencia
* **Liberación de Lotes (`RN-02`, `RN-04`):**
  * Validación previa en UI: el botón de liberar solo se activa si existe al menos un análisis vigente conforme y ningún análisis vigente no conforme.
  * Ejecución de `PATCH /api/v1/lotes/{codigo_lote}/liberar`.
* **Expediente 360° Consolidado (`GET /api/v1/lotes/{codigo_lote}`):**
  * Ficha técnica del lote con saldo en kilogramos (PostgreSQL).
  * Visor de actas de recepción y certificados polimórficos de laboratorio con historial de versiones (MongoDB).
  * Grafo interactivo con la ruta física completa desde la huerta hasta los envíos a tiendas (Neo4j).
* **Consola de Retiro (Recall de Emergencia - `RN-08`):**
  * Panel de contingencia sanitaria para bloquear un lote contaminado.
  * Checkbox para activar rastreo y bloqueo simultáneo de lotes hermanos (por vehículo o cuarto frío compartido).
  * Visualización inmediata de tiendas y sucursales afectadas con total de kilos en riesgo para alertar al equipo de retiro.
  * Apertura automática de expediente de incidente y formulario de seguimiento para cierre con causa raíz y firmas (`RN-09`).

## 5. Visualización Interactiva del Grafo (React Flow / Cytoscape)

* Renderizar la red de distribución física devuelta por los endpoints de trazabilidad (`GET /api/v1/trazabilidad/{codigo_lote}/adelante` y `GET /api/v1/trazabilidad/{codigo_lote}/atras-lateral`).
* Diferenciar nodos por tipo mediante íconos y colores:
  * `:Productor` y `:Parcela` (Verde olivo)
  * `:Lote` (Verde esmeralda cuando está Liberado; Rojo carmesí cuando está Bloqueado)
  * `:Vehiculo` y `:CuartoFrio` (Azul neutro)
  * `:Laboratorio` (Púrpura)
  * `:Envio` y `:Tienda` (Naranja / Ámbar)
* Permitir hacer zoom, pan y clic en un nodo para desplegar su ficha de detalles en un panel lateral.

## 6. Manejo de Errores y Experiencia de Usuario (UX)

* **Errores de Conflicto (`409 Conflict`):** Mostrar mensajes contextuales claros cuando un lote esté bloqueado o el saldo de kilos sea insuficiente, evitando mensajes genéricos.
* **Errores de Validación (`422 Unprocessable Entity`):** Marcar en rojo los campos específicos del formulario señalados por Pydantic en `detail`.
* **Caídas de Servicio Parciales (`503 Service Unavailable`):** Indicar con amabilidad si alguno de los motores no está respondiendo y permitir reintentar la acción.
* **Badges de Sincronización:**
  * Verde: Todo sincronizado en PostgreSQL, MongoDB y Neo4j.
  * Amarillo: Guardado en base principal pero con proyección pendiente de reconciliación en motor secundario.
