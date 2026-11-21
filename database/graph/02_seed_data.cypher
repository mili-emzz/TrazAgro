// ============================================================================
// PROYECTO: TrazaAgro - Sistema de Trazabilidad de Alimentos Frescos
// ENTREGABLE 4: Implementación de la Base de Datos de Grafos (Neo4j)
// ARCHIVO: 02_seed_data.cypher (Carga idempotente MERGE sincronizada con SQL y MongoDB)
// ============================================================================

// Limpieza previa de datos para reconstrucción reproducible desde cero
MATCH (n) DETACH DELETE n;

// ============================================================================
// 1. PRODUCTORES (3 nodos sincronizados con PostgreSQL)
// ============================================================================
MERGE (p1:Productor {productor_id: 1})
SET p1.rfc = 'AUM180412H59',
    p1.nombre_razon_social = 'Aguacateros Unidos de Michoacán S.P.R. de R.L.',
    p1.telefono = '452-523-8810',
    p1.activo = true;

MERGE (p2:Productor {productor_id: 2})
SET p2.rfc = 'HTI200905M14',
    p2.nombre_razon_social = 'Huertas del Tancítaro S.A. de C.V.',
    p2.telefono = '452-519-4402',
    p2.activo = true;

MERGE (p3:Productor {productor_id: 3})
SET p3.rfc = 'ASP150219K81',
    p3.nombre_razon_social = 'Agroexportadora San Pedro S.A. de C.V.',
    p3.telefono = '341-412-9077',
    p3.activo = false;

// ============================================================================
// 2. PARCELAS Y RELACIÓN (:Parcela)-[:PERTENECE_A]->(:Productor)
// ============================================================================
MATCH (p1:Productor {productor_id: 1}),
      (p2:Productor {productor_id: 2}),
      (p3:Productor {productor_id: 3})
MERGE (pa1:Parcela {parcela_id: 1})
SET pa1.codigo_senasica = 'SENASICA-MICH-URU-014',
    pa1.nombre_huerta = 'Huerta La Escondida',
    pa1.municipio = 'Uruapan, Michoacán',
    pa1.superficie_ha = 18.50
MERGE (pa1)-[:PERTENECE_A {fecha_registro: date('2024-01-15')}]->(p1)

MERGE (pa2:Parcela {parcela_id: 2})
SET pa2.codigo_senasica = 'SENASICA-MICH-PER-015',
    pa2.nombre_huerta = 'Huerta El Mirador',
    pa2.municipio = 'Peribán, Michoacán',
    pa2.superficie_ha = 24.00
MERGE (pa2)-[:PERTENECE_A {fecha_registro: date('2024-02-10')}]->(p1)

MERGE (pa3:Parcela {parcela_id: 3})
SET pa3.codigo_senasica = 'SENASICA-MICH-TAN-018',
    pa3.nombre_huerta = 'Huerta Los Pinos',
    pa3.municipio = 'Tancítaro, Michoacán',
    pa3.superficie_ha = 32.75
MERGE (pa3)-[:PERTENECE_A {fecha_registro: date('2023-11-05')}]->(p2)

MERGE (pa4:Parcela {parcela_id: 4})
SET pa4.codigo_senasica = 'SENASICA-JAL-ZAP-022',
    pa4.nombre_huerta = 'Huerta Santa Rosa',
    pa4.municipio = 'Zapotlán el Grande, Jalisco',
    pa4.superficie_ha = 12.00
MERGE (pa4)-[:PERTENECE_A {fecha_registro: date('2022-06-20')}]->(p3);

// ============================================================================
// 3. VEHÍCULOS, CUARTOS FRÍOS, LABORATORIOS Y TIENDAS
// ============================================================================
// Vehículos refrigerados (3 de entrada huerta -> CEDIS, 2 de reparto CEDIS -> tienda)
MERGE (v1:Vehiculo {placas: 'MICH-842-K'})
SET v1.tipo_refrigeracion = 'Thermo King V-520 MAX',
    v1.temperatura_minima_operativa_c = 2.0;

MERGE (v2:Vehiculo {placas: 'MICH-910-B'})
SET v2.tipo_refrigeracion = 'Carrier Supra 850',
    v2.temperatura_minima_operativa_c = 2.0;

MERGE (v3:Vehiculo {placas: 'JAL-405-C'})
SET v3.tipo_refrigeracion = 'Thermo King T-880R',
    v3.temperatura_minima_operativa_c = 3.0;

