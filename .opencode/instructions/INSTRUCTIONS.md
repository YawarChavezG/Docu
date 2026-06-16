# COFAR SGD — OpenCode Instructions

> Reglas operativas para que cualquier agente IA (Mavis, M3, Claude, GPT, etc.)
> trabaje correctamente en este monorepo.
> **Última revisión:** 2026-06-15 (sesión 4 + setup skills)
> **Stack:** FastAPI 0.137 + SQLAlchemy 2.0 async + PostgreSQL 16 + Redis 7 + Celery 5.6 + Alpine.js 3.15 + Docker Compose

---

## 1. Arquitectura del monorepo (verificada)

```
C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES\
├── frontend/                 # Alpine.js + Vite 8 (SPA)
├── backend/                  # FastAPI 0.137 + SQLAlchemy 2.0 async
│   ├── app/                  # código (main.py, models/, api/v1/, services/, workers/)
│   ├── alembic/              # migraciones (estado: vacía, bloqueante R2)
│   ├── scripts/              # scripts auxiliares (sync_ad_oficial.py validado)
│   ├── tests/                # pytest (estado: vacío)
│   └── requirements/
├── deploy/                   # Docker Compose + Nginx
│   ├── docker-compose.yml    # 8 servicios (postgres, redis, mailhog, backend, frontend, celery-W, celery-B, nginx)
│   └── nginx/
├── docs/                     # documentación funcional + PR
│   ├── PR/                   # Project Requirements (PRD, ESTADO, BITACORA, DECISIONES, INICIO-SESION)
│   ├── Diagramas_Matrices/   # diagramas de casos de uso + Gantt + matrices + plantillas
│   ├── SISTEMA DE GESTION DOCUMENTAL - HISTORIAS DE USUARIO.pdf
│   └── Sistema de Gestion Documental - Gantt_SGDv4.xlsx
└── .opencode/                # configuración del agente (skills, instrucciones, plugin)
    ├── instructions/         # INSTRUCTIONS.md (este archivo) + INICIO-SESION.md
    ├── skills/               # 21 skills curadas (16 ECC + 5 skills.sh)
    ├── opencode.json         # config del plugin + qué skills activar
    └── package.json          # deps del agente (ecc-universal + @opencode-ai/plugin)
```

### Infraestructura DES (Windows + VPN FortiClient)

- **Stack completa corre en Docker Compose** (ver `deploy/docker-compose.yml`).
- **El backend SÍ está dentro de Docker** (`sgd-backend` Up, healthy) y alcanza el RODC de COFAR (`172.16.10.17`) gracias a:
  - `.wslconfig` con `networkingMode=mirrored` (propaga VPN al WSL2)
  - DNS custom en `docker-compose.yml`: `172.16.10.50, 172.16.10.51, 8.8.8.8`
  - `LDAP_SERVER=172.16.10.17` (IP directa, no hostname)
- **Plan B documentado (ADR-013):** `scripts/dev-backend.bat` puede levantar el backend nativo si Docker se rompe.
- **Punto único de entrada:** `scripts\start-stack-des.bat` levanta TODO con un solo comando.

### Puertos NO estándar (importante)

| Servicio | Puerto host | Notas |
|---|---|---|
| Nginx | **8080** | Entry point navegador |
| Vite (frontend directo) | **5173** | Solo para HMR dev |
| FastAPI (debug directo) | **18000** | Solo para curl/debug |
| PostgreSQL | **25432** | NO 15432 (binding error en Docker Desktop Windows) |
| Redis | **26379** | NO 16379 (preventivo, mismo motivo) |
| MailHog UI | **8025** | SMTP dev |
| MailHog SMTP | **1025** | SMTP dev |

---

## 2. Convenciones operativas (DOCUMENTOS DE RETOMA)

Toda sesión nueva DEBE empezar leyendo estos 3 archivos en este orden:

1. **`docs/PR/INICIO-SESION.md`** — prompt maestro que arranca la sesión (lèelo y ejecutalo).
2. **`docs/PR/BITACORA.md`** — bitácora cronológica de sesiones anteriores (qué se hizo, qué quedó pendiente).
3. **`docs/PR/ESTADO.md`** — live tracker de las 46 tareas de R1+R2, con estado REAL del código (no el planeado).

Si la sesión se cierra abruptamente (tokens agotados, error, loop), el agente **debe actualizar** estos 3 archivos antes de terminar.

---

## 3. Coding Style & Convenciones (NO ROMPER)

### 3.1 Idioma
- **Código:** identificadores en **inglés** (`get_user_by_id`, `authenticate_user`).
- **SQL / DDL:** nombres de tabla/columna en **español** (`usuarios`, `gerencias`, `fecha_desde`) para paridad con COFAR.
- **Comentarios / docstrings:** en **español** (Google style).
- **Mensajes al usuario / UI:** en **español**.
- **Logs:** en **español** con timestamps ISO 8601 + timezone `America/La_Paz` (UTC-4).

