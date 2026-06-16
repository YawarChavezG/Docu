# PENDIENTES R1 - Pantalla de Parametrización

> **Estado:** Documento de trabajo. NO requiere accion inmediata.
> **Origen:** Analisis exhaustivo de la pantalla de Parametrizacion vs BD, realizado el 2026-06-16 al cierre de sesion 9.
> **Proposito:** Servir como guia tecnica para una sesion futura que cierre los bugs identificados antes de la presentacion de R1 al cliente.
> **Bloqueante para:** R1 - Cierre al 100% (actualmente 35/35 = 100% declarado, pero varios tabs usan MOCKS en vez de BD).

---

## Resumen ejecutivo

La pantalla de Parametrizacion (`frontend/src/pages/Parametrizacion.js`, 2153 lineas) tiene **dos declaraciones duplicadas** de las mismas propiedades, donde la **SEGUNDA declaracion usa datos del MOCK `ParametrosGlobalesDB`** (de `frontend/src/data/parametrosSistema.js`) y **sobreescribe** la primera que SI cargaba de la BD via `parametrizacionApi.js`.

Esto significa que **varios tabs no estan leyendo de la BD** aunque el backend este 100% funcional y conectado. Los handlers `guardar*` solo actualizan el mock y muestran un toast - **NO persisten en la BD**.

### Inventario de imports del mock

```js
// frontend/src/pages/Parametrizacion.js (lineas 31-42)
import {
  ParametrosGlobalesDB,       // <- mock de configuracion_global
  exclusionTiposDB,            // <- mock de tipos excluidos (chips)
  tiposExcluiblesDB,           // NO usado actualmente
  analistasETODB,             // <- mock de analistas ETO
  estadosProcesoParamDB,      // <- mock de estados
  etiquetasPlantillaDB,       // <- mock de etiquetas
  gerenciasParamDB,            // <- mock de gerencias
  matrizETOParamDB,            // <- mock de matriz ETO
  plantillasNotificacionParamDB,  // <- mock de plantillas
  tiposDocParamDB,             // <- mock de tipos de documento
} from '../data/parametrosSistema.js'
```

### Rango del codigo a eliminar (seccion de mocks duplicados)

```
Archivo: frontend/src/pages/Parametrizacion.js
Lineas:  537 - 744
Tamano:  ~208 lineas
```

Contiene:
- Segunda declaracion de `guardarTiempos`, `guardarSemaforizacion`
- Segunda declaracion de `restricciones`, `chips`, `quitarChip`, `agregarChip`, `guardarRestricciones`, `guardarLimitesDescarga`
- Segunda declaracion de `tiposDocs`, `addTipo`, `saveTipo`, `cancelTipo`, `deleteTipo`
- Segunda declaracion de `estados`, `addEstado`, `saveEstado`, `cancelEstado`, `deleteEstado`
- Segunda declaracion de `matrizETO`, `analistas`, `guardarFilaMatriz`
- Segunda declaracion de `gerencias`, `gerSelId`, `gerEditMode`, `gerSel`, `addGerencia`, `startEditGer`, `saveGer`, `deleteGer`, `addArea`, `saveArea`, `deleteArea`, `abrirMoverArea`
- Segunda declaracion de `plantillaSelect`, `plantillas`, `etiquetas`, `previewMode`, `previewHtml`, `insertarEtiqueta`, `guardarPlantilla`, `previsualizarPlantilla`, `cerrarPreview`

**IMPORTANTE:** Solo el bloque de la segunda declaracion debe eliminarse, NO la primera (que SI funciona y carga de BD). La primera declaracion es la "buena" y debe quedarse.

---

## Inventario de tabs y estado

### Tab 1: Tiempos y SLAs (lineas 1252-1317)

#### BD - `configuracion_global` (8 filas)

| clave | valor | categoria |
|---|---|---|
| `espera_auto_delegacion_dias` | 3 | VIGENCIA |
| `plazo_control_lectura_dias` | 30 | VIGENCIA |
| `tiempo_vigencia_anios` | 3 | VIGENCIA |
| `plazo_revision_aprobacion_dias` | 25 | FLUJO |
| `t_26664`, `t_6487`, `test_91726`, `test_clave_borrable` | 42, 42, 42, 99 | GENERAL (basura de testing) |