MERGE (v4:Vehiculo {placas: 'TRK-884-A'})
SET v4.tipo_refrigeracion = 'Carrier Vector 8500 (Caja 53ft)',
    v4.temperatura_minima_operativa_c = 1.5;

MERGE (v5:Vehiculo {placas: 'TRK-902-C'})
SET v5.tipo_refrigeracion = 'Thermo King Precedent S-600',
    v5.temperatura_minima_operativa_c = 1.5;

// Cuartos Fríos en CEDIS (rango óptimo aguacate Hass: 5.0 a 7.0 °C)
MERGE (cf1:CuartoFrio {codigo_cuarto_frio: 'CF-01'})
SET cf1.nombre_cuarto = 'Cámara Fría Norte 1',
    cf1.temperatura_objetivo_c = 5.5,
    cf1.capacidad_tarimas = 40;

MERGE (cf2:CuartoFrio {codigo_cuarto_frio: 'CF-02'})
SET cf2.nombre_cuarto = 'Cámara Fría Sur 2',
    cf2.temperatura_objetivo_c = 6.0,
    cf2.capacidad_tarimas = 35;

MERGE (cf3:CuartoFrio {codigo_cuarto_frio: 'CF-03'})
SET cf3.nombre_cuarto = 'Cámara Cuarentena y Revisión 3',
    cf3.temperatura_objetivo_c = 6.0,
    cf3.capacidad_tarimas = 15;

// Laboratorios externos acreditados (nodos ligeros proyectados desde MongoDB)
MERGE (lab1:Laboratorio {acreditacion_iso: 'EMA-ISA-17025-2024'})
SET lab1.nombre = 'Lab AgroBio S.A. de C.V.';

MERGE (lab2:Laboratorio {acreditacion_iso: 'EMA-LA-0412-2025'})
SET lab2.nombre = 'Centro Analítico Fitosanitario de Occidente S.C.';

// Tiendas / Sucursales destino (4 nodos sincronizados con PostgreSQL)
MERGE (t1:Tienda {tienda_id: 1})
SET t1.codigo_sucursal = 'SUC-MTY-04',
    t1.nombre_comercial = 'Supermercados del Norte - Valle',
    t1.direccion = 'Av. Vasconcelos 345, Col. Del Valle',
    t1.ciudad = 'Monterrey, N.L.',
    t1.activo = true;

MERGE (t2:Tienda {tienda_id: 2})
SET t2.codigo_sucursal = 'SUC-CDMX-01',
    t2.nombre_comercial = 'Selecto Chedraui - Polanco',
    t2.direccion = 'Av. Moliere 222, Col. Polanco',
    t2.ciudad = 'Ciudad de México',
    t2.activo = true;

MERGE (t3:Tienda {tienda_id: 3})
SET t3.codigo_sucursal = 'SUC-GDL-02',
    t3.nombre_comercial = 'Fresko La Comer - Providencia',
    t3.direccion = 'Av. Rubén Darío 1109, Providencia',
    t3.ciudad = 'Guadalajara, Jal.',
    t3.activo = true;

MERGE (t4:Tienda {tienda_id: 4})
SET t4.codigo_sucursal = 'SUC-QRO-01',
    t4.nombre_comercial = 'Distribución Horeca Bajío',
    t4.direccion = 'Blvd. Bernardo Quintana 4100',
    t4.ciudad = 'Querétaro, Qro.',
    t4.activo = false;

// ============================================================================
// 4. LOTES Y RELACIÓN (:Lote)-[:COSECHADO_EN]->(:Parcela)
// Nota: Neo4j NO almacena saldo_kg (exclusivo de PostgreSQL)
// ============================================================================
MATCH (pa1:Parcela {parcela_id: 1}),
      (pa2:Parcela {parcela_id: 2}),
      (pa3:Parcela {parcela_id: 3})
MERGE (l1:Lote {codigo_lote: 'AGU-P014-260312-01'})
SET l1.producto = 'Aguacate Hass',
    l1.fecha_cosecha = datetime('2026-03-12T07:30:00Z'),
    l1.peso_inicial_kg = 2000.0,
    l1.estado = 'Bloqueado'
MERGE (l1)-[:COSECHADO_EN {
    cuadrilla_cosecha: 'Cuadrilla Alfa-01',
    fecha_cosecha: datetime('2026-03-12T07:30:00Z')
}]->(pa1)

MERGE (l2:Lote {codigo_lote: 'AGU-P014-260312-02'})
SET l2.producto = 'Aguacate Hass',
    l2.fecha_cosecha = datetime('2026-03-12T09:00:00Z'),
    l2.peso_inicial_kg = 1500.0,
    l2.estado = 'Bloqueado'
