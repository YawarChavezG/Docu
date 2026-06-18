# Análisis de bugs/fixes — Sesión 25 (2026-06-17)

> **Origen:** lista de 22 issues reportados por el cliente durante testing manual del 2026-06-17.
> **Estado:** análisis + agrupación + validación en BD/API. **NO incluye código todavía**.
> **Próximo paso:** tu OK sobre los TODOs propuestos, y recién ahí empezar a codear.

## Resumen ejecutivo

| # | Grupo | Issues | Severidad | Tipo |
|---|---|---|---|---|
| 1 | Perfil / Ausencias | 2 | 🟠 Alta | Bug funcional |
| 2 | Performance al login | 1 | 🟡 Media | UX/perf |
| 3 | Editar Usuario / Rol | 1 | 🟠 Alta | Bug funcional |
| 4 | Sync AD | 4 | 🟠 Alta | Bug funcional |
| 5 | Estados de proceso/tarea | 1 | 🟡 Media | UI + error |
| 6 | Tipos de documento | 1 | 🟢 Baja | UI |
| 7 | Matriz de enrutamiento | 1 | 🟡 Media | UI |
| 8 | Gestión de Usuarios (filtros / columnas / KPIs / botones) | 5 | 🟡 Media | UI/feature |
| 9 | /plantillas (vista tienda + quitar IA) | 2 | 🟢 Baja | UI |
| 10 | /version-editable (política no hardcodeada) | 1 | 🟠 Alta | Bug datos |
| 11 | Wizard /aprobacion-documento | 3 | 🟠 Alta | UI + bug funcional |

**Total: 22 issues agrupados en 11 grupos.**

---

## Validación previa (datos reales)

| Hecho | Fuente | Impacto |
|---|---|---|
| User 18 (`eto_test`) tiene 4 ausencias registradas (3 vacaciones + 1 capacitación), todas activas o recientemente canceladas, pero `usuarios.ausente = false` | `SELECT * FROM usuarios u JOIN ausencias a ON a.usuario_id=u.id WHERE u.id=18` | **CONFIRMADO bug #1.1** |
| `soporteglpi` está en BD con `ad_postal_code=NULL, ad_info='', es_usuario_ad=f` | `SELECT * FROM usuarios WHERE username='soporteglpi'` | El usuario NO vino de sync (es_usuario_ad=false). Probablemente es un stub preexistente. El filtro en `ad_service.py:495-497` lo excluiría. |
| `ychavez` tiene `area_id=NULL, ad_info='Tecnología'` | `SELECT * FROM usuarios WHERE username='ychavez'` | **CONFIRMADO bug #4.3**: el login no muestra Área |
| `configuracion_global`: `max_descargas_editables_dia=3`, `tipos_excluidos_limite_descarga=["METODOLOGIA","ESPECIFICACION"]` | `SELECT * FROM configuracion_global WHERE clave LIKE '%descarga%'` | El "1 doc/día" del banner es HARDCODED (no es 1, es 3 en BD) |
| `tipos_documento.max_descargas_dia=10` para los 13 tipos activos | `SELECT * FROM tipos_documento WHERE activo=true` | El "10 docs/día" del banner es correcto solo para CC-1 y CC-7 |
| Estados activos: 3 PROCESO + 6 TAREA + 3 ACCION + 1 PENDIENTE | `SELECT * FROM estados WHERE activo=true` | La enum ACCION existe y está sembrada |
| `PATCH /api/v1/estados/58` con `{"contexto":"PROCESO","nombre":"Correccion"}` → **HTTP 200 OK** | `curl.exe` real | El backend SÍ acepta el cambio. El error reportado debe ser de frontend. |
| `usuarios.soporteglpi` tiene `es_usuario_ad=f` | `SELECT * FROM usuarios WHERE username='soporteglpi'` | Stub local, no fue traído por sync. |

---

## GRUPO 1 — Perfil / Ausencias (2 issues)

### Issue 1.1 — Ausencia con motivo distinto a "vacaciones" NO marca `usuario.ausente=true`

**Severidad:** 🟠 Alta
**Reportado por cliente:**
> "solo cuando marco de tipo vacaciones es que se guarda tanto en la tabla de usuarios como en la tabla de ausencias. Pero si es que marco la ausencia con motivo de licencia, capacitación y otro... solo se registra en la tabla de ausencias, pero en la tabla de usuario no."

**Validado en BD:**
```
user 18 (eto_test):
  ausencia id=2: vacaciones,    activo=t, vigente  → usuario.ausente=??
  ausencia id=3: vacaciones,    activo=t, vigente  → usuario.ausente=??
  ausencia id=4: vacaciones,    activo=f (cancel)
  ausencia id=5: capacitacion,  activo=t, vigente  → usuario.ausente=f  ← BUG
```

**Root cause (código revisado):**
- Archivo: `backend/app/api/v1/ausencias.py:60-82` (`_vigente_set_usuario_ausente`)
- El helper ES llamado correctamente desde POST/PATCH/DELETE (líneas 203, 248, 286).
- El código de la función es correcto: cuenta `vigentes` y setea `user.ausente = (count > 0)`.
- **PERO** la query de "vigentes" en `_vigente_set_usuario_ausente` (línea 66-73) usa `Ausencia.fecha_desde <= hoy AND fecha_hasta >= hoy` — esto debería incluir ausencias vigentes de CUALQUIER motivo.
- El usuario confirmó que las fechas de la capacitación están en rango vigente. Entonces el `count` debería ser > 0 y `ausente=True`.

