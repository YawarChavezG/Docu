# INICIO DE SESIÓN — Prompt maestro

> **Cómo arrancar cada sesión nueva con opencode + M3.**
> **Copia y pega este texto al abrir cada sesión** (o configúralo como un comando slash personalizado).

---

## Prompt para pegar al inicio de CADA sesión

```
Actua como Tech Lead senior del proyecto COFAR SGD. Realiza el siguiente ritual de inicio de sesion:

1. LEE en este orden:
   a) docs/PR/BITACORA.md (que se hizo en sesiones anteriores)
   b) docs/PR/ESTADO.md (estado REAL del codigo, no el planeado)
   c) docs/PR/INICIO-SESION.md (este archivo, para confirmar el flujo)
   d) docs/PR/REUNIONES-R3-R6.md (si estamos en R3 o posterior)
   e) docs/PR/DECISIONES.md (ADRs activos, especialmente los ultimos 3)

2. DIAGNOSTICA el ambiente:
   - Verificar que Docker esta corriendo: `docker info`
   - Verificar que el stack esta Up: `docker ps --filter "name=sgd-"`
   - Si el backend no esta Up: ejecutar `scripts\start-stack-des.bat`
   - Verificar health: `curl.exe http://localhost:18000/api/v1/health`
   - Si algo falla, usar el custom tool `build-error-resolver` agent

3. IDENTIFICA la siguiente tarea PENDIENTE:
   - Leer la tabla en ESTADO.md
   - Identificar la primera fila con estado ⏳ o pendiente
   - Si hay tareas en curso (🟡), evaluar si estan realmente completas
   - Si la sesion anterior quedo a mitad de una tarea, retomar ahi

4. PROPON al usuario:
   - "La siguiente tarea pendiente es #X: <titulo>"
   - "Tiempo estimado: <X> minutos"
   - "Skills que se invocaran: <lista>"
   - "Riesgos: <lista>"
   - "Como la voy a ejecutar: <plan corto>"
   - PREGUNTAR: "Procedo? o preferis priorizar otra cosa?"

5. Si el usuario aprueba, EJECUTA:
   - Si la tarea es codigo, invocar /plan primero
   - Si la tarea es bugfix, invocar /build-fix
   - Si la tarea es review, invocar /code-review
   - Si la tarea es test, invocar /tdd
   - Si la tarea es seguridad, invocar /security
   - Si la tarea es e2e, invocar /e2e
   - Documentar paso a paso con outputs visibles
   - Si te trabas >15 min, salir del loop y consultar

6. ANTES de cerrar sesion, ACTUALIZA:
   - docs/PR/ESTADO.md (marcar tareas como completadas/pendientes)
   - docs/PR/BITACORA.md (anadir sesion nueva con lo que se hizo)
   - Hacer commit con conventional commit
   - Reportar resumen al usuario: que se hizo, que quedo pendiente, si hay bloqueos

ESCENARIOS DE EMERGENCIA:

- Si la sesion se quedo sin tokens: el usuario debe decir "lee docs/PR/INICIO-SESION.md y retoma desde donde quedamos" y vos seguis el ritual.
- Si el agente itera en loop sobre lo mismo: SALIR inmediatamente. Decir "Detecte un loop. Forzando salida. Cual es el siguiente paso que el usuario quiere?" Documentar el loop en BITACORA.md.
- Si la sesion se cerro por error: el agente debe dejar ESTADO.md y BITACORA.md actualizados ANTES de cualquier cambio grande (regla de "checkpoint frecuente").
- Si el usuario vuelve despues de dias: leer BITACORA.md (entrada de la ultima sesion) y ESTADO.md, preguntar "retomamos la tarea #X que quedo al 50%? o preferis empezar una nueva?"