MERGE (l2)-[:COSECHADO_EN {
    cuadrilla_cosecha: 'Cuadrilla Alfa-02',
    fecha_cosecha: datetime('2026-03-12T09:00:00Z')
}]->(pa1)

MERGE (l3:Lote {codigo_lote: 'AGU-P018-260314-01'})
SET l3.producto = 'Aguacate Hass',
    l3.fecha_cosecha = datetime('2026-03-14T06:45:00Z'),
    l3.peso_inicial_kg = 3000.0,
    l3.estado = 'Liberado'
MERGE (l3)-[:COSECHADO_EN {
    cuadrilla_cosecha: 'Cuadrilla Tancítaro-03',
    fecha_cosecha: datetime('2026-03-14T06:45:00Z')
}]->(pa3)

MERGE (l4:Lote {codigo_lote: 'AGU-P015-260315-01'})
SET l4.producto = 'Aguacate Hass',
    l4.fecha_cosecha = datetime('2026-03-15T08:00:00Z'),
    l4.peso_inicial_kg = 1800.0,
    l4.estado = 'En revision'
MERGE (l4)-[:COSECHADO_EN {
    cuadrilla_cosecha: 'Cuadrilla Beta-01',
    fecha_cosecha: datetime('2026-03-15T08:00:00Z')
}]->(pa2)

MERGE (l5:Lote {codigo_lote: 'AGU-P018-260316-01'})
SET l5.producto = 'Aguacate Hass',
    l5.fecha_cosecha = datetime('2026-03-16T07:15:00Z'),
    l5.peso_inicial_kg = 2200.0,
    l5.estado = 'Liberado'
MERGE (l5)-[:COSECHADO_EN {
    cuadrilla_cosecha: 'Cuadrilla Tancítaro-01',
    fecha_cosecha: datetime('2026-03-16T07:15:00Z')
}]->(pa3)

MERGE (l6:Lote {codigo_lote: 'AGU-P014-260318-01'})
SET l6.producto = 'Aguacate Hass',
    l6.fecha_cosecha = datetime('2026-03-18T07:00:00Z'),
    l6.peso_inicial_kg = 1600.0,
    l6.estado = 'Cosechado'
MERGE (l6)-[:COSECHADO_EN {
    cuadrilla_cosecha: 'Cuadrilla Alfa-01',
    fecha_cosecha: datetime('2026-03-18T07:00:00Z')
}]->(pa1);

// ============================================================================
// 5. TRASLADO HUERTA -> CEDIS (:TRASLADADO_EN) Y ESTANCIA EN BODEGA (:ALMACENADO_EN)
// ============================================================================
MATCH (l1:Lote {codigo_lote: 'AGU-P014-260312-01'}),
      (l2:Lote {codigo_lote: 'AGU-P014-260312-02'}),
      (l3:Lote {codigo_lote: 'AGU-P018-260314-01'}),
      (l4:Lote {codigo_lote: 'AGU-P015-260315-01'}),
      (l5:Lote {codigo_lote: 'AGU-P018-260316-01'}),
      (v1:Vehiculo {placas: 'MICH-842-K'}),
      (v2:Vehiculo {placas: 'MICH-910-B'}),
      (v3:Vehiculo {placas: 'JAL-405-C'}),
      (cf1:CuartoFrio {codigo_cuarto_frio: 'CF-01'}),
      (cf2:CuartoFrio {codigo_cuarto_frio: 'CF-02'}),
      (cf3:CuartoFrio {codigo_cuarto_frio: 'CF-03'})

// Lote 1 y Lote 2 comparten camión MICH-842-K y cuarto frío CF-02 (clave para RN-08)
MERGE (l1)-[:TRASLADADO_EN {
    folio_recepcion: 'REC-2026-0104',
    fecha_llegada: datetime('2026-03-12T18:15:00Z'),
    nombre_chofer: 'Martín Morales',
    peso_recibido_kg: 1995.0,
    temperatura_llegada_c: 5.9
}]->(v1)
MERGE (l1)-[:ALMACENADO_EN {
    folio_recepcion: 'REC-2026-0104',
    fecha_ingreso: datetime('2026-03-12T18:30:00Z'),
    dictamen_recepcion: 'Conforme'
}]->(cf2)

