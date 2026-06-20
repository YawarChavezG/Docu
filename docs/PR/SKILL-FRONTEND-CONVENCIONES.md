# SKILL: Frontend Conventions — COFAR SGD

> **Convenciones de diseño, UI/UX y código para el frontend Alpine.js + Tailwind.**
> **Propósito:** Cualquier IA que genere/edite código frontend debe seguir estas reglas para mantener consistencia visual y de código.

---

## 1. Diseño System (main.css)

### 1.1 Colores
- **Brand (azul corporativo):** `#1a5fb4` (brand-500)
- **Success:** `#166534` (green-800)
- **Warning:** `#92400e` (amber-800)
- **Error:** `#dc2626` (red-600)
- **Gray scale:** `#1e293b` (slate-800), `#64748b` (slate-500), `#94a3b8` (slate-400), `#e2e8f0` (slate-200), `#f8fafc` (slate-50)

### 1.2 Badges (7 colores predefinidos)
```html
<span class="badge-green">Activo</span>
<span class="badge-amber">Pendiente</span>
<span class="badge-blue">Revisión</span>
<span class="badge-red">Vencido</span>
<span class="badge-gray">Inactivo</span>
<span class="badge-purple">Contexto ACCION</span>
<span class="badge-teal">Contexto AMBOS</span>
```

### 1.3 Botones
```html
<button class="btn btn-primary">Guardar</button>
<button class="btn btn-danger">Eliminar</button>
<button class="btn btn-ghost">Cancelar</button>
<button class="btn btn-sm">Pequeño</button>
```
- `btn` base: padding 8px 16px, border-radius 8px, font-size 13px
- `btn-primary`: bg brand-500, text white
- `btn-danger`: bg red-600, text white
- `btn-ghost`: transparent, text slate-600, hover: bg slate-100

### 1.4 Data tables
```html
<table class="data-table">
  <thead><tr><th class="th-filter">Columna</th></tr></thead>
  <tbody><tr><td>Valor</td></tr></tbody>
</table>
```
- `data-table`: border-collapse, width 100%, font-size 12px
- `th`: bg slate-50, text slate-600, font-weight 600, padding 10px 12px
- `td`: padding 10px 12px, border-bottom 1px solid #f1f5f9
- Hover row: bg slate-50

### 1.5 KPI Cards
```html
<div class="kpi-card">
  <span class="kpi-value">150</span>
  <span class="kpi-label">Usuarios activos</span>
</div>
<div class="kpi-card-amber">...</div>
<div class="kpi-card-red">...</div>
```
- `kpi-value`: font-size 28px, font-weight 700
- `kpi-label`: font-size 11px, color slate-500

### 1.6 Form inputs
```html
<input class="form-input" type="text" placeholder="Buscar...">
<label class="form-label">Nombre</label>
<span class="form-hint">Mínimo 3 caracteres</span>
<span class="form-error-msg">Campo requerido</span>
```

### 1.7 Section cards
```html
<div class="section-card">
  <div class="section-header">
    <h2>Título de sección</h2>
  </div>
  <!-- contenido -->
</div>
```

### 1.8 Modal system
```html
<div class="modal-overlay" x-show="abierto" x-cloak>
  <div class="modal-box" @click.outside="abierto=false">
    <!-- contenido -->
  </div>
</div>
```
- Z-index: modales normales 8000, modales de confirmación 8600
- ModalBase.js: 49 líneas, overlay backdrop-blur, animación scale-in

### 1.9 Glassmorphism
```html
<div class="glass-card">contenido</div>
```
- `glass`: backdrop-filter blur(12px), bg white/70%
- `glass-card`: + border-radius 16px, border 1px solid white/20%
- `glass-dark`: backdrop-filter blur(16px), bg slate-900/80%

---

## 2. Patrón de componentes Alpine

### 2.1 Estructura de página
```js
export const page = {
  init() {
    window.Alpine?.data('nombrePagina', () => ({
      state1: '',
      state2: [],

      async init() {
        await this.cargarDatos()
      },

      async cargarDatos() {
        // usar apiFetch de utils/api.js
      },

      get computedProp() {
        // computed properties
      },
    }))
  },
  template: /* html */`
    <div x-data="nombrePagina" style="animation:fadeIn 0.35s ease-out both">
      ...
    </div>`
}
```

### 2.2 Cargar datos del backend
```js
// MAL ❌
const res = await fetch('/api/v1/...')
const data = await res.json()

// BIEN ✅
import { apiGet } from '../utils/api.js'
const res = await apiGet('/endpoint')
if (res.ok) { this.data = res.data }
```

### 2.3 NUNCA usar fetch() directo en páginas
Siempre usar los atajos de `utils/api.js`:
- `apiGet(path, params?)`
- `apiPost(path, body?)`
- `apiPatch(path, body?)`
- `apiDelete(path)`

### 2.4 Loading state
Siempre incluir:
- `loading: true` al inicio
- `loading = false` al finalizar
- Spinner visible con `x-show="loading"`
- Mensaje de error con `errorMsg` y `window.toast?.(msg, 'error')`

