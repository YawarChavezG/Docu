```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

# HISTORIAS DE USUARIO

# DIGITALIZACION DEL PROCESO DE GESTIÓN

# DOCUMENTAL

### APROBACIÓN

```
Nombre Cargo Firma Fecha
Elaborado
por: Aracely Romero^
```
```
Analista de optimización de
procesos^^30 /0^4 /^
Revisado
por: Jasiel Sanjines^
```
```
Jefe de excelencia y
transformación organizacional^^30 /0^4 /^
Aprobado
por: Nombre Apellido^^^30 /0^4 /^
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

## SISTEMA DE GESTION DOCUMENTAL

El documento se desarrolla en base a la siguiente agrupación de Sprints:

1. **Épica 1: Autenticación, Perfil y Delegación Activa** (Login, Doble Auth, Configuración de
    suplentes, Vacaciones, Desvinculaciones).
2. **Épica 2: Solicitud y Elaboración Documental** (Flujo editable, Formulario de creación, Árbol de
    Outlook, Reemplazos).
3. **Épica 3: Workflow de Revisión y Aprobación** (Bandeja, Bitácora Timeline, Devoluciones,
    Tiempos límite de 10 días, Reasignación automática).
4. **Épica 4: Control y Liberación ETO** (Análisis IA de similitud, Ajuste de revisores, Modificación de
    árbol de difusión).
5. **Épica 5: Publicación y Lista Maestra** (Pase automático a VIGENTE, Notificaciones Outlook +
    ETO cc, Visor PDF con zoom/rotación, Obsolescencia automática).
6. **Épica 6: Capacitación y Certificación** (Controles de lectura a 1 mes, Evaluaciones IA, Nota más
    alta, Estados "No Ejecutado", Exención ETO).
7. **Épica 7: Trazabilidad Física** (Generación de CC/CN, Recepción con Firma del usuario,
    Devolución con Firma ETO).
8. **Épica 8: Monitoreo, Consultas e IA** (Buscador general, Reportes de tiempos, Chat Inteligente a
    la BD).
9. **ÉPICA 9: Administración del Sistema y Parametrización Global** (Configuración de variables de
    tiempo y SLA, Panel de restricciones, Gestión de Diccionarios y Matriz de Enrutamiento, Gestor
    de Plantillas de notificaciones email).


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

#### ÉPICA 1: AUTENTICACIÓN, PERFIL DE USUARIO Y GESTIÓN DE DELEGACIONES

Esta épica abarca el acceso al sistema, la identificación del rol del usuario, la gestión de sus datos
personales y, de forma crítica, las reglas de negocio automatizadas para evitar cuellos de botella mediante
delegaciones temporales o definitivas.

**US-1.01: Autenticación y Enrutamiento Basado en Roles**

- **Como** empleado de COFAR
- **Quiero** iniciar sesión en el Sistema de Gestión Documental usando mis credenciales corporativas
    las mismas que se usan para iniciar sesión en el sistema de boletas de pago.
- **Para** acceder a mi espacio de trabajo con los permisos y menús que corresponden estrictamente
    a mi cargo.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que me encuentro en la pantalla de inicio (login-overlay).
o Cuando ingreso mi usuario y contraseña y presiono "Enter" o hago clic en "Iniciar Sesión".
o Entonces el sistema debe validar mis credenciales.
o Y si son correctas, la pantalla de login debe desaparecer y mostrar la interfaz principal
(main-app).
o Y el Sidebar debe renderizar únicamente las opciones correspondientes a mi rol (ej.
Ocultar los monitores CC/CN si soy usuario solicitante; mostrar todo si soy ETO).
o Y debo aterrizar por defecto en la pantalla "Mi Bandeja de Tareas".
```
- **Reglas de Negocio / Backend:**
    1. **Autenticación (SSO/LDAP):** Las credenciales deben validarse contra el Directorio Activo
       de la empresa.
    2. **Variables de Sesión:** Al logearse, el backend debe inyectar en sesión los datos del
       usuario (Nombre, Cargo, Área, Gerencia, Rol en SGD) para poblar dinámicamente la
       esquina inferior izquierda del menú y el avatar con sus iniciales.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

**US-1.02: Visualización de Mi Perfil de Usuario**

- **Como** usuario autenticado
- **Quiero** poder visualizar mi información corporativa dentro del sistema
- **Para** confirmar que mis datos y mi asignación de área están correctos para los flujos
    documentales.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que estoy logeado en el sistema.
o Cuando hago clic en el botón " Mi Perfil" en la parte inferior del menú lateral.
o Entonces se debe abrir el modal modal-perfil superponiéndose a la pantalla actual.
o Y debe mostrar claramente mi avatar, Nombre Completo, Cargo, Área y Gerencia a la que
pertenezco.
```
**US-1.03: Configuración Manual de Delegado (Back-up)**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Como** usuario del sistema con tareas asignadas
- **Quiero** poder buscar y seleccionar a un compañero de trabajo como mi "Delegado"
- **Para** que asuma mis responsabilidades de revisión o aprobación cuando yo no pueda hacerlo.

**Nota:**
En la salida del sistema esta matriz ya será inyectada al sistema es decir cada usuario que REVISA Y/O
APRUEBA documentos ya debe contar con su delegado al asignársele el usuario a fin de evitar la omisión
de este proceso por parte de los usuarios.

En caso de que mi delegado configurado se retire de la organización o cambie de cargo/ área, debería
aparecer una alerta en mi perfil (signo de exclamación) que indique al usuario que debe cambiar a su
delegado, esta alerta debe permanecer hasta que el usuario defina un nuevo delegado.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que estoy dentro del modal de "Mi Perfil".
o Cuando escribo un nombre en el campo predictivo "Delegado (Back-up) y Ausencias" y
selecciono a un empleado válido.
o Y hago clic en "Guardar" sin marcar la opción de ausencia.
o Entonces el sistema debe mostrar el mensaje flotante " Delegado actualizado. Usted
sigue recibiendo sus tareas."
o Y en la interfaz debe actualizarse el estado de "No asignado" al nombre del nuevo
delegado.
```
- **Reglas de Negocio / Backend:**
    1. **Validación de Identidad:** Un usuario no puede seleccionarse a sí mismo como delegado.
    2. **Jerarquía:** El sistema no restringirá la delegación por jerarquía (un Gerente puede delegar
       a un Analista), asumiendo que es una responsabilidad operativa corporativa.
    3. **Estado Pasivo:** Configurar un delegado de esta forma lo mantiene "en la banca". Las
       tareas seguirán llegando al usuario original a menos que se cumplan las reglas de
       ausencia o _fuera de tiempo_ (ver siguientes US).

**US-1.04: Programación de Ausencia (Vacaciones / Licencias) y Enrutamiento**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

**Nota. -** Esto únicamente aplica a roles de GESTOR DOCUMENTAL Y ROLES DE REVISIÓN/
APROBACIÓN, ROLES DE VISUALIZACION no requieren un delegado.

- **Como** usuario que saldrá de vacaciones o licencia
- **Quiero** poder programar en el sistema mi periodo de ausencia
- **Para** que el sistema enrute automáticamente mis tareas a mi delegado sin que el flujo documental
    se estanque.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que estoy en "Mi Perfil" y ya tengo un delegado seleccionado.
o Cuando marco el checkbox " Marcarme como ausente".
o Entonces se deben desplegar los campos obligatorios de fecha "Desde" y "Hasta".
o Y al guardar, el estado del delegado en el modal debe cambiar mostrando una etiqueta
roja que indique "AUSENTE: [Fecha Inicio] al [Fecha Fin]".
```
- **Reglas de Negocio / Backend (Automatizaciones):**
    1. **Validación de Fechas:** El backend rechazará la configuración si la fecha "Desde" es
       posterior a la fecha "Hasta", o si son fechas pasadas.
    2. **Enrutamiento Automático Activo:** A las 00:00 hrs de la fecha "Desde", el sistema
       cambiará el estado interno del usuario a "Ausente". Cualquier tarea de Revisión o
       Aprobación que intente caer en su bandeja, será redirigida automáticamente a la bandeja
       de su delegado.
    3. **Notificación:** El sistema enviará un correo (Outlook) al delegado informando: "Ha recibido
       tareas derivadas por ausencia temporal de [Usuario Original]".
    4. **Retorno Automático:** A las 23:59 de la fecha "Hasta", el estado vuelve a "Activo" y las
       tareas nuevas volverán a caer al usuario original.

**US-1.05: Reasignación Automática por Vencimiento de SLA (Time-out de 10 días)**

- **Como** Gestor ETO / Administrador del Sistema
- **Quiero** que el sistema detecte a los usuarios inactivos y reasigne sus tareas automáticamente
- **Para** evitar que la aprobación de un documento clave quede paralizada por negligencia u olvido
    de un aprobador/revisor.

**Nota. -** el plazo de 10 días no aplica para ETO. Las tareas pueden quedarse un plazo indefinido.

- **Criterios de Aceptación (Frontend/UI):**
    o _Esta es una funcionalidad 100% de Backend, se reflejará en la Bitácora del documento en_
       _el Frontend._
    o **Dado que** reviso la bitácora de un documento.
    o **Entonces** debo ver un registro automático indicando la reasignación por límite de tiempo.
- **Reglas de Negocio / Backend (Automatizaciones):**
    1. **Cron Job Diario:** El sistema ejecutará un proceso nocturno que evaluará la antigüedad
       de todas las tareas pendientes ("En Revisión", "En Aprobación").
    2. **Regla de 10 Días:** Si una tarea específica lleva más de **10 días hábiles** (a definir
       parámetro exacto en BD y editable en Parametrización general **Epica 9** ) asignada a un
       usuario sin haber sido atendida (ni aprobada ni devuelta).


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
3. **Reasignación Forzada:** El sistema quitará la tarea del usuario moroso y la inyectará en
la bandeja de su **delegado** configurado a excepción de los usuarios que pertenezcan al
area de ETO.
4. **Registro de Bitácora:** Se insertará una fila automática en la bitácora (Timeline) del
documento:
▪ _Etapa:_ Revisión / Aprobación
▪ _Acción:_ Reasignación Automática (Color: plomo)
▪ _Usuario:_ Sistema SGD
▪ _Observaciones:_ "Plazo de 10 días excedido. Tarea reasignada automáticamente
de [Usuario Original] a su delegado [Nombre Delegado]."
5. **Notificación Cero Tolerancia:** Se enviará un correo de Outlook alertando al Usuario
Original, al delegado, y con copia a ETO informando la delegación de la tarea ante el
incumplimiento de plazos establecidos.

**US-1.06: Redirección de Flujos por Desvinculación de Personal**

- **Como** Administrador del Sistema SGD
- **Quiero** que el sistema audite si los usuarios con tareas pendientes siguen trabajando en la
    empresa
- **Para** que los flujos documentales no queden atrapados en cuentas de usuarios eliminadas o
    desactivadas.
- **Criterios de Aceptación (Frontend/UI):**

```
o Funcionalidad de Backend. Reflejada en la bitácora de la UI.
```
- **Reglas de Negocio / Backend (Automatizaciones):**
    1. **Sincronización Maestra:** El sistema debe sincronizarse periódicamente con la base de
       datos de Recursos Humanos (Active Directory).
    2. **Detección de Baja:** Cuando el sistema detecte que el estado de un usuario cambia a
       "Desvinculado / Inactivo".
    3. **Barrido de Pendientes:** El backend buscará absolutamente todas las tareas "En
       ejecución" donde este usuario sea Elaborador, Revisor, o Aprobador.
    4. **Transferencia de Cargo:** * **Si tiene delegado configurado:** Las tareas pasan
       inmediatamente al delegado.

**Si NO tiene delegado configurado (Fallback):** Las tareas se envían a la bandeja de su Jefatura Inmediata
(según organigrama de AD/SAP). Si tampoco se encuentra jefatura, la tarea pasa a ETO en la actividad
correspondiente del proceso y ETO realizará la reasignación manual.

5. **Registro de Bitácora:** En todos los documentos afectados, la bitácora indicará:
    "Reasignación administrativa por desvinculación de usuario". Y marcará/ identificará al
    usuario al que fue resignado la tarea.

**US-1.07: Matriz de Enrutamiento Automático para Gestores ETO**

