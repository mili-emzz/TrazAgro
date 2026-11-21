# Decisión de Diseño: Modelo Documental en MongoDB

Este documento reúne de forma independiente todo el razonamiento, los patrones de acceso, la definición de colecciones y la estructura completa de documentos para la capa documental de **TrazaAgro** en **MongoDB**. Funciona como referencia técnica directa junto con [01-arquitectura-tres-bases.md](file:///c:/Users/Emilia/OneDrive/Documentos/Emilia/UP/DaaS/proyecto-final/docs/decisiones/01-arquitectura-tres-bases.md) y alimenta la sección correspondiente en [02-modelado-datos.md](file:///c:/Users/Emilia/OneDrive/Documentos/Emilia/UP/DaaS/proyecto-final/docs/02-modelado-datos.md).

## 1. Enfoque de diseño y casos de uso

En lugar de traducir tablas relacionales a colecciones, el modelo documental se diseñó con **Query-Driven Modeling** (modelado guiado por consultas). MongoDB resuelve exclusivamente los datos que presentan polimorfismo (atributos variables por cultivo o estudio), anidamiento natural y versionado inmutable:

* **CU-DOC-01 (Cargar certificado de análisis de laboratorio):** El laboratorio externo o QA registra un estudio (`Residuos de Plaguicidas`, `Microbiologico` o `Materia Seca`) con una o varias muestras y decenas de determinaciones químicas o biológicas.
* **CU-DOC-02 (Emitir corrección o nueva versión):** Por regla de negocio (`RN-05`), un resultado de laboratorio nunca se borra ni se sobreescribe. Una corrección conserva la versión previa (`es_vigente: false`) e inserta un nuevo documento (`version: N + 1`, `es_vigente: true`) con su motivo de enmienda.
* **CU-DOC-03 (Auditar parámetros anidados fuera de norma):** QA filtra dentro de los certificados vigentes aquellas determinaciones que rebasaron los límites normativos (`conforme: false`).
* **CU-DOC-04 (Registrar acta de inspección física y sensorial en CEDIS):** Recepción captura la evidencia cualitativa de cada llegada de camión: lecturas térmicas por tarima, atributos sensoriales del fruto, defectos físicos, fotos y observaciones libres.
* **CU-DOC-05 (Consultar expediente 360° e historial):** QA, Gerencia y auditores recuperan en una sola consulta tanto el acta de entrada como el historial completo de análisis de un `codigo_lote`.

### Permisos por actor en la capa documental

| Actor del sistema | Qué registra en MongoDB | Qué puede consultar | Restricciones de acceso y modificación |
| :--- | :--- | :--- | :--- |
| **Laboratorio Externo** | Nuevos certificados y nuevas versiones en `analisis_laboratorio`. | Únicamente los estudios emitidos por su propio laboratorio. | No puede borrar ni editar documentos previos; no ve `actas_recepcion` ni análisis de otros laboratorios. |
| **Recepción CEDIS** | Actas físicas, evaluación sensorial, temperaturas y fotos en `actas_recepcion`. | Actas de recepción capturadas en su centro de distribución. | No puede crear ni modificar resultados en `analisis_laboratorio`. |
| **QA e Inocuidad** | Validación de enmiendas y dictámenes de inspección. | Acceso total a ambas colecciones, incluyendo versiones históricas (`es_vigente: false`). | Prohibido eliminar versiones previas o destruir el historial documental. |
| **Productor / Empacadora** | Ninguna escritura directa. | Resultados de laboratorio y actas de recepción únicamente de sus propios lotes. | Bloqueo estricto para ver documentos de otros productores (`RN-11`). |
| **Gerencia / Auditor** | Ninguna escritura directa. | Solo lectura sobre expedientes completos e historial de versiones. | Sin permisos de inserción, actualización ni borrado. |

## 2. Tabla de patrones de acceso

| ID | Operación / Caso de uso | Tipo | Clave de búsqueda / Filtro | Unidad atómica (qué se lee o escribe junto) | Frecuencia y criticidad |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PA-01** | Registrar nuevo certificado de laboratorio (CU-DOC-01) | Escritura (`insertOne`) | N/A (inserta con `folio_analisis` y `codigo_lote`) | Cabecera + `laboratorio` + `firma_digital` + arreglo completo de `muestras` y `determinaciones`. | Media (1 a 3 estudios por lote). Crítica para liberar inventario. |
| **PA-02** | Versionar análisis por corrección técnica (CU-DOC-02) | Escritura (`updateOne` + `insertOne`) | `codigo_lote` + `tipo_estudio` + `es_vigente: true` | Pasa a `es_vigente: false` el documento previo e inserta el nuevo documento con `version: N + 1` y `motivo_enmienda`. | Baja (excepciones), pero obligatoria por auditoría legal. |
| **PA-03** | Detectar parámetros fuera de norma (CU-DOC-03) | Lectura (`find`) | `codigo_lote` + `es_vigente: true` + `"muestras.determinaciones": { $elemMatch: { conforme: false } }` | Datos del laboratorio, dictamen general y determinaciones infractoras proyectadas. | Alta (en cada liberación y en bloqueos de emergencia). |
| **PA-04** | Consultar historial completo de versiones (CU-DOC-05) | Lectura (`find` con `sort: { version: -1 }`) | `codigo_lote` + `tipo_estudio` (sin filtrar vigencia) | Todas las versiones emitidas para auditar cambios entre V1, V2, etc. | Media (auditorías e investigaciones de incidentes). |
| **PA-05** | Guardar acta de inspección física en CEDIS (CU-DOC-04) | Escritura (`insertOne`) | N/A (ligada a `folio_recepcion` y `codigo_lote`) | `inspector` + `evaluacion_sensorial` + `defectos_detectados` + `monitoreo_temperatura_caja` + `evidencias_fotograficas`. | Alta (15 a 25 recepciones diarias en CEDIS). |
| **PA-06** | Recuperar acta física y evidencias (CU-DOC-05) | Lectura (`findOne`) | `folio_recepcion` o `codigo_lote` | Documento íntegro del acta de recepción para la vista 360° del lote. | Alta (consulta cotidiana de almacén, QA y reclamos). |

## 3. Análisis de repetición de datos: ¿Anidar o separar?

Al evaluar la frecuencia con la que se repiten los datos en los patrones de acceso, se tomaron cuatro decisiones de modelado:

1. **Determinaciones dentro de cada muestra (1 a 200 por análisis):** Se **anidan** en `muestras[].determinaciones[]`. Nunca se consultan huérfanas sin su certificado y su tamaño es acotado (< 40 KB, muy por debajo del límite de 16 MB de BSON). Evita usar `$lookup`.
2. **Datos del laboratorio emisor (`nombre`, `acreditacion_iso`):** Se **anidan** como subdocumento `laboratorio` aplicando el patrón *Snapshot*. Como un certificado es evidencia legal histórica, si el laboratorio cambia su acreditación en el futuro, los certificados antiguos deben conservar intactos los datos vigentes en su fecha de emisión.
3. **Múltiples estudios y versiones de un mismo lote:** Se **separan como documentos independientes** dentro de `analisis_laboratorio` (`1 documento = 1 versión de 1 estudio`). Meterlos todos en un arreglo del lote crearía tres niveles de anidamiento, complicaría el `$elemMatch` y bloquearía el uso de índices únicos parciales para controlar la vigencia.
4. **Lecturas térmicas, defectos físicos y fotos de recepción:** Se **anidan** dentro de `actas_recepcion`, pero el acta completa vive en su propia colección separada de `analisis_laboratorio` porque tienen actores distintos (Recepción CEDIS vs. Laboratorio Externo) y momentos de captura independientes.

## 4. Colecciones definitivas y especificación de campos

### Colección 1: `analisis_laboratorio`
Justificada por **PA-01, PA-02, PA-03 y PA-04**. Cada documento representa una versión inmutable de un certificado analítico.

* **Campos raíz:**
  * `_id`: `ObjectId` (PK autogenerada, obligatoria)
  * `folio_analisis`: `String` (Obligatorio, único; ej. `LAB-2026-AGU-0842-V1`)
  * `codigo_lote`: `String` (Obligatorio; llave puente con `lotes` en PostgreSQL y `(:Lote)` en Neo4j)
  * `tipo_estudio`: `String` (Obligatorio; `Residuos de Plaguicidas`, `Microbiologico`, `Materia Seca`)
  * `fecha_muestreo`: `Date / ISODate` (Obligatorio)
  * `fecha_emision`: `Date / ISODate` (Obligatorio)
  * `version`: `Int32` (Obligatorio, `>= 1`)
  * `es_vigente`: `Boolean` (Obligatorio; `true` en la versión activa, `false` en versiones reemplazadas)
  * `folio_reemplazado`: `String | Null` (Opcional; `null` en V1, folio previo en V2+)
  * `motivo_enmienda`: `String | Null` (Obligatorio cuando `version > 1`)
  * `dictamen_general`: `String` (Obligatorio; `Conforme`, `No Conforme`)
* **Subdocumento `laboratorio` (1:1, obligatorio):** `nombre` (`String`), `acreditacion_iso` (`String`), `contacto_correo` (`String`, opcional).
* **Subdocumento `firma_digital` (1:1, obligatorio):** `responsable_signatario` (`String`), `cedula_profesional` (`String`), `hash_integridad` (`String`).
* **Arreglo `muestras[]` (1 a 5 por estudio, obligatorio):** `identificador_muestra` (`String`), `parte_analizada` (`String`), `peso_gramos` (`Double / Int32`), `determinaciones` (`Array<Object>`).
* **Arreglo polimórfico `muestras[].determinaciones[]` (1 a 200 por muestra, obligatorio):**
  * `molecula` o `parametro`: `String` (Obligatorio)
  * `metodo_ensayo`: `String` (Obligatorio)
  * `resultado_mg_kg` / `resultado_numerico`: `Double` (Condicional para pruebas cuantitativas)
  * `resultado_cualitativo`: `String` (Condicional para pruebas de presencia/ausencia)
  * `unidad`: `String` (Obligatorio; `mg/kg`, `ppm`, `%`, `UFC/g`, `Presencia/Ausencia`)
  * `limite_maximo_mg_kg` / `limite_maximo`: `Double` (Condicional; tope superior permitido)
  * `limite_minimo`: `Double` (Condicional; piso mínimo, ej. `21.0%` materia seca)
  * `conforme`: `Boolean` (Obligatorio)

### Colección 2: `actas_recepcion`
Justificada por **PA-05 y PA-06**. Extiende cualitativamente el registro maestro de `recepciones_cedis` (PostgreSQL).

* **Campos raíz:**
  * `_id`: `ObjectId` (PK autogenerada, obligatoria)
  * `folio_recepcion`: `String` (Obligatorio, único; enlace 1:1 con `recepciones_cedis.folio_recepcion`)
  * `codigo_lote`: `String` (Obligatorio; enlace con `lotes.codigo_lote`)
  * `fecha_hora_inspeccion`: `Date / ISODate` (Obligatorio)
  * `observaciones_inspector`: `String` (Opcional)
* **Subdocumento `inspector` (1:1, obligatorio):** `usuario_id` (`String`), `nombre` (`String`), `turno` (`String`: `Matutino`, `Vespertino`, `Nocturno`).
* **Subdocumento `evaluacion_sensorial` (1:1, obligatorio):** `color_epidermis` (`String`), `firmeza_pulpa_lb` (`Double`), `materia_seca_estimada_pct` (`Double`, opcional), `calibre_predominante` (`String`), `pedunculo_presente_pct` (`Double`), `olor_extrano` (`Boolean`).
* **Arreglo `defectos_detectados[]` (0 a 10, opcional):** `tipo_defecto` (`String`), `severidad` (`String`: `Leve`, `Moderada`, `Critica`), `porcentaje_afectado` (`Double`, `0` a `100`).
* **Arreglo `monitoreo_temperatura_caja[]` (3 a 6 lecturas, obligatorio):** `zona_contenedor` (`String`), `tarima` (`String`), `temperatura_c` (`Double`).
* **Arreglo `evidencias_fotograficas[]` (1 a 10 imágenes, opcional):** `tipo_evidencia` (`String`), `url_archivo` (`String`), `descripcion` (`String`).

## 5. Ejemplos completos de documentos JSON

### Documento 1A: Certificado de Plaguicidas No Conforme (V1 en `analisis_laboratorio`)
```json
{
  "_id": { "$oid": "65f1a2b3c4d5e6f7a8b9c0d1" },
  "folio_analisis": "LAB-2026-AGU-0842-V1",
  "codigo_lote": "AGU-P014-260312-01",
  "tipo_estudio": "Residuos de Plaguicidas",
  "fecha_muestreo": "2026-03-12T10:00:00Z",
  "fecha_emision": "2026-03-13T16:45:00Z",
  "version": 1,
  "es_vigente": true,
  "folio_reemplazado": null,
  "motivo_enmienda": null,
  "dictamen_general": "No Conforme",
  "laboratorio": {
    "nombre": "Lab AgroBio S.A. de C.V.",
    "acreditacion_iso": "EMA-ISA-17025-2024",
    "contacto_correo": "certificados@agrobio.com.mx"
  },
  "firma_digital": {
    "responsable_signatario": "Q.F.B. Elena Rostova",
    "cedula_profesional": "7845129",
    "hash_integridad": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "muestras": [
    {
      "identificador_muestra": "M-01",
      "parte_analizada": "Pulpa y epidermis entera",
      "peso_gramos": 500,
      "determinaciones": [
        {
          "molecula": "Clorpirifos",
          "metodo_ensayo": "AOAC 2007.01 (QuEChERS / GC-MS/MS)",
          "resultado_mg_kg": 0.08,
          "unidad": "mg/kg",
          "limite_maximo_mg_kg": 0.01,
          "conforme": false
        },
        {
          "molecula": "Malation",
          "metodo_ensayo": "AOAC 2007.01 (QuEChERS / GC-MS/MS)",
          "resultado_mg_kg": 0.002,
          "unidad": "mg/kg",
          "limite_maximo_mg_kg": 0.05,
          "conforme": true
        }
      ]
    }
  ]
}
```

### Documento 1B: Certificado Enmendado V2 por corrección inmutable (`analisis_laboratorio`)
```json
{
  "_id": { "$oid": "65f2c8d1e4b0a1c2d3e4f5a6" },
  "folio_analisis": "LAB-2026-AGU-0910-V2",
  "codigo_lote": "AGU-P018-260314-01",
  "tipo_estudio": "Residuos de Plaguicidas",
  "fecha_muestreo": "2026-03-14T09:15:00Z",
  "fecha_emision": "2026-03-15T11:20:00Z",
  "version": 2,
  "es_vigente": true,
  "folio_reemplazado": "LAB-2026-AGU-0910-V1",
  "motivo_enmienda": "Reanálisis de contramuestra M-01B por ajuste de curva de calibración en detector MS/MS.",
  "dictamen_general": "Conforme",
  "laboratorio": {
    "nombre": "Lab AgroBio S.A. de C.V.",
    "acreditacion_iso": "EMA-ISA-17025-2024",
    "contacto_correo": "certificados@agrobio.com.mx"
  },
  "firma_digital": {
    "responsable_signatario": "Q.F.B. Elena Rostova",
    "cedula_profesional": "7845129",
    "hash_integridad": "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4"
  },
  "muestras": [
    {
      "identificador_muestra": "M-01B",
      "parte_analizada": "Pulpa y epidermis entera (Contramuestra sellada)",
      "peso_gramos": 500,
      "determinaciones": [
        {
          "molecula": "Abamectina",
          "metodo_ensayo": "AOAC 2007.01 (QuEChERS / LC-MS/MS)",
          "resultado_mg_kg": 0.008,
          "unidad": "mg/kg",
          "limite_maximo_mg_kg": 0.02,
          "conforme": true
        }
      ]
    }
  ]
}
```

### Documento 1C: Certificado Polimórfico Microbiológico y de Materia Seca (`analisis_laboratorio`)
```json
{
  "_id": { "$oid": "65f3d9e2f5c1b2d3e4f5a6b7" },
  "folio_analisis": "LAB-2026-AGU-0845-V1",
  "codigo_lote": "AGU-P014-260312-01",
  "tipo_estudio": "Microbiologico",
  "fecha_muestreo": "2026-03-12T10:30:00Z",
  "fecha_emision": "2026-03-13T14:00:00Z",
  "version": 1,
  "es_vigente": true,
  "folio_reemplazado": null,
  "motivo_enmienda": null,
  "dictamen_general": "Conforme",
  "laboratorio": {
    "nombre": "Centro Analítico Fitosanitario de Occidente S.C.",
    "acreditacion_iso": "EMA-LA-0412-2025",
    "contacto_correo": "resultados@cafo.mx"
  },
  "firma_digital": {
    "responsable_signatario": "M. en C. Roberto Villaseñor",
    "cedula_profesional": "4519082",
    "hash_integridad": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
  },
  "muestras": [
    {
      "identificador_muestra": "M-BIO-01",
      "parte_analizada": "Superficie epidérmica y pulpa",
      "peso_gramos": 250,
      "determinaciones": [
        {
          "parametro": "Salmonella spp.",
          "metodo_ensayo": "NOM-210-SSA1-2014 Apéndice A",
          "resultado_cualitativo": "Ausente en 25g",
          "unidad": "Presencia/Ausencia",
          "conforme": true
        },
        {
          "parametro": "Escherichia coli",
          "metodo_ensayo": "NOM-210-SSA1-2014",
          "resultado_numerico": 10,
          "unidad": "UFC/g",
          "limite_maximo": 100,
          "conforme": true
        },
        {
          "parametro": "Porcentaje de Materia Seca",
          "metodo_ensayo": "NMX-FF-016-SCFI-2016 (Horno de secado)",
          "resultado_numerico": 24.2,
          "unidad": "%",
          "limite_minimo": 21.0,
          "conforme": true
        }
      ]
    }
  ]
}
```

### Documento 2: Acta de Inspección Física y Sensorial en CEDIS (`actas_recepcion`)
```json
{
  "_id": { "$oid": "65f1b5e9c4d5e6f7a8b9c0e8" },
  "folio_recepcion": "REC-2026-0104",
  "codigo_lote": "AGU-P014-260312-01",
  "fecha_hora_inspeccion": "2026-03-12T18:30:00Z",
  "inspector": {
    "usuario_id": "USR-REC-08",
    "nombre": "Carlos Mendoza",
    "turno": "Vespertino"
  },
  "evaluacion_sensorial": {
    "color_epidermis": "Verde oscuro uniforme",
    "firmeza_pulpa_lb": 24.5,
    "materia_seca_estimada_pct": 23.8,
    "calibre_predominante": "48s",
    "pedunculo_presente_pct": 97.5,
    "olor_extrano": false
  },
  "defectos_detectados": [
    { "tipo_defecto": "Rozadura por rama (Russeting)", "severidad": "Leve", "porcentaje_afectado": 2.4 }
  ],
  "monitoreo_temperatura_caja": [
    { "zona_contenedor": "Frente (cerca de difusor)", "tarima": "T-01", "temperatura_c": 5.4 },
    { "zona_contenedor": "Centro", "tarima": "T-04", "temperatura_c": 5.9 },
    { "zona_contenedor": "Fondo (puertas)", "tarima": "T-08", "temperatura_c": 6.3 }
  ],
  "evidencias_fotograficas": [
    {
      "tipo_evidencia": "Termografo de transporte",
      "url_archivo": "https://storage.trazaagro.mx/recepciones/REC-2026-0104/termografo.jpg",
      "descripcion": "Lectura de sonda al abrir puertas de caja refrigerada"
    }
  ],
  "observaciones_inspector": "Lote recibido dentro del rango térmico de transporte (4.0 a 8.0 °C) y apto para cuarto frío (5.0 a 7.0 °C). Sellos de caja íntegros al arribo."
}
```

### Documento 3: Expediente de Incidente y Retiro / Recall (`expedientes_incidentes`)
Respalda **CU-DOC-06 (PA-07 y PA-08)** y el cumplimiento formal de **`RN-09`**, enlazado 1:1 con `incidentes_bitacora.folio_incidente` en PostgreSQL:

```json
{
  "_id": { "$oid": "65f4e1a2b3c4d5e6f7a8b9f0" },
  "folio_incidente": "INC-2026-0012",
  "codigo_lote_origen": "AGU-P014-260312-01",
  "lotes_afectados": ["AGU-P014-260312-01", "AGU-P014-260312-02"],
  "estado_expediente": "Cerrado",
  "fecha_apertura": "2026-03-13T17:10:00Z",
  "fecha_cierre": "2026-03-20T16:00:00Z",
  "causa_raiz": "Aplicación de insecticida Clorpirifos fuera del periodo de carencia en parcela P014; el lote hermano 02 viajó en la misma unidad refrigerada.",
  "acciones_correctivas": [
    "Suspensión temporal del productor P014 hasta auditoría de buenas prácticas agrícolas.",
    "Retiro completo y destrucción controlada de cajas recuperadas en sucursales.",
    "Lavado y sanitización certificada de la unidad MICH-842-K."
  ],
  "tiendas_notificadas": [
    {
      "codigo_sucursal": "SUC-MTY-04",
      "nombre_comercial": "Supermercados del Norte - Valle",
      "cantidad_enviada_kg": 450.0,
      "cantidad_retirada_kg": 410.0,
      "confirmado": true,
      "fecha_confirmacion": "2026-03-13T18:45:00Z"
    }
  ],
  "linea_tiempo": [
    { "fecha_hora": "2026-03-13T16:45:00Z", "actor": "Laboratorio AgroBio", "descripcion": "Carga de certificado LAB-2026-AGU-0842-V1 con dictamen No Conforme." },
    { "fecha_hora": "2026-03-13T17:10:00Z", "actor": "QA - Laura Méndez", "descripcion": "Bloqueo atómico del lote y lote hermano en PostgreSQL; emisión de alerta a tiendas vía recorrido Neo4j." }
  ],
  "firmas_cierre": {
    "responsable_qa": "Ing. Laura Méndez",
    "aprobacion_gerencia": "Lic. Andrés Salgado"
  }
}
```

## 6. Validaciones e índices críticos

* **Validación `$jsonSchema`:** Exige llaves obligatorias en raíz (`folio_analisis`, `codigo_lote`, `tipo_estudio`, `version`, `es_vigente`, `dictamen_general`, `muestras` en `analisis_laboratorio`; `folio_recepcion`, `codigo_lote`, `inspector`, `evaluacion_sensorial`, `monitoreo_temperatura_caja` en `actas_recepcion`; y `folio_incidente`, `codigo_lote_origen`, `lotes_afectados`, `estado_expediente`, `fecha_apertura`, `linea_tiempo` en `expedientes_incidentes`, exigiendo `causa_raiz`, `acciones_correctivas` y `firmas_cierre` para pasar a `"Cerrado"` según `RN-09`).
* **Índices en `analisis_laboratorio`:**
  * `{ codigo_lote: 1, tipo_estudio: 1 }` con `{ unique: true, partialFilterExpression: { es_vigente: true } }` (candado de única versión vigente por estudio).
  * `{ codigo_lote: 1, es_vigente: 1, "muestras.determinaciones.conforme": 1 }` (acelera **PA-03** con `$elemMatch`).
  * `{ codigo_lote: 1, tipo_estudio: 1, version: -1 }` (acelera **PA-04** para historial).
  * `{ folio_analisis: 1 }` con `{ unique: true }`.
* **Índices en `actas_recepcion`:**
  * `{ folio_recepcion: 1 }` con `{ unique: true }` (relación 1:1 con PostgreSQL) y `{ codigo_lote: 1 }`.
* **Índices en `expedientes_incidentes`:**
  * `{ folio_incidente: 1 }` con `{ unique: true }` (relación 1:1 con `incidentes_bitacora` en PostgreSQL), `{ estado_expediente: 1, fecha_apertura: -1 }` y `{ lotes_afectados: 1 }` (multikey).
