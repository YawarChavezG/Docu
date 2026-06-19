# INICIO DE SESIÓN — Prompt maestro actualizado

> **Última actualización:** 2026-06-18 (sesión 29).
> **Contiene: ritual de inicio, forma de trabajo, atajos, plan de avance, trucos MCP, clean state, reglas de commit.**

---

## Prompt para pegar al inicio de CADA sesión

```
Actúa como Tech Lead senior del proyecto COFAR SGD. Realiza el siguiente ritual de inicio:

1. LEE en este orden:
   a) docs/PR/RADIOGRAFIA-TOTAL-18-06-2026.md (radiografía completa del proyecto)
   b) docs/PR/INICIO-SESION.md (este archivo)
   c) docs/PR/BITACORA.md (última entrada de sesión)
   d) docs/PR/ESTADO.md (estado REAL del código)
   e) docs/PR/DECISIONES.md (ADRs activos, últimos 5)
   f) docs/PR/PRD.md (PRD actualizado)
   g) docs/PR/R2-PLAN-EJECUCION.md (plan R2 histórico, si aplica)

2. LEE los skills ANTES de escribir código:
   - docs/PR/LEARNINGS-ERRORES.md (errores conocidos por categoría — OBLIGATORIO)
   - docs/PR/SKILL-FRONTEND-CONVENCIONES.md (diseño system frontend)
   - docs/PR/SKILL-MCP-TESTING.md (patrones de prueba Chrome MCP)

3. DIAGNOSTICA el ambiente (rápido, 2 min):
   - Docker ps: `docker ps --filter "name=sgd-"`
   - Backend health: `curl.exe http://localhost:18000/api/v1/health`
   - BD limpia: `docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT * FROM verify_clean_state();"`
   - Branch actual: `git status --short && git log --oneline -3`

4. IDENTIFICA la siguiente tarea PENDIENTE:
   - Leer RADIOGRAFIA-TOTAL-18-06-2026.md §9 (Pendientes)
   - Identificar la primera tarea con prioridad P0/P1
   - Si la sesión anterior quedó a mitad, retomar ahí
   - PREGUNTAR: "La siguiente tarea pendiente es X. Procedo? o preferís priorizar otra cosa?"
   - Si el usuario NO responde específicamente, NO empezar — esperar confirmación

5. FORMA DE TRABAJO OBLIGATORIA:
   - Código limpio: sin code smells, sin debug leftovers, con type hints
   - Arquitectura modular: 1 archivo = 1 responsabilidad
   - REVISAR LEARNINGS-ERRORES.md ANTES de cada cambio (evitar errores pasados)
   - Si hay cambios en backend: `docker restart sgd-backend`
   - Si hay cambios en frontend: `docker restart sgd-frontend` (o esperar HMR)
   - Validar con Chrome MCP siguiendo SKILL-MCP-TESTING.md
   - Validar con pytest: `cd backend && .venv\Scripts\python -m pytest tests/`
   - Validar persistencia: F5 reload y verificar que el estado se mantenga
   - Probar múltiples escenarios: feliz, error, borde, permisos
   - Si el cambio requiere BD limpia: `scripts\restore_clean_state.bat`

6. AL FINALIZAR LA SESIÓN (antes de cerrar):
   a) Hacer commit atómico con conventional commit (tipo(scope): descripción)
   b) Actualizar ESTADO.md (marcar tareas completadas, añadir nuevas)
   c) Actualizar BITACORA.md (agregar entrada de sesión con resumen)
   d) Actualizar DECISIONES.md (si hubo nuevas decisiones técnicas)
   e) Actualizar PRD.md (si cambió el alcance del proyecto)
   f) Actualizar RADIOGRAFIA-TOTAL.md (si cambió estructura: nuevas tablas, endpoints, páginas)
   g) Si se descubrieron nuevos errores: actualizar LEARNINGS-ERRORES.md
   h) Reportar resumen al usuario: qué se hizo, qué falta, qué bloqueos hay

7. REGLAS DURAS (NO ROMPER):
   - No asumas victoria sin: evidencia visual + BD + persistencia + tests
   - No inventes datos — la BD es la única fuente de verdad
   - No uses mocks del frontend en backend
   - Toda mutación pasa por API y deja audit_log con write_audit()
   - No hagas DELETE físico — siempre borrado lógico (activo=False)
   - No cambies puertos sin verificar con netstat primero
   - Si te trabas >15 min, salir del loop y consultar al usuario
   - Si detectas un loop, forzar salida inmediatamente
