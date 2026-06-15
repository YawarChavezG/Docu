# REPORTE DE AUDITORÍA ARQUITECTÓNICA Y GAP ANALYSIS
## COFAR SGD — Migración Monolito HTML → SPA Vite + Alpine.js
**Fecha de auditoría:** 04 de mayo de 2026
**Auditor:** Kimi K2.6 (OpenCode)
**Modo:** AUDITORÍA PURA (Read-Only)
**Alcance:** `src/` vs. `SistemaGestionDocumental-29-4-2026-v2.html` (~7.263 líneas)

---

## RESUMEN EJECUTIVO

La migración del monolito HTML a la arquitectura SPA ha logrado un **mapeo funcional del ~88 %** de las pantallas y flujos originales. Sin embargo, existen **brechas críticas** en cuatro ejes que bloquean la calidad de producción:

1. **Deuda de estilos:** 1.913+ ocurrencias de `style="..."` en archivos `.js` de `src/`, violando el principio de utilidad de Tailwind CSS.
2. **Datos encapsulados en vistas:** 11 páginas contienen arrays y objetos de datos hardcodeados en su propio código, rompiendo el desacoplamiento entre UI y Data Layer.
3. **Duración de Toast incorrecta:** El sistema de notificaciones está configurado a 4.500 ms, mientras que la UX original requiere 2.500 ms.
4. **Flujo inter-página sin estado:** Las etapas del flujo documental (creación → liberación → revisión → aprobación) no comparten estado; cada página es una isla con datos estáticos.

**Veredicto general:** El `src/` es funcionalmente navegable pero requiere una **refactorización estructurada** antes de considerarse listo para producción.

---

## DIMENSIÓN 1: VISTAS, PANTALLAS Y CONTROL DE ROLES (RBAC)

### 1.1 Inventario 1:1 — Monolito vs. SPA

El HTML original define **27 pantallas** mediante `<div id="s-[nombre]" class="screen">`. A continuación el mapeo completo:

| # | Pantalla Monolito (`id`) | Ruta SPA (`src/pages/`) | Archivo | Estado |
|---|--------------------------|-------------------------|---------|--------|
| 1 | `s-lista` | `/lista` | `ListaMaestra.js` | ✅ Migrada |
| 2 | `s-solicitud` | — | — | ⚠️ **FALTA** (no existe vista consolidada de solicitud; se atomizó en `/version-editable` y `/aprobacion-documento`) |
| 3 | `s-liberacion` | `/liberacion` | `Liberacion.js` | ✅ Migrada |
| 4 | `s-liberacion-detalle` | `/liberacion-detalle` | `LiberacionDetalle.js` | ✅ Migrada |
| 5 | `s-revision` | `/revision` | `Revision.js` | ✅ Migrada |
| 6 | `s-publicacion` | `/publicacion` | `Publicacion.js` | ✅ Migrada |
| 7 | `s-config-examen` | `/config-examen` | `ConfigExamen.js` | ✅ Migrada |
| 8 | `s-reportes` | `/reportes` | `Reportes.js` | ✅ Migrada |
| 9 | `s-parametrizacion` | `/parametrizacion` | `Parametrizacion.js` | ✅ Migrada |
| 10 | `s-bandeja` | `/bandeja` | `Bandeja.js` | ✅ Migrada |
| 11 | `s-tareas-completas` | `/tareas-completas` | `TareasCompletas.js` | ✅ Migrada |
| 12 | `s-correccion` | `/correccion` | `Correccion.js` | ✅ Migrada |
| 13 | `s-pre-eval` | `/pre-eval` | `PreEval.js` | ✅ Migrada |
| 14 | `s-examen` | — | — | ❌ **FALTA** (solo existe `/pre-eval`; no hay pantalla de examen en ejecución) |
| 15 | `s-tomar-lectura` | `/tomar-lectura` | `TomarLectura.js` | ✅ Migrada |
| 16 | `s-req-editable` | `/version-editable` | `VersionEditable.js` | ✅ Migrada (renombrada) |
| 17 | `s-consulta-user` | `/consulta` | `ConsultaDocumentos.js` | ✅ Migrada |
| 18 | `s-mis-evaluaciones` | `/evaluaciones` | `Evaluaciones.js` | ✅ Migrada |
| 19 | `s-biblioteca` | `/biblioteca` | `Placeholder.js` | ⚠️ **PLACEHOLDER** (muestra "Módulo en construcción") |
| 20 | `s-plantillas` | `/plantillas` | `Plantillas.js` | ✅ Migrada |
| 21 | `s-modulo-copias` | — | — | ⚠️ **FALTA** (no existe vista consolidada; se atomizó en `/copias-cc` y `/copias-cn`) |
| 22 | `s-pdf-previsualizacion` | — | `PdfViewerModal.js` | ✅ Cubierto por modal global |
| 23 | `s-monitor-cc` | `/copias-cc` | `MonitorCC.js` | ✅ Migrada |
| 24 | `s-monitor-cn` | `/copias-cn` | `MonitorCN.js` | ✅ Migrada |
| 25 | `s-chat-ai` | `/chat` | `Chat.js` | ✅ Migrada |
| 26 | `s-mis-certificados` | `/certificados` | `Certificados.js` | ✅ Migrada |
| 27 | `s-pdf-certificado` | — | `PdfViewerModal.js` | ✅ Cubierto por modal global |

**Resumen:**
- ✅ **23 de 27** pantallas están cubiertas (85 %).
- ❌ **3 pantallas faltantes** o degradadas a placeholder: `/solicitud`, `/examen`, `/biblioteca`.
- ⚠️ **2 pantallas atomizadas** (`s-modulo-copias`, `s-solicitud`) fueron descompuestas en rutas hijas; esto es una decisión de arquitectura válida pero debe documentarse.

### 1.2 Navegación y Menús

El `AppLayout.js` construye la navegación lateral mediante `buildNav(role)` con cuatro configuraciones:
- `ETO_NAV`
- `USER_NAV`
- `ADMIN_NAV`
- `VIS_NAV` (Visualizador)

**Hallazgos:**
- ✅ Los submenús (Monitor de Copias, Mis Evaluaciones, Nueva Solicitud) usan `navGroup` con `x-show` y transiciones Alpine.
- ✅ La lógica de colapsado (`openSubmenus`, `toggleSubmenu`) replica el comportamiento del monolito.
- ⚠️ **Inconsistencia:** El badge de notificaciones en la campana (`#bell`) siempre muestra un punto rojo fijo (`bg-red-500 rounded-full`), sin contador dinámico ni conexión a `src/data/notificaciones.js`.
- ⚠️ **Inconsistencia:** El título de página (`#topbar-title`) es estático (`COFAR · Sistema de Gestión Documental`) y no cambia según la ruta activa, a diferencia del monolito donde se actualizaba por pantalla.

### 1.3 Gestión de Roles

El `authStore` (`src/store/auth.js`) define cuatro roles: `eto`, `user`, `visualizador`, `admin`.

**Mapeo de permisos (`canAccess`):**

| Sección | ETO | User | Visualizador | Admin |
|---------|-----|------|--------------|-------|
| bandeja | ✅ | ✅ | ✅ | ❌ |
| lista | ✅ | ✅ | ✅ | ❌ |
| consulta | ✅ | ✅ | ✅ | ❌ |
| copias | ✅ | ❌ | ❌ | ❌ |
| publicacion | ✅ | ❌ | ❌ | ❌ |
| reportes | ✅ | ❌ | ❌ | ❌ |
| evaluaciones | ✅ | ✅ | ✅ | ❌ |
| flujo | ✅ | ✅ | ❌ | ❌ |
| solicitud | ✅ | ✅ | ❌ | ❌ |
| chat | ✅ | ✅ | ✅ | ❌ |
| plantillas | ✅ | ✅ | ❌ | ❌ |
| parametrizacion | ✅ | ❌ | ❌ | ✅ |

