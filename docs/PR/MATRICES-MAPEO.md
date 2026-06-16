# Mapeo: Archivos de Matrices → Tabs de Parametrización General → Endpoints

> **Fecha:** 2026-06-15 (sesión 4)
> **Fuentes:** archivos en `docs/Diagramas_Matrices/MATRICES/` + `docs/SISTEMA DE GESTION DOCUMENTAL - HISTORIAS DE USUARIO.pdf` (ÉPICA 9 oficial).
> **Propósito:** Mapear cada archivo Excel/Word a su tab correspondiente en la pantalla de Parametrización General, y a su endpoint backend. Esto garantiza que NADA quede hardcodeado en el frontend.

---

## 📐 Fuente oficial: ÉPICA 9 del PDF (HISTORIAS DE USUARIO)

La pantalla **"Parametrización General del Sistema"** es de uso **exclusivo para Rol ETO** y se compone de **6 pestañas (tabs)**. A continuación, el desglose de cada US de la ÉPICA 9 con sus criterios de aceptación oficiales.

### US-9.01 — Tab "Tiempos y SLAs" (pestaña activa por default)

**Estructura UI (2 sub-tarjetas):**

**Sub-tarjeta 1 — "Vigencia Documental":**
- `Tiempo de vigencia (años)` — input numérico (default 3)
- `Plazo máx. revisión/aprobación (días)` — input numérico (default 15)
- `Espera antes de auto-delegación (días)` — input numérico (default 3)
- `Plazo máx. control de lectura (días)` — input numérico (default 30)
- Botón: **"Guardar Vigencia y Flujo"**

**Sub-tarjeta 2 — "Semaforización de Bandejas":**
- Verde — "Más de 5 días restantes" — input (default 5)
- Amarillo — "Entre 1 y 5 días" — input (default 1)
- Rojo — "Menos de 1 día o vencido" — (Automático)
- Botón: **"Guardar Semaforización"**

**Sub-tarjeta inferior — "Historial de Cambios de Parámetros":** tabla `Fecha | Parámetro | Valor Anterior | Valor Nuevo | Usuario`.

**Reglas de negocio:**
- Persistencia en `configuracion_global` (clave/valor).
- **No retroactividad:** cambios en plazos afectan solo a tareas generadas *después* del cambio.

**Endpoint backend:** `GET/POST/PATCH /api/v1/configuracion-global` con claves parametrizables.

---

### US-9.02 — Tab "Restricciones"

**Estructura UI (2 sub-tarjetas):**

**Sub-tarjeta 1 — "Restricciones de Archivos Adjuntos":**
- `Límite de archivos adjuntos por solicitud` — input (default 5)
- `Tamaño máximo por archivo (MB)` — input (default 20) — el backend rechaza con 413
- Botón: **"Guardar Restricciones de Archivo"**

**Sub-tarjeta 2 — "Límites de Descarga de Editables":**
- `Máx. descargas de editable por día/usuario` — input (default 3) — bloquea si excede
- `Paginación de "Mi Bandeja" (registros)` — dropdown (default 20)
- `Tipos de documento excluidos del límite de descarga` — multiselect con chips
- Botón: **"Guardar Límites de Descarga"**

**Reglas de negocio:**
- Backend rechaza con 413 si excede tamaño.
- Contador diario de descargas por usuario.

**Endpoint backend:** `GET/POST/PATCH /api/v1/configuracion-global` (claves de archivos + claves de descargas).

---

### US-9.03 — Tab "Diccionarios y Enrutamiento"

**Estructura UI (3 sub-tarjetas):**

**Sub-tarjeta 1 — "Tipos de Documento"** (con botón "+ Nuevo"):
- Tabla: `TIPO | CÓDIGO | ACCIONES`
- Ejemplo: Procedimiento | PRO | ✏️ / ⛔

**Sub-tarjeta 2 — "Estados de Proceso y Tarea"** (con botón "+ Nuevo"):
- Tabla: `ESTADO | CONTEXTO | ACCIONES`
- Ejemplo: Elaboración | Tarea | ✏️ / ⛔

**Sub-tarjeta 3 — "Matriz de Enrutamiento ETO (Asignación de Analistas por Gerencia)":**
- Tabla: `GERENCIA/ÁREA | ANALISTA ETO ASIGNADO | DISPONIBILIDAD | DELEGADO (SI AUSENTE) | ACCIONES`
- Si `DISPONIBILIDAD = ☐ (Ausente)`, mostrar selector de Delegado.