### 3.2 Backend (Python)
- **PEP 8** + Black con `line-length = 100`.
- **Type hints** obligatorios en todas las firmas.
- **Docstrings** en Google style, en español.
- **Imports:** stdlib → third-party → local.
- **Async only:** SQLAlchemy 2.0 async + `asyncpg`. Nunca sync calls que bloqueen el event loop.

### 3.3 Frontend (JavaScript)
- **ES modules** (`type: module`), **NO TypeScript** (mantener patrón original).
- Alpine.js stores en `src/store/*.js`, pages en `src/pages/*.js`, componentes en `src/components/*.js`.
- **Datos**: backend es la única fuente de verdad. NO usar `src/data/*.js` en producción (es legacy mock).

### 3.4 Git — Estrategia de branching (UNA RAMA POR ÉPICA)

```
main (protegido, solo PRs)
├── epica-1/rama-1   ← R1 trabajo actual
│   ├── feat/R1-login-ldap     (sub-rama solo si feature es grande/experimental)
│   └── fix/ad-sync-bitmask
├── epica-2/rama-1   ← R2 (crear al cerrar R1)
└── epica-3/rama-1   ← R3 (crear al cerrar R2)
```

**Reglas:**
- **`main`** está protegido. Solo recibe PRs desde `epica-X/rama-X` cuando la épica cierra (todos los criterios de aceptación OK + tests pasando + docs actualizados).
- **`epica-X/rama-X`** es la rama de trabajo del día a día. Commits directos ahí.
- **`feat/RX-descripcion`** solo si la feature es grande o experimental. Features medianas/pequeñas: commit directo en la rama de la épica.
- **`fix/descripcion-corta`** para bugfixes. Preferentemente desde la rama de la épica actual.
- **Al cerrar la épica**: PR de `epica-X/rama-X` → `main`, merge, crear `epica-(X+1)/rama-1` desde main actualizado.

**Estado actual:** estamos en `epica-1/rama-1` desde el commit inicial. Al cerrar R1 → merge a main → crear `epica-2/rama-1`.

**Commits:** Conventional Commits (`feat(scope): descripción`, `fix(scope):`, `docs(scope):`, etc.). Ver §8 para la regla de `git-workflow` antes de cada commit.

**NO commitear secretos.** El `.env` está en `.gitignore`.

---

## 4. Seguridad (OBLIGATORIO antes de cada commit)