**Causa probable REAL:** investigando más, veo que `ausencias.py:185` chequea `current.id != usuario_id` (línea 184). El usuario prueba en SU propio perfil → `current.id == usuario_id` → ok. Pero al guardar, si el cliente envía el path equivocado, podría no llamar al helper. Hay que agregar logs o un test con curl.

**Otra causa probable:** El usuario pudo haber probado con un usuario que NO está en `ProfileModal.js` (línea 162-170), donde el flujo de "guardar" llama a `apiPost(/ausencias/usuarios/${myId}, ...)`. Si por algún motivo el path POST no llamó al helper, el flag no se setea. Hay que verificar con un test e2e.

**Fix propuesto:**
1. Agregar test pytest que cree una ausencia con motivo="capacitacion" y verifique que `usuarios.ausente=True`.
2. Si el test pasa, el bug está en frontend (ProfileModal no llama correctamente al endpoint).
3. Si el test falla, el bug está en backend y hay que debuggear `_vigente_set_usuario_ausente`.

**Estimación:** 30 min.

---

### Issue 1.2 — Lista de delegados en Mi Perfil corta (solo hasta "D")

**Severidad:** 🟡 Media
**Reportado por cliente:**
> "La lista para buscar un delegado dentro de la pantalla de perfil, solo trae usuarios hasta la letra D parece, luego no puedo buscar a mas. Aqui debes considerar que solo me traiga la lista COMPLETA pero de los usuarios que tengan el rol de revisor, revisor-aprobador, ETO."

**Root cause (código revisado):**
- Archivo: `frontend/src/components/ProfileModal.js:99-102`
  ```js
  const resActivos = await apiGet('/usuarios?estado=activo&page_size=200&q=${encodeURIComponent(this.username)}')
  ```
- `page_size=200` y ordenado por `nombre_completo` (default en backend). Con 750+ usuarios activos, los primeros 200 llegan solo hasta "D" o "E" alfabéticamente.
- El backend ordena por `nombre_completo.asc()` en `usuarios.py:286`.
- **Otro bug:** el `q` se inicializa con `this.username` (el nombre del usuario actual), así que filtra por ese string. Pero como el input está vacío, no debería filtrar... aunque el `q` se pasa igual. Hay que limpiar.

**Fix propuesto:**
1. Reemplazar la llamada para usar `usuariosApi.listPorCualquierRol(['ELABORADOR - REVISOR', 'ELABORADOR - REVISOR - APROBADOR', 'ETO'])` (helper ya existe en `parametrizacionApi.js:159`).
2. Eliminar el `q` filtrado por username.
3. Subir `page_size` a 500+ como red de seguridad.
4. Bonus: el `auth.user.username` en `q` está mal — confunde con delegación.

**Estimación:** 20 min.

---

## GRUPO 2 — Performance al login (1 issue)

### Issue 2.1 — "Tarda mucho en recargar los recursos, no carga el perfil"

**Severidad:** 🟡 Media
**Reportado por cliente:**
> "Al momento de ingresar al sistema tarda mucho en recargar los recursos lo que hace que no cargue a tiempo ni siquiera el perfil"

**Root cause (código revisado):**
- Archivo: `frontend/src/router/index.js` + `frontend/src/store/auth.js` + `frontend/src/utils/api.js`
- Posibles causas:
  1. **Vite dev server (HMR) tiene 8+ servicios y tarda** en compilar el primer bundle de cada página. Solución: build de producción o `optimizeDeps` en vite.config.
  2. **ProfileModal hace 5+ requests en serie** (línea 50-112 en `ProfileModal.js`): `me`, `usuarios?...`, `roles`, `usuarios?estado=activo&page_size=200`, `ausencias`. Cada uno secuencial.
  3. **Bundle size**: el bundle incluye Tiptap, Alpine, full Calendar, etc. Se debería hacer code-splitting por ruta.

**Fix propuesto:**
1. Refactor `ProfileModal.abrir()` para usar `Promise.all` en las 5 requests.
2. Performance trace con Chrome DevTools en una sesión fresca para confirmar dónde está el cuello de botella real.
3. Si es Vite, considerar `manualChunks` en `vite.config.js`.

**Estimación:** 45 min (incluye perf trace).

---

## GRUPO 3 — Editar Usuario / Rol + Delegado (1 issue)

### Issue 3.1 — Asignar rol eto/revisor/aprobador obliga a seleccionar delegado

**Severidad:** 🟠 Alta
**Reportado por cliente:**
> "Si eliges eto, revisor o aprobador quiero que una vez le asignes ese rol a un usuario NO se OBLIGATORIO seleccionar un delegado."

**Root cause (código revisado):**
- Archivo: `frontend/src/pages/Parametrizacion.js:1342, 1386, 2372, 2377, 2384` (modal Editar Usuario)
- En el modal:
  - línea 1342: `if (!this.editForm.requiere_delegado) { ... }` (lógica que oculta el picker)
  - línea 1386: `if (this.editForm.requiere_delegado && !this.editForm.delegado_id) { window.toast('⚠️ ...'); return }` ← **BLOQUEA EL GUARDADO**
  - línea 2372: badge "⚠ requiere delegado" cuando `editForm.requiere_delegado`
  - línea 2377: option "(requiere delegado)" en el select de rol
  - línea 2384: `x-show="editForm.requiere_delegado"` muestra el campo delegado
