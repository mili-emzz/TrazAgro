// ============================================================================
// PROYECTO: TrazaAgro - Sistema de Trazabilidad de Alimentos Frescos
// ENTREGABLE 4: Implementación de la Base de Datos Documental (MongoDB)
// ARCHIVO: 03_queries_and_tests.js (Consultas representativas y pruebas de validación)
// ============================================================================

const db = db.getSiblingDB("trazaagro");

print("=== PARTE 1: CONSULTAS REPRESENTATIVAS DEL MODELO DOCUMENTAL ===");

// 1.1 PA-03: Detectar análisis vigentes con determinaciones fuera de norma ($elemMatch)
print("\n[Consulta 1.1 - PA-03] Determinaciones vigentes fuera de norma (conforme: false):");
const noConformes = db.analisis_laboratorio.find(
  {
    es_vigente: true,
    muestras: {
      $elemMatch: {
        determinaciones: {
          $elemMatch: { conforme: false }
        }
      }
    }
  },
  {
    _id: 0,
    folio_analisis: 1,
    codigo_lote: 1,
    tipo_estudio: 1,
    dictamen_general: 1,
    "laboratorio.nombre": 1,
    "muestras.determinaciones": 1
  }
).toArray();
printjson(noConformes);

// 1.2 PA-04: Auditar historial completo de versiones (V1 y V2) de un lote
print("\n[Consulta 1.2 - PA-04] Historial de versiones del lote AGU-P018-260314-01:");
const historialVersiones = db.analisis_laboratorio.find(
  {
    codigo_lote: "AGU-P018-260314-01",
    tipo_estudio: "Residuos de Plaguicidas"
  },
  {
    _id: 0,
    folio_analisis: 1,
    version: 1,
    es_vigente: 1,
    dictamen_general: 1,
    folio_reemplazado: 1,
    motivo_enmienda: 1
  }
).sort({ version: -1 }).toArray();
printjson(historialVersiones);

// 1.3 PA-06: Consultar acta física de recepción del lote con ruptura de cadena de frío
print("\n[Consulta 1.3 - PA-06] Acta física de recepción REC-2026-0107 (Ruptura térmica RN-07):");
const actaFrio = db.actas_recepcion.findOne(
  { folio_recepcion: "REC-2026-0107" },
  {
    _id: 0,
    folio_recepcion: 1,
    codigo_lote: 1,
    "inspector.nombre": 1,
    monitoreo_temperatura_caja: 1,
    defectos_detectados: 1,
    observaciones_inspector: 1
  }
);
printjson(actaFrio);

// 1.4 Agregación sobre expedientes_incidentes: Efectividad de retiro (Recall) en kg
print("\n[Consulta 1.4 - PA-07] Efectividad de recuperación de kilogramos en Recall INC-2026-0012:");
const resumenRecall = db.expedientes_incidentes.aggregate([
  { $match: { folio_incidente: "INC-2026-0012" } },
  { $unwind: "$tiendas_notificadas" },
  {
    $group: {
      _id: "$folio_incidente",
      estado_expediente: { $first: "$estado_expediente" },
      total_enviado_kg: { $sum: "$tiendas_notificadas.cantidad_enviada_kg" },
      total_retirado_kg: { $sum: "$tiendas_notificadas.cantidad_retirada_kg" },
      sucursales_notificadas: { $sum: 1 }
    }
  },
  {
    $project: {
      _id: 0,
      folio_incidente: "$_id",
      estado_expediente: 1,
      sucursales_notificadas: 1,
      total_enviado_kg: 1,
      total_retirado_kg: 1,
      porcentaje_recuperacion: {
        $round: [
          { $multiply: [{ $divide: ["$total_retirado_kg", "$total_enviado_kg"] }, 100] },
          2
        ]
      }
    }
  }
]).toArray();
printjson(resumenRecall);

// ============================================================================
// PARTE 2: PRUEBAS AUTOMATIZADAS DE DOCUMENTOS VÁLIDOS E INVÁLIDOS ($jsonSchema e Índices)
// ============================================================================
print("\n=== PARTE 2: PRUEBAS DE VALIDACIÓN ($jsonSchema) Y CANDADOS DE INTEGRIDAD ===");

function assertThrowsCode(nombrePrueba, codigoEsperado, fn) {
  try {
    fn();
    throw new Error("FALLO [" + nombrePrueba + "]: MongoDB permitió un documento inválido.");
  } catch (err) {
    if (err.code === codigoEsperado) {
      print("EXITO [" + nombrePrueba + "]: Rechazado correctamente con código " + err.code + " (" + (err.codeName || err.name) + ").");
    } else {
      throw new Error(
        "FALLO [" + nombrePrueba + "]: Se esperaba código " + codigoEsperado +
        " pero se obtuvo " + err.code + " -> " + err.message
      );
    }
  }
}

