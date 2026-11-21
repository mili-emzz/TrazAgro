| UNIVERSIDAD | POLITÉCNICA  |               | DE CHIAPAS |         |         |          |     |
| ----------- | ------------ | ------------- | ---------- | ------- | ------- | -------- | --- |
| Guía de     | trabajo para | estudiantes   |            |         |         |          |     |
| Proyecto    |              | final         |            |         |         |          |     |
| Diseño,     | desarrollo   | e integración |            | de tres | modelos | de bases | de  |
datos
Una aplicación, tres modelos de persistencia y una solución integrada
El proyecto consiste en definir y desarrollar una aplicación que resuelva un problema concreto y
queutilice,demanerajustificadaycoordinada,unabasededatosrelacional,unabasededatos
documental y una base de datos de grafos. El resultado final será una sola solución integrada,
| no tres  | ejercicios desconectados. |              |     |     |     |     |     |
| -------- | ------------------------- | ------------ | --- | --- | --- | --- | --- |
| Material | de orientación            | del proyecto |     |     |     |     |     |
2026

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
Índice
| 1. Propósito | y alcance | del proyecto |     |     | 2   |
| ------------ | --------- | ------------ | --- | --- | --- |
| 2. Reglas    | que deben | respetarse   |     |     | 2   |
2.1. Seguir la metodología y producir sus entregables . . . . . . . . . . . . . . . . . . . . . . 2
2.2. Definir una aplicación concreta . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
2.3. La aplicación debe justificar los tres modelos . . . . . . . . . . . . . . . . . . . . . . . . 2
2.4. Entregar una integración funcional . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
3. ¿Qué significa utilizar tres modelos en una misma aplicación? 3
| 4. Definición | de la | aplicación |     |     | 3   |
| ------------- | ----- | ---------- | --- | --- | --- |
4.1. Contenido mínimo de la propuesta . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
4.2. Prueba de suficiencia de la idea . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
| 5. Diseño | de responsabilidades |     | de las bases | de datos | 4   |
| --------- | -------------------- | --- | ------------ | -------- | --- |
5.1. Matriz de responsabilidades . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4
5.2. Definir la fuente de verdad . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
| 6. Metodología | y entregables |     |     |     | 5   |
| -------------- | ------------- | --- | --- | --- | --- |
6.1. Etapas de trabajo . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5
6.2. Relación con las actividades de refuerzo de las diapositivas . . . . . . . . . . . . . . . . 6
| 7. Entregables | finales |     |     |     | 7   |
| -------------- | ------- | --- | --- | --- | --- |
7.1. Entregable 1. Propuesta de aplicación . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
7.2. Entregable 2. Modelado de datos . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
7.3. Entregable 3. Arquitectura y selección tecnológica . . . . . . . . . . . . . . . . . . . . . 8
7.4. Entregable 4. Implementación de las tres bases . . . . . . . . . . . . . . . . . . . . . . 8
7.5. Entregable 5. Catálogo de operaciones y consultas . . . . . . . . . . . . . . . . . . . . . 9
7.6. Entregable 6. Backend y API . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
7.7. Entregable 7. Aplicación e integración . . . . . . . . . . . . . . . . . . . . . . . . . . . . 9
7.8. Entregable 8. Pruebas, documentación y despliegue . . . . . . . . . . . . . . . . . . . . 10
| 8. Arquitectura | de  | integración | esperada |     | 10  |
| --------------- | --- | ----------- | -------- | --- | --- |
8.1. Ejemplo de flujo integrado . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 11
| 9. Pruebas | obligatorias | de  | integración |     | 11  |
| ---------- | ------------ | --- | ----------- | --- | --- |
1

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
| 10.Organización | del             | repositorio |             | 12  |
| --------------- | --------------- | ----------- | ----------- | --- |
| 11.Criterios    | para considerar | completo    | el proyecto | 12  |
| 12.Errores      | que deben       | evitarse    |             | 13  |
| 13.Cómo         | debe entenderse | la entrega  | final       | 13  |
2

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
| 1. Propósito |     | y alcance | del | proyecto |     |
| ------------ | --- | --------- | --- | -------- | --- |
El propósito es que cada equipo diseñe, implemente y valide una aplicación de software a partir de un
problemarealoverosímil.Laaplicacióndeberájustificarelusocomplementariodetresparadigmasde
| bases de | datos: |     |     |     |     |
| -------- | ------ | --- | --- | --- | --- |
Relacional: para información estructurada, operaciones transaccionales, restricciones e integridad
referencial.
Documental: para información agrupada en documentos, estructuras anidadas o atributos cuya
| forma | puede | variar entre | registros. |     |     |
| ----- | ----- | ------------ | ---------- | --- | --- |
Grafo:pararepresentaryconsultarentidadesconectadasmedianterelacionesexplícitas,recorridos
y patrones.
La aplicación puede ser web, móvil o de escritorio. La interfaz no determina el modelo de datos: lo
importante es que las operaciones, los datos y las relaciones del dominio justifiquen la arquitectura
seleccionada.
| 2. Reglas  |     | que deben   | respetarse |     |                 |
| ---------- | --- | ----------- | ---------- | --- | --------------- |
| 2.1 Seguir | la  | metodología | y producir |     | sus entregables |
El desarrollo debe avanzar por etapas. Cada etapa genera evidencia que se utiliza en la siguiente.
No se debe comenzar programando las tres bases de datos sin haber definido antes el problema, los
| usuarios,   | los requerimientos |            | y el modelo |     | de información. |
| ----------- | ------------------ | ---------- | ----------- | --- | --------------- |
| 2.2 Definir | una                | aplicación | concreta    |     |                 |
Cada equipo debe proponer una aplicación con un propósito delimitado, usuarios identificables y
operacionesverificables.Noessuficientepresentarunaideaampliacomo “unaplataforma degestión”
o “una red social”. Se debe precisar qué problema atiende, quién la utiliza, qué información administra
| y qué decisiones  |     | u operaciones | permite    |     | realizar.    |
| ----------------- | --- | ------------- | ---------- | --- | ------------ |
| 2.3 La aplicación |     | debe          | justificar | los | tres modelos |
Cada aplicación deberá producir y utilizar una base relacional, una documental y una de grafos. La
selección de cada una debe responder a una necesidad real del dominio. No se aceptará dividir
artificialmente los mismos datos en tres bases solo para cumplir el requisito.
3

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
| 2.4 Entregar |     | una | integración |     | funcional |     |     |     |
| ------------ | --- | --- | ----------- | --- | --------- | --- | --- | --- |
Lastresbasesdeberánparticiparenunasoluciónúnica.LainterfazconsumiráunaAPIobackendque
coordine las operaciones y acceda a cada base mediante su correspondiente capa de persistencia. El
| usuario | no debe | tener | que | operar | tres sistemas | independientes. |     |     |
| ------- | ------- | ----- | --- | ------ | ------------- | --------------- | --- | --- |
3. ¿Qué significa utilizar tres modelos en una misma aplicación?
Una aplicación puede necesitar distintos tipos de persistencia porque no toda la información tiene la
misma estructura ni se consulta de la misma manera. La decisión no se toma por moda, sino por la
| naturaleza | de  | los datos | y   | las operaciones. |     |     |     |     |
| ---------- | --- | --------- | --- | ---------------- | --- | --- | --- | --- |
Modelo Información y responsabilidad típica Pregunta que ayuda a responder
Relacional Datos estructurados, entidades transac- ¿Qué registro existe, cuál es su estado
cionales, claves, restricciones y relacio- y qué operación debe mantenerse ínte-
|     |     | nes | tabulares. |     |     |     | gra? |     |
| --- | --- | --- | ---------- | --- | --- | --- | ---- | --- |
Documental Documentoscompletos,atributosanida- ¿Qué información contextual o flexible
|     |     | dos,      | formularios, |            | configuraciones |     | o es- pertenece | a este registro? |
| --- | --- | --------- | ------------ | ---------- | --------------- | --- | --------------- | ---------------- |
|     |     | tructuras |              | variables. |                 |     |                 |                  |
Grafo Nodos, relaciones dirigidas o no dirigi- ¿Cómo se conecta esta entidad con
das, propiedades y patrones de cone- otras y qué rutas o patrones existen?
xión.
Losmodelospuedenrepresentaraspectosrelacionadosdelmismodominio,perocadaunodebetener
una responsabilidad identificable. Por ejemplo, una persona puede tener un registro principal en la
base relacional, un expediente documental y conexiones con proyectos, cursos o colaboradores en la
| base de | grafos. |     |     |     |     |     |     |     |
| ------- | ------- | --- | --- | --- | --- | --- | --- | --- |
Eviten la duplicación sin propósito. Si un dato se almacena en más de una base, el equipo
debe explicar por qué se replica, cuál es la fuente autorizada de ese dato, cómo se actualiza y
cómo se resuelven inconsistencias. La redundancia no controlada genera errores.
| 4. Definición |     | de  | la  | aplicación |     |     |     |     |
| ------------- | --- | --- | --- | ---------- | --- | --- | --- | --- |
Antes de seleccionar tecnologías, el equipo debe elaborar una ficha de definición del proyecto.
| 4.1 Contenido |     | mínimo         |           | de  | la propuesta        |           |             |     |
| ------------- | --- | -------------- | --------- | --- | ------------------- | --------- | ----------- | --- |
| 1. Nombre     | de  | la aplicación: |           |     | claro y relacionado | con       | su función. |     |
| 2. Problema:  |     | situación      | concreta  |     | que se busca        | resolver. |             |     |
| 3. Usuarios:  |     | quién          | utilizará | el  | sistema y qué       | necesita  | hacer.      |     |
4. Objetivo general: resultado que se espera conseguir con la aplicación.
4

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
5. Alcance: funciones que sí se desarrollarán y exclusiones explícitas.
6. Operaciones principales: acciones que el usuario podrá ejecutar.
7. Datos necesarios: entidades, documentos y relaciones que requiere el dominio.
8. Justificación de los tres modelos: qué necesidad atiende cada base.
| 4.2 Prueba | de suficiencia | de la | idea |     |     |     |     |
| ---------- | -------------- | ----- | ---- | --- | --- | --- | --- |
La idea se considera suficientemente delimitada cuando el equipo puede describir, con ejemplos,
| operaciones | que requieren | cada modelo: |     |     |     |     |     |
| ----------- | ------------- | ------------ | --- | --- | --- | --- | --- |
Una operación transaccional o de integridad que justifique el modelo relacional.
Una operación que gestione documentos, atributos anidados o estructuras flexibles que justifique
| el modelo | documental. |     |     |     |     |     |     |
| --------- | ----------- | --- | --- | --- | --- | --- | --- |
Una operación que consulte conexiones, recorridos o patrones que justifique el modelo de grafos.
Unapreguntaútilparaevaluarlapropuestaes:sieliminamosunadelastresbases,¿quécapacidad
importante de la aplicación se pierde o se vuelve claramente menos adecuada? Si la respuesta es
| “ninguna”, | la justificación     | de esa base | todavía | no es suficiente. |          |     |     |
| ---------- | -------------------- | ----------- | ------- | ----------------- | -------- | --- | --- |
| 5. Diseño  | de responsabilidades |             | de      | las bases         | de datos |     |     |
Cadaequipodebeelaborarunamatrizdeasignacióndedatosyoperaciones.Estamatrizevitaquelas
bases se construyan de manera aislada y permite definir desde el inicio qué sistema es responsable
| de cada    | dato.                |     |            |     |     |       |     |
| ---------- | -------------------- | --- | ---------- | --- | --- | ----- | --- |
| 5.1 Matriz | de responsabilidades |     |            |     |     |       |     |
| Aspecto    | Relacional           |     | Documental |     |     | Grafo |     |
Entidades o Registros principales y Expedientes, formularios Nodos y propiedades de
| datos | transacciones. |     | o   | documentos. |     | entidades | conectadas. |
| ----- | -------------- | --- | --- | ----------- | --- | --------- | ----------- |
Estructura Tablas,columnas, claves Colecciones y documen- Etiquetas, nodos, relacio-
|     | y restricciones. |     | tos | JSON/BSON. |     | nes y propiedades. |     |
| --- | ---------------- | --- | --- | ---------- | --- | ------------------ | --- |
Operaciones Altas, cambios, consultas Crear, consultar y actuali- Crear relaciones, recorrer
|     | y transacciones. |     | zar | documentos. |     | conexiones | y buscar pa- |
| --- | ---------------- | --- | --- | ----------- | --- | ---------- | ------------ |
trones.
Reglas Integridad,unicidadycon- Validacióndeestructuray Tipos de relación, direc-
sistencia transaccional. reglas documentales. ción y reglas de conecti-
vidad.
Pruebas Restricciones, transaccio- Esquema, documentos Integridaddelgrafo,cardi-
nes y consultas. válidos y consultas. nalidades y recorridos.
5

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
La matriz debe adaptarse al proyecto. No se espera que todas las bases almacenen exactamente los
mismoscamposniquetenganelmismovolumen.Seesperaquecadaunacumplaunafuncióndentro
de la aplicación.
| 5.2 Definir | la fuente | de  | verdad |     |     |     |     |     |
| ----------- | --------- | --- | ------ | --- | --- | --- | --- | --- |
Para cada entidad o dato relevante, el equipo debe identificar dónde se mantiene el valor oficial. Si el
dato se replica en otra base, debe documentarse el mecanismo de sincronización.
| Decisión |     | Pregunta | que | debe responderse |     | Evidencia | requerida |     |
| -------- | --- | -------- | --- | ---------------- | --- | --------- | --------- | --- |
Fuente de verdad ¿Enquébasesemodificaoficialmente Matriz de propiedad de datos.
|     |     | este dato? |     |     |     |     |     |     |
| --- | --- | ---------- | --- | --- | --- | --- | --- | --- |
Replicación ¿Quéinformaciónsecopiaaotrabase Justificación y campos replicados.
|     |     | y para | qué? |     |     |     |     |     |
| --- | --- | ------ | ---- | --- | --- | --- | --- | --- |
Sincronización ¿Cómo se propagan los cambios? Flujo o mecanismo implementado.
Consistencia ¿Quésucedesiunaactualizaciónfalla Política de reintento, compensación o
|     |     | parcialmente? |     |     |     | reconciliación. |     |     |
| --- | --- | ------------- | --- | --- | --- | --------------- | --- | --- |
Para un proyecto académico, una arquitectura modular con una API que coordine las tres bases
suele ser suficiente. No es necesario implementar una arquitectura de microservicios ni transacciones
distribuidas si el alcance no lo justifica. Sí es necesario reconocer y documentar que una operación
| que modifica   | varias | bases         | puede fallar | parcialmente. |     |     |     |     |
| -------------- | ------ | ------------- | ------------ | ------------- | --- | --- | --- | --- |
| 6. Metodología |        | y entregables |              |               |     |     |     |     |
Las actividades de refuerzo de las diapositivas funcionan como guías de trabajo. Cada una permite
construirunapartedelproyectoyproducirevidenciaqueseincorporaalentregablefinalcorrespondiente.
| No son tareas | independientes |         | que | se olvidan | al terminar | la actividad. |     |     |
| ------------- | -------------- | ------- | --- | ---------- | ----------- | ------------- | --- | --- |
| 6.1 Etapas    | de             | trabajo |     |            |             |               |     |     |
EtapaPropósito Trabajo que debe realizar el equipo Evidencia / entrega-
ble
1 Definición de la Delimitar problema, usuarios, objeti- Ficha de propuesta
|     | aplicación |     | vos, | alcance | y operaciones. |     | yjustificacióndelos |     |
| --- | ---------- | --- | ---- | ------- | -------------- | --- | ------------------- | --- |
tres modelos.
2 Modelado del do- Identificar entidades, atributos, docu- Modelo conceptual
minio mentos, relaciones, reglas y cardinali- y modelos lógicos
|     |     |     | dades. |     |     |     | de las tres | bases. |
| --- | --- | --- | ------ | --- | --- | --- | ----------- | ------ |
6

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
EtapaPropósito Trabajo que debe realizar el equipo Evidencia / entrega-
ble
3 Arquitectura y tec- Diseñarcomponentes,flujos,API,res- Diagrama de arqui-
nología ponsabilidades y selección del stack. tectura y matriz de
|     |     |     |     | decisión | tecnológi- |
| --- | --- | --- | --- | -------- | ---------- |
ca.
4 Diseño físico Definir tablas, colecciones, documen- Esquemas físicos y
|     | tos, etiquetas, | propiedades, | índices | y scripts iniciales. |     |
| --- | --------------- | ------------ | ------- | -------------------- | --- |
restricciones.
5 Implementación Crear y poblar las tres bases con da- Scripts SQL,
| de persistencia | tos de prueba | coherentes. |     | scripts/documen- |         |
| --------------- | ------------- | ----------- | --- | ---------------- | ------- |
|                 |               |             |     | tos de           | carga y |
scripts Cypher.
6 Consultas y prue- Construir consultas representativas y Catálogo de con-
bas de base verificarintegridad,resultadosycasos sultas y reporte de
|     | límite. |     |     | pruebas | por base. |
| --- | ------- | --- | --- | ------- | --------- |
7 Backend e inte- Implementar API, servicios y reposito- Códigodelbackend
gración rios para coordinar las tres bases. y contratos de API.
8 Interfaz de usua- Construir la interfaz que consume la Aplicaciónweb,mó-
| rio | API y permite | ejecutar | los casos de | vil o de   | escritorio |
| --- | ------------- | -------- | ------------ | ---------- | ---------- |
|     | uso.          |          |              | funcional. |            |
9 Validación inte- Probar flujos completos, errores, con- Matriz de pruebas
gral sistencia, rendimiento y concurrencia yreportederesulta-
|     | según el alcance. |     |     | dos. |     |
| --- | ----------------- | --- | --- | ---- | --- |
10 Entrega y demos- Preparar instalación, configuración, Repositorio, ma-
| tración | datos, documentación |     | y demostra- | nual, evidencias |     |
| ------- | -------------------- | --- | ----------- | ---------------- | --- |
|         | ción.                |     |             | y demostración   |     |
integrada.
6.2 Relación con las actividades de refuerzo de las diapositivas
Las actividades de refuerzo ya incluidas en el material de clase deben utilizarse como guías para
producir los componentes del proyecto. Su relación general es la siguiente:
7

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
| Actividad | de  | re- | Qué construye |     |     |     | Se incorpora | al entregable |
| --------- | --- | --- | ------------- | --- | --- | --- | ------------ | ------------- |
fuerzo
Identificar una Problema,entidades,relacionesypre- Propuesta y justificación.
| aplicación |     |     | guntas | del dominio. |     |     |     |     |
| ---------- | --- | --- | ------ | ------------ | --- | --- | --- | --- |
Diseñar la arqui- Componentes y flujo de información. Arquitectura de la solución.
tectura
Seleccionar tec- Comparación y decisión tecnológica. Matriz de selección del stack.
nologías
Especificarelser- Capacidades, operaciones, entradas Especificación funcional.
| vicio |     |     | y salidas. |     |     |     |     |     |
| ----- | --- | --- | ---------- | --- | --- | --- | --- | --- |
Implementar la Esquema, nodos, relaciones y prue- Implementación Neo4j.
| base de | grafos |     | bas. |     |     |     |     |     |
| ------- | ------ | --- | ---- | --- | --- | --- | --- | --- |
Construir catálo- Consultas y resultados esperados. Catálogo de consultas de grafos.
go Cypher
Desarrollar bac- API, servicios, repositorios y valida- Backendintegradoconlastresbases.
| kend |     |     | ción. |     |     |     |     |     |
| ---- | --- | --- | ----- | --- | --- | --- | --- | --- |
Las actividades de refuerzo relacionadas con Neo4j se conservan como parte de la implementación
de la base de grafos. El proyecto integrador amplía el alcance para incorporar también los modelos
relacional y documental y demostrar que los tres participan en una sola aplicación.
| 7. Entregables |     |     | finales |     |     |     |     |     |
| -------------- | --- | --- | ------- | --- | --- | --- | --- | --- |
El equipo deberá entregar un conjunto coherente de artefactos. Los documentos, diagramas, scripts y
| código deben   | corresponder |     | a         | la misma | versión    | del proyecto. |     |     |
| -------------- | ------------ | --- | --------- | -------- | ---------- | ------------- | --- | --- |
| 7.1 Entregable |              | 1.  | Propuesta | de       | aplicación |               |     |     |
Debe incluir:
| Nombre,       | descripción |             | y problema    |            | que atiende.  |      |         |     |
| ------------- | ----------- | ----------- | ------------- | ---------- | ------------- | ---- | ------- | --- |
| Usuarios      | y           | necesidades | principales.  |            |               |      |         |     |
| Objetivo,     | alcance     |             | y operaciones |            | prioritarias. |      |         |     |
| Justificación |             | del uso     | de las        | tres bases | de datos.     |      |         |     |
| Ejemplos      | de          | consultas   | u operaciones |            | que requieren | cada | modelo. |     |
Criterio de aceptación: La propuesta es concreta y demuestra una razón funcional para utilizar cada
paradigma.
| 7.2 Entregable |     | 2.  | Modelado | de  | datos |     |     |     |
| -------------- | --- | --- | -------- | --- | ----- | --- | --- | --- |
Debe incluir:
8

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
| Modelo | conceptual |     | común | del dominio. |     |     |     |
| ------ | ---------- | --- | ----- | ------------ | --- | --- | --- |
Modelo lógico relacional: entidades, atributos, claves y cardinalidades.
Modelo documental: colecciones, estructura de documentos, anidamiento y validaciones.
Modelo de grafo: etiquetas, propiedades, tipos de relación, dirección y cardinalidades esperadas.
| Diccionario | de  | datos | y reglas | del | dominio. |     |     |
| ----------- | --- | ----- | -------- | --- | -------- | --- | --- |
Criterio de aceptación: Los tres modelos representan el mismo dominio sin contradicciones y cada
| uno responde   | a una | responsabilidad |     |     | definida.   |     |             |
| -------------- | ----- | --------------- | --- | --- | ----------- | --- | ----------- |
| 7.3 Entregable |       | 3. Arquitectura |     |     | y selección |     | tecnológica |
Debe incluir:
| Diagrama          | de             | arquitectura |               | de la aplicación. |                |        |                    |
| ----------------- | -------------- | ------------ | ------------- | ----------------- | -------------- | ------ | ------------------ |
| Responsabilidades |                |              | del frontend, |                   | API, servicios |        | y repositorios.    |
| Tecnologías       | elegidas       |              | para          | cada              | componente.    |        |                    |
| Matriz            | de comparación |              | y             | justificación     | del            | stack. |                    |
| Definición        | de             | la fuente    | de            | verdad            | y estrategia   |        | de sincronización. |
Criterio de aceptación: La arquitectura muestra cómo la aplicación accede a las tres bases y cómo
| se coordinan   | las | operaciones.      |     |     |     |     |            |
| -------------- | --- | ----------------- | --- | --- | --- | --- | ---------- |
| 7.4 Entregable |     | 4. Implementación |     |     | de  | las | tres bases |
Base relacional:
Definición de tablas, claves primarias y foráneas, restricciones e índices justificados.
| Scripts   | SQL de          | creación | y   | carga     | de datos. |                           |     |
| --------- | --------------- | -------- | --- | --------- | --------- | ------------------------- | --- |
| Consultas | representativas |          |     | y pruebas | de        | integridad/transacciones. |     |
Base documental:
| Definición | de             | colecciones |               | y estructura |     | de documentos. |                 |
| ---------- | -------------- | ----------- | ------------- | ------------ | --- | -------------- | --------------- |
| Reglas     | de validación, |             | índices       | y estrategia |     | de             | identificación. |
| Scripts    | o mecanismos   |             | reproducibles |              | de  | carga.         |                 |
Consultas representativas y pruebas de documentos válidos e inválidos.
| Base de grafos: |           |          |            |              |             |     |               |
| --------------- | --------- | -------- | ---------- | ------------ | ----------- | --- | ------------- |
| Restricciones,  |           | índices, | etiquetas, |              | propiedades |     | y relaciones. |
| Scripts         | Cypher    | de       | creación   | y carga.     |             |     |               |
| Datos           | de prueba | y        | consultas  | funcionales. |             |     |               |
9

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
| Pruebas | de  | humo, | integridad, |     | cardinalidad | y   | resultados. |     |
| ------- | --- | ----- | ----------- | --- | ------------ | --- | ----------- | --- |
Criterio de aceptación: Las tres bases pueden construirse desde cero mediante instrucciones docu-
| mentadas       | y generan |              | datos        | coherentes      |             | con el dominio. |     |           |
| -------------- | --------- | ------------ | ------------ | --------------- | ----------- | --------------- | --- | --------- |
| 7.5 Entregable |           |              | 5. Catálogo  | de              | operaciones |                 | y   | consultas |
| Cada operación |           | debe         | documentarse |                 | con:        |                 |     |           |
| Identificador  |           | y propósito. |              |                 |             |                 |     |           |
| Base           | o bases   | que          | intervienen. |                 |             |                 |     |           |
| Parámetros     |           | de           | entrada      | y validaciones. |             |                 |     |           |
| Resultado      |           | esperado     | y formato    |                 | de salida.  |                 |     |           |
| Casos          | normales, |              | límite       | y de error.     |             |                 |     |           |
| Evidencia      |           | de ejecución |              | y resultado     | obtenido.   |                 |     |           |
El catálogo debe incluir operaciones que demuestren el uso de los tres modelos y operaciones
integradas que requieran consultar más de una base cuando el caso de uso lo demande.
| 7.6 Entregable |     |     | 6. Backend | y   | API |     |     |     |
| -------------- | --- | --- | ---------- | --- | --- | --- | --- | --- |
Debe incluir:
| API           | REST | o GraphQL, |            | según      | la decisión | justificada    |     | del equipo. |
| ------------- | ---- | ---------- | ---------- | ---------- | ----------- | -------------- | --- | ----------- |
| Controladores |      | o          | resolvers, | servicios  |             | y repositorios |     | separados.  |
| Conexión      |      | mediante   | drivers    | o clientes |             | oficiales.     |     |             |
Validación de entradas, manejo de errores y autorización acorde con el alcance.
| Consultas     |     | parametrizadas |              | y configuración |      | externa |     | de credenciales. |
| ------------- | --- | -------------- | ------------ | --------------- | ---- | ------- | --- | ---------------- |
| Documentación |     |                | del contrato | de              | API. |         |     |                  |
Criterio de aceptación: El backend coordina las bases y aplica reglas de negocio; la interfaz no se
| conecta        | directamente |     | a las         | bases | de datos.     |     |     |     |
| -------------- | ------------ | --- | ------------- | ----- | ------------- | --- | --- | --- |
| 7.7 Entregable |              |     | 7. Aplicación |       | e integración |     |     |     |
Debe incluir:
| Interfaz | funcional |          | para        | los usuarios | definidos. |                  |     |     |
| -------- | --------- | -------- | ----------- | ------------ | ---------- | ---------------- | --- | --- |
| Flujos   | que       | utilicen | información |              | de la      | base relacional. |     |     |
| Flujos   | que       | utilicen | información |              | de la      | base documental. |     |     |
| Flujos   | que       | utilicen | consultas   | de           | la base    | de grafos.       |     |     |
Al menos un caso de uso integrado que combine información de dos o más bases, cuando el
| dominio | lo  | permita. |     |     |     |     |     |     |
| ------- | --- | -------- | --- | --- | --- | --- | --- | --- |
10

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
Evidencia de que los cambios y consultas se reflejan conforme a la estrategia de consistencia
definida.
Criterio de aceptación: La solución se presenta como una sola aplicación y los tres modelos tienen
| participación |            | demostrable. |             |               |     |     |     |            |     |
| ------------- | ---------- | ------------ | ----------- | ------------- | --- | --- | --- | ---------- | --- |
| 7.8           | Entregable |              | 8. Pruebas, | documentación |     |     | y   | despliegue |     |
Debe incluir:
| Pruebas       |     | unitarias   | o de         | componentes        |                | relevantes.  |         |               |     |
| ------------- | --- | ----------- | ------------ | ------------------ | -------------- | ------------ | ------- | ------------- | --- |
| Pruebas       |     | de cada     | base         | y de integración.  |                |              |         |               |     |
| Pruebas       |     | funcionales |              | de los principales |                | casos        | de uso. |               |     |
| Pruebas       |     | de manejo   | de           | errores            | y consistencia |              | entre   | bases.        |     |
| Evaluación    |     | básica      | de           | rendimiento,       | con            | condiciones  |         | documentadas. |     |
| Instrucciones |     | de          | instalación, | configuración,     |                | carga        | y       | ejecución.    |     |
| Variables     |     | de entorno  |              | de ejemplo,        | sin            | credenciales |         | reales.       |     |
| Repositorio   |     | de          | código       | y demostración     |                | funcional.   |         |               |     |
Criterio de aceptación: Otra persona debe poder seguir la documentación y ejecutar el proyecto en
| un entorno |              | compatible. |     |             |     |          |     |     |     |
| ---------- | ------------ | ----------- | --- | ----------- | --- | -------- | --- | --- | --- |
| 8.         | Arquitectura |             | de  | integración |     | esperada |     |     |     |
La integración se realiza desde la lógica de la aplicación. La interfaz se comunica con el backend
mediante una API; el backend coordina servicios y repositorios especializados para cada base.
Interfazdeusuario:aplicaciónweb,móvilodeescritorio
APIRESToGraphQL:contratodeentradaysalida
Serviciosdeaplicación:reglasdenegocio,validaciónycoordinación
| Baserelacional |     |     |     |     |     | Basedocumental |     |     | Basedegrafos |
| -------------- | --- | --- | --- | --- | --- | -------------- | --- | --- | ------------ |
|                | SQL |     |     |     |     | JSON/BSON      |     |     | Neo4j/Cypher |
Lectura del diagrama: la interfaz no conoce las credenciales ni la estructura interna de las bases. La
API recibe solicitudes; los servicios deciden qué operaciones ejecutar; los repositorios encapsulan las
consultas de cada motor. Cuando una función requiere información de más de una base, el servicio
| coordina | la  | lectura | o escritura | y construye |     | una respuesta |     | única. |     |
| -------- | --- | ------- | ----------- | ----------- | --- | ------------- | --- | ------ | --- |
11

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
| 8.1 Ejemplo |     | de  | flujo | integrado |     |     |     |     |
| ----------- | --- | --- | ----- | --------- | --- | --- | --- | --- |
Enunaplataformadeproyectosacadémicos,unaoperacióncomo“consultarelperfildeuninvestigador
| y sus colaboraciones” |     |          | podría | funcionar |                    | así: |             |     |
| --------------------- | --- | -------- | ------ | --------- | ------------------ | ---- | ----------- | --- |
| 1. La interfaz        |     | solicita | el     | perfil y  | sus colaboraciones |      | al backend. |     |
2. El backend consulta en la base relacional los datos principales y el estado de los proyectos.
3. Consulta en la base documental el expediente, líneas de trabajo o información complementaria
| con | estructura |     | flexible. |     |     |     |     |     |
| --- | ---------- | --- | --------- | --- | --- | --- | --- | --- |
4. Consultaenlabasedegrafoslasrelacionesentreinvestigadores,proyectos,publicacionesyáreas
de conocimiento.
5. El servicio integra los resultados, controla datos faltantes y devuelve una respuesta coherente.
| 6. La interfaz |     | presenta | una | sola | vista | al usuario. |     |     |
| -------------- | --- | -------- | --- | ---- | ----- | ----------- | --- | --- |
Este ejemplo es ilustrativo. Cada equipo debe construir un flujo equivalente que tenga sentido en su
propio dominio.
| 9. Pruebas |     | obligatorias |     |     | de  | integración |     |     |
| ---------- | --- | ------------ | --- | --- | --- | ----------- | --- | --- |
No basta con demostrar que cada motor funciona por separado. La integración debe verificarse con
| escenarios | de     | extremo | a   | extremo. |             |     |     |           |
| ---------- | ------ | ------- | --- | -------- | ----------- | --- | --- | --------- |
| Tipo de    | prueba |         | Qué | debe     | verificarse |     |     | Evidencia |
Conectividad El backend se conecta a los tres moto- Registrodeconexiónypruebaautoma-
|     |     |     | res con | configuración |     | segura. |     | tizada. |
| --- | --- | --- | ------- | ------------- | --- | ------- | --- | ------- |
Funcional Las operaciones de la aplicación pro- Casos de prueba y resultados.
|     |     |     | ducen | resultados |     | esperados. |     |     |
| --- | --- | --- | ----- | ---------- | --- | ---------- | --- | --- |
Integridad Lasreglasdecadamodelosecumplen. Consultas de validación.
Integración Una operación coordina correctamente Prueba de extremo a extremo.
|     |     |     | dos o | más | bases. |     |     |     |
| --- | --- | --- | ----- | --- | ------ | --- | --- | --- |
Consistencia Las actualizaciones replicadas no de- Escenariodeactualizaciónyreconcilia-
|     |     |     | janinformacióncontradictoriasindetec- |     |     |     |     | ción. |
| --- | --- | --- | ------------------------------------- | --- | --- | --- | --- | ----- |
tar.
Errores Se manejan fallos de conexión, datos Pruebas negativas y evidencia del ma-
|     |     |     | inválidos | y   | escrituras | parciales. |     | nejo. |
| --- | --- | --- | --------- | --- | ---------- | ---------- | --- | ----- |
Rendimiento Los flujos prioritarios responden en Mediciones con entorno y datos descri-
|     |     |     | tiempos | razonables |     | para el | alcance. | tos. |
| --- | --- | --- | ------- | ---------- | --- | ------- | -------- | ---- |
Atención a las escrituras múltiples. Si una operación actualiza dos bases y la segunda falla, no
sedebeafirmarquelaoperaciónfuecompletamenteexitosa.Elequipodebedefinircómodetectar
elfallo,reintentar,compensaroreconciliarlosdatos.Paraelalcanceacadémicopuedebastaruna
| estrategia | sencilla |     | y documentada, |     |     | pero no ignorar | el problema. |     |
| ---------- | -------- | --- | -------------- | --- | --- | --------------- | ------------ | --- |
12

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
| 10. Organización |     | del repositorio |     |     |
| ---------------- | --- | --------------- | --- | --- |
La estructura puede adaptarse al stack elegido. Una organización posible es:
proyecto/
|-- docs/
| | |-- | propuesta.md               |     |     |     |
| ----- | -------------------------- | --- | --- | --- |
| | |-- | modelos/                   |     |     |     |
| | |-- | arquitectura.md            |     |     |     |
| | |-- | decisiones-tecnologicas.md |     |     |     |
| | |-- | api/                       |     |     |     |
| | ‘-- | pruebas/                   |     |     |     |
|-- database/
| | |-- | relational/     |     |     |     |
| ----- | --------------- | --- | --- | --- |
| | |   | |-- schema/     |     |     |     |
| | |   | |-- data/       |     |     |     |
| | |   | ‘-- queries/    |     |     |     |
| | |-- | document/       |     |     |     |
| | |   | |-- validators/ |     |     |     |
| | |   | |-- data/       |     |     |     |
| | |   | ‘-- queries/    |     |     |     |
| | ‘-- | graph/          |     |     |     |
| |     | |-- schema/     |     |     |     |
| |     | |-- data/       |     |     |     |
| |     | |-- queries/    |     |     |     |
| |     | ‘-- tests/      |     |     |     |
|-- backend/
| | |-- | controllers-or-resolvers/ |     |     |     |
| ----- | ------------------------- | --- | --- | --- |
| | |-- | services/                 |     |     |     |
| | ‘-- | repositories/             |     |     |     |
| |     | |-- relational/           |     |     |     |
| |     | |-- document/             |     |     |     |
| |     | ‘-- graph/                |     |     |     |
|-- frontend/
|-- tests/
| | |-- | unit/        |     |     |     |
| ----- | ------------ | --- | --- | --- |
| | |-- | integration/ |     |     |     |
| | ‘-- | e2e/         |     |     |     |
|-- .env.example
|-- docker-compose.yml
‘-- README.md
| 11. Criterios | para | considerar | completo | el proyecto |
| ------------- | ---- | ---------- | -------- | ----------- |
El proyecto estará listo para evaluación cuando se pueda comprobar lo siguiente:
1. La aplicación resuelve un problema delimitado y tiene usuarios y operaciones identificables.
2. El uso de los tres modelos está justificado por necesidades distintas y concretas.
| 3. Los modelos | de datos       | son coherentes | entre sí y              | con el dominio. |
| -------------- | -------------- | -------------- | ----------------------- | --------------- |
| 4. Las tres    | bases se crean | y cargan       | de manera reproducible. |                 |
13