IMPORTANTE: usa SIEMPRE el stack de 21 skills instaladas en .opencode/skills/. Menciona explicitamente cual invocas en cada paso.
```

---

## ⚠️ CÓMO ENCONTRAR SKILLS Y AGENTS (lección aprendida sesión 5 — 2026-06-15)

> **Las skills y agents del plugin ECC NO se descubren automaticamente con el tool `skill`.**
> Hay que buscarlos en el filesystem antes de usarlos.

### Skills (21 archivos en `.opencode/skills/`)

| Tipo | Ubicación | Cómo se invoca |
|---|---|---|
| **Skills del proyecto (curadas)** | `.opencode/skills/<nombre>/SKILL.md` | Leer el archivo directo con `read`. El tool `skill` puede NO listarlas (encontrarás solo `customize-opencode`). |
| **Agents del plugin ECC** | `.opencode/node_modules/ecc-universal/agents/<nombre>.md` | Invocar con `task --subagent_type=<nombre>`. Ej: `python-reviewer`, `database-reviewer`, `code-reviewer`, `security-reviewer`. |
| **INSTRUCTIONS operativo** | `.opencode/instructions/INSTRUCTIONS.md` | Leer directo. Lista los 26 comandos slash y los 26 agents del plugin ECC v2.0.0. |

### Skill `git-workflow` (CRÍTICA — antes de cada commit)

Path: `.opencode/skills/git-workflow/SKILL.md`. **Siempre leerla antes de un commit.** Checklist de validación:

1. **Conventional Commits**: `feat(scope):`, `fix(scope):`, `docs(scope):`, `chore(scope):`, `refactor(scope):`, `test(scope):`, `perf(scope):`, `ci(scope):`, `revert(scope):`. Subject imperativo, <50 chars ideal.
2. **Sin secretos**: `grep -i 'password\|secret\|token\|api[_-]\?key\|credential' <archivos_nuevos>` antes de commitear. Solo deben aparecer keywords de la skill (p.ej. `csrf_token` nombre de cookie, `credentials` opción de fetch).
3. **Archivos correctos**: NO `node_modules/`, `.env`, `dist/`, `__pycache__/`, `*.log`, PDFs/XLSXs de diseño.
4. **Commit atómico**: 1 feature = 1 commit. NO mega-commits con archivos no relacionados.
5. **Branch correcta**: `epica-X/rama-X` (no `main` directamente, salvo cierre de épica con PR).

### Agentes del plugin ECC (CRÍTICOS para esta sesión A)

| Agent | Path | Cuándo invocar |
|---|---|---|
| `python-reviewer` | `.opencode/node_modules/ecc-universal/agents/python-reviewer.md` | **SIEMPRE antes de commit con código Python nuevo** (tareas #2 a #9c) |
| `database-reviewer` | `.opencode/node_modules/ecc-universal/agents/database-reviewer.md` | Para SQLAlchemy 2.0 + migraciones Alembic |
| `code-reviewer` | `.opencode/node_modules/ecc-universal/agents/code-reviewer.md` | Review genérico cross-stack |
| `security-reviewer` | `.opencode/node_modules/ecc-universal/agents/security-reviewer.md` | Solo cuando hay código sensible (auth, cookies, CSRF, secrets) |
| `docs-lookup` | `.opencode/node_modules/ecc-universal/agents/docs-lookup.md` | Cuando hay duda de sintaxis de una librería (usa Context7) |

### Flujo recomendado para cada tarea (sesión A)

```
1. Leer 2-3 skills relevantes (read del SKILL.md)
2. Plan: anotar archivos a crear/modificar + queries de validación
3. Codear
4. Validar empíricamente (curl, SELECT, logs Docker)
5. Invocar `python-reviewer` agent sobre el código nuevo
6. Releer skill `git-workflow` → checklist
7. git add + commit conventional
8. Actualizar ESTADO.md y BITACORA.md → commit docs
```

```

---

## Atajos rápidos (para usar en cualquier momento)

### Verificar que el stack está OK
```powershell
docker ps --filter "name=sgd-"
curl.exe http://localhost:18000/api/v1/health
```

### Re-levantar todo
```bash
scripts\start-stack-des.bat
```

### Bajar todo
```bash
scripts\stop-stack-des.bat
```

### Ver logs del backend en vivo
```bash
docker logs sgd-backend -f --tail 100
```

### Aplicar migración Alembic (cuando exista)
```bash
docker exec sgd-backend alembic upgrade head
```

### Generar nueva migración
```bash
docker exec sgd-backend alembic revision --autogenerate -m "descripcion del cambio"
```

### Probar login LDAP real
```bash
curl -X POST http://localhost:18000/api/v1/login -H "Content-Type: application/json" -d "{\"username\":\"soporteglpi\",\"password\":\"glpi.1T.C0f4r\",\"auth_source\":\"cofar\"}"
```