#### Comportamiento actual

| Elemento | Carga de BD | Guarda en BD | Notas |
|---|---|---|---|
| Vigencia por tipo de documento | SI (parcial) | NO | Lee `tipos_documento.periodo_vigencia`. PERO input muestra `"Indefinido"` cuando `indefinido=true` y no permite editar. 5/13 tipos son indefinidos. |
| Semaforo verde | SI | SI | `semaforo_verde_dias`. Funciona OK. |
| Semaforo amarillo | SI | SI | `semaforo_amarillo_dias`. Funciona OK. |
| Semaforo rojo | hardcoded | N/A | Texto fijo "Menos de 1 dia o vencido". No requiere dato en BD. |
| Plazo revision/aprobacion | SI | SI | `plazo_revision_aprobacion_dias`. Funciona OK. |
| Plazo control de lectura | SI | SI | `plazo_control_lectura_dias`. Funciona OK. |
| Boton "Guardar Vigencia y Flujo" | - | SI | Llama `configGlobal.bulkUpsert('VIGENCIA', ...)`. |
| Boton "Guardar Semaforizacion" | - | SI | Llama mismo handler (`guardarTiempos`). |

#### Bug especifico
- **Vigencia para tipos `indefinido=true`:** Los tipos `MANUAL_FUNCIONES`, `INSTRUCTIVO_TECNICO`, `PROTOCOLO`, `MANUAL_USUARIO` muestran "Indefinido" en el input, pero el input no permite editar. El usuario no puede asignarles años concretos.

---

### Tab 2: Restricciones (lineas 1319-1380) - BLOQUEANTE

#### BD - claves faltantes

El frontend busca estas claves en `configuracion_global`:
- `max_archivos_por_solicitud` (esperado, NO EXISTE en BD)
- `max_tamano_archivo_mb` (esperado, NO EXISTE en BD)
- `max_descargas_editables_dia` (esperado, NO EXISTE en BD)
- `paginacion_mi_bandeja` (esperado, NO EXISTE en BD)
- `tipos_excluidos_limite_descarga` (esperado, NO EXISTE en BD)

#### Comportamiento actual

| Elemento | Carga de BD | Guarda en BD | Notas |
|---|---|---|---|
| Limite archivos adjuntos (20) | NO | NO | HARDCODED en `restricciones: { maxAdjuntos: 20 }` del mock. No usa `parseInt(cfg.max_archivos_por_solicitud \|\| '20', 10)`. |
| Tamano max MB (20) | NO | NO | Mismo problema. |
| Max descargas/dia (10) | NO | NO | Mismo problema. |
| Paginacion bandeja (10) | NO | NO | Mismo problema. |
| Tipos excluidos (chips) | NO | NO | Dropdown VACIO porque solo lista los chips actuales. Ver bug especifico. |
| Boton "Guardar Restricciones" | - | NO | Solo actualiza mock. NO persiste. |
| Boton "Guardar Limites de Descarga" | - | NO | Solo actualiza mock. NO persiste. |

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

**Problema:** El dropdown solo lista `chips` (los tipos YA excluidos), NO los tipos de documento disponibles. El usuario no puede AGREGAR un nuevo tipo excluido.

**Solucion:** Reemplazar el `<template x-for="t in chips">` por `<template x-for="t in tiposExcluibles">` donde `tiposExcluibles` se llena con `tiposDocumento.list()` filtrado por `activo=true`.

---

### Tab 3: Diccionarios y Enrutamiento (lineas 1382-1532) - BLOQUEANTE

#### BD - `tipos_documento` (15 filas)

13 tipos del Excel + 2 de prueba (`TEST_NUEVO` inactivo, `TT_26664` activo). Campos: `codigo`, `nombre`, `codigo_doc` (1-14), `periodo_vigencia`, `indefinido`, `max_descargas_dia`, `activo`.

#### BD - `estados` (8 filas)

5 estados del flujo + 3 de prueba (2 activos, 1 inactivo). Campos: `codigo`, `nombre`, `contexto` (TAREA/PROCESO/AMBOS), `orden`, `activo`.

