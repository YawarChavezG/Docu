# ESTADO — COFAR SGD (live tracker)

> **Este archivo se actualiza al final de cada sesión de trabajo.**
> Última actualización: 2026-06-14 19:39 (sesión inicial)

## Versión actual
**v0.1.0-dev**

## Objetivo inmediato
**R1 + R2 para el martes 17 de junio de 2026**

---

## Tareas (copia de PLAN-EJECUCION.md, actualizada en vivo)

| # | Tarea | Estado | Fecha | Notas |
|---|---|---|---|---|
| 0 | Validar entorno | ✅ | 14-jun | Docker 28.5.2, Node 22.19, Python 3.12, Git 2.51 |
| 1 | Crear estructura monorepo | ✅ | 14-jun | Carpetas creadas en C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES |
| 2 | Crear docker-compose.yml + Dockerfiles | ✅ | 14-jun | 6 servicios: postgres, redis, mailhog, backend, celery-worker, celery-beat, frontend, nginx |
| 3 | Crear requirements + scripts de init | ✅ | 14-jun | Versiones validadas contra PyPI/npm |
| 4 | Crear backend/app/main.py + health + auth stub | ✅ | 14-jun | FastAPI 0.137, health + login stub con 4 usuarios dev |
| 5 | Crear .env raíz + .env.example | ✅ | 14-jun | 30+ variables, .gitignored |
| 6 | Levantar la stack y validar docker compose up | ✅ | 14-jun | Stack completa: 9 contenedores Up/healthy, login funciona via Nginx, login via Vite funciona, health OK, MailHog OK. Puertos cambiados: 15432→25432, 16379→26379. |
| 7 | **Schema SQLAlchemy de Organización (11 tablas: gerencias, areas, usuarios, roles, usuario_roles, modulos, usuario_modulos, delegaciones, ausencias, firmas_digitales, log_sincronizacion_ad)** | ⏳ **SIGUIENTE** | — | Sembrar 5 roles, 10 módulos, 8-10 gerencias, ~25 áreas con sigla. Nomenclatura código: sigla_area-codigo_tipo-correlativo. Credenciales AD en .env. |
| 8 | Migración Alembic inicial | pendiente | — | |
| 9 | Endpoints /auth/login con stub de usuarios + verificación 2FA | pendiente | — | |
| 10 | Endpoints /usuarios (CRUD) + /usuarios/{id}/modulos | pendiente | — | |
| 11 | Endpoints /organigrama | pendiente | — | |
| 12 | Endpoints /gerencias + /areas (CRUD) | pendiente | — | |
| 13 | Endpoints /usuarios/{id}/delegado + /ausencia | pendiente | — | |
| 14 | Endpoints POST /admin/sync-ad (manual) + job 00:05 | pendiente | — | |
| 15 | Endpoints /auth/verify-password (firma digital) | pendiente | — | |
| 16 | seed_data.py con todos los catalogos (roles, modulos, gerencias, areas, tipos_documento, plantillas, feriados, matriz_enrutamiento_eto) | pendiente | — | |
| 17 | Frontend src/utils/api.js con apiFetch | pendiente | — | |
| 18 | Refactorizar auth.js para API real | pendiente | — | |
| 19 | Refactorizar Login.js para API real | pendiente | — | |
| 20 | Integrar Parametrizacion.js con API usuarios + boton sync AD | pendiente | — | |
| 21 | Sanear 4 x-html con DOMPurify | pendiente | — | |
| 22 | Agregar CSP meta tag | pendiente | — | |
| 23 | Rate limit con slowapi | pendiente | — | |
| 24 | **TESTING R1** | pendiente | — | |
| 25-43 | R2 + docs | pendiente | — | |

---

## Progreso R1
**1/24 tareas completadas** (setup inicial cerrado)

## Progreso R2
**0/22 tareas pendientes**

## Total
**6/46 tareas (13%)** — fase de setup completada + stack validada

## Tablas de BD
**0/28 migradas** (próxima: tarea #7 — 11 tablas de Organización)

## Decisiones tomadas (ADRs)
- ADR-001 a ADR-010 (ver DECISIONES.md)
- ADR-011: Nomenclatura códigos = sigla_area + codigo_tipo + correlativo (mantener legacy COFAR)
- ADR-012: Sync AD = botón manual + job 00:05, reasignación inmediata

---

## Versiones validadas (snapshot 2026-06-14)

| Componente | Versión | Fuente |
|---|---|---|
| Python | 3.12-slim-bookworm | Docker Hub |
| FastAPI | 0.137.0 | PyPI (Jun 14, 2026) |
| SQLAlchemy | 2.0.50 | PyPI |
| Pydantic | 2.13.4 | PyPI |
| Alembic | 1.18.4 | PyPI |
| Celery | 5.6.3 | PyPI |
| Uvicorn | 0.49.0 | PyPI |
| asyncpg | 0.31.0 | PyPI |
| redis-py | 5.2.1 | PyPI (compat con Celery 5.6) |
| MSAL | 1.37.0 | PyPI |
| ldap3 | 2.9.1 | PyPI |
| PostgreSQL | 16-alpine | Docker Hub |
| Redis | 7-alpine | Docker Hub |
| Nginx | 1.27-alpine | Docker Hub |
| MailHog | latest | Docker Hub |
| Node | 22-alpine | Docker Hub |
| Vite | 8.0.16 | npm |
| Alpine.js | 3.15.12 | npm |
| Tailwind | 3.4.19 | npm |
| DOMPurify | 3.4.10 | npm |

---

## Decisiones tomadas (ADRs)

Ver `DECISIONES.md`.

## Bloqueos

Ninguno al momento.

## Próximo paso

**Tarea #6: Levantar la stack y validar `docker compose up`.**

Comando: `docker compose -f deploy/docker-compose.yml --env-file .env up -d`

Requiere:
1. Crear el archivo `.env` en la raíz (copiar de `.env.example`).
2. Docker Desktop corriendo (verificar con `docker info`).