- El **backend NO obliga** a delegado: `usuarios.py:810-826` solo actualiza roles sin tocar `delegado_id`. La validación es 100% frontend.

**Fix propuesto:**
1. **Frontend (`Parametrizacion.js`):**
   - Eliminar la validación bloqueante en línea 1386 (cambiar por warning no bloqueante).
   - Cambiar el label de línea 2372 de "⚠ requiere delegado" a algo más suave: "(asignar delegado recomendado)".
   - En línea 2377: cambiar el option text.
2. **Backend (`usuarios.py`):** no requiere cambios — el `rol_codigo` no fuerza `delegado_id`.

**Estimación:** 15 min (frontend only).

---

## GRUPO 4 — Sync AD (4 issues)

### Issue 4.1 — Error 403 al sincronizar AD

**Severidad:** 🟠 Alta
**Reportado por cliente:**
> "al querer realizar la accion de sincronizar AD. me sale error 403"

**Root cause (código revisado):**
- Archivo: `backend/app/api/v1/usuarios.py:328` → `_require_admin(request, db)`.
- El endpoint `POST /usuarios/sync-ad` SOLO lo puede invocar ADMIN.
- El cliente es ETO y presiona el botón → 403 (esperado por código).
- Frontend: `Parametrizacion.js:2144-2145` muestra el botón "Sincronizar AD" a todos (sin condición).

**Fix propuesto:**
- **Frontend:** Ocultar el botón si el rol no es ADMIN. Línea 2227 ya usa este patrón para "Impersonar":
  ```js
  x-show="$store.auth.role === 'admin' || $store.auth.role === 'eto'"
  ```
  Replicar para Sincronizar AD: `x-show="$store.auth.role === 'admin'"`.
- Eliminar la segunda copia en línea 2236 (que también muestra el botón).

**Estimación:** 5 min (frontend only).

---

### Issue 4.2 — Sync AD trae `soporteglpi` sin código SAP

**Severidad:** 🟠 Alta
**Reportado por cliente:**
> "vi que me trajo al usuario 'soporteglpi' el cual si esta en el ad y esta en la OU de Oficina Central, pero este NO tiene código SAP. Por lo que no debería haberlo traído al momento de ahcer la sincronización con AD. esto validalo porfavor solo debe poder traer usuarios que tengan algo lleno en su código SAP osea en AD ese campo es el 'postalCode'."

**Validado en BD:**
- `soporteglpi` está con `ad_postal_code=NULL, es_usuario_ad=f`.
- El filtro en `ad_service.py:495-497` (`if not postal: continue`) es correcto para sync_ad.
- `soporteglpi` no fue traído por sync_ad — fue creado como stub local.

**Root cause REAL:**
- El flujo de **login on-demand** (auth.py:262-276) llama a `ad_service.obtener_atributos_usuario_ad(username)` que SÍ acepta usuarios sin postal (no filtra por `postalCode`).
- Cuando un usuario sin SAP hace login contra AD, el sync on-demand lo crea/actualiza en BD sin filtro de SAP.

**Fix propuesto:**
1. `ad_service.ldap_get_user_by_samaccountname` debe filtrar también por `postalCode` no vacío.
2. Si el usuario se intenta loguear sin SAP, retornar warning al cliente (no abortar el login, pero avisar).
3. Alternativa: `auth.py` debe chequear `tiene_codigo_sap` después del bind y rechazar con 403 si no tiene (más estricto, alineado con sync_ad).

**Estimación:** 30 min (backend + test).

---

### Issue 4.3 — `ychavez` no muestra Área en Mi Perfil

**Severidad:** 🟠 Alta
**Reportado por cliente:**
> "Cuando me logee con mi usuario de AD y vi mi perfil el campo de Area sale vacio. ... debería salir Tecnologia o algo asi."

**Validado en BD:**
- `ychavez`: `area_id=NULL, ad_info='Tecnología', ad_postal_code='10002320'`

**Root cause (código revisado):**
- Archivo: `frontend/src/components/ProfileModal.js:64-66`
  ```js
  this.area = (u.gerencia_sigla && u.area_sigla)
    ? `${u.gerencia_sigla} / ${u.area_sigla}`
    : (u.gerencia_sigla || u.area_sigla || 'Sin área')
  ```
- Si `u.gerencia_sigla` y `u.area_sigla` son NULL (porque `area_id` es NULL), muestra "Sin área".
- Pero el usuario SÍ tiene `ad_info='Tecnología'` (department del AD) en BD.

**Fix propuesto:**
- En `ProfileModal.js:64-66`, agregar fallback a `ad_info` (department):
  ```js
  this.area = (u.gerencia_sigla && u.area_sigla)
    ? `${u.gerencia_sigla} / ${u.area_sigla}`
    : (u.gerencia_sigla || u.area_sigla
       || u.ad_info  // ← FALLBACK AD
       || 'Sin área')
  ```
- Similar al patrón que ya existe en `usuarios.py:641-645` para el export.

**Estimación:** 5 min (frontend only).

---

### Issue 4.4 — Sync AD debe hacer PATCH si hay diferencias (ej. área)