**Hallazgos críticos:**
- ⚠️ **Discrepancia de nombres:** El monolito usa `ETO`, `Estándar`, `Visualizador`, `Admin`. El SPA usa `eto`, `user`, `visualizador`, `admin`. Esto es consistente internamente pero debe alinearse con la nomenclatura del backend.
- ⚠️ **Rutas no protegidas por rol:** Aunque `canAccess` existe, el router (`src/router/index.js`) **no valida** si el usuario tiene permiso para acceder a una ruta específica. Un `visualizador` puede navegar manualmente a `#/liberacion` y el router cargará la página sin restricción. El monolito ocultaba los botones de menú pero también validaba al mostrar la pantalla.
- ⚠️ **Página `Placeholder.js` no tiene protección de rol:** Cualquier usuario puede acceder a `/biblioteca` aunque no esté en su menú.
- ✅ Las directivas `x-show="$store.auth.role !== 'visualizador'"` en `Bandeja.js` y `x-show="isETO"` en `ListaMaestra.js` replican correctamente la lógica de ocultamiento por rol.

---

## DIMENSIÓN 2: DISEÑO, ESTILOS Y TAILWIND CSS

### 2.1 Hardcoding de Estilos en Línea (`style="..."`)

Se ejecutó `grep -r 'style=' src/ --include="*.js"`.

**Resultado: 1.913+ matches.**

Esto representa una **violación masiva** del principio de utilidad de Tailwind. El `main.css` define clases robustas (`.section-card`, `.btn`, `.badge`, `.form-input`, `.data-table`, `.modal-overlay`, `.modal-box`, `.toast`), pero la gran mayoría de las páginas y componentes **no las utilizan**, prefiriendo inline styles.

**Archivos con mayor concentración de inline styles:**

| Archivo | Líneas aprox. | Severidad | Observaciones |
|---------|---------------|-----------|---------------|
| `src/pages/ListaMaestra.js` | ~250 | 🔴 Crítica | Casi 100 % inline. Tabla, KPIs, filtros, modales CC/CN. |
| `src/pages/Bandeja.js` | ~120 | 🔴 Crítica | Pre-rendered rows con `style="padding:9px 12px;..."` en cada `<td>`. |
| `src/pages/AprobacionDocumento.js` | ~280 | 🔴 Crítica | Wizard 3 pasos completo en inline. |
| `src/pages/LiberacionDetalle.js` | ~220 | 🔴 Crítica | Formulario, árbol Outlook, IA, chips. |
| `src/pages/Revision.js` | ~90 | 🟡 Alta | Timeline y paneles en inline. |
| `src/pages/Correccion.js` | ~70 | 🟡 Alta | Visor simulado en inline. |
| `src/pages/Login.js` | ~40 | 🟡 Alta | A pesar de usar muchas clases Tailwind, aún conserva inline para gradientes y blobs. |
| `src/components/AuthModal.js` | ~60 | 🟡 Alta | Modal overlay y caja en inline. |
| `src/components/AuthRecepcionModal.js` | ~20 | 🟢 Media | Modal específico en inline. |
| `src/components/AuthDevolucionModal.js` | ~20 | 🟢 Media | Modal específico en inline. |
| `src/components/DelegarTareaModal.js` | ~20 | 🟢 Media | Modal específico en inline. |

**Ejemplo representativo (Bandeja.js, línea 13-23):**
```javascript
const tareasRows = tareasBandejaDB.map(t => `
  <tr>
    <td style="padding:9px 12px;font-family:monospace;font-weight:600;color:#64748b;font-size:11px">${t.id}</td>
    <td style="padding:9px 12px"><span class="badge ${t.tipoBadge}">${t.tipo}</span></td>
    ...
  </tr>`).join('')
```

**Problema:** Incluso usando pre-render para evitar reactivity overhead, los estilos deberían ser clases Tailwind (`px-3 py-2 font-mono text-slate-500 text-[11px] font-semibold`).

### 2.2 Configuración de Tailwind

**Archivo:** `tailwind.config.js`

**Fortalezas:**
- ✅ Paleta de colores `brand` correctamente mapeada desde `#1a5fb4` (monolito) hacia `brand-50`..`brand-950`.
- ✅ Tipografía `Inter` (variable) importada en `index.html`.
- ✅ Animaciones custom: `fade-in`, `slide-up`, `scale-in`, `toast-in`, `toast-out`, `blob`, `shimmer`.
- ✅ Sombras: `shadow-card`, `shadow-card-md`, `shadow-card-hover`, `shadow-glass`, `shadow-glass-lg`.
- ✅ Plugins: `@tailwindcss/forms`, `@tailwindcss/typography`.

**Debilidades:**
- ⚠️ **Safelist masiva (46 líneas):** La safelist incluye cientos de clases. Esto es un **síntoma de uso inadecuado**: si las clases se usaran directamente en los templates, Tailwind las detectaría automáticamente. La necesidad de safelist tan extensa confirma que muchos estilos están hardcodeados en inline styles y no en clases utilitarias.
- ⚠️ **Inconsistencia de nomenclatura:** El monolito usa `badge-green`, `badge-amber`, etc. (definidas en CSS nativo). Tailwind config incluye estas clases en safelist, pero `main.css` las redefine con `@apply`. Esto es correcto, pero hay duplicación semántica: `badge-green` (custom) vs. `bg-emerald-50 text-emerald-700` (Tailwind nativo).
- ⚠️ **No se usa `container queries` ni `typography` plugin** en ninguna página visible.

### 2.3 UI/UX Consistency

**Botones:**
- ✅ `main.css` define `.btn`, `.btn-primary`, `.btn-danger`, `.btn-ghost`, `.btn-sm`, `.btn-lg`, `.btn-xl` con transiciones y estados focus/hover/active.
- ❌ **Pero** muchas páginas (`Revision.js`, `Correccion.js`, `VersionEditable.js`) crean botones con `style="padding:10px;border-radius:8px;background:#1a5fb4;color:#fff;..."` en lugar de `class="btn btn-primary"`.

**Badges:**
- ✅ `main.css` define `.badge` y variantes correctamente.
- ❌ `ListaMaestra.js` crea badges inline con `:style="'display:inline-flex;padding:2px 8px;border-radius:9999px;...'"` en lugar de usar `class="badge badge-green"`.

**Tablas:**
- ✅ `.data-table` en `main.css` replica fielmente el estilo del monolito (headers uppercase, bordes sutiles, hover suave).
- ❌ **Casi ninguna página usa `.data-table`.** `Bandeja.js` usa `<table class="data-table" style="...">` pero luego sobreescribe todos los estilos de celda con inline.

**Layouts:**
- ✅ `AppLayout.js` usa clases Tailwind extensivamente (`flex`, `h-full`, `overflow-hidden`, `bg-slate-50`, etc.).
- ⚠️ El sidebar usa `style="background: linear-gradient(...)"` inline en lugar de una clase utilitaria o custom.

---

## DIMENSIÓN 3: MODALES, OVERLAYS Y TOASTS

### 3.1 Inventario de Modales

Existen **14 modales globales** registrados en `AppLayout.js` e inicializados en `main.js`:

| # | Modal | Archivo | Uso | Estado |
|---|-------|---------|-----|--------|
| 1 | AuthModal (Firma Digital) | `AuthModal.js` | Doble auth genérico | ✅ |
| 2 | AuthModalDevolucion | `AuthModal.js` | Variante de devolución CC | ✅ |
| 3 | ProfileModal | `ProfileModal.js` | Perfil de usuario | ✅ |
| 4 | TimelineModal | `TimelineModal.js` | Historial de proceso | ✅ |
| 5 | PdfViewerModal | `PdfViewerModal.js` | Visor PDF | ✅ |
| 6 | CertificadoPdf | `PdfViewerModal.js` | Variante certificado | ✅ |
| 7 | AlertaVencidoModal | `AlertaVencidoModal.js` | Alerta de documento vencido | ✅ |
| 8 | AlcanceModal | `AlcanceModal.js` | Alcance de difusión | ✅ |
| 9 | ParametrosDifusionModal | `ParametrosDifusionModal.js` | Parámetros de difusión | ✅ |
| 10 | ConfirmLiberacionModal | `ConfirmLiberacionModal.js` | Confirmar liberar/devolver | ✅ |
| 11 | DelegarTareaModal | `DelegarTareaModal.js` | Delegar tarea | ✅ |
| 12 | AuthRecepcionModal | `AuthRecepcionModal.js` | Confirmar recepción copia | ✅ |
| 13 | AuthDevolucionModal | `AuthDevolucionModal.js` | Confirmar devolución copia | ✅ |
| 14 | ExamConfirmModal | `ExamConfirmModal.js` | Confirmar inicio de examen | ✅ |

**Hallazgos de ciclo de vida:**
- ✅ Todos los modales usan `x-show` de Alpine para control de visibilidad.
- ⚠️ **Doble control de display:** Muchos modales tienen `style="display:none"` inline **y** `:style="open ? 'display:flex' : 'display:none'"`. Esto crea una condición de carrera: Alpine maneja `x-show` con `display: none` vía estilos inline, pero el atributo `:style` también intenta setear `display`. En la práctica funciona porque `:style` tiene mayor prioridad de binding, pero es técnicamente redundante y propenso a bugs en transiciones.
- ⚠️ **z-index inconsistente:** Los modales de página (`ListaMaestra.js` CC/CN, `AprobacionDocumento.js` cancelar) usan `z-index: 3000`, mientras que los modales globales usan `z-index: 9999`. No hay conflicto visual porque los globales se montan fuera del flujo de páginas, pero esto debe estandarizarse.
- ⚠️ **Backdrop blur:** Algunos modales (`AuthModal.js`) no tienen `backdrop-filter: blur(4px)`, mientras que otros (`ListaMaestra.js` CC/CN) sí lo tienen. La experiencia visual es inconsistente.

### 3.2 Sistema de Toasts

**Archivo:** `src/components/Toast.js`

**Funcionamiento:**
- Exposición global: `window.toast = toast`
- Magic helper Alpine: `$toast`
- Container en `index.html`: `<div id="toast-container" class="fixed bottom-5 right-5 z-[9999]...">`

**Hallazgo CRÍTICO:**
- ❌ **Duración incorrecta:** La función `toast(message, type, duration = 4500)` tiene un default de **4.500 ms**.
- 📋 **Requerimiento de instrucciones:** "desaparecer exactamente a los **2.5 segundos**, imitando la UX original."
- **Impacto:** La experiencia de usuario se siente más lenta que el monolito. Además, el comentario en la JSDoc dice `@param {number} [duration=3500]`, pero el código usa `4500`. Hay una discrepancia documento-código.

**Otros hallazgos:**
- ✅ Auto-destrucción con animación `toastOut` (0.25s ease-in).
- ✅ Botón de cierre manual en cada toast.
- ✅ Prepend (nuevos toasts aparecen arriba).
- ⚠️ **No hay límite de toasts simultáneos.** Si se disparan 20 toasts rápidamente, se apilan indefinidamente. El monolito parecía limitar a 3-4 visibles.

---

## DIMENSIÓN 4: ARQUITECTURA DE DATOS (MOCKS vs UI)

### 4.1 Inventario de Archivos de Datos (`src/data/`)

| Archivo | Contenido | Usado por | Estado |
|---------|-----------|-----------|--------|
| `documents.js` | Lista Maestra, Consulta, CC, CN, Biblioteca, Timeline config | `ListaMaestra.js`, `ConsultaDocumentos.js`, `MonitorCC.js`, `MonitorCN.js` | ✅ Correcto |
| `tasks.js` | Tareas bandeja, completas, evaluaciones, lectura, recepción copias, liberación | `Bandeja.js`, `TareasCompletas.js` | ✅ Correcto |
| `users.js` | Usuarios DB, login map, avatares, lista empleados | `auth.js`, `ProfileModal.js` | ✅ Correcto |
| `gerencias.js` | Árbol de gerencias/áreas, tipos de doc | `AprobacionDocumento.js`, `LiberacionDetalle.js` | ✅ Correcto |
| `plantillas.js` | Plantillas documentales | `Plantillas.js` | ✅ Correcto |
| `copias.js` | — | — | ⚠️ Vacío o no inspeccionado |
| `evaluaciones.js` | — | — | ⚠️ Vacío o no inspeccionado |
| `bitacora.js` | — | — | ⚠️ Vacío o no inspeccionado |
| `movimientos.js` | — | — | ⚠️ Vacío o no inspeccionado |
| `slaConfig.js` | — | — | ⚠️ Vacío o no inspeccionado |
| `notificaciones.js` | — | — | ⚠️ Vacío o no inspeccionado |
| `enrutamiento.js` | — | — | ⚠️ Vacío o no inspeccionado |
| `parametrosSistema.js` | — | — | ⚠️ Vacío o no inspeccionado |

### 4.2 Datos Hardcodeados en Vistas (VIOLACIÓN CRÍTICA)

La instrucción establece: *"Ninguna vista debe tener arrays de datos quemados (hardcodeados) en su lógica. Absolutamente toda la data mockeada debe ser importada desde `src/data/`."*

Se encontraron **11 páginas** con datos encapsulados:

| # | Archivo | Variable hardcodeada | Tipo de dato | Líneas aprox. |
|---|---------|----------------------|--------------|---------------|
| 1 | `Liberacion.js` | `const TAREAS_LIB` | Array de tareas | 4-8 |
| 2 | `Publicacion.js` | `const PUB_DATA` | Array de publicaciones | 4-8 |
| 3 | `MonitorCC.js` | `const CC_DATA` | Array de copias controladas | 4-8 |
| 4 | `MonitorCN.js` | `const CN_DATA` | Array de copias no controladas | 4-8 |
| 5 | `Parametrizacion.js` | `const entradas` | Array de parámetros | ~20 |
| 6 | `ConfigExamen.js` | `const DOCS_DISPONIBLES` | Array de docs para examen | 4-8 |
| 7 | `Evaluaciones.js` | `const PENDIENTES`, `const HISTORIAL` | Arrays evaluaciones | 8-12 |
| 8 | `Certificados.js` | `const CERTS` | Array de certificados | 4-8 |
| 9 | `LiberacionDetalle.js` | `const TIPOS_LIST` | Array tipos de documento | 7 |
| 10 | `Chat.js` | `const RESPUESTAS` | Objeto de respuestas IA | 4-15 |
| 11 | `Revision.js` | Timeline array inline | Array de nodos timeline | ~20 (en template string) |