MERGE (l2)-[:TRASLADADO_EN {
    folio_recepcion: 'REC-2026-0105',
    fecha_llegada: datetime('2026-03-12T18:40:00Z'),
    nombre_chofer: 'Martín Morales',
    peso_recibido_kg: 1498.5,
    temperatura_llegada_c: 6.1
}]->(v1)
MERGE (l2)-[:ALMACENADO_EN {
    folio_recepcion: 'REC-2026-0105',
    fecha_ingreso: datetime('2026-03-12T18:50:00Z'),
    dictamen_recepcion: 'Conforme'
}]->(cf2)

// Lote 3 en MICH-910-B y CF-01
MERGE (l3)-[:TRASLADADO_EN {
    folio_recepcion: 'REC-2026-0106',
    fecha_llegada: datetime('2026-03-14T17:20:00Z'),
    nombre_chofer: 'Ricardo Pineda',
    peso_recibido_kg: 2992.0,
    temperatura_llegada_c: 5.5
}]->(v2)
MERGE (l3)-[:ALMACENADO_EN {
    folio_recepcion: 'REC-2026-0106',
    fecha_ingreso: datetime('2026-03-14T17:35:00Z'),
    dictamen_recepcion: 'Conforme'
}]->(cf1)

// Lote 4 con ruptura de cadena de frío (11.4 °C) en JAL-405-C y cuarentena CF-03
MERGE (l4)-[:TRASLADADO_EN {
    folio_recepcion: 'REC-2026-0107',
    fecha_llegada: datetime('2026-03-15T16:20:00Z'),
    nombre_chofer: 'Héctor Vargas',
    peso_recibido_kg: 1796.0,
    temperatura_llegada_c: 11.4
}]->(v3)
MERGE (l4)-[:ALMACENADO_EN {
    folio_recepcion: 'REC-2026-0107',
    fecha_ingreso: datetime('2026-03-15T16:25:00Z'),
    dictamen_recepcion: 'Retenido'
}]->(cf3)

// Lote 5 en MICH-910-B y CF-01
MERGE (l5)-[:TRASLADADO_EN {
    folio_recepcion: 'REC-2026-0108',
    fecha_llegada: datetime('2026-03-16T15:10:00Z'),
    nombre_chofer: 'Ricardo Pineda',
    peso_recibido_kg: 2198.0,
    temperatura_llegada_c: 5.8
}]->(v2)
MERGE (l5)-[:ALMACENADO_EN {
    folio_recepcion: 'REC-2026-0108',
    fecha_ingreso: datetime('2026-03-16T15:25:00Z'),
    dictamen_recepcion: 'Conforme'
}]->(cf1);

// ============================================================================
// 6. PROYECCIÓN ANALÍTICA DESDE MONGODB (:Laboratorio)-[:EMITIO_ANALISIS]->(:Lote)
// ============================================================================
MATCH (lab1:Laboratorio {acreditacion_iso: 'EMA-ISA-17025-2024'}),
      (lab2:Laboratorio {acreditacion_iso: 'EMA-LA-0412-2025'}),
      (l1:Lote {codigo_lote: 'AGU-P014-260312-01'}),
      (l3:Lote {codigo_lote: 'AGU-P018-260314-01'}),
      (l5:Lote {codigo_lote: 'AGU-P018-260316-01'})

MERGE (lab1)-[:EMITIO_ANALISIS {
    folio_analisis: 'LAB-2026-AGU-0842-V1',
    tipo_estudio: 'Residuos de Plaguicidas',
    dictamen_general: 'No Conforme',
    fecha_emision: datetime('2026-03-13T16:45:00Z'),
    es_vigente: true
}]->(l1)

MERGE (lab2)-[:EMITIO_ANALISIS {
    folio_analisis: 'LAB-2026-AGU-0845-V1',
    tipo_estudio: 'Microbiologico',
    dictamen_general: 'Conforme',
    fecha_emision: datetime('2026-03-13T07:30:00Z'),
    es_vigente: true
}]->(l1)

// Versionado V1 (es_vigente: false) y V2 (es_vigente: true) sincronizado con MongoDB
MERGE (lab1)-[:EMITIO_ANALISIS {
    folio_analisis: 'LAB-2026-AGU-0910-V1',
    tipo_estudio: 'Residuos de Plaguicidas',
    dictamen_general: 'No Conforme',
    fecha_emision: datetime('2026-03-14T20:00:00Z'),
    es_vigente: false
}]->(l3)

MERGE (lab1)-[:EMITIO_ANALISIS {
    folio_analisis: 'LAB-2026-AGU-0910-V2',
    tipo_estudio: 'Residuos de Plaguicidas',
    dictamen_general: 'Conforme',
    fecha_emision: datetime('2026-03-15T11:20:00Z'),
    es_vigente: true
}]->(l3)

