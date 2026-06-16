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