**Severidad:** 🟡 Media
**Reportado por cliente:**
> "Validar si esa funcion de sincronizar AD lo que hace es que si en una sincronización trajo al usuario pero sin el campo de AREA completo, pero luego en el AD ya lo completan ese campo. entonces cuando se vuelva a mandar la tarea se tendría que hacer un PATCH creo de las areas que se vean diferencias. Obviamente todo siempre matchearlo con el codigo SAP."

**Validado en código:**
- `usuarios.py:449-470`: el sync YA hace PATCH si cambia `email`, `nombre_completo`, `cargo`, `iniciales`, `ad_postal_code`, `ad_info`.
- Lo que NO se actualiza: **`area_id`**.

**Root cause:**
- `sync_ad` no tiene un mapping de `ad_info` (department) → `area_id` (BD).
- Si en el AD se llena el department, no se refleja en `area_id` de la BD.

**Fix propuesto:**
1. Crear una tabla de mapping `area_departments` (department del AD → area_id de BD) o usar fuzzy match.
2. En `sync_ad`, después de actualizar `ad_info`, intentar mapear el nuevo `ad_info` a un `area_id` y actualizarlo.
3. **Acción inmediata más simple:** en lugar de mapping automático, agregar una columna `area_por_department` (mapping) que ETO puede mantener manualmente desde Parametrización. Y usar ese mapping en sync.

**Estimación:** 2-3 horas (incluye diseño del mapping). Alternativa simple: solo log warning si `area_id` quedó NULL pero `ad_info` está lleno. 15 min.

---

## GRUPO 5 — Estados de proceso y tarea (1 issue)

### Issue 5.1 — Error al cambiar TAREA → PROCESO; faltan opciones en selector

**Severidad:** 🟡 Media
**Reportado por cliente:**
> "Quise el último elemento que hay de Correccion, lo veo que esta en Tarea, hice el lapiz y quise cambiarlo a proceso, cuando le di en guardar me salio un error... en el selector deberían haber 3 opciones: TAREA, PROCESO, ACCION."

**Validado en código:**
- Backend PATCH `/estados/58` con `contexto='PROCESO'` → **HTTP 200** (test ejecutado).
- La enum `ContextoEstado` tiene las 4 opciones: PROCESO, TAREA, ACCION, AMBOS (`estado.py:20-24`).
- BD tiene estados sembrados en los 3 contextos (CONFIRMADO).
- **El error reportado es 100% frontend.**

**Root cause probable:**
- Archivo: `frontend/src/pages/Parametrizacion.js` (sección estados)
- El select de contexto probablemente:
  - (a) Muestra solo TAREA/PROCESO (falta ACCION)
  - (b) Envía un valor que el backend rechaza (ej. lowercase o string no-normalizado)
  - (c) Validación local que no permite cambiar de TAREA a PROCESO
- **Acción:** inspeccionar el formulario de edición de estados en `Parametrizacion.js` para ver qué opciones se renderizan.

**Fix propuesto:**
1. Localizar el `<select x-model="...">` del contexto en `Parametrizacion.js`.
2. Confirmar que tiene las 4 opciones (PROCESO, TAREA, ACCION, AMBOS) hardcodeadas o desde un enum.
3. Reemplazar por iteración sobre una constante `CONTEXTOS = ['PROCESO','TAREA','ACCION','AMBOS']`.
4. Validar que el PATCH funcione end-to-end con un test manual.

**Estimación:** 20 min (incluye localizar el bug específico).

---

## GRUPO 6 — Tipos de documento (1 issue)

### Issue 6.1 — Columna SLUG debe desaparecer

**Severidad:** 🟢 Baja
**Reportado por cliente:**
> "En tipos de documento: la columna de SLUG debe desaparecer, no aporta en nada al usuario. Asi que esa columna debe desaparecer, es mas valida si eso actualmente sirve de algo, en todo caso lo que se usaria es el codigo del doc como te dije. El slug no lo quiero ver en la tabla porfavor."

**Validado en código:**
- `tipos_documento.py:142-143` muestra el slug en audit_log.
- `tipos_documento.py:60` ordena por `codigo, slug`.
- `tipos_documento.slug` se usa en `documentos.py:136, 290, 641, 752` (en DocumentoTipoRef).
- **El slug SÍ se usa** (se devuelve al frontend en responses de documentos), pero NO es necesario mostrarlo al usuario en la tabla de Parametrización.

**Fix propuesto:**
1. Frontend `Parametrizacion.js`: ocultar la columna SLUG de la tabla del tab "Diccionarios y Enrutamiento > Tipos de documento".
2. Backend: NO requiere cambios (el campo se sigue usando internamente para lógica de ordering, no se elimina del modelo).

**Estimación:** 5 min.

---

## GRUPO 7 — Matriz de enrutamiento (1 issue)

### Issue 7.1 — Solo usuarios con rol ETO en la matriz

**Severidad:** 🟡 Media
**Reportado por cliente:**
> "En matriz de enrutamiento, como te dije debería poder ver el listado solo con los usuarios con el ROL de ETO, xq esta es una funcionalidad para ellos."

