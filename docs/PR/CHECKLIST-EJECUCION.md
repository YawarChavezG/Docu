# CHECKLIST DE EJECUCIÓN — COFAR SGD

> **Documento VIVO.** Se actualiza después de cada tarea completada.
> Es la fuente de verdad del progreso actual. Antes de cada sesión, leer esto primero.
>
> **Basado en:** `PLAN-MAESTRO-IMPLEMENTACION.md`
> **Última actualización:** 2026-06-20

---

## Leyenda

| Símbolo | Significado |
|---------|-------------|
| ⬜ | Pendiente |
| 🔵 | En progreso |
| ✅ | Completado |
| ❌ | Bloqueado / Cancelado |
| 🟡 | Depende de otra tarea |

---

## Fase 0: Correcciones Inmediatas (Hotfixes)

> Rama: `r3/workflow-revision-aprobacion`
> Tests: 337 PASS
> Estado general: 🔵 EN PROGRESO

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 0.1 | Separador versión: `/` → ` ` V | ✅ | 2026-06-20 | 1df60db | `formatear_codigo_completo()` + displays + tests |
| 0.2 | Agregar credenciales MS Graph + SMTP al `.env` y `config.py` | ✅ | 2026-06-20 | 0ea4508 | Incluye SHAREPOINT_SITE_ID + fix entrypoint CRLF + POSTGRES_HOST |
| 0.3 | Ocultar LIBERACION de semaforización UI | ✅ | 2026-06-20 | cca102a | Filtrar en endpoint GET |
| 0.4 | Filtrar usuarios AUSENTES de dropdowns revisores/aprobadores | ✅ | 2026-06-20 | 5aad175 | Backend + frontend |
| **0.x** | **CIERRE DE FASE 0** | ✅ | 2026-06-20 | 5aad175 | 4/4 tareas completadas |

---

## Fase 1: Almacenamiento y Nomenclatura Definitiva

> Prerrequisito: Fase 0 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 1.1 | Nueva estructura de directorios en storage | 🔵 EN PROGRESO | — | — | `{gerencia}/{area}/{codigo}/V{version}/` |
| 1.2 | Contador de descargas de plantillas (métrica) | ⬜ | — | — | Solo KPI, sin límite |

---

## Fase 2: Control de Descargas de Editables

> Prerrequisito: Fase 0 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 2.1 | Tabla/conteo diario de descargas | ⬜ | — | — | `descargas_contador` o `audit_log` |
| 2.2 | Validación límite en endpoint + VersionEditable | ⬜ | — | — | 1/día normal, 10/día excepción |

---

## Fase 3: Catálogo de Procesos

> Prerrequisito: Fase 0 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 3.1 | Columna `codigo` en tabla `procesos` + seed | ⬜ | — | — | VARCHAR(4) UNIQUE |
| 3.2 | Selector de Proceso en LiberacionDetalle.js | ⬜ | — | — | Antes de "Decisión de Liberación" |

---

## Fase 4: Timeline / Bitácora del Flujo Documental

> Prerrequisito: Fase 1 ✅, Fase 0 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 4.1 | Crear `timeline_service.py` | ⬜ | — | — | Append-only |
| 4.2 | Integrar timeline en cada etapa del flujo | ⬜ | — | — | Wizard, liberación, aprobación, etc. |
| 4.3 | Endpoint GET /bitacora | ⬜ | — | — | Para el frontend |
| 4.4 | Refactor timeline visual en Revision.js | ⬜ | — | — | Datos reales vs mock |

---

## Fase 5: Servicios Core del Workflow (R3 Fase 2)

> Prerrequisito: Fase 4 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 5.1 | Crear `tarea_service.py` | ⬜ | — | — | CRUD + propagación |
| 5.2 | Endpoints REST de tareas | ⬜ | — | — | POST aprobar/rechazar/reasignar |
| 5.3 | Endpoints de notificaciones | ⬜ | — | — | GET count, POST leer |
| 5.4 | Integrar `envio_service.py` con tareas | ⬜ | — | — | Fan-out al liberar |

---

## Fase 6: Integración Flujo ETO → Revisores → Aprobadores

> Prerrequisito: Fase 5 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 6.1 | Refactor LiberacionDetalle.js | ⬜ | — | — | Datos reales + SharePoint |
| 6.2 | Refactor Bandeja.js | ⬜ | — | — | Tareas reales vs mock |
| 6.3 | Refactor Revision.js | ⬜ | — | — | Timeline real + botones |
| 6.4 | Refactor AprobacionFinal.js | ⬜ | — | — | Consumir API real |
| 6.5 | Refactor Correccion.js | ⬜ | — | — | Bypass directo |
| 6.6 | Refactor notificaciones.js store | ⬜ | — | — | API real vs mock |

---

## Fase 7: Delegación y Timeout

> Prerrequisito: Fase 5 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 7.1 | Cron `reasignar_tareas_vencidas` | ⬜ | — | — | 23:59 daily |
| 7.2 | Delegación por desvinculación | ⬜ | — | — | En sync_ad_service |
| 7.3 | Delegación por vacaciones | ⬜ | — | — | En ausencias.py |

---

## Fase 8: Sistema de Notificaciones por Correo

> Prerrequisito: Fase 5 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 8.1 | Configurar SMTP en `.env` (activar) | ⬜ | — | — | `SMTP_ENABLED=true` |
| 8.2 | Crear `email_service.py` | ⬜ | — | — | s mtplib + plantillas |
| 8.3 | Integrar en cada etapa del flujo | ⬜ | — | — | Asignación, liberación, etc. |

---

## Fase 9: Integración Microsoft Graph / SharePoint

