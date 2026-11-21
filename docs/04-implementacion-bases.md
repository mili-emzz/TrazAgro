# Implementación y Validación de las Tres Bases de Datos: TrazaAgro

Esta guía visual concentra el despliegue y validación de las tres bases de datos de **TrazaAgro** (**PostgreSQL 16**, **MongoDB 7** y **Neo4j 5**). Su propósito es servir como referencia gráfica, clara y práctica de cómo se levantan los contenedores, cómo interactúan los datos y cómo comprobar que cada candado de integridad funciona a la perfección.

## 1. Arquitectura del Entorno en Docker

Todo el ecosistema corre en contenedores orquestados con Docker Compose, por lo que no hace falta instalar ningún gestor de bases de datos directo en el sistema operativo anfitrión.

```mermaid
flowchart TD
    subgraph HOST["Tu Máquina Local (Host)"]
        COMPOSE["docker compose up -d --wait"]
        ENV[".env.example / .env"]
        SCRIPTS["./database/ (relational / document / graph)"]
    end

    subgraph DOCKER["Docker Engine"]
        subgraph PG_BOX["trazaagro-postgres (PostgreSQL 16 Alpine)"]
            PG_ENGINE[("PostgreSQL\nPuerto int: 5432")]
            PG_VOL[("Volumen: pg_data")]
            PG_SCRIPTS["Montaje: /scripts (relational)"]
        end

        subgraph MG_BOX["trazaagro-mongo (MongoDB 7)"]
            MG_ENGINE[("MongoDB\nPuerto int: 27017")]
            MG_VOL[("Volumen: mongo_data")]
            MG_SCRIPTS["Montaje: /scripts (document)"]
        end

        subgraph N4J_BOX["trazaagro-neo4j (Neo4j 5 Community)"]
            N4J_ENGINE[("Neo4j Engine\nBolt: 7687 | HTTP: 7474")]
            N4J_VOL[("Volumen: neo4j_data")]
            N4J_SCRIPTS["Montaje: /scripts (graph)"]
        end
    end

    COMPOSE --> DOCKER
    PG_ENGINE ---|"Puerto host: 5433"| HOST
    MG_ENGINE ---|"Puerto host: 27017"| HOST
    N4J_ENGINE ---|"Puertos host: 7474 / 7687"| HOST

    SCRIPTS -.-> PG_SCRIPTS
    SCRIPTS -.-> MG_SCRIPTS
    SCRIPTS -.-> N4J_SCRIPTS
```

### Comandos de control del entorno

Para levantar los tres contenedores y esperar a que sus *healthchecks* estén en verde:

```powershell
docker compose up -d --wait
```

Para apagar y limpiar volúmenes (empezar desde cero absoluto):

```powershell
docker compose down -v
docker compose up -d --wait
```

## 2. Coreografía Multimotor en Acción (El Flujo del Aguacate)

Para entender cómo se reparten la carga de trabajo los tres motores, este diagrama ilustra el flujo de un lote desde su cosecha hasta una alerta de recall por plaguicidas:

```mermaid
sequenceDiagram
    autonumber
    actor QA as Inspector / QA
    participant PG as PostgreSQL (ACID)
    participant MG as MongoDB (Docs)
    participant N4J as Neo4j (Grafo)

    Note over QA,N4J: 1. Cosecha y Arribo a CEDIS
    QA->>PG: Registra lote y recepción (lotes, recepciones_cedis)
    QA->>MG: Guarda acta física y perfil de temperatura (actas_recepcion)
    QA->>N4J: Conecta (:Lote)-[:COSECHADO_EN]->(:Parcela) y [:TRASLADADO_EN]->(:Vehiculo)

    Note over QA,N4J: 2. Análisis de Laboratorio
    QA->>MG: Registra dictamen multirresiduos (analisis_laboratorio)
    QA->>N4J: Proyecta (:Laboratorio)-[:EMITIO_ANALISIS]->(:Lote)
    QA->>PG: Si es Conforme, actualiza estado a 'Liberado' (lotes)

    Note over QA,N4J: 3. Despacho a Tiendas
    QA->>PG: Descuenta saldo_kg transaccionalmente (envios, envios_detalle)
    QA->>N4J: Conecta (:Lote)-[:DIVIDIDO_EN]->(:Envio)-[:ENTREGADO_A]->(:Tienda)

    Note over QA,N4J: 4. Alerta Sanitaria y Recall de Emergencia (RN-08)
    QA->>MG: Registra resultado No Conforme y abre expediente (expedientes_incidentes)
    QA->>PG: Bloqueo atómico: UPDATE lotes SET estado = 'Bloqueado'
    QA->>N4J: Consulta hacia adelante (tiendas afectadas) y lateral (lotes hermanos)
```