// Prueba 2.1 (Caso positivo): Inserción de documento polimórfico válido (Materia Seca) y limpieza posterior
const docValido = {
  folio_analisis: "LAB-2026-AGU-TEST-V1",
  codigo_lote: "AGU-P014-260318-01",
  tipo_estudio: "Materia Seca",
  fecha_muestreo: ISODate("2026-03-18T09:00:00Z"),
  fecha_emision: ISODate("2026-03-18T14:00:00Z"),
  version: Int32(1),
  es_vigente: true,
  folio_reemplazado: null,
  motivo_enmienda: null,
  dictamen_general: "Conforme",
  laboratorio: {
    nombre: "Centro Analítico Fitosanitario de Occidente S.C.",
    acreditacion_iso: "EMA-LA-0412-2025"
  },
  muestras: [
    {
      identificador_muestra: "M-MS-01",
      determinaciones: [
        {
          parametro: "Materia Seca",
          resultado_numerico: 23.5,
          unidad: "%",
          limite_minimo: 21.0,
          conforme: true
        }
      ]
    }
  ]
};
db.analisis_laboratorio.insertOne(docValido);
db.analisis_laboratorio.deleteOne({ folio_analisis: "LAB-2026-AGU-TEST-V1" });
print("EXITO [Prueba 2.1 - Documento válido]: Inserción polimórfica de Materia Seca aceptada y limpiada.");

// Prueba 2.2 (Negativa - $jsonSchema): Análisis con tipo_estudio fuera del enum y sin muestras
assertThrowsCode("Prueba 2.2 - tipo_estudio inválido y muestras vacías", 121, () => {
  db.analisis_laboratorio.insertOne({
    folio_analisis: "LAB-2026-ERR-01",
    codigo_lote: "AGU-P014-260318-01",
    tipo_estudio: "Estudio Inventado",
    fecha_muestreo: ISODate("2026-03-18T09:00:00Z"),
    version: Int32(1),
    es_vigente: true,
    dictamen_general: "Conforme",
    laboratorio: { nombre: "Lab X", acreditacion_iso: "ISO-001" },
    muestras: []
  });
});

// Prueba 2.3 (Negativa - $jsonSchema): Determinación sin campo booleano 'conforme'
assertThrowsCode("Prueba 2.3 - Determinación sin campo conforme", 121, () => {
  db.analisis_laboratorio.insertOne({
    folio_analisis: "LAB-2026-ERR-02",
    codigo_lote: "AGU-P014-260318-01",
    tipo_estudio: "Residuos de Plaguicidas",
    fecha_muestreo: ISODate("2026-03-18T09:00:00Z"),
    version: Int32(1),
    es_vigente: true,
    dictamen_general: "Conforme",
    laboratorio: { nombre: "Lab X", acreditacion_iso: "ISO-001" },
    muestras: [
      {
        identificador_muestra: "M-01",
        determinaciones: [
          { molecula: "Clorpirifos", resultado_mg_kg: 0.001 }
        ]
      }
    ]
  });
});

// Prueba 2.4 (Negativa - Índice único parcial RN-05): Dos versiones vigentes para el mismo lote y estudio
assertThrowsCode("Prueba 2.4 - Doble versión vigente (RN-05)", 11000, () => {
  db.analisis_laboratorio.insertOne({
    folio_analisis: "LAB-2026-AGU-0910-V3-CONFLICTO",
    codigo_lote: "AGU-P018-260314-01",
    tipo_estudio: "Residuos de Plaguicidas",
    fecha_muestreo: ISODate("2026-03-14T09:15:00Z"),
    version: Int32(3),
    es_vigente: true,
    dictamen_general: "Conforme",
    laboratorio: { nombre: "Lab AgroBio S.A. de C.V.", acreditacion_iso: "EMA-ISA-17025-2024" },
    muestras: [
      {
        identificador_muestra: "M-01C",
        determinaciones: [{ molecula: "Abamectina", conforme: true }]
      }
    ]
  });
});

// Prueba 2.5 (Negativa - $jsonSchema): Acta de recepción con temperatura absurda (85.0 °C)
assertThrowsCode("Prueba 2.5 - Temperatura fuera de rango físico en acta", 121, () => {
  db.actas_recepcion.insertOne({
    folio_recepcion: "REC-2026-ERR-99",
    codigo_lote: "AGU-P014-260318-01",
    fecha_hora_inspeccion: ISODate("2026-03-18T15:00:00Z"),
    inspector: { usuario_id: "USR-01", nombre: "Inspector Test" },
    evaluacion_sensorial: { color_epidermis: "Verde", olor_extrano: false },
    monitoreo_temperatura_caja: [
      { zona_contenedor: "Centro", temperatura_c: 85.0 }
    ]
  });
});

// Prueba 2.6 (Negativa - $jsonSchema RN-09): Cerrar expediente de incidente sin causa raíz ni firmas
assertThrowsCode("Prueba 2.6 - Cierre de expediente sin causa_raiz ni firmas (RN-09)", 121, () => {
  db.expedientes_incidentes.insertOne({
    folio_incidente: "INC-2026-ERR-99",
    codigo_lote_origen: "AGU-P015-260315-01",
    lotes_afectados: ["AGU-P015-260315-01"],
    estado_expediente: "Cerrado",
    fecha_apertura: ISODate("2026-03-18T10:00:00Z"),
    fecha_cierre: ISODate("2026-03-18T12:00:00Z"),
    causa_raiz: null,
    acciones_correctivas: [],
    linea_tiempo: [
      { fecha_hora: ISODate("2026-03-18T10:00:00Z"), actor: "QA", descripcion: "Intento de cierre sin evidencia." }
    ],
    firmas_cierre: null
  });
});

print("\n=== TODAS LAS CONSULTAS Y PRUEBAS DOCUMENTALES FINALIZARON CON ÉXITO ===");
