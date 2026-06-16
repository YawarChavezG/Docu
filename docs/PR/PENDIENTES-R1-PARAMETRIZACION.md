# PENDIENTES R1 - Pantalla de Parametrización

> **Estado:** Documento de trabajo. NO requiere accion inmediata.
> **Origen:** Analisis exhaustivo de la pantalla de Parametrizacion vs BD, realizado el 2026-06-16 al cierre de sesion 9.
> **Proposito:** Servir como guia tecnica para una sesion futura que cierre los bugs identificados antes de la presentacion de R1 al cliente.

---

## Resumen ejecutivo CORREGIDO

Mi primer analisis (commit `33b410c`) concluyo que **"Diccionarios, Gerencias, Restricciones estaban mockeados"**. **ESTO ES INCORRECTO** despues de una re-verificacion con Chrome DevTools.

**Conclusion correcta (sesion 9 - revision final):**

La pantalla de Parametrizacion tiene **dos declaraciones duplicadas** de los handlers de CRUD. La primera declaracion (linea 235-340) **lee de la BD correctamente** pero los handlers de save/delete/duplicate son **pisados por la segunda declaracion** (lineas 537-744) que solo hace `pushLog` local y `toast` - **NO llama al backend**.

**Resultado:**

| Operacion | Estado |
|---|---|
| **CARGAR** (GET) datos del backend | ✅ FUNCIONA - `cargarDiccionarios()`, `cargarGerencias()`, `cargarRestricciones()`, `cargarTiempos()` se ejecutan en `init()` y muestran datos reales de la BD. |
| **GUARDAR** cambios (POST/PATCH/PUT) | ❌ NO FUNCIONA - los handlers `saveTipo`, `deleteTipo`, `saveEstado`, `deleteEstado`, `saveGer`, `deleteGer`, `saveArea`, `deleteArea`, `guardarFilaMatriz`, `guardarPlantilla` son del mock y NO llaman al backend. |
| **Editar y crear** (CRUD completo) | ❌ NO FUNCIONA - mismo problema. |

**Implicacion:** La UI muestra datos correctos del backend (lo cual es por lo que ve "Test TD", "Gerencia Promovida Test", etc.). Pero **cualquier intento de crear/editar/eliminar no persiste** - solo muestra un toast de exito y guarda localmente en el state.

---

## Validacion empirica (Chrome DevTools)

### Test 1: Confirmar que datos SI cargan de la BD

```js
const root = document.querySelector('[x-data="paramPage"]');
const data = root._x_dataStack[0];
// Verificar tab Diccionarios:
data.tiposDocs.length   // = 14 (NO 6 que tiene el mock)
data.tiposDocs[0].id    // = 1 (NO esta en el mock)
data.tiposDocs[0].codigo_doc  // = 1 (campo que solo esta en la BD)
// Test TD esta en la lista:
data.tiposDocs.some(t => t.cod === 'TT_26664')  // = true
```

**Resultado:** 14 tipos con `id` y `codigo_doc` (campos de la BD). El mock solo tiene 6 tipos sin `id` y sin `codigo_doc`. **La carga de BD funciona.**

### Test 2: Confirmar que CRUD no funciona

```js
const t = data.tiposDocs.find(x => x.cod === 'TT_26664');
t.tipo = 'Test_Edicion_' + Date.now();
data.saveTipo(t);
// Error: "this.pushLog is not a function"
```

**Verificacion en BD despues:**
```bash
docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT nombre FROM tipos_documento WHERE codigo='TT_26664'"
# Resultado: "Test TD" - NO cambio
```

**Resultado:** `saveTipo` ejecuta la version del mock (linea 590) que llama `this.pushLog()` que no existe. La BD NO se modifica. **El CRUD de edicion NO funciona.**

### Test 3: Inspeccionar la funcion saveTipo que se ejecuta

