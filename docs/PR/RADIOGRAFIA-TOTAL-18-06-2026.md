# RADIOGRAFÍA TOTAL — COFAR SGD (2026-06-18)

> **Documento único de contexto para cualquier IA o developer.** Captura el estado real de: frontend, backend, BD, Docker, scripts, tests, pendientes, y deuda técnica. Para ser leído ANTES de cualquier sesión de trabajo.
> **Última actualización:** 2026-06-18 (sesión 30 — B7 P0 RESUELTO)

---

## 1. Stack verificada

| Componente | Versión | Ubicación |
|---|---|---|
| Python | 3.12-slim-bookworm | `backend/` |
| FastAPI | 0.137.0 | PyPI |
| SQLAlchemy | 2.0.50 async | PyPI |
| PostgreSQL | 16-alpine | Docker (host:25432) |
| Redis | 7-alpine | Docker (host:26379) |
| Celery | 5.6.3 | Docker (worker + beat) |
| Alpine.js | 3.15.12 | `frontend/` |
| Vite | 8.0.16 | `frontend/` |
| Tailwind | 3.4.19 | `frontend/` |
| Nginx | 1.27-alpine | Docker (host:8080) |

---

## 2. Frontend (86 archivos, ~15K líneas, ~756 KB)

### 2.1 Páginas (29 archivos)

| Archivo | Líneas | Estado | Consume API real? |
|---|---|---|---|
| `Parametrizacion.js` | 2,759 | ✅ Completo (7 tabs) | Sí — `parametrizacionApi.js` |
| `AprobacionDocumento.js` | 677 | 🟡 Wizard 3 pasos OK, flujo R3 pendiente | Sí — `documentosApi.js` |
| `LiberacionDetalle.js` | 375 | ❌ Sin refactor R3 (usa datos mock) | No |
| `ConsultaDocumentos.js` | 372 | ❌ Sin refactor | No |
| `ListaMaestra.js` | 333 | ❌ Sin refactor | No |
| `Bandeja.js` | 175 | ❌ Sin refactor (usa datos mock tasks) | No |
| `Login.js` | 305 | ✅ Funcional | Sí — `auth.js` |
| `VersionEditable.js` | 252 | ✅ Funcional (Issue 10.1 fix) | Sí — `documentosApi.js` |
| `Plantillas.js` | 136 | ✅ Funcional (Issues 9.1, 9.2 fix) | Sí — `plantillasApi.js` |
| `ProfileModal.js` | 570 | ✅ Funcional | Sí — `parametrizacionApi.js` |
| `Revision.js` | 173 | ❌ Sin refactor | No |
| `AprobacionFinal.js` | 165 | ❌ Sin refactor | No |
| `Correccion.js` | 102 | ❌ Sin refactor | No |
| Otras 16 páginas | varias | 🟡 Placeholder/mocks | Parcial |

### 2.2 Componentes (23 archivos)

| Componente | Líneas | Propósito |
|---|---|---|
| `ProfileModal.js` | 570 | Perfil usuario + ausencias + delegado |
| `AuthModal.js` | 149 | Firma 2FA (password verify) |
| `ConfirmImpersonateModal.js` | 146 | Modal impersonate |
| `EditUserModal.js` | 128 | Editar usuario (admin) |
| `Toast.js` | 85 | Sistema de notificaciones |
| `PlantillaEditor.js` | 56 | Editor Tiptap WYSIWYG |
| `ModalBase.js` | 49 | Base reutilizable para modales |
| Otros 16 modales | varios | Confirmaciones, visores, etc. |

### 2.3 Servicios API (3 archivos)

| Archivo | Líneas | Endpoints que consume |
|---|---|---|
| `parametrizacionApi.js` | 189 | `/gerencias`, `/areas`, `/usuarios`, `/roles`, `/tipos-documento`, `/estados`, `/configuracion-global`, `/matriz-enrutamiento-eto`, `/email-templates`, `/feriados`, `/semaforizacion-tarea`, `/audit-log` |
| `documentosApi.js` | 66 | `/documentos/buscar`, `/documentos/preview-codigo`, `/documentos`, `/documentos/{id}/archivos`, `/documentos/{id}/enviar`, `/bandeja` |
| `plantillasApi.js` | 24 | `/plantillas-documentales` |