## 3. Base Relacional (PostgreSQL 16)

PostgreSQL es la fuente de verdad contable y de estados. Garantiza que no se venda fruta bloqueada (`RN-01`), que no se despache más de lo que existe (`RN-03`) y que no se pierda la trazabilidad histórica (`RN-10`).

```mermaid
erDiagram
    PRODUCTORES ||--o{ PARCELAS : posee
    PARCELAS ||--o{ LOTES : origina
    LOTES ||--o| RECEPCIONES_CEDIS : arriba
    LOTES ||--o{ ENVIOS_DETALLE : divide
    ENVIOS ||--|{ ENVIOS_DETALLE : contiene
    TIENDAS ||--o{ ENVIOS : recibe
    LOTES ||--o{ INCIDENTES_BITACORA : audita

    LOTES {
        int lote_id PK
        string codigo_lote UK
        decimal peso_inicial_kg
        decimal saldo_kg
        string estado
    }
    RECEPCIONES_CEDIS {
        int recepcion_id PK
        string folio_recepcion UK
        int lote_id UK
        decimal temperatura_llegada_c
        string dictamen_recepcion
    }
    ENVIOS {
        int envio_id PK
        string codigo_envio UK
        int tienda_id FK
        string estado_envio
    }
    ENVIOS_DETALLE {
        int envio_id PK_FK
        int lote_id PK_FK
        decimal cantidad_kg
    }
```

### Ejecución de scripts

```powershell
docker exec trazaagro-postgres psql -v ON_ERROR_STOP=1 -U trazaagro -d trazaagro -f /scripts/01_schema.sql
docker exec trazaagro-postgres psql -v ON_ERROR_STOP=1 -U trazaagro -d trazaagro -f /scripts/02_seed_data.sql
docker exec trazaagro-postgres psql -v ON_ERROR_STOP=1 -U trazaagro -d trazaagro -f /scripts/03_queries_and_tests.sql
```

### Resultados y Candados Verificados

* **Balance de masa exacto (`RN-03`):** La consulta de balance verificó que en los 6 lotes la suma de `saldo_kg` más `total_despachado_kg` coincide al 100% con `cosechado_kg` (`cuadre_exacto = t`).
* **Auditoría de cadena de frío (`RN-07`):** La vista `v_auditoria_cadena_frio` aisló al lote `AGU-P015-260315-01` que llegó a `11.4 °C` (máximo permitido: `8.0 °C`), reteniéndolo en revisión.
* **Transacción de despacho ACID:** Se ejecutó `SELECT ... FOR UPDATE` sobre el lote `AGU-P018-260316-01`, descontando `300 kg` (`2000 kg` a `1700 kg`) con reversión limpia mediante `ROLLBACK`.
* **Pruebas negativas aprobadas:**
  * `Prueba 3.1`: Rechazó saldo negativo (`check_violation`).
  * `Prueba 3.2`: Rechazó saldo mayor al peso inicial (`check_violation`).
  * `Prueba 3.3`: Rechazó estado fuera de catálogo (`check_violation`).
  * `Prueba 3.4`: Rechazó doble recepción en relación 1:0..1 (`unique_violation`).
  * `Prueba 3.5`: Rechazó duplicar lote en mismo envío (`unique_violation`).
  * `Prueba 3.6`: Impidió borrado físico de lote con historial (`foreign_key_violation` por `ON DELETE RESTRICT`).

## 4. Base Documental (MongoDB 7)

MongoDB almacena información polimórfica, jerárquica e inmutable: certificados de laboratorio con listas variables de plaguicidas, actas de inspección física y expedientes de recall.

