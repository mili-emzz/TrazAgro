// ============================================================================
// PROYECTO: TrazaAgro - Sistema de Trazabilidad de Alimentos Frescos
// ENTREGABLE 4: Implementación de la Base de Datos Documental (MongoDB)
// ARCHIVO: 01_setup_collections.js (Colecciones, Validadores $jsonSchema e Índices)
// ============================================================================

const db = db.getSiblingDB("trazaagro");

print("=== Inicializando base documental TrazaAgro ===");

// Limpieza idempotente para reconstrucción desde cero
db.analisis_laboratorio.drop();
db.actas_recepcion.drop();
db.expedientes_incidentes.drop();

// ============================================================================
// 1. COLECCIÓN: analisis_laboratorio
// Certificados químicos y microbiológicos polimórficos con versionado inmutable (RN-05)
// ============================================================================
db.createCollection("analisis_laboratorio", {
  validationLevel: "strict",
  validationAction: "error",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      title: "Esquema de Certificados de Análisis de Laboratorio",
      required: [
        "folio_analisis",
        "codigo_lote",
        "tipo_estudio",
        "fecha_muestreo",
        "version",
        "es_vigente",
        "dictamen_general",
        "laboratorio",
        "muestras"
      ],
      properties: {
        folio_analisis: {
          bsonType: "string",
          minLength: 5,
          description: "Identificador único oficial del certificado (incluye sufijo -V1, -V2)."
        },
        codigo_lote: {
          bsonType: "string",
          minLength: 5,
          description: "Llave natural puente hacia la tabla lotes en PostgreSQL y :Lote en Neo4j."
        },
        tipo_estudio: {
          enum: ["Residuos de Plaguicidas", "Microbiologico", "Materia Seca"],
          description: "Clasificación del estudio emitido por el laboratorio."
        },
        fecha_muestreo: {
          bsonType: "date",
          description: "Fecha y hora ISO en que se recolectó la muestra."
        },
        fecha_emision: {
          bsonType: ["date", "null"],
          description: "Fecha y hora ISO de emisión del certificado."
        },
        version: {
          bsonType: "int",
          minimum: 1,
          description: "Número secuencial de versión inmutable (>= 1)."
        },
        es_vigente: {
          bsonType: "bool",
          description: "Indica si es la versión activa actual del estudio para el lote."
        },
        folio_reemplazado: {
          bsonType: ["string", "null"],
          description: "Folio de la versión anterior cuando existe una enmienda."
        },
        motivo_enmienda: {
          bsonType: ["string", "null"],
          description: "Justificación técnica obligatoria cuando version > 1."
        },
        dictamen_general: {
          enum: ["Conforme", "No Conforme"],
          description: "Resultado consolidado del certificado."
        },
        laboratorio: {
          bsonType: "object",
          required: ["nombre", "acreditacion_iso"],
          properties: {
            nombre: { bsonType: "string", minLength: 3 },
            acreditacion_iso: { bsonType: "string", minLength: 3 },
            contacto_correo: { bsonType: ["string", "null"] }
          }
        },
        firma_digital: {
          bsonType: "object",
          required: ["responsable_signatario", "hash_integridad"],
          properties: {
            responsable_signatario: { bsonType: "string" },
            cedula_profesional: { bsonType: ["string", "null"] },
            hash_integridad: { bsonType: "string" }
          }
        },
        muestras: {
          bsonType: "array",
          minItems: 1,
          items: {
            bsonType: "object",
            required: ["identificador_muestra", "determinaciones"],
            properties: {
              identificador_muestra: { bsonType: "string" },
              parte_analizada: { bsonType: "string" },
              peso_gramos: { bsonType: ["double", "int", "decimal"], minimum: 1 },
              determinaciones: {
                bsonType: "array",
                minItems: 1,
                items: {
                  bsonType: "object",
                  required: ["conforme"],
                  anyOf: [
                    { required: ["molecula"] },
                    { required: ["parametro"] }
                  ],
                  properties: {
                    molecula: { bsonType: "string" },
                    parametro: { bsonType: "string" },
                    metodo_ensayo: { bsonType: "string" },
                    unidad: { bsonType: "string" },
                    conforme: {
                      bsonType: "bool",
                      description: "Bandera obligatoria para auditoría con $elemMatch."
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
});

// Índices de analisis_laboratorio
// 1. Candado físico de versión vigente única por lote y tipo de estudio (RN-05 / PA-02)
db.analisis_laboratorio.createIndex(
  { codigo_lote: 1, tipo_estudio: 1 },
  {
    unique: true,
    partialFilterExpression: { es_vigente: true },
    name: "uq_analisis_lote_estudio_vigente"
  }
);

// 2. Índice multikey para auditoría rápida de determinaciones fuera de norma (PA-03)
db.analisis_laboratorio.createIndex(
  { codigo_lote: 1, es_vigente: 1, "muestras.determinaciones.conforme": 1 },
  { name: "idx_analisis_auditoria_parametros" }
);

// 3. Índice de historial cronológico de versiones (PA-04)
db.analisis_laboratorio.createIndex(
  { codigo_lote: 1, tipo_estudio: 1, version: -1 },
  { name: "idx_analisis_historial_versiones" }
);

// 4. Índice único de folio oficial (PA-01)
db.analisis_laboratorio.createIndex(
  { folio_analisis: 1 },
  { unique: true, name: "uq_analisis_folio" }
);

print("OK: Colección analisis_laboratorio e índices creados.");

// ============================================================================
// 2. COLECCIÓN: actas_recepcion
// Inspecciones físicas, sensoriales, lecturas térmicas y evidencias fotográficas en CEDIS
// ============================================================================
db.createCollection("actas_recepcion", {
  validationLevel: "strict",
  validationAction: "error",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      title: "Esquema de Actas de Inspección en Recepción CEDIS",
      required: [
        "folio_recepcion",
        "codigo_lote",
        "fecha_hora_inspeccion",
        "inspector",
        "evaluacion_sensorial",
        "monitoreo_temperatura_caja"
      ],
      properties: {
        folio_recepcion: {
          bsonType: "string",
          minLength: 5,
          description: "Llave puente 1:1 con recepciones_cedis.folio_recepcion en PostgreSQL."
        },
        codigo_lote: {
          bsonType: "string",
          minLength: 5
        },
        fecha_hora_inspeccion: {
          bsonType: "date"
        },
        inspector: {
          bsonType: "object",
          required: ["usuario_id", "nombre"],
          properties: {
            usuario_id: { bsonType: "string" },
            nombre: { bsonType: "string" },
            turno: { bsonType: "string" }
          }
        },
        evaluacion_sensorial: {
          bsonType: "object",
          required: ["color_epidermis", "olor_extrano"],
          properties: {
            color_epidermis: { bsonType: "string" },
            firmeza_pulpa_lb: { bsonType: ["double", "int", "decimal"], minimum: 0 },
            materia_seca_estimada_pct: { bsonType: ["double", "int", "decimal"], minimum: 0, maximum: 100 },
            calibre_predominante: { bsonType: "string" },
            pedunculo_presente_pct: { bsonType: ["double", "int", "decimal"], minimum: 0, maximum: 100 },
            olor_extrano: { bsonType: "bool" }
          }
        },
        defectos_detectados: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["tipo_defecto", "porcentaje_afectado"],
            properties: {
              tipo_defecto: { bsonType: "string" },
              severidad: { enum: ["Leve", "Moderada", "Grave"] },
              porcentaje_afectado: {
                bsonType: ["double", "int", "decimal"],
                minimum: 0,
                maximum: 100
              }
            }
          }
        },
        monitoreo_temperatura_caja: {
          bsonType: "array",
          minItems: 1,
          items: {
            bsonType: "object",
            required: ["zona_contenedor", "temperatura_c"],
            properties: {
              zona_contenedor: { bsonType: "string" },
              tarima: { bsonType: "string" },
              temperatura_c: {
                bsonType: ["double", "int", "decimal"],
                minimum: -10.0,
                maximum: 45.0,
                description: "Rango físico válido de lectura térmica en grados Celsius."
              }
            }
          }
        },
        evidencias_fotograficas: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["tipo_evidencia", "url_archivo"],
            properties: {
              tipo_evidencia: { bsonType: "string" },
              url_archivo: { bsonType: "string" },
              descripcion: { bsonType: "string" }
            }
          }
        },
        observaciones_inspector: {
          bsonType: ["string", "null"]
        }
      }
    }
  }
});

// Índices de actas_recepcion (PA-05 / PA-06)
db.actas_recepcion.createIndex(
  { folio_recepcion: 1 },
  { unique: true, name: "uq_actas_folio_recepcion" }
);

db.actas_recepcion.createIndex(
  { codigo_lote: 1 },
  { name: "idx_actas_codigo_lote" }
);

print("OK: Colección actas_recepcion e índices creados.");

// ============================================================================
// 3. COLECCIÓN: expedientes_incidentes
// Expedientes vivos de Recall y auditoría con regla condicional de cierre (RN-09)
// ============================================================================
db.createCollection("expedientes_incidentes", {
  validationLevel: "strict",
  validationAction: "error",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      title: "Esquema de Expedientes de Incidentes y Retiro (Recall)",
      required: [
        "folio_incidente",
        "codigo_lote_origen",
        "lotes_afectados",
        "estado_expediente",
        "fecha_apertura",
        "linea_tiempo"
      ],
      properties: {
        folio_incidente: {
          bsonType: "string",
          minLength: 5,
          description: "Llave puente 1:1 con incidentes_bitacora.folio_incidente en PostgreSQL."
        },
        codigo_lote_origen: {
          bsonType: "string",
          minLength: 5
        },
        lotes_afectados: {
          bsonType: "array",
          minItems: 1,
          items: { bsonType: "string" }
        },
        estado_expediente: {
          enum: ["Abierto", "En investigacion", "Cerrado"]
        },
        fecha_apertura: {
          bsonType: "date"
        },
        fecha_cierre: {
          bsonType: ["date", "null"]
        },
        causa_raiz: {
          bsonType: ["string", "null"]
        },
        acciones_correctivas: {
          bsonType: "array",
          items: { bsonType: "string", minLength: 5 }
        },
        tiendas_notificadas: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["codigo_sucursal", "nombre_comercial", "cantidad_enviada_kg", "confirmado"],
            properties: {
              codigo_sucursal: { bsonType: "string" },
              nombre_comercial: { bsonType: "string" },
              cantidad_enviada_kg: { bsonType: ["double", "int", "decimal"], minimum: 0 },
              cantidad_retirada_kg: { bsonType: ["double", "int", "decimal"], minimum: 0 },
              confirmado: { bsonType: "bool" },
              fecha_confirmacion: { bsonType: ["date", "null"] }
            }
          }
        },
        linea_tiempo: {
          bsonType: "array",
          minItems: 1,
          items: {
            bsonType: "object",
            required: ["fecha_hora", "actor", "descripcion"],
            properties: {
              fecha_hora: { bsonType: "date" },
              actor: { bsonType: "string" },
              descripcion: { bsonType: "string" }
            }
          }
        },
        firmas_cierre: {
          bsonType: ["object", "null"],
          properties: {
            responsable_qa: { bsonType: "string", minLength: 3 },
            aprobacion_gerencia: { bsonType: "string", minLength: 3 }
          }
        }
      },
      // Regla condicional RN-09: Solo permite estado "Cerrado" si tiene causa_raiz,
      // al menos una acción correctiva y ambas firmas de cierre (QA y Gerencia).
      anyOf: [
        {
          properties: {
            estado_expediente: { enum: ["Abierto", "En investigacion"] }
          }
        },
        {
          required: ["causa_raiz", "acciones_correctivas", "firmas_cierre", "fecha_cierre"],
          properties: {
            estado_expediente: { enum: ["Cerrado"] },
            causa_raiz: { bsonType: "string", minLength: 10 },
            acciones_correctivas: { bsonType: "array", minItems: 1 },
            fecha_cierre: { bsonType: "date" },
            firmas_cierre: {
              bsonType: "object",
              required: ["responsable_qa", "aprobacion_gerencia"]
            }
          }
        }
      ]
    }
  }
});

// Índices de expedientes_incidentes (PA-07 / PA-08)
db.expedientes_incidentes.createIndex(
  { folio_incidente: 1 },
  { unique: true, name: "uq_expedientes_folio_incidente" }
);

db.expedientes_incidentes.createIndex(
  { estado_expediente: 1, fecha_apertura: -1 },
  { name: "idx_expedientes_estado_fecha" }
);

db.expedientes_incidentes.createIndex(
  { lotes_afectados: 1 },
  { name: "idx_expedientes_lotes_afectados" }
);

print("OK: Colección expedientes_incidentes e índices creados.");

// ============================================================================
// 4. USUARIO DEDICADO DE APLICACIÓN CON PRIVILEGIOS MÍNIMOS (PoLP)
// ============================================================================
try {
  db.dropUser("trazaagro_app");
} catch (e) {
  // Ignorar si el usuario aún no existe
}

db.createUser({
  user: "trazaagro_app",
  pwd: "trazaagro_app_pass",
  roles: [
    { role: "readWrite", db: "trazaagro" }
  ]
});
print("OK: Usuario de aplicación trazaagro_app creado con rol readWrite.");

print("=== Configuración documental completada con éxito ===");
