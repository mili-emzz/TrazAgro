// ============================================================================
// PROYECTO: TrazaAgro - Sistema de Trazabilidad de Alimentos Frescos
// ENTREGABLE 4: Implementación de la Base de Datos Documental (MongoDB)
// ARCHIVO: 02_seed_data.js (Carga reproducible de documentos sincronizados con SQL)
// ============================================================================

const db = db.getSiblingDB("trazaagro");

print("=== Cargando datos semilla documentales de TrazaAgro ===");

// Limpieza previa conservando validadores e índices
db.analisis_laboratorio.deleteMany({});
db.actas_recepcion.deleteMany({});
db.expedientes_incidentes.deleteMany({});

// ============================================================================
// 1. ANÁLISIS DE LABORATORIO (5 certificados: polimórficos y versionado V1/V2)
// ============================================================================
db.analisis_laboratorio.insertMany([
  {
    folio_analisis: "LAB-2026-AGU-0842-V1",
    codigo_lote: "AGU-P014-260312-01",
    tipo_estudio: "Residuos de Plaguicidas",
    fecha_muestreo: ISODate("2026-03-12T10:30:00Z"),
    fecha_emision: ISODate("2026-03-13T16:45:00Z"),
    version: Int32(1),
    es_vigente: true,
    folio_reemplazado: null,
    motivo_enmienda: null,
    dictamen_general: "No Conforme",
    laboratorio: {
      nombre: "Lab AgroBio S.A. de C.V.",
      acreditacion_iso: "EMA-ISA-17025-2024",
      contacto_correo: "certificados@agrobio.com.mx"
    },
    firma_digital: {
      responsable_signatario: "Q.F.B. Elena Rostova",
      cedula_profesional: "7845129",
      hash_integridad: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    muestras: [
      {
        identificador_muestra: "M-01",
        parte_analizada: "Pulpa y epidermis entera",
        peso_gramos: 500,
        determinaciones: [
          {
            molecula: "Clorpirifos",
            metodo_ensayo: "AOAC 2007.01 (QuEChERS / GC-MS/MS)",
            resultado_mg_kg: 0.08,
            unidad: "mg/kg",
            limite_maximo_mg_kg: 0.01,
            conforme: false
          },
          {
            molecula: "Malation",
            metodo_ensayo: "AOAC 2007.01 (QuEChERS / GC-MS/MS)",
            resultado_mg_kg: 0.002,
            unidad: "mg/kg",
            limite_maximo_mg_kg: 0.05,
            conforme: true
          }
        ]
      }
    ]
  },
  {
    folio_analisis: "LAB-2026-AGU-0845-V1",
    codigo_lote: "AGU-P014-260312-01",
    tipo_estudio: "Microbiologico",
    fecha_muestreo: ISODate("2026-03-12T10:30:00Z"),
    fecha_emision: ISODate("2026-03-13T07:30:00Z"),
    version: Int32(1),
    es_vigente: true,
    folio_reemplazado: null,
    motivo_enmienda: null,
    dictamen_general: "Conforme",
    laboratorio: {
      nombre: "Centro Analítico Fitosanitario de Occidente S.C.",
      acreditacion_iso: "EMA-LA-0412-2025",
      contacto_correo: "resultados@cafo.mx"
    },
    firma_digital: {
      responsable_signatario: "M. en C. Roberto Villaseñor",
      cedula_profesional: "4519082",
      hash_integridad: "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
    },
    muestras: [
      {
        identificador_muestra: "M-BIO-01",
        parte_analizada: "Superficie epidérmica y pulpa",
        peso_gramos: 250,
        determinaciones: [
          {
            parametro: "Salmonella spp.",
            metodo_ensayo: "NOM-210-SSA1-2014 Apéndice A",
            resultado_cualitativo: "Ausente en 25g",
            unidad: "Presencia/Ausencia",
            conforme: true
          },
          {
            parametro: "Listeria monocytogenes",
            metodo_ensayo: "NOM-210-SSA1-2014 Apéndice C",
            resultado_cualitativo: "Ausente en 25g",
            unidad: "Presencia/Ausencia",
            conforme: true
          },
          {
            parametro: "Escherichia coli",
            metodo_ensayo: "NOM-210-SSA1-2014",
            resultado_numerico: 10,
            unidad: "UFC/g",
            limite_maximo: 100,
            conforme: true
          },
          {
            parametro: "Porcentaje de Materia Seca",
            metodo_ensayo: "NMX-FF-016-SCFI-2016 (Horno de secado)",
            resultado_numerico: 24.2,
            unidad: "%",
            limite_minimo: 21.0,
            conforme: true
          }
        ]
      }
    ]
  },
  {
    folio_analisis: "LAB-2026-AGU-0910-V1",
    codigo_lote: "AGU-P018-260314-01",
    tipo_estudio: "Residuos de Plaguicidas",
    fecha_muestreo: ISODate("2026-03-14T09:15:00Z"),
    fecha_emision: ISODate("2026-03-14T20:00:00Z"),
    version: Int32(1),
    es_vigente: false,
    folio_reemplazado: null,
    motivo_enmienda: null,
    dictamen_general: "No Conforme",
    laboratorio: {
      nombre: "Lab AgroBio S.A. de C.V.",
      acreditacion_iso: "EMA-ISA-17025-2024",
      contacto_correo: "certificados@agrobio.com.mx"
    },
    firma_digital: {
      responsable_signatario: "Q.F.B. Elena Rostova",
      cedula_profesional: "7845129",
      hash_integridad: "7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730"
    },
    muestras: [
      {
        identificador_muestra: "M-01A",
        parte_analizada: "Pulpa y epidermis entera",
        peso_gramos: 500,
        determinaciones: [
          {
            molecula: "Abamectina",
            metodo_ensayo: "AOAC 2007.01 (QuEChERS / LC-MS/MS)",
            resultado_mg_kg: 0.025,
            unidad: "mg/kg",
            limite_maximo_mg_kg: 0.02,
            conforme: false
          }
        ]
      }
    ]
  },
  {
    folio_analisis: "LAB-2026-AGU-0910-V2",
    codigo_lote: "AGU-P018-260314-01",
    tipo_estudio: "Residuos de Plaguicidas",
    fecha_muestreo: ISODate("2026-03-14T09:15:00Z"),
    fecha_emision: ISODate("2026-03-15T11:20:00Z"),
    version: Int32(2),
    es_vigente: true,
    folio_reemplazado: "LAB-2026-AGU-0910-V1",
    motivo_enmienda: "Reanálisis de contramuestra M-01B por ajuste de curva de calibración en detector MS/MS.",
    dictamen_general: "Conforme",
    laboratorio: {
      nombre: "Lab AgroBio S.A. de C.V.",
      acreditacion_iso: "EMA-ISA-17025-2024",
      contacto_correo: "certificados@agrobio.com.mx"
    },
    firma_digital: {
      responsable_signatario: "Q.F.B. Elena Rostova",
      cedula_profesional: "7845129",
      hash_integridad: "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4"
    },
    muestras: [
      {
        identificador_muestra: "M-01B",
        parte_analizada: "Pulpa y epidermis entera (Contramuestra sellada)",
        peso_gramos: 500,
        determinaciones: [
          {
            molecula: "Abamectina",
            metodo_ensayo: "AOAC 2007.01 (QuEChERS / LC-MS/MS)",
            resultado_mg_kg: 0.008,
            unidad: "mg/kg",
            limite_maximo_mg_kg: 0.02,
            conforme: true
          }
        ]
      }
    ]
  },
  {
    folio_analisis: "LAB-2026-AGU-0925-V1",
    codigo_lote: "AGU-P018-260316-01",
    tipo_estudio: "Residuos de Plaguicidas",
    fecha_muestreo: ISODate("2026-03-16T08:00:00Z"),
    fecha_emision: ISODate("2026-03-16T19:15:00Z"),
    version: Int32(1),
    es_vigente: true,
    folio_reemplazado: null,
    motivo_enmienda: null,
    dictamen_general: "Conforme",
    laboratorio: {
      nombre: "Lab AgroBio S.A. de C.V.",
      acreditacion_iso: "EMA-ISA-17025-2024",
      contacto_correo: "certificados@agrobio.com.mx"
    },
    firma_digital: {
      responsable_signatario: "Q.F.B. Elena Rostova",
      cedula_profesional: "7845129",
      hash_integridad: "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a"
    },
    muestras: [
      {
        identificador_muestra: "M-05",
        parte_analizada: "Pulpa y epidermis entera",
        peso_gramos: 500,
        determinaciones: [
          {
            molecula: "Clorpirifos",
            metodo_ensayo: "AOAC 2007.01 (QuEChERS / GC-MS/MS)",
            resultado_mg_kg: 0.001,
            unidad: "mg/kg",
            limite_maximo_mg_kg: 0.01,
            conforme: true
          },
          {
            molecula: "Abamectina",
            metodo_ensayo: "AOAC 2007.01 (QuEChERS / LC-MS/MS)",
            resultado_mg_kg: 0.004,
            unidad: "mg/kg",
            limite_maximo_mg_kg: 0.02,
            conforme: true
          }
        ]
      }
    ]
  }
]);

print("OK: 5 certificados insertados en analisis_laboratorio.");

// ============================================================================
// 2. ACTAS DE RECEPCIÓN EN CEDIS (5 actas 1:1 con recepciones_cedis de SQL)
// ============================================================================
db.actas_recepcion.insertMany([
  {
    folio_recepcion: "REC-2026-0104",
    codigo_lote: "AGU-P014-260312-01",
    fecha_hora_inspeccion: ISODate("2026-03-12T18:30:00Z"),
    inspector: {
      usuario_id: "USR-REC-08",
      nombre: "Carlos Mendoza",
      turno: "Vespertino"
    },
    evaluacion_sensorial: {
      color_epidermis: "Verde oscuro uniforme",
      firmeza_pulpa_lb: 24.5,
      materia_seca_estimada_pct: 23.8,
      calibre_predominante: "48s",
      pedunculo_presente_pct: 97.5,
      olor_extrano: false
    },
    defectos_detectados: [
      { tipo_defecto: "Rozadura por rama (Russeting)", severidad: "Leve", porcentaje_afectado: 2.4 },
      { tipo_defecto: "Lenticelosis superficial", severidad: "Leve", porcentaje_afectado: 1.1 }
    ],
    monitoreo_temperatura_caja: [
      { zona_contenedor: "Frente (cerca de difusor)", tarima: "T-01", temperatura_c: 5.4 },
      { zona_contenedor: "Centro", tarima: "T-04", temperatura_c: 5.9 },
      { zona_contenedor: "Fondo (puertas)", tarima: "T-08", temperatura_c: 6.3 }
    ],
    evidencias_fotograficas: [
      {
        tipo_evidencia: "Termografo de transporte",
        url_archivo: "https://storage.trazaagro.mx/recepciones/REC-2026-0104/termografo.jpg",
        descripcion: "Lectura de sonda al abrir puertas de caja refrigerada"
      },
      {
        tipo_evidencia: "Muestreo de cajas",
        url_archivo: "https://storage.trazaagro.mx/recepciones/REC-2026-0104/muestra-calibre.jpg",
        descripcion: "Revisión visual de calibre 48s y estado de pedúnculo"
      }
    ],
    observaciones_inspector: "Lote recibido dentro del rango térmico de transporte (4.0 a 8.0 °C) y apto para cuarto frío CF-02."
  },
  {
    folio_recepcion: "REC-2026-0105",
    codigo_lote: "AGU-P014-260312-02",
    fecha_hora_inspeccion: ISODate("2026-03-12T18:50:00Z"),
    inspector: {
      usuario_id: "USR-REC-08",
      nombre: "Carlos Mendoza",
      turno: "Vespertino"
    },
    evaluacion_sensorial: {
      color_epidermis: "Verde oscuro brillante",
      firmeza_pulpa_lb: 25.0,
      materia_seca_estimada_pct: 24.0,
      calibre_predominante: "48s",
      pedunculo_presente_pct: 98.0,
      olor_extrano: false
    },
    defectos_detectados: [
      { tipo_defecto: "Rozadura por rama (Russeting)", severidad: "Leve", porcentaje_afectado: 1.8 }
    ],
    monitoreo_temperatura_caja: [
      { zona_contenedor: "Frente (cerca de difusor)", tarima: "T-09", temperatura_c: 5.8 },
      { zona_contenedor: "Centro", tarima: "T-11", temperatura_c: 6.1 },
      { zona_contenedor: "Fondo (puertas)", tarima: "T-13", temperatura_c: 6.4 }
    ],
    evidencias_fotograficas: [
      {
        tipo_evidencia: "Estiba compartida",
        url_archivo: "https://storage.trazaagro.mx/recepciones/REC-2026-0105/estiba-cf02.jpg",
        descripcion: "Ingreso a cámara CF-02 junto a tarimas del lote AGU-P014-260312-01"
      }
    ],
    observaciones_inspector: "Lote hermano transportado en la misma unidad MICH-842-K y estibado en cuarto frío CF-02."
  },
  {
    folio_recepcion: "REC-2026-0106",
    codigo_lote: "AGU-P018-260314-01",
    fecha_hora_inspeccion: ISODate("2026-03-14T17:35:00Z"),
    inspector: {
      usuario_id: "USR-REC-12",
      nombre: "Sofía Ramírez",
      turno: "Vespertino"
    },
    evaluacion_sensorial: {
      color_epidermis: "Verde oscuro uniforme",
      firmeza_pulpa_lb: 26.2,
      materia_seca_estimada_pct: 25.1,
      calibre_predominante: "36s",
      pedunculo_presente_pct: 99.0,
      olor_extrano: false
    },
    defectos_detectados: [],
    monitoreo_temperatura_caja: [
      { zona_contenedor: "Frente (cerca de difusor)", tarima: "T-01", temperatura_c: 5.2 },
      { zona_contenedor: "Centro", tarima: "T-06", temperatura_c: 5.5 },
      { zona_contenedor: "Fondo (puertas)", tarima: "T-12", temperatura_c: 5.8 }
    ],
    evidencias_fotograficas: [
      {
        tipo_evidencia: "Termografo de transporte",
        url_archivo: "https://storage.trazaagro.mx/recepciones/REC-2026-0106/termografo.jpg",
        descripcion: "Cadena de frío estable en unidad MICH-910-B"
      }
    ],
    observaciones_inspector: "Fruta de calidad exportación sin defectos visibles; asignada a cuarto frío CF-01."
  },
  {
    folio_recepcion: "REC-2026-0107",
    codigo_lote: "AGU-P015-260315-01",
    fecha_hora_inspeccion: ISODate("2026-03-15T16:25:00Z"),
    inspector: {
      usuario_id: "USR-REC-08",
      nombre: "Carlos Mendoza",
      turno: "Vespertino"
    },
    evaluacion_sensorial: {
      color_epidermis: "Verde mate con ligero ablandamiento",
      firmeza_pulpa_lb: 17.8,
      materia_seca_estimada_pct: 24.4,
      calibre_predominante: "60s",
      pedunculo_presente_pct: 91.0,
      olor_extrano: false
    },
    defectos_detectados: [
      { tipo_defecto: "Ablandamiento prematuro por estrés térmico", severidad: "Moderada", porcentaje_afectado: 14.5 }
    ],
    monitoreo_temperatura_caja: [
      { zona_contenedor: "Frente (cerca de difusor)", tarima: "T-01", temperatura_c: 10.8 },
      { zona_contenedor: "Centro", tarima: "T-04", temperatura_c: 11.4 },
      { zona_contenedor: "Fondo (puertas)", tarima: "T-07", temperatura_c: 12.1 }
    ],
    evidencias_fotograficas: [
      {
        tipo_evidencia: "Alarma de termografo",
        url_archivo: "https://storage.trazaagro.mx/recepciones/REC-2026-0107/alarma-termica.jpg",
        descripcion: "Falla en compresor de unidad JAL-405-C; temperatura superó límite de 8.0 °C (RN-07)"
      }
    ],
    observaciones_inspector: "ALERTA RN-07: Ruptura de cadena de frío (11.4 °C promedio). Lote retenido en cuarentena CF-03 para dictamen de QA."
  },
  {
    folio_recepcion: "REC-2026-0108",
    codigo_lote: "AGU-P018-260316-01",
    fecha_hora_inspeccion: ISODate("2026-03-16T15:25:00Z"),
    inspector: {
      usuario_id: "USR-REC-12",
      nombre: "Sofía Ramírez",
      turno: "Vespertino"
    },
    evaluacion_sensorial: {
      color_epidermis: "Verde oscuro uniforme",
      firmeza_pulpa_lb: 25.4,
      materia_seca_estimada_pct: 24.6,
      calibre_predominante: "48s",
      pedunculo_presente_pct: 98.5,
      olor_extrano: false
    },
    defectos_detectados: [],
    monitoreo_temperatura_caja: [
      { zona_contenedor: "Frente (cerca de difusor)", tarima: "T-01", temperatura_c: 5.5 },
      { zona_contenedor: "Centro", tarima: "T-05", temperatura_c: 5.8 },
      { zona_contenedor: "Fondo (puertas)", tarima: "T-09", temperatura_c: 6.1 }
    ],
    evidencias_fotograficas: [],
    observaciones_inspector: "Ingreso conforme en unidad MICH-910-B, estibado en CF-01."
  }
]);

print("OK: 5 actas insertadas en actas_recepcion.");

// ============================================================================
// 3. EXPEDIENTES DE INCIDENTES Y RECALL (2 expedientes: 1 Cerrado y 1 En investigacion)
// ============================================================================
db.expedientes_incidentes.insertMany([
  {
    folio_incidente: "INC-2026-0012",
    codigo_lote_origen: "AGU-P014-260312-01",
    lotes_afectados: ["AGU-P014-260312-01", "AGU-P014-260312-02"],
    estado_expediente: "Cerrado",
    fecha_apertura: ISODate("2026-03-13T17:10:00Z"),
    fecha_cierre: ISODate("2026-03-20T16:00:00Z"),
    causa_raiz: "Aplicación de insecticida Clorpirifos fuera del periodo de carencia en parcela P014; el lote hermano 02 viajó en la misma unidad refrigerada.",
    acciones_correctivas: [
      "Suspensión temporal de cosecha en parcela SENASICA-MICH-URU-014 hasta auditoría de buenas prácticas agrícolas.",
      "Retiro completo y destrucción controlada de cajas recuperadas en sucursales SUC-MTY-04 y SUC-CDMX-01.",
      "Lavado y sanitización certificada de la unidad refrigerada MICH-842-K y cámara CF-02."
    ],
    tiendas_notificadas: [
      {
        codigo_sucursal: "SUC-MTY-04",
        nombre_comercial: "Supermercados del Norte - Valle",
        cantidad_enviada_kg: 450.0,
        cantidad_retirada_kg: 410.0,
        confirmado: true,
        fecha_confirmacion: ISODate("2026-03-13T18:45:00Z")
      },
      {
        codigo_sucursal: "SUC-CDMX-01",
        nombre_comercial: "Selecto Chedraui - Polanco",
        cantidad_enviada_kg: 400.0,
        cantidad_retirada_kg: 385.0,
        confirmado: true,
        fecha_confirmacion: ISODate("2026-03-13T19:15:00Z")
      }
    ],
    linea_tiempo: [
      {
        fecha_hora: ISODate("2026-03-13T16:45:00Z"),
        actor: "Lab AgroBio S.A. de C.V.",
        descripcion: "Carga de certificado LAB-2026-AGU-0842-V1 con Clorpirifos 0.08 mg/kg (No Conforme)."
      },
      {
        fecha_hora: ISODate("2026-03-13T17:10:00Z"),
        actor: "Ing. Laura Méndez (QA)",
        descripcion: "Bloqueo atómico de AGU-P014-260312-01 y lote hermano AGU-P014-260312-02 en PostgreSQL; alerta de retiro emitida vía Neo4j."
      },
      {
        fecha_hora: ISODate("2026-03-20T16:00:00Z"),
        actor: "Lic. Andrés Salgado (Gerencia)",
        descripcion: "Cierre formal del expediente de Recall tras confirmar 795 kg recuperados y sanitización completa."
      }
    ],
    firmas_cierre: {
      responsable_qa: "Ing. Laura Méndez",
      aprobacion_gerencia: "Lic. Andrés Salgado"
    }
  },
  {
    folio_incidente: "INC-2026-0015",
    codigo_lote_origen: "AGU-P015-260315-01",
    lotes_afectados: ["AGU-P015-260315-01"],
    estado_expediente: "En investigacion",
    fecha_apertura: ISODate("2026-03-15T16:25:00Z"),
    fecha_cierre: null,
    causa_raiz: null,
    acciones_correctivas: [],
    tiendas_notificadas: [],
    linea_tiempo: [
      {
        fecha_hora: ISODate("2026-03-15T16:25:00Z"),
        actor: "Carlos Mendoza (Recepción CEDIS)",
        descripcion: "Retención automática por llegada a 11.4 °C en unidad JAL-405-C (REC-2026-0107). En espera de inspección de vida de anaquel por QA."
      }
    ],
    firmas_cierre: null
  }
]);

print("OK: 2 expedientes insertados en expedientes_incidentes.");
print("=== Carga de datos semilla documentales finalizada con éxito ===");