### Login con stubs (sin LDAP)
```bash
curl -X POST http://localhost:18000/api/v1/login -H "Content-Type: application/json" -d "{\"username\":\"aromero\",\"password\":\"cofar.2026\",\"auth_source\":\"local\"}"
```

---

## 🧠 Skills: CHEAT SHEET (memoria de skills por fase)

> **Regla:** invocar 1-3 skills por tarea. NO saturar. El agente ya las tiene cargadas por opencode.json — solo hay que **mencionarlas explícitamente** en el prompt.

### Skills de FLUJO (siempre, en cualquier sesión)

| Cuándo | Skill | Prompt ejemplo |
|---|---|---|
| **Iniciar sesión** | `codebase-onboarding` | "Leyendo el codebase con la skill codebase-onboarding, dame un resumen de 5 líneas de la estructura." |
| **Diagnosticar ambiente** | (manual) | "Corre `docker info`, `docker ps`, `curl health`. Reporta qué falla." |
| **Antes de commit** | **`git-workflow`** ⭐ | "Usando la skill git-workflow, validá que el commit sigue conventional commits y no tiene secretos." |
| **Cuando hay error desconocido** | (built-in: `build-error-resolver` agent) | "Invocá el agente build-error-resolver para diagnosticar este traceback." |
| **Cuando hay duda sobre una librería** | (built-in: `docs-lookup` agent) | "Usá docs-lookup para confirmar la sintaxis exacta de SQLAlchemy 2.0 con asyncpg." |
| **Cuando te trabás >15 min** | `error-handling` | "Usando error-handling, identificá la causa raíz de este fallo y proponé 2 alternativas." |
| **Para limpiar código muerto** | (built-in: `refactor-cleaner` agent) | "Invocá refactor-cleaner sobre el directorio backend/app/api/v1/." |
| **Al cerrar sesión** | `doc-updater` (agent) + `git-workflow` | "Actualizá ESTADO.md y BITACORA.md, después hacé commit con git-workflow." |

### Skills por TIPO de TAREA (las 16 del plan, divididas en 2 sesiones)

> **El plan completo tiene 15 tareas. Está dividido en 2 sesiones de ~6-7h cada una.**
> Ver `docs/PR/MATRICES-MAPEO.md` para el detalle de cada US de la ÉPICA 9.

#### 🅰️ SESIÓN A — Backend completo (10 tareas, ~6-7h)

| # | Tarea concreta | Skills a invocar |
|---|---|---|
| **1** | `frontend/src/utils/api.js` (apiFetch con CSRF) | `frontend-design-direction`, `api-design`, `frontend-a11y` |
| **2** | `backend/scripts/seed_organizacion.py` | `database-migrations`, `coding-standards`, `verification-loop` |
| **3** | `GET/POST/PATCH /api/v1/gerencias` | `fastapi-patterns`, `api-design`, `error-handling`, `python-reviewer` (agent, antes de commit) |
| **4** | `GET/POST/PATCH /api/v1/areas` | `fastapi-patterns`, `api-design`, `error-handling` |
| **5** | `GET/POST/PATCH /api/v1/configuracion-global` | `fastapi-patterns`, `api-design`, `verification-loop` |
| **6** | `GET/POST/PATCH /api/v1/feriados` | `fastapi-patterns`, `api-design` |
| **7** | `GET/POST/PATCH /api/v1/email-templates` (US-9.04, **6 plantillas** del PDF) | `fastapi-patterns`, `api-design`, `error-handling` |
| **8** | `GET/POST/PATCH /api/v1/matriz-enrutamiento-eto` | `fastapi-patterns`, `api-design`, `verification-loop` |
| **9b** | `GET/POST/PATCH /api/v1/tipos-documento` (US-9.03) | `fastapi-patterns`, `api-design`, `database-migrations` |
| **9c** | `GET/POST/PATCH /api/v1/estados` (US-9.03) | `fastapi-patterns`, `api-design` |

#### 🅱️ SESIÓN B — UI + tests + bulk (6 tareas, ~4-5h)