- **Como** Administrador del Sistema
- **Quiero** que las solicitudes se enruten al Analista ETO correspondiente según la gerencia origen
- **Para** balancear la carga de trabajo de los analistas de ETO y evitar cuellos de botella.
- **Criterios de Aceptación (Frontend/UI):**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Dado que (Posible escenario) el "Analista ETO 1" tiene asignada la "Gerencia
Administrativa" y el "Analista ETO 2" la "Gerencia de Producción".
o Cuando un usuario de Producción envía una nueva solicitud.
o Entonces en la pantalla "Bandeja de Tareas", la solicitud solo debe aparecer visible para
el "Analista ETO 2".
o Y si el "Analista ETO 1" ingresa a su propia bandeja, no debe visualizar esa tarea.
o A creación de estas tareas deben notificarse a los respectivos analistas de ETO VIA
EMAIL, ejemplo si es una solicitud de producción notificar el proceso por correo al analista
ETO 2.
```
- **Reglas de Negocio / Backend:**
    1. **Matriz de Asignación (BD):** Existirá una tabla relacional que vincule cada Gerencia (Ej:
       Administrativa, Producción, Logística) con el ID_Usuario de un Analista ETO específico.
       **Revisar la U-9.**.
    2. **Enrutamiento Dinámico:** Cuando un usuario finaliza el Paso 4 del formulario de solicitud
       (Épica 2), el sistema leerá la "Gerencia Responsable" seleccionada. En lugar de mandar
       la tarea a una bandeja genérica de ETO, la asignará unívocamente a la "Bandeja de
       Tareas" del Analista ETO correspondiente a esa matriz.
    3. **Contingencia de Ausencia (Cascada):** Si el Analista ETO designado está con estado
       "Ausente" (vacaciones/licencia), el sistema buscará primero a su "Delegado configurado".
       Si no tiene delegado, la tarea se balanceará automáticamente (Round-Robin) hacia los
       otros Analistas ETO disponibles.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

#### ÉPICA 2: SOLICITUD Y ELABORACIÓN DOCUMENTAL

Esta épica abarca desde la descarga de un documento base para trabajar- documento existe (flujo corto),
solicitar las plantillas para la creacion de un documento segun el tipo, hasta el diligenciamiento completo
del asistente (wizard) de 4 pasos para ingresar un documento nuevo o actualizado al flujo de revisión de
COFAR.

**US-2.00: Gestión y Descarga de Plantillas Documentales (Flujo Corto)**

**Descripción:** Como Usuario Estándar (Solicitante/Revisor/Aprobador) o Gestor Documental (ETO), quiero
poder visualizar y descargar los formatos o plantillas oficiales correspondientes al documento que estoy
elaborando, y (como ETO) administrar dichas plantillas, para asegurar que la creación de documentos
parta siempre de la estructura corporativa vigente.

**Criterios de Aceptación:**

```
o Acceso por Rol: El módulo de descarga de plantillas solo debe ser visible y accesible para los
roles Usuario Estándar y Gestor Documental (ETO). Los roles Visualizador y Administrador no
deben ver esta opción.
o Descargas Ilimitadas: El sistema debe permitir la descarga de estos formatos (esqueletos vacíos)
sin aplicar el límite diario de descargas de documentos editables, ya que no contienen información
confidencial.
o Galería Clasificada: Las plantillas deben mostrarse en una lista o galería organizadas según el
"Tipo de Documento" (Ej. Plantilla de Procedimiento, Plantilla de Manual, etc.).
o Administración Exclusiva (Poder ETO): El rol ETO debe visualizar botones adicionales en este
módulo para hacer mantenimiento de las plantillas (Subir una nueva plantilla, actualizar una
existente o darla de baja si el formato cambia en el tiempo).
```
**Reglas de Negocio (Backend):**

1. **Protección de Endpoints (RBAC Fuerte):** El backend debe denegar activamente (HTTP 403
    Forbidden) cualquier petición al endpoint de descarga o listado de plantillas si el token de sesión
    pertenece a un Administrador del Sistema o a un Usuario Visualizador.
2. **Auditoría de Modificación (ETO):** Cuando el ETO agrega, modifica o elimina una plantilla, el
    backend debe registrar la acción en la bitácora de auditoría (quién subió el nuevo formato, cuándo
    y a qué tipo de documento pertenece).


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
3. **Almacenamiento Seguro:** Los archivos de las plantillas (.docx, .xlsx) deben guardarse en un
repositorio centralizado, asegurando que, si el ETO sube una "Versión 2" de la plantilla de
Procedimientos, esta reemplace automáticamente a la anterior para todos los usuarios.

**US-2.01: Descarga de Documento en Versión Editable (Flujo Corto)**

- **Como** elaborador de un documento
- **Quiero** poder buscar y descargar la versión editable original (Word/Excel) de un documento
    vigente
- **Para** poder realizar modificaciones, correcciones o actualizaciones sobre el archivo real antes de
    iniciar una solicitud de actualización.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que ingreso a "Nueva Solicitud" > "Documento en versión editable".
o Cuando ingreso un código en el campo "Código del documento requerido" (el campo debe
forzar mayúsculas automáticamente).
o Y presiono el botón " Buscar".
o Entonces el botón debe mostrar un spinner (animación de carga) simulando la consulta.
o Y si el código existe, se debe desplegar una tarjeta de "Resultado encontrado" mostrando
el nombre del archivo principal y notificando si contiene anexos.
o Y al hacer clic en "Descargar Editable", el sistema debe descargar los archivos.
```
- **Reglas de Negocio / Backend (Contingencias):**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
1. **Límite de Descargas de Seguridad:** El backend debe registrar cuántas descargas realiza
un usuario por día.
2. **Regla General:** Solo se permite la descarga de **1 documento por día**.
3. **Excepción "METODOLOGÍAS Y ESPECIFICACIONES":** Si el código del documento
inicia con CC-1 O CC- 7 (Metodologías y Especificaciones), el sistema permitirá descargar
hasta **10 documentos por día**. (si es 1 o 7)
4. **Parametros:** Los parámetros de descargas por día y excepciones se podrán configurar
desde la interfaz de parametrización general explicada en la **US- 9 - 02**.
5. **Bloqueo:** Si el usuario supera el límite, el backend devolverá un error y la UI mostrará un
_toast_ rojo: "Ha superado el límite diario de descargas permitidas para su perfil."

**US-2.02: Formulario de Aprobación (Paso 1) - Datos del Documento**

- **Como** solicitante/elaborador
- **Quiero** completar la metadata principal del documento
- **Para** que el sistema lo clasifique, asigne códigos automáticos y registre la auditoría de mi solicitud.
- **Criterios de Aceptación / Explicación de Campos:**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Tipo de documento (Desplegable - Obligatorio): Permite elegir entre Procedimiento
( 5 PRO), Instructivo ( 6 INS), Formulario (FOR), Manual (MAN 10 ), Metodología (MET 1 ), etc.
(Listado de tipos de documentos a definir con ETO) Se pueden modificar estos campos,
revisar la US- 9..
o Gerencia responsable (Desplegable - Obligatorio): Lista las gerencias mayores (CAL,
PRO, RRH, LOG, GER). Listado de gerencias de definir con ETO
o Área responsable (Desplegable - Obligatorio): Lista las sub-áreas específicas
dependientes de una gerencia. Listado a defInir con ETO
o Tipo de solicitud (Desplegable - Obligatorio): Opciones: "Creación nuevo documento"
o "Actualización de documento".
```
En este punto aclarar que, ante la salida del sistema, toda la codificación sería nueva como creación de
documento, sin embargo, una vez que un documento ya haya sido gestionado por el sistema tendrá un
código único, si este mismo documento posteriormente se actualiza, recien funcionaria como una
“actualización de documento” referente a la codificación automática que asignará el sistema. AHORA
DONDE SE COLOCARÁ EL CODIGO ANTIGUO “ORIGINAL” DEL DOCUMENTO considerando que este
codigo antiguo posteriormente se muestra en lista maestra.

```
o Código automático (Campo de Texto – Bloqueado/Readonly): Lógica: Se concatena
dinámicamente la sigla del “Área” , un guion, sigla “Tipo de Documento”, un guion, y un
correlativo de 3 dígitos. Ejemplo: PRO-CAL-0XX. MAN-INS- 001 este código automático
debe plasmarse dentro del documento original
o Versión (Campo de Texto – Bloqueado/Readonly): Lógica: Si es “Creación”, muestra
00. Si es “Actualización” (y el sistema detecta que el documento a actualizar era la v02),
mostrará 03. Esta versión automática debe plasmarse dentro del documento original
o Título del documento (Campo de Texto – Obligatorio): Campo libre para el nombre del
documento debe ser igual al nombre que se encuentra en el encabezado del documento
principal
```
```
Una vez aprobado el documento, el sistema debe generar el conteo de hojas considerando
que la caratula es la hoja 0
o Elaborador responsable (Campo de Texto - Bloqueado): El backend inyecta
automáticamente el Nombre del usuario logeado.
o Cargo (Campo de Texto - Bloqueado): El backend inyecta el cargo oficial extraído de
SAP/AD.
o Fecha (Campo de Texto - Bloqueado): Fecha del día extraída del servidor.
o Justificación / motivo (Área de Texto - Obligatorio): Espacio extenso para que ETO y
revisores entiendan por qué se está creando o modificando este archivo. CAMPO NO
OBLIGATORIO
```
- **Reglas de Negocio / Backend:**
    1. A cada documento se le asigna un código único, en caso de eliminarse alguna solicitud/
       proceso (que cuenta con un codigo asignado) este queda disponible y debe ser utilizado
       en una nueva solicitud según el tipo de documento y área. **Lista de Gerencias y áreas:**
       Estas listas serán parametrizables en la sección de Parametrización General US-9. 05


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
2. Si se selecciona en el desplegable de Tipo de solicitud en Creación de un nuevo
documento el sistema deberá en base al tipo de documento y area codificar el código en
versión 0. Si el usuario selecciona Actualización de un documento el sistema deberá
esperar para codificar hasta que el usuario suba su documento principal, revisará el
encabezado que tiene y verá cuál era su código para que en base a ello se autocomplete
el campo de Codigo y la versión que corresponda.

**US-2.03: Formulario de Aprobación (Paso 2) - Vigencia y Difusión (Outlook)**

- **Como** solicitante/elaborador
- **Quiero** definir si el documento requerirá lectura obligatoria y a quiénes afectará así mismo, quiero
    definir a quienes se debe notificar la creación o actualización de un documento.
- **Para** que el personal realice y registre sus evaluaciones y controles e lectura en el sistema y para
    que el sistema sepa a qué grupos de correo enviar el documento una vez publicado.
- **Criterios de Aceptación / Explicación de Campos:**

```
o Tiempo de vigencia (Campo Readonly): Fijo en "4 años" por norma general, editable
solo excepcionalmente por ETO en la liberación. Segun el tipo de documento las vigencias
podran variar, en su mayoria son 4 años. Matriz a comunicar por ETO que se transmitira
a la parametrizacion del sistema.
o Requiere evaluación (Desplegable): Sí/No. (Define si al final del flujo ETO deberá crear
un examen).
o Requiere control de lectura (Desplegable): Sí/No. (Define si se pedirá firma de lectura
a los definidos en el grupo de difusión ). si bien un gerente/ jefe/encargado que ha
revisado/ aprobado un documento forma parte del grupo de difusión, este no debe
presentar el control de lectura ni examen, por lo tanto se debe excluir a personal que haya
estado involucrado en la elaboración/ revisión y aprobación del documento.
o Alcance de difusión / Árbol de Outlook (Componente Avanzado - Obligatorio):
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
▪ Dado que hago clic en "Seleccionar grupos de difusión".
▪ Entonces se despliega un árbol jerárquico.
▪ Comportamiento del Árbol (UI): * Si marco una Gerencia (Padre), se deben
marcar todos sus departamentos (Hijos).
▪ Si marco solo algunos departamentos (Hijos), el checkbox de la Gerencia
(Padre) debe ponerse en estado "Indeterminado" (cuadrito/guion), no en
"Check" (palomita).
▪ Chips Visuales: Al marcar opciones, debajo del árbol deben generarse "Chips"
(Etiquetas azules/verdes con una X). Si selecciono toda la Gerencia, se crea 1
chip padre. Si selecciono ramas específicas, se crean chips por cada rama. Al
hacer clic en la "X" de un chip, se debe desmarcar automáticamente en el árbol.
```
- **Reglas de Negocio / Backend:**
    1. **Mapeo de AD (Active Directory):** Cada "nodo" de ese árbol está vinculado en backend a
       un _Distribution List_ (Grupo de correo) de Outlook (Microsoft Exchange).
    2. Al guardarse, el sistema guarda los IDs de esos grupos para gatillar los correos
       automáticos en la Épica 5.

**US-2.04: Formulario de Aprobación (Paso 3) - Carga Física de Archivos**

- **Como** solicitante/elaborador
- **Quiero** subir mi archivo Word principal y los formularios Excel o word asociados
- **Para** que sean los que viajen por todo el flujo de revisión.
- **Criterios de Aceptación (Frontend/UI):**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Zonas de Drop: Existirán dos recuadros de línea punteada, uno para el documento
principal y otro para anexos.
o Validación Frontend: El input de archivo principal solo debe aceptar la extensión .docx.
El de anexos debe aceptar .docx y .xlsx.
```
- **Reglas de Negocio / Backend (Contingencias):**
    1. **Límite de Peso:** El servidor rechazará archivos mayores a 20MB.
    2. **Escaneo Antivirus:** Todo archivo cargado pasará por una validación de seguridad (ej.
       ClamAV en servidor) antes de alojarse en el repositorio temporal.
    3. **Renombrado Automático:** Al subirse, el backend renombrará el archivo concatenando el
       código provisional y el nombre del usuario para evitar colisiones (Ej: TEMP_PRO-CAL-
       0XX_JuanPerez_v01.docx).

**US-2.05: Formulario de Aprobación (Paso 4) - Actores del Flujo y Reemplazos**

- **Como** solicitante/elaborador
- **Quiero** designar quién revisará y quién aprobará el documento, y a qué documentos podría
    reemplazar o dar de baja mi nueva version del documento
- **Para** obtener un documento revisado y aprobado por las instancias correspondientes contando
    con sus firmas digitales como respaldo.
- **Criterios de Aceptación / Explicación de Campos:**

```
o Revisores y Aprobadores asignados (Inputs Dinámicos): * Tienen un botón "
Agregar Revisor/Aprobador" que añade filas infinitas.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
▪ Tienen un botón "✕" para eliminar filas que se haya creado por error
▪ El campo de texto es un datalist autocompletable.
o ¿Este documento reemplaza a otro? (Desplegable + Input Chips):
▪ Si elijo "No", no pasa nada.
```
```
▪ Si elijo "Sí", aparece un input especial.
```
```
▪ Al escribir un código (Ej: CAL-MAN-001) y presionar "Enter" o "Coma", el texto se
transforma en un Chip visual (etiqueta gris con una X para borrar).
```
- **Reglas de Negocio / Backend:**
    1. **Validación de Mínimos:** Es imposible enviar el formulario si no hay _exactamente_ al menos
       1 Revisor válido y 1 Aprobador válido seleccionados.
    2. **Verificación de Directorio:** El backend cruzará los nombres ingresados contra la base de
       datos de usuarios activos. Directamente al intentar escribir el nombre de un usuario, si
       este no existe o fue dado de baja no debería aparecerle dicho nombre
    3. **Regla CRÍTICA de Obsolescencia Automática (Reemplazos):** Los códigos ingresados
       en el campo de "Reemplazo" se guardan en la base de datos como una relación
       pending_obsolescence. **No les pasa nada aún**. Solo cuando este nuevo documento
       llegue al estado de "Publicado en Lista Maestra", un trigger de base de datos buscará esos
       códigos viejos y cambiará automáticamente su Vigencia y Estado a "OBSOLETO",
       documentando el cambio en su bitácora. EN LISTA MAESTRA El documento en estado
       OBSOLETO debe tener una marca de agua “DOCUMENTO OBSOLETO” y en la columna
       comentarios “REEMPLAZADO POR COD DEL NUEVO DOC”.