```mermaid
flowchart TD
    subgraph MONGO_DB["Base de Datos: trazaagro"]
        COLL_LAB["analisis_laboratorio\n(Validación $jsonSchema estricta)"]
        COLL_ACT["actas_recepcion\n(Validación $jsonSchema estricta)"]
        COLL_INC["expedientes_incidentes\n(Validación condicional anyOf)"]
    end

    COLL_LAB --> LAB_DOC["Doc: { folio_analisis, codigo_lote, tipo_estudio,\nversion, es_vigente, muestras: [ { determinaciones: [...] } ] }"]
    COLL_ACT --> ACT_DOC["Doc: { folio_recepcion, codigo_lote,\ndefectos_detectados: [...], monitoreo_temperatura_caja: [...] }"]
    COLL_INC --> INC_DOC["Doc: { folio_incidente, codigo_lote, estado_expediente,\nafectaciones_cadena: [...], causa_raiz, firmas_cierre }"]

    INDEX_VIGENTE["Índice Único Parcial (RN-05):\n{ codigo_lote: 1, tipo_estudio: 1 }\nwhere: { es_vigente: true }"] -.-> COLL_LAB
```

### Ejecución de scripts

```powershell
$uri = "mongodb://trazaagro:trazaagro_dev_pass@localhost:27017/trazaagro?authSource=admin"
docker exec trazaagro-mongo mongosh $uri --file /scripts/01_setup_collections.js
docker exec trazaagro-mongo mongosh $uri --file /scripts/02_seed_data.js
docker exec trazaagro-mongo mongosh $uri --file /scripts/03_queries_and_tests.js
```

### Resultados y Validaciones Verificadas

* **Detección multirresiduos (`PA-03`):** Consulta por `$elemMatch` sobre `determinaciones` que encontró la molécula no conforme en `LAB-2026-AGU-0842-V1` (`Clorpirifos: 0.08 mg/kg`, rebasando el límite de `0.01 mg/kg`).
* **Versionado inmutable (`RN-05` y `PA-04`):** El lote `AGU-P018-260314-01` preservó su versión 1 histórica (`No Conforme`, `es_vigente: false`) y la versión 2 enmendada (`Conforme`, `es_vigente: true`).
* **Pipeline de agregación de recall (`PA-07`):** Calculó el porcentaje real de fruta retirada en el incidente `INC-2026-0012`, logrando recuperar `795 kg` de los `850 kg` despachados (`93.53%` de efectividad).
* **Pruebas negativas ($jsonSchema):**
  * `Prueba 2.2`: Rechazó tipo de estudio inexistente y array de muestras vacío (código `121`).
  * `Prueba 2.3`: Rechazó determinación sin booleano `conforme` (código `121`).
  * `Prueba 2.4`: Rechazó registrar dos certificados vigentes para el mismo lote y estudio (código `11000` por índice parcial único).
  * `Prueba 2.5`: Rechazó temperaturas físicas incoherentes en actas (código `121`).
  * `Prueba 2.6`: Rechazó cerrar un expediente si no incluye causa raíz ni firmas responsables (código `121` por validación condicional `anyOf`).

## 5. Base de Grafos (Neo4j 5)

Neo4j modela las rutas físicas y logísticas. Resuelve en milisegundos preguntas de conectividad profunda que en SQL requerirían múltiples joins recursivos.

```mermaid
graph LR
    PROD["(:Productor)"] -->|PERTENECE_A| PARC["(:Parcela)"]
    LOTE["(:Lote)"] -->|COSECHADO_EN| PARC
    LOTE -->|TRASLADADO_EN| VEH1["(:Vehiculo)"]
    LOTE -->|ALMACENADO_EN| CF["(:CuartoFrio)"]
    LAB["(:Laboratorio)"] -->|EMITIO_ANALISIS| LOTE
    LOTE -->|DIVIDIDO_EN| ENV["(:Envio)"]
    ENV -->|DESPACHADO_EN| VEH2["(:Vehiculo)"]
    ENV -->|ENTREGADO_A| TND["(:Tienda)"]
```

### Ejecución de scripts

```powershell
docker exec trazaagro-neo4j cypher-shell -u neo4j -p trazaagro_dev_pass -f /scripts/01_schema.cypher
docker exec trazaagro-neo4j cypher-shell -u neo4j -p trazaagro_dev_pass -f /scripts/02_seed_data.cypher
docker exec trazaagro-neo4j cypher-shell -u neo4j -p trazaagro_dev_pass -f /scripts/03_queries_and_tests.cypher
```

### Consultas de Alto Impacto Verificadas

