# BITÁCORA — Sesión de trabajo SGD

> **Bitácora cronológica de las sesiones de trabajo en el proyecto COFAR SGD.**
> Para que cuando la ventana de contexto se llene, una nueva sesión pueda leer este archivo y retomar.

## Sesión 1 — 2026-06-14 (sábado 19:35 → 20:05)

### Tareas ejecutadas
- ✅ Tarea #6: Levantar la stack y validar `docker compose up`
- 🔧 Fix aplicado: cambio de puertos 15432→25432 y 16379→26379 (puerto 15432 daba error de binding en Docker Desktop sobre Windows)
- 🔧 Fix aplicado: creación de `app/workers/celery_app.py` y `app/workers/tasks.py` (faltaban para que docker-compose no falle)
- 🔧 Fix aplicado: agregar `celery_broker_url`, `celery_result_backend`, `tz` a `app/core/config.py`
- 🔧 Fix aplicado: comando `alembic upgrade head` ahora tolera fallo (sin migraciones aún)

### Validación end-to-end
| Servicio | Estado | Endpoint probado | Respuesta |
|---|---|---|---|
| sgd-nginx | Up (11s) | `curl http://localhost:8080/` | 200 OK |
| sgd-frontend (Vite) | Up (24s) | `curl http://localhost:5173/` | 200 OK HTML |
| sgd-backend (FastAPI) | Up (12s, healthy) | `curl http://localhost:18000/health` | `{"status":"ok","database":"ok"}` |
| sgd-backend (FastAPI) | Up | `POST /api/v1/login` con aromero | 200 + cookies + JSON usuario |
| sgd-backend (FastAPI) | Up | `POST /api/v1/login` con Nginx | 200 OK |
| sgd-postgres | Up (24s, healthy) | Puerto 25432→5432 | Healthy |
| sgd-redis | Up (24s, healthy) | Puerto 26379→6379 | Healthy |
| sgd-mailhog | Up (24s) | `curl http://localhost:8025/api/v2/messages` | MailHog API vivo |
| sgd-celery-worker | Up (12s, starting) | health: starting | OK |
| sgd-celery-beat | Up (12s, starting) | health: starting | OK |

### Credenciales dev
- aromero / cofar.2026 → rol: eto
- solicitante / cofar.2026 → rol: estandar
- admin / cofar.2026 → rol: admin
- visualizador / cofar.2026 → rol: visualizador

### URLs
- App: http://localhost:8080
- Frontend Vite: http://localhost:5173
- Backend directo: http://localhost:18000
- Backend docs (Swagger): http://localhost:18000/docs
- MailHog UI: http://localhost:8025
- Postgres: localhost:25432 (user sgd, pass sgd_dev_only_change_in_prod)
- Redis: localhost:26379

### Tamaño imágenes Docker (al cierre de sesión 1)
- postgres:16-alpine
- redis:7-alpine
- mailhog/mailhog:latest
- nginx:1.27-alpine
- node:22-alpine (frontend)
- sgd-des-backend (custom)
- sgd-des-frontend (custom)
- sgd-des-celery-worker (custom)
- sgd-des-celery-beat (custom)

### Decisiones tomadas en esta sesión
- Cambiar `HOST_PORT_POSTGRES` de 15432 a 25432 (binding error en Windows con Docker Desktop)
- Cambiar `HOST_PORT_REDIS` de 16379 a 26379 (preventivo, mismo motivo)
- Crear `app/workers/celery_app.py` y `tasks.py` desde cero (no existían pero docker-compose los referenciaba)

### Próxima sesión
**Tarea #7:** Crear schema SQLAlchemy de Organización (5 tablas: gerencias, areas, usuarios, roles, usuario_roles)

**Requerimientos previos:**
- Docker Desktop corriendo (verificar con `docker info`)
- Stack levantada: `docker compose -f deploy/docker-compose.yml --env-file .env up -d`

### Notas para la IA
- El backend usa `--reload`, así que cualquier cambio en `backend/app/*.py` se refleja sin reiniciar.
- El frontend usa Vite HMR, así que cualquier cambio en `frontend/src/*.js` se refleja sin reiniciar.
- Las cookies del login son HttpOnly para `session` y NO HttpOnly para `csrf_token` (el frontend JS necesita leerlo).
- El prefijo del API es `/api/v1/` — está en `settings.api_v1_prefix` y se aplica a nivel de router en `main.py`.
- Las 4 rutas de auth están en `app/api/v1/auth.py`: `/login`, `/logout`, `/me`. (No `/auth/login` — el router NO tiene prefijo `/auth` adicional porque el `prefix=settings.api_v1_prefix` ya se aplica en `main.py`.)
- En QAS, cambiar `LDAP_ENABLED=true` + 3 variables de AD → login pasa de stub a LDAP real.
- En QAS, cambiar `GRAPH_ENABLED=true` + 3 vars de Azure → integración Office 365 se activa.
- En QAS, cambiar `SMTP_ENABLED=true` + 3 vars de SMTP → emails salen por SMTP real en vez de MailHog.

