# TrazaAgro: Sistema de Trazabilidad Integral de Alimentos

## 1\. Nombre, descripción y problema que atiende

### Nombre del sistema

TrazaAgro

### Descripción general

TrazaAgro es una plataforma web orientada a la gestión y rastreo integral de lotes agrícolas frescos en cadenas de suministro alimentarias. Su función primordial es conectar digitalmente cada etapa del producto (desde la huerta de origen hasta la entrega en anaqueles y restaurantes), asegurando control de calidad, cumplimiento normativo y una capacidad de respuesta inmediata ante riesgos de inocuidad.

### Problema que atiende

Hoy en día, las distribuidoras agrícolas enfrentan una fragmentación crítica de su información. El rastreo de lotes se realiza combinando hojas de cálculo de Excel por producto, mensajes informales de WhatsApp con transportistas, correos electrónicos con productores y facturas o análisis en papel o archivos PDF dispersos.

Esta desconexión provoca que, ante una contingencia sanitaria (como la detección de plaguicidas fuera de norma o contaminación microbiológica), identificar el origen del lote, las parcelas involucradas y las tiendas donde ya se está vendiendo el producto tome entre medio día y varias jornadas de trabajo manual. Durante ese tiempo, el producto sospechoso sigue vendiéndose a los consumidores finales, lo que expone a la empresa a graves pérdidas económicas por retiros descontrolados, demandas legales, auditorías fallidas y la posible cancelación definitiva como proveedor de grandes cadenas comerciales.

## 2\. Usuarios y necesidades principales

Para asegurar un desarrollo viable y enfocado, el alcance del sistema concentra la operación en cuatro actores esenciales dentro del flujo de valor:

### Empacadora / Productor

* Perfil: Personal en campo y cuadrilla de empaque que cosecha y prepara la fruta para su envío inicial.  
* Necesidades clave:  
  * Generar y registrar lotes con un código único estandarizado desde el origen.  
  * Capturar datos indispensables: fecha de cosecha, parcela de origen, cantidad recolectada en kilogramos y cuadrilla responsable.  
  * Consultar el estado de recepción y los resultados de calidad de sus propios lotes, manteniendo restringida la visualización de datos o precios de otros productores.

### Recepción y Almacén en CEDIS

* Perfil: Operadores de bodega y supervisores de patio en los centros de distribución.  
* Necesidades clave:  
  * Registrar la llegada física del transporte, capturando cantidad real recibida, temperatura de la caja refrigerada y observaciones de calidad física.  
  * Retener automáticamente en revisión cualquier lote cuya temperatura de llegada esté fuera de los parámetros permitidos.  
  * Dividir lotes grandes en envíos más pequeños hacia tiendas y restaurantes, garantizando que nunca se despachen más kilogramos de los que hay en inventario y bloqueando cualquier intento de salida para producto retenido.

### Laboratorio Externo / Analista

* Perfil: Laboratorios certificados y analistas técnicos encargados de las pruebas químicas y microbiológicas.  
* Necesidades clave:  
  * Subir directamente los certificados de análisis ligados al identificador del lote.  
  * Registrar parámetros analíticos variables según el tipo de producto (por ejemplo, residuos de plaguicidas y materia seca en aguacate frente a microbiología como Salmonella o E. coli en vegetales de hoja).  
  * Registrar correcciones y nuevas versiones de análisis de forma inmutable, conservando el historial previo para auditorías.

### Responsable de QA e Inocuidad / Gerencia

* Perfil: Dirección de calidad y gerencia de operaciones con autoridad para liberar o frenar producto.  
* Necesidades clave:  
  * Revisar los expedientes técnicos y análisis de laboratorio para emitir dictámenes de liberación de producto.  
  * Bloquear inmediatamente un lote ante cualquier queja, auditoría o análisis positivo de contaminantes.  
  * Obtener en segundos la lista completa de tiendas afectadas (rastreo hacia adelante) y localizar el origen y posibles lotes contaminados en el mismo transporte o cuarto frío (rastreo hacia atrás y lateral).  
  * Generar alertas formales de retiro (recall) y cerrar el expediente con evidencias documentadas de las acciones correctivas.