UniversidadPolitécnicadeChiapas Proyectointegradordebasesdedatos
| 5. Cada | base tiene | consultas | y pruebas | que | demuestran |     | su función. |
| ------- | ---------- | --------- | --------- | --- | ---------- | --- | ----------- |
6. El backend accede a las tres bases mediante componentes separados y contratos definidos.
7. La interfaz consume el backend y no accede directamente a los motores de datos.
8. Existe al menos un flujo integrado que demuestra la coordinación entre bases.
9. Los errores y los posibles problemas de consistencia se reconocen y gestionan.
10. La documentación permite instalar, configurar y ejecutar la solución.
| 12. Errores | que | deben |     | evitarse |     |     |     |
| ----------- | --- | ----- | --- | -------- | --- | --- | --- |
Elegir primero tres motores y después inventar una justificación para utilizarlos.
Construir tres bases aisladas que no participan en una misma aplicación.
Guardar los mismos datos en las tres bases sin definir fuente de verdad ni sincronización.
| Presentar | diagramas | sin | scripts, | o scripts | sin evidencia |     | de ejecución. |
| --------- | --------- | --- | -------- | --------- | ------------- | --- | ------------- |
Confundir una consulta exitosa con una validación completa del modelo.
| Conectar | la interfaz | directamente |     | a las bases | de  | datos. |     |
| -------- | ----------- | ------------ | --- | ----------- | --- | ------ | --- |
Reportar que la integración funciona cuando solo se probaron las bases por separado.
Dejar la documentación, pruebas y despliegue para el final sin considerarlos durante el diseño.
| 13. Cómo | debe | entenderse |     | la entrega |     | final |     |
| -------- | ---- | ---------- | --- | ---------- | --- | ----- | --- |
La entrega final es una sola aplicación integrada, respaldada por tres bases de datos espe-
cializadas. El equipo debe demostrar qué responsabilidad tiene cada base, cómo se comunican
mediante el backend, qué operaciones resuelve la aplicación y qué evidencia confirma que la
| solución | funciona. |     |     |     |     |     |     |
| -------- | --------- | --- | --- | --- | --- | --- | --- |
Las actividades de refuerzo desarrolladas durante el curso son avances y evidencias parciales de
este resultado. Al finalizar, deben estar revisadas, corregidas y articuladas en un solo proyecto. No
se trata de acumular documentos o capturas, sino de demostrar que las decisiones de modelado,
implementación e integración permiten resolver el problema propuesto.
|     |     | Del | problema | a una | aplicación |     | integrada |
| --- | --- | --- | -------- | ----- | ---------- | --- | --------- |
Tres modelos de datos. Una arquitectura coherente. Una solución verificable.
14