```js
data.saveTipo.toString()
// Resultado: "saveTipo(t) {\n  if (!t.tipo.trim() || !t.cod.trim()) { window.toast('Complete tipo y codigo', 'warn'); return }\n  const ant = t._new ? '(nuevo)' : tiposDocParamDB.find(x => x.cod === t.cod)?.tipo || ''\n  t.cod = t.cod.toUpperCase().slice(0, 5)\n  delete t._new\n  this.tipoEditing = null\n  this.pushLog('Tipo de documento', ant, t.tipo + ' (' + t.cod + ')', 'diccionarios')\n  window.toast('✅ Tipo guardado', 'success')\n}"
```

**Resultado:** La version que se ejecuta es la del MOCK (linea 590). La version que llama al backend (linea 274) es pisada.

---

## Hallazgo clave: que pasa y por que

### El bug de las "dos declaraciones"

En `frontend/src/pages/Parametrizacion.js`:

```js
window.Alpine?.data('paramPage', () => ({
  // ============ PRIMERA DECLARACION (lineas 235-340) ============
  // Estado vacio + funciones de CARGA que llaman al backend
  tiposDocs: [],
  estados: [],
  matrizETO: [],
  analistas: [],
  gerencias: [],
  
  async cargarDiccionarios() {
    // SI llama al backend y llena this.tiposDocs con data.items
  },
  async saveTipo(t) {
    // SI llama a tiposDocumento.create/update
  },
  // ... etc
  
  // ============ SEGUNDA DECLARACION (lineas 537-744) ============
  // PISA los handlers con versiones que NO llaman al backend
  tiposDocs: JSON.parse(JSON.stringify(tiposDocParamDB)),  // <- mock
  saveTipo(t) {
    // SOLO hace pushLog local + toast, NO llama al backend
  },
  saveEstado(e) { /* mismo problema */ },
  saveGer() { /* mismo problema */ },
  saveArea(a) { /* mismo problema */ },
  guardarFilaMatriz(m) { /* mismo problema */ },
  guardarPlantilla() { /* mismo problema */ },
  // ... etc
}))
```

### Por que JavaScript ejecuta la segunda declaracion

En JavaScript plano, cuando declaras un objeto literal con propiedades duplicadas, **la ultima gana**:

```js
const obj = { x: 1, x: 2 }
obj.x  // = 2
```

PERO Alpine.js tiene un truco: cuando registras `Alpine.data('name', () => ({...}))`, **Alpine ejecuta la factory cada vez que el componente se monta**. La primera declaracion define los handlers de CARGA (que SI funcionan), y la segunda pisa los handlers de SAVE con versiones del mock.

**Pero entonces por que los datos SI se ven en la UI?** Porque:
1. La primera declaracion define `tiposDocs: []`
2. La segunda declaracion pisa con `JSON.parse(JSON.stringify(tiposDocParamDB))` (mock con 6 items)
3. `init()` se ejecuta y llama `cargarDiccionarios()`
4. `cargarDiccionarios()` hace `this.tiposDocs = data.items` (14 items de la BD)
5. La UI muestra los 14 items

**El state se inicializa, pero los handlers de CRUD quedan pisados por la segunda declaracion.**

---

## Inventario de bugs reales (corregido)

### Tab 1: Tiempos y SLAs (lineas 1252-1317)

#### Comportamiento actual

| Elemento | Carga de BD | Guarda en BD | Notas |
|---|---|---|---|
| Vigencia por tipo de documento | ✅ SI | ❌ NO | Lee `tipos_documento.periodo_vigencia`. Bug especifico: input muestra "Indefinido" cuando `indefinido=true` y no permite editar. |
| Semaforo verde/amarillo | ✅ SI | ❌ NO | `semaforo_verde_dias` / `semaforo_amarillo_dias`. La primera `guardarTiempos` (linea 165) SI persiste. PERO la segunda `guardarTiempos` (linea 538) **NO** - solo toast. |
| Plazo revision/aprobacion | ✅ SI | ❌ NO | `plazo_revision_aprobacion_dias`. Mismo problema. |
| Plazo control de lectura | ✅ SI | ❌ NO | `plazo_control_lectura_dias`. Mismo problema. |