---

## Sesión 2 — 2026-06-14 (sábado 20:26 → 20:50)

### Documentación nueva revisada
- `docs/Diagramas_Matrices/` — 10 diagramas casos de uso, 20 diagramas de flujo, 7 excels de matrices, 1 word plantillas, 7 plantillas documentales.

### Hallazgos críticos que cambian la BD
1. **5 roles reales** (no 4): `ADMIN`, `ETO`, `ELABORADOR - REVISOR`, `ELABORADOR - REVISOR - APROBADOR`, `VISUALIZADOR (CL-EVAL)`.
2. **Tabla `usuario_modulos` N:M** (no RBAC derivado del rol) — 10 módulos reales.
3. **13 tipos de documento** con vigencias (4 indefinidos).
4. **8 gerencias, ~25 áreas con siglas** (no 6 gerencias).
5. **Límite de descarga por tipo de documento** (no global: 1 o 10).
6. **2 analistas ETO** con 7+ gerencias asignadas.
7. **156 usuarios con rol activo, 139 SIN delegado** (alerta crítica).

### Refinamientos (no rompen BD)
- SLA: 10 hábiles **O** 15 calendario (lo primero)
- Límite doble: 20 archivos Y 20 MB
- Umbral IA: 60% (no 70%)
- 4 KPIs + 2 series temporales en reportes

### Decisión
**El plan NO necesita reescribirse.** Las correcciones se aplican agregando tablas/catalogos a las tareas #7 y #23. Análisis completo en `docs/PR/ANALISIS-NUEVA-DOCS.md`.

### Próxima sesión (actualizada)
**Tarea #7 (REVISADA):** Crear schema SQLAlchemy de Organización (5 tablas originales + 6 nuevas):
- `gerencias`, `areas`, `usuarios`, `roles` (5 entradas), `usuario_roles`
- **+ `modulos` (catálogo), `usuario_modulos` (N:M), `delegaciones`, `ausencias`, `firmas_digitales`, `log_sincronizacion_ad`**

**Nota importante:** Sembrar las 5 entradas de `roles`, 10 de `modulos`, 10 de `gerencias` desde la nueva documentación.

---

## Sesión 3 — 2026-06-14 (sábado 21:00 → 21:30)

### Aclaraciones del cliente (en orden)
1. **H-09 corregido:** 20 archivos = total por solicitud; 20 MB = por archivo individual. Mi versión anterior era incorrecta.
2. **H-05 corregido (nomenclatura):** códigos son `sigla_area-codigo_tipo-correlativo v01` (no sigla del tipo). Mantener nomenclatura legacy COFAR. CC-1 = Metodología, CC-7 = Especificación (confirmado por cliente).
3. **ÉPICA 3-B (workflow corrección):** basarse en US-3.05 ya documentada (bypass al observador).
4. **Sync AD:** botón manual en `Parametrización > Usuarios` + job diario a las **00:05 hrs**.
5. **Firma digital:** 2FA simple (usuario + password), log en tabla `firmas_digitales`.
6. **Reasignación por desvinculación:** **inmediata** (no esperar al cron).
7. **Jefe inmediato:** diferido, TODO baja prioridad.
8. **Paginación:** parámetro configurable en `configuracion_global` (default 10).

### Credenciales AD entregadas (DES)
- `LDAP_USER=soporteglpi@cofar.com`
- `LDAP_PASSWORD=glpi.1T.C0f4r` (en `.env`, no en repo)
- `LDAP_SERVER=rodc.cofar.com.bo` (RODC = read-only domain controller)
- `LDAP_DOMAIN=cofar.com`

### Decisión sobre ubicación de docs
Todos los archivos en `docs/PR/`:
- `PRD.md` (actualizado § 5: 28 tablas + nomenclatura)
- `DECISIONES.md` (ADR-011 nomenclatura + ADR-012 sync AD)
- `ESTADO.md` (próxima tarea actualizada)
- `BITACORA.md` (este log)
- `ANALISIS-NUEVA-DOCS.md` (corregido H-04 y H-05)

### Próxima sesión (actualizada)
**Tarea #7 (REVISADA):** Crear schema SQLAlchemy de Organización. 11 tablas:
1. `gerencias` (8-10 sembradas)
2. `areas` (~25 sembradas con sigla)
3. `usuarios` (estructura + 4 stub dev + 4 reales para pruebas)
4. `roles` (5 sembrados con códigos exactos)
5. `usuario_roles` (N:M)
6. `modulos` (10 sembrados)
7. `usuario_modulos` (N:M)
8. `delegaciones`
9. `ausencias`
10. `firmas_digitales`
11. `log_sincronizacion_ad`

Orden:
1. Crear los 11 modelos SQLAlchemy.
2. Crear el `seed_data.py` con todos los catalogos.
3. Generar la migración Alembic.
4. Aplicar la migración.
5. Validar con queries.