## 3\. Objetivo, alcance y operaciones prioritarias

### Objetivo general

Diseñar e implementar una solución tecnológica integrada que permita registrar la vida de un lote agrícola y responder ante incidentes sanitarios en segundos, coordinando un modelo relacional para la integridad transaccional, un modelo documental para los expedientes técnicos variables y un modelo de grafos para la navegación de redes de distribución y contagio cruzado.

### Alcance del proyecto (MVP)

Funciones incluidas en esta versión:

* Registro inicial y asignación de código único de lote con datos maestros de cosecha y parcela.  
* Control de recepción física en CEDIS con validación de rangos de temperatura.  
* Carga, almacenamiento y versionado inmutable de análisis de laboratorio con atributos químicos y microbiológicos flexibles.  
* División transaccional de lotes de inventario hacia envíos a tiendas minoristas.  
* Bloqueo atómico de lotes por parte de QA con detención inmediata de despachos.  
* Motor de trazabilidad multidireccional: rastreo hacia adelante (tiendas con producto) y hacia atrás/lateral (causa raíz y contaminación cruzada por transporte o almacén compartido).  
* Generación de alertas de retiro e informe de auditoría del incidente.

Exclusiones explícitas para este MVP:

* Módulos de facturación electrónica, cobros o dispersión de pagos.  
* Sensores IoT en tiempo real o telemetría automática en carretera (se registran lecturas manuales en puntos de control).  
* Aplicaciones nativas para el consumidor final en supermercados.  
* Integración contable o ERPs comerciales de terceros.

### Operaciones prioritarias del sistema

1. Creación de lote y generación de identificador único: Registro de la fruta cosechada vinculada a su productor y parcela.  
2. Recepción e inspección física en CEDIS: Ingreso de producto con verificación de cadena de frío y pesaje real.  
3. Despacho fraccionado a clientes: Creación de órdenes de entrega descontando kilos del inventario en almacén.  
4. Carga de resultados de laboratorio: Incorporación de expedientes analíticos detallados al expediente del lote.  
5. Bloqueo de lote y freno de despacho: Cambio de estado con restricción automática en el módulo de almacén.  
6. Consulta de trazabilidad hacia adelante (Forward Traceability): Identificación de clientes y sucursales con producto en riesgo.  
7. Consulta de trazabilidad hacia atrás y lateral (Backward & Cross-contamination Traceability): Detección de parcelas origen y lotes que compartieron camión o cámara de refrigeración.  
8. Consulta consolidada de expediente 360°: Vista unificada que reúne el inventario actual, el dictamen de laboratorio y el mapa de ruta del lote.

## 4\. Justificación del uso de tres modelos de bases de datos

No toda la información de una cadena agroalimentaria se comporta de la misma manera ni requiere el mismo tipo de procesamiento. TrazaAgro distribuye las responsabilidades en tres motores especializados, evitando duplicaciones innecesarias y manteniendo una arquitectura coordinada.

### Base de datos relacional (PostgreSQL)

* Responsabilidad: Es la fuente de verdad de las entidades maestras, la seguridad, los estados de proceso y el control estricto de inventario.  
* Por qué se necesita: Los inventarios de producto fresco no toleran inconsistencias. Si un lote de 2,000 kg se reparte en pedidos para varias cadenas comerciales, el sistema debe garantizar transacciones ACID: o se descuenta el inventario y se crea la remisión de salida en un solo paso, o nada se guarda. De igual forma, las reglas que impiden despachar un lote bloqueado o en revisión deben estar blindadas por restricciones e integridad referencial en la base de datos.  
* Prueba de eliminación: Si se elimina la base relacional, la aplicación pierde el control de concurrencia y la consistencia transaccional. Dos operadores podrían vender los mismos kilogramos simultáneamente o despachar mercancía bloqueada por fallas de sincronización entre capas, obligando a programar complejas validaciones manuales en el backend que resultan frágiles ante accesos concurrentes.