### 2.4 Stores (4 archivos)

| Store | Líneas | Función |
|---|---|---|
| `auth.js` | 377 | Login/logout/refresh/RBAC/impersonate |
| `notificaciones.js` | 143 | Badge notificaciones + polling |
| `flow.js` | 88 | Estado compartido flujo documental |
| `app.js` | 13 | isLoading, pageTitle |

### 2.5 Data mock legacy (16 archivos, ~1,677 líneas)

> **IMPORTANTE:** Estos archivos son código muerto/mock que algunas páginas AÚN importan. `Parametrizacion.js` ya no los usa (sesión 7), pero `Bandeja.js`, `LiberacionDetalle.js`, `ListaMaestra.js`, `Revision.js`, `AprobacionFinal.js`, `Correccion.js`, etc. sí.

| Archivo | Líneas | Usado por |
|---|---|---|
| `evaluaciones.js` | 246 | Evaluaciones, PreEval |
| `bitacora.js` | 161 | ConsultaDocumentos |
| `copias.js` | 172 | ModuloCopias |
| `gerencias.js` | 150 | Legado (no usado por Parametrizacion) |
| `parametrosSistema.js` | 147 | Legado (no usado por Parametrizacion) |
| `documents.js` | 122 | ListaMaestra |
| `tasks.js` | 92 | Bandeja |
| `plantillas.js` | 30 | Plantillas (ya no usado — reemplazado en sesión 24) |
| Otros 8 archivos | varios | Varias páginas |

### 2.6 Layout

- `AppLayout.js` (487 líneas): sidebar + topbar + banner impersonate + 16 modales globales. 4 configuraciones de navegación por rol.

### 2.7 Diseño System (main.css, 335 líneas)

Tailwind 3.4 + clases utilitarias: badges (7 colores), botones, form inputs, data tables, glassmorphism, KPIs cards, modal overlay, toast, animaciones.

---

## 3. Backend (91 archivos .py)

### 3.1 Routers (19 routers, 87 endpoints)

Router principal `main.py` registra todo bajo prefix `/api/v1`:

| Router | Endpoints | Auth requerida |
|---|---|---|
| `auth.py` | POST `/login`, POST `/logout`, GET `/me`, POST `/verify-password` | Cookie session |
| `usuarios.py` | GET list, GET by id, POST sync-ad, GET sync-status, GET export, PATCH update | ETO/ADMIN |
| `gerencias.py` | GET list, GET by id, POST, PATCH, DELETE | GET=public, muta=ETO/ADMIN |
| `areas.py` | GET list, GET by id, POST, PATCH, DELETE, POST mover, POST promover | GET=public, muta=ETO/ADMIN |
| `documentos.py` | GET buscar, GET preview-codigo, GET by id, GET list, POST, PATCH, POST archivos, POST enviar | Autenticado |
| `bandeja.py` | GET list (elaboracion/revision/aprobacion/liberacion) | Autenticado |
| `ausencias.py` | GET list, GET vigente, GET by id, POST, PATCH, DELETE | Self/ETO/ADMIN |
| `configuracion_global.py` | GET list, GET by clave, POST upsert, PATCH, POST bulk, DELETE | GET=public, muta=ETO/ADMIN |
| `feriados.py`, `email_templates.py`, `matriz_enrutamiento_eto.py`, `tipos_documento.py`, `estados.py`, `semaforizacion_tarea.py`, `roles.py` | CRUD estándar | GET=public, muta=ETO/ADMIN |
| `audit_log.py` | GET list, GET export | ETO/ADMIN |
| `admin_impersonate.py` | GET list, POST start, POST stop | ADMIN/ETO |
| `plantillas_documentales.py` | GET list, GET download | Autenticado |
| `health.py` | GET `/health` | No auth |

### 3.2 Modelos (~22 tablas, 16 enums)