**Conclusion:** La primera declaracion SI funciona, pero la segunda pisa los handlers. Al ejecutar `guardarTiempos()`, se ejecuta la del mock que solo hace toast.

### Tab 2: Restricciones (lineas 1319-1380)

#### BD - claves faltantes

El frontend busca estas claves en `configuracion_global`:
- `max_archivos_por_solicitud` (NO EXISTE en BD)
- `max_tamano_archivo_mb` (NO EXISTE en BD)
- `max_descargas_editables_dia` (NO EXISTE en BD)
- `paginacion_mi_bandeja` (NO EXISTE en BD)
- `tipos_excluidos_limite_descarga` (NO EXISTE en BD)

#### Comportamiento actual

| Elemento | Carga de BD | Guarda en BD | Notas |
|---|---|---|---|
| Limite archivos adjuntos (20) | ❌ NO (fallback mock) | ❌ NO | `cfg.max_archivos_por_solicitud` es undefined, fallback al valor del state. |
| Tamano max MB (20) | ❌ NO (fallback mock) | ❌ NO | Mismo problema. |
| Max descargas/dia (10) | ❌ NO (fallback mock) | ❌ NO | Mismo problema. |
| Paginacion bandeja (10) | ❌ NO (fallback mock) | ❌ NO | Mismo problema. |
| Tipos excluidos (chips) | ❌ NO (fallback mock) | ❌ NO | Ver bug especifico. |
| Boton "Guardar Restricciones" | - | ❌ NO | `guardarRestricciones` (linea 566) es del mock - solo actualiza `ParametrosGlobalesDB` y toast. |
| Boton "Guardar Limites de Descarga" | - | ❌ NO | Mismo problema. |

#### Bug especifico - Dropdown de tipos excluidos VACIO

**Linea 1368-1373 del template:**
```html
<select x-model="nuevoChip" class="form-input text-xs w-auto min-w-[140px]">
  <option value="">Seleccionar tipo...</option>
  <template x-for="(t, idx) in chips" :key="idx + '-' + t">
    <option :value="t" x-text="t"></option>
  </template>
</select>
```

**Problema:** El dropdown solo lista `chips` (los tipos YA excluidos), NO los tipos de documento disponibles. **El usuario no puede AGREGAR un nuevo tipo excluido** desde la UI.

**Solucion:** Reemplazar `<template x-for="t in chips">` por `<template x-for="t in tiposExcluibles">` donde `tiposExcluibles` se llena con `tiposDocumento.list()` filtrado por `activo=true` y excluyendo los que ya estan en `chips`.

### Tab 3: Diccionarios y Enrutamiento (lineas 1382-1532)

#### Comportamiento actual

| Elemento | Carga de BD | Guarda en BD | Notas |
|---|---|---|---|
| Tipos de Documento (14) | ✅ SI (carga via `cargarDiccionarios`) | ❌ NO | `saveTipo` (linea 590) es del mock. `deleteTipo` tambien. |
| Estados (8) | ✅ SI | ❌ NO | `saveEstado` (linea 622) es del mock. `deleteEstado` tambien. |
| Matriz ETO (10) | ✅ SI | ❌ NO | `guardarFilaMatriz` (linea 648) es del mock - solo pushLog. |
| Analistas ETO (dropdown) | ✅ SI (via `usuarios.list({rol:'ETO'})`) | - | Funciona OK. |
| CRUD tipos (nuevo/editar/eliminar) | ❌ NO | ❌ NO | `addTipo`, `saveTipo`, `deleteTipo` son del mock. |
| CRUD estados | ❌ NO | ❌ NO | Mismo problema. |
| CRUD matriz ETO | ❌ NO | ❌ NO | Mismo problema. |