**Root cause (código revisado):**
- Archivo: `frontend/src/pages/Parametrizacion.js:1350-1380` (modal de matriz ETO).
- La query actual `usuariosActivos` (línea 380) trae TODOS los usuarios activos.
- El backend `matriz-enrutamiento-eto` SÍ filtra por `analista_id` y `delegado_id`, pero el dropdown no los filtra por rol.

**Fix propuesto:**
1. Reemplazar `usuariosActivos` por `usuariosApi.listPorRol('ETO')` en el tab de Matriz ETO.
2. Si la lista queda vacía, mostrar mensaje "No hay usuarios con rol ETO".

**Estimación:** 15 min.

---

## GRUPO 8 — Gestión de Usuarios (5 issues)

### Issue 8.1 — Filtro por activos/inactivos + ausentes/no ausentes

**Severidad:** 🟡 Media
**Reportado por cliente:**
> "Gestion de usuarios debe haber un Filtro para poder ver los usuario en base a si estan activos o inactivos. En vez de ese filtro que sale de Todas las fuentes, igual debería haber aqui un filtro para ver los que estan ausentes o estan no ausentes."

**Root cause:**
- Archivo: `frontend/src/pages/Parametrizacion.js:2138-2142`
- Filtro actual: "Todas las fuentes / Del AD / Locales (test)" — esto filtra por `azure_oid` no nulo vs nulo.
- El usuario quiere: filtro por `estado` (activo/inactivo/desvinculado) + filtro por `ausente` (sí/no).

**Fix propuesto:**
1. Reemplazar el select de "fuente" por 2 selects:
   - "Estado": Todos / Activos / Inactivos / Desvinculados
   - "Ausente": Todos / Solo ausentes / Solo presentes
2. Actualizar `uqOnFilterChange()` para enviar `estado=...&ausente=true|false` al backend.
3. El backend `usuarios.py:264-273` ya soporta `estado`; agregar `ausente` como Query param nuevo.

**Estimación:** 30 min (frontend + backend).

---

### Issue 8.2 — Botón Sincronizar AD solo visible para ADMIN

**Severidad:** 🟡 Media
**Reportado por cliente:**
> "El boton de sincronizar AD debería estar habilitado visualmente solo para el usuario con rol ADMIN, no tiene sentido que lo vea el usuario con rol ETO y no pueda ejecutar ese boton por falte de permisos obviamente. Entonces quita el boton si es que no eres rol adminn."

**Root cause:**
- Archivo: `frontend/src/pages/Parametrizacion.js:2144-2145, 2236`
- El botón no tiene condición de visibilidad.

**Fix propuesto:**
- Agregar `x-show="$store.auth.role === 'admin'"` a AMBOS botones (línea 2144 y 2236).
- Esto va de la mano con Issue 4.1.

**Estimación:** 5 min (cubierto por Issue 4.1).

---

### Issue 8.3 — Columna "Area/Gerencia" → "Area"

**Severidad:** 🟢 Baja
**Reportado por cliente:**
> "En la columna de los usuarios en vez que diga Area/Gerencia, solo debe decir 'Área' lo mismo para cuando se vaya a generar el archivo en excel, esa columna debe decir 'Area'."

**Root cause:**
- Frontend `Parametrizacion.js:2158`: `<th>Área / Gerencia</th>`.
- Backend `usuarios.py:681`: header `"Gerencia / Area"`.

**Fix propuesto:**
1. Frontend línea 2158: cambiar a `<th>Área</th>`.
2. Backend `usuarios.py:681`: cambiar header a `"Área"`.
3. **Decisión de UX:** el contenido actual muestra `"TGN / TI"` (gerencia/area). ¿Mantener ese contenido o solo el area? El usuario dijo "esa columna debe decir Area" — sugiero:
   - Header: "Área"
   - Contenido: priorizar `area_sigla`; si no hay, `ad_info`; si no, "—"
4. Eliminar la duplicación del segundo `<div x-show="u.ad_info">` en línea 2188 (queda solo el principal).

**Estimación:** 10 min.

---

### Issue 8.4 — Módulos Excel: añadir REPORTES a todos excepto VISUALIZADOR y ADMIN

**Severidad:** 🟡 Media
**Reportado por cliente:**
> "En la información de cada usuario cuando se descarga el excel se puede ver una columna de modulos, a ese listado de modulos falta añadirle el módulo 'REPORTES' añadir eso a todos los roles excepto a los de rol VISUALIZADOR y a ADMIN. a ETO no le añadas porque ETO ya tiene 'TODOS' que involucraria REPORTES mas."

**Root cause:**
- Archivo: `backend/app/api/v1/usuarios.py:662`
  ```python
  ", ".join(m.codigo for m in u.modulos) or "-"
  ```
- Esto usa los módulos REALES de la BD. El usuario quiere que en el EXPORT se agregue "REPORTES" virtualmente para ciertos roles.

**Fix propuesto:**
1. Calcular los "módulos efectivos para export":
   ```python
   modulos_export = list(u.modulos)
   tiene_todos = any(m.codigo == 'TODOS' for m in modulos_export)
   es_visualizador = all(r.codigo == 'VISUALIZADOR (CL-EVAL)' for r in u.roles)
   es_admin = any(r.codigo == 'ADMIN' for r in u.roles)
   if not tiene_todos and not es_visualizador and not es_admin:
       if not any(m.codigo == 'REPORTES' for m in modulos_export):
           modulos_export.append(ModuloVirtual(codigo='REPORTES'))
   ```

