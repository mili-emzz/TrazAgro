# Registro de Decisiones Técnicas (ADR / Architecture Decision Record)

Este documento recopila las decisiones de arquitectura, modelado y stack tecnológico tomadas para el desarrollo de **TrazaAgro**, detallando el contexto del problema, las alternativas analizadas, la decisión final tomada, los prompts o directrices clave que la detonaron y su impacto práctico en el proyecto.

## 1. Alcance y Caso de Estudio del MVP

### Contexto
El sistema debía resolver la trazabilidad integral de productos agrícolas de alto valor y riesgo fitosanitario/químico en México, evitando dispersión en múltiples cadenas de suministro complejas.

### Opciones consideradas
* **Opción A:** Sistema genérico multiproducto para cualquier tipo de alimento perecedero.
* **Opción B:** Cadena completa especializada en Aguacate Hass de exportación y distribución nacional, centrada en 4 actores clave.

### Decisión tomada
Se adoptó la **Opción B**: Cadena de Aguacate Hass en México cubriendo 4 actores esenciales:
1. Empacadora / Productor (cosecha y registro de lote).
2. Recepción y Almacén CEDIS (control térmico, ingreso y despacho de inventario).
3. Laboratorio Externo (análisis de plaguicidas y microbiología con esquemas dinámicos).
4. QA e Inocuidad / Gerencia (liberación, bloqueo atómico de emergencia y recall 360° en red de distribución).

### Directriz / Prompt detonante
"Enfocar el MVP en un producto insignia mexicano donde la trazabilidad, inocuidad y control de residuos químicos sea crítico para auditorías y emergencias sanitarias reales."

### Impacto
* Permitió acotar las reglas de negocio (`RN-01` a `RN-11`) a situaciones operativas tangibles: control de temperatura en recepción (-0.5°C a 12°C), límites máximos de residuos (LMR), inmutabilidad de certificados y bloqueo preventivo.

## 2. Persistencia Políglota y Matriz de Fuente de Verdad

### Contexto
Un sistema de trazabilidad alimentaria combina necesidades contradictorias: transacciones financieras/inventario estrictas (ACID), documentos técnicos heterogéneos y mutables en estructura, y consultas topológicas recursivas de impacto en red de transporte.

### Opciones consideradas
* **Opción A:** Monolito en PostgreSQL usando columnas JSONB y extensiones recursivas (CTE).
* **Opción B:** Arquitectura políglota distribuida con microservicios por motor.
* **Opción C:** Monolito modular con persistencia políglota de tres bases coordinadas por un backend central:
  * PostgreSQL (Relacional)
  * MongoDB (Documental)
  * Neo4j (Grafos)

### Decisión tomada
Se eligió la **Opción C**. Cada motor tiene una responsabilidad única y no negociable:
* **PostgreSQL:** Fuente de verdad transaccional ACID de entidades maestras, lotes, estados del ciclo de vida (`Registrado`, `En_Transito`, `En_Recepcion`, `Liberado`, `Bloqueado`), inventario disponible y despachos.
* **MongoDB:** Fuente de verdad para expedientes técnicos flexibles e inmutables: actas de recepción con firmas/evidencias fotográficas y análisis de laboratorio con atributos anidados y versionado inmutable (`v1`, `v2`, etc.).
* **Neo4j:** Fuente de verdad para la topología física de la red logística: recorridos en N saltos (lote → flete → CEDIS → flete → tiendas), detección de lotes hermanos en cuartos fríos y cálculo instantáneo de recall.

### Directriz / Prompt detonante
"Demostrar con rigor la necesidad real de los 3 paradigmas superando la 'prueba de eliminación' (qué se rompe si quitas cualquiera de las tres bases)."

### Impacto
* Cero duplicidad descontrolada: el `id_lote` actúa como identificador universal de correlación.
* PostgreSQL mantiene la integridad referencial y de inventario sin depender de locks en MongoDB o Neo4j.
* Neo4j responde a consultas recursivas de recall en milisegundos sin someter a PostgreSQL a `JOIN` recursivos pesados.