**US-2.06: Firma y Envío a Liberación ETO**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Como** solicitante/elaborador
- **Quiero** finalizar mi trabajo confirmando mi identidad
- **Para** que el documento inicie formalmente su viaje hacia el Gestor Documental (ETO).
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que he completado los 4 pasos y hago clic en "Firmar y enviar a Liberación →".
o Entonces se debe levantar el Modal de Doble Autenticación (auth-modal).
o Y el campo de "Usuario" debe estar autocompletado y bloqueado con mi usuario actual.
o Y debo ingresar mi contraseña obligatoriamente. Esta constraseña es la misma con la que
se ingresa al sistema.
o Cuando hago clic en "Firmar (Doble Auth)".
o Entonces el sistema valida, cierra el modal, muestra un mensaje de éxito ("Firma digital
registrada") y me redirige a "Mi Bandeja".
```
- En caso de no querer continuar con el proceso de todos los 4 pasos que se hizo, habrá un botón
    de “X”.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- Al presionar esta opción, se genera un popup de alerta que diga “Se borraran todos los datos
registrados” ¿está seguro de esta acción? Botón si/no
- En caso de seleccionar NO continuar con el proceso
- En caso de seleccionar SI cierra el modal y redirige a MI BANDEJA
- **Reglas de Negocio / Backend:**
1. **Sello de Tiempo (Timestamp):** El backend registra la fecha, hora exacta (zona horaria
Bolivia/La Paz GMT-4) y la IP de la solicitud.
2. **Creación de Bitácora:** Se crea el primer registro en el Timeline del documento: "Solicitud
- Creado" (Color Azul).
3. **Enrutamiento:** El sistema envía una alerta y pone el documento en la bandeja de
"Liberación" exclusiva del rol ETO.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

#### ÉPICA 3: WORKFLOW DE REVISIÓN Y APROBACIÓN

Esta épica detalla qué sucede exactamente cuando el Gestor Documental (ETO) libera el documento y
este cae en la "cancha" de los Revisores y posteriormente de los Aprobadores, incluyendo el manejo
estricto de las correcciones.

**US-3.01: Gestión de "Mi Bandeja" y Tipos de Tareas Activas**

- **Como** actor del flujo (Revisor, Aprobador o Solicitante)
- **Quiero** tener una bandeja de entrada centralizada
- **Para** visualizar, filtrar y acceder a todas mis tareas pendientes ordenadas por prioridad o
    antigüedad.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que ingreso a la opción "Mi Bandeja" en el menú lateral.
o Entonces visualizaré una tabla con las siguientes columnas:
▪ ID Proceso: Número único del flujo.
▪ Tipo de Tarea: Etiqueta visual (Ej: "Revisión Requerida", "Aprobación Pendiente",
"Corrección Solicitada").
▪ Codigo Doc: Codigo del Documento (Ej: PRO-CAL-045).
▪ Documento: Título del documento (Ej: Limpieza de Tanques).
▪ ELABORADOR: Quién envió la tarea (nombre del solicitante).
▪ Fecha de Asignación: Cuándo cayó en mi bandeja.
▪ SLA (DIAS EN BANDEJA) : dado que un documento puede estar con un usuario
revisor/ aprobador no más de 10 días, se semaforizan las tareas según lo
siguiente:
▪ Desde el día 0 (día de la asignación) hasta el día hábil 4 se marca en
verde
▪ Desde el día hábil 5 hasta el día hábil 7 se marca en amarillo.
▪ Desde el día hábil 8 hasta el día hábil 10 se marca en rojo.
▪ El día hábil 11 en que no se haya atendido la solicitud este documento
desaparece de la bandeja del usuario moroso y aparece en la bandeja del
USUARIO DESIGNADO iniciando el conteo de días en 0.
▪ Acción: Atender para abrir la tarea
```
- En caso de tener un listado amplio de tareas seleccionar “ver lista completa”
    Ello muestra un listado de todas las tareas pendientes en las cuales se pueden aplicar los filtros
    marcados


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Cuando hago clic en el botón "Atender Tarea".
o Entonces el sistema me redirige a la pantalla de trabajo de ese documento específico (s-
revisión).
```
- **Reglas de Negocio / Backend:**
    1. **Contador Inflexible:** Los días en bandeja se calculan desde el _Timestamp_ de creación de
       la tarea. Se deben contabilizar días hábiles L-V excluyendo feriados.

**US-3.02: Interfaz de Revisión y Visualización Office 365 Integrado**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Como** Revisor o Aprobador
- **Quiero** tener una pantalla dividida donde pueda ver los datos del formulario, la bitácora histórica
y el documento real
- **Para** poder leer el contenido sin necesidad de descargarlo a mi computadora y emitir un juicio.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que abrí una tarea desde mi bandeja.
o Entonces la pantalla mostrará 3 secciones claramente definidas:
```
1. **Cabecera de Metadatos:** Muestra el Título, Código
2. Historial del documento: que muestra todas las etapas por las que paso el
    documento resaltando hasta la actividad actual y las futuras marcadas en plomo
    como no habilitadas. En verde las etapas sin observación, en rojo las tapas
    observadas.

Observaciones de otros revisores: solo si algun revisor / aprobador emitió alguna observación se mostrará
en la casilla:

3. **Visor de Documento:** Un iframe seguro conectado a _Office 365 Web View_ que
    muestra el documento Word/Excel. _Nota de UI:_ En esta etapa de revisión, el
    documento se muestra en modo "Edición" con el control de cambios activado y el
    historial de versiones.
4. **Panel de Acciones:** Botones de " Aprobar Documento", " Devolver con
    Observaciones" y “Delegar”.
    Si el usuario marca la opción de Delegar se abrirá un modal de confirmar
    delegación.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

**US-3.03: Aprobación Positiva y Transición de Etapas (Paralelo)**

- **Como** Revisor o Aprobador
- **Quiero** dar mi visto bueno al documento mediante mi firma digital
- **Para** que el flujo avance hacia la siguiente persona o etapa.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que estoy en la pantalla de revisión y hago clic en "Aprobar Documento".
```
```
o Entonces se despliega el modal de Doble Autenticación pidiendo mi contraseña
corporativa.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Cuando ingreso mi contraseña correcta y firmo.
o Entonces la tarea desaparece de "Mi Bandeja" y veo un mensaje de éxito.
```
- **Reglas de Negocio / Backend (Routing Lógico):**
    1. **Lógica de Revisores (Trabajo en Paralelo):** Cuando el documento pasa a "Revisión", el
       sistema envía la tarea a TODOS los revisores al mismo tiempo. Si son 3 revisores, los 3
       lo tienen en su bandeja. El flujo NO avanza a la etapa de Aprobación hasta que el backend
       valide que los 3 han emitido una firma de "Aprobado".
    2. Lo mismo aplica si se rechaza/ observa el documento por alguno, ejemplo si se tienen 3
       revisores y uno observa el documento, una vez que los 3 hayan revisado, el flujo pasa al
       elaborador del documento para que realice las correcciones de todos, una vez corregido
       el documento va únicamente al revisor que haya tenido a observación.
    3. **Lógica de Aprobadores (Trabajo en Paralelo):** Una vez superada la revisión, el
       documento pasa a los Aprobadores. Se aplica la misma lógica en paralelo que la de
       revisores. Aplica lo mismo del párrafo anterior en caso de observaciones.
    4. **Registro en Bitácora:** Se inserta el nodo verde en el Timeline: "Etapa: Revisión (R1) -
       Acción: Aprobado". En caso de observación se marca el nodo rojo en el timeline y se
       muestra el (los) cajón(es) de observaciones.

**US-3.04: Rechazo / Devolución con Observaciones Obligatorias**

- **Como** Revisor o Aprobador
- **Quiero** poder rechazar el documento si encuentro errores y detallar exactamente qué está mal
- **Para** que el solicitante lo corrija.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que hago clic en " Devolver con Observaciones".
```
```
o Entonces el modal cambia y me muestra un campo textarea obligatorio llamado "Detalle
de las observaciones encontradas".
```
```
o Y si intento firmar con el campo vacío o con menos de 10 caracteres, el sistema arroja
error: "Debe proveer una justificación detallada para la devolución".
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Cuando lleno la observación y firmo digitalmente.
```
```
o Entonces la tarea sale de mi bandeja.
```
- **Reglas de Negocio / Backend:**
    1. **Impacto en el Timeline:** Se genera un nodo ROJO en la bitácora con el texto ingresado
       en la caja de observación.
    2. **Cambio de Estado en monitor Consultar Documentos:** El estado del documento pasa
       inmediatamente a "En Corrección".
    3. **Enrutamiento Inverso:** El sistema crea una nueva tarea de tipo "Corrección Solicitada" y
       la deposita en la bandeja del **Usuario Solicitante/Elaborador original**.
    4. **Corrección del usuario solicitante:** Una vez el usuario solicitante haya corregido las
       observaciones y el usuario haya dado en enviar correcciones, la tarea ya no volverá a
       pasar por ETO para liberación si no volverá únicamente al usuario revisor/aprobador que
       haya tenido la observación.

**US-3.05: Corrección en Office 365 y Bypass Directo (Retorno al Observador)**

- **Como** Usuario Solicitante
- **Quiero** recibir el documento observado, editarlo en la nube y devolverlo
- **Para** subsanar el error y que quien me observó valide mis cambios.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que ingreso a la tarea "Corrección Solicitada" en mi bandeja.
o Entonces veo en la parte superior, resaltada en ámbar, la observación exacta que me
hicieron.
o Y el visor de Office 365 ahora sí me permite EDITAR el documento en vivo (Word Online
integrado).
o Cuando termino mis cambios, debo realizar un check en el texto: "Confirmo que he
revisado y realizado todas las modificaciones solicitadas ").
```
```
o Y presiono el botón de “Confirmar y Reenviar”. Luego me saldrá el modal para firmo
digitalmente el envío.
```
- **Reglas de Negocio / Backend (La Regla del Retorno Directo):**
    1. **Bypass Estricto:** Cuando el solicitante envía la corrección, el sistema **NO DEBE**
       mandarlo de vuelta a Liberación ETO, ni a los demás revisores que ya habían aprobado.
    2. **Mapeo de Origen:** El backend debe leer en la base de datos el ID del Revisor o Aprobador
       que gatilló el estado de "Observado".
    3. **Enrutamiento Directo:** El sistema creará la tarea de validación _única y exclusivamente_
       en la bandeja de ese Revisor/Aprobador específico.
    4. **Actualización de Bitácora:** Se inserta un nodo AZUL "Acción: Corregido", mostrando el
       comentario de resolución.
    5. **La firma digital** para la caratula del documento en cuestión debe leer la primera vez que
       el usuario cargo el documento no las fechas de correcciones. Para aprobadores/ revisores
       se debe leer la fecha en la que dan su firma de aprobación final y no así a de correcciones.

**US-3.06: Ejecución de la Regla de "Timeout" (Castigo de los 10 días en el flujo)**

- **Como** Sistema / Motor de Flujo


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Quiero** quitarle la tarea a un Revisor o Aprobador que lleva 10 días sin responder
- **Para** reasignarla a su delegado y evitar el estancamiento del proceso.
- **Criterios de Aceptación (Backend/Cron Job):**

```
o Esta funcionalidad opera en background (por debajo) sin interacción directa en la UI en el
momento de la ejecución.
```
- **Reglas de Negocio / Backend:**
    1. **Monitoreo Continuo:** A las 23:59 de cada día, el sistema evalúa la tabla de tareas activas.
    2. **Condición de Disparo:** DATEDIFF(NOW(), tarea. Fecha_asignación) > 10.
    3. **Acción 1 (Búsqueda de Delegado):** El sistema consulta en la tabla de Perfiles si el
       usuario moroso tiene un "Delegado Back-up" activo (Épica 1).
    4. **Acción 2 (Ejecución):**
       ▪ _Escenario A (Tiene Delegado):_ El sistema mata la tarea del moroso y crea una
          tarea idéntica para el Delegado.
       ▪ Si el funcionario no tiene delegado, la tarea debería ir a la bandeja de su inmediato
          superior, notificando por correo electrónico la delegación automática ante el
          incumplimiento de plazos establecidos, en caso de no tener inmediato superior,
          dirigir a la bandeja de tareas de ETO para una reasignación manual.
    5. **Acción 3 (Auditoría):** Se estampa en la bitácora del documento: "Plazo de 10 días
       excedido. Reasignación automática ejecutada por el Sistema."


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

#### ÉPICA 4: CONTROL Y LIBERACIÓN ETO (GESTIÓN DOCUMENTAL)

Esta épica detalla las herramientas exclusivas del rol ETO para auditar una solicitud nueva, modificar sus
parámetros estructurales (como el árbol de Outlook) y asignarle validez oficial mediante la nomenclatura
de calidad.

**US-4.01: Gestión de las tareas de Liberación.**

- **Como** Gestor Documental (ETO)
- **Quiero** poder ver en la bandeja de Tareas pendientes una tabla con las tareas pendientes a liberar.
- **Para** priorizar mi carga de trabajo y asegurar que ningún documento inicie su revisión sin cumplir
    los estándares de formato ISO/GMP.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que inicio sesión con el rol ETO y hago clic en "Atender" a una tarea de tipo de
Liberación.
```
```
o Entonces se renderiza la pantalla s-liberacion mostrando una tabla de datos.
o Y la tabla debe contener: Id. Proceso, Tipo de tarea, Código Doc, Nombre Documento,
Remitente, Fecha de asignación, SLA, Acción (Atender).
o Cuando hago clic en el botón "Atender" en una fila específica.
o Entonces el sistema me redirige a la vista de auditoría detallada.,
```
- **Reglas de Negocio / Backend:**
    1. **Filtro Estricto:** Esta bandeja lee exclusivamente la tabla de flujos activos donde la
       columna etapa_actual sea estrictamente igual a "Liberación ETO".

**US-4.02: Análisis de Similitud por Inteligencia Artificial (Prevención de Duplicidad)**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Como** Gestor Documental (ETO)
- **Quiero** que el sistema escanee el contenido del nuevo documento contra toda la base de datos
vigente
- **Para** evitar que se creen procedimientos redundantes, duplicados o que contradigan normativas
ya publicadas.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que estoy dentro de la vista de auditoría de un documento.
o Cuando hago clic en el botón " Ejecutar Análisis de Similitud IA".
o Entonces el sistema muestra un modal de carga con el texto: "Vectorizando documento y
comparando con Lista Maestra...".
o Y tras unos segundos, me devuelve un reporte visual con un porcentaje global de riesgo.
```
```
o Si el riesgo es > 7 0%: Muestra una tabla con los documentos conflictivos (Ej:
"Coincidencia del 75% con PRO-CAL-012") y un extracto de los párrafos similares.
o Tambien se tiene la opcion de Re-ejecutar el análisis de similitud.
```
- **Reglas de Negocio / Backend (AI Flow):**
    1. **Extracción y Vectorización:** El backend extrae el texto del archivo .docx subido por el
       solicitante en el Paso 3. Utiliza un modelo de procesamiento de lenguaje natural (NLP)
       para convertir el texto en _embeddings_ (vectores numéricos).
    2. **Búsqueda Semántica:** Ejecuta una búsqueda de similitud coseno contra la base de datos
       vectorial de todos los documentos vigentes en la Lista Maestra.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
3. **Respuesta no vinculante:** La IA actúa como soporte. El sistema no bloquea el flujo
automáticamente; deja a criterio del usuario ETO decidir si devuelve el documento por
duplicidad o si ignora la advertencia justificando que es una actualización válida.
4. Este analisis de similitud unicamente debe aplicarse en el documento principal y no asi en
los formularios.

**US-4.03: Modificación del Árbol de Difusión, Revisores y Parámetros (Rol ETO)**

- **Como** Gestor Documental (ETO)
- **Quiero** tener permisos de superusuario para editar los campos que el solicitante ingresó
- **Para** corregir errores de selección de grupos de Outlook o modificar, agregar o quitar usuarios
    revisores/ aprobadores sin necesidad de devolver el documento y hacerle perder tiempo al
    solicitante.
- **Criterios de Aceptación / Explicación de Campos Editables:**

```
o Árbol de Outlook (Grupos de Difusión): La UI muestra el mismo árbol de jerarquías que
vio el solicitante. Acción ETO: ETO puede desmarcar o marcar nuevos departamentos.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Revisores y Aprobadores: ETO ve la lista cargada por el usuario. Acción ETO: Puede
hacer clic en el botón "✕" para eliminar a un revisor innecesario, o usar el buscador
predictivo para agregar a un usuario revisor o aprobador que el solicitante olvidó incluir.
o Tiempo de Vigencia: Este campo estaba readonly (4 años) para el usuario normal.
Acción ETO: Para ETO, este campo es un desplegable editable que permite cambiarlo a
1, 2, 3 o 5 años (matriz de parámetros a acordar con ETO) (Ej: Para documentos de alta
criticidad normativa que caducan al año).
```
- **Reglas de Negocio / Backend:**
    1. **Auditoría Silenciosa:** Cualquier modificación que haga ETO sobre los actores
       (Revisores/Aprobadores) o la difusión sobrescribe el JSON de la solicitud original en la
       base de datos de manera irreversible para este ciclo.
    2. **Validación Cero:** El sistema sigue exigiendo que al final de la edición de ETO exista al
       menos un Revisor y un Aprobador válido.

**US-4.04: Validación y Edición Excepcional de Codificación Oficial**

**Descripción:** Como Gestor Documental (ETO), quiero visualizar el código oficial generado
automáticamente por el sistema y tener la capacidad de editarlo solo en casos excepcionales, para
garantizar que la nomenclatura del documento sea exacta y cumpla con la normativa antes de enviarlo al
flujo de firmas.

**Criterios de Aceptación:**

1. Al ingresar a revisar los metadatos de una nueva solicitud en la Bandeja de Liberación, el campo
    "Código Oficial" debe mostrar el número correlativo real y definitivo ya asignado por el sistema (Ej:
    PRO-CAL-045).
2. **Edición Excepcional:** El campo "Código Oficial" no estará bloqueado. El ETO podrá editar
    libremente la cadena de texto en caso de que necesite forzar una nomenclatura especial (Ej.
    corregir un salto de numeración por auditoría histórica).
3. **Visibilidad de Versión:** Junto al código oficial, el sistema mostrará en modo solo lectura (readonly)
    la versión que se está tramitando que será en versión 00 si se trata de una creacion de documento
    y en version correlativa si es una actualización
4. Si la solicitud es una "Actualización", el código mostrado será exactamente el mismo del
    documento que se está actualizando (heredado).

**Nota.** - actualmente se presentan 2 tipos de codificación, POR GERENCIA Y POR ÁREA, ante la
implementación del sistema, se opta por manejar una codificación por área, por ello documentos que se
actualicen cuya codificación actual sea por gerencia, se les dará un código nuevo por área, en caso de
documentos que tengan la codificación de área, dicha codificación se mantiene y la versión se incrementa
en 1 ante la actualización. Esto se autentificará ante la creación de la solicitud con una matriz de área y
sigla, por lo tanto, si el solicitante carga un documento para determinada área, pero el código del
documento no existe como sigla, asigna código nuevo según área seleccionada, si la sigla y el área
coinciden se mantiene el código. O como alternativa se considera tener una matriz con las áreas y cuales
deben cambiar de código y cuales no, pudiendo el sistema identificarlo por “AREA RESPONSABLE”.

**Reglas de Negocio (Backend):**

1. **Autogeneración y Transacción Atómica:** La asignación del correlativo ocurre de forma
    transparente en el backend _en el instante en que el solicitante envía el trámite a la bandeja del_
    _ETO_ (US-2.06). El backend ejecuta un _Lock_ en la tabla maestra de códigos, lee el último número


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
utilizado para esa área/tipo (ej. 44), suma 1 (45), lo asigna al trámite y libera la tabla. Esto garantiza
que no existan duplicados por concurrencia.
```
2. Si una solicitud se elimina (es decir el documento ya no va) el codigo queda libre y se utiliza para
    una nueva solicitud de la misma área y tipo de documento.
3. **Control Estricto de Unicidad (Override ETO):** Si el ETO decide borrar el código autogenerado y
    escribir uno nuevo manualmente, el backend debe interceptar la petición de guardado y ejecutar
    una validación UNIQUE contra toda la base de datos (documentos en trámite, vigentes y
    obsoletos). Si el código ingresado ya existe, el backend devolverá un error HTTP 409 (Conflict) y
    la UI mostrará un toast rojo: _"El código ingresado ya pertenece a otro documento en el sistema"_.

```
Nota. - en cuanto inicie una solicitud y se asigne un codigo, este se debe reflejar en la lista maestra,
si es nuevo doc “en elaboración” si es actualización “en revisión” al reasignar manualmente un codigo,
este código tambien debe verse afectado en lista maestra y en monitor documental, al eliminarse la
solicitud se elimina de la lista maestra, pero en monitor documental (consultar documentos) se
mantiene el histórico como eliminado. Revisar US- 03
```
4. **Registro de Auditoría (Edición Manual):** Toda modificación manual del código autogenerado
    quedará registrada de forma inmutable en el log de auditoría (se guardará el código que el sistema
    calculó originalmente, el nuevo código que el ETO forzó y el timestamp exacto).
5. **Protección en Actualizaciones:** Si el trámite es una "Actualización", el backend validará que el
    código editado no rompa la trazabilidad de la familia de documentos. (Si el ETO cambia
    drásticamente el código de una actualización, el sistema arrojará una advertencia de integridad
    relacional).

**US-4.05: Devolución por Incumplimiento de Formato (Rechazo)**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Como** Gestor Documental (ETO)
- **Quiero** devolver el documento al solicitante si detecto observaciones mayores o alta duplicidad
- **Para** que no avance hacia el siguiente proceso si no cumple todos los criterios requeridos.
- **Criterios de Aceptación (Frontend/UI):**
o **Dado que** encuentro una observación mayor.
o **Cuando** en la lista desplegable de “¿Tiene observaciones al documento?” selecciono "Si".
**Entonces** se muestra un campo de texto para poner el detalle de las observaciones y el botón que aparece
es “Devolver al solicitante”.

```
o Una vez presionado el botón se abre un modal popup central de confirmación de la acción
del usuario.
```
- **Reglas de Negocio / Backend:**
    1. **Bitácora Timeline:** Se inserta el nodo ROJO "Etapa: Liberación ETO - Acción: Devuelto"
       con el texto de la observación de ETO, visible para todos.
    2. **Enrutamiento:** El estado cambia a "Corrección Solicitada" y viaja a la bandeja del usuario
       original.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

**US-4.06: Liberación Oficial y Enrutamiento Paralelo**

- **Como** Gestor Documental (ETO)
- **Quiero** dar mi confirmación de revisión
- **Para** oficializar el trámite y que el motor dispare las notificaciones simultáneas a todos los
    revisores.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que todo está correcto, el código está generado y los revisores validados.
o Cuando presiono el botón principal "Liberar Documento".
```
```
o Entonces se levanta un modal popup central solicitando la confirmación de la acción al
usuario.
```
```
o Y al confirmar, la fila desaparece de mi "Bandeja de Liberación".
o Y el sistema arroja el mensaje verde " Documento liberado exitosamente hacia
Revisión".
```
- **Reglas de Negocio / Backend (Activación del Paralelismo):**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
1. **Disparo de Bandejas (Fan-Out):** El backend cambia el estado general a Revisión
Revisores. Inmediatamente, ejecuta un bucle que crea **una tarea independiente por
cada Revisor** asignado en el Paso 4.
2. **Ejemplo Práctico:** Si hay 3 revisores (R1, R2, R3), la misma solicitud aparece al mismo
tiempo en la Bandeja de Tareas de las 3 personas, iniciando sus contadores SLA (10 días
habiles) de forma individual.
3. **Notificación Simultánea:** Se envían 3 correos de Outlook independientes a cada revisor
notificando: "Tiene un nuevo documento pendiente de revisión: [Código] - [Título]". Este
mensaje se parametriza en la plantilla US-9.04
4. **Actualización del Timeline:** Se inserta el nodo VERDE (Icono 'E') "Etapa: Liberación ETO
- Acción: Liberado".


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

#### ÉPICA 5: PUBLICACIÓN, LISTA MAESTRA Y VISOR DOCUMENTAL

**US-5.01: Publicación Automática, Cálculo de Fechas y Difusión (Outlook)**

- **Como** Motor del Sistema (Backend)
- **Quiero** procesar la última firma de aprobación de un flujo
- **Para** publicar el documento, calcular su caducidad y alertar a la compañía sin requerir clics
    adicionales.
- **Criterios de Aceptación (Backend/Automatizaciones):**

```
o Esta historia de uso opera en background inmediatamente después de la última firma de
la Épica 3.
```
- **Reglas de Negocio / Backend (Triggers):**
    1. **Cambio de Estado:** El documento pasa de "En Revisión " o “En Elaboración” a "Vigente"
       en lista maestra. Su flujo en la bitácora (consultar documentos) se marca como
       "Concluido".
    2. **Cálculo de Caducidad:** El sistema toma la fecha actual (Fecha de Aprobación) y le suma
       los años definidos en el campo "Tiempo de Vigencia" (Paso 2 / Edición ETO: 1, 2, 3 o 5
       años) para fijar la "Fecha de Expiración".
    3. **Ejecución de Obsolescencia Automática:** El sistema lee el campo "Reemplaza a"
       (Chips de códigos). Si encuentra códigos (Ej: PRO-CAL-012), busca esos registros en la
       base de datos y cambia su estado a "Obsoleto". (El impacto visual se detalla en la US-
       5.05).
    4. **Difusión por Outlook (Plantilla):** Se dispara un correo electrónico en formato HTML.
       ▪ _Destinatarios (TO):_ Todos los correos vinculados al Árbol de Difusión seleccionado
          en el Paso 2.
       ▪ _Destinatario Obligatorio (CC):_ El grupo de correo de ETO se inyecta
          obligatoriamente en copia, sin importar si el usuario lo seleccionó o no.
       ▪ _Cuerpo del Correo:_ "Se ha publicado un nuevo documento oficial: [Código] -
          [Título]. Por favor, revise el contenido en el siguiente enlace. “revisar plantillas de
          US-9.04
       ▪ _Enlace:_ Un hipervínculo seguro que redirige directo al Visor PDF del sistema
          (forzando login si la sesión caducó).
       ▪ CUANDO SEAN DOCUMENTOS CON CONTROLES DE LECTURA, se tendrá
          otra plantilla donde se tenga un enlace que redirija al control de lectura.

**US-5.02: Interfaz y Filtros de Lista Maestra (Rol Usuario Solicitante/Lector)**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Como** Usuario empleado de COFAR
- **Quiero** acceder a la Lista Maestra de documentos
- **Para** buscar, consultar y leer los procedimientos vigentes que rigen mi trabajo.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que inicio sesión como usuario estándar y voy a "Lista Maestra".
o Entonces visualizo una tabla de datos robusta.
o Y NO visualizo la tarjeta de KPI "Obsoletos" en la parte superior.
o Regla de Visibilidad Estricta: La tabla solo renderizará documentos cuyo estado sea
"Vigente" o "Vencido". Los documentos "Obsoletos" están ocultos a nivel de consulta a
base de datos para este rol.
o Los documentos en estado “En elaboración” o “en revisión” se visualizarán en la lista
maestra como filas, mas no tendrá un documento vigente aprobado que mostrar.
o Cuando utilizo los filtros por fuera desplegables o los filtros de las cabeceras (check de
Vigencia, check de Estado, Filtros de tipo, gerencia, área o inputs de texto de
Código/Título).
o Entonces la tabla se filtra en tiempo real (tecnología JS keyup ). Si una fila principal se
oculta por el filtro, su acordeón (hijos) se colapsa automáticamente.
o Estructura de Fila Principal: Muestra Gerencia, Área, Proceso, Tipo, Código, Versión,
Título, Fechas de aprobación y expiración, vigencia, estatus, codigo anterior y un botón
" Ver" - > el funcionamiento se detalla en la historia US-5.04. Tambien tiene un botón "+"
a la izquierda para desplegar el acordeón y visualizar los formularios o anexos asociados.
Botón " Ver" se refiere al documento en PDF protegido contra impresión y descarga
o Estructura del Acordeón (Desplegable): Al hacer clic en el "+":
```
```
▪ Se despliega una fila gris con un Badge azul indicando "DOCUMENTO
ORIGINAL" y el botón para visualizarlo.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
▪ Debajo, si el documento tiene anexos o formularios, se despliegan filas con un
Badge gris "FORMULARIO", mostrando el código del anexo (Ej: PRO-012/F01)
con opciones permitidas para descargar su editable.
▪ La codificación de formularios debe ser igual incremental por cada documento
principal. Si se da de baja por obsoleto algún formulario ese código deberá quedar
quemado y no volverse a reutilizar.
```
**US-5.03: Interfaz Avanzada de Lista Maestra (Rol Gestor ETO)**

- **Como** Gestor Documental (ETO)
- **Quiero** tener una vista sin restricciones de la Lista Maestra con botones de acción directa
- **Para** auditar documentos caducos, ver obsoletos y emitir copias controladas físicas.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que ingreso a la Lista Maestra con mi rol ETO.
o Entonces SÍ visualizo la tarjeta de KPI de "Obsoletos" en el panel superior.
```
```
o Y la tabla me muestra el 100% del universo documental (Vigentes, por vencer, Vencidos y
Obsoletos, en proceso).
o Y visualizo dos columnas extra que el usuario normal no tiene:
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
1. **Comentarios ETO:** Una columna que muestra textos en rojo cursiva justificando
cambios manuales de estado.
2. **Botones de Acción Expandidos:** En lugar de solo el botón " Ver", veo 4
botones en grupo: Ver (Que para ETO indica "Ver Editable en Office 365"
descargable).
▪ CV (Copia de Visualización - PDF limpio).
▪ CC (Generar Copia Controlada).
▪ CN (Generar Copia No Controlada).
o **Y** en la columna de "Estado", junto al badge verde de "Aprobado", veo un pequeño botón
gris con el ícono (Toggle Manual) - > esta función se explica en **US-5.05** en el escenario
manual.

**US-5.04: Visor PDF Interactivo y Puntero de Retorno Dinámico (SPA)**

- **Como** Lector del documento
- **Quiero** que el visor del documento tenga herramientas de lectura cómodas
- **Para** poder acercar textos pequeños o leer diagramas horizontales sin salir de la plataforma.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que hago clic en el botón "Ver documento" (ya sea en la Lista Maestra, en un Correo
(enlace del doc), o en el control de lectura, evaluaciones (si aplica)).
o Entonces se superpone la pantalla s-pdf-previsualizacion cubriendo la interfaz.
o Herramientas de Visor: En la barra superior (topbar), junto al título, debe existir una
botonera con:
▪ Botón + (Zoom In): Amplía la escala del PDF en un 20% por clic.
▪ Botón - (Zoom Out): Reduce la escala del PDF en un 20% por clic.
▪ Botón ↻ Rotar: Gira el lienzo del PDF 90 grados por cada clic (para leer diagramas
de flujo apaisados).
o Regla de Seguridad: Para los "Documentos Originales", está prohibido descargar o
imprimir (botón bloqueado o inexistente) si se entra con perfil de Solicitante, permitido para
perfil ETO
o Memoria de Navegación (Puntero de Retorno): Al hacer clic en el botón "← Volver", el
sistema no me manda al inicio. El código JS debe recordar la pantalla exacta desde la que
abrí el visor (Ej: s-monitor-cc o s-lista) y devolverme a ella preservando mis filtros
aplicados.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

**US-5.05: Gestión de Obsolescencia (Automática vs. Manual)**

- **Como** Gestor Documental (ETO)
- **Quiero** que la obsolescencia opere automáticamente (cuando se establece reemplazo de
    documentos en la solicitud), pero retener el poder de dar de baja un documento manualmente si
    existe una contingencia
- **Para** mantener el control total del repositorio.
- **Criterios de Aceptación / Backend:**

```
o Escenario Automático (Heredado de US-5.01): Cuando el sistema marca un documento
como obsoleto por un reemplazo, en la columna "Comentarios ETO" el sistema inyecta
automáticamente: "Reemplazado por CODIGO NUEVO” Este campo se podrá editar por
el gestor ETO. Para el usuario normal, este documento desaparece inmediatamente de su
pantalla.
o Escenario Manual (Uso del botón ):
▪ Dado que estoy en la Lista Maestra como ETO.
▪ Cuando hago clic en el botón de un documento "Vigente".
```
```
▪ Entonces el Badge de Vigencia cambia instantáneamente a "Obsoleto"
(Naranja/Ámbar).
▪ Y el Badge de Estado cambia a "Obsoleto" (Rojo).
▪ Y en la columna de Comentarios se estampa automáticamente: "Modificado
manualmente por ETO el [Fecha y Hora Actual, Usuario]" en texto rojo.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

Al volver un documento obsoleto, la copia de visualización CV debe marcarse con marca de agua como
“DOCUMENTO OBSOLETO” y se dejan de visualizar los botones de CC, CN y al reestablecer el estado,
vuelven a aparecer.

Al hacer clic en el se genera un popup al centro de la pantalla para que el usuario ETO confirme la
acción.

```
▪ Y si vuelvo a hacer clic en el , la acción se revierte, restaurando el documento
a "Vigente" y borrando el comentario.
```
**Nota. -** Esta acción no será posible si existe una version posterior (actual) del documento, y el sistema
también solicitará la confirmación de la acción.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

**US-5.06: Control de Vencimientos y Bloqueo de Riesgo (Alerta Roja)**

- **Como** Gestor de Calidad (ETO) y usuario solicitante
- **Quiero** que el sistema advierta visualmente e interrumpa a cualquier usuario que intente leer un
    documento cuya fecha de expiración ya pasó
- **Para** mitigar el riesgo de que el personal de planta opere con procedimientos desactualizados.
- **Criterios de Aceptación (Frontend/Backend):**

```
o Job de Base de Datos: Un Cron Job nocturno verifica IF(fecha_expiracion < HOY). Si es
verdadero, cambia la vigencia a "Vencido".
o Visualización en Tabla: En la Lista Maestra (para todos los roles), la columna Vigencia
mostrará un Badge rojo sangre indicando "Vencido".
o Barrera de Interrupción (Modal Vencido):
▪ Dado que un usuario hace clic en " Ver" sobre un documento Vencido.
▪ Entonces el Visor PDF NO se abre directamente.
▪ En su lugar , se despliega el modal modal-alerta-vencido con un ícono de alerta
.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
▪ Y el texto debe indicar: "Advertencia: Usted está a punto de visualizar un
documento que se encuentra VENCIDO. ¿Está seguro que desea continuar con
la visualización?"
▪ Cuando el usuario hace clic en el botón "Si, continuar".
▪ Entonces recién se lanza el Visor PDF (con sus respectivas herramientas de
zoom/rotación) el cual inyectará dinámicamente una marca de agua diagonal y
semitransparente (color rojo) que cruce toda la página con la marca de agua
"VENCIDO”.
```
**US-5.0 7 : Inyección Dinámica de Carátula y Carimbos (Encabezados)**

- **Como** Motor Backend
- **Quiero** que el sistema estampe automáticamente la meta data oficial en el archivo original
    aprobado por todas las partes.
- **Para** cumplir con la normativa BPM que exige que cada página esté foliada, carimbada,
    identificada y aprobada formalmente.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que un documento acaba de ser publicado (Vigente).
o Cuando cualquier usuario hace clic en " Ver doc" desde la Lista Maestra
```
```
o Entonces el visor PDF debe renderizar una Página 0 (Carátula) generada por el
sistema que contenga: Logo de COFAR, Título, Código, Versión y la Tabla de
Firmas (Creado por, Revisado por, Aprobado por, con sus fechas respectivas).
o Y a partir de la página 1 en adelante, el documento debe mostrar un "Carimbo"
(Encabezado de tabla) incrustado en la parte superior con: Nombre del
Documento, Código, Versión y la paginación Página X de Y.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Reglas de Negocio / Backend:**

```
o Renderizado Post-Aprobación: Al momento de la publicación oficial, una librería
de manipulación de documentos en el servidor (Ej: OpenXML o PDFBox) tomará
el archivo limpio.
o Generación de Carátula: El sistema insertará una primera página (Carátula) que
contenga el Logo corporativo, el Título, el Código, la Versión, el Cuadro de Firmas
(Nombres de quienes lo elaboraron, revisaron y aprobaron con sus fechas)
extraídos del Timeline.
o Inyección de Carimbo (Header): En todas las páginas, el sistema inyectará un
encabezado estándar en bloque que contenga: ÁREA, Nombre del Documento ,
Código TITULO, Versión y la paginación dinámica Página X de Y , FECHA EN
Que entra en vigencia, según modelo adjunto.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

#### ÉPICA 6: CAPACITACIÓN, EVALUACIÓN Y CERTIFICACIÓN AUTOMÁTICA

Esta épica gobierna cómo la empresa se asegura de que sus empleados lean y entiendan los nuevos
documentos. Abarca desde la configuración paramétrica por parte de ETO (apoyada por IA), la experiencia
de usuario al rendir la prueba, hasta la emisión automática del diploma oficial.

**US-6.01: Monitor de Evaluaciones y Habilitación Paramétrica (Rol ETO)**

- **Como** Gestor de Calidad (ETO)
- **Quiero** tener un panel de control global de las difusiones documentales
- **Para** configurar los exámenes o controles de lectura en el momento adecuado y hacer seguimiento
    al cumplimiento del personal.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que ingreso al "Monitor de Eval. / Controles" desde el Sidebar.
o Entonces visualizo una tabla con todos los documentos publicados recientemente que
requerían difusión (según lo definido en el Paso 2 de la solicitud). Filtros para buscar por
persona y entre un rango de fechas y/o filtros de cabecera. Y tambien un botón para
generar un reporte de la vista en Excel.
o Y la tabla muestra: Código, Nombre de documento, Fecha de Lanzamiento, Plazo,
Alcance, promedio, Tipo (Evaluación / Lectura), Estado de Configuración (Pendiente /
Finalizado / Cancelado) y un botón " Configurar Parámetros".
o Cuando el tipo es "Evaluación", el botón de configuración está siempre habilitado.
o Cuando el tipo es "Control de Lectura", el botón de configuración se habilitará a los 30
días posteriores a la difusión del documento a fin de volver a lanzar el control de lectura
cuando se requiera a grupos o usuarios específicos.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Reglas de Negocio / Backend (Restricciones de Tiempo):**
1. **Bloqueo de 1 Mes (Control de Lectura):** Si el documento es solo para Control de Lectura,
el botón " Configurar Parámetros" permanecerá bloqueado (gris) disabled hasta que
hayan transcurrido exactamente **30 días calendario** desde la fecha de publicación del
documento. Si ETO intenta forzarlo, el backend rechazará la petición indicando: "El control
de lectura solo puede parametrizarse un mes después de la publicación oficial".
2. **Exención Absoluta de ETO:** Al momento de generar la lista de destinatarios que deberán
rendir la evaluación o lectura, el backend excluirá automáticamente a cualquier usuario
que pertenezca al área de ETO o tenga el rol ETO. ETO audita, no se autoevalúa en este
flujo. Tambien se excluye a los usuarios que hayan participado en la elaboración, revisión,
aprobación del documento aunq se encuentren dentro de los grupos de difusión.

**US-6.02: Configuración del Examen y Asistente IA (Rol ETO)**

- **Como** Gestor DOCUMENTAL (ETO)
- **Quiero** definir las reglas del examen y utilizar Inteligencia Artificial para redactar las preguntas
- **Para** agilizar la creación de pruebas de comprensión sin tener que leer y extraer manualmente
    todo el documento.
- **Criterios de Aceptación / Explicación de Campos:**

```
o Dado que hago clic en " Configurar Parámetros" de un documento tipo Evaluación.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Entonces se abre la pantalla de Configuración s-config-examen.
o Tiempo Límite (Input Numérico - Obligatorio): Minutos que tendrá el usuario para
resolverlo.
o Intentos Permitidos (Input Numérico - Obligatorio): Rango de 1 a 5 intentos.
o Nota Mínima de Aprobación (Input Numérico - Obligatorio): a configurar por ETO.
o Checkbox "Habilitar Certificado" (Toggle): Si se activa, habilitará la emisión del PDF
(Ver US-6.06).
o Botón " Sugerir Preguntas con IA":
▪ Cuando ETO hace clic aquí.
▪ Entonces el sistema lee el archivo PDF oficial, lo procesa mediante NLP
(Procesamiento de Lenguaje Natural) y autocompleta la sección inferior con 10
preguntas de opción múltiple (indicando la opción correcta entre 4 opciones),
basadas estrictamente en el contenido del documento.
o Gestor de Preguntas (Manual): ETO puede editar el texto de las preguntas generadas
por la IA, borrar filas, o agregar nuevas manualmente marcando cuál es el radio button
correcto.
o Exportar: Se puede exportar en formato Excel las preguntas que se hayan realizado en
el sistema más sus respuestas correctas.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Reglas de Negocio / Backend:**
1. **Distribución Automática:** Al presionar "Guardar y Publicar Evaluación", el backend
inyecta una nueva tarea en la bandeja de todos los usuarios del árbol de difusión
(excluyendo ETO). Notifica la necesidad de realizar evaluación a través de correo
electrónico.
2. **Ponderación Automática:** El sistema divide los 100 puntos equitativamente entre la
cantidad de preguntas configuradas (Ej: 4 preguntas = 25 pts cada una).

**US-6.03: Recepción y Ejecución de "Control de Lectura" (Rol Usuario)**

- **Como** empleado de COFAR
- **Quiero** poder notificar al sistema que he leído y comprendido un nuevo procedimiento
- **Para** cumplir con mi responsabilidad normativa sin tener que rendir un examen formal.
- **Criterios de Aceptación (Frontend/UI):**
    o **Dado que** ingreso a "Mi Bandeja" y tengo una tarea de tipo " Control de Lectura
       Pendiente". O esta ha sido notificada por correo cuando se apruba el documento.
    o **Cuando** hago clic en "Leer y confirmar", se abre el Visor PDF del documento.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

En plazo maximo dado que los controles de lectura estarán abiertos por un mes desde la difusión del
documento, el plazo máximo es de 30 dias, estos plazos se deben semaforizar en mi bandeja, en rojo
cuando falten 10 dias para cumplir el plazo maximo, en amarillo cuando falten 20 dias y en verde de 30 a
20 dias.
o **Entonces** en la parte inferior del visor, bloqueando la lectura, habrá un recuadro de acuse
de recibo.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Regla Antifraude: El checkbox "He leído y comprendido este documento" estará disabled
hasta que el usuario haga scroll hasta la última página del PDF.
```
```
o Cuando marco el checkbox y presiono "Firmar Lectura".
o Entonces se despliega el modal de Doble Autenticación requiriendo mi contraseña.
```
- **Reglas de Negocio / Backend:**
    1. Al firmar, el estado de esta tarea en la BD pasa a **"LEÍDO"**.
    2. Se sella con el Timestamp exacto de la firma.

**US-6.04: Recepción y Ejecución de "Evaluación Temporizada" (Rol Usuario)**

La tarea se debe semaforizar según plazo para dar la evaluación, rojo hasta dos dias antes del vencimiento.

- **Como** empleado de COFAR
- **Quiero** rendir el examen asignado dentro de la plataforma y poder repasar el documento antes de
    iniciar
- **Para** demostrar mi competencia sobre el nuevo documento con la preparación adecuada.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que abro una tarea de tipo " Evaluación Pendiente" desde mi Bandeja y presiono
el botón “Iniciar examen”.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Entonces veo una pantalla previa de advertencia: "Este examen tiene un tiempo de [X]
minutos, requiere [Y] puntos para aprobar y se tiene una cantidad de [Z] intentos. Una vez
iniciado no se puede pausar."
```
```
o Y encima de la advertencia visualizo un botón azul secundario: " Ver Documento
o Cuando hago clic en " Abrir Documento ".
o Entonces aparece un mensaje flotante (toast): "Abriendo el documento desde la Lista
Maestra..." y se despliega el Visor PDF en modo lectura sin que inicie el cronómetro.
```
```
o Cuando cierro el visor y hago clic en el botón principal "Empezar examen ahora".
o Entonces arranca un cronómetro regresivo rojo en la parte superior y se renderizan las
preguntas.
```
```
o Cuando el cronómetro llega a 00:00, el sistema fuerza el envío ( submit ) automático con
las opciones marcadas.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Reglas de Negocio / Backend:**
1. **Anti-Trampas:** Si el usuario cierra el navegador en pleno examen (con el cronómetro ya
iniciado), el sistema cuenta ese intento como gastado con Nota: 0.
2. **Calificación en Tiempo Real:** El backend compara las respuestas enviadas con el JSON
de respuestas correctas y devuelve la calificación exacta instantáneamente.

**US-6.05: Lógica de Resultados, "Nota más Alta" y Vencimientos (Backend)**

- **Como** Sistema Evaluador
- **Quiero** procesar la nota obtenida, manejar los reintentos inteligentemente y auditar a los que no
    cumplan los plazos
- **Para** reflejar la realidad del desempeño del personal.
- **Criterios de Aceptación (Reglas de Backend):**
    1. **Visualización de Resultado:** Inmediatamente tras el envío, se muestra el modal result-
       modal. Si aprueba, es verde; si reprueba, es rojo.
    2. **Manejo de Intentos:** Si el usuario reprueba y aún tiene intentos disponibles (Ej: Gastó 1
       de 3), se muestra el botón " Volver a intentar". Si gasta todos sus intentos y reprueba,
       el estado final del flujo para él es **"REPROBADO"**.
    3. **Regla de la "Nota Más Alta":** Si el usuario aprueba en su primer intento con la nota
       mínima de aprobación establecido, puede decidir usar su segundo intento para mejorar.
       Si en el segundo intento saca 60/100, el sistema **no** lo aplaza. La lógica de base de datos
       siempre ejecutará MAX(nota_obtenida) agrupado por el ID del examen y el ID del usuario,
       asegurando que su expediente histórico conserve la nota más alta alcanzada en sus
       intentos.
    4. **Vencimiento de Tareas (Castigo de Tiempo):** A las 23:59 del día fijado como "Fecha
       Límite de Ejecución" (Configurado por ETO en la US-6.02), un Job de BD escanea las
       tareas pendientes. Cualquier usuario que no haya iniciado su evaluación o control de
       lectura pasará automáticamente al estado definitivo de **"NO EJECUTADO"** (Rojo). La


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
tarea desaparece de su bandeja y queda marcada permanentemente como una falta de
cumplimiento en su expediente “mis evaluaciones”.
```
**US-6.06: Emisión Automática del Certificado Oficial y Expediente Académico**

- **Como** empleado que ha aprobado un examen oficial
- **Quiero** que el sistema me genere un certificado imprimible y guarde mi historial
- **Para** tener un respaldo curricular de mis capacitaciones internas.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que finalizo el examen con nota APROBATORIA.
o Y (Condición Backend) ETO marcó el checkbox "Habilitar Certificado" al configurar la
prueba.
o Entonces dentro del modal de resultados exitosos aparece el botón verde " Ver
Certificado".
```
```
o O Cuando el usuario entra a "Mis Evaluaciones" > "Mis Certificados Obtenidos" desde el
Sidebar.
```
```
o Entonces visualiza una tabla histórica con todos sus exámenes aprobados (que tenían
certificación).
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Cuando hace clic en "Ver Certificado" en cualquier registro.
o Entonces el sistema renderiza el PDF s-pdf-certificado en formato horizontal (carta).
```
#### NOTA. - FORMATO A DEFINIR

- **Reglas de Negocio / Backend (Estructura del Certificado):**
    1. **Generación Dinámica:** El PDF no es un archivo estático. El backend inyecta variables
       sobre la plantilla en tiempo real.
    2. **Variables Inyectadas:**
       ▪ Logo corporativo de COFAR y Marco Oficial.
       ▪ $Nombre_Usuario: Nombre y Apellido extraídos de la sesión.
       ▪ $Titulo_Documento: Nombre oficial del documento (Ej: Política de Asistencia).
       ▪ $Nota_Obtenida: Inyecta el valor de la regla "Nota Más Alta" (Ej: 100/100).
       ▪ $ID_Verificacion: Código alfanumérico autogenerado (Ej: CF- 8492 - 2026) único
          por certificado, guardado en la BD para auditorías.
       ▪ $Fecha_Emision: Sello de tiempo de cuando el usuario obtuvo la nota aprobatoria
          definitiva.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

#### ÉPICA 7: TRAZABILIDAD DE COPIAS FÍSICAS (CONTROLADAS Y NO CONTROLADAS)

Esta épica documenta el ciclo de vida de un documento impreso: su generación desde la Lista Maestra, la
incrustación de sellos de seguridad dinámicos en el PDF, el acuse de recibo del usuario y, en el caso de
las copias controladas, la devolución y destrucción auditada.

**US-7.01: Módulo de Configuración y Generación de Copias Físicas (Rol ETO)**

- **Como** Gestor Documental (ETO)
- **Quiero** poder emitir copias físicas de un documento vigente desde la Lista Maestra
- **Para** entregar procedimientos impresos a áreas de planta (donde no hay computadoras)
    manteniendo el registro exacto de quién los posee.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que ingreso a la Lista Maestra con rol ETO.
```
```
o Cuando hago clic en el botón CC (Copia Controlada) o CN (Copia No Controlada) en la
fila de un documento vigente.
```
```
o Entonces se despliega la pantalla "Generación de Copias".
o Campos del Formulario:
▪ Código y Título del Documento: (Read-only) Se muestran en la cabecera como
referencia cruzada.
▪ Badge de Tipo: Se muestra un distintivo visual verde si es CONTROLADA o
ámbar si es NO CONTROLADA.
▪ Cantidad de copias a generar (Input Numérico - Obligatorio): Por defecto es
```
1. Permite un rango del 1 a rango indicado
▪ **Destinatarios (Inputs de Texto Dinámicos - Obligatorios):**
▪ _Lógica de UI:_ Si ETO cambia la cantidad a "3", el sistema renderiza
automáticamente 3 campos de texto vacíos debajo, rotulados como
"Nombre de destinatario 1...", "Nombre de destinatario 2...", etc. Este texto
de búsqueda de usuario debe ser autocompletado, sugerencia de
nombres.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Cuando intento hacer clic en "Generar Copias" dejando algún destinatario vacío.
o Entonces el sistema me bloquea y muestra un toast de error: " Debe indicar el nombre
de todos los destinatarios."
o Las copias deben poder emitirse en distintas cantidades y en distintas fechas según
necesidad pero manteniendo el correlativo de copias generadas al momento.
```
- **Reglas de Negocio / Backend:**
    1. **Asignación de ID Autoincremental:** Por cada destinatario ingresado, el backend crea un
       registro en la tabla de trazabilidad física. El sistema cuenta cuántas copias de _ese_
       _documento específico_ ya existen, y asigna el siguiente número. (Ej: Si el documento ya
       tenía 5 copias históricas, los 3 nuevos destinatarios recibirán los IDs de Copia 6, 7 y 8).
    2. **Transición Visual:** Tras procesar en la BD, la pantalla oculta los campos de configuración
       y muestra una tabla de "Copias Generadas Exitosamente" con botones individuales de
       previsualización por cada usuario.

**US-7.02: Motor de Previsualización y Sellado PDF Dinámico (Rol ETO)**

- **Como** Gestor Documental (ETO)
- **Quiero** que el sistema inyecte marcas de agua y pies de página legales en el PDF antes de
    imprimirlo
- **Para** que el papel físico sea inconfundible, rastreable y no pueda ser fotocopiado sin evidenciar su
    origen.
- **Criterios de Aceptación (Frontend/UI):**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Dado que generé las copias en la US-7.01 y hago clic en " Previsualizar Copia N".
```
```
o Entonces se abre el Visor PDF Oficial.
o Marca de Agua (UI): Se inyecta un texto diagonal grande y semitransparente cruzando
toda la hoja que dice "COPIA CONTROLADA" o "COPIA NO CONTROLADA" en color
rojo, dependiendo de la opción elegida inicialmente.
o Footer Legal (Inyección de Variables): En la base de todas las páginas del PDF, el
sistema inyecta una cadena de texto en tipografía monoespaciada (monospace).
```
- **Reglas de Negocio / Backend (Estructura del Footer):**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
1. **Construcción del String:** El backend une las variables generadas para formar el pie de
página exacto: Copia [Tipo]. ID copia [Tipo]: [N° Copia]. Fecha de emisión: [Fecha y Hora].
(Destino: [Destinatario]).
2. **Zona Horaria Estricta:** La variable de fecha y hora no toma la del navegador local del
usuario, sino que fuerza la zona horaria del servidor sincronizada con Bolivia
(America/La_Paz), inyectándola en formato DD/MM/YYYY HH:MM:SS.
3. **Impresión:** Al hacer clic en " Imprimir Copia", el navegador abre el diálogo nativo de
impresión bloqueando la edición del footer. Tambien debe permitir la descarga de CC Y
CN.

**US-7.03: Recepción y Firma Digital del Papel Físico Copia Controlada (Rol Usuario Receptor)**

- **Como** empleado de COFAR
- **Quiero** confirmar mediante el sistema que (ETO) me entregó el papel físico de Copia Controlada
    en las manos
- **Para** que quede constancia legal de que soy responsable del resguardo de ese documento.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que ETO generó una copia Copia Controlada a mi nombre, ingreso a "Mi Bandeja".
o Entonces observo una tabla inferior dedicada llamada "Recepción de Copias Físicas".
```
```
o Estructura de la Tabla: Muestra Badge del Tipo de Copia (Controlada), Código, Versión,
Nombre del Documento, N° de Copia ID (Ej: 3) y un botón azul " Recibido".
o Cuando hago clic en " Recibido".
o Entonces se despliega el modal de Doble Autenticación (modal-auth-recepcion) con el
ícono. El campo usuario viene autocompletado y bloqueado.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Cuando ingreso mi contraseña corporativa y firmo digitalmente.
o Entonces ocurre una animación fluida: la fila correspondiente se vuelve transparente, se
desliza hacia la derecha y desaparece de la tabla de tareas.
o Y emerge un popup inferior derecho (toast): " Recepción confirmada. Firma digital
registrada exitosamente."
```
- **Reglas de Negocio / Backend:**
    1. **Cambio de Estado:** En la base de datos (MONITOR DE COPIAS CONTROLADAS), el
       registro de esta copia física pasa del estado "Generado" al estado **"Entregado"**.
    2. **Mensaje de Bandeja Vacía:** Si el usuario firma su última copia pendiente y la tabla se
       vacía, el sistema inyecta dinámicamente una fila que dice: "No tiene copias físicas
       pendientes por recibir."

**US-7.04: Monitor de Copias No Controladas (Rol ETO – Tracking Unidireccional)**

- **Como** Gestor Documental (ETO)
- **Quiero** tener un registro histórico filtrable de todos los papeles "No Controlados" que he emitido
- **Para** auditorías internas, sabiendo que estos papeles son de uso informativo y no exigen
    devolución.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que ingreso a "Monitor Copias No Controladas" desde el menú lateral.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Entonces visualizo una tabla histórica.
```
```
o Filtros Avanzados: La parte superior cuenta con un motor de filtros en tiempo real
(tecnología keyup JS) que permite buscar cruces por: ID, Código, Versión, Documento,
Destinatario y un rango de Fechas (Desde / Hasta).
o Estados Visuales: La columna Estado mostrará un Badge ámbar ("Generado").
o Botón de Visualización: El botón " Mostrar" permite abrir el visor PDF para ver
exactamente qué copia se le dio a esa persona (útil para reimpresiones por pérdida).
o Boton de exportar: Se podrá exportar este monitor a un archivo en Excel.
```
- **Reglas de Negocio / Backend:**
    1. **Naturaleza del Flujo:** Al ser copias "No Controladas", el flujo termina cuando se ha
       generado la CN. No existe columna ni opción de devolución.

**US-7.05: Monitor de Copias Controladas (Rol ETO - Ciclo de Vida Cerrado)**

- **Como** Gestor Documental (ETO)
- **Quiero** tener un panel de control con seguimiento riguroso de las Copias Controladas
- **Para** exigir la devolución del papel físico cuando el documento original quede obsoleto y proceder
    a su destrucción.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que ingreso a "Monitor Copias Controladas".
```
```
o Entonces visualizo una tabla similar al Monitor CN, pero con dos columnas críticas
adicionales: Fecha Devolución y Devolución (Acción).
```
```
o Filtros Avanzados: La parte superior cuenta con un motor de filtros en tiempo real
(tecnología keyup JS) que permite buscar cruces por: ID, Código, Versión, Documento,
Destinatario y un rango de Fechas (Desde / Hasta).
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Estados Visuales: La columna Estado mostrará un Badge ámbar ("Generado") y color
“azul” /entregado) si se ha cumplido US- 7 - 03.
o Botón de Visualización: El botón " Mostrar" permite abrir el visor PDF para ver
exactamente qué copia se le dio a esa persona (útil para reimpresiones por pérdida).
o Boton de exportar: Se podrá exportar este monitor a un archivo en Excel.
o Comportamiento de la Columna Devolución:
▪ Si el estado es "Generado", la columna muestra un guion (No se puede devolver
algo que no se ha recibido).
▪ Si el estado es "Entregado", la columna muestra un <input type="checkbox">
habilitado.
▪ Si el estado es "Devuelto", la columna muestra un ícono " " fijo, sin checkbox.
```
- **Reglas de Negocio / Backend:**
    1. **Filtro de Fechas Múltiple:** El motor de búsqueda en JS formatea las fechas de la tabla
       (que están en DD/MM/YY HH:MM) transformándolas en objetos Date válidos, permitiendo
       a ETO filtrar exactamente quién recibió papeles entre fechas específicas.

**US-7.06: Firma Digital de Destrucción / Devolución de CC (Rol ETO)**

- **Como** Gestor Documental (ETO)
- **Quiero** que el sistema exija mi firma digital cuando marco que un papel me fue devuelto
- **Para** sellar el ciclo de vida del papel, asumiendo la responsabilidad legal de su destrucción.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que estoy en el Monitor de Copias Controladas (US-7.05).
o Cuando marco el checkbox de Devolución en la fila de un usuario que me entregó su
papel.
```
```
o Entonces el sistema despliega el modal de Doble Autenticación (modal-auth-dev) con el
ícono y el texto: "Ingrese sus credenciales corporativas para firmar digitalmente la
recepción de esta copia física".
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Si hago clic en Cancelar: El modal se cierra y el checkbox de la tabla se desmarca
automáticamente para evitar falsos positivos.
o Cuando ingreso mi contraseña correctamente y hago clic en "Confirmar y Firmar".
o Entonces:
```
1. El modal se cierra.
2. La columna "Fecha Devolución" se autocompleta inmediatamente con la fecha y
    hora de la firma.
3. El Badge de estado pasa a "Devuelto" (Color gris pastel).
4. El checkbox desaparece y es reemplazado por el ícono fijo " ".
- **Reglas de Negocio / Backend:**
1. **Sello de Auditoría:** El backend bloquea este registro de por vida. El estado "Devuelto" es
inmutable. Registra el IP, el usuario ETO que destruyó el papel y el _Timestamp_ exacto.

**US-7.0 7 : Catálogo y Descarga de Plantillas Documentales Oficiales**

- **Como** actor del sistema (Solicitante o ETO)
- **Quiero** acceder a un repositorio centralizado de plantillas oficiales en formatos editables (Word,
    Excel, etc.)
- **Para** asegurar que los nuevos documentos cumplan con el formato, carátulas y estructura
    normativa de COFAR desde su creación, evitando el uso de archivos obsoletos.
- **Criterios de Aceptación (Frontend/UI):**
    o **Acceso y Visualización:**
       o **Dado que** ingreso a la opción "Plantillas Documentales" desde el menú lateral
          (Sidebar).


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Entonces visualizo una pantalla con el título "Plantillas Documentales" y una breve
descripción instructiva.
```
```
o Y se presenta una cuadrícula ( grid ) de tarjetas ( cards ) estilizadas que representan
cada tipo de plantilla disponible.
o Estructura de las Tarjetas (Cards):
o Cada tarjeta debe contener un icono grande en la parte superior (ej. un icono de
archivo Word o Excel).
o Debe mostrar el nombre descriptivo de la plantilla (ej. "Plantilla de Procedimientos",
"Plantilla de Manuales", "Plantilla de Instructivos de Planta").
o Debe incluir un botón principal centrado con el texto: Descargar editable.
o Acción de Descarga:
o Cuando hago clic en el botón de descarga de una tarjeta.
o Entonces el sistema debe disparar la descarga directa del archivo editable (.docx o
.xlsx) al almacenamiento local del usuario.
o Y se debe mostrar un mensaje flotante ( toast ) de confirmación: "Iniciando descarga
de: [Nombre de la Plantilla]...".
o No existe una limitante para las descargas de plantillas
o Estética y Diseño:
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Las tarjetas deben seguir la línea visual de COFAR (bordes redondeados, sombras
suaves al pasar el mouse, colores corporativos).
o El diseño debe ser responsivo, ajustando la cantidad de tarjetas por fila según el ancho
de la pantalla.
```
**Reglas de Negocio / Backend:**

1. **Gestión de Archivos en Servidor:** Las plantillas se almacenarán en un directorio específico del
    servidor. El backend servirá estos archivos garantizando que siempre se entregue el archivo
    físicamente cargado como "Vigente".
2. **Integridad Documental:** Solo se permiten archivos en formatos editables que hayan sido
    aprobados previamente por el área de ETO
3. **Trazabilidad de Uso:** Cada acción de descarga debe generar un registro silencioso en la base de
    datos de auditoría (log_descargas_plantillas) guardando: _ID_Usuario, ID_Plantilla, Fecha y Hora_.
4. **Disponibilidad por Rol:** Aunque la visualización es general, el backend puede restringir la
    visibilidad de ciertas plantillas sensibles (ej. Plantillas de Contratos Legales) basándose en el
    departamento del usuario si así se parametrizara en la Épica 9.
5. Las plantillas vigentes serán actualizadas por ETO en PARAMETRIZACION GENERAL,
    actualizando automáticamente las vistas de los usuarios.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

#### ÉPICA 8: MONITOREO, CONSULTAS Y ASISTENTE IA (BUSINESS INTELLIGENCE)

Esta épica documenta las herramientas de auditoría y análisis de datos. Define cómo cualquier usuario
puede rastrear el historial de un trámite y cómo el rol ETO utiliza tableros de control (dashboards) e
Inteligencia Artificial conversacional para gestionar cuellos de botella y vencimientos normativos.

**US-8.01: Buscador Global, Filtros Avanzados y Despliegue de Bitácora Histórica (Timeline)**

- **Como** actor del sistema (Solicitante, Revisor o ETO)
- **Quiero** poder consultar el estado exacto de cualquier documento en proceso o finalizado y filtrar
    dinámicamente cada atributo del listado.
- **Para** saber en qué etapa se encuentra, quién lo tiene o por qué fue rechazado, leyendo su historial
    completo de forma cronológica y detallada.
- **Criterios de Aceptación (Frontend/UI):**
1. **Acceso y Visualización:** * Dado que ingreso a la pantalla "Consultar Documentos" (s-consulta-
user).

```
o Entonces visualizo una tabla principal dentro de una tarjeta de sección (section-card) con
desplazamiento horizontal habilitado.
```
2. **Panel de Filtros Avanzados por Columna:**

```
o Se deben visualizar exactamente las siguientes 9 columnas con sus respectivos filtros:
```
1. **Nro. Proceso:** Filtro de búsqueda de texto.
2. **Usuario Creador:** Filtro de búsqueda de texto.
3. **Área:** Filtro de búsqueda de texto.
4. **Código:** Filtro de búsqueda de texto.
5. Versión: filtro de búsqueda de texto.
6. **Fecha Solicitud:** Visualización de fecha.
7. **Fecha Liberación:** Visualización de fecha.
8. **Fecha Revisión:** Fecha en la que se concluyó la revisión.
**9. Fecha Aprobación:** Fecha en la que se concluyó la aprobación
10. **Etapa Actual:** Visualización de la fase del flujo.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
11. **Responsable:** Visualización del nombre o nombres de usuario que poseen la
tarea. Si es mas de uno, debe ser mostrado separado por una coma.
12. **Estado:** Filtro de tipo **Dropdown Fijo** (filter-fixed) con checkboxes para selección
múltiple de: _Concluido (cuando ha finalizado todas las etapas del proceso, En
ejecución (cuando se encuentra en alguna etapa del proceso) y Eliminado (cuando
manualmente se ha cancelado el proceso y ya no corre mas)_.
13. **Ver doc:** Se puede abrir el documento en office 365 pero solo con permisos de
lectura.
o **Evento de Filtrado:** Cuando ingreso un término en cualquier filtro de texto, la tabla debe
actualizarse en tiempo real mediante el evento keyup.
3. **Estructura de la Fila y Acciones Locales:**

```
o Botón de Expansión: A la izquierda de cada fila se encuentra un botón colapsable + para
abrir el historial.
```
```
o Visor de Documentos: Un botón con el icono Ver doc que abre el archivo PDF en
modo "Solo Lectura". Unicamente se podran visualizar documentos cuyo estaod sea
“concluido” leer el mismo doc PDF que en LISTA MAESTRA, documentos en versiones
anteriores (OBSOLETOS) se viaulizarán con marca de agua “OBSOLETO” al igual q en
lista maestra.
```
```
o Control ETO (Botón Eliminar): Si el usuario tiene rol ETO, visualiza un botón rojo ✕ al
lado del badge de Estado (solo si el proceso no está ya en estado "Eliminado o
Concluido"). es decir, solo se pueden eliminar/ cancelar proceso “En Ejecución”.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Al hacer clic, se despliega un modal de confirmación con doble autenticación.
```
4. **Despliegue del Timeline (Sub-fila):**

```
o Al hacer clic en el botón +, se despliega una sub-fila de fondo gris que contiene el Historial
del Proceso.
```
```
o Diseño Visual: Una línea vertical conectora de color gris claro vincula diferentes "Nodos"
o burbujas circulares.
o Contenido del Nodo: Cada burbuja representa un hito y debe mostrar: Etapa, Acción
Ejecutada, Fecha, Hora y Usuario responsable.
o Control ETO (Botón Reasignar): Si el usuario es ETO, visualiza un botón azul de
Reasignar únicamente en los nodos cuyo estado sea " Pendiente".
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

**Reglas de Negocio / Backend (Lógica de Colores y Estados):**

1. **Azul (Informativo):** Acción "Creado" o "Corregido". Icono letra 'S' o 'C'. Fondo de mensaje celeste.
2. **Verde (Positivo):** Acción "Liberado" o "Aprobado". Icono check '✓' o letra 'E' (para ETO). Fondo
    de mensaje verde menta.
3. **Rojo (Crítico/Final):** Acción "Devuelto" o "Eliminado". Icono 'X' roja. El título del mensaje cambia
    automáticamente a _"Observación adjunta:"_ sobre fondo rojizo.

#### 4.

5. **Ámbar (Espera):** Acción "Pendiente". Icono de reloj de arena. Representa una tarea asignada
    que no ha sido transaccionada.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
6. **Gris (Histórico):** Acción "Reasignado". Icono letra 'R'. Se aplica a tareas que fueron retiradas de
un usuario para ser entregadas a otro.

En caso de reasignar usuarios, estos nuevos usuarios son los que deben figurar en el monitor en la
columna “RESPONSABLE”.

**US-8.02: Intervención Administrativa, Reasignación Secuencial y Monitoreo ETO**

- **Como** Gestor Documental (ETO)
- **Quiero** ejecutar acciones de contingencia sobre tareas pendientes o documentos erróneos.
- **Para** destrabar flujos estancados y mantener la continuidad operativa sin violar la integridad de la
    auditoría.
- **Criterios de Aceptación (Frontend/UI):**
1. **Tablero de Monitoreo (Dashboard):**
2. En “CONSULTAR DOCUMENTOS” se podrá generar un reporte grafico (información a determinar
    por ETO) y esta tabla podrá ser exportada a Excel **Interfaz de Reasignación:**
       o Al hacer clic en Reasignar desde el Timeline, se abre un modal central.

```
o Campo Predictivo: Un input con funcionalidad de autocompletado (datalist) para buscar
y seleccionar al nuevo responsable.
o Seguridad: Panel de "Confirmación de Doble Autenticación" que solicita Usuario y
Contraseña obligatoriamente.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

**Reglas de Negocio / Backend (Lógica de Trazabilidad Secuencial):**

1. **Lógica de Reasignación (Paso 6 y 7):**
    o Cuando ETO transfiere una tarea del "Usuario A" al "Usuario B", el sistema **no**
       **sobrescribe** datos.
    o **Cierre de Nodo:** El registro original del "Usuario A" cambia su acción a "Reasignado". Se
       inyecta el mensaje: _"Reasignado por el usuario ETO [Nombre] la tarea que era de [Usuario_
       _A] a [Usuario B]"_.
    o **Apertura de Nodo:** Se crea un nuevo registro al final del historial (Paso 7) para el "Usuario
       B" con acción "Pendiente" y el mensaje: _"Tarea pendiente de atención tras reasignación"_.
2. Puede existir 5 formas de reasignar un documento
a) Reasignación manual desde el rol de Eto desde la pantalla de “Consultar documentos” en el
    timeline.