> Prerrequisito: Fase 1 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 9.1 | Implementar SharePointStorage real | ⬜ | — | — | Graph API |
| 9.2 | Guardar enlace SharePoint en BD | ⬜ | — | — | `sharepoint_link` en archivos |

---

## Fase 10: PDF Final, Carátula y Carimbo

> Prerrequisito: Fase 6 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 10.1 | Evaluar e instalar librería PDF | ⬜ | — | — | WeasyPrint / ReportLab |
| 10.2 | Implementar `pdf_service.py` | ⬜ | — | — | Carátula + carimbo |

---

## Fase 11: Limpieza de Datos Mock y Migraciones

> Prerrequisito: Fase 6 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 11.1 | Reuso de correlativos (tabla independiente) | ⬜ | — | — | Para cancelación de flujos |
| 11.2 | Limpiar archivos mock de `frontend/src/data/` | ⬜ | — | — | 16 archivos |

---

## Fase 12: Módulo de Reasignación ETO

> Prerrequisito: Fase 7 ✅
> Estado general: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Commit | Notas |
|---|-------|--------|-------|--------|-------|
| 12.1 | Backend: endpoint reasignación ETO | ⬜ | — | — | Firm a 2FA requerida |
| 12.2 | Frontend: botón reasignar en timeline | ⬜ | — | — | Consultar Documentos |

---

## Fase Transversal A: Seguridad y Hardening

> Naturaleza: Transversal — se implementa dentro de cada fase.
> Estado: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Notas |
|---|-------|--------|-------|-------|
| A.1 | Path traversal prevention | ⬜ | — | Aplica a Fase 1 |
| A.2 | Validación real de MIME (libmagic) | ⬜ | — | Aplica a Fase 1 |
| A.3 | Rate limiting real | ⬜ | — | Endpoints de descarga |
| A.4 | Log de seguridad | ⬜ | — | Intentos sospechosos |

---

## Fase Transversal B: Performance y Escalabilidad

> Naturaleza: Transversal.
> Estado: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Notas |
|---|-------|--------|-------|-------|
| B.1 | Índices para tablas R3 | ⬜ | — | Verificar existentes |
| B.2 | Cache de feriados en Redis | ⬜ | — | Para cálculo SLA |
| B.3 | Paginación con cursor | ⬜ | — | Para bandejas grandes |

---

## Fase Transversal C: Monitoreo y Operaciones

> Naturaleza: Transversal.
> Estado: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Notas |
|---|-------|--------|-------|-------|
| C.1 | Health checks para nuevos servicios | ⬜ | — | QAS compose |
| C.2 | Script backup de documentos | ⬜ | — | Almacenamiento físico |
| C.3 | Script de rollback por fase | ⬜ | — | Template genérico |
| C.4 | Logs estructurados (JSON) para cron | ⬜ | — | Monitoreo |

---

## Fase Transversal D: Testing Integral y Migración

> Naturaleza: Transversal.
> Estado: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Notas |
|---|-------|--------|-------|-------|
| D.1 | Migrar datos existentes a R3 | ⬜ | — | 10 seed docs → tareas + timeline |
| D.2 | Actualizar seed_documentos.py | ⬜ | — | Crear tareas en seed |
| D.3 | Data de prueba para testing | ⬜ | — | Documentos en varios estados |
| D.4 | Suite de tests por fase | ⬜ | — | +5-10 tests por fase |

---

## Fase Transversal E: Documentación y API

> Naturaleza: Transversal.
> Estado: ⬜ PENDIENTE

| # | Tarea | Estado | Fecha | Notas |
|---|-------|--------|-------|-------|
| E.1 | Actualizar `.env.example` | ⬜ | — | Nuevas variables |
| E.2 | Actualizar RADIOGRAFIA-TOTAL.md | ⬜ | — | Checklist post-fase |
| E.3 | OpenAPI docs | ⬜ | — | FastAPI auto |
| E.4 | Mantenimiento del PLAN MAESTRO | ⬜ | — | Marcar fases completadas |

---

## Resumen Global

| Fase | Estado | % |
|------|--------|---|
| Fase 0: Hotfixes | 🔵 EN PROGRESO | 0% |
| Fase 1: Storage | ⬜ Pendiente | 0% |
| Fase 2: Control Descargas | ⬜ Pendiente | 0% |
| Fase 3: Procesos | ⬜ Pendiente | 0% |
| Fase 4: Timeline | ⬜ Pendiente | 0% |
| Fase 5: Servicios Core | ⬜ Pendiente | 0% |
| Fase 6: Flujo Completo | ⬜ Pendiente | 0% |
| Fase 7: Delegación | ⬜ Pendiente | 0% |
| Fase 8: Notificaciones | ⬜ Pendiente | 0% |
| Fase 9: SharePoint | ⬜ Pendiente | 0% |
| Fase 10: PDF | ⬜ Pendiente | 0% |
| Fase 11: Migraciones | ⬜ Pendiente | 0% |
| Fase 12: Reasignación ETO | ⬜ Pendiente | 0% |
| T-A: Seguridad | ⬜ Pendiente | 0% |
| T-B: Performance | ⬜ Pendiente | 0% |
| T-C: Monitoreo | ⬜ Pendiente | 0% |
| T-D: Testing | ⬜ Pendiente | 0% |
| T-E: Documentación | ⬜ Pendiente | 0% |
| **TOTAL** | | **0%** |

---

## Bitácora de Avance

### Sesión 1 — 2026-06-20
- Creación del PLAN MAESTRO DE IMPLEMENTACIÓN (17 fases)
- Creación del CHECKLIST DE EJECUCIÓN (este documento)
- Pendiente: inicio de Fase 0 — tarea 0.1 (separador versión)
