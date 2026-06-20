# PROMPT MAESTRO PARA NUEVA SESIÓN — COFAR SGD

> **Instrucciones para cualquier IA que inicie una sesión de trabajo.**
> **Propósito:** Que la IA tenga contexto COMPLETO del proyecto, diagnóstique el estado actual, y evite errores pasados.
> **Última actualización:** 2026-06-20 (sesión 39 — CI/CD + deploy_qas.py + GUIA-DEPLOY.md)

---

## FASE 0 — RITUAL DE INICIO (OBLIGATORIO, en este orden)

### 0.1 Leer documentación del proyecto

```
 1. docs/PR/RADIOGRAFIA-TOTAL-18-06-2026.md     — radiografía completa del proyecto
 2. docs/PR/INICIO-SESION.md                      — prompt maestro anterior, forma de trabajo
 3. docs/PR/LEARNINGS-ERRORES.md                  — 40+ errores documentados (LEER ANTES DE CUALQUIER CAMBIO)
 4. docs/PR/DECISIONES.md                         — ADRs activos
 5. docs/PR/ESTADO.md                             — estado actual del código
 6. docs/PR/BITACORA.md                           — historial completo de sesiones (prestar atención a sesión 39)
 7. docs/PR/PROPUESTA-R3-TABLAS.md                — propuesta técnica de R3
 8. docs/PR/CHECKLIST-R3-FASES.md                 — fases de R3
 9. docs/PR/GUIA-DEPLOY.md                        — GUÍA DE DEPLOY (leer antes de cualquier deploy)
10. docs/PR/PROMPT-NUEVA-SESION.md                — este archivo
```

### 0.2 Leer skills (ANTES de escribir código)

```
11. docs/PR/SKILL-FRONTEND-CONVENCIONES.md        — diseño system frontend
12. docs/PR/SKILL-MCP-TESTING.md                  — patrones de prueba Chrome MCP
```

### 0.3 Diagnosticar ambiente LOCAL (DES)

```powershell
# Docker
docker ps --filter "name=sgd-"

# Health backend
curl.exe http://localhost:18000/api/v1/health

# Tests
cd backend && .venv\Scripts\python -m pytest tests/ -q --tb=short

# BD (conteo de tablas, alembic head)
docker exec sgd-postgres psql -U sgd -d sgd -tA -c "SELECT version_num FROM alembic_version"
docker exec sgd-postgres psql -U sgd -d sgd -tA -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"

# Entrypoint funciona?
docker exec sgd-backend env ENVIRONMENT=ci bash scripts/entrypoint.sh
```

### 0.4 Diagnosticar QAS (servidor remoto)

```bash
# SSH
ssh sistemas@sgdqas.cofar.com.bo

# Docker
docker ps --filter "name=sgd-qas-"

# Health
curl -k https://sgdqas.cofar.com.bo/api/v1/health

# BD
docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c "SELECT version_num FROM alembic_version"
docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"

# Validación completa
bash /opt/sgd/scripts/validate-qas.sh
```

### 0.5 Identificar la siguiente tarea

- Leer ESTADO.md y CHECKLIST-R3-FASES.md
- Identificar la primera tarea PENDIENTE
- Preguntar confirmación al usuario ANTES de empezar

---

## FASE 1 — CONTEXTO ACTUAL DEL PROYECTO

### Rama activa
```
r3/workflow-revision-aprobacion
```

### Métricas clave (post-sesión 39)

| Métrica | Valor |
|---|---|
| Tests | 340+ PASS |
| Tablas BD | 30 (23 originales + 7 Fase 1 + 1 plantillas) |
| Migraciones Alembic | 24 aplicadas (head: r3_plantillas_table_s37) |
| Endpoints | 90+ REST |
| Usuarios | 754 (725 usuario_roles) |
| Documentos semilla | 10 |
| Plantillas documentales | 8 en BD |
| Contenedores DES | 7/7 Up |
| Contenedores QAS | 8/8 Healthy |
| QAS validate | 38/38 PASS |
| Servidor QAS | Debian 12, Docker 29.5.3, 15GB RAM, 245GB disco |