#### BD - `matriz_enrutamiento_eto` (10 filas)

1 fila por gerencia con `analista_usuario_id`, `gerencia_id`, `disponibilidad` (DISPONIBLE/AUSENTE).

#### Comportamiento actual

| Elemento | Carga de BD | Guarda en BD | Notas |
|---|---|---|---|
| Tipos de Documento (15) | NO | NO | Segunda declaracion usa `JSON.parse(JSON.stringify(tiposDocParamDB))` (mock). |
| Estados (8) | NO | NO | Misma logica con `estadosProcesoParamDB` (mock). |
| Matriz ETO (10) | NO | NO | Misma logica con `matrizETOParamDB` (mock). |
| Analistas ETO (dropdown) | NO | NO | Usa `[...analistasETODB]` del mock. La primera declaracion SII carga de BD via `usuarios.list({ rol: 'ETO' })` pero es pisada. |
| CRUD tipos (nuevo/editar/eliminar) | NO | NO | `saveTipo` solo hace `pushLog` local. No llama `tiposDocumento.create/update/remove`. |
| CRUD estados | NO | NO | Mismo problema. |
| CRUD matriz ETO (cambiar analista/disponibilidad) | NO | NO | `guardarFilaMatriz` solo hace `pushLog` local. No llama `matrizEto.update`. |

---

### Tab 4: Gerencias y Areas (lineas 1534-1633) - BLOQUEANTE

#### BD - `gerencias` (14 filas)

10 gerencias semilla + 2 de prueba (`PROM29402`, `CC-S1`) + 1 editada (`X1` -> `GERENCIA TEST EDIT`) + 1 con borrado logico (`AUDIT_TEST`).

#### BD - `areas` (56 filas)

49 areas semilla + 7 de prueba/borrado. Cada area tiene `gerencia_id` FK.

#### Comportamiento actual

| Elemento | Carga de BD | Guarda en BD | Notas |
|---|---|---|---|
| Lista gerencias (14) | NO | NO | Usa `JSON.parse(JSON.stringify(gerenciasParamDB))` (mock). |
| Detalle gerencia | NO | NO | Misma logica. |
| Lista areas de una gerencia | NO | NO | Misma logica. |
| CRUD gerencia (nuevo/editar/eliminar) | NO | NO | `addGerencia` crea `{id: Date.now()}` random. No llama `gerencias.create/update/remove`. |
| CRUD area | NO | NO | Misma logica. |
| Mover area entre gerencias | NO | NO | `abrirMoverArea` usa `gerencias` del mock, no del backend. No llama `areas.mover`. |

---

### Tab 5: Plantillas de Notificacion (lineas 1635-1694) - BLOQUEANTE

#### BD - `email_templates` (6 filas)

6 plantillas con `codigo`, `nombre`, `asunto`, `cuerpo_html` (HTML con `{{VARIABLE}}`), `variables_json` (lista de variables).

| codigo | nombre | variables_json |
|---|---|---|
| NUEVA_TAREA | Nueva Tarea Asignada | (TEST) |
| ALERTA_VENCIMIENTO | Alerta de Vencimiento | `["{{CODIGO}}", "{{TITULO}}", "{{USUARIO}}", ...]` |
| DOCUMENTO_APROBADO | Documento Aprobado | idem |
| DOCUMENTO_OBSERVADO | Documento Observado | idem |
| EVALUACION_PENDIENTE | Evaluacion Pendiente (editado) | idem |
| AUTO_DELEGACION_ACTIVADA | Auto-delegacion Activada | idem |

#### Comportamiento actual

| Elemento | Carga de BD | Guarda en BD | Notas |
|---|---|---|---|
| Lista plantillas (6) | SI | - | Funciona OK. |
| Asunto del correo | SI | SI (parcial) | Editable. La primera declaracion `guardarPlantilla` SI llama `emailTemplates.update()`. PERO es pisada por la segunda. |
| Cuerpo del correo | SI | NO | Muestra HTML crudo en `<textarea>`. **No es amigable para usuario normal.** |
| Etiquetas (variables) | SI | - | Se muestran como chips clicables. |
| Previsualizar | SI | - | Llama `emailTemplates.preview()` con mock de variables. OK. |
| Boton "Guardar Plantilla" | - | NO | Segunda declaracion hace `pushLog` + toast, no PATCH. |