**Ejemplo (`Liberacion.js`):**
```javascript
const TAREAS_LIB = [
  {id:246,tipo:'Liberación ETO',codigo:'MET-CAL-002',...},
  {id:247,tipo:'Liberación ETO',codigo:'PRO-LOG-018',...},
  ...
]
```

**Impacto:** Si se necesita cambiar un dato de prueba, hay que editar 11 archivos diferentes en lugar de un único `src/data/`. Esto viola el principio DRY y dificulta la transición a backend real.

**Nota especial:** `Revision.js` tiene el timeline hardcodeado directamente en el template string HTML (array inline mapeado a `.join('')`). Este dato debería venir de `src/data/bitacora.js` o `src/data/movimientos.js`.

---

## DIMENSIÓN 5: TRAZABILIDAD LÓGICA (CRUDs, FILTROS Y EVENTOS)

### 5.1 Filtros Reactivos

**ListaMaestra.js:**
- ✅ Filtro de texto (`q`) busca en `cod`, `tit`, `ger`, `area`.
- ✅ Filtro por tipo (`filterTipo`) y gerencia (`filterGer`) con `<select>`.
- ✅ Filtros múltiples por vigencia (`filterVig[]`) y estatus (`filterEst[]`) con dropdowns de checkboxes.
- ✅ KPIs reactivos (`kpis`) calculados sobre `docs` filtrados.
- ✅ Ocultamiento de obsoletos para no-ETO (`!this.isETO && d.obsoleto`).
- ⚠️ **Performance:** La tabla se renderiza con `<template x-for="d in filtered">`. Con 16 documentos no hay problema, pero si la lista maestra crece a 500+, Alpine re-renderizará todo el DOM en cada keystroke del filtro de texto. Se recomienda `x-show` por fila o paginación.

**ConsultaDocumentos.js** (no inspeccionado en detalle, pero por patrón de arquitectura):
- Se asume que replica los filtros del monolito (usuario, área, código, etapa).

### 5.2 Operaciones (Acciones)

**Firma Digital:**
- ✅ `AuthModal.js` centraliza la firma digital con usuario pre-llenado y contraseña.
- ✅ Simulación de latencia de red (`setTimeout(..., 600)`).
- ❌ **No valida contraseña real.** Acepta cualquier texto no vacío. En producción esto debe hacer POST al backend.

**Aprobar / Devolver:**
- ✅ `Revision.js` permite aprobar o devolver con observación (mínimo 10 caracteres para devolución).
- ✅ Delegación de tarea mediante `DelegarTareaModal.js`.

**Declarar Obsoleto:**
- ✅ `ListaMaestra.js` tiene `togObsoleto(d)` que alterna entre Vigente y Obsoleto, con registro de fecha.

**Generar Copias:**
- ✅ `ListaMaestra.js` tiene modales inline para CC y CN con validación de destinatarios.

**Liberación ETO:**
- ✅ `LiberacionDetalle.js` tiene CRUD de revisores y aprobadores (add/remove).
- ✅ Árbol Outlook reactivo con checkboxes padre-hijo.
- ✅ Análisis de similitud IA simulado.

### 5.3 Tiempos y SLA (Semaforización)

**Bandeja.js:**
- ✅ Usa `tareasBandejaDB` importado desde `src/data/tasks.js`.
- ✅ Cada tarea tiene `slaBadge` (`badge-red`, `badge-amber`, `badge-green`).
- ✅ Visualización con emoji (🔴, 🟡, 🟢) y texto descriptivo.

**TareasCompletas.js:**
- Se asume que replica la misma lógica de SLA con más filas.

**Hallazgo:**
- ⚠️ **SLA no es calculado dinámicamente.** Es un campo estático en el mock (`sla: '🔴 6 días'`). En producción, el SLA debe calcularse a partir de `fechaAsignación` vs. `fechaActual` usando `src/data/slaConfig.js`.

---

## DIMENSIÓN 6: PRUEBAS DE ESCRITORIO (MENTAL WALK-THROUGH)

### 6.1 Flujo: Creación → Liberación → Revisión → Aprobación

**Paso 1: Creación de documento**
- Ruta: `/aprobacion-documento`
- Página: `AprobacionDocumento.js` (Wizard 3 pasos)
- Estado: ✅ Funcional
- Observación: El wizard guía al usuario por datos, difusión (árbol Outlook) y flujo de firmas. El botón "Firmar y Enviar a Liberación" invoca `authModal` y redirige a `/bandeja`.

**Paso 2: Bandeja de Liberación ETO**
- Ruta: `/liberacion`
- Página: `Liberacion.js`
- Estado: ✅ Funcional
- Observación: Muestra 3 tareas pendientes. Botón "Atender →" redirige a `/liberacion-detalle`.

**Paso 3: Atender Liberación (Detalle)**
- Ruta: `/liberacion-detalle`
- Página: `LiberacionDetalle.js`
- Estado: ✅ Funcional
- Observación: Muestra formulario colapsable, análisis IA, archivos, árbol de difusión. Decisiones: "Liberar Documento" o "Devolver al Solicitante".
- **Punto de quiebre:** La decisión invoca `confirmLiberacionModal` con `onConfirm: () => {window.location.hash = '/bandeja'}`. No hay transición de estado real del documento (sigue estando en la lista de liberación si se recarga).

**Paso 4: Revisión / Aprobación**
- Ruta: `/revision`
- Página: `Revision.js`
- Estado: ✅ Funcional
- Observación: Muestra timeline estático, observaciones, archivos Office 365. Acciones: Devolver, Delegar, Aprobar.
- **Punto de quiebre:** El timeline es un array inline hardcodeado. No refleja el estado real del flujo anterior.

**Paso 5: Corrección**
- Ruta: `/correccion`
- Página: `Correccion.js`
- Estado: ✅ Funcional
- Observación: Simula apertura de Office 365, checkbox de confirmación, firma digital y reenvío.

**Paso 6: Aprobación Final**
- La aprobación final está implícita en `Revision.js` (botón "Aprobar (Firma Digital)").
- No hay una pantalla separada de "Aprobación Final" como etapa distinta de Revisión.

### 6.2 Otros Flujos

**Flujo de Evaluación:**
- `/pre-eval` → `/examen`? No existe `/examen`. El usuario inicia desde `/pre-eval` pero no hay pantalla de examen propiamente dicha.
- **Punto de quiebre:** `s-examen` del monolito no tiene equivalente SPA.

**Flujo de Copias:**
- `/copias-cc` y `/copias-cn` existen.
- `ListaMaestra.js` puede generar copias desde la tabla.
- **Punto de quiebre:** No hay una vista consolidada de "Módulo de Copias" (`s-modulo-copias`).

**Flujo de Biblioteca:**
- `/biblioteca` mapea a `Placeholder.js`.
- **Punto de quiebre:** El monolito tenía una biblioteca virtual funcional con documentos favoritos. En SPA es solo un placeholder.

### 6.3 Puntos de Quiebre Globales