### Tab 4: Gerencias y Areas (lineas 1534-1633)

#### Comportamiento actual

| Elemento | Carga de BD | Guarda en BD | Notas |
|---|---|---|---|
| Lista gerencias (14) | ✅ SI (via `cargarGerencias`) | ❌ NO | `saveGer` (linea 676) es del mock. `addGerencia` crea `{id: Date.now()}` random. |
| Detalle gerencia | ✅ SI | ❌ NO | Mismo problema. |
| Lista areas | ✅ SI | ❌ NO | `saveArea` (linea 706) es del mock. |
| CRUD gerencia | ❌ NO | ❌ NO | `addGerencia`, `saveGer`, `deleteGer` son del mock. |
| CRUD area | ❌ NO | ❌ NO | Mismo problema. |
| Mover area entre gerencias | ❌ NO | ❌ NO | `abrirMoverArea` no llama `areas.mover`. |

### Tab 5: Plantillas de Notificacion (lineas 1635-1694)

#### Comportamiento actual

| Elemento | Carga de BD | Guarda en BD | Notas |
|---|---|---|---|
| Lista plantillas (6) | ✅ SI (via `cargarNotificaciones`) | - | Funciona OK. |
| Asunto del correo | ✅ SI (editable) | ❌ NO | `guardarPlantilla` (linea 758) es del mock - solo pushLog + toast. |
| Cuerpo del correo | ✅ SI (en `<textarea>`) | ❌ NO | Mismo problema. |
| Etiquetas (variables) | ✅ SI (de `variables_json` de la BD) | - | Funciona OK. |
| Previsualizar | ✅ SI (llama `/preview`) | - | Funciona OK. |

#### Bug adicional: Editor de HTML crudo

**Linea 1685:**
```html
<textarea class="form-input text-xs font-mono leading-relaxed" rows="10"
          x-model="plantillas[plantillaSelect].cuerpo" x-ref="editorBody"
          placeholder="(Plantilla en configuracion - haga clic en Previsualizar)">
</textarea>
```

El usuario ve HTML puro (`<div style="font-family: Arial...">`) en vez de un editor visual. Necesita un editor amigable (dual mode, Quill, etc.).

### Tab 6: Gestion de Usuarios

✅ Validado en sesion 9. Todo funciona. Sin cambios.

### Tab 7: Logs de Auditoria (lineas 2099-2150)

#### Comportamiento actual

| Elemento | Estado | Notas |
|---|---|---|
| Filtros (search, tab, accion, recurso) | ✅ OK | Funcionan con BD. |
| Carga desde BD | ✅ OK | `GET /audit-log?limit=200&offset=0`. |
| Paginacion 10 por pagina | ❌ MAL | `logLimit: 200`. El usuario pidio 10. |
| HTML columnas (fecha, tab, parametro, anterior, nuevo, usuario) | ❌ MAL | Mismatch con shape del backend. |
| Formato fecha (Bolivia UTC-4) | ❌ MAL | Viene UTC (`2026-06-16T17:56:33.513146Z`). |
| Exportar a Excel | ❌ MAL | Solo CSV client-side desde `this.logs`. |

#### Bug especifico - Mismatch de campos HTML vs Backend

**Template HTML (lineas 2120-2140):**
```html
<td class="text-slate-500" x-text="h.fecha"></td>
<td><span class="badge badge-gray text-[10px]" x-text="h.tab || '—'"></span></td>
<td class="font-semibold text-slate-800" x-text="h.parametro"></td>
<td class="text-red-600 font-mono text-[11px]" x-text="h.anterior"></td>
<td class="text-emerald-600 font-mono font-bold text-[11px]" x-text="h.nuevo"></td>
<td class="text-brand-600 font-mono text-[11px]" x-text="h.usuario"></td>
```

