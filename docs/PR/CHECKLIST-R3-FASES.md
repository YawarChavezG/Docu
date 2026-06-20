# PLAN DE EJECUCIÓN R3 — Fases ordenadas

> **Checklist de implementación para R3 (Workflow de Revisión y Aprobación).**
> **Cada fase termina con: código commiteado + tests PASANDO + docs actualizados.**
> **Rama:** `r3/workflow-revision-aprobacion` (creada desde `r2/wizard-y-version-editable`)
>
> **Estimación total:** 55-65h (14-16 sesiones de 4h)

---

## 🔴 Fase 0: Terminar R2 (lo que falta del wizard)

> **6-8h / 1-2 sesiones. Backend + Frontend.**

### 0.1 Código completo del documento
- [x] Helper `generar_nombre_completo(codigo, titulo, version)` en backend
- [x] Actualizar display en wizard: `CC-7-005 PROCEDIMIENTO DE MUESTREO V00`
- [x] Actualizar display en Bandeja, Lista Maestra, Consultas
- [x] Tests del helper (5 tests en test_correlativo_service.py)

### 0.2 Actualización documental
- [x] Backend: agregar `documento_flujo.documento_actualizado_id` (FK)
- [x] Frontend: wizard paso 1 — si `tipo_solicitud=ACTUALIZACION`, mostrar selector de documentos existentes filtrados por (área, tipo_documento)
- [x] Frontend: al seleccionar documento, autocompletar código, título, versión anterior
- [x] Backend: calcular `version_snapshot = version_anterior + 1`
- [x] Tests: 4 tests en test_documentos_enviar.py

### 0.3 Validación de carátula (lectura de .docx)
- [x] Backend: instalar `python-docx` para leer metadatos del .docx
- [x] Backend: al subir archivo PRINCIPAL, leer página 1 del .docx
- [x] Backend: extraer título, código, versión de la carátula
- [x] Backend: comparar con BD → advertencia si no coincide
- [x] Frontend: mostrar toast de advertencia sin bloquear
- [x] Tests: 6 tests en test_caratula_service.py

### 0.4 Código de formularios (-F01)
- [x] Backend: crear tabla `documento_formularios`
- [x] Backend: `formatear_codigo_formulario` y `siguiente_correlativo_formulario` en correlativo_service
- [x] Frontend: al subir formularios en wizard, generar código `-F01`, `-F02`...
- [x] Tests: 3 tests en test_documentos_archivos.py

### 0.5 Fix vigencia del wizard
- [x] Frontend: `AprobacionDocumento.js` init() — leer `tipos_documento.periodo_vigencia` al seleccionar tipo
- [x] Frontend: mostrar `periodo_vigencia` real o "Indefinido"
- [x] Verificar con Chrome MCP: crear documento con tipo indefinido → debe mostrar "Indefinido" (validado con MANUAL_FUNCIONES id=2)

### 0.6 Flujo post-wizard: va a ETO primero
- [x] Backend: `envio_service.py` — al firmar, transiciona a LIBERACION_ETO (no directo a EN_REVISION)
- [x] Backend: nuevo endpoint `POST /documentos/{id}/liberar` (ETO lo llama para pasar a EN_REVISION)
- [x] Agregar estado `LIBERACION_ETO` al enum `EstatusDocumento` (migración Alembic r3_liberacion_eto_s36)
- [x] Tests: 3 tests en test_documentos_enviar.py
- [ ] Pendiente Fase 1: crear tareas reales para ETO segun `matriz_enrutamiento_eto` (no en alcance de Fase 0)

---

## 🟡 Fase 1: Modelos R3 (nuevas tablas)

> **6-8h / 2-3 sesiones. Solo Backend.**

- [x] Crear tabla `tareas` con índices
- [x] Crear tabla `bitacora_timeline` (append-only)
- [x] Crear tabla `notificaciones` con tracking de lectura
- [x] Crear tabla `documento_reemplazos`
- [x] Crear tabla `documento_alcance_difusion`
- [x] Crear tabla `tarea_observaciones`
- [x] Crear tabla `procesos` (catálogo, seed con 10 valores genéricos)
- [x] Extender enum `TipoTarea`: agregar LIBERACION, CORRECCION
- [x] Agregar columna `usa_dias_habiles` a `semaforizacion_tarea`
- [x] Valores de semáforo: REVISION/APROBACION=7/12/15 (días naturales ≈ 10 hábiles), LIBERACION=999 (ETO sin plazo), CORRECCION=7/12/15
- [x] Migración Alembic (autogenerate + revisión manual)
- [x] Tests: 5-6 tests de cada nuevo modelo (creación, índices, constraints) — **51 tests nuevos**

