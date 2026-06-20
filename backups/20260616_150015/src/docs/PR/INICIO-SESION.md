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



---




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



#### 🅰️ SESIÓN A — Backend completo (10 tareas, ~6-7h)

| # | Tarea concreta | |
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

| # | Tarea concreta ||
|---|---|---|
| **9** | `GET /api/v1/audit-log` (con filtros) | `fastapi-patterns`, `api-design`, `postgres-patterns` |
| **9d** | Operaciones jerárquicas áreas (`POST /areas/{id}/mover`, `/promover-a-gerencia`, `DELETE` lógico) | `fastapi-patterns`, `api-design`, `error-handling`, `database-migrations` |
| **9e** | Override vacaciones (`PATCH /usuarios/{id}`) + export Excel/CSV | `fastapi-patterns`, `api-design`, `frontend-design-direction` |
| **10** | Refactor `Parametrizacion.js` para consumir los 9 endpoints | `frontend-design-direction`, `frontend-a11y`, `api-design`, `python-reviewer` (verificar contratos) |
| **11** | Tests pytest de los 9 endpoints nuevos (80% coverage) | `tdd-workflow`, `tdd-mattpocock`, `verification-loop` |
| **12** | Asignación masiva desde `USUARIOS EXISTENTES A ABRIL.xlsx` (730 usuarios) | `database-migrations`, `fastapi-patterns`, `api-design`, `python-reviewer` — ver `docs/PR/MATRIZ-ABRIL-ASIGNACION.md` |

**Total: 16 sub-tareas** (15 reales + 9c/9d/9e marcadas como sub-índices de 9).

**Verificación de cierre de R1:** cuando las 16 sub-tareas estén ✅, abrir PR `epica-1/rama-1` → `main`, mergear, crear `epica-2/rama-1`.




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
