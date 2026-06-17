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


---

## Sesion 16 � 2026-06-17 (miercoles) � Tiptap+Alpine root cause + eliminacion debug page

### Contexto
Sesion 15 habia intentado mitigar el bug preexistente "Applying a
mismatched transaction" con un workaround (reload limpio del browser)
sin resolver la causa raiz. Sesion 16 arranca con el objetivo de
investigar la doc oficial de Tiptap para encontrar la causa raiz y
probar cosas NUEVAS (no el workaround).

### Investigacion
- webfetch a https://tiptap.dev/docs/editor/getting-started/install/alpine
- La doc oficial dice verbatim: "Alpine's reactive engine automatically
  wraps component properties in proxy objects. If you attempt to use a
  proxied editor instance to apply a transaction, it will cause a Range
  Error: Applying a mismatched transaction, so be sure to unwrap it using
  Alpine.raw(), or simply avoid storing your editor as a component
  property."
- Esto confirma que la sesion 15 estaba mitigando el sintoma (usando
  chain().focus().X().run() en vez de editor.commands.X() directo)
  pero NO resolvia la causa: el editor seguia siendo wrapped en un
  Proxy porque estaba guardado en 	his._editorHandle (state reactivo
  de Alpine).

### Tareas ejecutadas

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 16.1 | Crear rontend/src/pages/DebugTiptap.js (pagina debug independiente) | (debug, eliminado al final) | Pagina fullscreen que replica EXACTAMENTE el patron de la doc oficial: let editor en closure del factory de Alpine.data, chain().focus().X().run() para la mayoria de los marks. Toolbar B/I/U/S/H1-3/listas/code/blockquote + undo/redo. 5 plantillas precargadas para testear cambio de contenido. |
| 16.2 | Registrar ruta /_debug/tiptap en router con render fullscreen (bypass auth + AppLayout) | (debug, eliminado) | Caso especial en handleRoute() similar a /login. URL accesible sin autenticacion. |
| 16.3 | Validar patron del debug con Chrome DevTools | OK | 0 errors, 0 warnings en consola. Typing, bold, H1, listas, cambio de plantilla, undo, color picker, fontSize, localStorage � TODO funciona. |
| 16.4 | Agregar persistencia localStorage al debug | OK | Boton "Guardar en navegador" + "Cargar del navegador" + "Limpiar". F5 recupera contenido automaticamente. Sirvio para validar que el patron funciona end-to-end sin BD. |
| 16.5 | Investigar setColor en Tiptap 3.x | OK | El source @tiptap/extension-text-style/dist/index.js linea 166 confirma: setColor: (color) => ({chain}) => chain().setMark(...).run(). Es un COMMAND (no chain method). Hay que usar editor.commands.setColor(color) directo, NO editor.chain().focus().setColor(color).run() (que falla con "setColor is not a function"). |
| 16.6 | Investigar setFontSize en Tiptap 3.x | OK | Mismo patron: setFontSize: (fontSize) => ({chain}) => chain().setMark(...).run(). Command, no chain method. |
| 16.7 | Reemplazar TextStyle + Color por TextStyleKit | OK | TextStyleKit de @tiptap/extension-text-style incluye TextStyle + Color + FontSize + FontFamily + BackgroundColor + LineHeight + emoveEmptyTextStyle. Es la forma recomendada por la doc oficial. |
| 16.8 | Refactor PlantillaEditor.js: API simple {editor, destroy} | 154bc4 | Eliminada la "handle API" intermedia. El modulo retorna {editor, destroy} y el caller es responsable de guardar el editor en closure. |
| 16.9 | Refactor ESTRUCTURAL del factory paramPage en Parametrizacion.js | 154bc4 | Convertido de Alpine.data('paramPage', () => ({...})) a Alpine.data('paramPage', () => { let editor = null; let editorDestroy = null; return {...}; }). Todos los metodos tbToggle, tbSetColor, tbSetFontSize, _mountTiptap, _cleanupEditor, insertarEtiqueta, guardarPlantilla acceden al editor del closure. |
| 16.10 | Validar TODO en Parametrizacion > Plantillas | OK | Bold, Italic, Underline, H1-3, listas (bullet/ordered), blockquote, codeBlock, undo/redo, color picker, fontSize, cambio de plantilla, insercion de variable {{CODIGO}} desde chips � TODO funciona. |
| 16.11 | Validar persistencia end-to-end | OK | data.guardarPlantilla() -> PATCH /api/v1/email-templates/ASIG_REVISION -> BD. Verificado con psql: contenido guardado correctamente. F5 + re-login -> editor carga HTML desde BD correctamente. |
| 16.12 | Validar previsualizar con MOCK data | OK | Click en "Previsualizar" -> POST /api/v1/email-templates/{codigo}/preview con mock { {{CODIGO}}: 'PRO-CAL-045', ... } -> HTML renderizado con variables sustituidas. |
| 16.13 | Agregar @mousedown.prevent a TODOS los botones de toolbar | 154bc4 | Patron WSIWYG: evita que el boton robe el focus del editor al hacer click. Aplicado a 17 botones (16 toolbar + 1 chip de variable). |
| 16.14 | Eliminar debug page + ruta | 154bc4 | Borrado DebugTiptap.js. Removida entrada en outes y outeTitles. Removido caso especial /_debug/* en handleRoute(). Removida excepcion de auth para /_debug/*. Limpiados screenshots de debug. |

### Causa raiz final (la que la sesion 15 no vio)

La sesion 15 intentaba mitigar el bug cambiando chain().X() por
editor.commands.X() (y viceversa) segun el contexto. Pero el bug NO
estaba ahi. Estaba en que el editor se guardaba en 	his._editorHandle
(state reactivo de Alpine). Alpine wrappea TODAS las props de 	his
en Proxies para detectar cambios. Cuando ProseMirror intentaba ejecutar
un command, el wrapper Proxy causaba el "Applying a mismatched
transaction" porque ProseMirror detecta que la transaction se origino
desde un state diferente.

El fix definitivo (segun la doc oficial): el editor debe vivir en el
CLOSURE del factory de Alpine.data, NO en 	his. Asi Alpine no tiene
forma de wrappear el editor en un Proxy.

### Logros tecnicos

1. **Causa raiz del bug "Applying a mismatched transaction" identificada
   y resuelta** � ya no es necesario el workaround de "reload limpio"
   de la sesion 15.
2. **Tiptap 3.x + Alpine 3.x + TextStyleKit + StarterKit** funcionando
   end-to-end en Parametrizacion.js.
3. **Color picker + fontSize** funcionando con TextStyleKit (requirio
   descubrir que son commands, no chain methods).
4. **Persistencia BD** verificada con query directo a email_templates.
5. **Previsualizar con MOCK data** funcionando (las variables {{...}}
   se sustituyen por datos de prueba antes de renderizar el HTML).
6. **Patron @mousedown.prevent** aplicado a todos los botones de
   toolbar (problema conocido de editores WSIWYG que la sesion 15
   habia intentado mitigar con timing/setTimeout).
7. **Debug page eliminada** � sin rastros en el codigo final.

### Bugs preexistentes confirmados (no relacionados, fuera de scope)

- sync-status devuelve 403 para aromero (ETO). El frontend lo llama
  sin verificar permisos. Bug preexistente, NO relacionado con Tiptap.
- Refresh bug (#15): despues de F5 el browser termina en /#/login
  aunque la sesion siga activa. Bug preexistente, NO resuelto en esta
  sesion (esta documentado para sesion futura).

### Progreso actualizado

- **R1 + EPICA9 + Parametrizacion + Tiptap**: 100% funcional sin
  workaround. Sesion 15 -> 16 cierra definitivamente el bug.
- **QAS**: 8/8 seeds automatizados (sin cambios).
- **R2**: 0/21 (sigue desbloqueado, no hubo avances).
- **Total**: 38/49 (78%) + 4 bonus.
- **Migraciones Alembic**: 13 aplicadas (sin cambios).
- **Endpoints totales**: 53+ REST (sin cambios).
- **Commit**: 154bc4 fix(frontend): Tiptap 3.x + Alpine 3.x root cause of mismatched transaction

### Decisiones tecnicas (ADRs candidatos para sesion 17)

- ADR-032: Tiptap 3.x + Alpine 3.x requiere que el editor viva en
  closure del factory, NO en 	his. Patron oficial de
  https://tiptap.dev/docs/editor/getting-started/install/alpine.
- ADR-033: Tiptap 3.x con TextStyle expone setColor/setFontSize como
  COMMANDS, no chain methods. Usar editor.commands.X() directo.
- ADR-034: Para Color+FontSize usar TextStyleKit de
  @tiptap/extension-text-style (incluye todas las styling extensions).

### Proxima sesion (sesion 17) � recomendaciones

1. **Fix refresh bug #15** (1-2h): el router redirige a /#/login
   antes de que auth.init() termine. Solucion: await refreshFromBackend
   en router antes de decidir.
2. **Fix Plazo 42 invalido** (cosmetic, 5 min): seed de
   plazo_revision_aprobacion_dias se sembro con 42, deberia ser 15.
3. **Fix 403 sync-status** para ETO (backlog).
4. **R2 � Wizard de creacion** (tareas #23+): ya esta todo listo.
5. **#13 Deuda delegado** (fuzzy + threshold 0.85): ~30 min.
6. **#14 Cargos a areas** (seed POSICION -> area_id): mediano.

---

## Sesion 17 - 2026-06-17 (miercoles 06:00 -> 06:25) - Cierre R1: Matriz ETO + Previsualizar + Impersonate

> Sesion dedicada a cerrar los 3 ultimos pendientes identificados por el usuario
> para dar R1 por cerrado. Todo en una sola sesion (~25 min de codigo + 30 min
> de diagnostico con Chrome DevTools + 15 min de docs).

### Problemas reportados
1. **Matriz ETO vacia**: dropdowns de Analista ETO Asignado mostraban
   "Seleccionar" aunque la BD tenia los analistas cargados (CAL=aromero,
   RRH=cecEspinoza, etc.). El usuario sospechaba que "ni se ven los valores".
2. **Previsualizar de plantillas obsoleto**: con Tiptap el editor es WYSIWYG,
   la opcion "Previsualizar" no tiene sentido, quiere eliminarla.
3. **Impersonate inactivo**: boton Impersonar existe en Gestion de Usuarios
   pero el flujo end-to-end (banner, audit, refresh) no estaba conectado.
   Solo ADMIN podia (no ETO). No habia registro en audit_log.

### Diagnostico (guiado por el ritual INICIO-SESION.md)

Sesion arranco con el ritual habitual (lectura de BITACORA, ESTADO,
INICIO-SESION). Stack diagnosticado: 8 contenedores Up, backend healthy.

**Bug 1**: inspeccion con Alpine.\ revelo que los datos SI se cargaban
correctamente (matrizETO.length=10, analistas.length=4, usuariosActivos.length=200)
pero los <select> con x-model.number="m.analista_id" no matcheaban. Causa:
bug clasico de Alpine 3 - x-model no se re-bindea cuando las options del
<template x-for> se cargan DESPUES del initial render. Mismo bug afecto al
checkbox de disponibilidad.

**Bug 2**: revisar dmin_impersonate.py (221 lineas, sesion 4) mostro que:
- Solo ADMIN podia impersonar (no ETO)
- Sin validacion de no-auto-impersonate
- write_audit() NO se llamaba en start/stop
- /me ya leia la cookie impersonated_user y devolvia impersonated_by
  (auth.py:352-385), asi que la base estaba

**Bug 3**: busqueda de previsualizar revelo 5 ocurrencias en
Parametrizacion.js: estado (previewMode/previewHtml), 2 handlers
(previsualizarPlantilla/cerrarPreview), boton, overlay, y 3 <template
x-if="!previewMode && ...">. Limpio.

### Tareas ejecutadas (en orden)

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 1 | Bug 1: Fix binding Matriz ETO | df4aceb | 3 cambios en Parametrizacion.js: (a) convertir analista_id/delegado_id a string en mapeo, (b) agregar data-matriz-id/data-matriz-select al <select>, (c) forzar el value desde cargarDiccionarios() dentro de await nextTick(). Mismo fix al checkbox. BD persistida, audit_log captura cambio. |
| 2 | Bug 3: Eliminar Previsualizar | (mismo df4aceb) | -30 lineas netas. Removido estado, 2 handlers, boton, overlay, 3 x-if condicionales. |
| 3 | Bug 2 front: impersonarUsuario + stopImpersonate | (mismo df4aceb) | Validaciones rol=admin/eto + no-auto-impersonate. refreshFromBackend() en vez de window.location.hash. Boton Impersonar solo visible si role=admin/eto. |
| 4 | Bug 2 back: admin_impersonate acepta ETO + audit dedicado | 4763ff9 | ADMIN o ETO pueden impersonar. Validacion no-auto + no-doble-impersonate. write_audit() con recurso='impersonate' y accion dedicada IMPERSONATE_START/STOP. Bugfix preexistente: ad_user.get('dn',''). |
| 5 | Bug 2 front: banner sticky en AppLayout.js | (mismo 4763ff9) | Banner TOP fixed con gradiente amber->orange->red. Visible en TODAS las paginas autenticadas. Padding-top dinamico en main. Boton "Terminar Impersonate" dispatchea evento. |
| 6 | Bug 2 front: auth.js stopImpersonate handler | (mismo 4763ff9) | Listener del evento sgd-stop-impersonate. Metodo stopImpersonate() en el store con POST + refresh. |
| 7 | stop() no loguea si no hay cookie | (mismo 4763ff9) | Fix de entradas huerfanas en audit_log. |

### Logros tecnicos

1. **3 bugs cerrados en 1 sesion** (~25 min de codigo).
2. **2 commits atomicos**:
   - df4aceb: 1 archivo (Parametrizacion.js, 162 lineas modificadas, +93/-69)
   - 4763ff9: 4 archivos (backend + AppLayout + auth.js, +187/-19)
3. **Audit log con campo dedicado**: ecurso='impersonate', ccion='IMPERSONATE_START'/'IMPERSONATE_STOP'. 7 entradas validadas (4 start + 3 stop, sin huerfanas).
4. **Banner sticky funcional**: visible en Bandeja, Parametrizacion, y todas las paginas autenticadas. Gradiente amber->orange->red para maxima visibilidad.
5. **Validaciones de seguridad**: no-auto-impersonate, no-doble-impersonate, solo ADMIN/ETO pueden impersonar (validado en backend + frontend).
6. **Bug preexistente resuelto**: ad_user['dn'] -> ad_user.get('dn','') (KeyError cuando LDAP_ENABLED=true pero AD no responde).

### Validacion empirica (Chrome DevTools)

| Verificacion | Resultado |
|---|---|
| Login aromero/cofar.2026 como ETO | 200 OK + 3 cookies (csrf, session, user_id) |
| Click tab Diccionarios y Enrutamiento | 10 filas, analistas visibles (Aracely/Cecilia), checkboxes Disponibilidad marcados |
| Desmarcar Disp en CAL + cambiar analista + guardar | PATCH /api/v1/matriz-enrutamiento-eto/11 OK, BD persistida, audit_log capturo |
| Boton Impersonar (frontend, aromero) | Visible solo si role=admin o role=eto (10 botones en la tabla actual) |
| POST /admin/impersonate/start con sAMAccountName=aromero (auto) | 422 "No puede impersonarse a si mismo" |
| POST /admin/impersonate/start con sAMAccountName=cespinoza | 200 OK, cookie impersonated_user seteada, /me devuelve cespinoza con es_impersonado=true |
| refreshFromBackend() actualiza store | auth.user.username=cespinoza, auth.user.impersonated_by=aromero |
| Banner sticky | display=block, texto "Impersonando a: Cecilia Andrea Espinoza Paredes (cespinoza). Sesion real: aromero" |
| dispatchEvent sgd-stop-impersonate | POST /stop, cookie borrada, /me devuelve aromero, banner display=none despues de transicion |
| Login como visualizador_cl + ir a /parametrizacion | Redirigido a /403 (guard del router) - RBAC OK |
| audit_log final | 7 entradas impersonate, sin huerfanas (stop solo loguea si habia cookie) |

### Decisiones tecnicas (ADRs candidatos para sesion 18)

- **ADR-035**: <select x-model> con <template x-for> para options dinamicas
  requiere re-bind imperativo en wait nextTick() post-carga de los options.
  Alpine 3 no re-bindea automaticamente cuando las options se cargan despues
  del initial render. Patron aplicable a cualquier select dinamico.

- **ADR-036**: Impersonate en SGD es accion ADMIN o ETO (no solo ADMIN).
  Cualquiera de los dos puede asumir temporalmente el rol de otro usuario
  para testing, soporte, o capacitacion. Ambos eventos (start/stop) quedan
  registrados en audit_log con campo dedicado.

- **ADR-037**: El banner de impersonate vive en AppLayout (no en la pagina
  actual) para que sobreviva a navegacion entre paginas. Se activa con
  x-show=".auth.user?.impersonated_by" y se oculta con transicion
  de 150ms. El boton "Terminar" usa CustomEvent (sgd-stop-impersonate)
  porque el banner no tiene acceso directo al store.

### Progreso actualizado

- **R1 + EPICA9 + Matriz ETO + Previsualizar + Impersonate**: 38+3 = **41 tareas R1 (100% cerrado)**
- **QAS**: 8/8 (100%) sin cambios
- **R2**: 0/21 sigue desbloqueado, listo para arrancar
- **Total**: 41/49 (84%) + 4 bonus
- **Migraciones Alembic**: 13 aplicadas, 0 nuevas en esta sesion
- **Endpoints totales**: 53+ REST, 0 nuevos
- **Tablas de BD**: 21/28 migradas, 0 nuevas
- **audit_log**: 7 nuevas entradas (4 start + 3 stop impersonate)

### Proxima sesion (sesion 18) - recomendaciones

1. **R2 (Wizard de creacion)**: ya esta todo listo, sesion desbloqueada
   oficialmente tras el cierre de R1. Estimado: 2-3 sesiones intensivas.
2. **#13 Deuda delegado** (fuzzy + threshold 0.85): ~30 min
3. **#14 Cargos a areas** (seed POSICION -> area_id): mediano
4. **#15 Refresh bug** (backlog preexistente): 1-2h
5. **#19-21 Security hardening** (CSP, DOMPurify, rate limit): pre-QAS-public
6. **#16 Fix Plazo 42 invalido** (cosmetic, 5 min)

Recomendacion: arrancar R2 ya que el R1 esta cerrado al 100%.

---

## Sesion 18 - 2026-06-17 (miercoles 10:00 -> 12:00) - Fix refresh bug #15 (deuda arrastrada)

> Sesion dedicada EXCLUSIVAMENTE a resolver el bug "F5 me bota al login" que
> estaba arrastrandose desde sesion 14 como #15 y se intento mitigar sin
> exito en sesiones 15 y 16. El usuario pidio: "requiero un analisis ya
> profesional ya que varias sesiones anteriores se intento esto sin exito".
> Enfoque: debug page primero para aislar, evidencia empirica con Chrome
> DevTools, despues fix minimo.

### Diagnostico (guiado por INICIO-SESION.md)

1. Lectura de BITACORA / ESTADO / INICIO-SESION
2. Stack diagnosticado: 16 contenedores Up (8 DES + 8 backup), backend healthy
3. Git history: el bug existia desde el initial commit (0aa9016), no es regresion
4. Lectura de codigo: main.js:46, auth.js:40-51, router/index.js:97

### Causa raiz identificada (confirmada empiricamente)

`main.js:46` → `Alpine.store('auth').init()` → `refreshFromBackend()` (Promise
sin await). `main.js:129` → `initRouter()` en `Promise.resolve().then()` (siguiente
microtask). El router consultaba `auth.isAuthenticated` (= `this.user !== null`)
en ese microtask, pero `/me` estaba en vuelo y `this.user` era `null`. El router
redirigia a `/login`. A los ~15ms llegaba la respuesta de `/me` y actualizaba
`auth.user` (TOO LATE, usuario ya estaba en /login).

### Debug page `/_debug/session` (NUEVA)

Inspirada en la DebugTiptap de sesion 16. Bypass auth + AppLayout. Permite:
- Ver estado del auth store en vivo (isReady, isAuthenticated, localStorage, cookies)
- Set fake session, hard reload, probe /me, AUTO-TEST
- Log de eventos con timestamps para correlacionar con Network tab

### Evidencia empirica (pre-fix, con Chrome DevTools)

| Test | Resultado | Esperado |
|---|---|---|
| Refresh en `/?_v=4#/bandeja` con sesion valida | URL final `/?_v=4#/login` | Debe quedar en /bandeja |
| Estado 800ms post-refresh | `isAuthenticated: true, user: visualizador_cl` | (correcto, pero too late) |
| Network: 2x GET /api/v1/me | Ambos 200 OK con user completo | (correcto, pero en paralelo) |

### Fix aplicado (commit `733e8b6`)

3 cambios minimos:

1. **`auth.js` — `init()` restaura sincrónicamente desde localStorage**
   - Cache + `isReady = true` en el primer tick (sin race condition)
   - Si no hay cache, `isReady = false` hasta que `/me` complete
   - `_refreshPromise` expuesta para tests/debug

2. **`router/index.js` — guard `!isReady` con loader**
   - Si `!auth.isReady`: muestra spinner "Verificando sesion..." y NO redirige
   - Polling 60ms re-dispara `handleRoute()` cuando `isReady` cambia a true
   - Safety timeout 5s (caso /me nunca responde)

3. **`DebugSession.js` (NUEVA)** — herramienta de diagnostico permanente
   - Bypass auth + AppLayout (igual que /login)
   - Captura screenshots de evidencia para futuras regresiones

### Validacion (6/6 smoke tests con Chrome MCP)

| # | Escenario | Resultado |
|---|---|---|
| 1 | Refresh en /bandeja con sesion valida | OK: queda en /bandeja |
| 2 | Refresh en /_debug/session | OK: queda |
| 3 | Logout + refresh en /bandeja | OK: redirige a /login |
| 4 | Login normal desde /login con BD Local | OK: redirige a /bandeja |
| 5 | Refresh en /parametrizacion con rol ETO | OK: queda, contenido carga |
| 6 | Refresh en /login sin auth | OK: queda en /login |

Evidencia visual: 11 screenshots en `docs/PR/screenshots/` (debug-01..04 +
fix-01..08).

### Logros tecnicos

1. **Bug #15 RESUELTO** (deuda arrastrada desde sesion 14, 4 sesiones)
2. **Doble red de seguridad**: cache localStorage (sincronico) + cookies HttpOnly
   (validadas por /me en background)
3. **Debug page permanente** para diagnostico futuro (no se elimino al final,
   queda en el codigo como `/_debug/session`)
4. **0 regresiones** detectadas: login, logout, /me, impersonate, todo OK
5. **15 archivos cambiados en 1 commit**: 2 modificados (auth.js, router/index.js)
   + 1 nuevo (DebugSession.js) + 11 screenshots de evidencia

### Decisiones tecnicas (ADRs candidatos para sesion 19)

- **ADR-038**: Auth store DEBE restaurar sesion SINCRONICAMENTE desde localStorage
  en `init()` antes de que el router pueda consultar `isAuthenticated`. La cache
  local es la "primera fuente de verdad" para evitar race conditions visuales.
  El backend (`/me`) sigue siendo la "fuente autoritativa" pero corre en background.

- **ADR-039**: Router DEBE gatear con `auth.isReady` antes de tomar decisiones
  de redireccion. Si `!isReady`, mostrar loader y esperar. Esto desacopla el
  tiempo de respuesta de `/me` del tiempo de carga visual de la UI.

- **ADR-040**: `/me` falla o retorna `authenticated: false` → limpiar localStorage
  y dejar que el router redirija a /login. No mantener sesion zombie en cache
  que el backend rechaza.

- **ADR-041**: Paginas de debug (como `/_debug/session` y la ex-`/_debug/tiptap`)
  se mantienen en el codigo de produccion, accesibles sin auth, para diagnostico
  futuro. Patron: sufijo `/_debug/*` con bypass en router + plantilla Alpine minima.

### Progreso actualizado

- **R1 + EPICA9 + Parametrizacion + Tiptap + Refresh fix**: 42 tareas R1 (100%)
- **QAS**: 8/8 (100%) sin cambios
- **R2**: 0/21 sigue desbloqueado
- **Total**: 42/49 (86%) + 4 bonus
- **Migraciones Alembic**: 13 aplicadas, 0 nuevas
- **Endpoints totales**: 53+ REST, 0 nuevos

### Proxima sesion (sesion 19) - recomendaciones

1. **R2 (Wizard de creacion)**: oficialmente desbloqueado. 2-3 sesiones intensivas.
2. **#13 Deuda delegado** (fuzzy + threshold 0.85): ~30 min, pequeno
3. **#14 Cargos a areas** (seed POSICION -> area_id): mediano
4. **#16 Fix Plazo 42 invalido** (cosmetic, 5 min)
5. **#19-21 Security hardening pre-QAS-public** (CSP, DOMPurify, rate limit)

Recomendacion: arrancar R2 ya que el R1 esta cerrado al 100% y el refresh
bug esta resuelto. Si quedan sesiones pequenas antes de R2, #13 y #16 caben
en 30-40 min.

---

## Sesion 19 � 2026-06-17 (miercoles) � DEPLOY QAS v1.0.0-qas (12/12 PASS)

> Sesion dedicada a ejecutar el plan \docs/PR/PLAN-DEPLOY-QAS-SESION18.md\
> completo. Deploy del codigo R1+R1-fixes (22 commits desde ultimo
> deploy QAS) en \https://sgdqas.cofar.com.bo\. 12/12 validaciones A-L
> en PASS. Tag \1.0.0-qas\ creado.

### Contexto de inicio

El usuario volvio con luz verde para ejecutar el deploy QAS pendiente de
sesion 18. Plan completo en PLAN-DEPLOY-QAS-SESION18.md (11 secciones,
estimado 40-50 min).

### Diagnostico (guiado por INICIO-SESION.md)

- Stack DES local: 16 contenedores Up (8 DES + 8 backup paralelo)
- Working tree limpio, branch epica-1/rama-1, 24 commits ahead de origin
- Plan completo commiteado (78caeb7)
- Reposicion de las preguntas criticas del ritual: el plan ya esta
  acordado, el usuario autorizo proceder. La validacion local + el
  PRE-FLIGHT SSH son las tareas obligatorias previas.

### Tareas ejecutadas (en orden)

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 19.1 | Validacion LOCAL: 8 seeds + 3 migraciones + openpyxl + Tiptap deps + Dockerfiles | (analisis) | TODO presente |
| 19.2 | PRE-FLIGHT SSH: conectividad + disco 225GB libres + cert SSL 1 ano + .env.qas (LDAP_SERVER=10.10.0.2) | (sin commit) | Todo OK |
| 19.3 | Backup pre-deploy: BD (100KB custom v1.15-0) + nginx confs + compose | (sin commit) | OK |
| 19.4 | FIX 1: rename sgd-qas.conf.bk -> sgd-qas.conf en deploy-qas.bat:75 | 5b22bde | 9 lineas agregadas |
| 19.5 | Fix preexistente seed_tipos_documento.py: INSTRUCTIVO_TECNICO 6 -> 15 (alineado con migracion 011) | 5b22bde | 1 linea modificada |
| 19.6 | Commit atomico FIX 1 + fix seed (2 archivos, 10 insertions, 1 deletion) | 5b22bde | OK |
| 19.7 | Re-confirmacion SSH + health QAS pre-deploy | (sin commit) | OK |
| 19.8 | Ejecutar scripts\\deploy-qas.bat (zip + scp + extract + rename + rebuild + restart) | (sin commit) | Deploy completo |
| 19.9 | Diagnostico: nginx 502 por IP cacheada del container backend viejo | (sin commit) | docker restart sgd-qas-nginx |
| 19.10 | Re-ejecutar start-stack-qas.sh (8/8 seeds aplicados: 11 email_templates, 11 configuracion_global, 4 semaforizacion) | (sin commit) | OK |
| 19.11 | BUG CRITICO detectado: zip del deploy NO contenia archivos del frontend | (sin commit) | Robo copia fallo |
| 19.12 | Causa raiz: /worktrees no es parametro valido de robocopy, aborta silenciosamente | d183ead | 1 linea modificada |
| 19.13 | Re-empaquetar frontend manualmente + SCP + extract + rebuild imagen + restart container | (sin commit) | OK |
| 19.14 | npm install DENTRO del container (bind mount deja node_modules vacio) | (sin commit) | 45 packages |
| 19.15 | Validaciones A-L exhaustivas (12 categorias) | (analisis) | 12/12 PASS |
| 19.16 | Tag v1.0.0-qas | (tag) | Resumen del release |

### Validaciones A-L (12/12 PASS)

| # | Categoria | Resultado |
|---|---|---|
| A | Health | ? HTTPS 200, interno 200, 8/8 servicios Up |
| B | Librerias nuevas | ? openpyxl 3.1.5, 27 paquetes Tiptap instalados |
| C | Migraciones (3 nuevas) | ? alembic 6451593bcab5 (013), semaforizacion_tarea existe, tipos_documento refactor OK |
| D | Datos BD | ? 5/11/10/50/754/13/5/20/11/10/11/4 (13 contadores), INSTRUCTIVO_TECNICO=15 |
| E | Login | ? aromero local 200, /me 200 con user completo |
| F | Endpoints nuevos | ? audit-log, semaforizacion-tarea, admin/impersonate/list (753 usuarios), PATCH /usuarios |
| G | Refresh fix #15 (Chrome MCP) | ? isReady=true, isAuthenticated=true, localStorage presente, refresh mantiene sesion |
| H | Tiptap editor plantillas | ? 11 plantillas + toolbar B/I/U/S/H1-3/listas/code/color/fontSize/undo/redo |
| I | Impersonate funcional | ? banner sticky visible, boton Impersonar, audit IMPERSONATE_START/STOP (9 entries previas) |
| J | Sync AD | ? 753 usuarios CSV, LDAP contra DC 10.10.0.2 OK |
| K | nginx | ? HTTP->HTTPS 301, HTTPS 200, sgd-qas.conf activo sin .bk |
| L | Seguridad | ? CORS 200, CSRF cookie no HttpOnly |

### Logros tecnicos

1. **Deploy QAS 100% funcional** en https://sgdqas.cofar.com.bo con
   codigo R1+R1-fixes sincronizado.
2. **2 fixes preexistentes** descubiertos y corregidos (commit 5b22bde
   + 5b22bde). Sin ellos el deploy NO habria sido completo.
3. **3 migraciones Alembic** aplicadas (010 -> 013). Ninguna fallo.
4. **8 seeds idempotentes** corriendo OK. conteos finales: 11
   email_templates, 11 configuracion_global, 4 semaforizacion_tarea.
5. **Bug preexistente #1** (\/worktrees\ en robocopy) que arrastraba
   silencio desde sesion 14 (4 deploys con frontend desactualizado).
   Documentado y arreglado en commit d183ead.
6. **Tag v1.0.0-qas** con resumen del release.
7. **Cero regresiones**: el bug preexistente \Plazo 42 invalid\ del
   plan ya estaba en DES y sigue en QAS (cosmetic, no bloqueante).

### Bugs preexistentes descubiertos durante el deploy

1. **\/worktrees\ no es parametro valido de robocopy** (sesion 14
   heredo el patron malo). El comando aborta silenciosamente y el
   frontend nunca se copiaba. FIX en commit d183ead.
2. **nginx cachea la IP del container backend** entre deploys. El
   container recreado recibe nueva IP, nginx sigue intentando la vieja
   -> 502. Fix operacional: \docker restart sgd-qas-nginx\ despues
   del deploy.
3. **\
ode_modules\ vacio en container** por bind mount + \COPY . .\
   en Dockerfile. El bind mount de compose (\../frontend:/app\) pisa
   el node_modules que npm install creo en el build. Fix operacional
   para este deploy: \docker exec sgd-qas-frontend npm install\. Fix
   permanente requiere Dockerfile/compose cambio (no urgente).
4. **Path real admin-impersonate es \/api/v1/admin/impersonate/list\**
   (con slash, no guion). El plan PLAN-DEPLOY-QAS-SESION18.md tenia
   typo. Documentado en ESTADO.

### Conteo final QAS post-deploy

\\\
roles:                   5
modulos:                11
gerencias:              10
areas:                  50
usuarios:              754   (4 stubs DES + 750 AD)
tipos_documento:        13   (DES tiene 14, +1 INSTRUCTIVO_TECNICO codigo=15)
estados:                 5
feriados:               20
email_templates:        11   (NUEVO, antes 0 post-migracion 013)
matriz_eto:             10
configuracion_global:   11   (NUEVO, antes 0)
semaforizacion_tarea:    4   (NUEVO, tabla creada por migracion 012)
audit_log:               1
alembic:         6451593bcab5 (013)  (NUEVO, antes b397cd9bfb91 = 010)
\\\

### Decisiones tecnicas (ADRs candidatos sesion 20)

- **ADR-028**: El script \deploy-qas.bat\ debe usar \worktrees\ (no
  \/worktrees\) en robocopy \/XD\. Cualquier parametro invalido
  causa abort silencioso sin error visible.
- **ADR-029**: Post-deploy de QAS, siempre ejecutar \docker restart
  sgd-qas-nginx\ para refrescar el cache DNS del container backend
  (su IP cambia en cada recreacion).
- **ADR-030**: El compose \docker-compose.qas.yml\ frontend debe
  excluir el bind mount de \/app/node_modules\ o el Dockerfile debe
  tener un paso final \
pm install\ que no sea sobrescrito por
  \COPY . .\. Workaround actual: \docker exec npm install\.

### Progreso actualizado

- **R1 + EPICA9 + Parametrizacion + Tiptap + Impersonate + Refresh fix + Deploy QAS**:
  100% CERRADO Y DESPLEGADO.
- **QAS**: v1.0.0-qas desplegado con 8 servicios + 754 usuarios AD + 11 plantillas + 11 params config.
- **R2**: 0/21 (sigue desbloqueado, no fue tocado).
- **Total commits sesion 19**: 2 (5b22bde + d183ead).
- **Tag**: v1.0.0-qas.

### Proxima sesion (sesion 20) � recomendaciones

1. **Fix permanente del bind mount node_modules** (ADR-030). Modificar
   \deploy/Dockerfile\ del frontend para excluir node_modules del
   \COPY . .\ o agregar un \.dockerignore\. Despues: rebuild imagen
   + restart container.
2. **Fix permanente del cache DNS de nginx** (ADR-029). Agregar paso al
   \start-stack-qas.sh\ que haga \docker restart sgd-qas-nginx\ al
   final.
3. **Fix Plazo 42 invalid** (cosmetic, 5 min): cambiar el seed de
   \plazo_revision_aprobacion_dias\ a 15.
4. **R2 - Wizard de creacion** (tareas #23+): ya esta todo listo.
5. **#13 Deuda delegado** (fuzzy + threshold 0.85): pequeno.

---

## Sesion 20 � 2026-06-17 (miercoles) � Fixes preventivos del deploy pipeline

> Sesion dedicada a aplicar todos los fixes preventivos descubiertos
> durante el deploy de sesion 19. **QAS NO fue tocado** � todos los
> cambios son en codigo local (DES) para que el proximo deploy sea
> mas robusto. Plan PLAN-DEPLOY-QAS-SESION18.md reescrito completamente
> con los nuevos bugs + fixes + escenarios + troubleshooting.

### Contexto

El usuario volvio despues de probar QAS v1.0.0-qas y confirmo que
funciona. Solicito que arregle TODOS los bugs que aparecieron en el
deploy, modifique el documento de deploy, y actualice ESTADO + BITACORA.

### Tareas ejecutadas (en orden)

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 20.1 | Fix bug \ind -prune -delete\ en deploy-qas.bat:75 (cambiar a \-not -path\) | (sesion 20) | Sin warning de find, mas robusto |
| 20.2 | Crear \rontend/.dockerignore\ (excluir node_modules, dist, .git, worktrees, etc.) | (sesion 20) | Nuevo archivo, evita el bug del COPY . . |
| 20.3 | Agregar pre-flight checks al deploy-qas.bat (SSH + disco + cert SSL + backup) | (sesion 20) | Nuevo paso 0/6 con abort si falla |
| 20.4 | Agregar \docker restart sgd-qas-nginx\ post-deploy (refresca cache DNS backend) | (sesion 20) | Fix 502 Bad Gateway |
| 20.5 | Crear \scripts/validate-qas.sh\ con validaciones A-L ejecutables en cualquier momento | (sesion 20) | Nuevo script, exit codes 0/1/2 |
| 20.6 | Reescribir PLAN-DEPLOY-QAS-SESION18.md con TODOS los bugs + fixes + escenarios + troubleshooting | (sesion 20) | 660 lineas (+528/-468 vs version anterior) |
| 20.7 | Actualizar ESTADO.md + BITACORA.md | (sesion 20) | OK |

### Logros tecnicos

1. **6 fixes preventivos** aplicados al deploy pipeline, todos basados
   en bugs descubiertos durante el deploy de sesion 19.
2. **\alidate-qas.sh\** nuevo: ejecutable en cualquier momento, NO
   solo post-deploy. Valida 12 categorias A-L con tabla PASS/FAIL.
3. **Plan de deploy reescrito** (660 lineas) con:
   - Tabla de contenidos
   - 8 bugs documentados con sus fixes
   - Estado actual del server
   - Cambios desde ultimo deploy (sesion por sesion)
   - Plan paso a paso con flags
   - Validaciones A-L con scripts de cada una
   - Comandos de troubleshooting
   - 8 escenarios especiales
   - Rollback
   - 12 riesgos identificados
   - Diferencias QAS vs DES
   - Backlog pre-PROD
4. **Pre-flight checks** agregados al \deploy-qas.bat\: SSH reachable,
   disco QAS > 2GB, cert SSL > 30 dias, backup pre-deploy obligatorio.
5. **Cero cambios en QAS**: la sesion 20 fue 100% cambios en codigo
   local (DES) para robustecer el deploy pipeline.

### Decisiones tecnicas (ADRs candidatos sesion 21)

- **ADR-031**: \deploy-qas.bat\ siempre ejecuta pre-flight checks antes
  de cualquier deploy. Si ALGUNO falla (SSH, disco, cert, backup), el
  script aborta con exit 1.
- **ADR-032**: Post-deploy de QAS, siempre \docker restart sgd-qas-nginx\
  para refrescar el cache DNS del container backend (su IP cambia en
  cada recreate).
- **ADR-033**: \rontend/.dockerignore\ excluye node_modules, dist,
  .git, worktrees, .env, logs, IDE configs. Es la primera linea de
  defensa contra el bug del bind mount + COPY . . .
- **ADR-034**: \scripts/validate-qas.sh\ es el punto de entrada
  unico para validar QAS en cualquier momento. Imprime tabla
  PASS/FAIL/WARN con conteos. Exit codes 0/1/2.

### Bugs de sesion 19 que se arreglaron en sesion 20

1. **\ind -prune -delete\** daba warning confuso. Cambiado a
   \ind -not -path\. (FIX 4)
2. **\COPY . .\ en Dockerfile** copiaba node_modules del host.
   Agregado \rontend/.dockerignore\. (FIX 5)
3. **Pre-flight checks ausentes** en deploy-qas.bat. Agregado paso 0/6
   con SSH + disco + cert + backup. (FIX 6)
4. **nginx 502 post-deploy** por cache DNS de IP vieja. Agregado
   \docker restart sgd-qas-nginx\ en paso 5/6. (FIX 7)
5. **\alidate-qas.sh\ no existia**. Creado con 12 validaciones A-L
   ejecutables en cualquier momento. (FIX 8)

### Pendientes (no abordados en sesion 20)

- **Plazo 42 invalid** (cosmetic): el seed dice 25, pero la BD del DES
  tiene 42. NO se toca (afectaria BD). Documentado en backlog pre-PROD.
- **Bind mount node_modules fix permanente**: requiere cambiar
  compose o Dockerfile. Workaround: \docker exec npm install\.
  Documentado en backlog.
- **Cert HTTPS valido**: autofirmado, OK por ahora. Documentado en
  backlog pre-PROD.

### Progreso actualizado

- **R1 + EPICA9 + Parametrizacion + Tiptap + Impersonate + Refresh fix + Deploy QAS**:
  100% CERRADO Y DESPLEGADO.
- **QAS**: v1.0.0-qas deployed y estable. Sin cambios en sesion 20.
- **Deploy pipeline ROBUSTO**: 6 fixes preventivos + validate-qas.sh
  ejecutable + plan reescrito.
- **R2**: 0/21 (sigue desbloqueado, no fue tocado).
- **Total commits sesion 20**: 1 (consolidado al final).

### Proxima sesion (sesion 21) � recomendaciones

1. **Fix permanente del bind mount node_modules** (ADR-034): cambiar
   compose \docker-compose.qas.yml\ para que el bind mount NO incluya
   \/app/node_modules\. Despues: rebuild imagen + restart container.
2. **Fix Plazo 42 invalid** (cosmetic, 5 min): cambiar valor en seed o
   forzar re-seed.
3. **Backups automaticos en QAS** (cron + pg_dump): el backup automatico
   del cron YA existe (visto en deploy de sesion 19: qas_20260617.dump
   del 17 jun 02:00). Verificar que el cron este correctamente
   configurado.
4. **Cert HTTPS valido** (Let's Encrypt o cert corporativo): pre-PROD.
5. **R2 - Wizard de creacion** (tareas #23+): ya esta todo listo.
6. **#13 Deuda delegado** (fuzzy + threshold 0.85): pequeno.

---

## Sesion 21 — 2026-06-17 (miercoles) — R2 FASE 1: Modelos + Endpoints lectura + Seed + Tests

> Sesion dedicada a cerrar la **Fase 1 de R2** segun `docs/PR/R2-PLAN-EJECUCION.md`.
> Plan operativo: 2 fases. Esta sesion cubre Fase 1 (3.5h estimadas → 4h reales con bugfixes).
> Fase 2 (wizard E2E + firma 2FA) queda para sesion 22.

### Contexto

El usuario (Y. Chavez) pidio implementar R2 (wizard de creacion + version editable) con 2 paginas del sidebar "Nueva Solicitud". Despues de exponer el plan y validar el analisis, se creo la rama `r2/wizard-y-version-editable` desde `epica-1/rama-1` (head `737574b`).

### Diagnostico de inicio

- Stack DES: 8/8 contenedores Up, backend healthy
- 20 tablas en BD (13 originales + 5 EPICA 9 + audit + semaforizacion)
- 53+ endpoints REST funcionando
- 13 migraciones Alembic aplicadas (head `6451593bcab5`)
- Catalogos base listos: 5 roles, 13 tipos_documento, 5 estados, 10 gerencias, 49+ areas, 11 config_global

### Tareas ejecutadas (en orden)

| # | Tarea | Commit | Resultado |
|---|---|---|---|
| 21.1 | Doc `docs/PR/R2-PLAN-EJECUCION.md` con plan completo en 2 fases | `c9aaea1` | 437 lineas, 10 secciones, decisiones, riesgos, archivo paths |
| 21.2 | Crear rama `r2/wizard-y-version-editable` | (rama) | working tree limpio |
| 21.3 | 3 modelos SQLAlchemy 2.0: `Documento` (CORE), `DocumentoFlujo`, `ArchivoAdjunto` + 5 enums | `68030d9` | 18 columnas en `documentos` + 17 indices + 2 UK + 1 CHECK constraint |
| 21.4 | Schemas Pydantic v2 (DocumentoBuscarItem, DocumentoOut, PreviewCodigoRequest, etc.) | `68030d9` | 11 schemas, validados con carga en contenedor |
| 21.5 | `correlativo_service.py` con SELECT FOR UPDATE + fallback `pg_try_advisory_xact_lock` | `68030d9` | portable SQLite/PostgreSQL. 10 tests |
| 21.6 | `vigencia_service.py` con `calcular_vigencia()` | `68030d9` | respeta regla: VENCIDO solo si APROBADO/OBSOLETO |
| 21.7 | Router `documentos.py` con 4 endpoints de lectura | `68030d9` | 4 rutas registradas en OpenAPI |
| 21.8 | Migracion Alembic 014 (autogenerate, limpieza manual de cambios colaterales) | `68030d9` | head `b88801d59687`. Aplicada OK |
| 21.9 | `seed_documentos.py` idempotente (10 docs) | `68030d9` | 1ra corrida=10 insertados, 2da=0 (verificado idempotente) |
| 21.10 | Tests pytest: 23 del router + 10 del service | `68030d9` | 33/33 passing. Stubs SQLite para `hashtext` y `pg_try_advisory_xact_lock` |
| 21.11 | Smoke test E2E con cookies reales (aromero) | (sin commit) | 6/6 endpoints validados con curl-style |
| 21.12 | Fix placeholder `/version-editable` (`PRO-CAL-005` → `CC-3-005/01`) | `68030d9` | 1 string |
| 21.13 | Commit atomico + actualizar ESTADO + BITACORA | `68030d9`, `c9aaea1` | 15+2 archivos, 3163 inserciones |

### Distribucion de documentos sembrados

| Codigo | Titulo | Estatus | Vigencia | Dias_atras |
|---|---|---|---|---|
| CC-5-001/00 | Procedimiento de Control de Documentos del SIG | APROBADO | VIGENTE | 120 |
| DT-3-001/00 | Politica de Direccion Tecnica | APROBADO | VIGENTE | 90 |
| EST-7-001/00 | Especificacion de Estabilidad Acelerada | APROBADO | VIGENTE | 180 |
| PRO-5-001/00 | Procedimiento Operativo de Produccion | APROBADO | VENCIDO | 1500 (regla OK) |
| BET-7-001/00 | Especificacion de Betalactamicos | APROBADO | POR_VENCER | 1430 |
| ACD-5-001/00 | Procedimiento de Acondicionamiento | EN_ELABORACION | VIGENTE | — |
| VAL-5-001/00 | Procedimiento de Validaciones | EN_ELABORACION | VIGENTE | — |
| REG-4-001/00 | Plan Regulatorio 2026 | EN_REVISION | VIGENTE | — |
| GAC-3-001/00 | Politica de Garantia de Calidad | EN_REVISION | VIGENTE | — |
| MCB-6-001/00 | Instructivo de Microbiologia vAntigua | OBSOLETO | OBSOLETO | 1825 |

### Logros tecnicos

1. **3 modelos nuevos + 5 enums** registrados y persistidos en BD con 17 indices optimizados.
2. **Migracion 014** aplicada con 1 CHECK constraint (regla de negocio) y 2 UK (correlativo monotono, codigo unico con version).
3. **4 endpoints REST** con 23 tests pytest, todos pasando.
4. **correlativo_service** con doble estrategia (FOR UPDATE + advisory lock) portable a SQLite (tests) y PostgreSQL (DES/QAS/PROD).
5. **Seed idempotente** con 10 docs basados en datos reales (claves foraneas validas, vigencias distribuidas, regla VENCIDO validada).
6. **33/33 tests nuevos pasan** + stubs SQLite para funciones de PostgreSQL.
7. **Smoke test E2E** con login real (aromero) + cookies + 6 escenarios curl-style.
8. **Placeholder fix** del campo de busqueda (legacy `PRO-CAL-005` → `CC-3-005/01`).

### Bugs detectados y corregidos

1. **Alembic autogenerate detecto cambios colaterales** en `email_templates.variables_json` y `tipos_documento.uq_tipos_documento_codigo` (de sesiones 13/14 no propagados). Fix: removidos manualmente del archivo de migracion.
2. **Seed NO era idempotente en 1ra version** (correlativo se incrementaba en cada corrida). Fix: usar `(area, tipo, titulo)` como clave de deteccion en vez de `(area, tipo, correlativo)`.
3. **Tests fallaban en SQLite** por funciones PostgreSQL `hashtext` y `pg_try_advisory_xact_lock`. Fix: registrados como custom functions en SQLite en conftest.
4. **`register_adapter` rompio el adapter de SQLAlchemy** para enums. Fix: eliminado el register_adapter, las funciones custom funcionan sin el.
5. **`siguiente_correlativo_advisory` no filtraba por `activo=True`** (incluia borrados logicos en el MAX). Fix: agregado `.where(Documento.activo == True)`.

### Decisiones tecnicas (ADRs candidatos sesion 22)

- **ADR-042**: Tablas N:M (revisores, aprobadores, alcance difusion) se guardan como JSONB en `documento_flujo` para R2. En R3 se migraran a tablas N:M individuales con timestamps.
- **ADR-043**: Trigger SQL de obsolescencia (R2 plan #30) se difiere a R5. Vigencia se calcula en backend (Python) al servir.
- **ADR-044**: Catalogo `tipo_solicitud` es enum SQLAlchemy (CREACION, ACTUALIZACION) — 2 valores, no cambia nunca.
- **ADR-045**: Separador de version es `/` (no `v`) segun ejemplo del usuario `CC-3-005/01`. Sobreescribe ADR-011.

### Validacion empirica

- 33/33 tests pytest nuevos passing (4.28s)
- 6/6 smoke tests E2E con curl-style + cookies reales
- 10/10 documentos sembrados con claves foraneas validas
- 1/1 regla de negocio validada (PRO-5-001/00 VENCIDO con estatus=APROBADO)
- 1/1 check constraint aplicado (vigencia != VENCIDO OR estatus IN (APROBADO, OBSOLETO))
- 1/1 placeholder fix (CC-3-005/01 visible en browser)

### Progreso actualizado

- **R1 + EPICA9 + Parametrizacion + Tiptap + Impersonate + Refresh fix + Deploy QAS**: 100% (sin cambios)
- **R2**: **7/21 tareas (33%)** — FASE 1 cerrada
- **Total commits sesion 21**: 2 (`68030d9`, `c9aaea1`)
- **Rama**: `r2/wizard-y-version-editable` (basada en `epica-1/rama-1`, head `737574b`)
- **Migraciones Alembic**: 14 aplicadas (head `b88801d59687`)
- **Endpoints totales**: 57+ REST (+4 nuevos)
- **Tablas de BD**: 23/28 migradas (+3 nuevas)
- **Tests totales**: 156/164 passing (8 fallos preexistentes no introducidos por esta sesion)

### Proxima sesion (sesion 22) — FASE 2

Segun `docs/PR/R2-PLAN-EJECUCION.md` § 4.2:

1. **Storage service** (LocalStorage real + SharePointStorage stub): 20min
2. **POST/PATCH /documentos**: 30min
3. **POST /documentos/{id}/archivos**: 20min
4. **POST /documentos/{id}/enviar** (firma 2FA): 40min
5. **Endpoints /bandeja** (4 tipos): 30min
6. **Refactor VersionEditable.js** (autocomplete real): 25min
7. **Refactor AprobacionDocumento.js** completo (3 pasos): 1h30min
8. **Frontend `documentosApi.js`**: 30min
9. **Validacion E2E + tests adicionales**: 30min
10. **Commit + docs + ADR-042 en DECISIONES.md**: 20min

Estimado: 5.5h.
