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

## Skills por tipo de tarea

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
| **Git workflow** | `git-workflow` |

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