#### Bug critico: Editor de HTML crudo

**Linea 1685:**
```html
<textarea class="form-input text-xs font-mono leading-relaxed" rows="10"
          x-model="plantillas[plantillaSelect].cuerpo" x-ref="editorBody"
          placeholder="(Plantilla en configuracion - haga clic en Previsualizar)">
</textarea>
```

El usuario ve HTML puro (`<div style="font-family: Arial...">`) en vez de un editor visual. La imagen que me compartiste muestra exactamente este problema.

**Opciones de solucion (de menor a mayor esfuerzo):**

1. **Editor dual mode** (1-2h): Toggle entre "Editor de variables" (textarea simple con texto plano + insertar variables con clic) y "Vista previa HTML" (readonly con `x-html="$sanitize(cuerpo)"`).
2. **Editor de texto plano** (30 min): Reemplazar `<textarea>` por uno con `cuerpo` en texto plano (sin HTML), interpretando saltos de linea como `<br>`. Mas simple pero pierde el estilo HTML.
3. **RichText editor (Quill/TinyMCE)** (3-4h): Integrar un editor visual que produzca HTML. Mas bonito pero requiere libreria externa.
4. **Markdown editor** (2-3h): Editor de markdown con preview en tiempo real. Al guardar, convertir markdown a HTML.

**Recomendacion:** Opcion 1 (dual mode) por balance entre esfuerzo y resultado.

---

### Tab 6: Gestion de Usuarios (lineas 1696-2000) - **OK 100%**

Validado en sesion 9. Todo funciona. Sin cambios.

---

### Tab 7: Logs de Auditoria (lineas 2099-2150) - BLOQUEANTE

#### BD - `audit_log` (46 filas)

Tabla append-only con: `id`, `usuario_id`, `usuario_username`, `usuario_nombre`, `accion`, `recurso`, `recurso_id`, `descripcion`, `detalles` (JSONB), `ip`, `exitoso`, `error_msg`, `created_at` (UTC timestamp).

#### Comportamiento actual