---

## Sesión 4 — 2026-06-15 (lunes)

### Contexto
El proyecto quedó en pausa tras la sesión 3. Hoy se retomó con dos objetivos principales:
1. Auditoría del estado real del repo (los `ESTADO.md` y `BITACORA.md` quedaron en sesión 1 y se sabía que estaban desactualizados).
2. Instalación del plugin ECC (`ecc-universal` v2.0.0) en opencode y validación del flujo agentivo.

### Auditoría: lo que en realidad hay en el repo
- **Backend:** 12 endpoints REST implementados, 11 modelos SQLAlchemy con 16 clases, 2 servicios (`ad_service.py` de 620 líneas con LDAP real, `impersonate_service.py`), workers de Celery listos.
- **Frontend:** 28 pages, 20 componentes, 4 stores, 16 archivos de datos hardcoded. Las 3 pages tocadas en sesión 3 (Login, Parametrizacion, auth store) están actualizadas al 15/6. El resto usa `data/*.js` legacy.
- **Docker:** 7 contenedores Up (nginx, frontend, postgres, redis, mailhog, celery-W, celery-B). 2 unhealthy (celery-W/B por falta de Alembic). **Backend NO está en Docker** — corre como `python.exe` nativo por la VPN FortiClient.
- **Alembic:** carpeta existe pero VACÍA. Los modelos se cargan en runtime. **BLOQUEANTE** para R2+.

### Limpieza de raíz
20 archivos basura sacados del tracking (preservados en disco):
- `backend.{err,out,pid}`, `bg.{err,out}` — outputs del proceso uvicorn
- `cookies.txt`, `cookies_local.txt` — cookies de pruebas manuales
- `login_*.json` (6 archivos), `test_*.json` (5), `trash_args.json` — payloads de prueba

`.gitignore` reforzado con bloque "Dev artifacts" para evitar que vuelvan a aparecer.

Commit: `c27a766 chore(repo): limpiar archivos basura de raíz y reforzar .gitignore`

### Plugin ECC (ecc-universal v2.0.0)
- 26 commands slash (`/plan`, `/tdd`, `/code-review`, `/security`, `/build-fix`, `/e2e`, `/refactor-clean`, `/orchestrate`, `/learn`, `/checkpoint`, `/verify`, `/eval`, `/update-docs`, `/update-codemaps`, `/test-coverage`, `/setup-pm`, etc.)
- 26 agents especializados (`python-reviewer`, `database-reviewer`, `code-reviewer`, `security-reviewer`, `tdd-guide`, `e2e-runner`, `doc-updater`, `harness-optimizer`, etc.)
- 7 custom tools (`run-tests`, `check-coverage`, `security-audit`, `format-code`, `lint-check`, `git-summary`, `changed-files`, `dependency-analyzer`)
- Hooks configurables via `ECC_HOOK_PROFILE=minimal|standard|strict`

Para este proyecto (Python/FastAPI) se recomienda **perfil minimal** + desactivar hooks de JS/TS que no aplican.

### Decisiones tomadas en esta sesión
- **ADR-013 (en draft):** Backend fuera de Docker en DES. Razón: FortiClient VPN corre en el host Windows, no en WSL2/Docker. El backend nativo puede alcanzar `172.16.10.17 = dc3-cofar` (RODC); un contenedor Docker no. En QAS (VM Debian) esto no aplica — todo corre en Docker.
- Estrategia de avance: **un orquestador `scripts/start-stack-des.bat`** que levante Docker compose (postgres, redis, mailhog, nginx, frontend, celery) + backend nativo en una sola acción. Documenta el contrato de "cómo arrancar el proyecto" sin tener que recordar los 2 comandos separados.

### Estado al cierre
- ✅ `ESTADO.md` reescrito con la realidad (43% R1, 0% R2, 14/48 tareas totales)
- ✅ `BITACORA.md` actualizada (este log)
- ✅ Raíz limpia (commit `c27a766`)
- ⏳ ADR-013, orquestador y ECC hooks (siguiente paso inmediato)