b) Reasignación automática por incumplimiento a plazos establecidos.
c) Reasignación automática por retiro/desvinculación de personal.
d) Reasignación manual cuando el usuario revisor/aprobador realiza la acción de DELEGAR su tarea
    a su usuario configurado como delegado.
e) Reasignación automática cuando el usuario configura sus vacaciones.

En todos los casos esta reasignación se debe marcar en el nodo de etapas del proceso y reportar en el
monitor al usuario reasignado/delegado con el que se encuentra la tarea. En cualquier caso al usuario
reasignado se le notificara la asignación de la tarea por email.

3. **Lógica de Anulación:** Al confirmar con el botón ✕, el estado del proceso en la base de datos
    cambia a "Eliminado". Se bloquea cualquier edición posterior y se añade el nodo de cierre en el
    Timeline

**US-8.03: Generación de Reportes Dinámicos (Rol ETO)**

- **Como** Gestor Documental (ETO)
- **Quiero** exportar la metadata del sistema y ver gráficos estadísticos
- **Para** presentar informes de calidad, medir tiempos de respuesta por gerencia y preparar
    auditorías.
- **Criterios de Aceptación (Frontend/UI):**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Dado que me encuentro en la pantalla "Reportes"
```
Los gráficos se van a definir con ETO según la data generada y necesidad.

```
o Cuando hago clic en el botón " Visualizar reporte gráfico".
o Entonces se despliega un contenedor interactivo con gráficos de barras horizontales
mostrando:
▪ Documentos por Estado del Proceso (En ejecución vs. Concluido vs. Eliminado).
▪ Documentos por Área (Top 4 áreas con más flujo documental).
o Cuando utilizo el menú desplegable "↓ Exportar reporte" y selecciono "Excel" o "PDF".
o Entonces el sistema compila la vista actual (respetando los filtros aplicados) y descarga
el archivo con el nombre Reporte_SGD_COFAR_DDMMYYYY.
```
- Lo reportes gráficos definidos al querer profundizar en algun dato, presionar sobre el grafico y
    mostrar los datos asociados que muestran ese resultado, como interacción entre objetos/
    obtención de detalles de power bi.
- Ejemplo:
- **Reglas de Negocio / Backend:**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
1. **Sanitización de Datos:** La exportación a Excel no debe incluir HTML ni código de los
badges. Debe mapear los datos planos (Ej: En lugar de renderizar el badge azul, exporta
la celda como "Concluido").
2. **Columnas de Tiempos Ocultos (Excel):** El Excel incluirá columnas de metadatos
profundos como: Tiempo Promedio en Revisión (Horas) y Cantidad de Devoluciones
(Ciclos), calculados matemáticamente por el backend leyendo la tabla del timeline.

**US-8.04: Interacción con el Asistente Inteligente de Base de Datos)**

- **Como** usuario del sistema en todos sus roles
- **Quiero** poder hacerle preguntas en lenguaje natural a un asistente de IA conectado al servidor
- **Para** obtener datos complejos sobre vencimientos o cuellos de botella sin tener que armar filtros
    manuales o exportar Excels pesados.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que hago clic en el botón "Asistente IA (BD)" en el menú lateral.
```
```
o Entonces se abre la interfaz s-chat-ai simulando una aplicación de mensajería.
o Y el sistema muestra un mensaje de bienvenida.
o Cuando ingreso un texto en la barra de chat input y presiono "Enter" o "Enviar".
o Entonces mi mensaje aparece alineado a la derecha en color azul.
o Y aparece un indicador visual "Consultando Base de Datos..." alineado a la izquierda.
o Tras el tiempo de procesamiento , el indicador desaparece y el bot responde.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Reglas de Negocio / Backend (Motor NLP a SQL):**
1. **Traducción de Lenguaje Natural a Query:** El backend cuenta con un middleware NLP
(ej. integración por API segura). Si el usuario escribe _"¿Cuáles son los documentos
próximos a vencer?"_ , el middleware extrae la intención y ejecuta un Query interno:
SELECT * FROM documentos WHERE estado = 'Vigente' AND fecha_expiracion <=
DATE_ADD(NOW(), INTERVAL 30 DAY).
2. **Respuesta Estructurada:** El asistente devuelve un formato HTML limpio, listando los
códigos, títulos y fechas, y ofreciendo botones interactivos dentro del chat (Ej: Botón
"Generar Reporte de Retrasos en Excel").
3. **Aislamiento de Datos:** La IA no tiene permisos de escritura (UPDATE/DELETE). Es
estrictamente de consulta (SELECT). No puede alterar el estado de ningún documento ni
flujo.
4. Los usuarios generales únicamente pueden hacer consultas sobre documentos que se
encuentran aprobados en la lista maestra. EL ROL ETO puede hacer consultas sobre
todos los datos de la base de datos, procesos en ejecución, eliminados y otros.

**US-8.05: Intervención Administrativa (Reasignación Secuencial)**

- **Como** Gestor Documental (ETO)
- **Quiero** poder reasignar tareas estancadas directamente desde el buscador


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Para** destrabar los flujos sin perder la trazabilidad de la auditoría.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que hago clic en el botón "Reasignar" que se puede acceder a el desplegando las
tareas de proceso.
```
```
o Entonces se despliega un Modal centrado pidiendo el Nombre del nuevo responsable
(solo en reasignación) mediante un autocompletado predictivo.
```
```
o Y el modal exige obligatoriamente la Doble Autenticación (Usuario y Contraseña).
```
- **Reglas de Negocio / Backend (La Cronología Estricta):**
    1. **Regla de Reasignación Secuencial:** En la base de datos **nada se sobrescribe**. Al
       reasignar la tarea del "Usuario A" al "Usuario B":
          ▪ El nodo original del "Usuario A" pasa de estado _Pendiente_ a _Reasignado_ (Gris).
             En su mensaje se inyecta: "Reasignado por ETO [Nombre] la tarea que era de
             [Usuario A] a [Usuario B]".
          ▪ Se genera un **nuevo nodo** al final del historial (abajo de todo) asignado al "Usuario
             B" con estado _Pendiente_ (Ámbar) y la fecha/hora de la reasignación.
          ▪ La Bandeja de Tareas se actualiza quitándole la tarea al Usuario A y
             entregándosela al Usuario B, notificandose el cambio por email.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