```mermaid
flowchart LR
    subgraph LATERAL["Contaminación Lateral (RN-08)"]
        LOTE_A["Lote Contaminado\nAGU-P014-260312-01"]
        RECURSO["Vehículo MICH-842-K\ny Cuarto Frío CF-02"]
        LOTE_B["Lote Hermano en Riesgo\nAGU-P014-260312-02"]
        LOTE_A --- RECURSO --- LOTE_B
    end

    subgraph FORWARD["Blast Radius / Forward Recall"]
        LOTE_A --> ENV1["Envío ENV-2026-1052\n(450 kg)"] --> SUC1["Supermercados del Norte\n(Monterrey)"]
        LOTE_A --> ENV2["Envío ENV-2026-1053\n(400 kg)"] --> SUC2["Selecto Chedraui Polanco\n(CDMX)"]
    end
```

* **Rastreo hacia adelante (`CU-GRF-01`):** Identificó al instante las sucursales donde ya se habían colocado los `850 kg` del lote contaminado para notificar el retiro inmediato.
* **Trazabilidad hacia atrás (`CU-GRF-02`):** Rastreó el origen de un pallet en góndola hasta la huerta "La Escondida" en Uruapan y el teléfono de contacto del productor.
* **Detección de contaminación cruzada lateral (`CU-GRF-03`):** Alertas automáticas para el lote hermano `AGU-P014-260312-02` por haber compartido simultáneamente el camión `MICH-842-K` y el cuarto frío `CF-02`.

## 6. Matriz de Identificadores Cruzados (Vista 360°)

Para que el backend pueda integrar las respuestas sin discrepancias, todos los scripts de prueba comparten las mismas llaves de negocio:

| Concepto de Negocio | PostgreSQL (Relacional) | MongoDB (Documental) | Neo4j (Grafos) |
| :--- | :--- | :--- | :--- |
| **Lote con Recall** | `codigo_lote: AGU-P014-260312-01`<br>`estado: Bloqueado` | `folio_analisis: LAB-2026-AGU-0842-V1`<br>`folio_incidente: INC-2026-0012` | Nodo `:Lote`<br>Aristas a envíos `ENV-1052` y `1053` |
| **Lote Hermano (`RN-08`)** | `codigo_lote: AGU-P014-260312-02`<br>`estado: Bloqueado` | `folio_recepcion: REC-2026-0105` | Comparte nodos `:Vehiculo` (`MICH-842-K`) y `:CuartoFrio` (`CF-02`) |
| **Enmienda de Lab (`RN-05`)** | `codigo_lote: AGU-P018-260314-01`<br>`estado: Liberado` | `LAB-2026-AGU-0910-V1` (no vigente)<br>`LAB-2026-AGU-0910-V2` (vigente) | 2 relaciones `[:EMITIO_ANALISIS]` desde el mismo laboratorio |
| **Ruptura Térmica (`RN-07`)** | `codigo_lote: AGU-P015-260315-01`<br>`estado: En revision` | `folio_recepcion: REC-2026-0107`<br>Monitoreo por zona: `10.8`, `11.4`, `12.1 °C` | Nodo `:Lote` vinculado a `:Vehiculo` `JAL-405-C` y `:CuartoFrio` `CF-03` |
| **Lote en Tránsito** | `codigo_lote: AGU-P014-260318-01`<br>`estado: Cosechado` | Sin recepción registrada aún | Nodo `:Lote` únicamente con `[:COSECHADO_EN]` |

## 7. Accesos Directos e Inspección Visual

Si deseas explorar los datos de forma interactiva con herramientas visuales:

* **Neo4j Browser Web:** Abre en el navegador `http://localhost:7474`, usuario `neo4j`, contraseña `trazaagro_dev_pass`. Puedes ejecutar `MATCH (n) RETURN n LIMIT 50;` para ver los grafos en pantalla con colores interactivos.
* **MongoDB Compass:** Conéctate con la URI `mongodb://trazaagro:trazaagro_dev_pass@localhost:27017/trazaagro?authSource=admin` para inspeccionar los documentos en formato JSON y ver las reglas `$jsonSchema`.
* **DBeaver / pgAdmin / psql:** Conéctate a PostgreSQL en `localhost:5433`, base `trazaagro`, usuario `trazaagro`, contraseña `trazaagro_dev_pass`.