| Tabla | PK | FK clave |
|---|---|---|
| `gerencias` | id | — |
| `areas` | id | gerencia_id |
| `usuarios` | id | area_id, delegado_id |
| `roles` | id | — |
| `usuario_roles` | (usuario_id, rol_id) | ambas |
| `modulos` | id | — |
| `documentos` | id | gerencia_id, area_id, tipo_documento_id |
| `documento_flujo` | id | documento_id |
| `archivos_adjuntos` | id | documento_id |
| `configuracion_global` | clave (str) | — |
| `feriados` | id | — |
| `email_templates` | id | — |
| `matriz_enrutamiento_eto` | id | gerencia_id (unique) |
| `tipos_documento` | id | — |
| `estados` | id | — |
| `semaforizacion_tarea` | tipo_tarea (PK) | — |
| `audit_log` | id | usuario_id |
| `ausencias` | id | usuario_id |
| `firmas_digitales` | id | usuario_id |
| `delegaciones` | id | usuario_principal_id |
| `log_sincronizacion_ad` | id | triggered_by_user_id |
| `alembic_version` | version_num | — |

> **Nota:** `usuario_modulos` fue eliminada (migración `drop_modulos_s26`). Los accesos se controlan por rol vía `auth.js:canAccess()`, no por tabla.

### 3.3 Schemas Pydantic (14 archivos)

Todos los schemas de input/output para los 19 routers. Incluyen validación de tipos, optional/nullable, y response models con `from_attributes=True`.

### 3.4 Servicios (8 archivos)

| Servicio | Líneas | Función |
|---|---|---|
| `ad_service.py` | 616 | LDAP real (bind, search, sync). Filtra usuarios sin SAP. |
| `impersonate_service.py` | 114 | Wrapper AD para impersonate |
| `area_mapping.py` | 149 | Match AD department → area_id por scoring |
| `correlativo_service.py` | 138 | SELECT FOR UPDATE + advisory lock fallback |
| `envio_service.py` | 270 | Firma 2FA + envío a liberación (transacción atómica) |
| `storage.py` | 183 | LocalStorage real + SharePointStorage stub |
| `vigencia_service.py` | 166 | Cálculo vigencia documento |
| `matriz_import_service.py` | 401 | Carga masiva desde Excel matriz abril |

### 3.5 Core (5 archivos)

| Archivo | Líneas | Función |
|---|---|---|
| `config.py` | 145 | Pydantic Settings (todas las vars de entorno) |
| `database.py` | 50 | SQLAlchemy async engine + session |
| `permissions.py` | 145 | Helpers de autorización (get_current_user, require_eto_or_admin, require_admin, etc.) |
| `audit.py` | 126 | write_audit() con soporte impersonate |
| `excel_export.py` | 204 | Generación XLSX/CSV profesional |

### 3.6 Workers Celery (2 archivos)

- `celery_app.py`: instancia "cofar_sgd", broker=Redis, beat schedule activo
- `tasks.py`: `desactivar_ausencias_vencidas` (cron 00:05)

---

## 4. Base de Datos (PostgreSQL 16)

- **22 tablas** + 16 enums
- **18 migraciones Alembic** aplicadas
- **Head:** `drop_modulos_s26`
- **Datos sembrados:** 10 gerencias, 50 áreas, 761 usuarios, 5 roles, 13 tipos_documento, 12 estados, 20 feriados, 11 email_templates, 10 matriz_eto, 10 documentos, 7 configuracion_global
- **Seed complementario:** 5 usuarios locales de prueba (admin_local, eto_test, elaborador_revisor, elaborador_revisor_aprobador, visualizador_cl)

### Funciones PL/pgSQL
- `verify_clean_state()` — retorna conteo de filas por tabla para verificar estado limpio

### Clean state
- Dump: `backups/clean_state_20260618/clean_state.dump` (134 KB)
- Script restore: `scripts/restore_clean_state.bat`

---

## 5. Docker (8 servicios)

| Servicio | Puerto host | Health |
|---|---|---|
| `sgd-nginx` | 8080 → 80 | ✅ |
| `sgd-frontend` | 5173 → 5173 | ✅ |
| `sgd-backend` | 18000 → 8000 | ✅ curl /health |
| `sgd-celery-worker` | — | ✅ |
| `sgd-celery-beat` | — | ✅ |
| `sgd-postgres` | 25432 → 5432 | ✅ pg_isready |
| `sgd-redis` | 26379 → 6379 | ✅ redis ping |
| `sgd-mailhog` | 8025, 1025 | ✅ |

