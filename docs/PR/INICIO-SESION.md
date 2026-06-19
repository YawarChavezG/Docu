# INICIO DE SESIÓN — Prompt maestro actualizado

> **Última actualización:** 2026-06-18 (sesión 29).
> **Contiene: ritual de inicio, forma de trabajo, atajos, plan de avance, trucos MCP, clean state, reglas de commit.**

---

## Prompt para pegar al inicio de CADA sesión

```
Actúa como Tech Lead senior del proyecto COFAR SGD. Realiza el siguiente ritual de inicio:

1. LEE en este orden:
   a) docs/PR/RADIOGRAFIA-TOTAL-18-06-2026.md (radiografía completa del proyecto)
   b) docs/PR/BITACORA.md (última entrada de sesión)
   c) docs/PR/ESTADO.md (estado REAL del código)
   d) docs/PR/INICIO-SESION.md (este archivo)
   e) docs/PR/DECISIONES.md (ADRs activos, últimos 5)
   f) docs/PR/PRD.md (PRD actualizado)

2. DIAGNOSTICA el ambiente (rápido, 2 min):
   - Docker ps: `docker ps --filter "name=sgd-"`
   - Backend health: `curl.exe http://localhost:18000/api/v1/health`
   - BD limpia: `docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT * FROM verify_clean_state();"`
   - Branch actual: `git status --short && git log --oneline -3`

3. IDENTIFICA la siguiente tarea PENDIENTE:
   - Leer RADIOGRAFIA-TOTAL-18-06-2026.md §9 (Pendientes)
   - Identificar la primera tarea con prioridad P0/P1
   - Si la sesión anterior quedó a mitad, retomar ahí
   - Siempre preguntar al usuario: "Procedo con X? o preferís priorizar otra cosa?"

4. FORMA DE TRABAJO OBLIGATORIA:
   - Código limpio: sin code smells, sin debug leftovers, con type hints
   - Arquitectura modular: 1 archivo = 1 responsabilidad
   - Si hay cambios en backend: `docker restart sgd-backend`
   - Si hay cambios en frontend: `docker restart sgd-frontend` (o esperar HMR)
   - Validar con Chrome MCP (take_snapshot + take_screenshot) para UI
   - Validar con pytest para backend: `cd backend && .venv\Scripts\python -m pytest tests/`
   - Validar persistencia: F5 reload y verificar que el estado se mantenga
   - Probar múltiples escenarios (no solo el feliz)
   - Usar `scripts\restore_clean_state.bat` para volver a BD limpia

5. AL FINALIZAR LA SESIÓN (antes de cerrar):
   a) Hacer commit atómico con conventional commit
   b) Actualizar ESTADO.md (marcar tareas completadas)
   c) Actualizar BITACORA.md (agregar entrada de sesión)
   d) Actualizar DECISIONES.md (si hubo nuevas decisiones)
   e) Actualizar PRD.md (si cambió el alcance)
   f) Actualizar RADIOGRAFIA-TOTAL.md (si cambió la estructura)
   g) Reportar resumen al usuario

6. REGLAS DURAS:
   - No asumas victoria sin evidencia visual + BD + persistencia + tests
   - No inventes datos — la BD es la única fuente de verdad
   - No uses mocks del frontend en backend
   - Toda mutación pasa por API y deja audit_log
   - Si te trabas >15 min, salir del loop y consultar
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

## Orden de lectura de archivos (para IA)

1. `docs/PR/RADIOGRAFIA-TOTAL-18-06-2026.md` — radiografía completa
2. `docs/PR/INICIO-SESION.md` — este archivo
3. `docs/PR/BITACORA.md` — última sesión
4. `docs/PR/ESTADO.md` — progreso actual
5. `docs/PR/DECISIONES.md` — ADRs activos
6. `docs/PR/PRD.md` — PRD actualizado