**US- 8 .0 6 : Suspensión de Flujo por Rechazo Crítico (Eliminación Definitiva)**

- **Como** Gestor Documental (ETO)
- **Quiero** tener la opción de eliminar un proceso si el documento es insalvable o viola normativas
    críticas o fue abierto por error.
- **Para** detener el ciclo de vida sin estar en un bucle infinito de devoluciones.
- **Criterios de Aceptación (Frontend/UI):**
    o **Dado que** estoy en la pantalla de “Consultar documentos”, existe un botón (ícono de una
       X color rojo): " Anular proceso".

```
o Cuando lo presiono, el sistema advierte: "Esta acción abortará todo el proceso documental
actual."
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Reglas de Negocio / Backend:**
1. El documento cambia el estado en el que se haya encontrado a “Eliminado”.

Únicamente se pueden eliminar procesos en estado “EN EJECUCION” no asi los concluidos o eliminados.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

#### ÉPICA 9: ADMINISTRACIÓN DEL SISTEMA Y PARAMETRIZACIÓN GLOBAL

Esta épica centraliza la configuración de todas las reglas de negocio, permitiendo que el sistema sea
flexible y auditable sin necesidad de cambios en el código fuente.

**US-9.01: Configuración de Variables de Tiempo y SLA (Acuerdos de Nivel de Servicio)**

- **Como:** Administrador del Sistema / Rol ETO
- **Quiero:** Modificar los plazos de vigencia, tiempos de respuesta y límites de atención
- **Para:** Ajustar el flujo documental a las políticas de calidad vigentes de la compañía.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que ingreso a la pantalla "Parametrización General" (Rol ETO).
```
```
o Entonces visualizo una sección denominada "Tiempos y SLAs" con campos de entrada
numéricos.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

La vigencia depende del tipo de documento, el plazo máximo de revisión, aprobación es igual al plazo para
delegación. Semaforización por tareas (control de lectura 30 días, por evaluaciones y por revisión y
aprobación semaforización en lista, maestra por docs. próximos a vencer.

```
o Cuando modifico el valor de "Tiempo de vigencia (Años)" y guardo los cambios.
o Entonces el sistema debe validar que el valor sea positivo y mostrar un mensaje de
confirmación: "Parámetro actualizado: Los nuevos documentos se calcularán a [X] años."
o Y debo visualizar selectores para:
▪ Plazo máximo de revisión/aprobación (Días).
▪ Tiempo de espera antes de auto delegación (Días).
▪ Semaforización: Configuración de umbrales para colores Verde, Amarillo y Rojo
en bandejas.
```
- **Reglas de Negocio / Backend:**
    1. **Persistencia Dinámica:** Los valores se almacenan en una tabla de configuracion_global.
       Todas las funciones de cálculo de fechas (SLA y Vencimientos) deben consultar esta tabla
       en tiempo real.
    2. **No Retroactividad:** Los cambios en los plazos de revisión afectan solo a las tareas
       generadas _después_ del cambio; los flujos en curso mantienen su SLA original para no
       viciar la auditoría.

**US-9.02: Panel de Restricciones Físicas, Descargas e Interfaz**

- **Como:** Administrador del Sistema / Rol ETO
- **Quiero:** Establecer límites técnicos sobre archivos y visualización de datos
- **Para:** Garantizar la seguridad de la información y el rendimiento óptimo del servidor.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que estoy en el panel de Ajustes.
o Entonces visualizo la sección "Restricciones".
```
```
o Cuando configuro el "Límite de archivos adjuntos" o el "Tamaño máximo (MB)".
o Entonces el formulario de "Nueva Solicitud" debe actualizar sus validaciones de lado del
cliente instantáneamente.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Y debo poder definir:
▪ Límite de descargas de editables por día (Input numérico).
▪ Tipos de documentos excluidos del límite de descarga (Multiselect).
▪ Paginación de "Mi Bandeja de tareas" (Dropdown: 10 como sugerido pero
modificable).
```
- **Reglas de Negocio / Backend:**
    1. **Validación de Middleware:** El backend debe rechazar peticiones que excedan el tamaño
       configurado (ej. 20MB) devolviendo un error 413 ( _Payload Too Large_ ).
    2. **Contador de Sesión:** El sistema debe llevar un registro diario de descargas por
       usuario/documento para bloquear el acceso al editable si excede el límite parametrizado.