---

### Bonus — Mejoras wizard (US-2.02, US-2.04) + Admin plantillas
- [x] Searchable dropdown "Documento a actualizar" (US-2.02)
- [x] Formularios drag-reorder + título editable + codificación -F01/-F02 (US-2.04)
- [x] Extracción de título real desde .xlsx/.docx al subir (POST /extraer-titulo-formulario)
- [x] Dropdowns visuales custom (Tipo, Gerencia, Area, Solicitud, Eval, Lectura, Reemplazo)
- [x] Checkboxes custom en árbol de difusión
- [x] Searchable dropdowns para Revisores y Aprobadores
- [x] Autocomplete en vivo para Códigos de reemplazo (vía /documentos/buscar)
- [x] Tabla `plantillas` en BD (soft-delete, audit_log, storage_path)
- [x] CRUD plantillas desde Parametrización > Restricciones (subir, renombrar, eliminar)
- [x] ConfirmDeleteModal en vez de confirm() nativo
- [x] Tabla `documento_formularios` (Fase 0.4)
- [x] Validación de carátula .docx (Fase 0.3)
- [x] Columna `usa_dias_habiles` en semaforizacion_tarea
- [x] Valores semáforo corregidos: 7/12/15 naturales, LIBERACION=999
- [x] Contexto AMBAS eliminado del modelo Estado

## 🟡 Fase 2: Servicios core R3

> **6h / 2 sesiones. Solo Backend.**

- [ ] `tarea_service.py` — crear_tarea, completar_tarea, rechazar_tarea, reasignar_tarea
- [ ] `timeline_service.py` — escribir_bitacora (append-only)
- [ ] `notificacion_service.py` — crear_notificacion, marcar_leida
- [ ] Integrar con `envio_service.py`:
  - `enviar_a_liberacion()` → crear tarea LIBERACION para el ETO
  - `completar_tarea(tipo=LIBERACION)` → crear tareas REVISION para cada revisor
- [ ] Helper `calcular_color_sla(tarea)` — días hábiles vs feriados
- [ ] Tests: 8-10 tests de servicios

---

## 🟡 Fase 3: Cron job de timeout (US-3.06)

> **4h / 1 sesión. Solo Backend.**

- [ ] Tarea Celery `reasignar_tareas_vencidas` a las 23:59
- [ ] Lógica: encontrar tareas PENDIENTE con fecha_vencimiento < NOW()
- [ ] Reasignar al delegado (usuarios.delegado_id) o al jefe (areas.jefe_id) o a ETO
- [ ] Máximo 3 intentos de reasignación
- [ ] Bitácora: REASIGNADO_AUTO (gris)
- [ ] Notificación al usuario original y al delegado
- [ ] Tests: 4-5 tests del cron (mock de datetime.now)

---

## 🟠 Fase 4: Endpoints API R3

> **8-10h / 3 sesiones. Backend.**

### 4.1 Endpoints de tareas
- [ ] `GET /tareas?usuario_id=X&estado=PENDIENTE` — bandeja del usuario
- [ ] `POST /tareas/{id}/aprobar` — completa tarea + timeline + verificar si todas completas
- [ ] `POST /tareas/{id}/rechazar` — rechaza + observación obligatoria + timeline
- [ ] `GET /tareas/{id}` — detalle de una tarea

### 4.2 Endpoints de bandeja (refactor)
- [ ] `GET /bandeja?tipo=elaboracion` — desde `tareas`, no de JSONB
- [ ] `GET /bandeja?tipo=revision` — mismo
- [ ] `GET /bandeja?tipo=aprobacion` — mismo
- [ ] `GET /bandeja?tipo=liberacion` — mismo

### 4.3 Endpoints de notificaciones
- [ ] `GET /notificaciones` — paginado, filtro por leída
- [ ] `POST /notificaciones/{id}/leer` — marca como leída
- [ ] `GET /notificaciones/no-leidas/count` — para el badge de la campana

### 4.4 Endpoint de bitácora
- [ ] `GET /bitacora?documento_flujo_id=X` — timeline del documento

### 4.5 Tests
- [ ] 15-20 tests de endpoints

---

## 🔴 Fase 5: Migración de datos (JSONB → N:M)