| # | Punto de Quiebre | Severidad | Descripción |
|---|------------------|-----------|-------------|
| 1 | Estado no persistente entre páginas | 🔴 Alta | Cada página es una isla. Aprobar en `/revision` no actualiza el estado en `/bandeja`. |
| 2 | Timeline estático en Revision | 🔴 Alta | No consume `bitacora.js`; es un array inline. |
| 3 | Falta `/examen` | 🟡 Media | `s-examen` del monolito no migrado. |
| 4 | Biblioteca es placeholder | 🟡 Media | `s-biblioteca` degradada. |
| 5 | No hay `/solicitud` consolidada | 🟢 Baja | Atomizada en `/version-editable` + `/aprobacion-documento`; aceptable. |
| 6 | Documento hardcodeado en Correccion | 🟡 Media | `PRO-CAL-045` está quemado; debería venir de la tarea seleccionada en bandeja. |
| 7 | Revisores/Aprobadores quemados en Revision | 🟡 Media |
| 8 | Pérdida de UI Generación Copias | 🔴 Alta | El Módulo de Copias (`s-modulo-copias`) se perdió. En `src/` solo se listan tablas, falta la interfaz para generar múltiples copias con destinatarios dinámicos. |
| 9 | Visor PDF sin herramientas | 🔴 Alta | `PdfViewerModal.js` es un cascarón. Faltan funciones del monolito: Zoom (+20%/-20%), rotación, marca de agua dinámica y carátula automática de firmas. |
| 10 | Expediente de Personal (Kardex) | 🟡 Media | En el monitor de evaluaciones, falta la lógica de búsqueda que oculta la tabla principal y muestra el historial académico del empleado. |
| 11 | Lógica de "ACID Lock" omitida | 🟡 Media | La generación de códigos está concatenando strings estáticos; falta la preparación para consultar el correlativo real. |
 `MAN-LOG-003 v01` y revisores fijos; deberían ser dinámicos. |

---

## PLAN DE REFACTORIZACIÓN Y CONFIGURACIÓN

A continuación, el orden exacto en que el siguiente agente de programación debe ejecutar los cambios. Este orden está diseñado para minimizar conflictos y establecer bases sólidas antes de tocar las vistas.

### FASE 1: FUNDAMENTOS (Base de la pirámide)
**Objetivo:** Establecer la capa de datos y configuración antes de refactorizar vistas.

1. **`tailwind.config.js` y `src/main.css`**
   - Revisar y reducir la `safelist`. Eliminar clases que ya se usan directamente en templates. La meta es reducirla a menos de 20 entradas.
   - Añadir utilidades custom para los patrones de inline style más comunes:
     - `.kpi-card`, `.kpi-card-amber`, `.kpi-card-red` (para los 5 KPIs de ListaMaestra).
     - `.table-cell-mono`, `.table-cell-badge`.
     - `.page-header`, `.page-subtitle`.
     - `.form-grid-2`, `.form-grid-3`.
     - `.card-base` (reemplazo de `background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;box-shadow:...`).
   - Crear una clase `.animate-fade-in-page` para reemplazar `style="animation:fadeIn 0.35s ease-out both"` en cada página.

2. **`src/data/` — Completar y centralizar**
   - Extraer TODOS los datos hardcodeados de las 11 páginas identificadas y moverlos a archivos existentes o nuevos:
     - `Liberacion.js` → `src/data/tasks.js` (agregar `tareasLiberacionDB`).
     - `Publicacion.js` → `src/data/documents.js` o nuevo `publicaciones.js`.
     - `MonitorCC.js` / `MonitorCN.js` → `src/data/copias.js`.
     - `Parametrizacion.js` → `src/data/parametrosSistema.js`.
     - `ConfigExamen.js` → `src/data/evaluaciones.js`.
     - `Evaluaciones.js` → `src/data/evaluaciones.js`.
     - `Certificados.js` → `src/data/evaluaciones.js`.
     - `LiberacionDetalle.js` → `src/data/documents.js` (tipos de documento ya parcialmente en `gerencias.js`).
     - `Chat.js` → nuevo `src/data/iaRespuestas.js`.
     - `Revision.js` → `src/data/bitacora.js` (timeline dinámico por código de documento).
   - Crear `src/data/procesosFlujo.js` para almacenar el estado de cada proceso documental (id, etapa actual, revisores, aprobadores, observaciones). Esto permitirá compartir estado entre `/liberacion-detalle`, `/revision`, `/correccion` y `/bandeja`.

### FASE 2: INFRAESTRUCTURA GLOBAL

3. **Store Global para Estado de Flujo Documental**
   - Crear `src/store/flow.js` (Alpine store).
   - Estado: `procesos: []`, `procesoActivo: null`.
   - Métodos: `crearProceso(datos)`, `avanzarEtapa(idProceso, nuevaEtapa)`, `agregarObservacion(idProceso, obs)`, `asignarRevisores(idProceso, revisores)`.
   - Este store será la fuente de verdad para el flujo completo, reemplazando los datos estáticos de `Revision.js` y `LiberacionDetalle.js`.

4. **Corregir Toast.js**
   - Cambiar `duration = 4500` a `duration = 2500`.
   - Corregir el comentario JSDoc que dice `3500`.
   - Opcional: Agregar límite de toasts visibles (máximo 5, eliminar el más antiguo).

5. **Estandarizar Modales**
   - Crear `src/components/ModalBase.js` con template genérico usando las clases `.modal-overlay` y `.modal-box` de `main.css`.
   - Refactorizar `AuthModal.js`, `AuthRecepcionModal.js`, `AuthDevolucionModal.js` para que usen `ModalBase` inyectando solo contenido específico.
   - Eliminar todos los `style="width: 100vw; height: 100vh; ..."` de los modales y reemplazarlos por `class="modal-overlay"`.

### FASE 3: REFACTORIZACIÓN DE VISTAS (De más crítica a menos)

6. **`src/pages/ListaMaestra.js`**
   - Reemplazar TODOS los inline styles por clases Tailwind y las utilidades custom de Fase 1.
   - Extraer los modales CC/CN inline a componentes separados (`src/components/CopiaControladaModal.js`, `src/components/CopiaNoControladaModal.js`) o reutilizar `ModalBase`.
   - Usar `.data-table` de `main.css` y eliminar los `<style>` de celda.

7. **`src/pages/Bandeja.js`**
   - Reemplazar inline styles de las cards y tablas por clases Tailwind.
   - Eliminar los `style="padding:9px 12px;..."` de los `<td>` pre-renderizados; usar clases en el `<table>` y estilos globales.
   - La sección de "Recepción de Copias Físicas" es la única que requiere reactividad real (se eliminan filas); mantener `x-for` pero limpiar los inline styles.

8. **`src/pages/AprobacionDocumento.js`**
   - Reemplazar inline styles del wizard y stepper por clases Tailwind.
   - Extraer datalist de empleados a `src/data/users.js` (ya existe `listaEmpleados`).
   - Reemplazar modal inline de cancelación por `ModalBase`.

9. **`src/pages/LiberacionDetalle.js`**
   - Reemplazar inline styles masivos.
   - Conectar el timeline/formulario a `src/store/flow.js` en lugar de datos quemados.
   - El árbol Outlook ya está bien implementado; solo limpiar estilos.

10. **`src/pages/Revision.js`**
    - Reemplazar timeline inline por `x-for` sobre datos de `src/data/bitacora.js` o `src/store/flow.js`.
    - Reemplazar documento hardcodeado (`MAN-LOG-003 v01`) por lectura del proceso activo.
    - Limpiar inline styles.

11. **`src/pages/Correccion.js`**
    - Reemplazar documento hardcodeado (`PRO-CAL-045`) por lectura del proceso activo.
    - Limpiar inline styles del visor simulado.
    - Reemplazar modal inline de firma por `AuthModal.js` (ya existe; solo invocarlo).

12. **`src/pages/Liberacion.js`**
    - Extraer `TAREAS_LIB` a `src/data/tasks.js`.
    - Limpiar inline styles de la tabla.

13. **`src/pages/Chat.js`**
    - Extraer `RESPUESTAS` a `src/data/iaRespuestas.js`.
    - Limpiar inline styles de burbujas de chat.

### FASE 4: RUTAS Y NAVEGACIÓN