**US-9.03: Gestión de Diccionarios y Matriz de Enrutamiento (CRUD)**

- **Como:** Administrador del Sistema / Rol ETO
- **Quiero:** Gestionar los catálogos de datos y la asignación de analistas por gerencia
- **Para:** Mantener la integridad de las categorías y asegurar que las tareas lleguen al responsable
    correcto.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que accedo a "Diccionarios y Enrutamiento".
```
```
o Entonces visualizo tablas editables para: Tipos de Documentos, Estados de Proceso y
Estados de Tarea, enrutacion eto, codificación de documentos
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia

```
o Y visualizo la Matriz de Enrutamiento ETO : Una tabla que permite vincular una Gerencia
(ej. Calidad) con uno de los 3 Analistas ETO (ej. aromero).
o Cuando un analista es marcado como "Ausente", el sistema debe mostrar un selector para
elegir al "Delegado" que recibirá sus tareas de liberación, salvo ya se haya configurado un
delegado en mi perfil (mostrar el mismo)
```
- **Reglas de Negocio / Backend:**
    1. **Integridad Referencial:** No se permite eliminar un "Estado" o "Tipo de Doc" si existen
       registros activos asociados a él (borrado lógico/desactivación).
    2. **Lógica de Enrutamiento:** El sistema consulta esta matriz en el Paso 4 del flujo para
       asignar el owner_id de la tarea de liberación.