MERGE (lab1)-[:EMITIO_ANALISIS {
    folio_analisis: 'LAB-2026-AGU-0925-V1',
    tipo_estudio: 'Residuos de Plaguicidas',
    dictamen_general: 'Conforme',
    fecha_emision: datetime('2026-03-16T19:15:00Z'),
    es_vigente: true
}]->(l5);

// ============================================================================
// 7. ENVÍOS, FRACCIONAMIENTO (:DIVIDIDO_EN), REPARTO (:DESPACHADO_EN) Y ENTREGA (:ENTREGADO_A)
// ============================================================================
MATCH (l1:Lote {codigo_lote: 'AGU-P014-260312-01'}),
      (l3:Lote {codigo_lote: 'AGU-P018-260314-01'}),
      (l5:Lote {codigo_lote: 'AGU-P018-260316-01'}),
      (v4:Vehiculo {placas: 'TRK-884-A'}),
      (v5:Vehiculo {placas: 'TRK-902-C'}),
      (t1:Tienda {codigo_sucursal: 'SUC-MTY-04'}),
      (t2:Tienda {codigo_sucursal: 'SUC-CDMX-01'}),
      (t3:Tienda {codigo_sucursal: 'SUC-GDL-02'})

// Envío 1: 450 kg del Lote 1 hacia Monterrey (SUC-MTY-04)
MERGE (e1:Envio {codigo_envio: 'ENV-2026-1052'})
SET e1.fecha_despacho = datetime('2026-03-13T09:00:00Z'),
    e1.estado_envio = 'Entregado'
MERGE (l1)-[:DIVIDIDO_EN {cantidad_kg: 450.0}]->(e1)
MERGE (e1)-[:DESPACHADO_EN {fecha_despacho: datetime('2026-03-13T09:00:00Z'), nombre_chofer: 'Luis Estrada'}]->(v4)
MERGE (e1)-[:ENTREGADO_A {fecha_entrega: datetime('2026-03-13T15:20:00Z'), recibido_por: 'Jefe Perecederos MTY'}]->(t1)

// Envío 2: 400 kg del Lote 1 hacia CDMX (SUC-CDMX-01)
MERGE (e2:Envio {codigo_envio: 'ENV-2026-1053'})
SET e2.fecha_despacho = datetime('2026-03-13T10:30:00Z'),
    e2.estado_envio = 'Entregado'
MERGE (l1)-[:DIVIDIDO_EN {cantidad_kg: 400.0}]->(e2)
MERGE (e2)-[:DESPACHADO_EN {fecha_despacho: datetime('2026-03-13T10:30:00Z'), nombre_chofer: 'Jorge Domínguez'}]->(v5)
MERGE (e2)-[:ENTREGADO_A {fecha_entrega: datetime('2026-03-13T16:10:00Z'), recibido_por: 'Recepción Polanco'}]->(t2)

// Envío 3: 600 kg del Lote 3 hacia Guadalajara (SUC-GDL-02)
MERGE (e3:Envio {codigo_envio: 'ENV-2026-1054'})
SET e3.fecha_despacho = datetime('2026-03-15T14:00:00Z'),
    e3.estado_envio = 'Entregado'
MERGE (l3)-[:DIVIDIDO_EN {cantidad_kg: 600.0}]->(e3)
MERGE (e3)-[:DESPACHADO_EN {fecha_despacho: datetime('2026-03-15T14:00:00Z'), nombre_chofer: 'Luis Estrada'}]->(v4)
MERGE (e3)-[:ENTREGADO_A {fecha_entrega: datetime('2026-03-15T19:00:00Z'), recibido_por: 'Almacén Providencia'}]->(t3)

// Envío 4 consolidado (N:M): mezcla 350 kg del Lote 3 + 200 kg del Lote 5 hacia Monterrey (SUC-MTY-04)
MERGE (e4:Envio {codigo_envio: 'ENV-2026-1055'})
SET e4.fecha_despacho = datetime('2026-03-16T08:30:00Z'),
    e4.estado_envio = 'En transito'
MERGE (l3)-[:DIVIDIDO_EN {cantidad_kg: 350.0}]->(e4)
MERGE (l5)-[:DIVIDIDO_EN {cantidad_kg: 200.0}]->(e4)
MERGE (e4)-[:DESPACHADO_EN {fecha_despacho: datetime('2026-03-16T08:30:00Z'), nombre_chofer: 'Jorge Domínguez'}]->(v5)
MERGE (e4)-[:ENTREGADO_A]->(t1);