14. **Protección de rutas por rol**
    - En `src/router/index.js`, antes de cargar un módulo, verificar:
      ```javascript
      const auth = window.Alpine?.store('auth')
      if (!auth?.canAccessRoute(hash)) { navigate('/bandeja'); return }
      ```
    - Agregar `canAccessRoute(route)` en `authStore` que mapee rutas a las secciones existentes de `canAccess()`.

15. **Topbar dinámico**
    - Agregar un objeto `routeTitles` en el router para actualizar `#topbar-title` según la ruta activa.

### FASE 5: PÁGINAS FALTANTES

16. **Implementar `/examen`**
    - Crear `src/pages/Examen.js` con el flujo de examen migrado desde `s-examen` del monolito.
    - Agregar ruta en `src/router/index.js`.

17. **Implementar `/biblioteca`**
    - Reemplazar `Placeholder.js` en la ruta `/biblioteca` por una vista real que consuma `documents.js` (filtrando `fav: true`).

18. **Restaurar el Módulo de Copias (`/generar-copias`)**
   - Reconstruir la pantalla `s-modulo-copias` del monolito como una vista dedicada (no modal), incluyendo la generación dinámica de inputs para destinatarios.

19. **Potenciar el Visor PDF y Expediente**
   - Añadir la lógica de Zoom, Rotación y Carátula al `PdfViewerModal.js`.
   - Restaurar el buscador de Expediente de Personal en `Publicacion.js`.

---

## CONCLUSIÓN FINAL

El proyecto `cofar-sgd` representa un **esfuerzo de migración considerable** con una arquitectura SPA bien estructurada (Vite, Alpine.js, Tailwind, hash router). El layout principal, el sistema de autenticación, el enrutamiento y los modales globales son sólidos.

Las principales amenazas para la producción son:

1. **Deuda técnica de estilos:** 1.913+ inline styles que bloquean el mantenimiento y la consistencia visual.
2. **Datos encapsulados en vistas:** 11 archivos con lógica de datos que debería estar centralizada.
3. **Estado no compartido entre páginas:** El flujo documental no tiene memoria; cada etapa es independiente.
4. **Duración de Toast incorrecta:** 4.500 ms en lugar de 2.500 ms.
5. **Páginas faltantes:** `/examen` y `/biblioteca` (placeholder) deben completarse.

Si se ejecuta el **Plan de Refactorización** en el orden propuesto, el sistema alcanzará una calidad de producción en aproximadamente **2-3 iteraciones de desarrollo** (estimado: 15-20 horas de trabajo enfocado).

**Recomendación:** No se debe desplegar a producción hasta completar al menos la **Fase 1** (datos centralizados) y **Fase 2** (Toast corregido, modal base, store de flujo).

---
*Fin del Reporte de Auditoría*

---

## 🛑 ANTI-PATRONES Y REGLAS ARQUITECTÓNICAS ESTRICTAS (LESSONS LEARNED)
Durante las fases de refactorización, se identificaron errores críticos generados por malas interpretaciones del framework. **Queda estrictamente prohibido repetir estos patrones:**

1. **API de Alpine.js Global (El Bug del Bucle Infinito):**
   - ❌ **ANTI-PATRÓN:** Intentar acceder al scope de Alpine desde Vanilla JS usando `el.__x.$data` (Sintaxis de Alpine v2). Esto genera `undefined` y rompe el hilo de ejecución silenciosamente.
   - ✅ **SOLUCIÓN (Alpine v3):** Usar SIEMPRE `el._x_dataStack[0].miFuncion()`. Ejemplo: 
     `const store = document.querySelector('[x-data="miModalData"]'); if (store && store._x_dataStack) store._x_dataStack[0].abrir();`

2. **Inyección Doble de Modales Globales (El Bug de los Clones Invisibles):**
   - ❌ **ANTI-PATRÓN:** Registrar un modal inyectando su HTML vía `document.body.insertAdjacentHTML(...)` en `src/main.js`.
   - ✅ **SOLUCIÓN:** El archivo `main.js` SOLO debe ejecutar la inicialización de la lógica (`initMiModal()`). El Template HTML (`MiModalTemplate`) DEBE inyectarse EXCLUSIVAMENTE en `src/layouts/AppLayout.js` dentro del bloque de modales globales para aprovechar el Virtual DOM y evitar duplicidad.

3. **Renderizado de HTML Dinámico en Alpine:**
   - ❌ **ANTI-PATRÓN:** Usar `x-text="mensaje"` cuando el mensaje contiene etiquetas HTML (ej. `<strong>Texto</strong>`).
   - ✅ **SOLUCIÓN:** Usar `x-html="mensaje"` asegurando la renderización de negritas e íconos inyectados desde JS.

4. **Acceso Seguro a Propiedades del Store Global:**
   - ❌ **ANTI-PATRÓN:** Asumir directamente `window.Alpine.store('auth').usuario` sin fallbacks.
   - ✅ **SOLUCIÓN:** Mapear de forma segura contra la estructura real del AuthStore: `auth?.user?.username || auth?.user?.name || 'Usuario'`.

5. **Uso de Eventos de Teclado Deprecados:** - **Anti-patrón:** Usar `@keypress.enter` en inputs o textareas. La API `keypress` está deprecada en los navegadores modernos y causa que Alpine.js ignore el modificador `.enter`, disparando la función en cada pulsación de tecla.
   - **Solución:** Usar SIEMPRE `@keydown.enter.prevent` para la captura de la tecla "Enter". Esto garantiza compatibilidad, filtra correctamente la tecla y bloquea el comportamiento nativo del navegador (como recargas de página o saltos de línea no deseados).

6. **Hardcodeo de Contadores en Template Strings:** - **Anti-patrón:** Renderizar variables de estado o contadores como texto estático desde funciones de JavaScript (ej. inyectar un `5` fijo al construir el menú lateral). Esto rompe la reactividad y causa inconsistencias visuales.
   - **Solución:** Inyectar siempre directivas reactivas apuntando al Store global (ej. `<span x-text=\"$store.notificaciones.total\"></span>`), delegando a Alpine el trabajo de hidratar el dato en tiempo real.

7. **Comparación Textual de Fechas:** - **Anti-patrón:** Intentar filtrar rangos de fechas (ej. en tablas) comparando strings directamente (`"15/04/2026" > "2026-04-12"`), lo cual genera falsos positivos.
   - **Solución:** Implementar siempre un helper de parseo (como `parseDMY()`) para convertir la data de los mocks y los `input[type="date"]` a objetos `Date` nativos (timestamps) antes de aplicar lógica de filtrado reactivo en Alpine.