## 3. Modelo de Consistencia y Coordinación Multi-Base

### Contexto
Al escribir en tres bases de datos independientes dentro de un mismo flujo de negocio (por ejemplo, registrar un despacho o aplicar un bloqueo de recall), existe riesgo de caídas parciales que provoquen inconsistencias entre motores.

### Opciones consideradas
* **Opción A:** Transacciones distribuidas con 2-Phase Commit (2PC) / XA.
* **Opción B:** Consistencia eventual basada en Apache Kafka / RabbitMQ.
* **Opción C:** Consistencia eventual coordinada en el backend con orden estricto de escritura, operaciones idempotentes (`MERGE` en Neo4j, `upsert` en Mongo) y tabla de compensación outbox (`eventos_reconciliacion`) en PostgreSQL.

### Decisión tomada
Se adoptó la **Opción C**.
* PostgreSQL siempre es la primera base en escribir; si la transacción relacional falla, la operación aborta de inmediato con rollback limpio.
* Las proyecciones a Neo4j y MongoDB se ejecutan como pasos posteriores mediante operaciones idempotentes.
* Si el motor secundario no responde, el evento se registra en la tabla `eventos_reconciliacion` dentro de PostgreSQL para reintento asíncrono, garantizando que el usuario recibe una respuesta predecible sin estados corruptos.

### Directriz / Prompt detonante
"Evitar la sobreingeniería de brokers de mensajería para el MVP, pero garantizar formalmente que ante caídas parciales no existan inconsistencias silenciosas."

### Impacto
* Arquitectura resiliente sin dependencias de infraestructura pesadas.
* Trazabilidad total de fallos de sincronización y garantía de no duplicar nodos o relaciones en el grafo gracias a sentencias `MERGE` con llaves unívocas.

## 4. Stack Tecnológico del Backend

### Contexto
El backend debe coordinar tres clientes de base de datos simultáneos, validar contratos estrictos de entrada/salida y ofrecer alto rendimiento en operaciones asíncronas de I/O.

### Opciones consideradas
* **Opción A:** Node.js con Express / NestJS y TypeORM.
* **Opción B:** Python con Django y Django REST Framework.
* **Opción C:** Python con FastAPI, Pydantic v2 y drivers nativos oficiales (`psycopg` v3, `pymongo`, `neo4j-driver`).

### Decisión tomada
Se eligió la **Opción C**:
* **FastAPI:** Framework nativo ASGI moderno, de alto rendimiento asíncrono y generación automática de OpenAPI 3.1.
* **Pydantic v2:** Validación estricta y tipada en tiempo de ejecución de esquemas de entrada y salida para los 14 endpoints.
* **Drivers oficiales directos:** Sin ORMs pesados genéricos que limiten la expresividad de Cypher (Neo4j), pipelines de agregación (MongoDB) o queries transaccionales con `SELECT ... FOR UPDATE` (PostgreSQL).

### Directriz / Prompt detonante
"Elegir un stack robusto, ágil de programar y con soporte nativo de primera clase para los tres motores de bases de datos."

### Impacto
* Claridad total en las consultas ejecutadas: control milimétrico sobre el SQL parametrizado, el BSON de Mongo y el Cypher de Neo4j.
* Documentación Swagger interactiva lista para consumo del frontend desde el día uno.

## 5. Estructura y Flujo de Arquitectura del Backend

### Contexto
Se requería una organización limpia de carpetas que evitara mezclar lógica HTTP, reglas de negocio y consultas de bases de datos.

### Opciones consideradas
* **Opción A:** Estructura clásica por modelo o dominio disperso.
* **Opción B:** Arquitectura en capas limpia y desacoplada con separación explícita de repositorios por tecnología.

### Decisión tomada
Se acordó la estructura reflejada en `docs/desiciones/arquitectura-carpetas-back-front.md`:

