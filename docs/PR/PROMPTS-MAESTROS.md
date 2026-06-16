

---

## 🎯 PROMPT MAESTRO — SESIÓN A (pegar al abrir opencode)

```
Hola. Soy Y. Chávez, tech lead del proyecto COFAR SGD (sistema de
gestión documental farmaceutico en Bolivia, 750 usuarios).

**ALCANCE DE ESTA SESION (Sesión A — backend completo):**
Esta sesion cierra el BACKEND de la ÉPICA 9 al 100% con 10 tareas.
NO se toca frontend. NO se hacen tests pytest. NO se hace
asignacion masiva desde la matriz de abril. Esas son Sesion B.

**LO QUE VAS A HACER (en orden estricto):**
1. Lee docs/PR/INICIO-SESION.md (ritual de inicio)
2. Lee docs/PR/ESTADO.md (estado REAL del codigo)
3. Lee docs/PR/BITACORA.md (que se hizo en sesiones anteriores)
4. Lee docs/PR/MATRICES-MAPEO.md (mapeo archivos MATRICES -> endpoints)
5. Identifica la siguiente tarea PENDIENTE: la #1 (utils/api.js)
6. Proponme plan con tiempo, skills, riesgos. ESPERA mi OK.

**LAS 10 TAREAS DE ESTA SESION:**
1. frontend/src/utils/api.js (apiFetch con CSRF, retry, error handling)
2. backend/scripts/seed_organizacion.py (10 gerencias, 49 areas, 5 roles, 10 modulos)
3. CRUD /api/v1/gerencias (US-9.06)
4. CRUD /api/v1/areas (US-9.06)
5. CRUD /api/v1/configuracion-global (US-9.01 + 9.02)
6. CRUD /api/v1/feriados (calendario Bolivia 2026)
7. CRUD /api/v1/email-templates (US-9.04 — 6 plantillas, NO 5)
8. CRUD /api/v1/matriz-enrutamiento-eto (US-9.03)
9b. CRUD /api/v1/tipos-documento (US-9.03 — 13 tipos)
9c. CRUD /api/v1/estados (US-9.03 — 5 estados)

**SKILLS POR TAREA (usar EXACTAMENTE estas):**
| Tarea | Skills a invocar |
|---|---|
| 1 | frontend-design-direction, api-design, frontend-a11y |
| 2 | database-migrations, coding-standards, verification-loop |
| 3,4 | fastapi-patterns, api-design, error-handling |
| 5 | fastapi-patterns, api-design, verification-loop |
| 6,7,8,9b,9c | fastapi-patterns, api-design |

**INVOCAR python-reviewer (agent) ANTES de cada commit** para validar
codigo nuevo.
**INVOCAR git-workflow (skill) ANTES de cada commit** para validar
conventional commit + sin secretos.

**VALIDACION EMPIRICA (no asumas nada):**
- Cada endpoint nuevo: test con curl.exe y ver el JSON de respuesta
- Cada seed: ejecutar y verificar con SELECT en la BD
- Al final: docker logs sgd-backend --tail 30 (no debe haber errores)

**DOCUMENTACION CONTINUA:**
- Al terminar cada tarea, actualiza docs/PR/ESTADO.md
- Al cerrar sesion, actualiza BITACORA.md con sesion N+1

**CIERRE DE SESION:** "Ejecutá el ritual de cierre" → actualiza docs,
commit, reporte resumen.

Empieza con el ritual de inicio. NO codear nada todavia.
```

## 🎯 PROMPT DE CIERRE (pegar al final de la sesión)

```
Cerrá la sesión. Ejecutá el ritual de cierre:
1. Actualizá docs/PR/ESTADO.md (marca las 10 tareas completadas/pendientes)
2. Actualizá docs/PR/BITACORA.md (sesion N+1 con que se hizo y que quedo)
3. Hacé commit con conventional commit
4. Reportame resumen: que se hizo, que quedo pendiente, si hay bloqueos
5. Anotar en BITACORA.md que Sesion B (UI + tests + bulk) es lo que sigue
```

## 🎯 PROMPT DE CONTINUACIÓN — SESIÓN B (pegar al abrir la próxima sesión)

```
Hola. Soy Y. Chávez, continuando COFAR SGD Sesion B.

**CONTEXTO:** La Sesion A cerro el backend de la EPICA 9 (10 tareas
backend completas y validadas con curl). El frontend todavia NO
consume el backend — los datos siguen hardcoded en
frontend/src/data/parametrosSistema.js.

**ALCANCE DE ESTA SESION (Sesion B — UI + tests + bulk):**
6 tareas que cierran R1 al 100%.

1. Lee docs/PR/BITACORA.md (que se hizo en Sesion A)
2. Lee docs/PR/ESTADO.md (que tareas backend ya estan)
3. Levanta el stack: scripts\start-stack-des.bat
4. Identifica la siguiente tarea PENDIENTE: la #9 (audit-log)
5. Proponme plan. ESPERA mi OK.

**LAS 6 TAREAS:**
9. GET /api/v1/audit-log (con filtros)
9d. Operaciones jerarquicas areas (POST /areas/{id}/mover, /promover-a-gerencia, DELETE logico)
9e. Override vacaciones (PATCH /usuarios/{id}) + export Excel/CSV
10. Refactor frontend/src/pages/Parametrizacion.js para consumir los 9 endpoints de Sesion A
11. Tests pytest de los 9 endpoints (cobertura 80% minimo)
12. Asignacion masiva desde USUARIOS EXISTENTES A ABRIL.xlsx (730 usuarios)

**SKILLS POR TAREA:**
| Tarea | Skills a invocar |
|---|---|
| 9, 9d, 9e | fastapi-patterns, api-design, error-handling, frontend-design-direction, frontend-a11y |
| 10 | frontend-design-direction, frontend-a11y, api-design, python-reviewer (verificar contratos) |
| 11 | td-workflow, tdd-mattpocock, verification-loop |
| 12 | database-migrations, fastapi-patterns, api-design, python-reviewer |

**VALIDACION EMPIRICA:**
- 9-9e: curl + ver el frontend en localhost:8080
- 10: abrir Parametrizacion.js y ver que NO use data/parametrosSistema.js
- 11: pytest --cov=app --cov-report=term
- 12: ejecutar carga y validar conteo en BD (SELECT COUNT(*), ver warnings de diff)

**CIERRE:** Mismo ritual (ESTADO + BITACORA + commit + reporte).

Empieza con el ritual.
```