**Shape del backend (de `GET /audit-log`):**
```json
{
  "id": 46,
  "usuario_id": 17,
  "usuario_username": "admin_local",
  "usuario_nombre": "Carlos Mendoza",
  "accion": "OVERRIDE",
  "recurso": "usuario",
  "recurso_id": 9,
  "descripcion": "Override administrativo sobre ychavez (campos: [])",
  "detalles": {"antes": {...}, "despues": {...}, "campos": [], "observaciones": null},
  "ip": "172.20.0.1",
  "exitoso": true,
  "error_msg": null,
  "created_at": "2026-06-16T17:56:33.513146Z"
}
```

**Solucion - mapping en `cargarLogs()` (linea 89):**
```js
this.logs = data.items.map(l => ({
  id: l.id,
  fecha: new Date(l.created_at).toLocaleString('es-BO', {
    timeZone: 'America/La_Paz',
    dateStyle: 'short',
    timeStyle: 'medium',
  }),
  tab: this._tabFromRecurso(l.recurso),
  parametro: `${l.accion} ${l.recurso}${l.recurso_id ? ' #' + l.recurso_id : ''}`,
  anterior: l.detalles?.antes ? JSON.stringify(l.detalles.antes) : '-',
  nuevo: l.detalles?.despues ? JSON.stringify(l.detalles.despues) : '-',
  // Campos crudos del backend por si se necesitan
  accion: l.accion,
  recurso: l.recurso,
  descripcion: l.descripcion,
  usuario_username: l.usuario_username,
}))
```

---

## Plan de correcciones

### Fase 1 (CRITICA, 2-3h) - Restaurar CRUD

**Objetivo:** Que todos los handlers `save/delete/add` persistan en la BD.

1. **Eliminar mocks duplicados** (lineas 537-744)
   - Mantener solo la primera declaracion (la que SI carga de BD)
   - Las funciones de la primera declaracion (saveTipo, saveEstado, saveGer, saveArea, etc.) SI llaman al backend
   - Eliminar imports de `parametrosSistema.js`

2. **Crear claves faltantes en BD** para Restricciones:
   ```sql
   INSERT INTO configuracion_global (clave, valor, categoria, descripcion) VALUES
     ('max_archivos_por_solicitud', '20', 'ARCHIVOS', 'Limite de archivos adjuntos por solicitud'),
     ('max_tamano_archivo_mb', '20', 'ARCHIVOS', 'Tamano maximo por archivo en MB'),
     ('max_descargas_editables_dia', '10', 'DESCARGAS', 'Max descargas de editable por dia/usuario'),
     ('paginacion_mi_bandeja', '10', 'DESCARGAS', 'Paginacion por defecto en Mi Bandeja'),
     ('tipos_excluidos_limite_descarga', '[]', 'DESCARGAS', 'Tipos excluidos del limite de descarga (JSON)');
   ```

3. **Validar end-to-end** en navegador con `docker restart sgd-frontend` (cache de Vite).

### Fase 2 (ALTA, 1-2h) - Logs de Auditoria

4. **Cambiar `logLimit: 200` a `logLimit: 10`** y agregar paginacion en HTML
5. **Mapear campos del backend al HTML** (snippet en seccion anterior)
6. **Convertir fecha UTC a Bolivia** con `timeZone: 'America/La_Paz'`

### Fase 3 (MEDIA, 2-3h) - Editor de Plantillas

7. **Implementar dual mode** (Editor de variables + Vista previa HTML)
   - Toggle entre "Texto plano" y "HTML Preview"
   - En modo "Texto plano": textarea + insertar variables
   - En modo "HTML Preview": readonly con `x-html="$sanitize(cuerpo)"`
   - El backend SI soporta `cuerpo_html` (es la BD), no se cambia el schema

### Fase 4 (BAJA, 30min) - Dropdown de tipos excluidos