```text
backend/
├── controllers/            # Routers FastAPI: endpoints HTTP, JWT/RBAC, validación I/O
├── schemas/                # Modelos Pydantic (contratos de API)
├── services/               # Lógica de negocio (RN-01 a RN-11) y orquestación multi-base
├── repositories/
│   ├── relational/         # Consultas PostgreSQL con psycopg v3
│   ├── document/           # Consultas MongoDB con PyMongo
│   └── graph/              # Consultas Neo4j con driver Bolt
├── core/                   # Variables de entorno, conexiones y pools
└── main.py                 # Punto de entrada y configuración de la app
```

Flujo unificado:
`Controller (Router)` → `Service (Orquestador)` → `Repository (Motor específico)` → `Base de Datos`

### Directriz / Prompt detonante
"Definir una arquitectura de backend donde cada capa tenga una responsabilidad única y la coordinación entre motores viva exclusivamente en la capa de servicios."

### Impacto
* Si cambia una consulta de Neo4j o MongoDB, no se tocan los controladores ni las rutas HTTP.
* Facilidad absoluta para mockear repositorios en pruebas unitarias y de integración.

## 6. Stack Tecnológico del Frontend

### Contexto
La interfaz debe servir como herramienta de trabajo interno para cuatro roles operativos y de supervisión, con paneles de captura rápida, visualización de fichas técnicas y representación gráfica interactiva de redes de distribución.

### Opciones consideradas
* **Opción A:** Renderizado del lado del servidor (SSR) con Next.js.
* **Opción B:** SPA ligera y rápida con React + Vite + TypeScript.

### Decisión tomada
Se adoptó la **Opción B**: **React + Vite (SPA)** con el siguiente conjunto de librerías especializadas (una por necesidad):
* **React Router:** Enrutamiento y control de navegación protegida según el rol del usuario autenticado.
* **TanStack Query (React Query):** Manejo de caché, reintentos, estados de carga y sincronización con la API REST.
* **React Hook Form + Zod:** Gestión y validación declarativa de formularios complejos (actas de recepción, parámetros de laboratorio y despachos).
* **React Flow / react-force-graph:** Renderizado visual interactivo del grafo de trazabilidad y nodos afectados durante una alerta de recall.
* **Tailwind CSS:** Diseño de interfaz utilitario, consistente y responsivo sin sobrecarga de dependencias pesadas.

### Directriz / Prompt detonante
"Elegir un frontend ligero y rápido de arrancar para paneles internos de trabajo por rol, sin necesidad de SEO ni complejidad innecesaria de SSR."

### Impacto
* Tiempos de compilación casi instantáneos durante el desarrollo con Vite.
* Validación idéntica en frontend (Zod) y backend (Pydantic), reduciendo errores de integración.
* Visualización gráfica intuitiva para los auditores de QA durante auditorías o crisis sanitarias.

## 7. Estructura y Flujo de Arquitectura del Frontend

### Contexto
Mantener simetría conceptual entre cómo fluyen los datos en el frontend y cómo se procesan en el backend.

### Decisión tomada
Se acordó una estructura modular en capas que refleja el flujo descendente del backend:

```text
frontend/
├── pages/                  # Vistas por rol: Productor, Recepción, Laboratorio, Consola Recall
├── components/             # Componentes reusables: formularios, tablas, visor interactivo de grafos
├── hooks/                  # Lógica de consumo de datos con TanStack Query (equivalente a services)
├── api/                    # Cliente HTTP tipado hacia FastAPI (equivalente a repositories)
├── auth/                   # Contexto de autenticación, almacenamiento seguro de JWT y guards por rol
├── types/                  # Interfaces y tipos TypeScript alineados a los esquemas de la API
└── main.tsx                # Montaje de la app y definición de rutas
```

Flujo unificado:
`Page (Vista)` → `Hook (Lógica y Caché)` → `API Client (HTTP)` → `Backend REST`

### Directriz / Prompt detonante
"Asegurar que la estructura del frontend sea espejo del flujo de capas del backend para que el equipo hable el mismo idioma de desarrollo."

### Impacto
* Código limpio y predecible: un desarrollador sabe exactamente a qué carpeta ir según si edita diseño visual (`components`), lógica de petición (`hooks`) o llamadas HTTP (`api`).

