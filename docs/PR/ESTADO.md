# ESTADO — COFAR SGD (live tracker)

> **Este archivo se actualiza al final de cada sesión de trabajo.**
> Última actualización: 2026-06-17 (sesión 23 — **Bloques A+B+C+D cerrados: 14 sub-tareas, 4 commits atómicos**)

## Versión actual
**v1.0.0-qas** (tag creado en sesión 19, sin cambios en QAS). Sesión 20 aplicó 6 fixes preventivos al deploy pipeline basados en los bugs descubiertos durante el deploy de sesión 19. **QAS NO fue tocado en sesión 20** — todos los cambios son en código local (DES) para que el próximo deploy sea más robusto. Tag `v1.0.0-qas` se mantiene.

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

**Sesión 21 (2026-06-17)**: R2 arranca oficialmente con la rama `r2/wizard-y-version-editable`. Se cierra FASE 1 (modelos + endpoints + seed + tests). Tag no bumpeado todavía (Fase 2 + deploy QAS pendiente).

**Sesión 22 (2026-06-17)**: R2 FASE 2 cerrada al 100%. Backend: storage service (LocalStorage + SharePointStorage stub), POST/PATCH /documentos, POST /documentos/{id}/archivos con validación MIME/tamaño, POST /enviar con firma 2FA atómica, 4 endpoints /bandeja. Frontend: documentosApi.js, VersionEditable.js con autocomplete real, AprobacionDocumento.js refactor completo (catalogos del backend + codigo auto + firma 2FA). Tests: 31 nuevos (60 totales R2 verde). Validado E2E con Chrome DevTools. ADRs 042-045 formalizados.

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
| 7 | Schema SQLAlchemy de Organización (11 tablas) | ✅ | 15-jun | 16 clases en `backend/app/models/` — gerencia, area, usuario (+usuario_roles, usuario_modulos), rol, modulo, delegacion, ausencia, firma_digital, log_sync_ad |
| 8 | Migración Alembic inicial | ✅ | 15-jun | 10 migraciones aplicadas (head `b397cd9bfb91`). Sesión 5 cerró la tarea. **ESTADO.md previo era incorrecto (sesión 4 auditó antes de que existieran las migraciones).** |
| 9 | Endpoints /auth/login con stub + verificación 2FA | ✅ | 15-jun | `app/api/v1/auth.py` — `/login`, `/logout`, `/me`, `/verify-password`. Login contra `usuarios` (BD) o LDAP real (env-driven) |
| 10 | Endpoints /usuarios (CRUD) + /usuarios/{id}/modulos | 🟡 | 15-jun | `app/api/v1/usuarios.py` — `GET /usuarios` paginado, `GET /{id}`, `POST /sync-ad`, `GET /sync-status`. **Falta**: `PATCH /{id}` (admin), `GET/PUT /{id}/modulos` |
| 11 | Endpoints /organigrama | 🟡 | 15-jun | `GET /gerencias?activo=...` + `GET /gerencias/{id}` + `GET /areas?gerencia_id=...` + `GET /areas/{id}` cubren el organigrama publico. Faltaria: `/usuarios/{id}/delegado` y `/usuarios/{id}/ausencia` (Sesion B) |
| 12 | Endpoints /gerencias + /areas (CRUD) | ✅ | 15-jun | `app/api/v1/gerencias.py` (5 endpoints) + `app/api/v1/areas.py` (5 endpoints). ETO/ADMIN-only para mutaciones. Validacion con 5 tests cada uno (200/201/401/404/409/422). |
| 13 | Endpoints /usuarios/{id}/delegado + /ausencia | 🟡 | 15-jun | Modelos `Delegacion` y `Ausencia` ya existen en `app/models/`. Endpoints no implementados todavia (Sesion B). El campo `ausente` y `estado_delegacion` ya estan en el modelo Usuario. |
| 14 | Endpoints POST /admin/sync-ad (manual) + job 00:05 | 🟡 | 15-jun | `POST /usuarios/sync-ad` listo; falta el job Celery Beat (carpeta `workers/` existe con `celery_app.py` pero no se ven tareas de sync programadas) |
| 15 | Frontend src/utils/api.js con apiFetch | ✅ | 15-jun | `frontend/src/utils/api.js` (290 líneas) + `config.js` — CSRF auto, retry 5xx, timeout 30s, 401→login, 6 atajos (apiGet/Post/Put/Patch/Delete/Download) |
| **Tareas nuevas sesión 5 (backend ÉPICA 9)** |  |  |  |  |
| N1 | Seed organización (10 gerencias + 49 áreas) | ✅ | 15-jun | `backend/scripts/seed_organizacion.py` — 27 áreas creadas, total 50 (incluyendo 2 sigilias omitidas del Excel) |
| N2 | CRUD /api/v1/configuracion-global (US-9.01+9.02) | ✅ | 15-jun | `app/api/v1/configuracion_global.py` (6 endpoints) + modelo + migración Alembic 003. UPSERT + bulk. |
| N3 | CRUD /api/v1/feriados (US-9.01 calendario) | ✅ | 15-jun | `app/api/v1/feriados.py` (5 endpoints) + modelo + migración Alembic 004 + seed Bolivia 2026 (11 nacionales + 9 departamentales = 20) |
| N4 | CRUD /api/v1/email-templates (US-9.04, 6 plantillas) | ✅ | 15-jun | `app/api/v1/email_templates.py` (4 endpoints) + modelo + migración Alembic 005 + seed (6 plantillas) + motor Jinja2 con preview |
| N5 | CRUD /api/v1/matriz-enrutamiento-eto (US-9.03) | ✅ | 15-jun | `app/api/v1/matriz_enrutamiento_eto.py` (6 endpoints) + modelo + migración Alembic 006 + seed (10 filas + crea usuario cecEspinoza) |
| N6 | CRUD /api/v1/tipos-documento (US-9.03, 13 tipos) | ✅ | 15-jun | `app/api/v1/tipos_documento.py` (5 endpoints) + modelo + migración Alembic 007 + seed (13 tipos) |
| N7 | CRUD /api/v1/estados (US-9.03, 5 estados) | ✅ | 15-jun | `app/api/v1/estados.py` (5 endpoints) + modelo + migración Alembic 008 + seed (5 estados del flujo) |
| 16 | Refactorizar auth.js para API real | ✅ | 15-jun | `frontend/src/store/auth.js` modificado 15/6/2026 |
| 17 | Refactorizar Login.js para API real | ✅ | 15-jun | `frontend/src/pages/Login.js` modificado 15/6/2026 |
| 18 | Integrar Parametrizacion.js con API usuarios + boton sync AD | ✅ | 16-jun | Sesion 6 - tarea #10: refactor COMPLETO. `Parametrizacion.js` ya NO importa de `data/parametrosSistema.js` (verificado con grep). Nuevo módulo `frontend/src/services/parametrizacionApi.js` con 30+ funciones. Los 7 tabs cargan del backend en paralelo al `init()`. exportUsuarios delega al endpoint XLSX profesional. |
| 19 | Sanear 4 x-html con DOMPurify | ❌ | — | (no verificado — buscar `x-html` en `frontend/src/pages/*.js`) |
| 20 | Agregar CSP meta tag | ❌ | — | (no verificado) |
| 21 | Rate limit con slowapi | ❌ | — | (no implementado) |
| 22 | **TESTING R1** | ✅ | 16-jun | `backend/tests/` poblado. **193/204 tests passing en ~20s** (sesión 24). 11 tests nuevos para plantillas_documentales (100% PASS). 11 fallas preexistentes NO relacionadas con E+F (refs a enum/field antiguos). |
| **Tareas nuevas sesión 9 (Editar Usuario + Mi Perfil)** |  |  |  |  |
| N8 | Backend `GET /api/v1/roles` (catalogo) | ✅ | 16-jun | `backend/app/api/v1/roles.py` + `schemas/rol.py`. 5 roles con flag `requiere_delegado`. |
| N9 | Backend `PATCH /usuarios/{id}` con `rol_codigo` y `delegado_id` | ✅ | 16-jun | Extiende `UsuarioUpdate`. Reemplaza roles via `delete + insert` en `usuario_roles`. Asigna/quita delegado. Setea `estado_delegacion=asignado` automaticamente. `db.expire()` para refrescar relaciones. |
| N10 | Frontend: columna DELEGADO en tabla Gestion de Usuarios | ✅ | 16-jun | 3 estados visuales: verde (asignado), amber (sin delegado + rol lo requiere), gris (no requiere). |
| N11 | Frontend: modal Editar Usuario (centrado) | ✅ | 16-jun | Modal con ROL (select de BD), DELEGADO (searchable picker fuzzy), VACACION (checkbox), ESTADO (select activo/inactivo/desvinculado), Observaciones. |
| N12 | Frontend: Mi Perfil (ProfileModal) lee de BD | ✅ | 16-jun | Reemplaza mock `listaEmpleados`. Carga info del usuario, delegado, estado, ausente. PATCH con `delegado_id` y `ausente`. |
| N13 | Backend: export XLSX/CSV columna AREA = gerencia/area | ✅ | 16-jun | Formato "Gerencia / Area" con fallback a `ad_info` (department del AD) si no tiene area en BD. |
| **Tareas nuevas sesión 10 (Backup paralelo para demo)** |  |  |  |  |
| B10-1 | `.env.backup` + `deploy/docker-compose.backup.yml` + nginx config aislado | ✅ | 16-jun | Stack completo en puertos 8081/5174/18001/25433/26380/8026/1026. Container prefix `sgd-bk-`, volume prefix `sgd-bk_`, network `sgd-bk-net`, DB `sgd_backup`. |
| B10-2 | `scripts/start-stack-backup.bat` + `stop-stack-backup.bat` | ✅ | 16-jun | Orquestador automatizado: up pg/redis → cp dump → pg_restore → up resto → wait health → URLs. |
| B10-3 | `backups/20260616_150015/` (dump + working tree) | ✅ | 16-jun | pg_dump -Fc (119KB) + 393 archivos de codigo (31.82MB total). Permite restaurar el estado exacto. |
| B10-4 | `docs/PR/BACKUP-PARALELO.md` | ✅ | 16-jun | Doc completa: URLs, troubleshooting, limitaciones, comandos. |
| **Tareas nuevas sesión 12 (Fase 1 PENDIENTES-R1: restaurar CRUD Parametrizacion)** |  |  |  |  |
| N14 | `backend/scripts/seed_configuracion_global.py` (11 params) | ✅ | 16-jun | Idempotente. VIGENCIA (4) + SEMAFORO (2) + ARCHIVOS (2) + DESCARGAS (3). Cubre las 5 claves faltantes del PENDIENTES-R1. Commit `29001ae`. |
| N15 | `frontend/src/pages/Parametrizacion.js`: eliminar duplicacion handlers | ✅ | 16-jun | Borrada la 2da declaracion mock (lineas 537-784, 247 lineas). Renombrado `gerEditSigla` -> `gerEditCod`. Dropdown Tipos Excluidos ahora muestra catalogo real. Commit `4b75cdc`. -240 lineas netas (2153 -> 1897). |
| **Tareas nuevas sesión 13 (PENDIENTES-R1 segunda tanda, comiteadas en af1de7d)** |  |  |  |  |
| N16 | A1-A11 bugfixes (refresh, errores Alpine, export, logs, paginacion) | ✅ | 16-jun | Commit `af1de7d fix(frontend+backend): Parametrizacion UI bugs (A1-A11) + auth cross-origin` |
| N17 | Refactor `tipos_documento`: codigo int UNIQUE + slug + nombre UNIQUE, drop codigo_doc | ✅ | 17-jun | Modelo + schema + endpoints + seed actualizados. Migracion 6b244889632f (data-migration + drop column). Commit en sesion 14. |
| N18 | Semaforizacion por tipo de tarea (modelo + API + UI) | ✅ | 17-jun | `app/api/v1/semaforizacion_tarea.py` (4 endpoints) + modelo + migracion f04b96c6dff2. Tab UI con 4 tipos (REVISION, APROBACION, CONTROL_LECTURA, EVALUACION). |
| N19 | Plantillas notificacion: 10 plantillas (ampliar enum) | ✅ | 17-jun | enum de 6 a 10 codigos. Seed actualizado. Migracion 6451593bcab5. |
| N20 | Editor Tiptap para plantillas (B/I/U/S/H1-3/listas/code/color/fontSize/undo) | ✅ | 17-jun | `frontend/src/components/PlantillaEditor.js` (106 lineas) + toolbar HTML en Parametrizacion.js (lineas 1912-1951) + lifecycle completo (mount, selectionUpdate, transaction). 5 deps Tiptap 3.26.1 en package.json. **Sesion 16**: editor en closure del factory (root cause fix), TextStyleKit, @mousedown.prevent, commands.setColor/setFontSize. |
| **Tareas nuevas sesión 14 (recuperacion + cierre pendientes)** |  |  |  |  |
| N21 | Fix bug preexistente `sgd-qas.conf` en `conf.d/` de DES | ✅ | 17-jun | Movido a `sgd-qas.conf.bk`. Nginx ya no redirige a HTTPS inexistente. Commit `beafe03`. |
| N22 | Docker compose con `${VAR:-default}` en env vars | ✅ | 17-jun | Todas las env vars del backend tienen default. Resuelve el loop de sesión 13. |
| N23 | API_BASE relativa (cross-origin auth fix) | ✅ | 17-jun | `frontend/src/utils/config.js`: `'http://localhost:18000/api/v1'` → `'/api/v1'`. Cookies de sesión se manejan via Nginx (mismo origin). |
| N24 | `seed_configuracion_global.py` agregado a `start-stack-qas.sh` | ✅ | 17-jun | 8/8 seeds (antes 7/7). REQUIRED_FILES y SEEDS arrays actualizados. Conteo BD incluye `configuracion_global` y `semaforizacion_tarea`. Commit `1ebfe5e`. |
| N25 | Fix Tiptap duplicate underline | ✅ | 17-jun | Tiptap 3.x StarterKit ya incluye Underline. Removido import adicional y dep `extension-underline`. Commit `d135788`. |
| **Sesion 16** | | | | |
| N26 | Tiptap+Alpine root cause fix (closure pattern) | ✅ | 17-jun | Editor movido a `let editor` en closure del factory `Alpine.data('paramPage', ...)` segun doc oficial de Tiptap Alpine. Eliminado el `_editorHandle` intermedio. Commit `a154bc4`. **Bug "Applying a mismatched transaction" RESUELTO definitivamente** (workaround de reload limpio ya no necesario). |
| N27 | Tiptap color/fontSize con TextStyleKit | ✅ | 17-jun | Reemplazado `TextStyle + Color` por `TextStyleKit` (incluye FontSize). Usar `editor.commands.setColor/setFontSize` (commands, no chain methods). |
| N28 | WSIWYG @mousedown.prevent en toolbar | ✅ | 17-jun | Aplicado a 17 botones (16 toolbar + 1 chip de variable) para evitar que roben focus del editor. |
| N29 | Validacion persistencia Tiptap -> BD | ✅ | 17-jun | Editor -> PATCH /email-templates/{cod} -> BD verificada con `psql`. F5 + re-login recupera contenido correctamente. |
| N30 | Validacion previsualizar con MOCK data | ✅ | 17-jun | Preview genera HTML con variables {{...}} sustituidas por mock. |
| **Sesion 17 (cierre R1)** | | | | |
| N31 | Fix Matriz ETO dropdowns binding (Alpine 3 quirk) | ✅ | 17-jun | Convertir analista_id/delegado_id a string en mapeo, agregar data-attrs, forzar value en await nextTick. Mismo fix al checkbox. Commit `df4aceb`. |
| N32 | Eliminar opcion "Previsualizar" de plantillas | ✅ | 17-jun | -30 lineas netas. Estado, 2 handlers, boton, overlay, 3 x-if condicionales. Tiptap es WYSIWYG, no necesita preview. Commit `df4aceb`. |
| N33 | Impersonate funcional: ADMIN/ETO + no-auto + audit dedicado | ✅ | 17-jun | Backend admin_impersonate acepta ETO. Validaciones no-auto + no-doble-impersonate. write_audit con recurso='impersonate' + accion dedicada IMPERSONATE_START/STOP. Bugfix preexistente ad_user['dn']. Commit `4763ff9`. |
| N34 | Banner sticky de impersonate en AppLayout | ✅ | 17-jun | Banner TOP fixed con gradiente amber→orange→red, visible en todas las paginas autenticadas. Padding-top dinamico. Boton "Terminar Impersonate" via CustomEvent. Commit `4763ff9`. |
| N35 | Frontend impersonarUsuario + stopImpersonate | ✅ | 17-jun | Validaciones frontend (rol + no-auto). refreshFromBackend en vez de window.location.hash. Boton Impersonar solo visible para admin/eto. Commit `df4aceb` (impersonarUsuario/stopImpersonate) + `4763ff9` (handler del store). |
| **Sesion 18 (refresh bug #15 RESUELTO)** | | | | |
| N36 | Fix refresh bug: race auth.init vs initRouter | ✅ | 17-jun | 3 cambios: (1) auth.js init() restaura SINCRONO desde localStorage + flag isReady. (2) router/index.js guard !isReady con loader (no redirige durante init). (3) debug page /_debug/session permanente. 6/6 smoke tests Chrome MCP. Commit `733e8b6` |
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
| 4.3 | ychavez sin Área en Mi Perfil | 🟠 | CRIT (fix) | `f9c3629` | Fallback a u.ad_department en ProfileModal.js |
| 3.1 | Delegado obligatorio al asignar eto/revisor | 🟠 | CRIT (fix) | `a63b453` | Validación bloqueante reemplazada por confirm() no bloqueante. Label "sugiere delegado". |
| 4.1 | Botón Sincronizar AD 403 para ETO | 🟠 | CRIT (fix) | `dcfb46b` | x-show=role==admin en ambos botones. Cubre también Issue 8.2. |
| 10.1 | Política de Descargas hardcodeada | 🟠 | CRIT (fix) | `235ad86` | VersionEditable.js carga desde BD (config DESCARGAS). Default 1, el cliente cambia a 1 en BD. |
| 11.1 | Quitar Analista ETO del wizard paso 1 | 🟠 | CRIT (fix) | `1371aec` | Estado, validación, UI y F1 fetch removidos. analistasEtoList se mantiene para paso 3. |
| 11.2 | UI Reemplazo o baja + sub-bug chipsReemplazo | 🟠 | CRIT (fix) | `5a23846` | UI select+chips agregado. Fix: chipsReemplazo se enviaba como `[]` (vacio) en vez del array de códigos. |
| 11.3 | Wizard no persiste en documento_flujo | 🟠 | CRIT (NO-BUG) | `3cd5c2d` | Test e2e con curl + 2 tests pytest: flujo SÍ persiste. Sub-bug: modelo `reemplaza_documento_ids` era `list[int]`, ahora `list[str]` (códigos). |
| 4.2 | soporteglpi sin SAP en login on-demand | 🟡 | IMP (fix) | `19e2b36` | ldap_get_user_by_samaccountname retorna None si sin postalCode (alineado con sync_ad). |
| 4.4 | Sync AD: mapping ad_info→area_id automático | 🟡 | IMP (feat) | `b9cf37a` | Nuevo módulo `area_mapping.py` con match por palabra completa. Aplicado en sync_ad masivo y login on-demand. 15 tests. |
| 8.1 | Filtros activos/inactivos + ausentes en Gestión Usuarios | 🟡 | IMP (feat) | `dc2efe0` | Backend: nuevo param `ausente: bool`. Frontend: 2 selects. |
| 8.4 | REPORTES en Excel para elaboradores | 🟡 | IMP (feat) | `7aa64c0` | Script `add_reportes_module.py` idempotente: 154 usuarios asignados, 0 errores. |
| 5.1 | Selector Estados con 4 opciones (PROCESO/TAREA/ACCION/AMBOS) | 🟡 | IMP (fix) | `0bcb499` | Selector ampliado a 4 valores UPPERCASE que matchean enum backend. Badge con 4 colores. |
| 1.2 | Lista delegados corta (solo hasta D) | 🟡 | IMP (fix) | `5331d34` | Reemplazado con `listPorCualquierRol([3 roles relevantes])`. page_size 200→500. |
| 7.1 | Matriz ETO: dropdown delegado solo ETO | 🟡 | IMP (fix) | `9554ad7` | Dropdown delegado ahora itera sobre `analistas` (ya filtrado a ETO). |
| 2.1 | Performance login - Promise.all en ProfileModal | 🟡 | IMP (perf) | `bb3a06d` | 3 requests en paralelo (antes 5 en serie). 2.4x más rápido. |
| 8.3 | Header 'Área' (no 'Gerencia / Área') | 🟢 | MENOR (fix) | `4335665` | Header tabla y XLSX cambiados a "Area". Contenido se mantiene. |
| 8.5 | KPI inactivos + desvinculados | 🟢 | MENOR (feat) | `e92a369` | Backend: 2 nuevos kpis. Frontend: 2 nuevos cards (grid 3→5 cols). |
| 9.1 | /plantillas vista tienda responsive | 🟢 | MENOR (fix) | `c4f501c` | Grid: 1/2/3/4 cols según breakpoint (mobile/tablet/desktop/large). |
| 9.2 | Quitar bloque 'IA — Recomendación' | 🟢 | MENOR (fix) | `c4f501c` | Removido del template. |
| 6.1 | Ocultar columna SLUG en tipos_documento | 🟢 | MENOR (fix) | `f112a68` | Header: Tipo | Cód. Doc | Acciones. Slug sigue en form (hidden) y en modelo. |

**Resumen:** 22 issues cerrados, 21 commits atómicos, 217/228 tests PASS (+15 nuevos). 2 issues marcados como NO-BUG (1.1 y 11.3) con cobertura de tests para evitar regresión.

---

## Progreso R1
**38/38 tareas R1 + EPICA9 + Parametrizacion (100% CERRADO)** = **41/41 con la sesión 17 (Matriz ETO + Previsualizar + Impersonate) + sesión 18 (Refresh bug #15 RESUELTO)** = **42/42**. Tests pytest 123/123.

## Progreso QAS
**8/8 tareas QAS (100%)**: stack completo en https://sgdqas.cofar.com.bo + HTTPS + AD real + 8 seeds (incluye `seed_configuracion_global.py` en sesión 14) + sync AD automatizado (753 usuarios) + `start-stack-qas.sh` 1-click.

## Progreso R2
**17/21 tareas R2 completadas (FASE 1 + FASE 2 cerradas en sesiones 21+22, branch `r2/wizard-y-version-editable`)**. Plan completo + 2 fases ejecutado. 60 tests pytest R2 (33 FASE 1 + 27 FASE 2), 100% verde. 10 documentos sembrados idempotentemente + 1 creado via POST live. Regla "VENCIDO → APROBADO u OBSOLETO" validada. Wizard AprobacionDocumento.js refactor completo con catalogos del backend + firma 2FA real. VersionEditable.js con autocomplete real (BD). E2E validado con Chrome DevTools (aromero ve catalogos reales, codigo auto CC-1-002/00 generado correctamente).

**Handoff para sesion 23:** Pendiente refactor Bandeja.js + LiberacionDetalle.js + ListaMaestra.js (tareas 38-40), trigger obsolescencia (R5), deploy QAS con R2 completo.

## Total
**38/49 tareas (78%)** + 4 bonus ya entregados + 8 tareas QAS automatizadas + 5 tareas nuevas sesión 16 + 1 tarea nueva sesión 18 (refresh bug fix) = **86%**

## Tablas de BD
**21/28 migradas** (16 originales + 6 sesión 5 + 1 sesión 6 + 1 sesión 9 + 3 sesión 13/14: refactor tipos_documento + semaforizacion_tarea + expand plantillas enum).

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

> **Backlog de issues identificados durante sesiones de desarrollo.**
> Cada bug tiene: severidad, impacto, workaround actual, sesion sugerida para resolver.
> Agregar aqui cualquier nuevo bug发现的. No son bloqueantes pero conviene resolverlos en algun momento.

| # | Bug | Severidad | Impacto | Workaround | Sesion sugerida |
|---|---|---|---|---|---|
| B1 | `areas.sigla UNIQUE` global impide re-crear un area con la misma sigla despues de borrado logico | 🟡 Media | UX: usuario no puede "revivir" un area con sigla identica | PATCH con sigla nueva antes de borrar, o fixear el modelo a `UniqueConstraint('gerencia_id', 'sigla')` | Sesion B (tarea #9d) |
| B2 | `Gerencia.areas` tiene `cascade="all, delete-orphan"` en la relacion ORM | 🟡 Media | Si se hace DELETE fisico de un Gerencia desde el ORM, se borran las areas hijas. Incompatible con borrado logico. | El router usa solo borrado logico (activo=false). NO hay DELETE fisico en la API. | Sesion B (tarea #9d) |
| B3 | NO existe middleware CSRF en backend (solo se setea cookie en `/login`) | 🟠 Alta | El header `X-CSRF-Token` que envia `api.js` no se valida en el backend. Vector de CSRF si el sitio se sirve desde otro origen. | Confiar en que `allow_origins` de CORS este bien configurado y `credentials: include` funcione. | Sesion B (seguridad hardening, despues de CSP) |
| B4 | `build-error` de Vite falla por `manualChunks` como objeto en `vite.config.js` (no funcion). Preexistente. | 🟢 Baja | Solo afecta `npm run build` de frontend. El dev server (HMR) funciona. | Cambiar `manualChunks` a funcion en `frontend/vite.config.js`. | Sesion B (cuando se haga build de produccion) |
| B5 | `frontend/src/data/*.js` aun tiene datos hardcoded del mock legacy | 🟡 Media | Componentes que importen de ahi muestran datos desactualizados, no los del backend. | El refactor de `Parametrizacion.js` a `apiFetch` (Sesion B tarea #10) cubre los principales. | Sesion B (tarea #10) |
| B6 | PowerShell + `http.client` filtra cookies `#HttpOnly_` en scripts de validacion | 🟢 Baja | Solo afecta a tests manuales. NO al backend ni al frontend. | Usar `urllib.request.Request` con headers manuales o el script `test_*.py` que ya tiene el fix. | N/A (solo tooling) |
| B7 | Modelos SQLAlchemy NO tienen `__repr__` consistente (algunos si, otros no) | 🟢 Baja | UX: logs de SQLAlchemy muestran `<Modelo at 0x...>` en vez de algo legible | Agregar `def __repr__` a los modelos que faltan. | Sesion B (cleanup) |
| B8 | `auth.py` logica de password dummy `cofar.2026` hardcoded | 🟠 Alta (en QAS) | En DES esta OK, pero si llega a QAS con `LDAP_ENABLED=false` se acepta cualquier pass. | Verificar que `LDAP_ENABLED=true` en QAS/PRD. Ya documentado. | Pre-deployment QAS |

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
- ADR-001 a ADR-027 (ver `DECISIONES.md`)
- ADR-013: **Backend DENTRO de Docker en DES** (invalidado el draft inicial sesión 4, reescrito sesión 5 con networkingMode=mirrored + DNS custom)
- ADR-014: AuditLog append-only via `write_audit()` no-bloqueante (sesión 6)
- ADR-015: `areas.sigla` UNIQUE(gerencia_id, sigla) en vez de global (sesión 6)
- ADR-016: Mapeo EXPLICITO de normalización de módulos (sesión 8)
- ADR-017: Preferencia por `id ASC` cuando hay duplicados de `ad_postal_code` (sesión 8)
- ADR-018: Skip delegado con warning (sesión 8, deuda #13)
- ADR-023: QAS deploy usa Docker stack con cert autofirmado (sesión 10)
- ADR-024: celery-beat usa `-s /app/storage/celerybeat-schedule` (sesión 10, ratificado sesión 11)
- ADR-025: Workflow de migración es `deploy-qas.bat` (sesión 10)
- ADR-026: `start-stack-qas.sh` es el punto único de entrada para QAS (sesión 11)
- ADR-027: Sync AD output path = `/app/storage/` (sesión 11)

## Bloqueos identificados

**Al cierre de sesión 11 (2026-06-16), NO hay bloqueos críticos.**

Bloqueos menores pre-QAS-public:
- 🟠 B3: CSRF middleware ausente (seguridad pre-QAS-public)
- 🟠 B8: `auth.py` password dummy `cofar.2026` (pre-QAS-public; ya validado que en QAS `LDAP_ENABLED=true` por lo que no aplica)
- 🟠 QAS password `sistemas` SSH (cambiada en sesión 11 — ahora se accede por SSH key)
- 🟠 QAS sudo NOPASSWD `ALL` (recomendable restringir a comandos específicos)
- 🟠 QAS cert HTTPS autofirmado (cambiar a Let's Encrypt o cert corporativo pre-PUBLIC)

Backlog menor:
- 🟡 B2: `Gerencia.areas` cascade cleanup opcional
- 🟡 B4: `vite.config.js` manualChunks
- 🟡 B5-B7: cleanup varios
- 🟡 #13: Deuda delegado (sesión 8)
- 🟡 #14: Cargos a areas (pendiente)
- 🟡 Backups automáticos en QAS (cron + pg_dump, no automatizado)

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