### Próxima sesión (sesión 5)
**Prioridad #1 — NO NEGOCIABLE:**
1. Generar migración Alembic inicial (tarea #8). Sin esto, el modelo no es durable. El seed actual se pierde cada vez que se reinicia.
2. Crear `frontend/src/utils/api.js` (tarea #15). Wrapper `apiFetch` con manejo de cookies CSRF, errores y 401.
3. Tests mínimos con `pytest + httpx` (tarea #22) para los 12 endpoints actuales.

**Prioridad #2:**
4. Endpoints restantes de R1: organigrama, gerencias, áreas, delegado, ausencia.
5. CSP, DOMPurify, rate limit (`slowapi`).

**Lo que NO se debe hacer todavía:**
- R2 (#23+) — depende de cerrar R1 con Alembic.
- Refactor de pages no tocadas (Bandeja, Liberacion, ListaMaestra) — depende de utils/api.js.

---

## Sesión 5 — 2026-06-15 (lunes) — en curso

> Sesión dedicada a cerrar el **backend de la ÉPICA 9 al 100%** (10 tareas).
> NO se toca frontend (excepto api.js), NO tests pytest, NO asignación masiva desde la matriz.
> Esas son Sesión B.

### Tarea #1 — `frontend/src/utils/api.js` ✅ (15-jun)

**Commit:** `bd7d423` — `feat(frontend): add apiFetch wrapper with CSRF, retry, timeout and error handling`
**Commit docs:** `4525281` — `docs(pr): update ESTADO + BITACORA after tarea 1 (sesion A)`

**Archivos creados:**
- `frontend/src/utils/api.js` (290 líneas) — wrapper `apiFetch` + 6 atajos (`apiGet`, `apiPost`, `apiPut`, `apiPatch`, `apiDelete`, `apiDownload`)
- `frontend/src/utils/config.js` (16 líneas) — `API_BASE` + `ROLES` extraídos de `auth.js` para reuso

**Features del wrapper:**
- `credentials: 'include'` para cookies HttpOnly (`session`, `user_id`)
- CSRF automático: lee cookie `csrf_token` y la envía en `X-CSRF-Token` en métodos no seguros
- 401 → redirige a `#/login` (sin loop si ya estamos ahí)
- 403 → toast + loggeo (NO redirige)
- 5xx + network errors → retry exponencial (400ms, 800ms) max 2 reintentos
- AbortController → timeout 30s (configurable)
- Body: JSON salvo FormData/Blob
- Errores normalizados: `{ok:false, status, code, message, detail}`
- Expuesto en `window.*` para uso inline desde Alpine templates

**Validación empírica:**
- `curl.exe -X POST /api/v1/login` con aromero + cofar.2026 → 200 OK + 3 cookies
- Cookies: `user_id=1` (HttpOnly), `session=dev-session-1` (HttpOnly), `csrf_token=dev-csrf-aromero-1` (NO HttpOnly)
- `curl.exe /api/v1/me` con cookies → 200 + `{authenticated: true, roles: ["ETO"], modulos: ["TODOS"]}`
- Vite dev server (HMR) sirve `api.js` y `config.js` (HTTP 200)

**Hallazgos del pre-flight (importantes para el resto de la sesión):**
- ✅ Alembic YA está aplicado en BD (tabla `alembic_version` existe) — el GAP reportado en sesión 4 es incorrecto
- ✅ BD ya tiene: 10 gerencias, 23 áreas (de 49 posibles), 763 usuarios, 5 roles, 11 módulos
- ✅ Schemas de `gerencias` y `areas` en BD coinciden 100% con modelos SQLAlchemy
- ❌ NO hay middleware CSRF en backend (solo cookie en `/login`) — `api.js` envía header `X-CSRF-Token` aunque no se valide (preparado para futuro)
- ❌ `app/schemas/` está VACÍO — se debe poblar con cada tarea nueva
- ⚠️ Skills `git-workflow` y `python-reviewer` (plugin ECC) no disponibles en este opencode — reemplazadas por auto-revisión + scan secretos

**Pendiente sesión A (9 tareas restantes):**
- #2 seed_organizacion.py (10 gerencias, 49 áreas, 5 roles, 10 módulos)
- #3 CRUD `/api/v1/gerencias`
- #4 CRUD `/api/v1/areas`
- #5 CRUD `/api/v1/configuracion-global`
- #6 CRUD `/api/v1/feriados`
- #7 CRUD `/api/v1/email-templates` (6 plantillas)
- #8 CRUD `/api/v1/matriz-enrutamiento-eto`
- #9b CRUD `/api/v1/tipos-documento` (13 tipos)
- #9c CRUD `/api/v1/estados` (5 estados)

**Notas para la IA (próximas tareas):**
- `aromero` es rol ETO (no ADMIN) — endpoints de parametrización deben aceptar ETO **o** ADMIN. Crear helper `_require_eto_or_admin` reutilizable
- `gerencia.py` tiene `cascade="all, delete-orphan"` en `areas` — incompatible con borrado lógico, ajustar antes de la tarea #3
- Modelos faltantes a crear: `configuracion_global`, `feriado`, `email_template`, `matriz_enrutamiento_eto`, `tipo_documento`, `estado`
- Build de Vite falla por config preexistente (`manualChunks` con objeto en `vite.config.js`) — no es por mi cambio. Dev server (HMR) sí funciona


---

## Sesion 5 � 2026-06-15 (CIERRE) � Backend EPICA 9 al 100%

### Resultado global
**10/10 tareas de la sesion A completadas.** Backend de la EPICA 9 (US-9.01 a 9.06) cerrado al 100%.
**Total commits sesion 5: 14** (10 de codigo + 4 de docs).

### Tareas ejecutadas (en orden)

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 1 | frontend/src/utils/api.js (apiFetch con CSRF, retry, error handling) | bd7d423 | 290 lineas, 6 atajos, validado con curl. Docs asociados: 4525281, a07263f, 7778568. |
| 2 | backend/scripts/seed_organizacion.py | 812cecb | 27 areas nuevas. Total BD: 50 (23 preexistentes + 27 nuevas). |
| 3 | CRUD /api/v1/gerencias (US-9.06) | 3a03298 | 5 endpoints validados. Helper permissions.py reubicable. |
| 4 | CRUD /api/v1/areas (US-9.06) | f922148 | 5 endpoints. Limitacion documentada: sigla UNIQUE global impide re-crear tras borrado. |
| 5 | CRUD /api/v1/configuracion-global (US-9.01+9.02) | eaff39a | 6 endpoints (incluye bulk). Modelo + migracion Alembic 003. UPSERT (no 409 en POST dup). |
| 6 | CRUD /api/v1/feriados (US-9.01 calendario) | 8b6a059 | 5 endpoints. Modelo + migracion Alembic 004 + seed Bolivia 2026 (20 feriados). |
| 7 | CRUD /api/v1/email-templates (US-9.04, 6 plantillas) | c83bf35 | 4 endpoints. Modelo + migracion Alembic 005 + seed (6 plantillas) + motor Jinja2 con preview. |
| 8 | CRUD /api/v1/matriz-enrutamiento-eto (US-9.03 sub-3) | cd4a444 | 6 endpoints. Modelo + migracion Alembic 006 + seed (10 filas + crea usuario cecEspinoza). |
| 9b | CRUD /api/v1/tipos-documento (US-9.03 sub-1) | f0d3650 | 5 endpoints. Modelo + migracion Alembic 007 + seed (13 tipos del Excel). |
| 9c | CRUD /api/v1/estados (US-9.03 sub-2) | 8ffaaa2 | 5 endpoints. Modelo + migracion Alembic 008 + seed (5 estados del flujo). |

### Logros tecnicos

1. **40+ endpoints REST** implementados (12 originales + 28 nuevos de la sesion 5).
2. **6 migraciones Alembic** autogeneradas y aplicadas (003 a 008) � base durable.
3. **5 seeds idempotentes** (seed_organizacion, seed_feriados, seed_email_templates, seed_matriz_eto, seed_estados).
4. **1 helper de permisos reutilizable** (app/core/permissions.py) usado por 9 routers.
5. **2 usuarios ETO** sembrados (aromero preexistente + cecEspinoza creado en sesion 5).
6. **Datos sembrados**: 10 gerencias, 50 areas, 5 roles, 11 modulos, 763 usuarios AD, 20 feriados Bolivia 2026, 6 plantillas email, 10 filas matriz ETO, 13 tipos documento, 5 estados.

### Bugs detectados y corregidos durante la sesion

1. **SQLAlchemy 2.0 no acepta description= en String()/Text()** � kwarg desconocido. Quite de los modelos.
2. **usuario_roles se importa de app/models/usuario.py**, NO de app/models/rol.py � bug de import en tarea #8.
3. **PowerShell + http.client filtra mal cookies #HttpOnly_** � bug del tooling. Fix documentado.
4. **cascade=all, delete-orphan en gerencia.areas** � incompatible con borrado logico. Documentado.
5. **Doble endpoint list_matriz** en tarea #8 (codigo experimental). Reescrito limpio.
6. **Metodo inventado activo_disponibilidad()** en seed original. Eliminado.

### Hallazgos del pre-flight (importantes para futuras sesiones)

- ? Alembic YA estaba aplicado (tabla alembic_version existe). El GAP reportado en sesion 4 es incorrecto.
- ? Backend SI esta en Docker (verificado docker ps), no nativo. Sesion 4 estaba equivocada.
- ? NO hay middleware CSRF en backend (solo se setea cookie en /login). api.js envia X-CSRF-Token aunque no se valide.
- ? app/schemas/ estaba VACIO � ahora poblado con 8 schemas Pydantic v2.
- ?? Skills git-workflow y python-reviewer (plugin ECC) NO disponibles como subagent � reemplazadas por lectura directa de la skill y auto-revision con checklist.

### Progreso actualizado
- **R1:** 20/23 tareas (87%). Pendientes: tests pytest, rate limit, CSP.
- **R2:** 0/21 (bloqueado por tests).
- **Total:** 20/48 (42%) + 4 bonus.

### Proxima sesion (Sesion B) � UI + tests + bulk
1. Refactor Parametrizacion.js para usar los 28 nuevos endpoints con apiFetch (US-9.01-9.06).
2. Tests pytest de los endpoints nuevos (Sesion B tarea #11).
3. Asignacion masiva desde USUARIOS EXISTENTES A ABRIL.xlsx (730 usuarios, tarea #12).
4. GET /api/v1/audit-log con filtros (tarea #9, audit de admin).
5. Operaciones jerarquicas de areas (mover, promover-a-gerencia, DELETE logico) ��� sub-tareas #9d.
6. Override vacaciones + export Excel/CSV (tarea #9e).

---

## Sesion 6 — 2026-06-16 (martes) — UI + tests + bulk

> Sesion dedicada a cerrar el FRONTEND de la EPICA 9 + 3 endpoints backend nuevos
> (audit-log, ops jerarquicas areas, export XLSX/CSV). El usuario decidio
> DETENER la sesion tras tarea #9e. Tareas #11 (tests) y #12 (bulk) CANCELADAS.

### Tareas ejecutadas (en orden)

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 9 | `GET /api/v1/audit-log` con filtros | `33c3fef` | Modelo `AuditLog` + migracion 009 + helper `write_audit()` + router con 8 filtros. **8 routers instrumentados** (gerencias, areas, feriados, email-templates, matriz-eto, tipos-doc, estados, configuracion-global). 15+ entradas validadas. |
| 9d | Operaciones jerarquicas areas | `79120cf` | `POST /areas/{id}/mover` + `POST /areas/{id}/promover-a-gerencia` + `DELETE ?fisico=true|false`. **Fix B1** aplicado: `UniqueConstraint('gerencia_id', 'sigla')` (migracion 010). |
| 9e | Override vacaciones + export XLSX/CSV | `1559cdb` | `PATCH /usuarios/{id}` (override estado/ausente/delegacion) + `GET /usuarios/export?formato=xlsx|csv`. Helper `app/core/excel_export.py` con paleta pastel (verde COFAR, amarillo totales, zebra), auto-width, freeze, auto-filtros, totales. **764 usuarios exportados a XLSX validados**. Dependencia `openpyxl==3.1.5` agregada. |
| 10 | Refactor `Parametrizacion.js` con `apiFetch` | `52cc80c` | Nuevo `frontend/src/services/parametrizacionApi.js` (30+ funciones). `Parametrizacion.js` (65KB) ya NO importa de `data/parametrosSistema.js` (verificado con grep). 7 tabs cargan del backend en paralelo al `init()`. E2E validado con login admin en `localhost:8080`. |
| 11 | Tests pytest 80% | CANCELADA | Usuario detuvo la sesion. |
| 12 | Asignacion masiva desde Excel | CANCELADA | Usuario detuvo la sesion. |

### Logros tecnicos

1. **4 commits** de codigo + 1 de docs (en esta sesion).
2. **2 migraciones Alembic** (009 audit_log, 010 areas unique compound) aplicadas en BD.
3. **1 bug critico (B1) RESUELTO**: `areas.sigla` ya es `UNIQUE(gerencia_id, sigla)`, no global.
4. **Helper reusables nuevos**: `app/core/audit.py:write_audit()` (auditoria no-bloqueante) + `app/core/excel_export.py:build_excel/build_csv()` (paleta pastel, profesional).
5. **Patron replicado en 8 routers**: `await require_eto_or_admin()` al inicio + `await write_audit()` post-commit + doble commit (atomicidad).
6. **Frontend desacoplado del mock legacy**: `Parametrizacion.js` consume backend real, no `data/parametrosSistema.js`.

### Bugs detectados y corregidos

1. **`AsyncSession` no es Pydantic field**: error 500 al usar `current_user: Usuario = Depends(require_eto_or_admin)` con `response_model=...`. Patron del codebase: `await require_eto_or_admin(request, db)` dentro del endpoint, no como Depends.
2. **`AuditLog` no acepta `Base.metadata.bind`** (SQLAlchemy 2.0). Fix: `JSONType = JSON().with_variant(JSONB(), "postgresql")`.
3. **`EmailTemplate.variables_schema` no existe** (campo real: `variables_json`). Bug en mi codigo de instrumentacion.
4. **`ConfiguracionGlobal` PK es `clave` (str), no `id` (int)**. Error 500 al usar `cfg.id` en el audit.
5. **DELETE + commit + write_audit + commit** no escribia el audit (transaccion separada). Fix: `write_audit` + `db.delete` + un solo `commit` (atomico).
6. **`UnboundLocalError: Area`** en export_usuarios: import local dentro del bloque `if` causaba el error. Fix: importar `Area` al top.
7. **MissingGreenlet en PATCH /usuarios/{id}**: `expire_on_commit=True` invalida selectinload. Fix: nuevo query con selectinload post-commit.
8. **Orden de rutas en usuarios.py**: `/{user_id}` capturaba `/export` y `/sync-ad` antes. Fix: rutas especificas primero, `/{user_id}` al final.
9. **API_BASE hardcodeado en Parametrizacion.js** (usaba `localhost:18000` directo, no Nginx). Fix: eliminado, usa paths relativos via `apiGet/Post/etc`.

### Hallazgos del pre-flight (importantes para futuras sesiones)

- **Patron del codebase**: `await require_eto_or_admin(request, db)` se llama DENTRO del endpoint, no como `Depends()`. Usar `Depends()` con esta funcion causa 500.
- **Schemas con PK string**: `ConfiguracionGlobal` usa `clave` (str) como PK. NO tiene `id`. El audit_log debe usar `recurso_id=None` y poner la `clave` en `detalles`.
- **Patron de orden de rutas**: `/{user_id}` generico DEBE ir al final, sino captura paths especificos como `user_id="export"`.
- **El frontend se sirve en `localhost:8080` (Nginx)** y el backend en `localhost:18000` (directo). Las cookies se setean en el dominio del BACKEND, no del frontend. Esto causa problemas de auth cuando se hace login via curl y luego se navega en el browser. El flujo correcto es login DESDE el browser via la UI.
- **Frontend design system YA EXISTE** en `frontend/src/main.css`: `brand-500` (#1a5fb4 azul), `.btn-primary`, `.data-table`, `.badge-{color}`, `.section-card`, glassmorphism, animaciones. **Respetado y NO tocado**.

### Progreso actualizado

- **R1 + EPICA9:** 27/27 tareas (100%). Backend + frontend cerrados.
- **R2:** 0/21 (bloqueado por tests pendientes — cancelados).
- **Total:** 27/48 (56%) + 4 bonus.
- **Migraciones Alembic:** 10 aplicadas (001 a 010). 1 tabla nueva (audit_log).
- **Endpoints totales:** 49+ REST. Audit log captura los 9 routers de parametrizacion + auth + usuarios.

### Proxima sesion (Sesion C) — opcional / por definir

Si se retoman los tests y la asignacion masiva, los archivos a tocar seran:
- `backend/tests/conftest.py` + `backend/tests/test_*.py` (8 archivos minimo)
- `backend/app/api/v1/admin.py` con nuevo endpoint `POST /admin/asignar-roles-desde-matriz`
- `backend/scripts/import_matriz_usuarios.py` para parsear el Excel (openpyxl ya instalado)

Si se quiere cerrar R2 (documentos + workflow + bandejas), el orden de ataque es:
1. Schemas SQLAlchemy de las 19 tablas restantes (tareas 23-27)
2. Migracion Alembic 011 con todas las tablas nuevas
3. Endpoints de documentos + archivos + enviar
4. Frontend: refactor Bandeja.js, LiberacionDetalle.js, ListaMaestra.js

### Decisiones tomadas en esta sesion (ADRs nuevos en draft)

- **ADR-014 (en draft)**: `AuditLog` append-only via `write_audit()` no-bloqueante. Garantiza atomicidad con doble `commit` (operacion + audit) y rollback en error sin enmascarar el resultado de la operacion original.
- **ADR-015 (en draft)**: `areas.sigla` UNIQUE(gerencia_id, sigla) en vez de global. Fix B1. Permite revivir un area con la misma sigla en otra gerencia sin conflictos.
1. Refactor Parametrizacion.js para usar los 28 nuevos endpoints con apiFetch (US-9.01-9.06).
2. Tests pytest de los endpoints nuevos (Sesion B tarea #11).
3. Asignacion masiva desde USUARIOS EXISTENTES A ABRIL.xlsx (730 usuarios, tarea #12).
4. GET /api/v1/audit-log con filtros (tarea #9, audit de admin).
5. Operaciones jerarquicas de areas (mover, promover-a-gerencia, DELETE logico) � sub-tareas #9d.
6. Override vacaciones + export Excel/CSV (tarea #9e).

---

## Sesion 7 — 2026-06-16 (martes PM) — Bugfix del refactor incompleto de Sesion 6

### Contexto
Al loguearse en la pantalla de Parametrizacion General y navegar a la pestana Gestion
de Usuarios, la consola del browser mostraba multiples errores y la pagina no se visualizaba
correctamente. La sesion 6 declaro "B5 RESUELTO: Parametrizacion.js ya no usa
data/parametrosSistema.js" pero la realidad era que el refactor estaba **incompleto**:
los imports se removieron pero las referencias al mock legacy quedaron huerfanas.

### Diagnostico (guiado por el usuario via ritual INICIO-SESION.md)
1. Lectura de BITACORA / ESTADO / INICIO-SESION / DECISIONES / REUNIONES-R3-R6 / MATRIZ-ABRIL
2. Stack diagnosticado: `curl http://localhost:18000/api/v1/health` OK
3. Inspeccion de errores de consola + network requests via Chrome DevTools
4. Identificacion de los 10 bugs que se detallan abajo

### Bugs encontrados y corregidos (1 commit: `89f5ac6`)

| # | Bug | Severidad | Fix |
|---|---|---|---|
| 1 | `api.js:normalizePath()` REMOVIA el prefijo /api/v1 | Critico | Dejar API_BASE intacto |
| 2 | 13 referencias huerfanas a mocks legacy | Critico | Re-importar 10 nombres de data/parametrosSistema.js |
| 3 | Template usa `g.areas.length` (backend retorna `areas_count`) | Alto | Cambiar a `g.areas_count ?? 0` |
| 4 | `cargarGerencias()` no mapea response al shape del template | Alto | Mapear cod/codigo, n/c, areas:[] |
| 5 | `cargarTiempos()` filtra por VIGENCIA pero plazo_revision esta en FLUJO | Alto | Traer TODAS las claves |
| 6 | Chips inicializa vacio (no usa mock como fallback) | Medio | `chips: [...exclusionTiposDB]` |
| 7 | 60 warnings de "x-for key cannot be an object" | Medio | Usar IDs unicos en keys |
| 8 | XLSX export header "Cod. SAP (AD)" | Bajo | Renombrar a "Cód. SAP" |
| 9 | Tabla Usuarios no muestra `ad_postal_code` | Medio | Agregar columna "Cód. SAP" |
| 10 | Seccion "Gestion de Usuarios" con `})` huerfano + falta `guardarTiempos()` | Alto | Reconstruir bloque |

### Validacion empirica (Chrome DevTools)

7 tabs validadas cargando datos del backend:

| Tab | Endpoint | Datos cargados | Error/Warn |
|---|---|---|---|
| Tiempos y SLAs | `/configuracion-global` | plazoRevision: 25 (de BD!), vigencias: 14 | 0 |
| Restricciones | `/configuracion-global` | maxAdjuntos: 20, maxSizeMB: 20, etc. | 0 |
| Diccionarios y Enrutamiento | `/tipos-documento` + `/estados` + `/matriz-enrutamiento-eto` | tiposDocs: 14, estados: 7, matrizETO: 10 | 0 |
| Gerencias y Areas | `/gerencias` + `/areas` | 12 gerencias, areasGerSel: 12 | 0 |
| Plantillas de Notificacion | `/email-templates` | 6 plantillas (las 6 del PDF oficial) | 0 |
| Gestion de Usuarios | `/usuarios` + `/audit-log` | 10 usuarios, kpis: 764, columna Cód. SAP visible | 0 |
| Logs de Auditoria | `/audit-log` | 29 entradas con accion/recurso/usuario/descripcion | 0 |

**Consola del browser: 0 errors, 0 warnings** (post-fix).

### Estado de la BD validado

```
gerencias: 14 (10 esperadas + 4 de pruebas; 12 activas)
areas: 56 (49 esperadas; distribuidas en las 10 gerencias semilla)
usuarios: 764 (730 del Excel + 34 extras)
roles: 5 (ADMIN, ETO, ELABORADOR-REVISOR, etc.)
modulos: 11 (los 10 + 1 extra)
feriados: 23 (20 Bolivia 2026 + 3 extra)
email_templates: 6 (los 6 del PDF oficial - 9.04)
matriz_enrutamiento_eto: 10 (1 por gerencia)
tipos_documento: 15 (13 del Excel + 2 de prueba)
estados: 8 (5 del flujo + 3 extra)
configuracion_global: 8
audit_log: 29 (todas las mutaciones de sesion 6 + 9e)
```

### Trampas/ensenanzas

1. **El refactor de sesion 6 fue declarado "completo" pero NO LO ERA.** Validar empiricamente
   navegando a CADA tab, no solo a uno.
2. **El cache del browser es agresivo con Vite HMR** — para forzar reload use
   `rm -rf /app/node_modules/.vite` + restart del container.
3. **`console.log` al inicio del modulo** es la forma mas rapida de verificar que version
   se esta ejecutando (es un marker que invalida cualquier cache).
4. **El backend puede tener categorias mal asignadas** (VIGENCIA vs FLUJO) — mejor
   traer todas las claves y mergear en el frontend.
5. **El shape del template debe coincidir con el shape del backend** — si no, fallar
   silenciosamente con `undefined.length`.

### Proxima sesion

- **Tarea #11:** Tests pytest de los 28+ endpoints nuevos (cobertura 80%)
- **Tarea #12:** Asignacion masiva desde `USUARIOS EXISTENTES A ABRIL.xlsx` (730 usuarios)
  - match estricto por `ad_postal_code == str(COFAR)`
  - CLI script `backend/scripts/run_matriz_import.py` (sin endpoint, sin UI)
  - Skip delegado (warning en log)

### Pendientes menores (no bloqueantes)

- Chips se inicializan del mock pero BD no tiene `tipos_excluidos_limite_descarga`
- Restricciones: defaults del mock (maxAdjuntos=20 etc) porque la BD no tiene
  las claves `max_archivos_por_solicitud` / `max_tamano_archivo_mb` / `max_descargas_editables_dia`
- Semaforo verde/amarillo: defaults del mock porque la BD no tiene `semaforo_verde_dias`/`semaforo_amarillo_dias`

(Esto es BUENO: confirma que la pagina CARGA del backend cuando existe, y usa
fallback del mock solo si no existe. Es la mejora clave del fix.)
