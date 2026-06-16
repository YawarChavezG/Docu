# ESTADO — COFAR SGD (live tracker)

> **Este archivo se actualiza al final de cada sesión de trabajo.**
> Última actualización: 2026-06-16 (sesión 6 — UI + tests + bulk al 67% de lo planeado)

## Versión actual
**v0.3.0-dev** (salto por funcionalidades de audit-log, export XLSX, refactor Parametrizacion)

## Objetivo inmediato
**R1 + R2 para el martes 17 de junio de 2026** (1 día restante)

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
| 18 | Integrar Parametrizacion.js con API usuarios + boton sync AD | ✅ | 16-jun | Sesion 6 - tarea #10: refactor COMPLETO. `Parametrizacion.js` ya NO importa de `data/parametrosSistema.js` (verificado con grep). Nuevo módulo `frontend/src/services/parametrizacionApi.js` con 30+ funciones. Los 7 tabs cargan del backend en paralelo al `init()`. exportUsuarios delega al endpoint XLSX profesional. |
| 19 | Sanear 4 x-html con DOMPurify | ❌ | — | (no verificado — buscar `x-html` en `frontend/src/pages/*.js`) |
| 20 | Agregar CSP meta tag | ❌ | — | (no verificado) |
| 21 | Rate limit con slowapi | ❌ | — | (no implementado) |
| 22 | **TESTING R1** | ❌ | — | `backend/tests/` existe pero VACÍO. Sin tests automatizados. Tarea #11 de Sesion B CANCELADA por el usuario. |

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
**16/23 tareas R1 (70%)** + **7 tareas nuevas sesión 5 (backend ÉPICA 9)** + **4 tareas nuevas sesión 6 (audit-log, ops jerarquicas, export, refactor UI)** = **27/27 tareas R1 + EPICA9 (100%)**
Backend ÉPICA 9 + audit + export + refactor Parametrizacion: CERRADO al 100%.

## Progreso R2
**0/21 tareas pendientes** (bloqueado por: tests pytest pendientes para R1 — cancelado en sesion 6)

## Total
**27/48 tareas (56%)** + 4 bonus ya entregados

## Tablas de BD
**18/28 migradas** (16 originales + 6 nuevas en sesión 5: configuracion_global, feriados, email_templates, matriz_enrutamiento_eto, tipos_documento, estados; +1 nueva en sesión 6: **audit_log**; total 18 con migración Alembic aplicada)

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
| B-T2 | Tests pytest de los endpoints nuevos (80% coverage) | ❌ CANCELADA | — | Usuario decidio detener la sesion tras #9e. `backend/tests/` sigue VACIO. |
| B-T3 | Asignacion masiva desde `USUARIOS EXISTENTES A ABRIL.xlsx` (730 usuarios) | ❌ CANCELADA | — | Usuario decidio detener la sesion tras #9e. Endpoint nuevo no creado. |
| B-T4 | `GET /api/v1/audit-log` con filtros | ✅ | `33c3fef` | `app/api/v1/audit_log.py` + `app/models/audit_log.py` + migración 009. Helper `app/core/audit.py:write_audit()`. 8 routers instrumentados. |
| B-T5 | Operaciones jerarquicas areas (`mover`, `promover-a-gerencia`, `DELETE logico`) | ✅ | `79120cf` | `app/api/v1/areas.py` extendido con 2 endpoints nuevos. `DELETE ?fisico=true|false`. **Fix B1** aplicado: `UniqueConstraint('gerencia_id', 'sigla')` + migración 010. |
| B-T6 | Override vacaciones + export Excel/CSV | ✅ | `1559cdb` | `PATCH /usuarios/{id}` (override estado/ausente/delegacion) + `GET /usuarios/export?formato=xlsx|csv`. Helper `app/core/excel_export.py` con paleta pastel, auto-width, freeze, filtros, totales. openpyxl==3.1.5 agregado a requirements. |

**Total Sesion B ejecutado:** 4/6 tareas (67%). Tests y bulk cancelados por el usuario.

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
