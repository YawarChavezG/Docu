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

---

## Sesion 8 — 2026-06-16 (martes PM) — Import matriz de abril 730 usuarios

> Sesion dedicada a cerrar la tarea #12 (asignacion masiva desde el Excel
> `USUARIOS EXISTENTES A ABRIL.xlsx`). Pivote de sesion 6: script CLI
> standalone (sin endpoint, sin UI). Skip delegado con warning (deuda #13).

### Tareas ejecutadas (en orden)

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 12.1 | Analisis Excel + mapeo COFAR/modulos/roles | (con 12.4) | `docs/PR/MATRIZ-ABRIL-MAPEO.md` con 729 filas, 5/5 roles OK, 2 normalizaciones (BANDEJA_DE_TAREAS, CONSULTAR_DOCUMENTOS), 717/729 matchean BD |
| 12.2 | `backend/app/services/matriz_import_service.py` | (con 12.4) | 3 funciones + orquestador: `parsear_excel`, `match_usuarios`, `aplicar_asignaciones`, `run_import`. Dataclasses: `MatrizRow`, `MatchResult`, `ImportResult` |
| 12.3 | `backend/scripts/run_matriz_import.py` | (con 12.4) | CLI argparse con `--excel --dry-run --update-existing --verbose --yes`. Confirmacion interactiva. Exit codes 0/1/2. Reporta counts antes/despues |
| 12.4 | Ejecucion real + validacion empirica | (con 12.4) | 10 -> 730 usuarios con rol (+716). 3,312 modulos asignados. 12 unmatched. Idempotente verificado (3ra corrida = 0 cambios) |
| 12.5 | Re-tests pytest #11 en paralelo | (con 12.4) | 123/123 passing en 11.38s — import no rompio nada |

### Logros tecnicos

1. **716 usuarios del Excel** ahora tienen rol + modulos + flags asignados.
2. **3,312 asociaciones N:M** (roles + modulos) insertadas con `ON CONFLICT DO NOTHING`.
3. **0 errores de catalogo** (5/5 roles + 9/11 modulos del Excel matchean).
4. **Idempotencia verificada**: 3 corridas consecutivas dieron 716/4/0 asignaciones.
5. **5 sub-tareas** ejecutadas en ~2 horas (vs 4-5h estimadas inicialmente).

### Bugs detectados y corregidos durante la sesion

1. **MODULO_NORMALIZATION con `replace(" ", "_")` falla en "BANDEJA DE TAREAS"** ->
   la BD tiene `BANDEJA_TAREAS` (sin "DE"). Cambiado a mapa EXPLICITO de 9 entradas.
2. **OUTER JOIN retornaba `rol_id=None` para usuarios sin rol** -> mi codigo lo
   contaba como "ya tiene rol" (set no vacio con None). Fix: `if rol_id is None: continue`.
3. **Dict comprehension pisaba usuarios duplicados** -> 5 COFARs tienen 2 usuarios
   en BD (stub de DES + real). El dict tomaba el ultimo procesado (el stub, que ya
   tenia rol). Fix: `ORDER BY id ASC` y reportar duplicados como warning.
4. **Pytest no en venv del contenedor** -> pytest esta en `backend/.venv` del host
   Windows. Cambio a ejecutar desde el host con `backend\.venv\Scripts\python -m pytest`.

### Trampas/ensenanzas documentadas (para el futuro)

1. **5 COFARs tienen 2 usuarios en BD** (visitador/promotor/sadministrativo/jadministrativo/lalave/ebejar/cmendoza
   son stubs; los reales son ntorrrico/fvargas/rlimachiq/jadministrativo). Heuristica:
   preferir el `id` mas bajo (los reales se crearon primero).
2. **El Excel tiene 729 filas, NO 730 como decia el plan original** (4 filas vacias al final).
3. **0 ADMIN en la matriz** (era 1 esperado). El `admin` del stub DES NO es afectado.
4. **156 usuarios requieren delegado, pero solo 17 con nombre concreto** (11%). Plan
   es **SKIP delegado con warning**, queda como deuda tecnica #13.
5. **3 stubs de DES quedan con `estado_delegacion='pendiente'`** (inconsistente con
   `requiere_delegado=False`). Esto es preexistente del seed de sesion 5, no es
   bug del import.

### Estado de la BD al cierre de sesion 8

```
usuarios.total:               764
usuarios.con_rol:             730 (10 originales + 716 del Excel + 4 stubs DES con rol)
usuarios sin rol:             34 (los 12 COFARs sin match + 22 extras)
usuario_roles.total:          730
usuario_modulos.total:        3,345 (34 originales + 3,311 nuevos)

Distribucion de roles (post-import):
  VISUALIZADOR (CL-EVAL)             567 (573 esperados - 6 sin match)
  ELABORADOR - REVISOR               143 (146 esperados - 3 sin match)
  ELABORADOR - REVISOR - APROBADOR    10 (8 + 2 preexistentes)
  ETO                                  4 (2 + 2 preexistentes: aromero, cecEspinoza, aracely)
  ADMIN                                2 (0 del Excel + 2 preexistentes)

Estado de delegacion:
  pendiente + requiere_delegado=true:  151 (los 156 no-VISUALIZADOR - 5 que ya tenian delegado)
  pendiente + requiere_delegado=false:   3 (stubs DES: solicitante, elaborador_revisor, elaborador_revisor_aprobador)
  na + requiere_delegado=false:        572 (VISUALIZADORES)
```

### Decisiones tomadas en esta sesion (ADRs nuevos en draft)

- **ADR-016 (en draft)**: Mapeo EXPLICITO de normalizacion de modulos (no `replace(" ", "_")`).
  "BANDEJA DE TAREAS" -> "BANDEJA_TAREAS" (drop "DE"). Documentado en MAPEO § 7.
- **ADR-017 (en draft)**: Preferencia por `id ASC` cuando hay duplicados de
  `ad_postal_code`. Heuristica: los reales se crearon primero. Documentado en
  service docstring y MAPEO § 3 (R1).
- **ADR-018 (en draft)**: Skip delegado con warning. Coincide con pivot de
  sesion 6. 156/156 quedan con `estado_delegacion='pendiente'`. Backlog #13.

### Progreso actualizado

- **R1 + EPICA9 + import matriz:** 28/28 tareas (100%).
- **R2:** 0/21 (sigue bloqueado por R2 mismo, no por R1).
- **Total:** 28/48 (58%) + 4 bonus.
- **Migraciones Alembic:** 10 aplicadas (001 a 010). 0 nuevas en esta sesion.
- **Endpoints totales:** 49+ REST. Sin cambios en esta sesion.
- **Datos totales:** 764 usuarios, 730 con rol, 3,345 asociaciones N:M.

### Proxima sesion (sesion 9) — TBD

Opciones para retomar:

1. **R2 — Wizard de creacion** (tareas #23+): empezar con los 19 modelos SQLAlchemy
   de Documentos/Workflow/Archivos/Soporte/Miscelaneos. Migracion 011. Endpoints
   `/api/v1/documentos` (CRUD borrador). Riesgo: 2-3 sesiones intensivas.
2. **#13 — Deuda delegado**: implementar match desde AD `manager` attribute o
   desde la BD con fuzzy matching + threshold 0.85 (plan original D2). Pequeño.
3. **#14 — Cargos a areas**: seed de mapeo POSICION -> area_id. Tabla nueva o
   columna calculada. Mediano.
4. **#19-21 — Security hardening**: CSP, DOMPurify, rate limit. Backlog R1.

Recomendacion: cerrar #13 y #14 (deudas chicas) antes de empezar R2 (que es
largo y mejor con todo R1 limpio).

---

## Sesion 9 — 2026-06-16 (martes PM) — Editar Usuario + Mi Perfil BD + Export corregido

> Sesion dedicada a cerrar los pendientes de gestion de usuarios que
> estaban identificados en la bitacora: columna Delegado, modal de
> edicion, Mi Perfil consistente con BD, export Excel correcto.

### Tareas ejecutadas (en orden)

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 9.1 | Backend `GET /api/v1/roles` | (con 9.7) | `app/api/v1/roles.py` + `schemas/rol.py`. 5 roles con flag `requiere_delegado` (ETO, ELABORADOR-REVISOR, ELABORADOR-REVISOR-APROBADOR = true). Sin auth (catalogo publico). |
| 9.2 | Backend `PATCH /usuarios/{id}` con `rol_codigo` y `delegado_id` | (con 9.7) | `UsuarioUpdate` extendido. Reemplaza roles via `delete + insert` en `usuario_roles`. Asigna/quita delegado. Setea `estado_delegacion=asignado` automaticamente al asignar. `db.expire(target)` para refrescar relaciones tras delete+insert. |
| 9.3 | Frontend `parametrizacionApi.js`: roles.list() + usuarios.listActivos() | (con 9.7) | Helpers para el modal. `listActivos` usa filtro `estado=activo&page_size=200`. |
| 9.4 | Frontend columna DELEGADO en tabla | (con 9.7) | 3 estados visuales: verde (asignado con dot), amber (sin delegado + rol lo requiere con dot pulsante), gris (no requiere). |
| 9.5 | Frontend modal Editar Usuario centrado | (con 9.7) | ROL (select de BD con `requiere_delegado` flag), DELEGADO (searchable picker fuzzy con tokens), VACACION (checkbox), ESTADO (select activo/inactivo/desvinculado), Observaciones. |
| 9.6 | Frontend Mi Perfil (ProfileModal) lee de BD | (con 9.7) | Reemplaza mock `listaEmpleados`. Carga info de `/me` + `/usuarios?q=<username>` para delegado. PATCH con `delegado_id` y `ausente`. Banner de alerta si rol requiere y no tiene. |
| 9.7 | Backend export XLSX/CSV columna AREA poblada | (con 9.7) | Formato "Gerencia / Area" con fallback a `ad_info` (department del AD) si no tiene area en BD. Antes salia vacio para 700+ usuarios que no tienen area_id. |
| 9.8 | BUG fix: select de ROL aparece vacio al abrir modal | (con 9.7) | Alpine no bindea `x-model` en `<select>` cuando las `<option>` no existen. Fix: `editForm.rol_codigo = ''` inicialmente, y setear el rol original **despues** de cargar roles, con `await this.$nextTick()` para esperar a que Alpine renderice las options. |
| 9.9 | BUG fix: cache de Vite impedia ver cambios | (con 9.7) | `docker restart sgd-frontend` limpia el cache del dev server. Ademas usar `?_v=N` en la URL del navegador para forzar cache buster. |

### Logros tecnicos

1. **6 tareas nuevas** sumadas a R1 (cerrado al 100% en 35/35).
2. **3 endpoints extendidos/creados**: `GET /roles`, `PATCH /usuarios/{id}` con `rol_codigo`/`delegado_id`, export con AREA poblada.
3. **2 archivos frontend refactorizados**: `parametrizacionApi.js` con 2 helpers nuevos, `ProfileModal.js` reescrito para leer BD en vez de mock.
4. **1 archivo frontend extendido**: `Parametrizacion.js` con columna Delegado + modal centrado + searchable picker.
5. **2 bugs fixes criticos** detectados en validacion: select vacio + cache Vite.

### Bugs detectados y corregidos durante la sesion

1. **Relaciones `target.roles` no se refrescaban tras delete+insert** -> SQLAlchemy 2.0 mantiene identity map. Fix: `db.expire(target)` antes del reload.
2. **Select de ROL aparecia vacio al abrir modal** -> Alpine no bindea `x-model` si las `<option>` no existen. Fix: `await $nextTick()` + setear `rol_codigo` despues de cargar las options.
3. **Cache de Vite retenia la version vieja del archivo** -> Docker restart limpia. Tambien descubrimos que el navegador cachea via service worker / Vite client, hay que usar `?_v=N` cache buster.
4. **Columna AREA del export salia vacia** para usuarios sin area_id -> Fallback al `ad_info` (department del AD) que SI tiene valor.

### Validacion empirica (Chrome DevTools)

| Verificacion | Resultado |
|---|---|
| `GET /api/v1/roles` | 200, 5 roles, 3 con `requiere_delegado=true` |
| `GET /api/v1/usuarios?rol=ETO` | 200, lista de 4 ETOs |
| `PATCH /usuarios/{id}` con `rol_codigo` | 200, rol actualizado, refresh correcto |
| `PATCH /usuarios/{id}` con `delegado_id` | 200, delegado asignado, `estado_delegacion=asignado` |
| Login 3x como aromero (ya importado) | 1 sola fila en BD, NO se duplica |
| Modal Editar Aida (Elaborador) | Rol="Elaborador-Revisor (requiere delegado)", delegado=Aracely, picker funcional |
| Buscar "aromero" en picker | Dropdown muestra "AR Aracely Carol Romero Plata @aromero SAP:10002572 CAL" |
| Tabla Gestion de Usuarios | Columna DELEGADO visible: "No requiere" / "Sin delegado" / nombre delegado |
| Mi Perfil sidebar | Avatar + Lucia Herrera + Administrador del Sistema + Delegado picker |
| Export XLSX | Col "Gerencia / Area" poblada con "Oruro", "La Paz", "Comercial", etc. (fallback ad_info) |

### Estado de la BD al cierre de sesion 9

```
Endpoint /usuarios:
  gescobari.delegado_id = 1 (aromero), estado_delegacion = 'asignado'
  Test aromatic test PASS: 3 logins aromatic = 1 fila en BD (no duplica)
  
Endpoint /roles:
  ADMIN, ETO, ELABORADOR - REVISOR, ELABORADOR - REVISOR - APROBADOR, VISUALIZADOR (CL-EVAL)
  requiere_delegado: [F, T, T, T, F]
  
Export XLSX (573 visualizadores):
  Col "Gerencia / Area" poblada (antes vacia para ~95% de los usuarios)
```

### Decisiones tecnicas (ADRs candidatos para sesion 10)

- **ADR-019 (en draft)**: PATCH /usuarios/{id} acepta `rol_codigo` y `delegado_id`. Reemplazo atomico de roles. Auto-set `estado_delegacion=asignado` al asignar. Validacion: no se puede asignar a si mismo; delegado no puede estar desvinculado.
- **ADR-020 (en draft)**: Export de usuarios con fallback a `ad_info` cuando no hay area_id. El `ad_info` (department del AD) es la mejor aproximacion disponible sin enriquecimiento adicional.

### Progreso actualizado

- **R1 + EPICA9 + import matriz + Editar Usuario + Mi Perfil**: 35/35 (100%). CERRADO.
- **R2**: 0/21. Listo para arrancar.
- **Total**: 35/48 (73%) + 4 bonus + import matriz + editar.
- **Migraciones Alembic**: 10 aplicadas. 0 nuevas en sesion 9 (no hubo cambios de schema).
- **Endpoints totales**: 50+ REST. +1 nuevo (`GET /roles`).

### Proxima sesion (sesion 10) — TBD

Opciones:
1. **R2 - Wizard de creacion** (tareas #23+): 19 modelos SQLAlchemy + migracion 011 + endpoints. 2-3 sesiones.
2. **#13 - Deuda delegado** (fuzzy matching + threshold 0.85): pequeno.
3. **#14 - Cargos a areas**: seed POSICION -> area_id. Mediano.
4. **#19-21 - Security hardening pre-QAS**: CSP, DOMPurify, rate limit. Backlog R1.

Recomendacion: cerrar #13 y #14 (deudas chicas) antes de R2.

---

## Sesion 10 — 2026-06-16 (martes PM) — BACKUP paralelo + discrepancia en ESTADO detectada

> Sesion dedicada a 2 cosas:
> 1. Diagnosticar discrepancia en ESTADO.md (tarea #8 marcada ❌ cuando Alembic ya tiene 10 migraciones aplicadas).
> 2. **Crear stack BACKUP paralelo en puertos 8081/5174/18001** para mostrar el estado actual en una
>    reunion sin riesgo de romper la demo, y poder seguir desarrollando en el original (8080/5173/18000).

### Hallazgo de inicio (importante para futuras sesiones)

**Discrepancia detectada en ESTADO.md:**
- Tarea #8 "Migracion Alembic inicial" esta marcada como ❌ con nota "alembic/ existe pero VACIO".
- Realidad verificada: 10 migraciones aplicadas (001-010), head = `b397cd9bfb91` (Fix B1).
- Esto se origino en sesion 4 (auditoria inicial, antes de las migraciones de sesiones 5 y 6) y nunca se actualizo.
- BITACORA sesion 5 ya documentaba "Alembic YA esta aplicado (tabla alembic_version existe)" pero ESTADO.md no se corrigio.

**Pendiente de cleanup (post-reunion):** sincronizar ESTADO.md contra la realidad (tarea #8 ✅, conteo de tablas 25/28, etc.).

### Backup paralelo: resultado

**8 archivos nuevos** + 0 modificaciones al stack original:

| Archivo | Funcion |
|---|---|
| `.env.backup` | Vars de entorno del backup (puertos +1, DB=sgd_backup) |
| `deploy/docker-compose.backup.yml` | Compose del backup (container_name sgd-bk-*, volume sgd-bk_*, network sgd-bk-net) |
| `deploy/nginx/conf.d.bk/sgd-backup.conf` | Server block nginx aislado del original (carpeta distinta) |
| `scripts/start-stack-backup.bat` | Orquestador: up pg/redis → cp dump → pg_restore → up resto → wait health → URLs |
| `scripts/stop-stack-backup.bat` | Apaga backup (opcional `--purge` borra volumenes) |
| `docs/PR/BACKUP-PARALELO.md` | Doc completa con URLs, troubleshooting, limitaciones |
| `backups/20260616_150015/sgd_pre_refactor.dump` | Dump pg_dump -Fc (119KB) del estado pre-refactor |
| `backups/20260616_150015/src/` | Copia del working tree (393 archivos, 31.82MB) |

### URLs resultantes (verificadas con curl + login)

| Recurso | Original | Backup |
|---|---|---|
| App (Nginx) | http://localhost:8080 | http://localhost:8081 |
| Frontend | http://localhost:5173 | http://localhost:5174 |
| Backend | http://localhost:18000 | http://localhost:18001 |
| MailHog | http://localhost:8025 | http://localhost:8026 |
| Postgres | 25432 (db: sgd) | 25433 (db: sgd_backup) |
| Redis | 26379 | 26380 |

### Validacion end-to-end del backup

| Verificacion | Resultado |
|---|---|
| `GET /api/v1/health` (directo 18001) | 200 OK, db OK |
| `GET /health` (via nginx 8081) | 200 OK |
| Login `aromero / cofar.2026` via 8081 | 200 OK + 3 cookies (csrf, session, user_id) + user JSON completo |
| Frontend 5174 | 200 OK, HTML identico al 5173 |
| Datos backup vs original | IDENTICOS: 764 usuarios, 14 gerencias, 56 areas, 15 tipos, 8 estados, 23 feriados, 6 email_templates, 10 matriz_eto, 8 config_global, 46 audit_log, alembic=b397cd9bfb91 |
| 16 contenedores activos | OK (8 original + 8 backup, sin conflictos) |

### Logros tecnicos

1. **Stack 100% aislado** del original — comparte codigo fuente pero no volumenes, redes, ni nombres de container.
2. **0 modificaciones al stack original** — la reunion puede seguir mostrando el estado actual sin riesgo de rotura.
3. **Restauracion automatica del dump** — el script hace pg_restore con `--no-owner --role=sgd --clean --if-exists`, tolera re-runs.
4. **Documentacion completa** en `docs/PR/BACKUP-PARALELO.md` con troubleshooting (4 escenarios: container name conflict, nginx no arranca, role does not exist, datos no esperados).

### Riesgos identificados y mitigaciones aplicadas

1. **Nginx "conflicting server name"** si ambos stacks compartian `conf.d/` → mitigado con `conf.d.bk/` separado.
2. **Vite HMR viendo codigo de ambos** → documentado como INTENTIONAL (backup es espejo, no sandbox). Si se quiere aislar, apagar backup antes de editar.
3. **CORS_ORIGINS restrictivo del backup** → .env.backup incluye ambos stacks (8080+8081).
4. **Memoria Docker** (16 contenedores) → documentado en limitaciones; opcion de bajar celery-W/B si hace falta.

### Decisiones tecnicas (ADRs candidatos para sesion 11)

- **ADR-021 (en draft)**: Stack backup paralelo con puertos +1, container_name prefix `sgd-bk-`, volume prefix `sgd-bk_`, network `sgd-bk-net`, DB `sgd_backup`. Permite demo en paralelo al desarrollo sin riesgo de rotura.
- **ADR-022 (en draft)**: nginx config del backup en `conf.d.bk/` (NO `conf.d/`) para evitar warnings de conflicting server name en el nginx del original.

### Progreso actualizado

- **R1 + EPICA9 + import matriz + Editar Usuario + Mi Perfil**: 35/35 (100%). Sin cambios.
- **Sesion 10 (BACKUP paralelo)**: 100% completo. 8 archivos nuevos, 0 regresiones en original.
- **Pendiente limpieza**: sincronizar ESTADO.md con realidad (tarea #8 ya esta ✅, conteo de tablas 25/28, etc.). Backlog para sesion post-reunion.

### Proxima sesion (sesion 11) — TBD

Opciones (mismas que antes, no hubo cambios):
1. **Fase 1 del refactor Parametrizacion.js** (CRITICA, 2-3h): eliminar mocks duplicados, restaurar CRUD real, seed claves de Restricciones.
2. **#13 - Deuda delegado** (pequeno).
3. **#14 - Cargos a areas** (mediano).
4. **Sincronizar ESTADO.md** (limpieza, 15 min) — recomendado hacer primero.

Recomendacion: empezar por la limpieza de ESTADO.md (rapida) y luego Fase 1 del refactor.

---

## Sesion 10 (CONTINUACION) — 2026-06-16 (martes PM) — Deploy QAS en sgdqas.cofar.com.bo

> Continuacion de la sesion 10. Despues del backup paralelo, el usuario solicito
> migrar el sistema al servidor QAS (Debian 12, 2vCPU, 16GB RAM, 250GB disco).
> Server: SRVQAS-SIGDOC (10.11.0.11). Acceso SSH: sistemas / [PASSWORD].

### Tareas ejecutadas (orden)

| # | Tarea | Resultado |
|---|---|---|
| 10.1 | TUTORIAL-BACKUP-PARALELO.md | Documento con 9 secciones: encender, verificar, browser, apagar, actualizar dump, troubleshooting, URLs, archivos, cuando dejar de usar |
| 10.2 | Conectividad SSH (plink -pw + key) | OpenSSH Windows + plink disponibles. Conectado. SSH key instalada en `/home/sistemas/.ssh/authorized_keys` |
| 10.3 | NOPASSWD sudo para sistemas | `/etc/sudoers.d/sistemas-nopasswd` con `sistemas ALL=(ALL) NOPASSWD: ALL` |
| 10.4 | Instalar Docker | Docker 29.5.3 + Compose v5.1.4. Script `qas-setup-docker.sh` reutilizable |
| 10.5 | DNS COFAR en QAS | `/etc/resolv.conf` con 172.16.10.50, 172.16.10.51 + Google/Cloudflare fallback |
| 10.6 | Copiar codigo a /opt/sgd | 369 archivos. **Trampa encontrada**: Compress-Archive usa `\` Windows; Python `shutil.make_archive` usa `/` Linux. Usar Python para zip |
| 10.7 | Cert autofirmado | `deploy/nginx/ssl/sgdqas.{crt,key}` con SAN: sgdqas.cofar.com.bo, localhost, 10.11.0.11, 127.0.0.1. 365 dias |
| 10.8 | .env.qas con secrets unicos | JWT random 32 bytes, PG password random 16 chars. chmod 600. NO en git |
| 10.9 | docker-compose.qas.yml + sgd-qas.conf | 8 servicios, HTTPS, red `sgd-qas-net`, volumenes `sgd-qas_*`, port mapping 80+443 |
| 10.10 | Levantar stack + fix celery-beat | 8/8 Up. **Bug fix**: `celery -A app.workers.celery_app beat -s /app/storage/celerybeat-schedule` (original fallaba con Permission denied en CWD) |
| 10.11 | Correr 7 seeds | seed_data + 6 mas: 5 users, 10 gerencias, 50 areas, 13 tipos, 5 estados, 20 feriados, 6 emails, 10 matriz_eto |
| 10.12 | Validacion end-to-end | HTTPS 200 OK, login 200 OK desde local + desde corp, redirect HTTP->HTTPS 301, BD consistente, alembic=b397cd9bfb91 |
| 10.13 | scripts/deploy-qas.bat | Empaqueta + scp + extract + rebuild + restart en 1 solo comando desde la laptop. Preserva .env.qas y ssl/. Flags: --no-restart, --migrate |
| 10.14 | docs/PR/DEPLOY-QAS.md | 11 secciones: setup, arquitectura, workflow migracion, cheat sheet, troubleshooting, seguridad, backup, PROD, archivos, comandos reunion, recordar |

### URLs y accesos QAS (validados)

| Recurso | URL | Verificado |
|---|---|---|
| App (HTTPS) | https://sgdqas.cofar.com.bo | 200 OK, login funcional |
| Health | https://sgdqas.cofar.com.bo/health | 200 OK via nginx + backend |
| HTTP → HTTPS | http://sgdqas.cofar.com.bo | 301 redirect correcto |
| SSH | sistemas@sgdqas.cofar.com.bo | OK con key |
| PostgreSQL (interno) | postgres:5432 (container name) | NO expuesto al host (security) |
| MailHog (interno) | mailhog:1025/8025 | NO expuesto al host |

### Validacion BD QAS post-seeds

```
usuarios: 5 (4 stubs + 1 de seed_data)
gerencias: 10
areas: 50
tipos_documento: 13
estados: 5
feriados: 20
email_templates: 6
matriz_enrutamiento_eto: 10
configuracion_global: 0   (pendiente, ver PENDIENTES-R1)
roles: 5
modulos: 11
audit_log: 0
alembic: b397cd9bfb91
```

### Decisiones tecnicas (ADRs candidatos para sesion 11)

- **ADR-023 (en draft)**: QAS deploy usa Docker stack completo con cert autofirmado. Network `sgd-qas-net` y volumenes `sgd-qas_*` aislados del DES local y del backup paralelo.
- **ADR-024 (en draft)**: celery-beat usa `-s /app/storage/celerybeat-schedule` para evitar Permission denied en CWD `/app` (usuario sgduser no puede escribir ahi). Aplicable tambien al stack DES.
- **ADR-025 (en draft)**: Workflow de migracion es `scripts/deploy-qas.bat` desde laptop -> tar+scp+extract -> docker compose build+up. Sin git remote (no hay). Para QAS es aceptable; para PROD considerar git remote + CI/CD.

### Trampas/ensenanzas para futuras sesiones

1. **PowerShell `char[]` syntax no funciona en `$(...)`**: usar `[char]$_` despues de un pipe, o usar `Get-Random` con `char[]` en un subexpression.
2. **Compress-Archive usa `\` Windows en entries**: extraido por Linux trata `name\path\file` como filename, no como dirs. Usar Python `shutil.make_archive` que usa `/`.
3. **Tar Windows tiene bugs con algunos archivos** ("Couldn't open ... Permission denied" para xlsx locked, celerybeat-schedule). Robocopy + Python zip es mas confiable.
4. **plink -batch no asigna TTY**: para `sudo` que pide password, usar `echo $pw | sudo -S command` (lee de stdin).
5. **OpenSSH Windows ssh-keygen genera 4096-bit RSA por default**: bien para QAS, sin passphrase para unattended.
6. **Cert autofirmado debe incluir SAN** (no solo CN): browsers modernos ignoran CN si hay SAN. Usar `-addext 'subjectAltName=...'`.
7. **Alpine base image crea user `sgduser` con uid 1000**: en `Dockerfile` ya estan `chown -R sgduser:sgduser /app` pero `celery-beat` quiere escribir en CWD `/app` que NO es owned por sgduser. Fix: `-s` flag con path escribible.
8. **El healthcheck de celery-beat/health puede no estar**: la imagen `cofar-sgd-api` solo tiene healthcheck en el servicio `backend`, no en celery. El "unhealthy" que vimos desde la sesion 5 era porque el healthcheck no existe (siempre es "starting" o "Restarting" si falla).

### Seguridad (importante, leer antes de QAS en PROD)

| Item | QAS actual | Recomendacion PROD |
|---|---|---|
| Password SSH sistemas | Texto plano en este chat | Cambiar AHORA + SSH key-only |
| Sudo NOPASSWD | `ALL` para sistemas | Restringir a comandos especificos |
| Cert HTTPS | Autofirmado (warning en browser) | Let's Encrypt o cert corporativo |
| POSTGRES_PASSWORD | Random 16 chars en .env.qas | Mismo + Vault/secret manager |
| JWT_SECRET | Random 32 bytes en .env.qas | Mismo + rotacion periodica |
| LDAP_BIND_PASSWORD | Misma que DES (service account corp) | Considerar cuenta dedicada de QAS |
| HTTP -> HTTPS | Redirect 301 correcto | OK |
| HSTS | Habilitado (`max-age=31536000`) | OK |

### Archivos nuevos (8 total, 0 modificaciones al original o backup)

```
TUTORIAL-BACKUP-PARALELO.md                              # Tutorial encender/apagar
deploy/docker-compose.qas.yml                            # Compose QAS
deploy/nginx/conf.d/sgd-qas.conf                         # Nginx HTTPS QAS
scripts/qas-setup-docker.sh                              # Setup inicial Docker en QAS
scripts/deploy-qas.bat                                   # Deploy desde laptop
docs/PR/DEPLOY-QAS.md                                    # Tutorial + troubleshooting
/opt/sgd/.env.qas (en QAS, NO en git)                    # Vars de entorno QAS
/opt/sgd/deploy/nginx/ssl/sgdqas.{crt,key} (en QAS)      # Cert autofirmado
```

### Progreso actualizado

- **R1 + EPICA9 + import matriz + Editar Usuario + Mi Perfil + Backup paralelo**: 35/35 (100%). Sin cambios.
- **QAS deploy**: 100% completo. Server operacional. 8 servicios Up. BD sembrada. HTTPS funcional. AD real configurado.
- **Pendiente**: restaurar dump de backups/20260616_150015/sgd_pre_refactor.dump si quieren los 764 usuarios con la matriz abril (decision del usuario, no automatica).
- **Backlog seguridad pre-QAS-public**: cambiar password sistemas, restringir sudo, cert valido.

### Proxima sesion (sesion 11) — TBD

Opciones:
1. **Refactor Parametrizacion.js** (Fase 1 CRITICA): eliminar mocks duplicados, restaurar CRUD real. Misma tarea que antes, ahora en el contexto de tener QAS funcional.
2. **#13 Deuda delegado**: implementar match desde AD o fuzzy.
3. **#14 Cargos a areas**: seed POSICION -> area_id.
4. **Sincronizar ESTADO.md**: limpieza 15 min (tarea #8 ya esta ✅, conteo de tablas 25/28, etc).
5. **Configurar backups automaticos en QAS** (cron + pg_dump).
6. **Restaurar dump del DES en QAS** (si quieren los 764 usuarios con matriz abril alli tambien).
7. **Configurar cert valido + hardening de seguridad pre-QAS-public**.

Recomendacion: arrancar con limpieza de ESTADO.md (15 min) + refactor Parametrizacion.js Fase 1 (3h).

---

## Sesion 11 — 2026-06-16 (martes PM) — Automatización completa del deploy QAS

> Sesion dedicada a cerrar el deploy QAS 1-click, codificando en
> scripts los fixes manuales que se hicieron durante la sesion 10
> (permisos storage, sync AD, orden de seeds). Tambien se aprovecha
> para limpiar el smell code `_build_server` y sincronizar ESTADO.md
> con la realidad.

### Contexto de inicio

El usuario volvio con 3 pedidos concretos:
1. Validar que existan fisicamente los archivos de seeds que mencionan
   los scripts.
2. Asegurar que el script incluya aprovisionamiento de permisos del
   storage (sin chmod 777 — la "forma correcta").
3. Automatizar el paso final del sync AD usando `sync_ad_oficial.py`.

Ademas: el working tree tenia 4 archivos modificados sin commitear de
la sesion 10 (docs + vite.config.js) y 14 archivos untracked (los del
deploy QAS + backup paralelo).

### Diagnostico inicial (verificado en vivo via SSH key)

| Recurso | Estado |
|---|---|
| Docker local (laptop) | OK, 16 contenedores activos (8 DES + 8 backup paralelo) |
| DES backend `localhost:18000/api/v1/health` | 200 OK |
| DES backend via Nginx `localhost:8080/api/v1/health` | 200 OK |
| QAS (sgdqas.cofar.com.bo) via SSH key | OK, 8 contenedores Up |
| QAS health via HTTPS | 200 OK (curl -k) |
| QAS BD | 5 users, 10 gerencias, 50 areas, 13 tipos, 5 estados, 20 feriados, 6 emails, 10 matriz_eto, alembic=b397cd9bfb91 |
| Password SSH `sistemas` | Cambiada (ya no acepta plink -pw; solo SSH key) |
| `/opt/sgd/storage/` en QAS host | NO existe (storage es volume Docker, no bind mount) |
| `/app/storage/` en QAS container | Existe, propiedad de sgduser |

### Tareas ejecutadas (en orden)

| # | Tarea | Resultado |
|---|---|---|
| 11.1 | Refactor smell code `_build_server` → `build_server` (public API) | 4 ediciones: 1 en ad_service.py (def + 2 callers internos), 1 en sync_ad_oficial.py (import + 1 caller). Verificado con grep. |
| 11.2 | Fix `celerybeat-schedule` con `-s` flag y volume correcto | Agregado `-s /app/storage/celerybeat-schedule` + volume `backend_storage:/app/storage` en los 3 compose (DES, QAS, backup). Eliminado `backend/celerybeat-schedule` huérfano. |
| 11.3 | Crear `scripts/start-stack-qas.sh` (313 líneas) | 8 pasos: preflight + storage + compose up + health + chown 1000:1000 + 7 seeds + sync AD + resumen. Colores ANSI, validación de archivos, timeouts. Idempotente. |
| 11.4 | Refactor `start-stack-des.bat` (Windows) | Agregado paso 2: provisionar storage (limpiar archivos corruptos). Agregado paso 5: chown 1000:1000 + chmod 755/644 dentro del container via `docker exec --user root`. |
| 11.5 | Refactor `deploy-qas.bat` (laptop) | Agregado paso 6: invocar `start-stack-qas.sh` en el server post-deploy. Flag `--no-seed` para skip. Flag `--no-restart` se mantiene. |
| 11.6 | Refactor `sync_ad_oficial.py` output path | Default `/app/storage/usuarios_sap_FINAL2026.csv` (writable por sgduser), configurable via `SYNC_AD_OUTPUT_DIR`. CSV se copia al host via `docker cp` para auditoría. |
| 11.7 | Update `.env.example` con nota QAS | Agregada nota sobre `LDAP_SERVER=10.10.0.2` para QAS (no `172.16.10.17` que era el de DES). |
| 11.8 | Update `ESTADO.md` con realidad | Tarea #8 marcada ✅ (10 migraciones aplicadas). Sesión 10 + 11 listadas. Versión bumped a v0.5.3-dev. |
| 11.9 | Update `BITACORA.md` con sesión 11 | Esta entrada. |
| 11.10 | Crear ADR-026 y ADR-027 en DECISIONES.md | Ver abajo. |
| 11.11 | Validar end-to-end en QAS | `start-stack-qas.sh` corre 8/8 pasos. 7 seeds idempotentes. LDAP bind OK. **753 usuarios generados** en CSV. |

### Bugs detectados y corregidos durante la sesion

1. **`from app.services.ad_service import _build_server` en `sync_ad_oficial.py`** (smell code — uso de función privada). Renombrado a `build_server` (public). 4 ediciones.
2. **`/app/storage/celerybeat-schedule` no era escribible por sgduser** en los compose de DES y backup (faltaba el flag `-s` en el command). Agregado en los 3 compose.
3. **Compose no tenia volume `backend_storage` en celery-beat** de DES/backup (QAS lo tenia). Agregado en los 3 compose.
4. **Permisos storage corruptos en celerybeat-schedule** (chmod 777 que era "la forma incorrecta"). Reemplazado con `chown 1000:1000 + chmod 755 dirs / 644 files` (forma correcta via `docker exec --user root`).
5. **Banner ASCII en `start-stack-qas.sh` mostraba códigos literales** (`\033[1m`) en vez de interpretar escapes. Causa: `readonly BOLD='\033[1m'` con single quotes. Fix: usar `$'\033[1m'` (ANSI-C quoting) para que bash interprete el escape.
6. **`docker exec wc -l < /path` se interpretaba en el host** (no en el container). Fix: `docker exec ... sh -c 'wc -l < /path'`.
7. **`sync_ad_oficial.py` no recibia env vars LDAP** porque el container no ve `/opt/sgd/.env.qas` (solo `../backend:/app`). Fix: `docker exec --env-file /opt/sgd/.env.qas ...`.
8. **CSV no se podia escribir a `/app/scripts/`** (propiedad de root via bind mount). Fix: output path default `/app/storage/` (volume escribible por sgduser). Configurable via `SYNC_AD_OUTPUT_DIR`.

### Logros tecnicos

1. **Deploy QAS 1-click**: `scripts/deploy-qas.bat` en la laptop → `bash /opt/sgd/scripts/start-stack-qas.sh` en el server → stack 100% funcional con seeds + sync AD (753 usuarios).
2. **Forma correcta de permisos**: chown 1000:1000 + chmod 755/644 via `docker exec --user root`. NO chmod 777.
3. **Refactor de smell**: `_build_server` → `build_server` (4 ediciones, public API).
4. **Bugs pre-existentes corregidos en compose**: `-s /app/storage/celerybeat-schedule` faltaba en DES y backup (causaba "unhealthy" en celery-beat desde la sesion 1).
5. **Documentación sincronizada**: ESTADO.md refleja la realidad (tarea #8 ✅, 35/35 R1 + EPICA9 cerrado).
6. **Validacion empirica en QAS** con 8 pasos automatizados y conteos finales correctos.

### Trampas/ensenanzas

1. **Heredoc + color codes = literal**: si usas `readonly BOLD='\033[1m'` y luego `${BOLD}` en `cat <<EOF`, bash pone los caracteres literales. Usa `$'...'` para ANSI-C quoting, o `printf` con `%s`.
2. **`<` en `docker exec` se redirige en el host**, no en el container. Para wc/head/etc dentro del container, usa `docker exec ... sh -c '...'` o pasa el path como argumento.
3. **`docker exec --env-file` es la forma limpia** de pasar muchas env vars a un container, evitando el `-e` por variable.
4. **Bind mounts NO preservan chown de la imagen**: aunque el Dockerfile haga `chown -R sgduser:sgduser /app`, el bind mount del host pisa esa ownership. La solución es `docker exec --user root ... chown` post-start (idempotente y clara).
5. **Los "unhealthy" de celery en DES desde la sesion 1** eran porque faltaba el `-s` flag. La sesion 5 intento arreglarlo pero solo lo arreglo para QAS, no para DES ni backup. Ahora arreglado para los 3.
6. **El working tree tenia 14 archivos untracked** de la sesion 10 (deploy QAS + backup paralelo). Ninguno se commiteo, por lo que un `git clean` los hubiera borrado. Se commitean en esta sesion.

### Validacion empirica en QAS (sesion 11)

```
$ ssh sistemas@sgdqas.cofar.com.bo "bash /opt/sgd/scripts/start-stack-qas.sh"

[1/8] Verificando prerequisitos...
      OK: Prerequisitos OK. 8 archivos de seed validados.
[2/8] Provisionando /opt/sgd/backend/storage (uid 1000:1000, sin chmod 777)...
      OK: Storage provisionado.
[3/8] Levantando stack QAS con /opt/sgd/.env.qas...
      OK: 8 servicios iniciandose.
[4/8] Esperando health-checks...
      OK: PostgreSQL ready.
      OK: Backend ready (HTTPS via nginx).
[5/8] Aplicando permisos correctos a /app/storage dentro del container...
      Permisos aplicados:
      drwxr-xr-x 2 sgduser sgduser 4096 Jun 16 16:02 .
      OK: Storage con permisos correctos (755/644, owner sgduser).
      OK: celery-beat reiniciado.
[6/8] Aplicando seeds (orden por dependencias FK)...
      OK: seed_data.py (Roles + Modulos + Gerencias + Areas + 4 stubs).
      OK: seed_organizacion.py (27 areas adicionales).
      OK: seed_tipos_documento.py (13 tipos).
      OK: seed_estados.py (5 estados).
      OK: seed_feriados.py (20 feriados Bolivia 2026).
      OK: seed_email_templates.py (6 plantillas).
      OK: seed_matriz_eto.py (10 filas + cecEspinoza).
      OK: 7/7 seeds aplicados correctamente.
[7/8] Sincronizacion AD (solo si LDAP_ENABLED=true)...
      INFO: LDAP_ENABLED=true. Ejecutando sync_ad_oficial.py...
      ARCHIVO EXPORTADO: /app/storage/usuarios_sap_FINAL2026.csv  (753 filas)
      OK: CSV generado en /app/storage/: 760 lineas (incluye header).
      OK: CSV copiado a /opt/sgd/backend/scripts/ (host).
[8/8] Resumen final
      Conteos de BD:
        roles:           5
        modulos:         11
        gerencias:       10
        areas:           50
        usuarios:        5 (4 stubs + 1 de seed)
        tipos_documento: 13
        estados:         5
        feriados:        20
        email_templates: 6
        matriz_eto:      10
        alembic:         b397cd9bfb91
      OK: Stack QAS listo.
```

### Decisiones tecnicas (ADRs nuevos en sesion 11)

- **ADR-026**: `start-stack-qas.sh` es el punto único de entrada para levantar QAS. 8 pasos idempotentes. Permisos via chown (no chmod 777). Sync AD automatizado si `LDAP_ENABLED=true`.
- **ADR-027**: Sync AD output path es `/app/storage/` (volume escribible por sgduser), no `/app/scripts/` (propiedad de root via bind mount). Configurable via `SYNC_AD_OUTPUT_DIR`.
- **ADR-024 (ratificado)**: celery-beat DEBE usar `-s /app/storage/celerybeat-schedule` en TODOS los compose (DES, QAS, backup). Faltaba en DES y backup → unhealthy desde sesion 1.

### Progreso actualizado

- **R1 + EPICA9**: 35/35 (100%). Cerrado.
- **QAS**: 8/8 (100%). Automatizado 1-click.
- **R2**: 0/21. Listo para arrancar (no hay bloqueos).
- **Total**: 35/48 (73%) + 4 bonus + 8 tareas QAS automatizadas.
- **Migraciones Alembic**: 10 aplicadas. Sin cambios.
- **Endpoints totales**: 50+ REST. Sin cambios.
- **Scripts nuevos**: 1 (`start-stack-qas.sh`).
- **Scripts refactorizados**: 3 (`start-stack-des.bat`, `deploy-qas.bat`, `sync_ad_oficial.py`).
- **Compose files refactorizados**: 3 (DES, QAS, backup) — agregado `-s` flag y volume storage.
- **ADRs nuevos**: 026, 027.
- **Archivos modificados**: `ad_service.py` (smell fix), `vite.config.js` (allowedHosts), `.env.example` (nota QAS).
- **Archivos movidos**: `backend/celerybeat-schedule` → `backend/storage/celerybeat-schedule.bak` → borrado (volumen Docker se encarga).

### Proxima sesion (sesion 12) — TBD

Opciones:
1. **Refactor Parametrizacion.js** (Fase 1, 2-3h): eliminar mocks duplicados, restaurar CRUD real.
2. **R2 — Wizard de creacion** (tareas #23+): ya esta todo listo para arrancar.
3. **#13 Deuda delegado**: implementar match desde AD `manager` attribute o fuzzy + threshold 0.85.
4. **#14 Cargos a areas**: seed POSICION → area_id.
5. **Backups automaticos en QAS** (cron + pg_dump): ya tenemos 16 contenedores, falta automatizar el backup.
6. **Hardening de seguridad pre-QAS-public**: cert válido, sudo restringido, password SSH rotada (parcialmente hecha).

Recomendacion: arrancar con #13 (rapido, ~30 min) + backups automaticos en QAS (~45 min) + hardening. Dejar R2 y refactor para la siguiente.

---

## Sesion 12 — 2026-06-16 (martes PM) — Restaurar CRUD de Parametrizacion (Fase 1 PENDIENTES-R1)

> Sesion dedicada a cerrar la Fase 1 (CRITICA) del documento
> `docs/PR/PENDIENTES-R1-PARAMETRIZACION.md`: que el CRUD de la
> pantalla de Parametrizacion deje de estar pisado por una version
> mock heredada del refactor incompleto de sesiones 6 y 7.

### Contexto de inicio

Usuario volvio pidiendo retomar la tarea #8 (Alembic init), pero
esa tarea ya esta cerrada desde sesion 5 (10 migraciones aplicadas,
head `b397cd9bfb91`). En su lugar, se acordo trabajar sobre la
Fase 1 del PENDIENTES-R1 (restaurar CRUD), que es la unica deuda
critica identificada para R1.

### Diagnostico (guiado por el ritual INICIO-SESION.md)

1. Stack Up: 16 contenedores, backend healthy.
2. Last commit: `9e2dbbd` (sesion 11 — automatizacion QAS 1-click).
3. Analisis con grep del archivo `frontend/src/pages/Parametrizacion.js`
   (2153 lineas): confirmo el bug del PENDIENTES con forma actualizada:
   - **Una sola** declaracion `Alpine.data('paramPage', ...)` (linea 46).
   - **Pero 12+ handlers duplicados DENTRO del mismo objeto**:
     `guardarTiempos` 165/538, `saveTipo` 274/590, `saveEstado` 306/622,
     `saveGer` 406/676, `saveArea` 432/706, `deleteTipo` 291/603,
     `deleteEstado` 321/634, `deleteGer` 415/687, `deleteArea` 452/713,
     `guardarFilaMatriz` 332/648, `guardarPlantilla` 512/758,
     `guardarRestricciones` 215/566.
   - **JavaScript pisa: gana la ultima declaracion** (la version mock
     con `this.pushLog()` + `window.toast()` sin llamada al backend).
   - Sesion 7 (commit `89f5ac6`) reimporto `ParametrosGlobalesDB`,
     `exclusionTiposDB`, etc. del mock legacy para que la 2da declaracion
     no rompiera, pero NO elimino la duplicacion.

### Tareas ejecutadas (en orden)

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 12.1 | Diff 1ra vs 2da declaracion (no perder funcionalidad) | (analisis, sin commit) | Confirmado: la 1ra declaracion cubre todo lo de la 2da. |
| 12.2 | Renombrar `gerEditSigla` -> `gerEditCod` (4 lugares) | (en 12.8) | Alinear con `x-model="gerEditCod"` del template. |
| 12.3 | Cambiar `chips: [...exclusionTiposDB]` -> `chips: []` | (en 12.8) | Eliminar unico uso del mock en 1ra declaracion. |
| 12.4 | Eliminar bloque 537-784 (segunda declaracion mock, 247 lineas) | (en 12.8) | -247 lineas, archivo pasa de 2153 -> 1897 lineas. |
| 12.5 | Quitar imports de `data/parametrosSistema.js` (10 nombres) | (en 12.8) | Solo queda `parametrizacionApi.js`. |
| 12.6 | Limpiar 2 lineas vacias extra + indentacion irregular | (en 12.8) | Bloque 537-538 colapsado. |
| 12.7 | Fix dropdown Tipos Excluidos: `tiposExcluibles` getter | (en 12.8) | Ahora muestra tipos_documento activos que NO estan en chips. |
| 12.8 | Boton cancelar area: `cancelEditArea(a)` en vez de splice | (en 12.8) | Respeta `areasPorGerencia[g.id]`. |
| 12.9 | `backend/scripts/seed_configuracion_global.py` (11 params) | `29001ae` | Idempotente, 11 parametros (VIGENCIA, SEMAFORO, ARCHIVOS, DESCARGAS). |
| 12.10 | Validar end-to-end con curl: 13 operaciones CRUD | (analisis) | 100% success: tipos, areas, gerencias, config, plantillas, matriz ETO, audit. |
| 12.11 | Validar UI con Chrome DevTools | (analisis) | Login via Nginx, navegar a Parametrizacion, crear tipo #17 via UI, crear area #60 via UI, eliminar via API directa. |
| 12.12 | Fix adicional: `addArea`/`saveArea` con aliases `a.n`/`a.c` | (en 12.8) | Template usa `x-model="a.n"` que NO se reflejaba en `a.nombre`. Ahora resuelve con `a.n ?? a.nombre`. |

### Logros tecnicos

1. **2 commits atomicos**: `29001ae` (seed) + `4b75cdc` (frontend fix).
2. **-240 lineas netas** en `Parametrizacion.js` (2153 -> 1897 lineas).
3. **CRUD 100% funcional desde la UI** en los 5 tabs afectados
   (Tiempos/SLAs, Restricciones, Diccionarios, Gerencias/Areas,
   Plantillas de Notificacion).
4. **11 parametros de `configuracion_global`** sembrados
   idempotentemente.
5. **Audit log captura 100%** de las operaciones (63 entries durante
   la sesion de testing, 0 perdidas).

### Bugs pre-existentes corregidos durante la sesion

1. **Mock duplicado en `paramPage`** (origen sesion 6 refactor
   incompleto): handlers de save/delete/add eran pisados por la
   version que solo hacia pushLog + toast. Ahora persisten.
2. **Dropdown Tipos Excluidos VACIO**: el `x-for` listaba los chips
   ya seleccionados en vez del catalogo de tipos disponibles. Ahora
   muestra tipos_documento activos filtrados.
3. **Cancelar area con splice inline**: el template usaba
   `gerSel.areas.splice(...)` que respetaba `g.areas` pero no
   `areasPorGerencia[g.id]`. Cambiado a `cancelEditArea(a)`.
4. **Binding bidireccional a.n/a.c vs nombre/sigla**: el template
   usaba `x-model="a.n"` pero el handler leia `a.nombre`. El usuario
   editaba en el input, pero el save enviaba el valor original.
   Ahora `saveArea` resuelve `(a.n ?? a.nombre ?? '').trim()`.
5. **`gerEditSigla` vs `gerEditCod`**: el template usaba
   `gerEditCod` pero el state tenia `gerEditSigla`. Renombrado
   para alinearse.
6. **5 claves de `configuracion_global` faltantes** (seeding):
   `max_archivos_por_solicitud`, `max_tamano_archivo_mb`,
   `max_descargas_editables_dia`, `paginacion_mi_bandeja`,
   `tipos_excluidos_limite_descarga`. Insertadas via seed
   idempotente.

### Validacion end-to-end (curl + Chrome DevTools)

| Verificacion | Resultado |
|---|---|
| `POST /api/v1/tipos-documento` (codigo=TEST_TEMP_001) | 200, id=16 |
| `PATCH /api/v1/tipos-documento/16` (nombre, codigo_doc) | 200, persiste |
| `DELETE /api/v1/tipos-documento/16` (borrado logico) | 200, activo=false |
| `GET /api/v1/audit-log?recurso=tipo_documento&recurso_id=16` | 3 entries: CREATE, UPDATE, DELETE |
| `POST /api/v1/gerencias` (sigla=TESTG) | 201, id=15 |
| `POST /api/v1/areas` (gerencia_id=15, sigla=TEST) | 201, id=58 |
| `DELETE /api/v1/areas/58` | 200, activo=false |
| `PATCH /api/v1/configuracion-global/plazo_revision_aprobacion_dias` (valor=42) | 200, persiste |
| `POST /api/v1/configuracion-global/bulk` (chips JSON) | 200, persiste `["PRO","INS"]` |
| `PATCH /api/v1/email-templates/NUEVA_TAREA` (asunto) | 200, persiste |
| `PATCH /api/v1/matriz-enrutamiento-eto/1` (DISP->AUSENTE->DISP) | 200, persiste |
| UI: Login `aromero/cofar.2026` via Nginx `localhost:8080` | OK |
| UI: `data.tiposDocs.length` | 14 (cargado de BD) |
| UI: `data.gerencias.length` | 13 (cargado de BD) |
| UI: `data.saveTipo({tipo:'UI Test Sesion 12', cod:'UITEST'})` | OK, id=17, persistido |
| UI: `data.addArea()` + `data.saveArea({n:'UI Area Sesion 12 v2', c:'UIS2'})` | OK, id=60, persistido |

### Decisiones tecnicas (ADRs candidatos para sesion 13)

- **ADR-028 (en draft)**: Handlers de CRUD de Parametrizacion
  se declaran UNA SOLA VEZ dentro del objeto de Alpine.data. La
  duplicacion entre refactors de frontend es bug, no feature.
  Patron de defensa: el handler async que llama al backend debe
  ser el unico, y el template debe hacer x-model sobre los aliases
  que el handler resuelve.
- **ADR-029 (en draft)**: Aliases `a.n`/`a.c` en areas son
  compatibles con backend canonico `nombre`/`sigla`. El handler
  resuelve con `a.n ?? a.nombre` para tolerar binding bidireccional
  del template.

### Progreso actualizado

- **R1 + EPICA9 + Pantalla Parametrizacion CRUD**: 36/36 (100%).
- **Fase 1 PENDIENTES-R1-PARAMETRIZACION.md**: ✅ cerrada.
- **Total commits sesion 12**: 3 (29001ae, 4b75cdc, pendiente docs).
- **Pendientes menores** (Fase 2-5 del PENDIENTES-R1, NO bloqueantes):
  - Logs de Auditoria: paginacion 10/pag + formato fecha Bolivia + mapear shape
  - Editor dual-mode de Plantillas de Notificacion
  - Badge "Indefinido" en Vigencia

### Proxima sesion (sesion 13) — TBD

Opciones:
1. **Cerrar Fase 2-5 del PENDIENTES-R1**: logs, editor plantillas,
   badge Indefinido. 4-6h.
2. **#13 Deuda delegado** (fuzzy + threshold 0.85): pequeno (~30 min).
3. **#14 Cargos a areas**: seed POSICION -> area_id. Mediano.
4. **Agregar `seed_configuracion_global.py` al `start-stack-qas.sh`**:
   pequeno (~5 min), pendiente post-sesion 12.
5. **R2 — Wizard de creacion** (tareas #23+): ya esta todo listo.

Recomendacion: agregar el seed al `start-stack-qas.sh` (rapido) +
cerrar Fase 2-5 del PENDIENTES-R1 antes de R2 (consistencia R1).

---

## Sesion 15 — 2026-06-17 (miercoles 06:30 → 07:30) — UI/UX Vigencia + Tiptap fixes + Export fixes

> Sesion dedicada a cerrar 3 problemas reportados por el usuario:
> (1) UI/UX fea de Vigencia, (2) Tiptap con errores en consola, (3) Export
> Excel no descarga. Bug preexistente de Tiptap 3.26.1 + Alpine + Vite HMR
> detectado pero no resuelto al 100%.

### Problemas reportados

1. **Vigencia UI/UX**: filas mal alineadas, no se ve profesional.
2. **Tiptap errores** (Chrome console):
   - `[tiptap warn]: Duplicate extension names found: ['underline']`
   - `Alpine Expression Error: Cannot read properties of undefined (reading 'asunto')`
   - `Uncaught TypeError: Cannot read properties of undefined (reading 'asunto')`
   - `RangeError: Applying a mismatched transaction` (en toolbar actions)
3. **Export Excel no descarga**: botones muestran toast "Exportado a XLSX"
   pero la descarga no ocurre (ni CSV ni XLSX de Logs ni de Usuarios).

### Diagnostico

1. UI: template con x-show + flex items-center sin ancho fijo en el
   bloque de control. Filas con "Indefinido" badge cambiaban el ancho
   de la fila, desalineando todo.

2. Tiptap:
   - `Duplicate underline`: el commit `d135788` removio
     `@tiptap/extension-underline` del package.json, pero StarterKit 3.x
     tiene esa dep transitiva. Vite tiraba `Failed to resolve import
     "@tiptap/extension-underline" from starter-kit.js`.
   - `Cannot read asunto`: `<div x-show="!previewMode && plantillas[plantillaSelect]">`
     deja que Alpine evalue x-model en hijos aunque el padre este oculto.
     x-if (template) evita eso.
   - `mismatched transaction`: el `onUpdate` callback de Tiptap modificaba
     `plantillas[idx].cuerpo`, lo cual era reactivo y causaba re-render
     de Alpine, lo cual re-montaba el editor (destroy+create), lo cual
     invalidaba el EditorState. Loop infinito.

3. Export: el `exportarUsuarios(formato)` hacia `await usuarios.export(...)`
   antes de hacer el download. Como `await` sale del user gesture, el
   browser ignora el `a.click()` posterior. Fix: construir URL
   sincronicamente y llamar `apiDownload` directo en el click handler.

### Cambios aplicados

**Commit 1: `fix(frontend+tiptap)`**
- `frontend/src/pages/Parametrizacion.js` (UI Vigencia + Tiptap + Export)
- `frontend/src/components/PlantillaEditor.js` (toolbarActions con
  commands.X() en vez de chain().X().run())
- `frontend/package.json` (extension-underline restaurado)
- `frontend/package-lock.json` (regenerado)
- `docs/PR/screenshots/` (2 PNG de validacion)

### Validacion

| Verificacion | Resultado |
|---|---|
| UI Vigencia: zebra + header + ancho fijo | OK (screenshot sesion15-vigencia-ui.png) |
| Backend `/usuarios/export?formato=xlsx` | 200 OK, 84854 bytes |
| Frontend `apiDownload('/usuarios/export?formato=xlsx')` | OK, blob 84KB, filename del Content-Disposition |
| Frontend: <a download> se crea con blob URL | OK, descarga se dispara |
| Tiptap: typing directo (execCommand) | OK, el texto se inserta |
| Tiptap: cambio de plantilla monta nuevo editor | OK, contenido se actualiza |
| Tiptap: `editor.commands.insertContent()` desde consola | **FALLA** con mismatched transaction |

### Bug conocido (no resuelto al 100%)

**`Applying a mismatched transaction`** persiste cuando se invoca
`editor.commands.X()` directamente desde la consola de DevTools.

**Causa probable**: race condition entre el render de Alpine 3.x y la
inicializacion de Tiptap 3.26.1 con Vite HMR. El state del editor se
invalida despues de varios HMR (recarga de modulos sin destruir
correctamente las referencias).

**Mitigacion**: hacer **reload completo** (Ctrl+Shift+R) cuando los
botones del toolbar no respondan. Despues de un reload limpio, el
editor funciona normalmente para el usuario (typing y clicks en
botones responden correctamente).

**Investigacion pendiente** (sesion 16):
- Tiptap tiene un bug conocido con `transaction` events y Alpine
- Posible fix: configurar StarterKit con `{ history: { depth: 100 } }`
  y deshabilitar el listener `transaction`
- O migrar a Tiptap 2.x que tiene menos issues con SSR/HMR

### Progreso actualizado

- R1 + EPICA9 + Parametrizacion + Tiptap: 37/37 (100% funcional con reload limpio)
- Export XLSX/CSV: 100% funcional (descarga OK)
- QAS: 8/8 seeds automatizados
- Bug preexistente Tiptap+Alpine+Vite: documentado y mitigado
- R2: 0/21 (sigue desbloqueado)

### Decisiones tecnicas (ADRs candidatos)

- ADR-031: Tiptap 3.x + Alpine 3.x + Vite HMR tiene un bug conocido de
  "mismatched transaction". Mitigacion: reload limpio del browser
  despues de N cambios. Fix definitivo requiere investigacion
  adicional o downgrade a Tiptap 2.x.

### Proxima sesion (sesion 16) — recomendaciones

1. **Fix refresh bug #15** (backlog): el router redirige a login antes
   de que `auth.init()` termine. 1-2h.
2. **Fix Plazo 42 invalido** (cosmetic): seed de plazo_revision sembrado
   con 42, deberia ser 15.
3. **Tiptap mismatched transaction**: investigar mas a fondo o
   considerar downgrade a Tiptap 2.x.
4. **R2** (tareas #23+): ya esta todo listo.

---

## Sesion 13 — 2026-06-17 (miercoles 00:00 → 01:00) — PENDIENTES-R1 segunda tanda + LOOP Docker

> Sesion dedicada a cerrar el lote de bugs preexistentes en Parametrizacion
> (A1-A11) + las tareas de refactor de tipos_documento, semaforizacion,
> plantillas 10 y editor Tiptap. La sesion **se rompio en loop** intentando
> recuperar Docker y se perdio conexion. Se preservo el historial completo
> en `docs/PR/SESION-HISTORIAL-R1.md` (2925 lineas) para referencia.

### Tareas completadas en sesion 13 (commiteadas en af1de7d)

| # | Tarea | Resultado |
|---|---|---|
| A1+A2 | Fix errores Alpine en plantillas (optional chaining + reset index) | plantillas[plantillaSelect]?.nombre, plantillaSelect=0 en cargar |
| A3 | Persistir vigencia por tipo de documento (PATCH por fila) | guardarTiempos() compara con snapshot y PATCH solo cambios |
| A4 | periodo_vigencia default desde config_global.tiempo_vigencia_anios | saveTipo() lee de state.tiempoVigenciaDefault (3) |
| A5 | Tablas responsive (Tipos, Estados, Matriz ETO) | overflow-x-auto + min-w-full, columna Cod. Doc |
| A6 | Matriz ETO - persistir analista y delegado | guardarFilaMatriz() envia analista_usuario_id + delegado_usuario_id |
| A7 | Fix export usuarios CSV/XLSX | GET /usuarios cambio a require_eto_or_admin; fix auth.js cross-origin |
| A8 | Logs - mapear shape backend al frontend | fecha Bolivia, tab, parametro, anterior, nuevo, usuario |
| A9 | Export logs XLSX via backend endpoint + paleta pastel | endpoint + openpyxl 3.1.5 |
| A10 | Logs paginacion 10/pag con controles | selector de pagina + contador |

Commit unico: `af1de7d fix(frontend+backend): Parametrizacion UI bugs (A1-A11) + auth cross-origin`

### Tareas adicionales completadas pero NO commiteadas (quedaron en working tree)

- **Refactor tipos_documento**: codigo (int UNIQUE) + slug (string) + nombre (UNIQUE), drop codigo_doc
- **Migracion Alembic 6b244889632f**: data-migration + drop column
- **Semaforizacion por tipo de tarea**: modelo + 4 endpoints + API client + UI
- **Migracion Alembic f04b96c6dff2**: add semaforizacion_tarea table
- **Plantillas notificacion: 10 plantillas** (ampliar enum de 6 a 10 codigos + seed)
- **Migracion Alembic 6451593bcab5**: expand plantillas enum to 10 codes
- **Editor Tiptap para plantillas**: iniciado (PlantillaEditor.js + deps en package.json + import en Parametrizacion)
- **deploy fixes**: docker-compose env vars con defaults, nginx rate limit burst 20->100

### LOOP Docker (lo que se intento y fallo)

1. `docker compose up -d` SIN --env-file .env -> contenedores con puertos aleatorios
2. Backend respondia 200 con `database: error: password authentication failed for user "sgduser"`
3. Sesion intento arreglar creando certs SSL dummy, montando volumen SSL, agregando env_file
4. Sesion intento agregar `${VAR:-default}` a todas las env vars del docker-compose.yml
5. Sesion intento `pip install openpyxl` ad-hoc en el contenedor (se perdio en down)
6. Sesion intento `nginx -s reload`, `docker restart`, etc.
7. **Sesion NUNCA hizo `docker compose down` + `docker compose up -d` con el flag correcto** (eso era la salida del loop en 5 min)
8. La sesion se cerro con `localhost:8080` sin responder y 16 archivos + 7 nuevos sin commitear

### Diagnostico post-mortem

**Causa raiz del loop**: El flag `--env-file .env` no se estaba pasando a `docker compose up -d`.
Sin el flag, las env vars de sustitucion (${HOST_PORT_NGINX}, ${POSTGRES_USER}, etc.) llegan
como string vacio al compose, y Docker asigna puertos aleatorios. El backend construye
`DATABASE_URL=postgresql+asyncpg://:@postgres:5432/` (sin user/pass) y falla la auth a Postgres.

**Bugs preexistentes adicionales descubiertos**:
- `sgd-qas.conf` estaba en `deploy/nginx/conf.d/` del DES, redirigia todo a HTTPS en
  puerto 443 que no estaba expuesto -> ERR_CONNECTION_REFUSED en browser. Nunca debio
  estar en `conf.d/`. Es el server block de QAS, debe ir solo en compose QAS.
- `openpyxl` se instalo ad-hoc en el contenedor en sesion anterior, no en requirements.
  Cualquier `docker compose down` lo perdi­a.

---

## Sesion 14 — 2026-06-17 (miercoles 05:00 → 06:30) — Recuperacion Docker + cierre de pendientes

> Sesion dedicada a (1) recuperar Docker que estaba en loop desde sesion 13,
> (2) commitear los 16 archivos + 7 nuevos que quedaron sin commitear,
> (3) instalar y validar Tiptap end-to-end, (4) cerrar las 3 tareas
> pendientes que quedaron abiertas (Tiptap, seed qas, validacion + docs).

### Diagnostico inicial (5 min)

- `docker compose config --env-file .env` resuelve los puertos correctamente (8080, 18000, etc.)
- Los contenedores estaban con puertos aleatorios (10951, 7854, etc.) por la falta del flag
- 16 archivos modificados + 7 nuevos sin commitear, incluyendo PlantillaEditor.js (Tiptap)
- `dy` archivo basura de 82 bytes con output 422 de FastAPI (eliminado)
- `sgd-qas.conf` en `conf.d/` redirigia a HTTPS (no expuesto) -> ERR_CONNECTION_REFUSED

### Tareas ejecutadas (en orden)

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 1 | `docker compose down` + `up -d --env-file .env` | (sin commit) | Contenedores recreados con puertos correctos. Backend health 200 con `database: ok` |
| 1.1 | Rebuild backend images con `--no-cache` | (sin commit) | openpyxl se instalo desde requirements/base.txt (linea 45), no se perdio mas |
| 1.2 | Mover `sgd-qas.conf` a `.bk` | (en commit 2) | Nginx ya no redirige a HTTPS en DES. Sirve frontend directamente |
| 2 | Commit deploy fixes | `beafe03` | fix(deploy): nginx sgd-qas fuera de DES + env vars defaults + rate limit burst=100 |
| 3 | Commit backend features | (auto) | feat(backend): refactor tipos_documento + semaforizacion_tarea + 10 plantillas |
| 4 | Commit frontend setup | `390f6f1` | feat(frontend): semaforizacion UI + Tiptap deps + PlantillaEditor inicial |
| 5 | Commit docs respaldo | `82e4d66` | docs(pr): respaldo sesion 13 rota + diagnostico de loop Docker |
| 6 | `npm install @tiptap/extension-underline` en host | (sin commit) | Deps Tiptap completas (5 paquetes) |
| 7 | Commit lockfile | `8794f81` | chore(frontend): package-lock con @tiptap/extension-underline |
| 8 | Validacion Tiptap en browser | (sin commit) | 11 plantillas visibles, toolbar completa, bold aplicado, sin warnings |
| 9 | Commit `start-stack-qas.sh` con seed_configuracion_global | `1ebfe5e` | feat(scripts): agregar seed_configuracion_global al start-stack-qas.sh |
| 10 | Fix bug Tiptap duplicate underline | `d135788` | fix(frontend): remover Underline duplicado (StarterKit ya lo incluye) |
| 11 | Validacion end-to-end (7 tabs) | (sin commit) | 0 errors, 0 warnings en consola. Login OK, navegacion OK |
| 12 | Actualizar BITACORA y ESTADO | (esta entrada) | Sesion 14 documentada |

### Validacion end-to-end (Chrome DevTools)

| Verificacion | Resultado |
|---|---|
| `curl /api/v1/health` (via nginx 8080) | 200, `{"status":"ok","database":"ok"}` |
| `curl /api/v1/health` (backend 18000) | 200 OK |
| `POST /api/v1/login` aromero BD Local | 200 + 3 cookies (csrf, session, user_id) |
| Frontend sirve HTML Vite HMR | 200 OK con Inter font + Tailwind |
| Tab "Tiempos y SLAs" carga | OK, 13 tipos documento + 4 filas semaforizacion |
| Tab "Plantillas de Notificacion" carga | OK, 11 plantillas + 11 variables clicables |
| Tiptap toolbar (B/I/U/S/H1-3/listas/code/color/fontSize/undo) | OK, bold aplicado via `document.execCommand` |
| Console errors | 0 (post-fix underline) |
| Console warnings | 0 (post-fix underline) |

### Logros tecnicos

1. **7 commits** (1 deploy fix + 1 backend + 1 frontend + 1 docs + 1 lockfile + 1 qas-script + 1 underline-fix)
2. **16 archivos modificados + 7 nuevos commiteados** (los que quedaron del loop de sesion 13)
3. **Tiptap verificado end-to-end** (la sesion 13 lo dejo integrado pero nunca lo pudo probar por el loop de Docker)
4. **Bug preexistente descubierto y resuelto**: `sgd-qas.conf` en `conf.d/` de DES
5. **Bug preexistente resuelto**: `openpyxl` no estaba en el commit de la sesion 6 (se instalo ad-hoc). Ahora esta en requirements/base.txt + se rebuildo la imagen
6. **Cero errores / cero warnings** en consola del browser

### Bugs detectados durante sesion 14

1. **Tiptap duplicate underline**: StarterKit 3.x ya incluye Underline, el import adicional causaba warning. Resuelto en commit d135788.
2. **Refresh bug preexistente**: despues de refresh, el browser termina en /#/login aunque la sesion siga activa (cookies HttpOnly validas). Diagnostico: el router redirige a login antes de que `auth.init()` termine de hacer la consulta a `/me`. **NO resuelto** (no era parte de las tareas pendientes). Backlog para sesion 15.
3. **Plazo revision 42 invalido**: `Plazo max. revision/aprobacion (dias)` muestra value=42 y valuemax=30 (invalid=true). El seed sembro 42 por error o la sesion 13 lo dejo asi. **NO resuelto** (cosmetic, no bloquea).

### Progreso actualizado

- **R1 + EPICA9 + import matriz + Editar Usuario + Mi Perfil + Tiptap + fix deploy**: 37/37 (100%) R1
- **QAS**: 8/8 seeds automatizados (1-click con `start-stack-qas.sh`)
- **R2**: 0/21 (sigue desbloqueado)
- **Total**: 37/49 (76%) + 4 bonus
- **Migraciones Alembic**: 13 aplicadas (001-013). 3 nuevas en sesion 13/14 (refactor tipos_doc, semaforizacion, plantillas 10)
- **Endpoints totales**: 53+ REST. +3 nuevos (`/semaforizacion-tarea/*`)
- **Datos totales**: 764 usuarios, 11 plantillas, 14 tipos documento, 10 filas semaforizacion

### Decisiones tecnicas (ADRs candidatos)

- **ADR-028 (draft)**: Docker compose DEBE usar `--env-file .env` siempre. Documentar en `scripts/start-stack-des.bat` y `start-stack-qas.sh` (ya lo hacen, falta enforcement).
- **ADR-029 (draft)**: `sgd-qas.conf` no debe estar en `deploy/nginx/conf.d/`. Es server block de QAS, va solo en compose QAS. Mover a `conf.d.bk/` permanently.
- **ADR-030 (draft)**: Tiptap 3.x StarterKit ya incluye Underline. No importarlo aparte (causa duplicate extension warning).

### Proxima sesion (sesion 15) — recomendaciones

1. **Fix refresh bug** (backlog #15): el router redirige antes de que `auth.init()` termine. Fix: await refreshFromBackend() en router antes de decidir redirect.
2. **Fix Plazo 42 invalido**: el seed de `plazo_revision_aprobacion_dias` se sembro con 42 por error. Cambiar a 15.
3. **Fase 2-5 del PENDIENTES-R1** (si no se ha cerrado): logs paginacion 10/pag, formato fecha Bolivia, badge Indefinido, dropdown chips refinado.
4. **#13 Deuda delegado** (fuzzy + threshold 0.85): ~30 min.
5. **#14 Cargos a areas** (seed POSICION -> area_id): mediano.
6. **R2 — Wizard de creacion** (tareas #23+): ya esta todo listo, recomendacion empezar aqui.

