# Entrevista de levantamiento de requerimientos: TrazaAgro

## 0. Instrucciones para la IA que responde (leer primero)

**Tu rol:** Eres **Responsable de Aseguramiento de Calidad e Inocuidad (QA)** de una empresa distribuidora de productos agrícolas frescos (frutas y verduras) en México, con **15 años de experiencia**. Has manejado auditorías sanitarias, retiros de producto (recalls) y relación con productores, transportistas, tiendas y autoridades.

**Cómo debes responder:**
- Responde **como persona del negocio**, no como técnico de sistemas. No uses términos de bases de datos.
- Sé **concreto**: da ejemplos reales, cifras aproximadas (volúmenes, tiempos, frecuencias), nombres de documentos, estados y casos.
- Si no sabes algo, **di "no lo sé"** o **"depende"** y explica de qué depende. No inventes normas ni leyes: si mencionas una, indica que debe verificarse.
- Mantén **coherencia** entre respuestas (mismo producto, mismos actores, mismas cifras).
- Si una respuesta tiene excepciones o casos raros, **menciónalos**: son los más valiosos.
- Formato por pregunta: respuesta breve (2 a 6 líneas) + lista si hay varios elementos.
- Al terminar todas las secciones, genera la **Sección 10 (Resumen final)**.

---

## 1. Contexto del proyecto (para que lo conozcas)

**TrazaAgro** es un sistema para rastrear lotes de alimentos desde el productor hasta la tienda, para actuar rápido ante contaminación o retiros de producto.

- Equipo: estudiantes que diseñan la app. Tú eres el **experto del negocio** al que entrevistan.
- Se necesita definir **requerimientos funcionales, datos, reglas de negocio y alcance**.
- Tú **no** decides la tecnología; solo cuentas cómo funciona (o debería funcionar) la operación.

---

## 2. Tu empresa y el producto

1. ¿Qué producto(s) manejan? Elige **uno principal** para el caso de estudio (ej. aguacate, jitomate, berries, lechuga) y explica por qué.
2. ¿Cuántos **productores** surten, cuántos **lotes** manejan al mes y a cuántas **tiendas/clientes** entregan?
3. ¿Cómo se ve la cadena completa, paso por paso, desde la parcela hasta el anaquel?
4. ¿Cuál es el **problema más costoso** hoy en trazabilidad? Cuenta un **caso real o verosímil** (brote, devolución, auditoría fallida).
5. Hoy, ¿cómo se rastrea un lote? (papel, Excel, WhatsApp, ERP) ¿Cuánto tarda y qué falla?
6. ¿Qué se espera lograr con el sistema? Da **metas medibles** (ej. "ubicar un lote en menos de X minutos").

---

## 3. Actores y permisos

7. ¿Quiénes intervienen en el proceso? (productor, empacadora, transportista, centro de distribución, tienda, inspector, laboratorio, gerencia, etc.)
8. Para **cada actor**: ¿qué necesita **registrar**, qué necesita **consultar** y qué **no debería poder ver ni modificar**?
9. ¿Quién **autoriza** liberar o bloquear un lote?
10. ¿Qué actores son **externos** a la empresa (autoridades, auditores, clientes) y qué información reciben?
11. ¿Hay información **confidencial** (precios, productores, resultados de laboratorio)? ¿Quién puede verla?

---

## 4. Operación diaria (flujo normal)

12. Describe el **flujo de un lote**, desde que se cosecha hasta que se vende, con **cada evento que se registra** (cosecha, empaque, carga, traslado, recepción, almacenamiento, venta).
13. ¿Qué **datos se capturan en cada evento**? (fecha, hora, responsable, cantidad, temperatura, ubicación, documentos)
14. ¿Un lote puede **dividirse** (por ejemplo, en varios envíos) o **mezclarse** con otros? Da ejemplos y qué pasa con su identificador.
15. ¿Cómo se identifica un lote? (código, formato, quién lo asigna, ¿puede repetirse?)
16. ¿Qué **estados** tiene un lote? (ej. creado, en tránsito, recibido, bloqueado, retirado) ¿Quién cambia cada estado?
17. ¿Qué pasa si un envío llega **incompleto, tarde o con temperatura fuera de rango**?
18. ¿Qué **reportes** consultas semanalmente o mensualmente y con qué fin?

---

## 5. Documentos, certificados y análisis

19. ¿Qué **documentos** acompañan a un lote? (certificados fitosanitarios, análisis de laboratorio, bitácoras, facturas, permisos)
20. ¿Los **análisis de laboratorio** son iguales para todos los productos o cambian? Da **2 ejemplos de productos con campos distintos**.
21. ¿Qué **datos varían** entre productores, productos o laboratorios? (parámetros, unidades, formatos, certificaciones)
22. ¿Hay documentos con **información anidada**? (ej. un análisis con varias muestras, cada una con varios parámetros)
23. ¿Cuánto tiempo se **conservan** los documentos y quién puede modificarlos o reemplazarlos?
24. ¿Un documento puede tener **versiones** o correcciones? ¿Cómo se manejan?

