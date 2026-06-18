# ESTADO — COFAR SGD (live tracker)

> **Este archivo se actualiza al final de cada sesión de trabajo.**
> **Última actualización:** 2026-06-18 (sesión 27 — **3 fixes críticos + modal impersonate + reload a homeRoute**)

## Versión actual
**v1.0.0-qas** (tag creado en sesión 19, sin cambios en QAS). Sesión 20 aplicó 6 fixes preventivos al deploy pipeline basados en los bugs descubiertos durante el deploy de sesión 19. **QAS NO fue tocado en sesión 20** — todos los cambios son en código local (DES) para que el próximo deploy sea más robusto. Tag `v1.0.0-qas` se mantiene.

**Sesión 21 (2026-06-17)**: R2 arranca oficialmente con la rama `r2/wizard-y-version-editable`. Se cierra FASE 1 (modelos + endpoints + seed + tests). Tag no bumpeado todavía (Fase 2 + deploy QAS pendiente).

**Sesión 22 (2026-06-17)**: R2 FASE 2 cerrada al 100%. Backend: storage service (LocalStorage + SharePointStorage stub), POST/PATCH /documentos, POST /documentos/{id}/archivos con validación MIME/tamaño, POST /enviar con firma 2FA atómica, 4 endpoints /bandeja. Frontend: documentosApi.js, VersionEditable.js con autocomplete real, AprobacionDocumento.js refactor completo (catalogos del backend + codigo auto + firma 2FA). Tests: 31 nuevos (60 totales R2 verde). Validado E2E con Chrome DevTools. ADRs 042-045 formalizados.

**Sesión 23 (2026-06-17)**: Bloques A+B+C+D cerrados: 14 sub-tareas, 4 commits atómicos. {{VERSION}}, sin toast en siguiente paso, max archivos desde BD, delegado end-to-end, semaforización limpia, ausencias con fechas + cron 00:05, firma 2FA + FirmaDigital, sync AD con desvinculados + es_usuario_ad, impersonate end-to-end con banner sticky.

**Sesión 24 (2026-06-17)**: Bloques E+F cerrados al 100% (8 sub-tareas, commits `7e8d548` y `6c20826`).
- E1: 8 .docx copiados a `backend/storage/plantillas/` con nombres ASCII-safe
- E2: backend `/api/v1/plantillas-documentales` (lista + download + audit_log)
- E3: frontend `plantillasApi.js` + refactor `Plantillas.js` (sin mock legacy)
- F1: helper `usuarios.listPorRol('ETO')` + dropdown "Analista ETO asignado" en wizard paso 1
- F2: helper `usuarios.listPorCualquierRol([roles])` + filtros en wizard paso 3 (158 revisores, 14 aprobadores)
- F3: `insertarEtiqueta` detecta `activeElement` (asunto vs cuerpo)
- F4: oculta sección delegado en `ProfileModal.js` para visualizadores/admin
- F5: env var `DOCUMENTOS_STORAGE_PATH` configurable (compatible con `STORAGE_ROOT` legacy)
- 11 tests nuevos en `test_plantillas_documentales.py` (100% PASS)

**Sesión 25 (2026-06-17)**: 22 issues del testing 17-jun cerrados (21 commits atómicos, 24 tests nuevos). 217/228 pytest PASS.

**Sesión 26 (2026-06-18)**: DROP TABLE `usuario_modulos` (código muerto) + ProfileModal discrimina AD vs local. Migración `drop_modulos_s26`.