### Base de datos documental (MongoDB)

* Responsabilidad: Repositorio central de expedientes técnicos, actas de recepción con observaciones e imágenes, y análisis de laboratorio.  
* Por qué se necesita: Los estudios de calidad e inocuidad son estructuralmente polimórficos y anidados. Un análisis de aguacate evalúa porcentaje de materia seca y residuos de plaguicidas sobre decenas de moléculas químicas; un análisis de hortalizas evalúa microbiología (Salmonella, Escherichia coli, Listeria monocytogenes) con conteos de unidades formadoras de colonias; y cada laboratorio externo entrega parámetros, unidades y límites de detección distintos. Además, las correcciones analíticas demandan un versionado inmutable donde la versión histórica se preserva íntegra junto a la nueva.  
* Prueba de eliminación: Si se elimina la base documental, los análisis tendrían que forzarse en esquemas tabulares rígidos mediante cientos de columnas nulas o recurrir al problemático modelo EAV (Entidad-Atributo-Valor), destruyendo la legibilidad y castigando el rendimiento al consultar o exportar un certificado completo. Si se intentaran guardar en nodos de grafos, sobrecargarían la memoria del motor con propiedades pesadas que entorpecen la navegación.

### Base de datos de grafos (Neo4j)

* Responsabilidad: Modelar la red viva de conexiones físicas y logísticas entre parcelas, lotes, transportes, cuartos fríos y tiendas.  
* Por qué se necesita: En la distribución agrícola, las rutas son dinámicas y los lotes se dividen, viajan juntos en el mismo camión o comparten el mismo cuarto frío en distintas fechas. Responder preguntas de investigación epidemiológica como "¿qué tiendas recibieron fruta de este lote?" o "¿qué otros lotes viajaron en el mismo transporte contaminado?" exige recorrer caminos de profundidad variable (de 3 a 7 saltos de distancia).  
* Prueba de eliminación: Si se elimina la base de grafos, las consultas de rastreo durante un retiro de producto se convertirían en consultas recursivas con múltiples uniones de tablas (JOINs anidados) en SQL, lo que resulta sumamente costoso en tiempo de cómputo y difícil de mantener. En una emergencia sanitaria, donde cada minuto cuenta para retirar el producto del anaquel antes de que se consuma, la lentitud o complejidad para descubrir conexiones indirectas pondría en riesgo la salud pública.

### Fuente de verdad y estrategia de sincronización

Para evitar duplicidad descontrolada:

* La base relacional es la dueña oficial de la existencia del lote, su código maestro (`codigo_lote`), su saldo en kilogramos y su estado operativo (`Cosechado`, `Recibido`, `En revisión`, `Liberado`, `Bloqueado`, `Retirado`).  
* La base documental almacena los análisis técnicos y evidencias referenciando únicamente el `codigo_lote` como clave externa de consulta.  
* La base de grafos almacena nodos ligeros identificados por `codigo_lote` y orientados exclusivamente a mantener las relaciones físicas del flujo (`COSECHADO_EN`, `ALMACENADO_EN`, `DIVIDIDO_EN`, `ENTREGADO_A`).  
* El backend coordina las escrituras: ante la creación de un lote o un envío, registra primero la transacción en la base relacional y propaga los metadatos de relación hacia Neo4j y MongoDB. En caso de interrupción en la propagación, el backend maneja políticas de reintento y bitácora de reconciliación para asegurar que la red del grafo refleje fielmente los despachos confirmados.

## 5\. Ejemplos de consultas y operaciones por modelo

A continuación se detallan las operaciones representativas de cada paradigma y la operación integrada central del sistema:

### Operaciones en el modelo relacional (PostgreSQL)