| # | Tarea concreta | Skills a invocar |
|---|---|---|
| **9** | `GET /api/v1/audit-log` (con filtros) | `fastapi-patterns`, `api-design`, `postgres-patterns` |
| **9d** | Operaciones jerárquicas áreas (`POST /areas/{id}/mover`, `/promover-a-gerencia`, `DELETE` lógico) | `fastapi-patterns`, `api-design`, `error-handling`, `database-migrations` |
| **9e** | Override vacaciones (`PATCH /usuarios/{id}`) + export Excel/CSV | `fastapi-patterns`, `api-design`, `frontend-design-direction` |
| **10** | Refactor `Parametrizacion.js` para consumir los 9 endpoints | `frontend-design-direction`, `frontend-a11y`, `api-design`, `python-reviewer` (verificar contratos) |
| **11** | Tests pytest de los 9 endpoints nuevos (80% coverage) | `tdd-workflow`, `tdd-mattpocock`, `verification-loop` |
| **12** | Asignación masiva desde `USUARIOS EXISTENTES A ABRIL.xlsx` (730 usuarios) | `database-migrations`, `fastapi-patterns`, `api-design`, `python-reviewer` — ver `docs/PR/MATRIZ-ABRIL-ASIGNACION.md` |

**Total: 16 sub-tareas** (15 reales + 9c/9d/9e marcadas como sub-índices de 9).

**Verificación de cierre de R1:** cuando las 16 sub-tareas estén ✅, abrir PR `epica-1/rama-1` → `main`, mergear, crear `epica-2/rama-1`.

### Skills por TIPO de TAREA (catálogo general, para futuras sesiones)

| Tipo de tarea | Skills a invocar |
|---|---|
| **Implementar endpoint FastAPI nuevo** | `fastapi-patterns`, `api-design`, `error-handling`, `coding-standards`, `verification-loop` |
| **Crear modelo SQLAlchemy** | `database-migrations`, `database-reviewer` (agent), `backend-patterns` |
| **Generar migración Alembic** | `database-migrations`, `verification-loop` |
| **Tests con pytest** | `tdd-workflow`, `tdd-mattpocock` o `tdd-superpowers`, `verification-loop` |
| **Tests E2E con Playwright** | `webapp-testing`, `e2e-testing` |
| **Review de código** | `python-reviewer` (agent), `coding-standards` |
| **Setup de Docker** | `docker-patterns`, `deployment-patterns` |
| **Trabajo en frontend Alpine.js** | `frontend-design-direction`, `frontend-a11y`, `design-system` |
| **Diseño UI/UX** | `frontend-design-anthropic`, `design-system` |
| **Trabajo en SQL/PostgreSQL** | `postgres-patterns`, `postgres-best-practices` |
| **Seguridad / CSRF / hardening** | `security-review` (agent), `error-handling` |
| **Documentación** | `doc-updater` (agent), `codebase-onboarding` |
| **Git workflow (cualquier commit)** | **`git-workflow`** ⭐ — SIEMPRE antes de hacer commit |
| **Refactor / limpieza** | `refactor-cleaner` (agent) |
| **Hacer deploy a QAS/PRD** | `deployment-patterns`, `docker-patterns` |
| **Trabajo en R5 (PDF / obsolescencia)** | `fastapi-patterns`, `postgres-patterns`, `database-migrations` (triggers SQL) |
| **Trabajo en R6 (capacitación / chat NLP)** | `api-design`, `verification-loop`, `security-review` (chat NLP es vector de ataque) |

### ⭐ REGLA DE ORO: `git-workflow` SIEMPRE antes de commit

> **Ningún commit sin antes invocar la skill `git-workflow`.**
> Esa skill valida que:
> 1. El mensaje sigue Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
> 2. NO hay secretos commiteados (escanea con `security` agent)
> 3. Los archivos versionados son los correctos (no `node_modules`, no `.env`, no logs)
> 4. El commit tiene sentido lógico (1 feature = 1 commit, no mega-commits)

**Prompt obligatorio antes de CUALQUIER commit:**
```
"Invocá la skill git-workflow para validar este commit antes de hacerlo.
Verificá: conventional commit, sin secretos, archivos correctos, mensaje claro.
Después procedé con git add -A && git commit -m '...' "
```

---

## 📋 Plan de avance actualizado (16 sub-tareas, divididas en 2 sesiones)

> **IMPORTANTE:** el plan tiene 15 sub-tareas dividido en 2 sesiones para que sea alcanzable. Ver tabla arriba.
>
> - **Sesión A:** 10 sub-tareas backend (~6-7h). Cierra el backend de la ÉPICA 9. Validación con curl.
> - **Sesión B:** 6 sub-tareas UI + tests + bulk (~4-5h). Cierra R1 al 100% (backend + UI + tests + bulk).