Volúmenes: postgres_data, redis_data, backend_storage, frontend_node_modules.
Red: `sgd-des_net` (bridge, DNS corporativo COFAR).

### Stacks disponibles
1. **DES** (`deploy/docker-compose.yml`): 8 servicios, puertos custom
2. **Backup** (`deploy/docker-compose.backup.yml`): stack paralelo (puertos +1)
3. **QAS** (servidor Debian): HTTPS, cert autofirmado, workers=2, sin --reload

---

## 6. Scripts

| Script | Propósito |
|---|---|
| `scripts/start-stack-des.bat` | Orquestador principal DES |
| `scripts/stop-stack-des.bat` | Apagado stack DES |
| `scripts/restore_clean_state.bat` | Restaura BD a snapshot limpio |
| `scripts/dev-backend.bat` | Backend nativo Windows (fallback) |
| `scripts/deploy-qas.bat` | Deploy a QAS via SSH |
| `scripts/start-stack-backup.bat` | Stack backup paralelo |
| `scripts/stop-stack-backup.bat` | Apagado stack backup |
| `scripts/validar_stack.ps1` | Smoke test post-deploy |
| `backend/scripts/seed_data.py` | ✅ Funcional (sesión 30: fix `usuario_modulos`) |
| `backend/scripts/seed_local_test_users.py` | ✅ Funcional (sesión 30: fix `usuario_modulos`) |
| `backend/scripts/seed_matriz_eto.py` | ✅ Funcional (sesión 30: fix `usuario_modulos`) |
| `backend/scripts/seed_organizacion.py` | ✅ Funcional |
| `backend/scripts/seed_documentos.py` | ✅ Funcional |
| `backend/scripts/seed_feriados.py` | ✅ Funcional |
| `backend/scripts/seed_email_templates.py` | ✅ Funcional |
| `backend/scripts/seed_configuracion_global.py` | ✅ Funcional |
| `backend/scripts/seed_tipos_documento.py` | ✅ Funcional |
| `backend/scripts/seed_estados.py` | ✅ Funcional |
| `backend/scripts/sync_ad_oficial.py` | ✅ Funcional |
| `backend/scripts/run_matriz_import.py` | ✅ Funcional |
| `backend/scripts/add_reportes_module.py` | ✅ Funcional |
| `backend/scripts/desactivar_ausencias_vencidas.py` | ✅ Funcional |

---

## 7. Tests (228 tests, 23 archivos)

| Archivo | Tests | Estado |
|---|---|---|
| `test_gerencias.py` | 21 | ✅ |
| `test_usuarios.py` | 21 | ✅ (1 fail preexistente) |
| `test_documentos.py` | 23 | ✅ |
| `test_areas.py` | 16 | ✅ |
| `test_area_mapping.py` | 15 | ✅ |
| `test_audit_log.py` | 13 | ✅ |
| `test_configuracion_global.py` | 11 | ✅ |
| `test_plantillas_documentales.py` | 11 | ✅ |
| `test_storage.py` | 11 | ✅ |
| `test_correlativo_service.py` | 10 | ✅ |
| `test_bandeja.py` | 8 | ✅ |
| `test_feriados.py` | 8 | ✅ |
| `test_matriz_enrutamiento_eto.py` | 8 | ✅ |
| `test_documentos_create.py` | 8 | ✅ |
| `test_ausencias.py` | 7 | ✅ |
| `test_email_templates.py` | 7 | ✅ (3 fail preexistentes) |
| `test_estados.py` | 7 | ✅ |
| `test_tipos_documento.py` | 7 | ✅ (4 fail preexistentes) |
| `test_documentos_enviar.py` | 6 | ✅ (3 fail preexistentes) |
| `test_documentos_archivos.py` | 4 | ✅ |
| `test_documentos_flujo_wizard.py` | 2 | ✅ |
| `test_tracer.py` | 4 | ✅ |
| **Total** | **~228** | **~217 PASS, ~11 FAIL** |

**Fallas preexistentes (no relacionadas con cambios recientes):**
- `test_email_templates.py` (3): refs a `CodigoPlantilla.NUEVA_TAREA` (enum antiguo)
- `test_tipos_documento.py` (4): refs a `codigo_doc` (campo removido en sesión 13)
- `test_usuarios.py` (1): esperaba 403 pero retorna 200
- `test_documentos_enviar.py` (3): necesita estado REVISION