#### Operación R1: Despacho fraccionado con descuento transaccional de inventario

* Propósito: Registrar la salida de un pedido hacia una tienda minorista descontando los kilogramos del lote.  
* Actores: Recepción y Almacén en CEDIS.  
* Naturaleza técnica: Transacción ACID estricta. Verifica que el estado del lote sea `Liberado` y que la cantidad solicitada no exceda el saldo disponible en inventario.  
* Ejemplo SQL conceptual:

```sql
BEGIN;
SELECT saldo_kg, estado 
FROM lotes 
WHERE codigo_lote = 'AGU-P014-260312-01' 
FOR UPDATE;

-- Se comprueba en aplicación: estado == 'Liberado' AND saldo_kg >= 250

UPDATE lotes 
SET saldo_kg = saldo_kg - 250 
WHERE codigo_lote = 'AGU-P014-260312-01';

INSERT INTO envios_detalle (envio_id, codigo_lote, cantidad_kg, tienda_id, fecha_despacho)
VALUES (1052, 'AGU-P014-260312-01', 250, 42, CURRENT_TIMESTAMP);

COMMIT;
```

#### Operación R2: Bloqueo atómico de lote y registro de auditoría de incidente

* Propósito: Inmovilizar inmediatamente un lote e impedir cualquier nuevo despacho o movimiento de almacén.  
* Actores: Responsable de QA e Inocuidad.  
* Naturaleza técnica: Actualización de estado maestro y registro de bitácora con control de integridad.  
* Ejemplo SQL conceptual:

```sql
BEGIN;
UPDATE lotes 
SET estado = 'Bloqueado', 
    fecha_actualizacion = CURRENT_TIMESTAMP 
WHERE codigo_lote = 'AGU-P014-260312-01';

INSERT INTO incidentes_bitacora (codigo_lote, usuario_id, motivo, estado_previo, nuevo_estado, fecha_evento)
VALUES ('AGU-P014-260312-01', 5, 'Deteccion de plaguicida fuera de norma SENASICA', 'Liberado', 'Bloqueado', CURRENT_TIMESTAMP);

COMMIT;
```

### Operaciones en el modelo documental (MongoDB)

#### Operación D1: Registro y versionado inmutable de análisis de laboratorio

* Propósito: Almacenar los resultados de laboratorio polimórficos con estructura anidada de muestras y parámetros químicos.  
* Actores: Laboratorio Externo / QA.  
* Naturaleza técnica: Inserción de documentos con esquema flexible y control de versiones para conservar el histórico.  
* Ejemplo JSON conceptual:

```json
{
  "codigo_lote": "AGU-P014-260312-01",
  "laboratorio": "Lab AgroBio S.A.",
  "tipo_estudio": "Residuos de Plaguicidas",
  "fecha_muestreo": "2026-03-12T10:00:00Z",
  "version": 1,
  "es_vigente": true,
  "dictamen_general": "No Conforme",
  "muestras": [
    {
      "identificador_muestra": "M-01",
      "peso_gramos": 500,
      "determinaciones": [
        { "molecula": "Clorpirifos", "resultado_mg_kg": 0.08, "limite_maximo_mg_kg": 0.01, "conforme": false },
        { "molecula": "Malation", "resultado_mg_kg": 0.002, "limite_maximo_mg_kg": 0.05, "conforme": true }
      ]
    }
  ]
}
```

#### Operación D2: Consulta de expedientes con filtrado de parámetros anidados fuera de norma

* Propósito: Encontrar expedientes donde alguna muestra particular haya rebasado los límites máximos permitidos.  
* Actores: Responsable de QA e Inocuidad.  
* Naturaleza técnica: Filtrado sobre matrices y subdocumentos anidados mediante operadores de consulta documental.  
* Ejemplo de consulta MongoDB conceptual:

```js
db.analisis_laboratorio.find({
  codigo_lote: "AGU-P014-260312-01",
  es_vigente: true,
  "muestras.determinaciones": {
    $elemMatch: { conforme: false }
  }
}, {
  "laboratorio": 1,
  "dictamen_general": 1,
  "muestras.determinaciones.$": 1
});
```

### Operaciones en el modelo de grafos (Neo4j)

#### Operación G1: Rastreo hacia adelante en N saltos (Forward Traceability)

* Propósito: Localizar todas las tiendas y destinos finales que recibieron fruta derivada de un lote específico que ha resultado contaminado.  
* Actores: Responsable de QA / Gerencia de Operaciones.  
* Naturaleza técnica: Búsqueda de caminos dirigidos y recorrido de grafos desde el nodo del lote a través de sus divisiones y envíos.  
* Ejemplo Cypher conceptual:

```
MATCH (l:Lote {codigo: 'AGU-P014-260312-01'})-[:DIVIDIDO_EN*1..3]->(e:Envio)-[:ENTREGADO_A]->(t:Tienda)
RETURN t.nombre AS TiendaAfectada, 
       t.direccion AS Ubicacion, 
       e.codigo AS EnvioId, 
       e.cantidad_kg AS KilogramosEntregados,
       e.fecha_entrega AS FechaLlegada
ORDER BY e.fecha_entrega DESC;
```

#### Operación G2: Detección de causa raíz y contaminación cruzada lateral (Backward & Lateral Traceability)

* Propósito: Identificar la parcela y productor de origen del lote sospechoso, y simultáneamente descubrir qué otros lotes compartieron el mismo camión de transporte o el mismo cuarto frío en fechas coincidentes.  
* Actores: Responsable de QA e Inocuidad.  
* Naturaleza técnica: Búsqueda de patrones en estrella y caminos alternativos compartidos en la red.  
* Ejemplo Cypher conceptual:

```
MATCH (loteProblema:Lote {codigo: 'AGU-P014-260312-01'})-[:TRANSPORTADO_EN]->(v:Vehiculo)<-[:TRANSPORTADO_EN]-(loteHermano:Lote)
WHERE loteProblema <> loteHermano 
  AND abs(duration.inDays(loteProblema.fecha_cosecha, loteHermano.fecha_cosecha).days) <= 1
RETURN loteHermano.codigo AS LoteSospechosoPorVehiculo,
       v.placas AS VehiculoCompartido,
       loteHermano.fecha_cosecha AS FechaCosecha;
```

### Flujo integrado del sistema: Bloqueo de emergencia y alerta de retiro (Recall)

Esta operación es la pieza que cohesiona los tres modelos bajo un único caso de uso real:

1. El Laboratorio emite un informe no conforme. QA consulta el expediente técnico en MongoDB (Operación D2) confirmando que el lote `AGU-P014-260312-01` excede los límites legales de agroquímicos.  
2. Desde la interfaz web, el usuario de QA pulsa "Iniciar Protocolo de Retiro".  
3. El servicio del backend ejecuta la transacción en PostgreSQL (Operación R2), cambiando el estado del lote a `Bloqueado` e inhabilitando en tiempo real cualquier despacho en el almacén.  
4. Inmediatamente después, el servicio ejecuta en Neo4j las consultas de trazabilidad (Operaciones G1 y G2).  
5. La API consolida una respuesta unificada y presenta en pantalla:  
   * Los datos oficiales del lote y su saldo restante inmovilizado en el CEDIS (obtenido de SQL).  
   * La evidencia del análisis químico y el parámetro infractor (obtenido de MongoDB).  
   * La lista exacta de las 10 tiendas que tienen producto en sus anaqueles con las cantidades despachadas, más la advertencia de otros 2 lotes que viajaron en el mismo camión para sugerir su bloqueo preventivo (obtenido de Neo4j).  
6. El sistema emite automáticamente el reporte formal de alerta sanitaria para la gerencia y las tiendas involucradas, demostrando el valor coordinado de los tres paradigmas de persistencia.