### Fases de R3

| Fase | Estado |
|---|---|
| Fase 0 (R2 wizard completado) | ✅ Código completo, formularios -F01, validación carátula, vigencia BD, flujo LIBERACION_ETO |
| Fase 1 (Modelos R3) | ✅ 7 tablas workflow + enums + semáforo corregido |
| Fase 2 (Servicios core) | ⏳ PENDIENTE (tarea_service, timeline_service, notificacion_service) |
| CI/CD | ✅ Pipeline GitHub Actions + deploy_qas.py + GUIA-DEPLOY.md |

---

## FASE 2 — REGLAS DURAS PARA ESCRIBIR CÓDIGO

### FRONTEND (Alpine.js + Tailwind)

- NO usar `confirm()` nativo. Usar modales existentes:
  * `window.confirmDeleteModal?.abrir({ titulo, mensaje, onConfirm })`
  * `window.confirmImpersonate?.abrir({ target, me, onConfirm })`
  * `window.confirmDelegadoModal?.abrir({ mensaje, onConfirm })`
- NO usar `<template x-if>` dentro de `x-teleport` (causa `_x_dataStack` null). Usar `<span x-show>` con doble control (F12 en LEARNINGS).
- NO usar `$refs` para trigger de file input. Usar `document.querySelector('[x-ref=name]')?.click()`
- `x-show` en elementos con `x-for`: ponerlo en el span PADRE, no en el botón individual.
- Paleta: brand-500 (#1a5fb4), slate-50/100/200/400/600/800, emerald, amber, red.
- Tipografía: text-xs (11px), text-[11px], font-semibold, font-mono para códigos.
- Modales de confirmación: z-index 8600.
- Dropdowns custom: form-input text-xs, con ▼, shadow-xl, hover:bg-blue-50.
- NO usar fetch() directo: usar `apiGet`, `apiPost`, `apiPatch`, `apiDelete` de `utils/api.js`.

### BACKEND (FastAPI + SQLAlchemy 2.0 async)

- SQLite en tests (conftest.py). JSONB usar `JSON().with_variant(JSONB(), "postgresql")`.
- Toda mutación pasa por `write_audit()` y deja audit_log.
- No DELETE físico. Borrado lógico (`activo=False`).
- SELECT FOR UPDATE para operaciones concurrentes (correlativo_service).
- Endpoints admin de plantillas requieren `require_eto_or_admin`.
- Al crear endpoints nuevos, registrar en `main.py` con prefix `/api/v1`.
- Migraciones: NO usar `sa.Enum(name=X)` si el ENUM ya existe (usar `sa.String(50)`).
- Entrypoint unificado: `bash scripts/entrypoint.sh` (3 modos: development/qas/ci).

### BD (PostgreSQL 16)

- 30 tablas actuales (listar con `\dt` en psql).
- Siempre verificar estado actual con consultas SQL antes de asumir.
- Migraciones manuales via `docker exec sgd-postgres psql` (patrón ADR-069).
- Antes de eliminar un valor de enum, migrar datos legacy con `UPDATE`.

### TESTS

- Siempre correr al inicio: `cd backend && .venv\Scripts\python -m pytest tests/ -q`
- Tests de FK en SQLite requieren `PRAGMA foreign_keys=ON` en conftest.
- No romper tests existentes. 340+ deben seguir pasando.
- `aiosqlite` requerido por conftest.py (instalado en requirements).

### DEPLOY

- **NUNCA** asumir que `on: push tags:` funciona (bug conocido en GitHub). Usar `on: push` + `if: startsWith(github.ref, 'refs/tags/v')`.
- **NUNCA** hacer SCP directo desde GitHub Actions (no llega a IP privada). Usar `deploy_qas.py` desde DES.
- El entrypoint debe soportar `POSTGRES_HOST=localhost` (CI) y `POSTGRES_HOST=postgres` (Docker).
- `command_timeout` en SSH actions debe ser >= 600s para docker compose build.
- Validar migrations LOCAL antes de deployar: `docker exec sgd-backend env ENVIRONMENT=ci bash scripts/entrypoint.sh`

### FLUJO DE TRABAJO

1. Preguntar al usuario la tarea a realizar
2. Si no responde, NO empezar
3. Leer LEARNINGS-ERRORES.md antes de CADA cambio
4. Validar con pytest después de CADA cambio
5. Si el cambio afecta BD: verificar con psql
6. Si hay cambios en backend: `docker restart sgd-backend`
7. Si hay cambios en frontend: `docker restart sgd-frontend`
8. Si el cambio requiere BD limpia: `scripts\restore_clean_state.bat`
9. Si te trabas >15 min: salir del loop y consultar al usuario
10. Si detectas un loop: forzar salida inmediatamente

### AL FINALIZAR LA SESIÓN

1. Commit atómico con conventional commit
2. Actualizar ESTADO.md (marcar tareas completadas)
3. Actualizar BITACORA.md (agregar entrada de sesión)
4. Actualizar DECISIONES.md (si hubo nuevas decisiones técnicas)
5. Actualizar GUIA-DEPLOY.md (si cambió el proceso)
6. Actualizar LEARNINGS-ERRORES.md (si se descubrieron nuevos errores)
7. Reportar resumen al usuario

---

## FASE 3 — REFERENCIA RÁPIDA

### Servidor QAS

| Dato | Valor |
|---|---|
| Hostname | sgdqas.cofar.com.bo |
| IP | 10.11.0.11 |
| Usuario | sistemas |
| Contraseña | D3s4rr0*2026* |
| Autenticación SSH | Key-based (id_rsa) |
| OS | Debian 12 (bookworm) |
| Docker | 29.5.3 |
| Docker Compose | v5.1.4 |
| Python | 3.11.2 |
| Git | 2.39.5 |
| Directorio base | /opt/sgd |

### Comandos rápidos

```powershell
# DES: levantar stack
docker compose -f deploy/docker-compose.yml --env-file .env up -d

# DES: tests
cd backend && .venv\Scripts\python -m pytest tests/ -q

# DES: entrypoint CI
docker exec sgd-backend env ENVIRONMENT=ci bash scripts/entrypoint.sh

# QAS: deploy completo
python scripts\deploy_qas.py

# QAS: validar
ssh sistemas@sgdqas.cofar.com.bo "bash /opt/sgd/scripts/validate-qas.sh"

# CI/CD: disparar validación
git tag vX.Y.Z-qas && git push origin vX.Y.Z-qas

# QAS: acceder BD
docker exec sgd-qas-postgres psql -U sgd -d sgd

# QAS: logs backend
docker logs sgd-qas-backend --tail 50 -f
```

### Proceso de deploy (resumen)

```
1. cd backend && .venv\Scripts\python -m pytest tests/ -q
2. docker exec sgd-backend env ENVIRONMENT=ci bash scripts/entrypoint.sh
3. git tag vX.Y.Z-qas && git push origin vX.Y.Z-qas
4. python scripts\deploy_qas.py --skip-validation
5. ssh qas "bash /opt/sgd/scripts/validate-qas.sh"  # 38/38 PASS
```

---

## FASE 4 — OBJETIVO DE LA SESIÓN

``` 
Próxima tarea: Fase 2 — Servicios core R3
1. tarea_service.py (crear/completar/rechazar/reasignar tarea)
2. timeline_service.py (bitácora append-only)
3. notificacion_service.py (crear/marcar leída)
4. Integrar envio_service.liberar_documento() con tabla tareas
5. Helper calcular_color_sla(tarea) — días hábiles vs feriados
6. Tests: 8-10 de servicios
```

Tenés el contexto COMPLETO del proyecto. Estás listo para continuar.
Preguntá cuál es la siguiente tarea o esperá instrucciones.