8. **Cargar tipos de documento disponibles** y mostrarlos en el dropdown
   - Agregar `tiposExcluibles: []` al state (en la primera declaracion, no en el mock)
   - Cargar via `tiposDocumento.list()` en `cargarRestricciones()`
   - Filtrar los que ya estan en `chips` para no duplicar
   - Reemplazar `<template x-for="t in chips">` por `<template x-for="t in tiposExcluibles">`

### Fase 5 (OPCIONAL, 30min) - Bug "Indefinido" en Vigencia

9. **Mostrar badge en vez de input** cuando `indefinido=true`:
   ```html
   <span x-show="v.años === 'Indefinido'" class="badge badge-gray text-[10px]">Indefinido</span>
   <input x-show="v.años !== 'Indefinido'" type="number" x-model.number="v.años" ...>
   ```
   Ademas, **agregar soporte de PATCH** en el backend para que el cambio se persista.

### Estimacion total

| Fase | Horas |
|---|---|
| Fase 1 (mocks + CRUD) | 2-3h |
| Fase 2 (logs) | 1-2h |
| Fase 3 (editor plantillas) | 2-3h |
| Fase 4 (dropdown chips) | 30min |
| Fase 5 (badge Indefinido) | 30min |
| **TOTAL** | **6.5-9h** |

---

## Skills a invocar

Para esta sesion futura:
- `git-workflow` (obligatorio antes de cada commit)
- `codebase-onboarding` (al inicio, para confirmar estructura)
- `python-reviewer` (si hay cambios en backend)
- `verification-loop` (validar end-to-end con curl/Chrome DevTools)
- `frontend-design-direction` (para Fase 3 - editor plantillas)
- `frontend-a11y` (para Fase 2 - paginacion accesible)
- `error-handling` (si hay bugs raros)

---

## Convenciones a respetar

- **Commits atomicos:** 1 feature = 1 commit. NO mega-commits.
- **Conventional Commits:** `feat(frontend):`, `fix(frontend):`, `docs(pr):`, `chore(repo):`
- **Sin secretos:** Scan con `grep` antes de commitear
- **Archivos correctos:** NO `.env`, NO logs, NO `test_*.py` en raiz
- **Branch correcta:** `epica-1/rama-1` (NO `main`)
- **Idioma:** Comentarios en espanol, codigo en ingles
- **Estilo Python:** PEP 8 + Black, type hints, docstrings Google
- **Estilo Frontend:** ES modules, Alpine.js, paleta pastel COFAR (#1a5fb4 brand-500)

---

## Validacion final al cerrar

1. Login con admin, ir a cada tab, verificar que muestra datos de BD
2. **Crear un tipo de documento nuevo** desde la UI, verificar que aparece en la BD via psql
3. **Editar un tipo de documento** desde la UI, verificar que el cambio persiste via psql
4. **Eliminar un tipo de documento** desde la UI, verificar que tiene `activo=false` en la BD
5. **Cambiar plazo de revision** desde la UI, verificar que persiste
6. Revisar log de auditoria, verificar formato de fecha Bolivia
7. Exportar a CSV/Excel, verificar que las celdas tienen datos

---

## Archivos a tocar

| Archivo | Accion |
|---|---|
| `frontend/src/pages/Parametrizacion.js` | Eliminar lineas 537-744 (seccion mock duplicada). Quitar imports de `parametrosSistema.js`. Mapear campos en `cargarLogs()`. Cambiar `logLimit` a 10. Paginacion de logs. Toggle de editor plantillas. |
| `frontend/src/data/parametrosSistema.js` | **NO eliminar todavia** - primero verificar que nada mas lo usa. Posiblemente eliminar exports no usados. |
| `backend/scripts/seed_*.py` o nuevo `seed_configuracion_global.py` | Crear script para insertar claves de Restricciones faltantes. |
| `docs/PR/ESTADO.md` | Actualizar progreso si se cierran bugs. |
| `docs/PR/BITACORA.md` | Agregar entrada de sesion. |