---

## 8. Estado de los 22 fixes de sesión 25

| # | Issue | Sev | Estado |
|---|---|---|---|
| 1.1 | Ausencia motivo!=vacaciones no marca ausente | 🟠 | ✅ RESUELTO |
| 4.3 | ychavez sin Área en Mi Perfil | 🟠 | ✅ RESUELTO |
| 3.1 | Delegado obligatorio al asignar eto/revisor | 🟠 | ✅ RESUELTO |
| 4.1 | Botón Sincronizar AD 403 para ETO | 🟠 | ✅ RESUELTO |
| 10.1 | Política de Descargas hardcodeada | 🟠 | ✅ RESUELTO |
| 11.1 | Quitar Analista ETO del wizard paso 1 | 🟠 | ✅ RESUELTO |
| 11.2 | UI Reemplazo o baja + sub-bug | 🟠 | ✅ RESUELTO |
| 11.3 | Wizard no persiste en documento_flujo | 🟠 | ✅ RESUELTO |
| 4.2 | soporteglpi sin SAP en login on-demand | 🟡 | ✅ RESUELTO |
| 4.4 | Sync AD: mapping ad_info→area_id | 🟡 | ✅ RESUELTO |
| 8.1 | Filtros activos/inactivos + ausentes | 🟡 | ✅ RESUELTO |
| 8.4 | REPORTES en Excel para elaboradores | 🟡 | ⛔ DEPRECADO |
| 5.1 | Selector Estados con 4 opciones | 🟡 | ✅ RESUELTO |
| 1.2 | Lista delegados corta | 🟡 | ✅ RESUELTO |
| 7.1 | Matriz ETO dropdown delegado solo ETO | 🟡 | ✅ RESUELTO |
| 2.1 | Performance login (Promise.all) | 🟡 | ✅ RESUELTO |
| 8.3 | Header "Área" | 🟢 | ✅ RESUELTO |
| 8.5 | KPI inactivos + desvinculados | 🟢 | ✅ RESUELTO |
| 9.1 | /plantillas vista tienda responsive | 🟢 | ✅ RESUELTO |
| 9.2 | Quitar bloque "IA — Recomendación" | 🟢 | ✅ RESUELTO |
| 6.1 | Ocultar columna SLUG en tipos_documento | 🟢 | ✅ RESUELTO |

**Total: 20 RESUELTO + 1 DEPRECADO = 21/22 cerrados.**

---

## 9. Pendientes (deuda técnica + backlog)

### 🔴 P0 — Bloqueantes para QAS/PRD

| ID | Descripción | Archivos afectados |
|---|---|---|
| ~~B7~~ | ~~3 scripts seed ROTOS: importan `usuario_modulos` (eliminado)~~ **✅ RESUELTO sesión 30** | `backend/scripts/seed_data.py`, `seed_local_test_users.py`, `seed_matriz_eto.py` |
| CSRF | Middleware CSRF ausente — api.js envía token pero backend no valida | `backend/app/main.py`, `middleware/` |
| QAS cert | Certificado HTTPS autofirmado — cambiar a Let's Encrypt o corporativo | `deploy/nginx/ssl/` |
| QAS tag | Bumpear `v1.1.0-qas` con acumulado sesiones 20-28 | tag git |

### 🟡 P1 — Funcionalidad incompleta

| ID | Descripción | Impacto |
|---|---|---|
| R3 bandejas | `Bandeja.js` usa datos mock — necesita refactor para consumir API | Experiencia usuario |
| R3 liberación | `LiberacionDetalle.js` usa datos mock — necesita refactor | Flujo ETO |
| R3 lista maestra | `ListaMaestra.js` usa datos mock — necesita refactor | Consulta documentos |
| R3 revisión | `Revision.js` usa datos mock | Flujo revisores |
| R3 aprobación | `AprobacionFinal.js` usa datos mock | Flujo aprobadores |
| R3 corrección | `Correccion.js` usa datos mock | Flujo correcciones |
| R2 flow | Wizard crea documento pero flujo completo (revisión→aprobación→liberación) no está encadenado | R3 depende |
| B9 | #13 Deuda delegado: 139 usuarios sin delegado | Bandeja ETO no óptima |
| B10 | #14 Cargos a áreas: seed POSICION → area_id | Wizard muestra área correcta? |