**Reglas de negocio:**
- **Borrado lógico** si tiene FK activas (no DELETE físico).
- Lógica de enrutamiento: el sistema consulta esta matriz en el Paso 4 del flujo.

**Endpoints backend:**
- `GET/POST/PATCH /api/v1/tipos-documento` (CRUD)
- `GET/POST/PATCH /api/v1/estados` (CRUD) ← **NUEVO endpoint, no estaba en plan**
- `GET/POST/PATCH /api/v1/matriz-enrutamiento-eto` (CRUD)

---

### US-9.04 — Tab "Plantillas de Notificación"

**Estructura UI:**
- **Lista lateral** de 6 plantillas: `Nueva Tarea Asignada`, `Alerta de Vencimiento`, `Documento Aprobado`, `Documento Observado`, `Evaluación Pendiente`, `Auto-delegación Activada`.
- **Editor Rich Text** del cuerpo del correo seleccionado.
- **Panel "Etiquetas Disponibles"**: `{{CODIGO}}`, `{{TITULO}}`, `{{USUARIO}}`, `{{FECHA_LIMITE}}`, `{{ETAPA}}`, `{{LINK}}`, `{{GERENCIA}}`, `{{OBSERVACION}}`.
- **Input de Asunto** con variables entre corchetes: `[COFAR - SGD] Nueva tarea asignada: [{{CODIGO}}] — [{{TITULO}}]`.
- Botón **"Previsualizar"** → modal con datos de prueba inyectados.
- Botón **"Guardar Plantilla"**.

**Reglas de negocio:**
- Motor Jinja2 o Handlebars para reemplazo de variables antes del envío SMTP.

**Endpoint backend:** `GET/POST/PATCH /api/v1/email-templates` (CRUD, con `cuerpo_html` + `variables_json`).

**Nota:** el Excel de MATRICES tiene 5 plantillas; el PDF oficial menciona **6** (incluye "Auto-delegación Activada"). Usar las 6 del PDF.

---

### US-9.05 — Tab "Gestión de Usuarios"

**Estructura UI:**
- Banner: *"Panel de Control de Usuarios — Sincronizado desde AD/LDAP"* + indicador "Última sincronización hace X min."
- **KPIs superiores:** `Usuarios Totales | Activos | En Vacaciones | Rol ETO | Administradores`.
- **Filtros:** buscar por nombre/área, todos los roles, todos los estados.
- Botones: **"Limpiar"**, **"Sincronizar"**, **"Exportar"** (CSV/Excel).
- **Tabla principal de usuarios:** `Colaborador (avatar + nombre + username) | Rol | Área | Delegado (avatar) | Vacaciones (toggle) | Acciones (Editar)`.
- **Override manual de Vacaciones** — toggle on/off por usuario (para emergencias).
- **Exportar a Excel/CSV** — botón adicional.

**Reglas de negocio:**
- Lista desde BD local (sincronizada con AD).
- Override manual: actualizar `usuarios.ausente` y `estado_delegacion`.