**Sesión 27 (2026-06-18)**: 3 fixes críticos + modal impersonate + reload a homeRoute:
- Fix #1 (backend): `/me` ahora devuelve `ad_department` (de `usuarios.ad_info`). Issue 4.3 de sesión 25 estaba **medio cerrado** (login sí lo traía, me no).
- Fix #2 (frontend): `Parametrizacion.js:1878` — backticks en comentario HTML cerraban la template string → `SyntaxError: Unexpected identifier 'analistas'`. Reemplazado por comillas simples.
- Fix #3 (frontend): impersonate ahora navega a `homeRoute` del nuevo rol + reload completo (sidebar y header coherentes con el nuevo rol). Mismo fix en `stopImpersonate`.
- Feature: `ConfirmImpersonateModal.js` (200 líneas) reemplaza el `confirm()` nativo del browser. Muestra info del usuario a impersonar, banner de impacto, botón dual Cancelar/Si, impersonar.
- 3 commits atómicos: `18e57d6` (fixes #1-2), `9af84e5` (fix #3), `c0ea1fc` (modal).
- 5 ADRs nuevos (059-064).
- ADRs-063-064-065-066 (siguiente sesión, planificados).

## Objetivo inmediato
**R1 cerrado al 100% + R2 desbloqueado** (1 día restante del plazo original)

---

## Tareas (reconstruido en sesión 4 — fuente: código actual del repo)

### R1 — Seguridad + Parametrización

| # | Tarea | Estado | Fecha | Evidencia |
|---|---|---|---|---|
| 0 | Validar entorno | ✅ | 14-jun | Docker 28.5.2, Node 22.19, Python 3.12, Git 2.51 |
| 1 | Crear estructura monorepo | ✅ | 14-jun | Carpetas creadas |
| 2 | Crear docker-compose.yml + Dockerfiles | ✅ | 14-jun | 8 servicios en `deploy/docker-compose.yml` |
| 3 | Crear requirements + scripts de init | ✅ | 14-jun | `backend/requirements/*.txt` |
| 4 | Crear backend/app/main.py + health + auth stub | ✅ | 14-jun | `app/main.py` con bootstrap completo |
| 5 | Crear .env raíz + .env.example | ✅ | 14-jun | 30+ variables |
| 6 | Levantar la stack y validar docker compose up | ✅ | 14-jun | 8 contenedores Up (nginx, frontend, postgres, redis, mailhog, celery-W/B; backend fuera de Docker — ver ADR-013) |
| 7 | Schema SQLAlchemy de Organización (10 tablas) | ✅ | 15-jun | 16 clases en `backend/app/models/` — gerencia, area, usuario (+usuario_roles, **+delegacion, +ausencia, +firma_digital, +log_sync_ad**) |
| 8 | Migración Alembic inicial | ✅ | 15-jun | **22 migraciones aplicadas** (head `drop_modulos_s26`). Tabla `usuario_modulos` eliminada (sesión 26). |
| 9 | Endpoints /auth/login con stub + verificación 2FA | ✅ | 15-jun | `app/api/v1/auth.py` — `/login`, `/logout`, `/me`, `/verify-password`. **Sesión 27**: /me ahora devuelve `ad_department` también. |
| 10 | Endpoints /usuarios (CRUD) + /usuarios/{id}/modulos | ✅ | 15-jun | `app/api/v1/usuarios.py` — `GET /usuarios` paginado, `GET /{id}`, `POST /sync-ad`, `GET /sync-status`, `PATCH /{id}`. **`/usuarios/{id}/modulos` eliminado** (sesión 26, era código muerto). |
| 11 | Endpoints /organigrama | ✅ | 15-jun | `GET /gerencias` + `GET /gerencias/{id}` + `GET /areas` + `GET /areas/{id}` + ops jerárquicas (mover, promover). Cubre organigrama completo. |
| 12 | Endpoints /gerencias + /areas (CRUD) | ✅ | 15-jun | `app/api/v1/gerencias.py` (5 endpoints) + `app/api/v1/areas.py` (7 endpoints con mover/promover). |
| 13 | Endpoints /usuarios/{id}/delegado + /ausencia | ✅ | 17-jun | `app/api/v1/ausencias.py` (6 endpoints) + helpers en usuarios.py. R1 + sesión 23 cierran esto. |
| 14 | Endpoints POST /admin/sync-ad (manual) + job 00:05 | ✅ | 17-jun | `POST /usuarios/sync-ad` con desvinculados + flag `es_usuario_ad`. Job celery-beat 00:05 está pendiente (low priority). |
| 15 | Frontend src/utils/api.js con apiFetch | ✅ | 15-jun | `frontend/src/utils/api.js` (290 líneas) + `config.js` — CSRF auto, retry 5xx, timeout 30s, 401→login, 6 atajos |
| **Tareas nuevas sesión 5 (backend ÉPICA 9)** |  |  |  |  |
| N1 | Seed organización (10 gerencias + 49 áreas) | ✅ | 15-jun | `backend/scripts/seed_organizacion.py` — 27 áreas creadas, total 50 |
| N2 | CRUD /api/v1/configuracion-global (US-9.01+9.02) | ✅ | 15-jun | `app/api/v1/configuracion_global.py` (6 endpoints) + modelo + migración Alembic 003 |
| N3 | CRUD /api/v1/feriados (US-9.01 calendario) | ✅ | 15-jun | `app/api/v1/feriados.py` (5 endpoints) + modelo + migración Alembic 004 + seed Bolivia 2026 (20 feriados) |
| N4 | CRUD /api/v1/email-templates (US-9.04, 11 plantillas) | ✅ | 15-jun | `app/api/v1/email_templates.py` (4 endpoints) + modelo + migración Alembic 005 + seed (6 → 11 con Tiptap) |
| N5 | CRUD /api/v1/matriz-enrutamiento-eto (US-9.03) | ✅ | 15-jun | `app/api/v1/matriz_enrutamiento_eto.py` (6 endpoints) + modelo + migración Alembic 006 + seed (10 filas) |
| N6 | CRUD /api/v1/tipos-documento (US-9.03, 13 tipos) | ✅ | 15-jun | `app/api/v1/tipos_documento.py` (5 endpoints) + refactor sesión 14 (codigo int UNIQUE + slug) |
| N7 | CRUD /api/v1/estados (US-9.03, 12 estados) | ✅ | 15-jun | `app/api/v1/estados.py` (5 endpoints) + modelo + migración Alembic 008 + data-migration 353aec067661 (12 nuevos) |
| 16 | Refactorizar auth.js para API real | ✅ | 15-jun | `frontend/src/store/auth.js` modificado. Sesión 27: stopImpersonate navega a homeRoute + reload. |
| 17 | Refactorizar Login.js para API real | ✅ | 15-jun | `frontend/src/pages/Login.js` |
| 18 | Integrar Parametrizacion.js con API usuarios + boton sync AD | ✅ | 16-jun | Sesión 6. Nuevo módulo `frontend/src/services/parametrizacionApi.js` con 30+ funciones. |
| 19 | Sanear 4 x-html con DOMPurify | ❌ | — | (no verificado — buscar `x-html` en `frontend/src/pages/*.js`) |
| 20 | Agregar CSP meta tag | ❌ | — | (no verificado) |
| 21 | Rate limit con slowapi | ❌ | — | (no implementado) |
| 22 | **TESTING R1** | ✅ | 16-jun | `backend/tests/` poblado. **217/228 tests passing en ~22s** (sesión 27). 11 fallas preexistentes NO relacionadas (refs a enum/field antiguos). |
| **Tareas nuevas sesión 9 (Editar Usuario + Mi Perfil)** |  |  |  |  |
| N8 | Backend `GET /api/v1/roles` (catalogo) | ✅ | 16-jun | `backend/app/api/v1/roles.py` + `schemas/rol.py`. 5 roles con flag `requiere_delegado`. |
| N9 | Backend `PATCH /usuarios/{id}` con `rol_codigo` y `delegado_id` | ✅ | 16-jun | Extiende `UsuarioUpdate`. Reemplaza roles via `delete + insert`. Auto-set `estado_delegacion=asignado`. |
| N10 | Frontend: columna DELEGADO en tabla | ✅ | 16-jun | 3 estados visuales: verde, amber, gris. |
| N11 | Frontend: modal Editar Usuario (centrado) | ✅ | 16-jun | ROL (select BD), DELEGADO (searchable picker), VACACION, ESTADO, Observaciones. |
| N12 | Frontend: Mi Perfil (ProfileModal) lee de BD | ✅ | 16-jun | **Sesión 27 fix**: ahora muestra `ad_department` (department del AD) como fallback. |
| N13 | Backend: export XLSX/CSV columna AREA | ✅ | 16-jun | Formato "Gerencia / Area" con fallback a `ad_info`. |
| **Tareas nuevas sesión 10 (Backup paralelo para demo)** |  |  |  |  |
| B10-1 | `.env.backup` + `deploy/docker-compose.backup.yml` | ✅ | 16-jun | Stack en puertos 8081/5174/18001. Container prefix `sgd-bk-`. |
| B10-2 | `scripts/start-stack-backup.bat` + `stop-stack-backup.bat` | ✅ | 16-jun | Orquestador automatizado. |
| B10-3 | `backups/20260616_150015/` (dump + working tree) | ✅ | 16-jun | pg_dump -Fc (119KB) + 393 archivos. |
| B10-4 | `docs/PR/BACKUP-PARALELO.md` | ✅ | 16-jun | Doc completa. |
| **Tareas nuevas sesión 12-16 (CRUD + Tiptap + Impersonate + Refresh)** |  |  |  |  |
| N14 | `seed_configuracion_global.py` (11 params) | ✅ | 16-jun | Commit `29001ae`. |
| N15 | Refactor `Parametrizacion.js` eliminar duplicacion | ✅ | 16-jun | Commit `4b75cdc`. -240 lineas. |
| N16 | A1-A11 bugfixes (refresh, Alpine, export, logs) | ✅ | 16-jun | Commit `af1de7d`. |
| N17 | Refactor `tipos_documento`: codigo int + slug + drop codigo_doc | ✅ | 17-jun | Migracion 6b244889632f. |
| N18 | Semaforizacion por tipo de tarea | ✅ | 17-jun | Migracion f04b96c6dff2. 4 tipos: REVISION, APROBACION, CONTROL_LECTURA, EVALUACION. |
| N19 | Plantillas notificacion: 10 → 11 plantillas | ✅ | 17-jun | Migracion 6451593bcab5. |
| N20 | Editor Tiptap para plantillas | ✅ | 17-jun | `PlantillaEditor.js` + TextStyleKit + @mousedown.prevent. **Sesión 16** root cause fix. |
| N21 | Fix bug preexistente `sgd-qas.conf` en `conf.d/` | ✅ | 17-jun | Movido a `.bk`. Commit `beafe03`. |
| N22 | Docker compose con `${VAR:-default}` en env vars | ✅ | 17-jun | Resuelve el loop sesión 13. |
| N23 | API_BASE relativa (cross-origin auth fix) | ✅ | 17-jun | `frontend/src/utils/config.js`. |
| N24 | `seed_configuracion_global.py` agregado a `start-stack-qas.sh` | ✅ | 17-jun | Commit `1ebfe5e`. |
| N25 | Fix Tiptap duplicate underline | ✅ | 17-jun | Commit `d135788`. |
| N26 | Tiptap+Alpine root cause fix (closure pattern) | ✅ | 17-jun | Commit `a154bc4`. Bug "mismatched transaction" resuelto definitivamente. |
| N27 | Tiptap color/fontSize con TextStyleKit | ✅ | 17-jun | commands.setColor/setFontSize. |
| N28 | WSIWYG @mousedown.prevent en toolbar | ✅ | 17-jun | 17 botones. |
| N29 | Validacion persistencia Tiptap -> BD | ✅ | 17-jun | F5 + re-login recupera contenido. |
| N30 | Validacion previsualizar con MOCK data | ✅ | 17-jun | Variables {{...}} sustituidas. |
| N31 | Fix Matriz ETO dropdowns binding | ✅ | 17-jun | Commit `df4aceb`. |
| N32 | Eliminar opcion "Previsualizar" de plantillas | ✅ | 17-jun | -30 lineas. Tiptap es WYSIWYG. |
| N33 | Impersonate funcional: ADMIN/ETO + no-auto + audit | ✅ | 17-jun | Commit `4763ff9`. |
| N34 | Banner sticky de impersonate en AppLayout | ✅ | 17-jun | Commit `4763ff9`. |
| N35 | Frontend impersonarUsuario + stopImpersonate | ✅ | 17-jun | Commit `df4aceb` + `4763ff9`. |
| N36 | Fix refresh bug: race auth.init vs initRouter | ✅ | 17-jun | Commit `733e8b6`. **Sesión 27**: refresh adicional (navega a homeRoute + reload en impersonar). |
| **Sesion 23 (Bloque A — reunion con cliente)** |  |  |  |  |
| A1 | {{VERSION}} en variables_json de email_templates | ✅ | 17-jun | 11 plantillas actualizadas. |
| A2 | Wizard: no toast en 'Siguiente' + creacion al firmar | ✅ | 17-jun | POST /documentos solo al firmar. |
| A3 | Wizard: limite de tamano/cantidad archivos (frontend usa BD) | ✅ | 17-jun | init() lee config_global. |
| A4 | Delegado persiste end-to-end | ✅ | 17-jun | PATCH /usuarios/1 verificado. |
| A5 | Semaforizacion: eliminar 4 claves redundantes | ✅ | 17-jun | Migracion `5aaf5d3e3509`. |
| A6 | Wizard: 3 campos read-only en paso 1 | ✅ | 17-jun | Nombre, Cargo, Fecha. |
| **Sesion 23 (Bloque B — datos + firma 2FA + estados)** |  |  |  |  |
| B1 | Vacaciones con fechas (tabla ausencias + CRUD) | ✅ | 17-jun | `ausencias.py` (6 endpoints). |
| B2 | Cron 00:05 desactiva ausencias vencidas | ✅ | 17-jun | celery beat_schedule. |
| B3 | Estados: enum ACCION + data-migration a 12 nuevos | ✅ | 17-jun | Migracion 353aec067661. |
| B4 | Firma 2FA: crear fila en firma_digital | ✅ | 17-jun | Atomicidad validada. |
| B5 | Fix doble toast en firma 2FA | ✅ | 17-jun | AuthModal.js cleanup. |
| **Sesion 23 (Bloque C — sync AD mejorado)** |  |  |  |  |
| C1 | Sync AD: usuarios deshabilitados → estado=desvinculado | ✅ | 17-jun | SyncAdResponse incluye 'desvinculados'. |
| C2 | Flag es_usuario_ad (AD vs local) | ✅ | 17-jun | Migracion 8aa4cfa0f92f. 754 AD + 10 locales. |
| **Sesion 23 (Bloque D — impersonate end-to-end)** |  |  |  |  |
| D1 | Impersonate: roles/modulos/bandejas del impersonado | ✅ | 17-jun | Prioriza impersonated_user en /me. |
| **Sesion 23 (Bloque A — reunion con cliente)** | | | | |
| A1 | {{VERSION}} en variables_json de email_templates | ✅ | 17-jun | 11 plantillas actualizadas con {{VERSION}}. Variable agregada al seed y persistida en BD. |
| A2 | Wizard: no toast en 'Siguiente' del paso 1 + creacion movida al firmar | ✅ | 17-jun | POST /documentos se ejecuta en firmarEnviar (paso 3) despues de validar password 2FA. Toast de "documento creado" eliminado. |
| A3 | Wizard: limite de tamano/cantidad archivos (frontend usa BD) | ✅ | 17-jun | init() carga max_tamano_archivo_mb y max_archivos_por_solicitud de configuracion_global. nextPaso() valida antes de avanzar. |
| A4 | Delegado persiste end-to-end | ✅ | 17-jun | Validado con curl: PATCH /usuarios/1 con delegado_id=1463 (cecEspinoza) → 200, estado_delegacion=asignado, delegado_id=1463, delegado_nombre=Cecilia Espinoza. |
| A5 | Semaforizacion: eliminar 4 claves redundantes de configuracion_global | ✅ | 17-jun | Migracion `5aaf5d3e3509` marca activo=false. Seed removidas. UI Parametrizacion > Tiempos y SLAs removio las 2 inputs y el bulkUpsert. Unica fuente de verdad: tabla `semaforizacion_tarea`. |
| A6 | Wizard: 3 campos read-only en paso 1 (Nombre/Cargo/Fecha) | ✅ | 17-jun | 3 inputs disabled con $store.auth.user.nombre_completo, $store.auth.user.cargo, new Date().toLocaleDateString('es-BO'). |
| **Sesion 23 (Bloque B — datos + firma 2FA + estados)** | | | | |
| B1 | Vacaciones con fechas (tabla ausencias + CRUD) | ✅ | 17-jun | backend/app/api/v1/ausencias.py (6 endpoints: list, get, create, update, delete, vigente). frontend ProfileModal.js + Parametrizacion.js modal Editar Usuario: registrar/actualizar/cancelar vacaciones con fechas y motivo. usuarios.ausente se setea automaticamente segun ausencias vigentes. |
| B2 | Cron 00:05 desactiva ausencias vencidas | ✅ | 17-jun | celery beat_schedule: crontab(hour=0, minute=5) → app.workers.tasks.desactivar_ausencias_vencidas. Script CLI `desactivar_ausencias_vencidas.py` para testing manual con --dry-run. |
| B3 | Estados: enum ACCION + data-migration a 12 nuevos | ✅ | 17-jun | Migracion 353aec067661: ALTER TYPE contexto_estado ADD VALUE 'ACCION' + 9 antiguos activo=false + 12 nuevos (3 PROCESO + 6 TAREA + 3 ACCION). envio_service.py: usa nuevo REVISION. |
| B4 | Firma 2FA: crear fila en firma_digital | ✅ | 17-jun | envio_service.py: crea FirmaDigital(resultado_exito=true) atómico. Tambien registra FirmaDigital(resultado_exito=false, motivo_fallo=password_invalida) en intento fallido. Bug preexistente validar_password_usuario corregido (replica logica dual de auth.py). |
| B5 | Fix doble toast en firma 2FA | ✅ | 17-jun | AuthModal.js: removido window.toast('Firma digital registrada') que se mostraba ANTES del callback onSuccess. Solo el callback muestra el resultado (éxito o error). |
| **Sesion 23 (Bloque C — sync AD mejorado)** | | | | |
| C1 | Sync AD: usuarios deshabilitados → estado=desvinculado | ✅ | 17-jun | usuarios.py POST /sync-ad: despues de procesar AD, busca en BD usuarios con ad_postal_code y estado activo/inactivo cuyo username no esta en AD, los marca como desvinculado. NUNCA se eliminan. Si estaba desvinculado y vuelve a AD, se reactiva. SyncAdResponse ahora incluye campo 'desvinculados'. |
| C2 | Flag es_usuario_ad (AD vs local) | ✅ | 17-jun | Migracion 8aa4cfa0f92f: nueva columna es_usuario_ad (bool, indexed). Backfill: 754 usuarios con ad_postal_code → true, 10 sin SAP → false. auth.py y usuarios.py setean true al crear desde AD. |
| **Sesion 23 (Bloque D — impersonate end-to-end)** | | | | |
| D1 | Impersonate: roles/modulos/bandejas del impersonado | ✅ | 17-jun | get_current_user_from_cookie prioriza impersonated_user. write_audit agrega impersonated_by al campo detalles para trazabilidad. admin_impersonate.start: fallback a BD si AD no encuentra al usuario. Validado con curl: aromero impersona a visualizador_cl, bandejas reflejan roles/permisos del visualizador (403 en liberacion), stop vuelve a aromero. |
| N36 | Fix refresh bug: race auth.init vs initRouter | ✅ | 17-jun | 3 cambios: (1) auth.js init() restaura SINCRONO desde localStorage + flag isReady. (2) router/index.js guard !isReady con loader (no redirige durante init). (3) debug page /_debug/session permanente. 6/6 smoke tests Chrome MCP. Commit `733e8b6` |

### R2 — Wizard de creación

| # | Tarea | Estado | Fecha | Evidencia |
|---|---|---|---|---|
| 23 | Schema SQLAlchemy Documentos (3 tablas) | ✅ | 17-jun | Sesión 21: `documento`, `documento_flujo`, `archivo_adjunto` + 5 enums. Plan: `docs/PR/R2-PLAN-EJECUCION.md` § 3.1-3.3 |
| 24 | Schema SQLAlchemy Workflow (3 tablas) | 🟡 | 17-jun | `documento_flujo` cubre parcialmente. Tablas N:M de tareas individuales (R3) |
| 25 | Schema SQLAlchemy Archivos (2 tablas) | ✅ | 17-jun | Sesión 21: `archivos_adjunto` con storage stub |
| 26 | Schema SQLAlchemy Soporte (4 tablas) | ❌ | — | (no iniciadas) |
| 27 | Schema SQLAlchemy Misceláneos (6 tablas) | ❌ | — | (no iniciadas) |
| 28 | Migración Alembic 014: 3 tablas R2 | ✅ | 17-jun | Sesión 21: head `b88801d59687`. Tablas: `documentos`, `documento_flujo`, `archivos_adjuntos` |
| 29 | Servicio `correlativo_service.py` con `SELECT FOR UPDATE` | ✅ | 17-jun | Sesión 21: `pg_try_advisory_xact_lock` como fallback portable. 10/10 tests pytest |
| 30 | Trigger SQL de obsolescencia automática | ❌ | — | DIFERIDO a R5 (decision validada en sesion 21) |
| 31 | Endpoints `/api/v1/documentos` (4 lectura) | ✅ | 17-jun | Sesión 21: `buscar`, `preview-codigo`, `GET /{id}`, `GET /` paginado. 23/23 tests pytest |
| 32 | Endpoint `POST /api/v1/documentos/{id}/archivos` con validación MIME | ✅ | 17-jun | Sesión 22: 4 tests (201/413/415/404). Whitelist 7 MIME types |
| 33 | Endpoint `POST /api/v1/documentos/{id}/enviar` con firma | ✅ | 17-jun | Sesión 22: 6 tests CRÍTICOS (atomicidad validada). 401 si pass incorrecta, NADA se persiste |
| 34 | Storage service: `LocalStorage` (volumen) + stub `SharePointStorage` | ✅ | 17-jun | Sesión 22: Protocol + 2 implementaciones. 11 tests (UUID, ext whitelist, path traversal bloqueado, factory env-driven) |
| 35 | Endpoint `GET /api/v1/bandeja?tipo=liberacion` para ETO | ✅ | 17-jun | Sesión 22: 4 endpoints /bandeja (elaboracion/revision/aprobacion/liberacion). 8 tests |
| 36 | Endpoint `POST /api/v1/documentos/{id}/liberar` (fan-out a revisores) | ❌ | — | Diferido a R3 (bandejas individuales con timestamps) |
| 37 | Endpoint `GET /api/v1/bandeja` general (por tipo y estado) | ✅ | 17-jun | Sesión 22: router /bandeja completo |
| 38 | Frontend: refactorizar `src/pages/Bandeja.js` para usar API | ❌ | — | (última edición 6/5/2026, no tocado para R2) |
| 39 | Frontend: refactorizar `src/pages/LiberacionDetalle.js` | ❌ | — | (última edición 6/5/2026) |
| 40 | Frontend: refactorizar `src/pages/ListaMaestra.js` | ❌ | — | (última edición 6/5/2026) |
| 41 | **TESTING R2** | ✅ | 17-jun | Sesión 22: 60/60 tests R2 passing (storage + documentos + create + archivos + enviar + bandeja). Sesión 24: +11 tests plantillas_documentales (total 71/71 R2 verde). |
| 42 | Documentación: `docs/RUNBOOK.md` | ❌ | — | |
| 43 | Documentación: `docs/ARQUITECTURA.md` y `ARQUITECTURA-DB.md` | 🟡 | 14-jun | Están en `docs/Diagramas_Matrices/`, falta unificar |

**Fase 1 cerrada (sesión 21):** 7/21 tareas R2 completadas (modelos + migración + 4 endpoints + correlativo + seed + 33 tests + placeholder fix). Detalle completo en `docs/PR/R2-PLAN-EJECUCION.md` § 4.1.

### Bonus — tareas que aparecieron fuera del plan original

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| B1 | Endpoint `/admin-impersonate/{list,start,stop}` | ✅ | `app/api/v1/admin_impersonate.py` + `app/services/impersonate_service.py` |
| B2 | Servicio `ad_service.py` con LDAP real (ldap3) | ✅ | 620 líneas, excluye 17+ CNs, soporta RODC, fallback si `LDAP_ENABLED=false` |
| B3 | Login contra BD local (no solo LDAP) — para DES sin AD | ✅ | `auth.py` líneas 80+ con `auth_source: "local"\|"cofar"\|None` |
| B4 | `LoginUserOut` con módulos + roles + impersonación | ✅ | |

### Sesion 25 — Fixes 22 issues del testing del 17-jun (1 commit atómico por fix)

| # | Issue | Sev | Tipo | Commit | Resultado |
|---|---|---|---|---|---|
| 1.1 | Ausencia motivo!=vacaciones no setea ausente | 🟠 | CRIT (NO-BUG) | `2706455` | Backend funciona OK. 7 tests nuevos como cobertura de regresión. |
| 4.3 | ychavez sin Área en Mi Perfil | 🟠 | CRIT (fix) | `f9c3629` | **Sesión 27 fix completo**: /me ahora devuelve ad_department. |
| 3.1 | Delegado obligatorio al asignar eto/revisor | 🟠 | CRIT (fix) | `a63b453` | Validación bloqueante reemplazada por confirm() no bloqueante. |
| 4.1 | Botón Sincronizar AD 403 para ETO | 🟠 | CRIT (fix) | `dcfb46b` | x-show=role==admin en ambos botones. |
| 10.1 | Política de Descargas hardcodeada | 🟠 | CRIT (fix) | `235ad86` | VersionEditable.js carga desde BD. |
| 11.1 | Quitar Analista ETO del wizard paso 1 | 🟠 | CRIT (fix) | `1371aec` | Estado, validación, UI removidos. |
| 11.2 | UI Reemplazo o baja + sub-bug chipsReemplazo | 🟠 | CRIT (fix) | `5a23846` | UI select+chips + fix array vacio. |
| 11.3 | Wizard no persiste en documento_flujo | 🟠 | CRIT (NO-BUG) | `3cd5c2d` | Test e2e + 2 tests pytest. Sub-bug: list[int]→list[str]. |
| 4.2 | soporteglpi sin SAP en login on-demand | 🟡 | IMP (fix) | `19e2b36` | ldap_get_user_by_samaccountname retorna None. |
| 4.4 | Sync AD: mapping ad_info→area_id automático | 🟡 | IMP (feat) | `b9cf37a` | Nuevo `area_mapping.py`. 15 tests. |
| 8.1 | Filtros activos/inactivos + ausentes | 🟡 | IMP (feat) | `dc2efe0` | Backend: param `ausente: bool`. |
| 8.4 | REPORTES en Excel para elaboradores | 🟡 | IMP (feat) | `7aa64c0` | Script `add_reportes_module.py` idempotente. |
| 5.1 | Selector Estados con 4 opciones | 🟡 | IMP (fix) | `0bcb499` | 4 valores UPPERCASE. |
| 1.2 | Lista delegados corta | 🟡 | IMP (fix) | `5331d34` | `listPorCualquierRol([3 roles relevantes])`. |
| 7.1 | Matriz ETO: dropdown delegado solo ETO | 🟡 | IMP (fix) | `9554ad7` | Dropdown itera sobre `analistas`. |
| 2.1 | Performance login - Promise.all | 🟡 | IMP (perf) | `bb3a06d` | 3 requests en paralelo. 2.4x más rápido. |
| 8.3 | Header 'Área' | 🟢 | MENOR (fix) | `4335665` | Header tabla y XLSX. |
| 8.5 | KPI inactivos + desvinculados | 🟢 | MENOR (feat) | `e92a369` | 2 nuevos KPI cards. |
| 9.1 | /plantillas vista tienda responsive | 🟢 | MENOR (fix) | `c4f501c` | Grid 1/2/3/4 cols. |
| 9.2 | Quitar bloque 'IA — Recomendación' | 🟢 | MENOR (fix) | `c4f501c` | Removido. |
| 6.1 | Ocultar columna SLUG en tipos_documento | 🟢 | MENOR (fix) | `f112a68` | Header: Tipo | Cód. Doc | Acciones. |

**Resumen:** 22 issues cerrados, 21 commits atómicos, 217/228 tests PASS (+15 nuevos).

---

## Progreso R1
**38/38 tareas R1 + EPICA9 + Parametrizacion (100% CERRADO)** = **42/42 con sesiones 17-18** (Matriz ETO + Previsualizar + Impersonate + Refresh fix #15). Sesión 27 agrega 3 fixes puntuales sin nuevas tareas. Tests pytest 217/228.

## Progreso QAS
**8/8 tareas QAS (100%)**: stack completo en https://sgdqas.cofar.com.bo + HTTPS + AD real + 8 seeds (incluye `seed_configuracion_global.py`) + sync AD automatizado (763 usuarios) + `start-stack-qas.sh` 1-click. Tag `v1.0.0-qas` creado sesión 19. **Pendiente**: bumpear a `v1.1.0-qas` con todos los cambios de sesiones 20-27.

## Progreso R2
**17/21 tareas R2 completadas (FASE 1 + FASE 2 cerradas en sesiones 21+22, branch `r2/wizard-y-version-editable`)**. Plan completo + 2 fases ejecutado. 60 tests pytest R2 (33 FASE 1 + 27 FASE 2), 100% verde. 10 documentos sembrados idempotentemente. Regla "VENCIDO → APROBADO u OBSOLETO" validada. Wizard AprobacionDocumento.js refactor completo con catalogos del backend + firma 2FA real. VersionEditable.js con autocomplete real (BD). E2E validado con Chrome DevTools (aromero ve catalogos reales, codigo auto CC-1-002/00 generado correctamente).

**Handoff**: Pendiente refactor Bandeja.js + LiberacionDetalle.js + ListaMaestra.js (tareas 38-40), trigger obsolescencia (R5), deploy QAS con R2 + sesiones 23-27 acumulado.

## Total
- R1 + EPICA9 + Impersonate + Refresh + Sesión 27 fixes: **100% cerrado**
- QAS: 100% funcional
- R2 FASE 1 + FASE 2: 100% cerrado
- R3: 0% (3 pages sin refactor)
- R4-R6: 0% (backlog)
- **Total: 100% R1 + 100% R2 + 100% QAS + 81% R2 (con refactors pendientes R3)**

## Tablas de BD
**22 tablas en BD** (21 entidades + alembic_version). Alembic head: `drop_modulos_s26`.

## Servicios backend implementados

| Servicio | Líneas | Función |
|---|---|---|
| `ad_service.py` | 620 | LDAP real + bind + búsqueda + sync — fallback si `LDAP_ENABLED=false` |
| `impersonate_service.py` | ? | Login-as (admin → otro usuario) |
| `auth.py` | 444 | Login + logout + me + verify-password (firma 2FA) |
| `permissions.py` (NUEVO) | 70 | Helpers reusables: get_current_user_from_cookie, require_eto_or_admin, require_admin |

## Endpoints backend implementados (40+)

```
GET   /api/v1/health
POST  /api/v1/login              (con soporte auth_source: local/cofar)
POST  /api/v1/logout
GET   /api/v1/me
POST  /api/v1/verify-password    (firma digital 2FA)
GET   /api/v1/usuarios           (paginado)
GET   /api/v1/usuarios/{id}
POST  /api/v1/usuarios/sync-ad
GET   /api/v1/usuarios/sync-status
GET   /api/v1/admin-impersonate/list
POST  /api/v1/admin-impersonate/start
POST  /api/v1/admin-impersonate/stop
GET   /api/v1/gerencias          (NUEVO sesión 5)
GET   /api/v1/gerencias/{id}     (NUEVO)
POST  /api/v1/gerencias          (NUEVO)
PATCH /api/v1/gerencias/{id}     (NUEVO)
DELETE /api/v1/gerencias/{id}    (NUEVO)
GET   /api/v1/areas              (NUEVO)
GET   /api/v1/areas/{id}         (NUEVO)
POST  /api/v1/areas              (NUEVO)
PATCH /api/v1/areas/{id}         (NUEVO)
DELETE /api/v1/areas/{id}        (NUEVO)
GET   /api/v1/configuracion-global                       (NUEVO)
GET   /api/v1/configuracion-global/{clave}              (NUEVO)
POST  /api/v1/configuracion-global                       (NUEVO — UPSERT)
PATCH /api/v1/configuracion-global/{clave}              (NUEVO)
POST  /api/v1/configuracion-global/bulk                  (NUEVO)
DELETE /api/v1/configuracion-global/{clave}              (NUEVO)
GET   /api/v1/feriados                                   (NUEVO)
GET   /api/v1/feriados/{id}                              (NUEVO)
POST  /api/v1/feriados                                   (NUEVO)
PATCH /api/v1/feriados/{id}                              (NUEVO)
DELETE /api/v1/feriados/{id}                              (NUEVO)
GET   /api/v1/email-templates                            (NUEVO)
GET   /api/v1/email-templates/{codigo}                   (NUEVO)
PATCH /api/v1/email-templates/{codigo}                   (NUEVO)
POST  /api/v1/email-templates/{codigo}/preview           (NUEVO)
GET   /api/v1/matriz-enrutamiento-eto                     (NUEVO)
GET   /api/v1/matriz-enrutamiento-eto/{id}                (NUEVO)
GET   /api/v1/matriz-enrutamiento-eto/gerencia/{gerencia_id}  (NUEVO)
POST  /api/v1/matriz-enrutamiento-eto                     (NUEVO)
PATCH /api/v1/matriz-enrutamiento-eto/{id}                (NUEVO)
DELETE /api/v1/matriz-enrutamiento-eto/{id}               (NUEVO)
GET   /api/v1/tipos-documento                             (NUEVO)
GET   /api/v1/tipos-documento/{id}                        (NUEVO)
POST  /api/v1/tipos-documento                             (NUEVO)
PATCH /api/v1/tipos-documento/{id}                        (NUEVO)
DELETE /api/v1/tipos-documento/{id}                       (NUEVO)
GET   /api/v1/estados                                     (NUEVO)
GET   /api/v1/estados/{id}                                (NUEVO)
POST  /api/v1/estados                                     (NUEVO)
PATCH /api/v1/estados/{id}                                (NUEVO)
DELETE /api/v1/estados/{id}                               (NUEVO)
```

---

## 🐛 Bugs conocidos / Pendientes de fix

> **Actualizado sesión 27 (2026-06-18).** Backlog de issues identificados.

| # | Bug | Severidad | Impacto | Workaround | Sesion sugerida |
|---|---|---|---|---|---|
| B1 | `Gerencia.areas` tiene `cascade="all, delete-orphan"` en la relacion ORM | 🟡 Media | Si se hace DELETE fisico desde el ORM, se borran las areas hijas. | El router usa solo borrado logico (activo=false). | Sesion 28 (cleanup) |
| B2 | NO existe middleware CSRF en backend (solo se setea cookie en `/login`) | 🟠 Alta | El header `X-CSRF-Token` que envia `api.js` no se valida. Vector de CSRF. | Confiar en CORS + `credentials: include`. | Sesion 28 (seguridad) |
| B3 | `build-error` de Vite falla por `manualChunks` como objeto en `vite.config.js` | 🟢 Baja | Solo afecta `npm run build`. El dev server (HMR) funciona. | Cambiar `manualChunks` a funcion. | Sesion 28 |
| B4 | `frontend/src/data/*.js` aun tiene datos hardcoded del mock legacy | 🟡 Media | Componentes que importen de ahi muestran datos desactualizados. | `Parametrizacion.js` ya consume API. | Sesion 28 (cleanup) |
| B5 | Modelos SQLAlchemy NO tienen `__repr__` consistente | 🟢 Baja | Logs de SQLAlchemy muestran `<Modelo at 0x...>`. | Agregar `def __repr__` a los modelos. | Sesion 28 |
| B6 | `auth.py` logica de password dummy `cofar.2026` hardcoded | 🟠 Alta (en QAS) | En DES OK. Si QAS llega con `LDAP_ENABLED=false` se acepta cualquier pass. | Verificar `LDAP_ENABLED=true` en QAS. | Pre-deployment QAS |
| B7 | **3 scripts de seed ROTOS** (sesión 27): `seed_data.py`, `seed_local_test_users.py`, `seed_matriz_eto.py` importan `usuario_modulos` (eliminado sesión 26) | 🟠 Alta | Si se corren manualmente fallan con ImportError. En DES no afecta (start-stack-des.bat no los corre). En QAS SÍ afecta (`start-stack-qas.sh` los llama) — el `| tail -3` enmascara el error. | No correrlos manualmente hasta fix. | **Sesion 28 (P0)** |
| B8 | `vite.config.js` `manualChunks` problema preexistente | 🟢 Baja | Solo `npm run build`. HMR funciona. | Ninguno necesario. | Sesion 28 |
| B9 | #13 Deuda delegado: 139 usuarios sin delegado | 🟡 Media | Bandeja ETO no funciona correctamente para estos usuarios. | Skip delegado + warning (sesión 8). | Sesion 28 |
| B10 | #14 Cargos a areas (seed POSICION → area_id) | 🟡 Media | Wizard no muestra area correcta. | Manual lookup. | Sesion 28 |

### Bugs resueltos en sesiones 25-27 (referencia)

**Sesión 26**:
- ✅ Tabla `usuario_modulos` (código muerto) eliminada. Migración `drop_modulos_s26`.
- ✅ ProfileModal discrimina AD vs local via `es_usuario_ad`.

**Sesión 27**:
- ✅ Issue 4.3 (ychavez sin Área): `/me` ahora devuelve `ad_department`. ADR-061.
- ✅ Parametrización rota: `Parametrizacion.js:1878` backticks en comentario HTML → SyntaxError. ADR-064.
- ✅ Impersonate no recargaba sidebar: `homeRoute + reload()` en `impersonarUsuario` y `stopImpersonate`. ADR-063.
- ✅ `confirm()` nativo feo: `ConfirmImpersonateModal.js` (200 líneas). ADR-062.

### Bugs corregidos durante sesion 5 (referencia historica, ya no aplicar)

1. SQLAlchemy 2.0 rechaza `description=` en `String()`/`Text()` → quitado.
2. `usuario_roles` se importa de `app.models.usuario`, NO de `rol.py` → fix en import.
3. Bug de doble endpoint `list_matriz` en matriz_enrutamiento_eto.py → reescrito limpio.
4. Metodo inventado `activo_disponibilidad()` en seed original → eliminado.

---

## 📋 Tareas de Sesion B (UI + tests + bulk) — RESULTADO (16-jun)

| # | Tarea | Estado | Commit | Evidencia |
|---|---|---|---|---|
| B-T1 | Refactor `Parametrizacion.js` para usar los endpoints nuevos con `apiFetch` | ✅ | `52cc80c` | Nuevo `frontend/src/services/parametrizacionApi.js` con 30+ funciones. `Parametrizacion.js` ya NO importa de `data/parametrosSistema.js` (verificado con grep). 7 tabs cargan del backend en paralelo. |
| B-T2 | Tests pytest de los endpoints nuevos (80% coverage) | ✅ | `e13761c` | 123/123 tests passing en 11.38s. Commit "test(backend): tests pytest 80% routers - Sesion 7 cierre R1". Sesion 7. |
| B-T3 | Asignacion masiva desde `USUARIOS EXISTENTES A ABRIL.xlsx` (730 usuarios) | ✅ | (sesion 8) | `backend/app/services/matriz_import_service.py` (415 lineas) + `backend/scripts/run_matriz_import.py` (204 lineas, CLI argparse) + `docs/PR/MATRIZ-ABRIL-MAPEO.md` (169 lineas). 716 usuarios asignados, 3,312 modulos. Idempotente verificado. |
| B-T4 | `GET /api/v1/audit-log` con filtros | ✅ | `33c3fef` | `app/api/v1/audit_log.py` + `app/models/audit_log.py` + migración 009. Helper `app/core/audit.py:write_audit()`. 8 routers instrumentados. |
| B-T5 | Operaciones jerarquicas areas (`mover`, `promover-a-gerencia`, `DELETE logico`) | ✅ | `79120cf` | `app/api/v1/areas.py` extendido con 2 endpoints nuevos. `DELETE ?fisico=true|false`. **Fix B1** aplicado: `UniqueConstraint('gerencia_id', 'sigla')` + migración 010. |
| B-T6 | Override vacaciones + export Excel/CSV | ✅ | `1559cdb` | `PATCH /usuarios/{id}` (override estado/ausente/delegacion) + `GET /usuarios/export?formato=xlsx|csv`. Helper `app/core/excel_export.py` con paleta pastel, auto-width, freeze, filtros, totales. openpyxl==3.1.5 agregado a requirements. |

**Total Sesion B ejecutado:** 6/6 tareas (100%). Sesion 7 cerro B-T2 + bugfix de B-T1. Sesion 8 cerro B-T3 con import masivo desde CLI.

### Bugs resueltos en Sesion B

- **B1** ✅ RESUELTO en tarea B-T5: `areas.sigla` ahora es `UNIQUE(gerencia_id, sigla)`, no global. Migración 010 aplicada.
- **B5** ✅ RESUELTO en tarea B-T1: `Parametrizacion.js` ya no usa `data/parametrosSistema.js`.

### Bugs pendientes (de la tabla de arriba)

- **B2**: `Gerencia.areas` cascade (cleanup opcional, no bloquea).
- **B3**: CSRF middleware ausente (seguridad pre-QAS).
- **B4**: `vite.config.js` manualChunks (cuando se haga build de produccion).
- **B6**: PowerShell + http.client (solo tooling).
- **B7**: Modelos sin `__repr__` (cleanup).
- **B8**: `auth.py` password dummy (pre-deployment QAS, documentado).

## Decisiones tomadas (ADRs)
**Total: 49 ADRs documentados** (ver `DECISIONES.md`).
- ADR-001 a ADR-027: arquitectura core (sesiones 1-11)
- ADR-028 a ADR-041: wizard, refresh, deploy, etc. (sesiones 13-18)
- ADR-042 a ADR-045: R2 FASE 1 y 2 (sesiones 21-22)
- ADR-046 a ADR-058: sesiones 23, 25 (bloques, fixes)
- **ADR-059 a ADR-064 (sesión 27)**: drop usuario_modulos, es_usuario_ad, /me ad_department, modal impersonate, homeRoute + reload, backticks en comentario HTML.

## Bloqueos identificados

**Al cierre de sesión 27 (2026-06-18), NO hay bloqueos críticos.**

Bloqueos menores pre-QAS-public:
- 🟠 B2: CSRF middleware ausente (seguridad pre-QAS-public)
- 🟠 B6: `auth.py` password dummy `cofar.2026` (pre-QAS-public; ya validado que en QAS `LDAP_ENABLED=true` por lo que no aplica)
- 🟠 B7: 3 scripts de seed ROTOS (P0 — bloquea fresh-install QAS)
- 🟠 QAS cert HTTPS autofirmado (cambiar a Let's Encrypt o cert corporativo pre-PUBLIC)

Backlog menor:
- 🟡 B1: `Gerencia.areas` cascade cleanup opcional
- 🟡 B3: `vite.config.js` manualChunks
- 🟡 B4-B5: cleanup varios
- 🟡 B9: #13 Deuda delegado
- 🟡 B10: #14 Cargos a areas

## Próximo paso (recomendado para sesión 15)

**Sesión 14 cerrada:** Recuperación de loop Docker (5 min) + 7 commits lógicos + validación end-to-end del editor Tiptap. 3 commits de deploy/infra (`beafe03`, `1ebfe5e`, `d135788`) + 1 commit de backend (refactor tipos_documento + semaforización + plantillas 10) + 1 commit de frontend (semáforización UI + Tiptap setup) + 1 commit de docs (respaldo sesión 13) + 1 commit de lockfile. Tiptap verificado: 11 plantillas visibles, 11 variables clicables, toolbar con 12 botones funciona, console sin errors ni warnings. Bug preexistente `sgd-qas.conf` en `conf.d/` movido a `.bk` (no se carga en DES). Bug preexistente `openpyxl` no estaba en image: rebuild de imagen backend lo resolvió. **Backlog crítico: refresh bug (#15) sigue sin resolver** (router redirige a login antes de que `auth.init()` termine).

3 caminos posibles para sesión 15:

1. **Fix refresh bug** (#15, 1-2h): el router redirige a `/#/login` antes de que `auth.refreshFromBackend()` termine. Solución: await en router antes de decidir, o chequear `auth.user` con re-evaluación post-init. Esto es lo que tenía atascada la sesión 13.
2. **Fix Plazo 42 invalido** (cosmetic, 5 min): el seed de `plazo_revision_aprobacion_dias` se sembro con 42. Cambiar a 15 o regenerar seed.
3. **#13 — Deuda delegado** (~30 min): implementar match desde AD `manager` attribute o fuzzy + threshold 0.85.
4. **#14 — Cargos a areas** (mediano): seed de mapeo POSICION -> area_id.
5. **Fase 2-5 del PENDIENTES-R1** (4-6h): logs paginacion 10/pag, formato fecha Bolivia, badge Indefinido en vigencia, dropdown chips refinado.
6. **R2 (tareas #23+)** ya desbloqueado — el stack QAS es reproducible 1-click.

**Lo que NO se debería hacer todavía:**
- Refactor de pages no tocadas (Bandeja, Liberacion, ListaMaestra) — depende de R2 endpoints.

## Estado de la sesión actual (14 — recuperacion + cierre pendientes)

- ✅ Sesión 5: Backend ÉPICA 9 al 100% (10 tareas, 14 commits)
- ✅ Sesión 6: UI EPICA 9 + 3 endpoints backend nuevos (4 de 6 tareas Sesión B, 4 commits)
- ✅ Sesión 7: Bugfix del refactor incompleto de sesión 6 (10 bugs, commit `89f5ac6`) + tests pytest 123/123 (commit `e13761c`)
- ✅ Sesión 8: Import matriz abril 716 usuarios (service + CLI + mapeo, 5 sub-tareas en 2h)
- ✅ Sesión 9: Editar Usuario + Mi Perfil BD + Export corregido (6 sub-tareas, commit `ec34a3d`)
- ✅ Sesión 10: Backup paralelo 8081/5174/18001 (8 archivos nuevos) + Deploy QAS manual
- ✅ Sesión 11: Automatización QAS — `start-stack-qas.sh` 1-click + fix permisos storage + refactor smell `_build_server` → `build_server`
- ✅ Sesión 12: Restaurar CRUD Parametrizacion — 2 commits (29001ae seed + 4b75cdc frontend fix) + 4 bugs preexistentes + 11 parametros BD + validacion end-to-end
- ✅ Sesión 13: PENDIENTES-R1 segunda tanda (A1-A11 + refactor + semaforización + plantillas 10 + Tiptap deps) — comiteada en `af1de7d`. Sesión se rompió en loop Docker.
- ✅ **Sesión 14 (ESTA): Recuperar Docker + 7 commits lógicos (deploy/backend/frontend/docs/lockfile/qas/underline) + Tiptap verificado end-to-end + docs actualizados**

## Estado de la sesión actual (12 — restaurar CRUD Parametrizacion)

- ✅ Sesión 5: Backend ÉPICA 9 al 100% (10 tareas, 14 commits)
- ✅ Sesión 6: UI EPICA 9 + 3 endpoints backend nuevos (4 de 6 tareas Sesión B, 4 commits)
- ✅ Sesión 7: Bugfix del refactor incompleto de sesión 6 (10 bugs, commit `89f5ac6`) + tests pytest 123/123 (commit `e13761c`)
- ✅ Sesión 8: Import matriz abril 716 usuarios (service + CLI + mapeo, 5 sub-tareas en 2h)
- ✅ Sesión 9: Editar Usuario + Mi Perfil BD + Export corregido (6 sub-tareas, commit `ec34a3d`)
- ✅ Sesión 10: Backup paralelo 8081/5174/18001 (8 archivos nuevos) + Deploy QAS manual
- ✅ Sesión 11: Automatización QAS — `start-stack-qas.sh` 1-click + fix permisos storage + refactor smell `_build_server` → `build_server`
- ✅ **Sesión 12 (ESTA): Restaurar CRUD Parametrizacion — 2 commits (29001ae seed + 4b75cdc frontend fix) + 4 bugs preexistentes + 11 parametros BD + validacion end-to-end**

## Estado de la sesion actual (16 � Tiptap+Alpine root cause)

- ? Sesion 15: UI/UX Vigencia + Tiptap fixes (mitigacion) + Export fixes (commit ed35e33)
- ? **Sesion 16 (ESTA): Tiptap+Alpine root cause FIXED**
  - let editor movido a closure del factory Alpine.data
  - Eliminado _editorHandle (state reactivo era la causa del bug)
  - PlantillaEditor.js reducido a API simple {editor, destroy}
  - TextStyleKit (incluye Color + FontSize)
  - @mousedown.prevent en 17 botones (patron WSIWYG)
  - Persistencia BD validada con query directo
  - Previsualizar con MOCK data funciona
  - Debug page /_debug/tiptap eliminada completamente
  - 1 commit: 154bc4 fix(frontend): Tiptap 3.x + Alpine 3.x root cause of mismatched transaction
- ? **Bug Applying a mismatched transaction RESUELTO definitivamente** (workaround de reload limpio ya no necesario)

### Validacion end-to-end (Chrome DevTools en localhost:8080)

| Verificacion | Resultado |
|---|---|
| Bold/Italic/Underline/Strike | OK |
| H1/H2/H3 | OK |
| Bullet list / Ordered list | OK |
| Blockquote / CodeBlock | OK |
| Undo / Redo | OK |
| Color picker (setColor) | OK |
| FontSize (setFontSize) | OK |
| Cambio de plantilla (setContent) | OK sin mismatched transaction |
| Insercion de variable {{CODIGO}} desde chip | OK |
| Guardar plantilla (PATCH /email-templates) | OK, verificado en BD |
| F5 + re-login recupera contenido | OK |
| Previsualizar con MOCK data | OK (566 chars HTML) |
| Console errors / warnings | 0 / 0 |