---

## 🔧 PRE-FLIGHT CHECKS (5 min, ANTES de la tarea #1)

> Estos checks son OBLIGATORIOS antes de arrancar Sesión A. El agente los hace una sola vez al inicio.

1. **Crear helper `_require_eto_or_admin`** en `backend/app/api/v1/auth.py` (reutilizable para todos los routers nuevos; el patrón es el mismo que `_require_admin` pero acepta ETO o ADMIN).

2. **Verificar cómo se inicializan las tablas en la BD** (`create_all()` o init SQL). Si las tablas `gerencias`/`areas` NO existen, el seed falla. Documentar el mecanismo en un comentario.

3. **Ajustar `cascade="all, delete-orphan"`** en `gerencia.py` a `"save-update, merge"` para que el borrado lógico funcione (no queremos delete físico en cascada).

4. **Verificar el middleware CSRF**: leer `auth.py` y `core/` para confirmar cómo se emite/valida el token. Si NO existe, agregarlo en la tarea #1.

5. **Crear los 6 modelos faltantes como archivos vacíos** (solo la clase con `__tablename__`) para que el import no rompa. Después cada tarea los va completando:
   - `backend/app/models/configuracion_global.py`
   - `backend/app/models/feriado.py`
   - `backend/app/models/email_template.py`
   - `backend/app/models/matriz_enrutamiento_eto.py`
   - `backend/app/models/tipo_documento.py`
   - `backend/app/models/estado.py`
   - + registrarlos en `models/__init__.py`

**NO empezar con Alembic** (no es R1, queda para sesión 5). **NO hacer tests pytest** (queda para Sesión B). **NO tocar Parametrizacion.js** (queda para Sesión B).

---

## 🎯 Prompts maestros (copiar y pegar)

> Los prompts completos están en **`docs/PR/PROMPTS-MAESTROS.md`** (separados para fácil copia).
> Son 3 prompts:
> 1. **Prompt de inicio Sesión A** (pegar al abrir opencode)
> 2. **Prompt de cierre** (pegar al final del día)
> 3. **Prompt de inicio Sesión B** (pegar al abrir la próxima sesión)
>
> **Atajo rápido:**
> - Sesión A → copiar bloque 1 de `PROMPTS-MAESTROS.md`
> - Cierre → copiar bloque 2
> - Sesión B → copiar bloque 3 (cuando vuelvas)

---

## Plan de avance (resumen)

| Lote | Alcance | Estado |
|---|---|---|
| **L1** (R1 cierre) | Alembic init + utils/api.js + endpoints faltantes + tests + rate limit + CSP | 🟡 ~50% |
| **L2** (R2) | Modelos R2 + wizard 4 pasos + correlativos + uploads + firma 2FA + storage + bandejas | 🔴 0% |
| **L3** (R3) | Workflow ETO + bandejas paralelas + aprobación + cron SLA + liberación + árbol Outlook | 🔴 0% |
| **L4** (R4) | Office 365 + IA similitud + embeddings + webhook + cron sincronización AD | 🔴 0% |
| **L5** (R5) | PDF custodiado + marca de agua + obsolescencia + lista maestra + vencimientos | 🔴 0% |
| **L6** (R6) | Capacitación + exámenes + certificados + copias CC/CN + BI + chat RAG | 🔴 0% |

Ver `docs/PR/REUNIONES-R3-R6.md` para el detalle de cada lote.

---

## Para MAÑANA (presentación R1+R2)

Lo más importante es poder mostrar **demostración end-to-end** de:
1. **Login LDAP real** (soporteglpi / glpi.1T.C0f4r) — `auth_source: "cofar"`
2. **Login con stubs** (aromero / cofar.2026) — `auth_source: "local"`
3. **Pantalla Parametrización > Gestión de Usuarios** con los 753 usuarios del AD ya sincronizados
4. **Bandeja del ETO** mostrando un documento (cuando R2 esté listo)
5. **Wizard de creación** (cuando R2 esté listo)

Si no llegamos a R2 completo, al menos R1 demo debe estar sólido:
- Login funciona (LDAP real + stubs)
- 753 usuarios en BD con código SAP
- ETO puede parametrizar gerencias/áreas
- Sync AD manual funciona (botón ya implementado)