---

## 6. Rastreo y relaciones (hacia atrás y hacia adelante)

25. Si se detecta un problema en un lote, ¿qué **preguntas necesitas responder de inmediato**? (ej. ¿de qué parcelas vino? ¿qué otros lotes comparten origen? ¿a qué tiendas llegó?)
26. ¿Qué es más urgente: rastrear **hacia atrás** (origen) o **hacia adelante** (destino)? ¿Por qué?
27. ¿Cuántos **niveles o pasos** tiene normalmente la cadena (productor → empacadora → CEDIS → tienda)? ¿Cuál es el máximo?
28. ¿Qué **conexiones indirectas** importan? (ej. mismo transporte, misma empacadora, misma fecha, mismo laboratorio)
29. ¿Puedes dar un caso donde **la relación entre varios actores** reveló la causa de un problema?
30. ¿Qué **tan rápido** deberías obtener la lista de tiendas afectadas ante un retiro? ¿Qué pasa hoy si no se obtiene a tiempo?

---

## 7. Gestión de incidentes y retiros (recall)

31. Paso a paso, ¿cómo se **declara** un lote sospechoso y quién lo decide?
32. Cuando se bloquea un lote, ¿qué debe pasar con **lotes relacionados**, envíos en curso e inventario en tiendas?
33. ¿Qué información debe contener una **alerta de retiro**? ¿A quién se notifica y por qué medio?
34. ¿Cómo se **cierra** un incidente? (evidencias, resultados, responsables, tiempos)
35. ¿Qué **evidencia** debe quedar guardada para una auditoría o autoridad?

---

## 8. Reglas de negocio y restricciones

36. Enumera las **reglas que nunca deben romperse** (ej. "no se despacha un lote bloqueado", "no se envía más cantidad de la disponible").
37. ¿Qué datos son **obligatorios** y cuáles opcionales en cada registro?
38. ¿Qué operaciones deben ser **todo o nada**? (ej. registrar un envío y descontar inventario al mismo tiempo)
39. ¿Qué se **puede borrar** y qué solo debe marcarse como inactivo o histórico?
40. ¿Hay **límites** (tiempos máximos en tránsito, rangos de temperatura, caducidades, cantidades)?
41. ¿Qué **normas o requisitos legales** conoces que apliquen? (indica si debe verificarse)

---

## 9. Requisitos de uso, calidad y alcance

42. ¿Quién usaría el sistema, desde **qué dispositivos** y en qué condiciones? (oficina, campo, bodega, sin internet)
43. ¿Qué tan **rápido** debe responder en situaciones normales y en una emergencia?
44. ¿Qué pasa si el sistema **falla** durante un retiro? ¿Qué es lo mínimo que no puede perderse?
45. ¿Cuántos **usuarios simultáneos** y cuántos **registros por día** esperarías?
46. ¿Qué cosas **no** esperas que haga el sistema en una primera versión? (pagos, facturación, app móvil, sensores IoT, etc.)
47. Si solo pudiera hacer **5 cosas** en la primera versión, ¿cuáles serían y por qué?
48. ¿Qué escenario te convencería en una **demostración**? Descríbelo con datos de ejemplo.
49. ¿Qué **riesgos o dudas** ves para que el proyecto fracase en la práctica?

---

## 10. Resumen final (la IA debe generarlo al terminar)

Con base en **tus propias respuestas**, genera:

1. **Lista de actores** con sus permisos (tabla).
2. **Requerimientos funcionales** (ID, actor, acción, resultado esperado, criterio de aceptación). Mínimo 10.
3. **Entidades y datos clave** mencionados (productor, lote, envío, tienda, análisis, etc.) con sus atributos principales.
4. **Reglas de negocio** numeradas (RN-01, RN-02, ...).
5. **Estados y transiciones** de un lote.
6. **Preguntas de rastreo** que el sistema debe responder (útiles para consultas de recorrido).
7. **Datos que varían o son anidados** (útiles para estructuras de documento).
8. **Operaciones críticas que deben ser consistentes** (transacciones).
9. **Requerimientos no funcionales** (rendimiento, seguridad, disponibilidad, uso).
10. **Alcance**: lo que **sí** y lo que **no** entra en la primera versión (priorizado).
11. **Escenario de demo** de principio a fin.
12. **Supuestos y lagunas**: lo que dijiste que no sabes o depende.

> Nota para el equipo: las secciones 5, 6 y 8 alimentan, respectivamente, la justificación de la base **documental**, la de **grafo** y la **relacional**. Validar que cada una tenga al menos 3 respuestas sólidas.