```

---

## Stack y credenciales

- **Frontend:** `http://localhost:8080` (Nginx) o `http://localhost:5173` (Vite dev)
- **Backend:** `http://localhost:18000/api/v1/...` (FastAPI)
- **BD:** `postgresql://sgd:sgd_dev_only_change_in_prod@localhost:25432/sgd`
- **Usuarios locales:** admin_local, eto_test, elaborador_revisor, elab._revisor_aprob., visualizador_cl (password: `cofar.2026`, admin_local: `admin.2026`)
- **Usuarios AD (requieren auth_source: "cofar"):** aromero, ychavez, etc.

---

## Pre-flight checks

```powershell
docker ps --filter "name=sgd-"           # 8 servicios Up
curl.exe http://localhost:18000/api/v1/health  # {"status":"ok","database":"ok"}
docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT * FROM verify_clean_state();"
```

Si nginx da 502: `docker restart sgd-nginx` (recarga DNS tras stop/start).

---

## Clean state (BD)

```powershell
scripts\restore_clean_state.bat
```

Esto detiene backend+celery, restaura dump de `backups/clean_state_20260618/`, y los vuelve a levantar. Verificar después con `verify_clean_state()`.

---

## Trucos Chrome MCP aprendidos

- `x-model` de Alpine NO se actualiza con `dispatchEvent(new Event('input'))` para `<input type="date">` ni checkboxes. Workaround: setear `Alpine.$data(root).variable = valor` directamente.
- Para `<select>`, el match por `value` SÍ funciona bien.
- Después de hacer click en botón que dispara POST, los uids del snapshot pueden quedar viejos. Hacer `take_snapshot` antes del próximo click.
- Para evitar `confirm()` del browser: `window.confirm = () => true;` antes del click.
- Para radio buttons "Fuente de autenticación": usar `evaluate_script` con `r.click()` directo.

---

## Atajos rápidos

```powershell
# Re-levantar todo
scripts\start-stack-des.bat

# Bajar todo
scripts\stop-stack-des.bat

# Logs backend
docker logs sgd-backend -f --tail 100

# Tests
cd backend && .venv\Scripts\python -m pytest tests/ 2>&1 | Select-Object -Last 5

# Login local
curl.exe -X POST http://localhost:18000/api/v1/login -H "Content-Type: application/json" -d '{\"username\":\"eto_test\",\"password\":\"cofar.2026\",\"auth_source\":\"local\"}'
```

---

## Skills de referencia (leer ANTES de escribir código)

| Skill | Archivo | Cuándo leerlo |
|---|---|---|
| Errores conocidos | `docs/PR/LEARNINGS-ERRORES.md` | **SIEMPRE** antes de cualquier cambio |
| Frontend conventions | `docs/PR/SKILL-FRONTEND-CONVENCIONES.md` | Cuando toques UI/frontend |
| MCP Testing | `docs/PR/SKILL-MCP-TESTING.md` | Cuando hagas pruebas con Chrome MCP |

## Orden de lectura de archivos (para IA)

1. `docs/PR/RADIOGRAFIA-TOTAL-18-06-2026.md` — radiografía completa
2. `docs/PR/INICIO-SESION.md` — este archivo
3. `docs/PR/LEARNINGS-ERRORES.md` — errores conocidos
4. `docs/PR/BITACORA.md` — última sesión
5. `docs/PR/ESTADO.md` — progreso actual
6. `docs/PR/DECISIONES.md` — ADRs activos
7. `docs/PR/PRD.md` — PRD actualizado
8. `docs/PR/SKILL-FRONTEND-CONVENCIONES.md` — si tocas UI
9. `docs/PR/SKILL-MCP-TESTING.md` — si pruebas con Chrome

## Prompt corto para nueva sesión

Para arrancar una nueva sesión, solo decime esto:

> "Lee docs/PR/INICIO-SESION.md y seguí las instrucciones.
> Empezá con la tarea [P0/P1/prioridad que corresponda].
> Cuando termines, actualizá los docs y commitá."

Ejemplo real:
> "Lee docs/PR/INICIO-SESION.md y seguí las instrucciones.
> Empezá con la tarea P0: scripts seed rotos.
> Cuando termines, actualizá los docs y commitá."

La IA va a:
1. Leer RADIOGRAFIA → INICIO-SESION → LEARNINGS → BITACORA → ESTADO
2. Leer skills relevantes (LEARNINGS + los que apliquen)
3. Diagnosticar ambiente
4. Identificar la tarea específica
5. Preguntar confirmación
6. Ejecutar con validación MCP + BD + persistencia + tests
7. Actualizar docs y commitear al final
8. Reportar resumen