## 8. Seguridad, Inmutabilidad y Reglas de Negocio Clave

### Contexto
El valor legal y operativo de un sistema de trazabilidad depende de la certeza de que los certificados de inocuidad no puedan ser alterados retroactivamente y que el inventario no se venda en falso.

### Decisiones acordadas
1. **Inmutabilidad en Laboratorio (RN-03, RN-04):**
   * Los certificados de análisis en MongoDB son inmutables. Toda corrección crea una nueva versión (`v2`) y archiva la anterior, manteniendo el historial completo de auditoría y autor.
2. **Bloqueo Atómico de Inventario (RN-07):**
   * Cuando QA detecta un contaminante (ej. *Salmonella* o exceso de plaguicidas), el lote se bloquea de forma atómica en PostgreSQL con `SELECT ... FOR UPDATE` y `WHERE estado != 'Bloqueado'`, cancelando de inmediato cualquier despacho en curso.
3. **Control Estricto de Roles (RBAC / RN-11):**
   * Productor solo registra cosechas; Recepción solo registra pesajes y temperatura; Laboratorio solo carga análisis; únicamente QA / Gerencia puede liberar o bloquear lotes.

### Directriz / Prompt detonante
"Garantizar que el sistema cumpla con estándares auditables de inocuidad alimentaria (FDA / Senasica), donde los certificados nunca se borran ni se sobreescriben."

### Impacto
* Cumplimiento normativo y confianza total de auditoría para clientes internacionales y autoridades regulatorias.

## 9. Seguridad en Persistencia: Principio de Menor Privilegio (PoLP)

### Contexto
Actualmente los contenedores de desarrollo exponen usuarios con privilegios administrativos totales (`trazaagro` superuser/owner en PostgreSQL, usuario root en MongoDB y `neo4j` admin en Neo4j). Si la API backend se conecta usando estas credenciales maestras, cualquier brecha de seguridad o error de código podría permitir operaciones destructivas de DDL (`DROP TABLE`, `DROP DATABASE`) o escalación de privilegios en el motor.

### Opciones consideradas
* **Opción A:** Mantener un solo usuario administrativo para desarrollo y producción compartiendo credenciales root con la API.
* **Opción B:** Separar roles por nivel de privilegio: un usuario administrador de infraestructura (para ejecutar scripts DDL iniciales, migraciones y mantenimiento) y un usuario de aplicación dedicado (`trazaagro_app`) con privilegios mínimos (DML: `SELECT`, `INSERT`, `UPDATE`, `DELETE`) para el backend.

### Decisión tomada
Se adoptó la **Opción B**:
* **PostgreSQL:** Crear el rol `trazaagro_app` con permisos exclusivos de DML (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) sobre las tablas del esquema `public` y uso de secuencias. No tiene permisos de superusuario, creación de bases ni alteración de esquemas (DDL).
* **MongoDB:** Crear un usuario específico de aplicación acotado únicamente a la base `trazaagro` con el rol estándar `readWrite`, sin acceso a colecciones del sistema (`admin`, `config`) ni roles de gestión de usuarios (`userAdmin`, `dbAdmin`).
* **Neo4j:** En entorno Community se segregan las credenciales de conexión de la API frente a las credenciales administrativas de mantenimiento, limitando la superficie de exposición.
* **Backend:** La API en tiempo de ejecución solo recibe y utiliza las cadenas de conexión del usuario `trazaagro_app` vía variables de entorno en `.env`. Los scripts DDL y semillas continúan siendo administrados por el usuario de aprovisionamiento.

### Directriz / Prompt detonante
"Implementar el Principio de Menor Privilegio en las conexiones de base de datos para que la API no opere con credenciales de superusuario o privilegios administrativos innecesarios."

### Impacto
* Arquitectura mucho más profesional y alineada con estándares de seguridad en producción (defensa en profundidad).
* Protección contra caídas o borrados accidentales de estructuras de datos desde la capa de la API.
* Transición transparente para el backend: solo requiere actualizar las cadenas de conexión en las variables de entorno sin modificar la lógica de los repositorios.