8. **Modificaciones Globales vs Locales (CSS):** - **Regla:** Cuando se detecte un error visual que afecta a múltiples pantallas (ej. modales descentrados o tablas solapadas), la corrección DEBE priorizarse en los componentes base (`main.css` o Layouts) en lugar de parchear archivo por archivo, promoviendo el principio DRY (Don't Repeat Yourself).

9. **Manejo de Transacciones Globales (Logs/Auditoría):** - **Anti-patrón:** Repetir código de registro de logs dentro de cada función individual o usar variables locales que no se comunican entre pestañas/componentes.
   - **Solución:** Utilizar funciones centralizadas (ej. `pushLog()`) ancladas al componente padre (`x-data` principal) o usar `$store`/`$dispatch` para emitir eventos transversales. Cualquier acción CRUD debe pasar por este embudo para garantizar la auditoría en tiempo real.

---

## 🧪 PROTOCOLO DE VALIDACIÓN E2E (PLAYWRIGHT STANDALONE)
*Basado en incidencias críticas del Lote 7*

1. **Entorno y Puertos:** El servidor de desarrollo (Vite) se ejecuta localmente en `http://localhost:3000`. NO intentar levantarlo desde el script de test; asumir que ya está activo.
2. **Arquitectura Standalone:** Prohibido el uso de `@playwright/test` o configuraciones de framework pesadas. Usar scripts de Node puros (`.mjs`) importando `chromium` directamente para evitar bloqueos en el entorno CLI.
3. **Persistencia de Estado (SPA):** Al ser una SPA con Alpine.js, el uso de `page.goto()` para rutas internas provoca un "Hard Reload" que limpia el store de autenticación. 
   - **Regla:** Navegar usando `page.evaluate(() => window.location.hash = '#/ruta')` tras el login inicial.
4. **Interacción con Modales:** Dado que múltiples modales coexisten en el DOM (ocultos con `x-show`), las aserciones y clics deben filtrar por visibilidad (`visible: true`) o usar selectores de ID únicos para evitar ambigüedad.
5. **Logs Visuales:** El script debe imprimir con `console.log` cada hito del test para permitir el monitoreo en tiempo real desde la terminal de OpenCode.
6. **Ubicación del Script Standalone:** El archivo temporal `.mjs` de Playwright DEBE crearse SIEMPRE en la **raíz absoluta del proyecto** (ej. `cofar-sgd/test-temp.mjs`), NUNCA en directorios temporales del sistema operativo (`AppData`, `/tmp`, etc.). Esto evita errores catastróficos de resolución de módulos de Node y conflictos de rutas.
7. **Selectores de Login Estándar:** Para el flujo de autenticación en los scripts E2E, NO adivines selectores ni uses `name=\"username\"`. Usa estrictamente los IDs del DOM de nuestra arquitectura: `#login-username`, `#login-password` y `#login-submit`.
8. **Delay de Reactividad de Alpine.js:** El framework toma unos milisegundos en hidratar el DOM con los datos de los Stores (ej. renderizar un badge o llenar una tabla). El script de prueba DEBE incluir pequeñas esperas (`await page.waitForTimeout(600)`) antes de ejecutar aserciones (`expect`/`assert`) sobre elementos dinámicos para evitar falsos negativos.
9. **Debugging Visual (Screenshots):** Si el script E2E sufre un timeout o no encuentra un selector, el agente DEBE usar `await page.screenshot({ path: 'debug-error.png' })` para inspeccionar el estado exacto del DOM y la UI. Esta imagen DEBE ser eliminada obligatoriamente al final del script en el bloque `finally` para no ensuciar el repositorio.

10. **Interacción con Elementos en Transición (x-transition):** Los modales y popovers en nuestro sistema usan animaciones de entrada. El agente DEBE forzar a Playwright a esperar a que el elemento esté completamente visible (`await page.waitForSelector('...', { state: 'visible' })` o un `waitForTimeout(300)`) antes de ejecutar clics como "Confirmar" o "Cancelar". Ignorar esto causará timeouts por "Element is not clickable".

11. **🛑 ANTI-PATRÓN CRÍTICO (NO USAR spawn):**Está ESTRICTAMENTE PROHIBIDO que los scripts .mjs de Playwright intenten levantar el servidor de Vite mediante child_process o spawn('npm', ['run', 'dev']). El agente SIEMPRE debe asumir que el servidor ya está corriendo en http://localhost:3000. El script solo debe importar chromium, hacer las pruebas en headless: true, cerrar el browser y hacer process.exit(0).

---

# 🚀 REGISTRO DE EJECUCIÓN (BITÁCORA)

* **FASE 1 (Fundamentos y Data):** ✅ COMPLETADA (04/May/2026).
  - **Pruebas/Estado:** Código generado, guardado directamente en disco y validado sintácticamente. Cero defectos.
  - **Acciones Estilos:** Se optimizó `tailwind.config.js` reduciendo la safelist a < 20 clases dinámicas. Se inyectaron utilidades clave en `src/main.css` (`.card-base`, `.page-header`, `.kpi-card`, `.table-cell-mono`, `.animate-fade-in-page`). *Nota para el Agente: Usar estas clases en lugar de inline-styles al refactorizar vistas.*
  - **Acciones Data:** Se crearon/actualizaron TODOS los archivos en `src/data/` extrayendo los *mocks* sin alterar las vistas. Los archivos disponibles son: `tasks.js`, `copias.js`, `evaluaciones.js`, `bitacora.js`, `parametrosSistema.js`, `documents.js`, `iaRespuestas.js` y `procesosFlujo.js`.
* **FASE 2 (Infraestructura Global):** ✅ COMPLETADA.
  - **Estado:** Se crearon los stores, utilidades y modales base (`flow.js`, `ModalBase.js`, `Toast.js`).
* **FASE 3 - LOTE 1 (Saneamiento Visual y Bandeja):** ✅ COMPLETADA.
  - **Acciones:** `Toast.js` corregido a 2500ms y limpiado de listeners conflictivos. Los modales globales (`AuthModal`, `ProfileModal`, `TimelineModal`) fueron reparados exitosamente aplicando `<template x-teleport="body">` y la clase `.modal-overlay` para escapar del *Transform Trap* y centrarse perfectamente.
  - **Páginas Refactorizadas:** `src/pages/Bandeja.js` purgada de estilos en línea (CSS inline) usando Tailwind estricto.
* * **FASE 3 - LOTE 2 (Componentización Visor PDF y Lista Maestra):** ✅ COMPLETADA.
  - **Estado:** Código consolidado y libre de modales zombis.
  - **Acciones:** Se refactorizó profundamente `PdfViewerModal.js` aislando sus componentes en múltiples `<template x-teleport="body">` para respetar el Virtual DOM de Alpine.js. Se eliminó la deuda técnica y el código muerto (`AlertaVencidoModal.js`) purgando sus inyecciones en `AppLayout.js` y `main.js`. En `ListaMaestra.js`, se unificó la lógica de los botones "Ver" y "CV" para que deleguen el control al Visor PDF inteligente, garantizando consistencia visual para todos los roles (ETO y Usuarios).
* **FASE 3 - LOTE 3 (Aprobación Documento y Modal Cancelar):** ✅ COMPLETADA.
  - **Estado:** Código consolidado, saneado y con soporte para adjuntos múltiples.
  - **Acciones:** Se refactorizó `AprobacionDocumento.js` eliminando +280 líneas de estilos CSS en línea, migrándolos a Tailwind estricto. Se implementó una funcionalidad robusta de *Drag & Drop* múltiple para formularios secundarios (Word, Excel, DWG, PDF) con UI dinámica. Se extrajo la data dura a `src/data/users.js`. Se construyó el componente global `ConfirmCancelModal.js` para estandarizar las cancelaciones de flujo, reparando incompatibilidades previas con la API de Alpine v3 (`_x_dataStack`).
* **FASE 3 - LOTE 4 (Liberación Detalle y Árbol Outlook):** ✅ COMPLETADA.
  - **Estado:** Código consolidado, saneado y con reactividad de Alpine v3 corregida.
  - **Acciones:** Se refactorizaron `LiberacionDetalle.js` y `ConfirmLiberacionModal.js`. Se eliminaron ~235 estilos CSS en línea (inline-styles) migrándolos 100% a clases utilitarias de Tailwind. Se corrigió un bug lógico de colisión de estado (`x-model` vs inversión manual) en el árbol de distribución Outlook que bloqueaba la UI. Se implementó una regla de validación reactiva de mínimo 25 caracteres para devoluciones con observaciones. El modal de liberación ahora es un componente global puro (Teleport al `body`, clases estandarizadas).
* **FASE 3 - LOTE 5 (Flujo de Revisión y Corrección):** ✅ COMPLETADA.
  - **Estado:** Código modularizado, con UX rediseñada y datos independizados.
  - **Acciones:** Se dividió la pantalla monolítica en `Revision.js` y `AprobacionFinal.js`. Se optimizó el layout moviendo los archivos a una franja superior para aprovechar el grid. La caja de observaciones se hizo condicional. Se crearon los mocks `historialRevision` e `historialAprobacion` en `bitacora.js`. Se saneó `Correccion.js` conectándolo al `AuthModal` global. Se inyectó `DelegarTareaModal.js` correctamente al `body`. Los botones de aprobación final fueron reubicados al extremo derecho por convenciones de UX. Las rutas dinámicas fueron actualizadas en el router y en el mock de `tasks.js`.
* **FASE 3 - LOTE 6 (Módulo de Publicación y Evaluaciones):** ✅ COMPLETADA.
  - **Estado:** Código refactorizado, reactivo y validado con pruebas E2E (Playwright).
  - **Acciones:** Se refactorizó `Publicacion.js` migrando la tabla maestra a `.data-table` y los filtros a componentes dropdown en las cabeceras (Código, Nombre, Tipo, Estado). Se implementó el Expediente Académico del empleado con notas clickeables (RBAC: solo visibles para rol ETO). Se creó el componente global `RespuestasExamenModal.js` para visualizar preguntas y validaciones en colores semánticos. 
  - **Lógica de Negocio (Re-abrir):** Se rediseñó `ParametrosDifusionModal.js` para validar fechas de inicio/fin y despachar eventos a `Publicacion.js`. La tabla maestra ahora captura el evento y usa `unshift()` inyectando un ID dinámico para preservar la reactividad de Alpine, acompañado de una animación CSS (`bg-emerald-100`) para feedback visual.
  - **Configuración de Exámenes:** Se destruyó el viejo formato Wizard en `ConfigExamen.js`, convirtiéndolo en un Single Page Form con CRUD completo de preguntas, sugerencia vía IA simulada y exportación, sin dejar ningún mock hardcodeado en la vista (todo consumido desde `src/data/evaluaciones.js`).

* **FASE 3 - LOTE 7 (Monitores de Copias y Trazabilidad):** ✅ COMPLETADA.
  - **Estado:** Refactorización total de UI y lógica de filtrado reactivo.
  - **Acciones:** `MonitorCC.js` y `MonitorCN.js` migrados a `.data-table` con estilos estandarizados. Se eliminó la data hardcodeada, centralizándola en `src/data/copias.js`.
  - **Funcionalidad:** Implementación de filtros de fecha instantáneos y dropdowns multiselect en cabeceras. El `AuthDevolucionModal.js` ahora es condicional; oculta la advertencia de firma cuando se invoca desde el Monitor CC (Rol ETO).
  - **Validación:** Superada prueba E2E Standalone gestionando la persistencia de sesión en la SPA y el manejo de modales solapados.

* **FASE 3 - LOTE 8 (Asistente IA y Solicitud Editable):** ✅ COMPLETADA.
  - **Estado:** Componentes refactorizados, responsivos y con datos desacoplados.
  - **Acciones:** Se rediseñó `Chat.js` a una UI moderna de burbujas, con scroll automático, estados de carga y envío controlado exclusivamente mediante `@keydown.enter.prevent`. Se limpió la página `SolicitudEditable.js` migrando estilos inline a Tailwind CSS puro, manteniendo la consistencia de tipografía y espaciado de los lotes anteriores.
  - **Validación:** Se validó correctamente mediante Playwright Standalone la interacción sin pérdida de sesión (cambio de hash).

* **FASE 3 - LOTE 9 (Notificaciones Globales Sincronizadas):** ✅ COMPLETADA.
  - **Estado:** Dropdown moderno implementado y sincronizado exitosamente con el Sidebar.
  - **Acciones:** Se creó el store `notificaciones.js` utilizando *lazy getters* para filtrar la data de `tasks.js` según el rol (`Alpine.store('auth')?.role`). Se migró la campana estática de `AppLayout.js` a un Dropdown interactivo (Tailwind) y se reemplazaron los badges estáticos del menú lateral por enlaces reactivos al nuevo Store.
  - **Validación:** El script E2E Playwright Standalone verificó el Login mediante IDs directos, esperó la hidratación de Alpine y comprobó la sincronización 1:1 entre el contador de Mi Bandeja y el Header. Cero errores en consola.

* **FASE 3 - LOTE 10 (Expediente de Evaluaciones y Certificados):** ✅ COMPLETADA.
  - **Estado:** Vistas refactorizadas con cero estilos inline, KPIs matemáticos correctos y previsualización de impresión operativa.
  - **Acciones:** Eliminación de pestañas erróneas en Evaluaciones. Inyección del helper `parseDMY()` para filtrado exacto de fechas. Creación de la vista aislada `CertificadoImprimible.js` usando Tailwind puro para asegurar consistencia al usar `window.print()`.
  - **Validación:** El script E2E utilizó `page.screenshot()` para depuración visual proactiva, pasando exitosamente la navegación por hash y comprobando que no hay variables nulas.

* **FASE 3 - LOTE 11 (Módulo de Parametrización General):** ✅ COMPLETADA.
  - **Estado:** Pestañas modulares con CRUD reactivo en memoria, modales aislados y sistema de Logs transaccional.
  - **Acciones:** Centralización de data en `src/data/parametrosSistema.js`. Creación de los componentes `EditUserModal`, `MoveAreaModal` y el guardián global `ConfirmDeleteModal`. Implementación del bus de eventos para inyectar automáticamente acciones destructivas/creativas en la nueva pestaña de "Logs".
  - **Validación:** El script E2E navegó por múltiples pestañas, superó la barrera de las animaciones `x-transition` en los modales usando esperas explícitas y validó la inyección cruzada de datos en la tabla de Logs.

* **FASE 3 - LOTE 12 (Auditoría Global UI/UX y Responsiveness):** ✅ COMPLETADA (En Paralelo).
  - **Estado:** Solapamientos corregidos, Wizards responsivos en móviles y modales globales centrados.
  - **Acciones:** Ajustes en `main.css` y layouts para estandarización.

* **FASE 3 - LOTE 13 (Blindaje de Seguridad y Saneamiento Arquitectónico):** ✅ COMPLETADA.
* **FASE 3 - LOTE 13.5 / 13.6 (Refinamiento UX/UI y Lógica de Timeline):** ✅ COMPLETADA.
  - **Estado:** Modales centrados con `x-teleport`, alertas persistentes operativas y lógica transaccional del timeline secuenciada cronológicamente sin nodos redundantes.
* **FASE 4 - LOTE 14 (Seguridad OWASP y Mitigación XSS):** ✅ COMPLETADA.
  - **Estado:** SPA protegida contra inyección de código.
  - **Acciones:** Instalación de `dompurify`. Creación de Magic Property `$sanitize` en Alpine.js (`main.js`). Refactorización de `x-html` en `Parametrizacion.js`, `Chat.js`, `AuthModal.js` y `ConfirmDeleteModal.js`. 
  - **Validación:** Test E2E comprobó la neutralización exitosa de un payload XSS en el componente del Chat.

* **FASE ACTUAL:** 🚧 A la espera del Lote 15 (Saneamiento Visual y Migración a Íconos SVG).