- [ ] **Input validation:** Pydantic v2 estricto en TODOS los endpoints.
- [ ] **SQL injection:** solo queries parametrizadas con SQLAlchemy. NUNCA `text()` con concatenación.
- [ ] **XSS:** sanitizar todo `x-html` con DOMPurify. Preferir `x-text` cuando sea posible.
- [ ] **CSRF:** cookie + header `X-CSRF-Token` (double-submit). Frontend lee de cookie y reenvía.
- [ ] **Session:** `HttpOnly; SameSite=Lax; Secure` (en prod). Login via LDAP bind (nunca `password === 'cofar.2026'`).
- [ ] **Firma digital 2FA:** endpoint `POST /api/v1/auth/verify-password` para flujos críticos (US-2.06, 3.03, 3.04, etc.). Log en tabla `firmas_digitales`.
- [ ] **Secrets:** NUNCA hardcodear LDAP_PASSWORD, MS_CLIENT_SECRET, etc. Usar `.env` + Pydantic Settings.
- [ ] **Rate limit:** `slowapi` en backend (100 req/min por usuario, 10 req/min login) + Nginx (30 req/s por IP, 5 req/min auth/*).

---

## 5. Base de datos (R1+R2 = 28 tablas)

> Detalle completo en `docs/ARQUITECTURA-DB.md`. Resumen: las **11 tablas de Organización** ya están en código (`backend/app/models/`), **FALTA migración Alembic** (tarea #8, bloqueante para R2).

### A. Organización (11 ya creadas en código)
- `gerencias` (8-10 sembradas)
- `areas` (~25 sembradas con sigla)
- `usuarios` (estructura + sync on-demand al login)
- `roles` (5 sembrados: ADMIN, ETO, ELABORADOR-REVISOR, ELABORADOR-REVISOR-APROBADOR, VISUALIZADOR-CL-EVAL)
- `usuario_roles` (N:M)
- `modulos` (10 sembrados)
- `usuario_modulos` (N:M)
- `delegaciones`
- `ausencias`
- `firmas_digitales`
- `log_sincronizacion_ad`

### B. Pendientes para R2 (17 tablas)
Ver `docs/PR/PRD.md § 5` y `docs/PR/REUNIONES-R3-R6.md` para el detalle completo.

### Nomenclatura del código de documento (ADR-011)
```
{sigla_area}-{codigo_tipo}-{correlativo_3_digitos} v{version_2_digitos}
Ejemplo: CC-5-001 v01
```

---

## 6. Agentes y comandos slash del plugin de opencode

> **Plugin activo:** `ecc-universal` (ECC v2.0.0) + `@opencode-ai/plugin`.
> **Hook profile:** `ECC_HOOK_PROFILE=minimal` (configurado en opencode.json).
> Esto le da al modelo M3 acceso a **26 comandos slash** y **26 agentes especializados** que el plugin invoca automáticamente según el contexto.

### 6.1 Comandos slash disponibles (26)

| Comando | Cuándo usarlo |
|---|---|
| `/plan` | Antes de empezar una tarea grande (ej: implementar wizard 4 pasos) |
| `/tdd` | Cuando implementes endpoints con sus tests |
| `/code-review` | Después de modificar código en `models/` o `api/v1/` |
| `/security` | Cuando trabajes en `auth.py`, JWT, cookies, secrets |
| `/build-fix` | Cuando el backend no compila o Alembic falla |
| `/e2e` | Cuando termines una fase y quieras validar end-to-end con Playwright |
| `/refactor-clean` | Para limpiar código muerto entre sesiones |
| `/orchestrate` | Para tareas multi-paso (ej: tarea #7 = 11 modelos + seed + migración) |
| `/learn` | Para extraer patrones de la sesión a skills reutilizables |
| `/checkpoint` | Para guardar progreso explícitamente |
| `/verify` | Bucle de verificación (asserción, no asunción) |
| `/eval` | Evaluación de calidad |
| `/update-docs` | Para mantener `docs/PR/ESTADO.md` y `BITACORA.md` sincronizados |
| `/update-codemaps` | Genera mapas visuales del código |
| `/test-coverage` | Análisis de cobertura de tests |
| `/setup-pm` | Configurar package manager |
| `/go-review`, `/go-test`, `/go-build` | Para código Go (no aplica a este proyecto) |
| `/skill-create` | Generar skills nuevas |
| `/instinct-status`, `/instinct-import`, `/instinct-export` | Gestión de instincts |
| `/evolve` | Clustering de instincts |
| `/promote` | Promover instincts a skills |
| `/projects` | Listar proyectos conocidos |

### 6.2 Agentes especializados (26 — usar proactivamente)

| Agente | Cuándo invocarlo |
|---|---|
| `build` | Coding agent primario |
| `planner` | Planning de features complejas |
| `architect` | Decisiones de arquitectura y escalabilidad |
| `code-reviewer` | Después de escribir/modificar código |
| `security-reviewer` | Antes de commits con código sensible |
| `tdd-guide` | Nuevas features, bug fixes (TDD) |
| `build-error-resolver` | Cuando falla el build |
| `e2e-runner` | Tests E2E con Playwright |
| `doc-updater` | Mantener docs sincronizados |
| `refactor-cleaner` | Limpiar código muerto |
| `python-reviewer` | **PRINCIPAL** — review de código Python |
| `database-reviewer` | **PRINCIPAL** — SQLAlchemy + PostgreSQL |
| `docs-lookup` | Buscar docs de librerías (Context7) |
| `harness-optimizer` | Tuning del setup del agente |
| `go-reviewer`, `go-build-resolver` | Para código Go (no aplica) |
| `java-reviewer`, `java-build-resolver` | Para Java (no aplica) |
| `kotlin-reviewer`, `kotlin-build-resolver` | Para Kotlin (no aplica) |
| `php-reviewer` | Para PHP (no aplica) |
| `rust-reviewer`, `rust-build-resolver` | Para Rust (no aplica) |
| `cpp-reviewer`, `cpp-build-resolver` | Para C++ (no aplica) |
| `loop-operator` | Ejecución de loops autónomos |

### 6.3 Custom tools (accesibles como tools del agente)

- `run-tests` — correr suite de tests
- `check-coverage` — análisis de cobertura
- `security-audit` — scan de vulnerabilidades
- `format-code` — detectar formatter
- `lint-check` — detectar linter
- `git-summary` — resumen de branch + status + diff
- `changed-files` — listar archivos cambiados
- `dependency-analyzer` — analizar dependencias

### 6.4 Cómo invocar skills instaladas

Las 21 skills en `.opencode/skills/` están listadas en `opencode.json` → `instructions`. El agente las lee automáticamente cuando el contexto lo requiere. Para invocar explícitamente, mencionar la skill en el prompt:

```
"Usando la skill fastapi-patterns, refactoriza este endpoint..."
"Como dice coding-standards, aplica Black + type hints aquí..."
"Como dice database-migrations, genera la migración Alembic para..."
```

---

## 7. Plan de avance (R1 + R2 + roadmap completo)

Ver `docs/PR/INICIO-SESION.md` para el flujo paso a paso, y `docs/PR/REUNIONES-R3-R6.md` para el análisis de las reuniones futuras.

### R1 (martes 17-jun-2026) — Seguridad + Parametrización
Estado actual: **~50% completo** (ver `docs/PR/ESTADO.md`).
Pendiente crítico: Alembic init, endpoints faltantes, tests, rate limit, CSP/DOMPurify.

### R2 (martes 17-jun-2026) — Wizard de creación
Estado actual: **0% completo**. Bloqueado por R1 + Alembic.

### R3-R6 (próximas 4 reuniones, cada 2 semanas)
Análisis completo en `docs/PR/REUNIONES-R3-R6.md` con todas las US pendientes.

---

## 8. ⭐ REGLA DE ORO: `git-workflow` SIEMPRE antes de commit

**Ningún commit sin antes invocar la skill `git-workflow`.** Esta skill valida:
1. Mensaje sigue Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`, `perf:`, `ci:`).
2. NO hay secretos (`security-review` agent escanea).
3. Archivos versionados correctos (no `node_modules`, no `.env`, no logs, no PDFs/XLSXs de diseño).
4. Commit atómico (1 feature = 1 commit, no mega-commits).

**Prompt obligatorio antes de CUALQUIER commit:**
```
"Invocá la skill git-workflow para validar este commit antes de hacerlo.
Verificá: conventional commit, sin secretos, archivos correctos, mensaje claro.
Después procedé con git add + git commit."
```

**Conventional Commits de este proyecto** (prefijos más usados):
- `feat(api):` endpoint nuevo
- `feat(ui):` nueva vista o componente
- `feat(db):` nuevo modelo o migración
- `feat(agent):` setup del agente (skills, opencode.json)
- `fix(ad-sync):` fix en la sincronización AD
- `fix(auth):` fix de login/JWT/cookies
- `docs(pr):` actualización de docs/PR
- `chore(repo):` limpieza, gitignore
- `refactor(api):` refactor de endpoints sin cambio funcional
- `test(api):` tests nuevos
- `feat(deploy):` cambios en docker-compose

## 9. Stubs en DES (reemplazables en QAS con env vars)

---

## 10. Trampas conocidas (NO caer en ellas)

1. **PowerShell aliasa `curl` a `Invoke-WebRequest`.** Usar `curl.exe` directamente.
2. **JSON inline en PowerShell falla** (convierte comillas). Usar archivo: `echo '{"k":"v"}' > test.json` y luego `--data-binary @test.json`.
3. **El prefijo del API es `/api/v1/`** aplicado a nivel de router en `main.py`. Los routers individuales NO deben tener prefijo `/auth/` adicional.
4. **El `docker-compose.yml` se valida al hacer `up`** — si el backend no tiene `app/workers/celery_app.py`, el comando celery falla.
5. **NO comparar `userAccountControl` contra valores literales** (514, 66050). Usar **bit-mask**: `(int(uac) & 2) != 0`. Ver `backend/scripts/sync_ad_oficial.py` (fuente de verdad validada).
6. **Las migraciones Alembic no existen todavía** (R1 tarea #8). El `Base.metadata.create_all()` carga los modelos en runtime pero NO es durable. **CRÍTICO generar antes de R2**.
7. **NO escribir `password === 'cofar.2026'`** en frontend. Eso es mock legacy. Usar API real.

---

## 11. Reglas de oro (NO ROMPER)

1. **No inventar datos.** Si una tabla no existe, crearla con Alembic. No hardcodear arrays.
2. **No usar datos del frontend (`src/data/*.js`) en el backend.** El backend es la única fuente de verdad.
3. **Toda mutación pasa por API.** El frontend NUNCA modifica estado directamente sin pasar por backend.
4. **Validar con el cliente antes de cambiar stack.** Esto está en este PRD.
5. **No commitear secretos.** El `.env` está en `.gitignore`.
6. **Tests antes de marcar como hecho.** Cada US tiene criterios de aceptación que se prueban.
7. **Documentar decisiones en `docs/PR/DECISIONES.md`** (formato ADR).
8. **Versiones fijas, no `latest`.** Cualquier upgrade se documenta en el PRD.
9. **Validar empíricamente antes de declarar éxito.** Ejecutar el script, hacer el curl, ver los logs — no asumir.

---

## 12. Métricas de éxito

Una tarea está terminada cuando:
1. El código corre sin errores (verificado con `docker logs` o `curl`).
2. Los tests pasan (cuando existan).
3. La documentación está sincronizada (`ESTADO.md`, `BITACORA.md`).
4. El commit sigue Conventional Commits y no tiene secretos.
5. Los criterios de aceptación del US correspondiente están cumplidos.