2. **Decisión clave:** ¿Esto debe persistirse en BD o ser solo cosmético del export? El usuario dijo "a ETO no le añadas porque ETO ya tiene TODOS" — sugiere que es cosmético. Pero también dijo "añadirle el módulo REPORTES" lo que sugiere persistir.

   **Recomendación:** persistir en BD (tabla `usuario_modulos`). Esto es más limpio. Un script de migración agrega REPORTES a los usuarios correspondientes.

3. **Acción inmediata:** crear script `backend/scripts/add_reportes_module.py` que recorre los usuarios y agrega REPORTES según el criterio. Idempotente.

**Estimación:** 45 min (script + test + verificar).

---

### Issue 8.5 — KPI extra "Total inactivos"

**Severidad:** 🟢 Baja
**Reportado por cliente:**
> "En los KPI cards de gestion de usuarios poner un kpi extra para ver total de usuarios inactivos."

**Root cause:**
- Archivo: `frontend/src/pages/Parametrizacion.js:2103-2116` (KPIs)
- KPIs actuales: total, activos, ausentes.
- Backend `usuarios.py:297-301`: retorna `kpis: { total, activos, ausentes }`.

**Fix propuesto:**
1. Backend: agregar `inactivos` y `desvinculados` a `kpis`:
   ```python
   inactivos_all = await db.execute(select(func.count()).where(Usuario.estado == EstadoUsuario.INACTIVO)).scalar_one()
   desvinculados_all = await db.execute(select(func.count()).where(Usuario.estado == EstadoUsuario.DESVINCULADO)).scalar_one()
   kpis = { "total": ..., "activos": ..., "ausentes": ..., "inactivos": inactivos_all, "desvinculados": desvinculados_all }
   ```
2. Frontend: agregar 2 KPI cards más (inactivos en gray, desvinculados en red).

**Estimación:** 15 min.

---

## GRUPO 9 — /plantillas (2 issues)

### Issue 9.1 — Vista tienda responsive

**Severidad:** 🟢 Baja
**Reportado por cliente:**
> "En la seccion de /plantillas se desperdicia mucho espacio, hacer tipo una tienda con los documentos como en cuadrados, hazlo tambien pensando en responsive."

**Root cause:**
- Archivo: `frontend/src/pages/Plantillas.js:106-138` (cards).
- Grid actual: `repeat(2, 1fr)` por default, `lg:grid-cols-3` para ≥1024px.
- El usuario quiere más "tipo tienda" → cards más anchas, mejor uso del espacio.

**Fix propuesto:**
- Cambiar el grid a:
  - Mobile: 1 columna
  - Tablet (sm): 2 columnas
  - Desktop (md+): 3 columnas
  - Large (xl+): 4 columnas
- Cards con `padding` más generoso, iconos más grandes, mejor spacing.
- Estilo tienda: añadir precio visual (versión), rating visual (categoría), botón "Ver detalles" como hover.

**Estimación:** 30 min.

---

### Issue 9.2 — Quitar "IA — Recomendación"

**Severidad:** 🟢 Baja
**Reportado por cliente:**
> "quitar ese elemento que dice: '✦ IA — Recomendación...'. no quiero ver nada de eso."

**Root cause:**
- Archivo: `frontend/src/pages/Plantillas.js:93-97` (bloque hardcodeado).

**Fix propuesto:**
- Eliminar el `<div>` completo de líneas 93-97.
- Sin cambio de backend.

**Estimación:** 2 min.

---

## GRUPO 10 — /version-editable (1 issue)

### Issue 10.1 — Política de Descargas no debe estar hardcodeada

**Severidad:** 🟠 Alta
**Reportado por cliente:**
> "En la pantalla de /version-editable validar que... 'Politica de Descargas: Se puede descargar 1 documento por dia...' Todo ese texto no sea hardcodeado y debería sacar los valores de la base de datos, el 1 documento por día es lo que se tiene en Restricciones de parametrizacion general, luego lo que dice a excepcion de: esos documentos igual son los que estan registrados en la BD como las excepciones, e igual esta registrado el límite de las extensiones."

**Validado en BD:**
```sql
SELECT * FROM configuracion_global WHERE clave LIKE '%descarga%';
  max_descargas_editables_dia = 3
  tipos_excluidos_limite_descarga = ["METODOLOGIA","ESPECIFICACION"]
SELECT codigo, max_descargas_dia FROM tipos_documento WHERE activo=true;
  13 tipos, todos con max_descargas_dia=10
```

**Inconsistencias detectadas:**
- El texto dice "1 documento por día" pero la BD tiene `max_descargas_editables_dia=3`.
- El texto dice "10 por día" para excepciones pero los tipos "excluidos" (METODOLOGIA=CC-1, ESPECIFICACION=CC-7) tienen `max_descargas_dia=10` mientras los demás también tienen 10. No hay diferenciación real.

**Root cause:**
- Archivo: `frontend/src/pages/VersionEditable.js:117-119` (texto hardcodeado).
- Los valores correctos están en BD pero el template no los usa.