> **3h / 1 sesión. Backend.**

- [ ] Script `migrar_jsonb_a_tablas_r3.py` idempotente
- [ ] Migrar `revisor_ids` → `tareas` (tipo REVISION)
- [ ] Migrar `aprobador_ids` → `tareas` (tipo APROBACION)
- [ ] Migrar `reemplaza_documento_ids` → `documento_reemplazos`
- [ ] Migrar `alcance_difusion_ids` → `documento_alcance_difusion`
- [ ] Migrar `audit_log` de documentos → `bitacora_timeline` (opcional)
- [ ] Validar en DES con `restore_clean_state.bat` + seed documentos
- [ ] Actualizar `seed_documentos.py` para crear tareas
- [ ] Tests: 3-4 tests de migración

---

## 🔴 Fase 6: Frontend — Refactor de páginas (datos mock → API real)

> **12-16h / 4 sesiones. Frontend + Chrome MCP.**

### 6.1 Bandeja.js (175 líneas)
- [ ] Reemplazar import de `data/tasks.js` por `const res = await apiGet('/tareas?usuario_id=X&estado=PENDIENTE')`
- [ ] SLA semáforo en runtime (verde/amarillo/rojo según días hábiles)
- [ ] Vincular "Atender →" con la ruta correcta según tipo de tarea

### 6.2 LiberacionDetalle.js (375 líneas)
- [ ] Consumir `GET /tareas/{id}` + `POST /tareas/{id}/aprobar`
- [ ] Verificar reemplazos y árbol de difusión

### 6.3 Revision.js + AprobacionFinal.js + Correccion.js (3 páginas)
- [ ] Consumir `POST /tareas/{id}/aprobar`
- [ ] Consumir `POST /tareas/{id}/rechazar` con observación obligatoria

### 6.4 ListaMaestra.js (333 líneas)
- [ ] Consumir `GET /documentos` real (hoy usa mock `documents.js`)

### 6.5 ConsultaDocumentos.js (372 líneas)
- [ ] Consumir `GET /documentos?q=` con timeline desde `GET /bitacora`

### 6.6 Notificaciones (store + panel)
- [ ] Store `notificaciones.js` → consumir `GET /notificaciones/no-leidas/count`
- [ ] Dropdown → consumir `GET /notificaciones`
- [ ] Al hacer clic → `POST /notificaciones/{id}/leer`

### 6.7 Validación con Chrome MCP
- [ ] Login como cada rol: tareas correctas en bandeja
- [ ] Revisor: ver solo tareas REVISION
- [ ] ETO: ver solo tareas LIBERACION
- [ ] Admin: ver todo
- [ ] Crear documento → Liberar → Revisar → Aprobar → Publicar → Ver en Lista Maestra

---

## 🟢 Fase 7: Tests de integración + limpieza

> **6-8h / 2 sesiones.**

- [ ] Tests unitarios de todos los servicios nuevos
- [ ] Tests de integración de todos los endpoints nuevos
- [ ] Tests del cron job (mock de datetime)
- [ ] Tests de migración (idempotencia)
- [ ] 228 tests anteriores siguen PASANDO (sin regresiones)
- [ ] Limpiar `frontend/src/data/` — archivos mock que ya no se usan
- [ ] Actualizar `RADIOGRAFIA-TOTAL.md`, `ESTADO.md`, `BITACORA.md`, `DECISIONES.md`

---

## Dependencias entre fases

```
Fase 0 (R2) ──→ Fase 1 (Modelos) ──→ Fase 2 (Servicios) ──→ Fase 4 (Endpoints) ──→ Fase 6 (Frontend)
                      │                      │                       │
                      ↓                      ↓                       ↓
                   Fase 5 (Migración)    Fase 3 (Cron)           Fase 7 (Tests)
```

- **Fase 0 es obligatoria** antes de cualquier otra (sin wizard completo, no hay datos correctos para R3)
- **Fase 1 y 5** se pueden hacer en paralelo con Fase 2 (los modelos nuevos no rompen los viejos)
- **Fase 6** requiere Fase 4 (los endpoints deben existir)
- **Fase 7** cierra todo (tests finales + limpieza)

---

## Rama de trabajo

```bash
git checkout r2/wizard-y-version-editable
git checkout -b r3/workflow-revision-aprobacion
# ... implementar fase por fase ...
# Cada fase termina con: commit + push + tests PASANDO
```