**Endpoints backend:**
- `GET /api/v1/usuarios?filtros...` (✅ ya existe, tarea #10 del plan original)
- `PATCH /api/v1/usuarios/{id}` (actualizar rol, ausente, etc.) ← **NUEVO endpoint**
- `POST /api/v1/usuarios/sync-ad` (✅ ya existe)
- `GET /api/v1/usuarios/export?format=csv|excel` (export) ← **NUEVO endpoint**
- `POST /api/v1/admin/asignar-roles-desde-matriz` (tarea #12)

---

### US-9.06 — Tab "Gerencias y Áreas"

**Estructura UI:**
- Banner: *"Esta estructura alimenta los desplegables de Gerencia/Área del formulario de solicitud (US-2.02) y el Árbol de Difusión de Outlook (US-2.03)."*
- **Panel izquierdo — "Gerencias registradas"** (con botón "+ Nueva"): lista de gerencias con conteo de áreas y código.
- **Panel derecho — Gerencia seleccionada:**
  - Botones **"Editar"**, **"Eliminar"**
  - Sub-tarjeta **"Áreas / Sub-unidades"** (con botón "+ Nueva Área") y tabla `NOMBRE | CÓDIGO | ESTADO | ACCIONES`
  - Advertencia si hay documentos vinculados: *"Será ocultada de las nuevas solicitudes, pero se mantendrá en el historial para fines de auditoría"*

**Operaciones especiales (NO estaban en mi plan original):**
1. **Mover** un Área entre Gerencias.
2. **Promover** un Área a Gerencia (sin crear registro nuevo, solo cambiar `parent_id` a null).
3. **Borrado lógico** (UPDATE estado='Inactivo') si tiene FK activas.

**Reglas de negocio:**
- Migración jerárquica: al promover, NO crear registro nuevo, solo actualizar `parent_id` del existente.
- Refrescar caché del sistema tras cualquier cambio.

**Endpoints backend:**
- `GET/POST/PATCH /api/v1/gerencias` (CRUD)
- `GET/POST/PATCH /api/v1/areas` (CRUD)
- `POST /api/v1/areas/{id}/mover` (cambiar gerencia_id) ← **NUEVO**
- `POST /api/v1/areas/{id}/promover-a-gerencia` ← **NUEVO**
- `DELETE /api/v1/areas/{id}` (borrado lógico) ← **NUEVO**
- `DELETE /api/v1/gerencias/{id}` (borrado lógico) ← **NUEVO**

---

## 📊 Inventario completo de archivos (en `docs/Diagramas_Matrices/MATRICES/`)

| # | Archivo | Formato | Tamaño | Tab destino |
|---|---|---|---|---|
| 1 | `GERENCIAS, AREAS Y SIGLAS.xlsx` | xlsx | 9.8 KB | Gerencias y Áreas (US-9.06) |
| 2 | `TIPOS DE DOCUMENTO, CÓDIGO Y VIGENCIA.xlsx` | xlsx | 8.5 KB | Diccionarios y Enrutamiento (US-9.03) |
| 3 | `LIMITE ARCHIVOS.xlsx` | xlsx | 7.7 KB | Restricciones (US-9.02) |
| 4 | `MAXIMA DESCARGA DE EDITABLES.xlsx` | xlsx | 8.4 KB | Restricciones (US-9.02) |
| 5 | `PLAZOS PARA LA EJECUCIÓN DE TAREAS.xlsx` | xlsx | 10.8 KB | Tiempos y SLAs (US-9.01) |
| 6 | `ASIGNACION AUTOMATICA ANALISTAS ETO.xlsx` | xlsx | 8.0 KB | Diccionarios y Enrutamiento (US-9.03) |
| 7 | `PLANTILLAS DE NOTIFICACION.docx` | docx | 23 KB | Plantillas de Notificación (US-9.04) |
| 8 | `USUARIOS EXISTENTES A ABRIL.xlsx` | xlsx | 50.2 KB | Gestión de Usuarios (US-9.05) |
| — | `REPORTES GRAFICOS.xlsx` | xlsx | 180.7 KB | (R6, fuera de alcance R1) |

**Total R1:** 8 archivos → 6 tabs distintas → **6 US** (US-9.01 a US-9.06) del PDF oficial.

---

## 🔗 Mapeo archivo → tab → US oficial → endpoint → tarea

### 1. `GERENCIAS, AREAS Y SIGLAS.xlsx` → Tab "Gerencias y Áreas" → **US-9.06**

**Datos:** 10 gerencias + 49 áreas con sigla (CAL, PLA, RRH, ADM-FIN, COM, LOG, OPS, AUD, TER, GEN). Una fila por área con su sigla.

**Endpoints backend necesarios:**
- `GET/POST/PATCH /api/v1/gerencias`
- `GET/POST/PATCH /api/v1/areas`
- `POST /api/v1/areas/{id}/mover` (entre gerencias)
- `POST /api/v1/areas/{id}/promover-a-gerencia`
- `DELETE /api/v1/areas/{id}` (lógico)
- `DELETE /api/v1/gerencias/{id}` (lógico)

**Seed script:** `backend/scripts/seed_organizacion.py`.

**Tareas en el plan:** **#3 + #4 (CRUD básico) + #9d (operaciones especiales mover/promover)**.

---

### 2. `TIPOS DE DOCUMENTO, CÓDIGO Y VIGENCIA.xlsx` → Tab "Diccionarios y Enrutamiento" → **US-9.03 (sub-tarjeta 1)**

**Datos:** 13 tipos (METODOLOGÍA, MANUAL DE FUNCIONES, POLÍTICA, PLAN, PROCEDIMIENTO, INSTRUCTIVO, INSTRUCTIVO TÉCNICO, ESPECIFICACIÓN, PROTOCOLO, MANUAL DE PROCESO, MANUAL, MANUALES DE USUARIO, FICHA DE CARACTERIZACIÓN) con código 1-14 y vigencia.

⚠️ INSTRUCTIVO e INSTRUCTIVO TÉCNICO comparten código 6. La PK es interna, `codigo` es campo lógico.

**Endpoint backend:** `GET/POST/PATCH /api/v1/tipos-documento` (con `max_descargas_dia` integrado).

**Tarea en el plan:** **#9b** ✅ NUEVA.

---

### 3. `LIMITE ARCHIVOS.xlsx` + `MAXIMA DESCARGA DE EDITABLES.xlsx` → Tab "Restricciones" → **US-9.02**

**Datos:** 20 archivos máx, 20MB por archivo, max_descargas_dia por tipo.

**Endpoints backend:**
- `GET/POST/PATCH /api/v1/configuracion-global` (claves de archivos)
- `/api/v1/tipos-documento` (max_descargas_dia por tipo)

**Tarea en el plan:** **#5 (configuracion-global)** + #9b (tipos-documento).

---

### 4. `PLAZOS PARA LA EJECUCIÓN DE TAREAS.xlsx` → Tab "Tiempos y SLAs" → **US-9.01**

**Datos:** plazo_revision/aprobacion = 10 hábiles O 15 calendario; plazo_lectura = 30 cal.

**Endpoints backend:**
- `GET/POST/PATCH /api/v1/configuracion-global` (claves de plazos + semáforo)
- `GET/POST/PATCH /api/v1/feriados`

**Tareas en el plan:** **#5 + #6** ✅ INCLUIDAS.

---

### 5. `ASIGNACION AUTOMATICA ANALISTAS ETO.xlsx` → Tab "Diccionarios y Enrutamiento" → **US-9.03 (sub-tarjeta 3)**

**Datos:** 10 gerencias con su ETO (Aracely/Cecilia).

**Endpoint backend:** `GET/POST/PATCH /api/v1/matriz-enrutamiento-eto`.

**Tarea en el plan:** **#8** ✅ INCLUIDA.

---

### 6. `PLANTILLAS DE NOTIFICACION.docx` → Tab "Plantillas de Notificación" → **US-9.04**

**Datos:** 5 plantillas en el .docx (REVISIÓN, APROBACIÓN, CORRECCIÓN, LECTURA, EVALUACIÓN). Pero el PDF oficial menciona **6** (incluye `Auto-delegación Activada`).

**Endpoint backend:** `GET/POST/PATCH /api/v1/email-templates` con motor Jinja2.

**Tarea en el plan:** **#7** ✅ INCLUIDA (agregar la 6ta plantilla `auto-delegacion-activada` desde el PDF).

---

### 7. `USUARIOS EXISTENTES A ABRIL.xlsx` → Tab "Gestión de Usuarios" → **US-9.05**

**Datos:** 730 usuarios con rol/módulos/delegados.

**Endpoints backend:**
- `POST /api/v1/admin/asignar-roles-desde-matriz` (tarea #12)
- `GET /api/v1/usuarios/export?format=csv|excel` (NUEVO)

**Tarea en el plan:** **#12** ✅ INCLUIDA + #9e (export a Excel/CSV).

---

## 📋 Plan de tareas REVISADO (15 tareas, no 13)

| # | Tarea | Endpoint | Archivo/EPICA | US |
|---|---|---|---|---|
| 1 | `frontend/src/utils/api.js` | — | — | (base) |
| 2 | `seed_organizacion.py` | — | GERENCIAS, AREAS Y SIGLAS | 9.06 |
| 3 | CRUD gerencias | `/api/v1/gerencias` | GERENCIAS, AREAS Y SIGLAS | 9.06 |
| 4 | CRUD areas | `/api/v1/areas` | GERENCIAS, AREAS Y SIGLAS | 9.06 |
| 5 | CRUD configuracion-global | `/api/v1/configuracion-global` | LIMITE ARCHIVOS + PLAZOS | 9.01, 9.02 |
| 6 | CRUD feriados | `/api/v1/feriados` | (calendario Bolivia) | 9.01 |
| 7 | CRUD email-templates | `/api/v1/email-templates` | PLANTILLAS + EPICA 9.04 (6 plantillas) | 9.04 |
| 8 | CRUD matriz-enrutamiento-eto | `/api/v1/matriz-enrutamiento-eto` | ASIGNACION ETO | 9.03 |
| 9 | GET audit-log | `/api/v1/audit-log` | (generado) | 9.05 |
| **9b** | **CRUD tipos-documento** | `/api/v1/tipos-documento` | TIPOS DE DOCUMENTO + MAXIMA DESCARGA | 9.03 |
| **9c** | **CRUD estados** | `/api/v1/estados` | (sub-tarjeta 2 de US-9.03) | 9.03 |
| **9d** | **Operaciones jerárquicas áreas** | `mover`, `promover-a-gerencia`, `DELETE lógico` | (operaciones de US-9.06) | 9.06 |
| **9e** | **Override vacaciones + export** | `PATCH /usuarios/{id}`, `GET /usuarios/export` | (override de US-9.05) | 9.05 |
| 10 | Refactor `Parametrizacion.js` | — | — | 9.01-9.06 |
| 11 | Tests pytest | — | — | 9.01-9.06 |
| 12 | Asignación masiva desde matriz | `/api/v1/admin/asignar-roles-desde-matriz` | USUARIOS EXISTENTES A ABRIL | 9.05 |

**Total:** 15 tareas (en lugar de 11 o 12). Las nuevas son: 9b, 9c, 9d, 9e.

**⏱️ Tiempo estimado:** ~10-12 horas de trabajo concentrado (2 sesiones largas).

---

## 🧮 Resumen de seeds que se necesitan (8 scripts Python)

1. `seed_organizacion.py` — 10 gerencias + 49 áreas (US-9.06)
2. `seed_tipos_documento.py` — 13 tipos con `max_descargas_dia` (US-9.03)
3. `seed_feriados.py` — calendario Bolivia 2026 (US-9.01)
4. `seed_email_templates.py` — **6 plantillas** (las 5 del .docx + `auto-delegacion-activada` del PDF) (US-9.04)
5. `seed_matriz_enrutamiento.py` — 10 filas gerencia-ETO (US-9.03)
6. `seed_roles.py` — 5 roles
7. `seed_modulos.py` — 10 módulos
8. `seed_matriz_abril.py` — 730 usuarios con rol/módulos/delegados (US-9.05, tarea #12)
9. `seed_estados.py` — 5+ estados (Elaboración, Liberación ETO, Revisión Paralela, Finalizado, Anulado) (US-9.03)

Cada seed es **idempotente** (puede correr varias veces sin duplicar) y se loggea cuántos registros creó/actualizó.

---

## ⚠️ Riesgos macro

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | El Excel GERENCIAS tiene filas con "POR CONFIRMAR" en OBSERVACIÓN | Sembrar igual, dejar la obs. en el campo. |
| 2 | El Excel PLAZOS TAREA es ambiguo ("10 hábiles O 15 calendario, lo primero") | Documentar lógica con un test que valide el primero que se cumple. |
| 3 | El Excel TIPOS DOC tiene INSTRUCTIVO e INSTRUCTIVO TÉCNICO con código 6 (duplicado) | Sembrar ambos con PKs distintas, `codigo` es campo lógico. |
| 4 | El Excel USUARIOS no tiene sAMAccountName, solo COFAR | Mapeo por `ad_postal_code = COFAR` (ya validado). |
| 5 | El .docx de PLANTILLAS tiene tildes/UTF-8 mal parseado | Convertir a UTF-8 limpio al sembrar. |
| 6 | El PDF menciona 6 plantillas pero el .docx solo tiene 5 | Sembrar las 5 del .docx, agregar la 6ta (`auto-delegacion-activada`) desde el PDF con contenido stub. |
| 7 | Las operaciones `mover` y `promover` rompen FK si no se manejan en transacción | Hacer TODA la operación de árbol jerárquico en una transacción SQL con savepoints. |