**Fix propuesto:**
1. **Backend:** agregar endpoint `GET /api/v1/configuracion-global/categoria/DESCARGAS` (o usar el existente `?categoria=DESCARGAS`).
2. **Frontend `VersionEditable.js`:**
   - En `init()`, cargar `configGlobal.list('DESCARGAS')`.
   - Renderizar el texto dinámicamente:
     ```
     "Se puede descargar {max_descargas_editables_dia} documento(s) por día, a excepción de los documentos tipo {tipos_excluidos_limite_descarga join}, de los cuales se pueden descargar hasta {max_descargas_dia_de_excepcion} por día."
     ```
3. **Decisión de datos:** confirmar con el cliente si la política correcta es 3 (lo que está en BD) o 1 (lo que dice el texto actual). Probablemente 1 es el "default histórico" y 3 fue un cambio que no se reflejó en la UI.

**Estimación:** 30 min (frontend + verificación con cliente).

---

## GRUPO 11 — Wizard /aprobacion-documento (3 issues)

### Issue 11.1 — Quitar "Analista ETO asignado" del wizard paso 1

**Severidad:** 🟠 Alta
**Reportado por cliente:**
> "En la pantalla de /aprobacion-documento en el wizard 1, no se porque pusiste: 'Analista ETO asignado *' esto no debería haber, no esta en los requerimientos, el usuario solicitante no tiene xq estar viendo eso. elimina todo eso."

**Root cause:**
- Archivo: `frontend/src/pages/AprobacionDocumento.js:506-518` (template del campo).
- Estado: `analistaEtoAsignado` (línea 41), `analistasEtoList` (línea 27).
- En `init()` líneas 96-110: carga `usuariosApi.listPorRol('ETO')`.
- En `nextPaso()` línea 294-298: valida que haya ETO asignado (esto bloquea el flujo).

**Fix propuesto:**
1. Eliminar:
   - Estado `analistaEtoAsignado` (línea 41)
   - Computed `analistaEtoSeleccionadoAusente` (línea 182-185)
   - Bloque HTML en líneas 506-518
   - Fetch de `etosRes` en init líneas 96-110
   - Validación bloqueante en `nextPaso()` líneas 294-298
2. **Backend NO requiere cambios** — el campo nunca se envió al backend.

**Estimación:** 15 min (frontend only).

---

### Issue 11.2 — Wizard paso 3: añadir "Reemplazo o baja de documento" sí/no

**Severidad:** 🟠 Alta
**Reportado por cliente:**
> "En el wizard 3 de flujo y firmas quitaste el campo de: 'Reemplazo o baja de documento' debes añadir eso como para que puedan seleccionar en un desplegable si o no."

**Validado en código:**
- Estado `reemplaza: 'no'` (línea 68) y `chipsReemplazo: []` (línea 70) ya existen.
- Funciones `addChipReemplazo` (línea 277) y `removeChipReemplazo` (línea 282) ya existen.
- **Pero NO hay UI en el template para este campo** (líneas 649-695).

**Root cause:**
- El estado y la lógica existen, pero el template no renderiza el select ni los chips.
- Posible regresión: cuando se refactorizó el wizard en sesión 22, se perdió la UI.

**Fix propuesto:**
- Agregar al template del paso 3 (después del bloque de aprobadores, antes del bloque de firma):
  ```html
  <div class="mt-4">
    <label class="form-label">¿Reemplazo o baja de documento?</label>
    <select class="form-input text-xs" x-model="reemplaza">
      <option value="no">No</option>
      <option value="si">Sí</option>
    </select>
    <div x-show="reemplaza==='si'" class="mt-2">
      <label class="form-label">Códigos de documentos a dar de baja</label>
      <div class="flex gap-2">
        <input type="text" x-model="inputReemplazo" @keydown.enter.prevent="addChipReemplazo()" class="form-input text-xs" placeholder="CC-3-005/00">
        <button @click="addChipReemplazo()" class="btn btn-sm">+ Agregar</button>
      </div>
      <div class="flex flex-wrap gap-1.5 mt-2">
        <template x-for="chip in chipsReemplazo" :key="chip">
          <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] bg-amber-50 text-amber-700 border border-amber-200">
            <span x-text="chip"></span>
            <button @click="removeChipReemplazo(chip)">X</button>
          </span>
        </template>
      </div>
    </div>
  </div>
  ```
- Verificar que `firmarEnviar()` ya envíe `reemplaza_documento_ids: this.chipsReemplazo.length ? this.chipsReemplazo : null` (línea 375 — esto ya está pero siempre envía [] si hay chips, lo cual es bug).

  **Sub-bug detectado en línea 375:**
  ```js
  reemplaza_documento_ids: this.chipsReemplazo.length ? [] : null,
  ```
  Esto SI hay chips → envía array vacío. **NO TIENE SENTIDO.** Debería ser:
  ```js
  reemplaza_documento_ids: this.chipsReemplazo.length ? this.chipsReemplazo : null,
  ```

**Estimación:** 25 min (incluye fix sub-bug).

---

### Issue 11.3 — Wizard no persiste datos en `documento_flujo`

**Severidad:** 🟠 Alta
**Reportado por cliente:**
> "hice la prueba de completar este flujo y a lo que veo no se registro en la tabla de documento_flujo, solo se registro mi firma en la tabla firmas_digitales. Pero debería haberse insertado en documento flujo con todo lo que fui llenando en los formularios de wizard y con eso llenar en la tabla que te dije. lo de la tabla de las firmas digitales esta bien, pero la otra tabla que te dije igual es importane."

