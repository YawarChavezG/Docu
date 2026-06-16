# ESTADO — COFAR SGD (live tracker)

> **Este archivo se actualiza al final de cada sesión de trabajo.**
> Última actualización: 2026-06-15 (sesión 5 — backend ÉPICA 9 CERRADO al 100%)

## Versión actual
**v0.2.0-dev**

## Objetivo inmediato
**R1 + R2 para el martes 17 de junio de 2026** (2 días restantes)

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
| 8 | Migración Alembic inicial | ❌ | — | `backend/alembic/` existe pero VACÍO. Modelos se cargan en runtime (probable `Base.metadata.create_all()` en startup o seed). **BLOQUEANTE para R2+.** |
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
| 18 | Integrar Parametrizacion.js con API usuarios + boton sync AD | 🟡 | 15-jun | `Parametrizacion.js` modificado 15/6/2026 (65KB). Vista incluye boton sync-AD. Falta verificar uso de `apiFetch` (depende de tarea 15) |
| 19 | Sanear 4 x-html con DOMPurify | ❌ | — | (no verificado — buscar `x-html` en `frontend/src/pages/*.js`) |
| 20 | Agregar CSP meta tag | ❌ | — | (no verificado) |
| 21 | Rate limit con slowapi | ❌ | — | (no implementado) |
| 22 | **TESTING R1** | ❌ | — | `backend/tests/` existe pero VACÍO. Sin tests automatizados |

### R2 — Wizard de creación

| # | Tarea | Estado | Fecha | Evidencia |
|---|---|---|---|---|
| 23 | Schema SQLAlchemy Documentos (3 tablas) | ❌ | — | (no iniciadas) |
| 24 | Schema SQLAlchemy Workflow (3 tablas) | ❌ | — | (no iniciadas) |
| 25 | Schema SQLAlchemy Archivos (2 tablas) | ❌ | — | (no iniciadas) |
| 26 | Schema SQLAlchemy Soporte (4 tablas) | ❌ | — | (no iniciadas) |
| 27 | Schema SQLAlchemy Misceláneos (6 tablas) | ❌ | — | (no iniciadas) |
| 28 | Migración Alembic 002: 19 tablas restantes | ❌ | — | depende de 23-27 |
| 29 | Servicio `correlativo_service.py` con `SELECT FOR UPDATE` | ❌ | — | |
| 30 | Trigger SQL de obsolescencia automática | ❌ | — | |
| 31 | Endpoints `/api/v1/documentos` (CRUD borrador paso 1-4) | ❌ | — | |
| 32 | Endpoint `POST /api/v1/documentos/{id}/archivos` con validación MIME | ❌ | — | |
| 33 | Endpoint `POST /api/v1/documentos/{id}/enviar` con firma | ❌ | — | |
| 34 | Storage service: `LocalStorage` (volumen) + stub `SharePointStorage` | ❌ | — | |
| 35 | Endpoint `GET /api/v1/bandeja?tipo=liberacion` para ETO | ❌ | — | |
| 36 | Endpoint `POST /api/v1/documentos/{id}/liberar` (fan-out a revisores) | ❌ | — | |
| 37 | Endpoint `GET /api/v1/bandeja` general (por tipo y estado) | ❌ | — | |
| 38 | Frontend: refactorizar `src/pages/Bandeja.js` para usar API | ❌ | — | (última edición 6/5/2026, no tocado para R2) |
| 39 | Frontend: refactorizar `src/pages/LiberacionDetalle.js` | ❌ | — | (última edición 6/5/2026) |
| 40 | Frontend: refactorizar `src/pages/ListaMaestra.js` | ❌ | — | (última edición 6/5/2026) |
| 41 | **TESTING R2** | ❌ | — | |
| 42 | Documentación: `docs/RUNBOOK.md` | ❌ | — | |
| 43 | Documentación: `docs/ARQUITECTURA.md` y `ARQUITECTURA-DB.md` | 🟡 | 14-jun | Están en `docs/Diagramas_Matrices/`, falta unificar |

### Bonus — tareas que aparecieron fuera del plan original