### 2.5 Toast system
```js
window.toast?.('✅ Operación exitosa', 'success')
window.toast?.('❌ Error', 'error')
window.toast?.('⚠️ Advertencia', 'warn')
window.toast?.('ℹ️ Info', 'info')
```

---

## 3. Convenciones de código

### 3.1 Nombres
- Variables/estados: `camelCase` (`filterTipo`, `loading`, `plantillas`)
- Funciones: `camelCase` (`cargar()`, `descargar(p)`)
- Constantes: `UPPER_SNAKE` (`TIPO_META`)
- Componentes Alpine: PascalCase en nombre data (`plantillasPage`)

### 3.2 Sin comentarios en código
El código debe ser auto-explicativo. NO agregar comentarios.

### 3.3 Imports
Siempre al inicio del archivo, con ruta relativa desde `src/`:
```js
import { plantillas } from '../services/plantillasApi.js'
```

### 3.4 Template strings
- Usar backticks `` ` `` para HTML multilinea
- Dentro de template strings, NO usar backticks ni en comentarios ni en strings embebidos
- Usar `class=` en vez de `className=`

### 3.5 Alpine directives order (consistente)
```html
<div x-data x-show x-if x-for x-model x-text x-html :style @click></div>
```

---

## 4. Layout y navegación

### 4.1 AppLayout.js (único layout)
- Se monta una vez, persiste entre navegaciones
- El router reemplaza solo `#page-content`
- Sidebar con 4 configuraciones según rol: admin, eto, user, visualizador
- Banner de impersonación sticky (visible solo cuando hay impersonate activo)

### 4.2 Estructura de sidebar
```
MI ESPACIO → Mi Bandeja
DOCUMENTACIÓN → Lista Maestra, Consultar Documentos
CONSULTAS → Monitor de Copias, Monitor Eval., Reportes, Mis Evaluaciones
FLUJO DOCUMENTAL → Plantillas Documentales, Nueva Solicitud, Asistente IA
CONFIGURACIÓN → Parametrización General (solo admin/ETO)
```

### 4.3 Roles y acceso a páginas
| Rol | homeRoute | Puede ver |
|---|---|---|
| admin | `/parametrizacion` | Todo |
| eto | `/bandeja` | Casi todo excepto config avanzada |
| user | `/bandeja` | Bandeja, docs, plantillas, evaluaciones |
| visualizador | `/bandeja` | Solo consulta (sin crear/editar) |

---

## 5. Responsive design

### 5.1 Breakpoints estándar
| Alias | Min-width | Uso |
|---|---|---|
| `sm` | 640px | Tablets pequeñas |
| `md` | 768px | Tablets grandes |
| `lg` | 1024px | Desktop |
| `xl` | 1280px | Desktop grande |
| `2xl` | 1536px | Pantallas extra grandes |

### 5.2 Grid patterns
```html
<!-- Cards responsive: 1→2→3→4 columnas -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
```

```html
<!-- Form grid 2 columnas -->
<div class="form-grid-2">
  <!-- form-grid-2 = grid grid-cols-1 sm:grid-cols-2 gap-3 -->
```

### 5.3 NUNCA usar inline styles para layout
```html
<!-- MAL ❌ -->
<div style="display:grid;grid-template-columns:1fr;gap:14px" class="sm:grid-cols-2">

<!-- BIEN ✅ -->  
<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
```

---

## 6. Modales existentes y sus z-index

| Modal | Archivo | z-index |
|---|---|---|
| Modal base | `ModalBase.js` | 8000 |
| Edit User | `EditUserModal.js` | 8000 |
| Profile | `ProfileModal.js` | 8000 |
| Auth (firma) | `AuthModal.js` | 8500 |
| Confirm Delete | `ConfirmDeleteModal.js` | 8600 |
| Confirm Impersonate | `ConfirmImpersonateModal.js` | 8600 |
| Confirm Delegado | `ConfirmDelegadoModal.js` | 8600 |
| Auth Devolución | `AuthDevolucionModal.js` | 8500 |
| Auth Recepción | `AuthRecepcionModal.js` | 8500 |

**Regla:** Modales de confirmación SIEMPRE van a z-index 8600 (encima de modales de edición/formulario que van a 8000).

---

## 7. Tiptap Editor (plantillas de notificación)

- Editor WYSIWYG en `PlantillaEditor.js` (56 líneas)
- Extensiones: StarterKit, TextStyle, Color, Underline
- Toolbar con 17 botones con `@mousedown.prevent`
- Inserción de variables `{{CODIGO}}` mediante chip click
- El editor detecta `activeElement` para saber si inserta en asunto o cuerpo

---

## 8. Errores comunes a evitar (ver LEARNINGS-ERRORES.md)

- F01: Inline CSS vence a Tailwind classes
- F02: x-show sin display:none fallback
- F03: Backticks en comentarios HTML dentro de template strings
- F04: dispatchEvent NO funciona con Alpine + date/checkbox
- F06: confirm() nativo → usar modal
- F09: Shape de datos del template debe coincidir con backend
- F11: Promise.all con requests sin .catch()