### 🟢 P2 — Mejoras / Cleanup

| ID | Descripción |
|---|---|
| Data mocks | 16 archivos en `frontend/src/data/` son código muerto que ya no debería usarse. Limpiar progresivamente al refactorizar cada página. |
| B1 | `Gerencia.areas` cascade cleanup (cascade="all, delete-orphan" → cambiar a "save-update, merge") |
| B3 | `vite.config.js` manualChunks como objeto (falla en `npm run build`) |
| B5 | Modelos SQLAlchemy sin `__repr__` |
| B2 | `auth.py` password dummy `cofar.2026` hardcoded (solo DES, QAS tiene LDAP) |

### 📋 Backlog general

| Lote | Alcance | Estado |
|---|---|---|
| L3 (R3) | Workflow ETO + bandejas paralelas + aprobación + cron SLA + liberación + árbol Outlook | 🟡 Planificado |
| L4 (R4) | Office 365 + IA similitud + embeddings + webhook + cron sincronización AD | 🔴 0% |
| L5 (R5) | PDF custodiado + marca de agua + obsolescencia + lista maestra + vencimientos | 🔴 0% |
| L6 (R6) | Capacitación + exámenes + certificados + copias CC/CN + BI + chat RAG | 🔴 0% |

---

## 10. ADRs activos (resumen)

| ADR | Decisión | Estado |
|---|---|---|
| 001-003 | Stack: FastAPI + PostgreSQL + Docker Compose | ✅ |
| 004 | LDAP stub en DES, real en QAS | ✅ |
| 011 | Nomenclatura códigos: sigla_area-codigo_tipo-correlativo vXX | ✅ |
| 012 | Sync AD: botón manual + job 00:05 | ✅ |
| 013 | Backend dentro de Docker (DNS corporativo custom) | ✅ Ratificado |
| 014 | AuditLog append-only via write_audit() | ✅ |
| 042 | JSONB para N:M en documento_flujo (tablas N:M en R3) | ✅ |
| 045 | Separador versión: `/` (no `v`) | ✅ |
| 059 | DROP TABLE usuario_modulos (código muerto) | ✅ |
| 060 | columna es_usuario_ad (bool) | ✅ |
| 061 | /me DEBE incluir ad_department | ✅ |
| 062 | Modal personalizado en vez de confirm() nativo | ✅ |
| 065 | pg_dump -Fc + pg_restore como clean state | ✅ |

---

## 11. Variables de entorno críticas (`.env`)

```env
# Puertos NO estándar (no usar 15432/16379)
HOST_PORT_POSTGRES=25432
HOST_PORT_REDIS=26379
HOST_PORT_NGINX=8080
HOST_PORT_BACKEND=18000
HOST_PORT_FRONTEND=5173

# LDAP / AD (DES)
LDAP_ENABLED=true
LDAP_SERVER=172.16.10.17      # IP directa (no resuelve por nombre en Docker)
LDAP_PORT=389
LDAP_BIND_USER=soporteglpi@cofar.com
LDAP_BASE_DN=OU=Oficina Central,DC=COFAR,DC=COM

# Storage
DOCUMENTOS_STORAGE_PATH=/app/storage/uploads
PLANTILLAS_STORAGE_PATH=/app/storage/plantillas
```

---

## 12. Comandos rápidos de diagnóstico

```powershell
# Estado stack
docker ps --filter "name=sgd-"

# Health
curl.exe http://localhost:18000/api/v1/health

# BD limpia?
docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT * FROM verify_clean_state();"

# Logs
docker logs sgd-backend -f --tail 50

# Login local
curl.exe -X POST http://localhost:18000/api/v1/login -H "Content-Type: application/json" -d '{\"username\":\"eto_test\",\"password\":\"cofar.2026\",\"auth_source\":\"local\"}'

# Tests
cd backend; .\.venv\Scripts\python -m pytest tests/ 2>&1 | Select-Object -Last 5

# Restaurar BD limpia
scripts\restore_clean_state.bat

# Re-levantar stack
scripts\start-stack-des.bat
```