**Validado en código:**
- `envio_service.py:198-212`: el flujo SÍ se actualiza con `revisor_ids`, `aprobador_ids`, `alcance_difusion_ids`, `reemplaza_documento_ids`, `justificacion`.
- `envio_service.py:262`: commit al final.
- `documentos.py:603-604`: el POST inicial crea un `DocumentoFlujo` con `revisor_ids=[]`, `aprobador_ids=[]`, `alcance_difusion_ids=[]`.

**Root cause probable:**
- Si el cliente miró la tabla `documento_flujo` DESPUÉS del POST inicial (antes de firmar), vería los arrays VACÍOS.
- Después del `/enviar`, los arrays se llenan. Pero si la consulta es muy rápida, puede no ver el cambio.
- **Otra posibilidad:** el flujo se actualiza pero con valores NULL o `[]` si:
  - `firmarEnviar()` no envía `revisor_ids` o `aprobador_ids` (línea 370-371 sí los envía)
  - La request falla por algún motivo y se hace rollback (dejando el flujo con datos vacíos del POST inicial)
  - El cliente visualiza `revisores` que es local state (`this.revisores`) y el flujo tiene `revisor_ids`

**Fix propuesto:**
1. **Diagnóstico:** agregar log en `firmarEnviar()` que muestre qué payload se está enviando.
2. **Verificación manual:** crear un documento completo, firmar, y luego hacer `SELECT * FROM documento_flujo WHERE documento_id=X` y ver los campos JSONB.
3. **Posible fix:** si el flujo SÍ se actualiza, entonces el "bug" es solo visual (el cliente pensó que no se persistió). Documentar en `BITACORA.md`.
4. **Fix adicional:** en `POST /documentos` (paso 1→2 o paso 3), NO crear el flujo con arrays vacíos. Mejor: crear el flujo en el `/enviar` (atómico) y dejar `POST /documentos` solo crear el Documento.
   - **Decisión de diseño:** este cambio es mayor. La sesión 22 decidió crear el flujo en POST para tener el `flujo_id` antes. Revertirlo requeriría cambiar el response del POST para devolver un placeholder.

**Estimación:** 45 min (incluye test e2e del flujo completo con verificación de BD).

---

## RESUMEN DE PRIORIDADES

### 🟠 CRÍTICOS (resolver HOY)
1. **Issue 1.1** — Ausencia motivo != vacaciones no setea `ausente` (BD confirmado)
2. **Issue 4.3** — ychavez sin Área en Mi Perfil (BD confirmado)
3. **Issue 3.1** — Editar usuario: delegado opcional para eto/revisor/aprobador
4. **Issue 4.1** — Botón Sincronizar AD solo para ADMIN (UX + 403)
5. **Issue 10.1** — Política de Descargas no hardcodeada
6. **Issue 11.1** — Quitar "Analista ETO" del wizard
7. **Issue 11.2** — Añadir "Reemplazo o baja" al wizard paso 3
8. **Issue 11.3** — Wizard no persiste en `documento_flujo` (verificar primero)

### 🟡 IMPORTANTES (resolver MAÑANA)
9. **Issue 4.2** — Soporteglpi sin SAP (login on-demand debe filtrar)
10. **Issue 4.4** — Sync AD debe actualizar `area_id` (decidir diseño)
11. **Issue 8.1** — Filtros activos/inactivos/ausentes
12. **Issue 8.4** — REPORTES en Excel (script de migración)
13. **Issue 5.1** — Estados: error al cambiar TAREA→PROCESO (frontend bug)
14. **Issue 1.2** — Lista de delegados corta
15. **Issue 7.1** — Matriz ETO solo usuarios ETO
16. **Issue 2.1** — Performance al login (perf trace primero)

### 🟢 MENORES (backlog)
17. **Issue 8.2** — Cubierto por Issue 4.1
18. **Issue 8.3** — Header "Área" en columna y Excel
19. **Issue 8.5** — KPI inactivos
20. **Issue 9.1** — Vista tienda responsive
21. **Issue 9.2** — Quitar "IA — Recomendación"
22. **Issue 6.1** — Ocultar SLUG de tabla tipos documento

---

## Estimación total

| Severidad | # issues | Estimación |
|---|---|---|
| 🟠 Críticos | 8 | ~4-5 horas |
| 🟡 Importantes | 8 | ~3-4 horas |
| 🟢 Menores | 5 | ~1-1.5 horas |
| **Total** | **22** | **~8-10 horas** |

**Recomendación:** Dividir en **2 sesiones** (~4-5h cada una):
- **Sesión 25 (HOY)**: 8 críticos + 4 importantes = ~6-7h
- **Sesión 26 (MAÑANA)**: 4 importantes + 5 menores = ~3-4h

---

## Próximos pasos

1. **Tu OK** sobre la priorización propuesta
2. Confirmar la estimación de tiempo
3. Identificar si hay issues que **NO** se resuelvan (acepta el bug como "by design")
4. Arrancar con **Issue 1.1** (verificación con test pytest) para validar el flujo de testing

Una vez aprobado, voy a:
- Crear una rama `fix/sesion-25-bugs-17jun` (o continuar en `r2/wizard-y-version-editable`)
- Hacer commits atómicos por issue (1 commit = 1 fix)
- Actualizar `ESTADO.md` y `BITACORA.md` al cerrar