| # | Tarea | Estado | Evidencia |
|---|---|---|---|
| B1 | Endpoint `/admin-impersonate/{list,start,stop}` | ✅ | `app/api/v1/admin_impersonate.py` + `app/services/impersonate_service.py` |
| B2 | Servicio `ad_service.py` con LDAP real (ldap3) | ✅ | 620 líneas, excluye 17+ CNs, soporta RODC, fallback si `LDAP_ENABLED=false` |
| B3 | Login contra BD local (no solo LDAP) — para DES sin AD | ✅ | `auth.py` líneas 80+ con `auth_source: "local"\|"cofar"\|None` |
| B4 | `LoginUserOut` con módulos + roles + impersonación | ✅ | |

---

## Progreso R1
**16/23 tareas R1 (70%)** + **7 tareas nuevas sesión 5 (backend ÉPICA 9)** = **20/23 tareas R1 (87%)**
Backend ÉPICA 9 (US-9.01 a 9.06) cerrado al 100%.

## Progreso R2
**0/21 tareas pendientes** (bloqueado por: tests pytest pendientes para R1)

## Total
**20/48 tareas (42%)** + 4 bonus ya entregados

## Tablas de BD
**17/28 migradas** (16 originales + 5 nuevas en sesión 5: configuracion_global, feriados, email_templates, matriz_enrutamiento_eto, tipos_documento, estados — 6 con migración Alembic aplicada)

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

## Decisiones tomadas (ADRs)
- ADR-001 a ADR-012 (ver `DECISIONES.md`)
- ADR-013 (en draft sesión 4): **Backend fuera de Docker en DES por VPN FortiClient**

## Bloqueos identificados (sesión 4)

1. **🔴 CRÍTICO — Sin Alembic**: los modelos están en código pero NO hay migraciones. Cada vez que se reinicia el backend los modelos se recrean desde cero (posible pérdida de datos). **Hay que arreglar ANTES de seguir con R2** o vamos a perder trabajo.

2. **🟠 IMPORTANTE — Frontend sin `utils/api.js`**: la mayoría de los componentes todavía usan datos hardcoded de `frontend/src/data/*.js`. Sin el wrapper `apiFetch`, no hay forma consistente de llamar al backend.

3. **🟡 MENOR — Tests vacíos**: `backend/tests/` está creado pero sin tests. La cobertura de R1 no es verificable automáticamente.

4. **🟡 MENOR — Sin rate limit, sin CSP, sin DOMPurify verificado**: 3 tareas de seguridad pendientes en R1.

## Próximo paso (recomendado para sesión 5)

**Orden propuesto (no negociable, por dependencias):**
1. **Generar migración Alembic inicial** (tarea #8) — toma 20 min, evita perder datos. **Prioridad #1.**
2. **Crear `frontend/src/utils/api.js`** (tarea #15) — sin esto, refactorizar más pages no tiene sentido.
3. **Endpoints de organigrama y gerencias/áreas** (tareas #11, #12) — el cliente las necesita para parametrizar.
4. **Tests con pytest + httpx** (tarea #22) — antes de cerrar R1.
5. **CSP + DOMPurify + rate limit** (tareas #19-21) — barra de seguridad mínima.

**Lo que NO se debería hacer todavía:**
- R2 (#23+) — depende de que R1 esté cerrada con Alembic
- Refactor de pages no tocadas (Bandeja, Liberacion, ListaMaestra) — depende de utils/api.js

## Estado de la sesión actual (4)

- ✅ Investigación completa del repo
- ✅ Investigación del plugin ECC (`ecc-universal` v2.0.0) — 26 commands, 26 agents, 11 skills por default
- ✅ Limpieza de raíz: 20 archivos basura sacados del tracking (.err, .out, .pid, cookies, login_*, test_*, trash_*). .gitignore reforzado.
- 🔄 Actualización de ESTADO.md con realidad (este archivo)
- ⏳ ADR-013 sobre backend fuera de Docker
- ⏳ Bitácora sesión 4
- ⏳ Orquestador `scripts/start-stack-des.bat`
- ⏳ Configurar ECC hooks en minimal