**US-9.04: Gestor de Plantillas de Notificación (Email)**

- **Como:** Administrador del Sistema / Rol ETO
- **Quiero:** Personalizar el contenido de los correos automáticos mediante variables dinámicas
- **Para:** Estandarizar la comunicación oficial de COFAR sin depender de programadores.
- **Criterios de Aceptación (Frontend/UI):**

```
o Dado que selecciono una notificación (ej. "Nueva Tarea Asignada").
```
```
o Entonces se abre un editor de texto enriquecido (Rich Text) con el cuerpo del correo.
o Y visualizo un panel de "Etiquetas Disponibles" (ej. {{CODIGO}}, {{USUARIO}}, {{LINK}}).
o Cuando inserto una etiqueta y guardo.
o Entonces el sistema muestra una previsualización del correo con datos de prueba
inyectados.
```

```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Reglas de Negocio / Backend:**
1. **Motor de Plantillas:** El backend utiliza un motor (como Handlebars o Jinja2) para
reemplazar las etiquetas por los valores reales de la base de datos antes del envío vía
SMTP.

**US-9.05: Gestión Centralizada de Usuarios y Roles**


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
- **Descripción:** Como Administrador del Sistema, quiero tener un panel de control de usuarios para
gestionar sus accesos, perfiles y estados de disponibilidad, garantizando la continuidad operativa
del flujo documental.
- **Criterios de Aceptación principales:**

```
o Visualizar la lista completa de usuarios sincronizados (AD/LDAP).
o Consultar y modificar los Roles (Visualizador, Estándar, ETO, Admin) y Perfiles de cada
usuario.
o Ver el delegado (back-up) asignado a cada usuario.
o Acción de Override: Capacidad de marcar o desmarcar el estado de "Vacaciones /
Ausencia" de un usuario de forma manual (útil para emergencias donde el usuario no
puede acceder al sistema).
```
Este listado se debe poder exportar en Excel.

**US-9.06: Mantenimiento de la Estructura Organizacional (Gerencias y Áreas)**

**Descripción:** Como Administrador / Gestor Documental (ETO), quiero administrar la jerarquía de
Gerencias y Áreas de la empresa mediante un panel de control, incluyendo la capacidad de promover
áreas a gerencias, para que el motor de enrutamiento y los formularios reflejen la evolución corporativa
vigente sin romper el historial.

**Criterios de Aceptación:**

1. El sistema debe permitir listar, crear y editar (nombres o códigos) Gerencias de primer nivel.
2. El sistema debe permitir listar, crear y editar Áreas (Sub-unidades) y asignarlas a una Gerencia
    específica.
3. **Reestructuración (Movilidad):** La interfaz debe permitir "Mover" un Área existente hacia una
    Gerencia distinta mediante un selector desplegable.
4. **Promoción de Jerarquía (Conversión):** El sistema debe incluir una opción para convertir un Área
    existente en una Gerencia de primer nivel, independizándola de su gerencia original.


```
UNIDAD SOLICITANTE: ETO Vigente desde: 30 /0 4 /202 6
```
```
DIGITALIZACION DEL PROCESO DE GESTIÓN DOCUMENTAL Versión: 00
```
..
La información contenida en este documento es de propiedad y uso confidencial de COFAR, si la impresión de este documento no lleva un sello rojo de “Copia
5. **Alerta de Inactivación:** Si el usuario intenta eliminar un área/gerencia que posee historial, el
frontend debe mostrar un modal de advertencia indicando: _"Esta estructura tiene documentos
vinculados. Será ocultada de las nuevas solicitudes, pero se mantendrá en el historial para fines
de auditoría"_.

**Reglas de Negocio (Backend):**

1. **Migración Jerárquica (Conversión de Área a Gerencia):** Al ejecutar una conversión, el backend
    NO debe crear un registro nuevo ni eliminar el anterior. Debe actualizar el nivel del registro
    existente en el árbol jerárquico (ej. estableciendo su parent_id como nulo/raíz) conservando su
    identificador original (PK). Esto garantiza que los documentos históricos sigan vinculados
    correctamente y no se rompan las consultas.
2. **Integridad Referencial y Borrado Lógico:** El backend debe rechazar categóricamente cualquier
    intento de borrado físico (DELETE) de áreas o gerencias que tengan llaves foráneas (FK)
    vinculadas a documentos históricos o flujos en curso. En su lugar, el backend aplicará
    automáticamente un "Borrado Lógico" (UPDATE estado='Inactivo').
3. **Invalidación de Caché (Runtime Impact):** Una vez que el backend confirma la creación, edición,
    conversión o inactivación de un elemento de la estructura, debe refrescar la caché del sistema
    para que estos cambios impacten inmediatamente en los desplegables de "Creación de Solicitud"
    (Épica 2) y filtros (Épica 5), sin requerir un redespliegue de la aplicación.