| Elemento | Estado | Notas |
|---|---|---|
| Filtros (search, tab, accion, recurso) | OK | Funcionan con BD. |
| Carga desde BD | OK | `GET /audit-log?limit=200&offset=0`. |
| Total | OK | Mostrado correctamente. |
| Paginacion 10 por pagina | **MAL** | `logLimit: 200`. El usuario pidio 10. |
| HTML columnas (fecha, tab, parametro, anterior, nuevo, usuario) | **MAL** | Mismatch con shape del backend. Ver bug especifico. |
| Formato fecha (Bolivia UTC-4) | **MAL** | Viene UTC (`2026-06-16T17:56:33.513146Z`). |
| Exportar a Excel | **MAL** | Solo CSV client-side. |

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
  "detalles": {
    "antes": {...},
    "despues": {...},
    "campos": [],
    "observaciones": null
  },
  "ip": "172.20.0.1",
  "exitoso": true,
  "error_msg": null,
  "created_at": "2026-06-16T17:56:33.513146Z"
}
```

**Campos HTML no existen en el backend:** `h.fecha`, `h.tab`, `h.parametro`, `h.anterior`, `h.nuevo`. El HTML muestra vacios o `undefined`.

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

Y el `logsFiltrados` (linea 71) ya busca por `descripcion`, `usuario_username`, `recurso`, `accion` - **funciona correctamente** con el shape del backend.

---

## Plan de correcciones

### Fase 1 (CRITICA, 2-3h) - Quitar mocks + restaurar CRUD

**Objetivo:** Que todos los tabs lean de BD y todos los handlers persistan cambios.

1. **Eliminar mocks duplicados** (lineas 537-744)
   - Mantener solo la primera declaracion (la que SI carga de BD)
   - Verificar que la primera declaracion SI tiene todas las funciones necesarias
   - Eliminar imports de `parametrosSistema.js`

2. **Validar primera declaracion** de cada propiedad
   - `restricciones` linea 182: OK (carga de BD, guarda con PATCH)
   - `chips` linea 183: OK
   - `tiempos` linea 133: OK
   - `vigencias` linea 134: OK
   - `tiposDocs` linea 235: OK
   - `estados` linea 237: OK
   - `matrizETO` linea 239: OK
   - `analistas` linea 240: OK
   - `gerencias` linea 270 (buscar): OK
   - `plantillas` linea 480: OK

3. **Crear claves faltantes en BD** para Restricciones:
   ```sql
   INSERT INTO configuracion_global (clave, valor, categoria, descripcion) VALUES
     ('max_archivos_por_solicitud', '20', 'ARCHIVOS', 'Limite de archivos adjuntos por solicitud'),
     ('max_tamano_archivo_mb', '20', 'ARCHIVOS', 'Tamano maximo por archivo en MB'),
     ('max_descargas_editables_dia', '10', 'DESCARGAS', 'Max descargas de editable por dia/usuario'),
     ('paginacion_mi_bandeja', '10', 'DESCARGAS', 'Paginacion por defecto en Mi Bandeja'),
     ('tipos_excluidos_limite_descarga', '[]', 'DESCARGAS', 'Tipos excluidos del limite de descarga (JSON)');
   ```

4. **Validar end-to-end** en navegador con `docker restart sgd-frontend` (cache de Vite).

### Fase 2 (ALTA, 1-2h) - Logs de Auditoria

5. **Cambiar `logLimit: 200` a `logLimit: 10`** y agregar paginacion en HTML
6. **Mapear campos del backend al HTML** (snippet en seccion anterior)
7. **Convertir fecha UTC a Bolivia** con `timeZone: 'America/La_Paz'`

### Fase 3 (MEDIA, 2-3h) - Editor de Plantillas

8. **Implementar dual mode** (Editor de variables + Vista previa HTML)
   - Toggle entre "Texto plano" y "HTML Preview"
   - En modo "Texto plano": textarea + insertar variables
   - En modo "HTML Preview": readonly con `x-html="$sanitize(cuerpo)"`
   - El backend SI soporta `cuerpo_html` (es la BD), no se cambia el schema

9. **Validar end-to-end**: editar plantilla, guardar, previsualizar

### Fase 4 (BAJA, 30min) - Dropdown de tipos excluidos

10. **Cargar tipos de documento disponibles** y mostrarlos en el dropdown
    - Agregar `tiposExcluibles: []` al state
    - Cargar via `tiposDocumento.list()` en `cargarRestricciones()`
    - Filtrar los que ya estan en `chips` para no duplicar
    - Reemplazar `<template x-for="t in chips">` por `<template x-for="t in tiposExcluibles">`

### Fase 5 (OPCIONAL, 30min) - Bug "Indefinido" en Vigencia

11. **Mostrar badge en vez de input** cuando `indefinido=true`:
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
2. Crear un tipo de documento nuevo, verificar que aparece en el siguiente reload
3. Cambiar plazo de revision, verificar que persiste despues de F5
4. Marcar un usuario como ausente, verificar que aparece en la columna Delegado
5. Revisar log de auditoria, verificar formato de fecha Bolivia
6. Exportar a CSV/Excel, verificar que las celdas tienen datos

---

## Archivos a tocar

| Archivo | Accion |
|---|---|
| `frontend/src/pages/Parametrizacion.js` | Eliminar lineas 537-744 (seccion mock duplicada). Quitar imports de `parametrosSistema.js`. Mapear campos en `cargarLogs()`. Cambiar `logLimit` a 10. Paginacion de logs. Toggle de editor plantillas. |
| `frontend/src/data/parametrosSistema.js` | **NO eliminar todavia** - primero verificar que nada mas lo usa. Posiblemente eliminar exports no usados. |
| `backend/scripts/seed_*.py` o nuevo `seed_configuracion_global.py` | Crear script para insertar claves de Restricciones faltantes. |
| `docs/PR/ESTADO.md` | Actualizar progreso si se cierran bugs. |
| `docs/PR/BITACORA.md` | Agregar entrada de sesion. |
