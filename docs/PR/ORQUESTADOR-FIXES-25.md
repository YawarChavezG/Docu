# ORQUESTADOR — Validación de Fixes Sesión 25

> **Prompt maestro para retomar el trabajo de validación de los 22 fixes de sesión 25 en una nueva sesión de opencode.**
> **Última actualización:** 2026-06-18 (cierre de Issue 1.1).
> **Próximo fix a atacar:** Issue 4.3 (ychavez sin Área en Mi Perfil).

---

## Cuando abras la nueva sesión, pegá este prompt:

```
Actua como Tech Lead senior del proyecto COFAR SGD. Tu trabajo: validar uno por uno
los fixes de la sesion 25 que ya fueron mergeados a codigo pero el cliente reporto
como "no del todo bien aplicados".

Lee en este orden:
  1. docs/PR/ORQUESTADOR-FIXES-25.md  (este archivo, panorama y forma de trabajo)
  2. docs/PR/FIXES-SESION-25.md        (los 22 fixes, con RESUELTO marcado en los validados)
  3. docs/PR/INICIO-SESION.md          (ritual de inicio, atajos, plan de avance)
  4. docs/PR/ESTADO.md                 (estado REAL del codigo)
  5. docs/PR/DECISIONES.md             (ADRs, ultimos 5)

Identifica el primer fix SIN "RESUELTO" en FIXES-SESION-25.md.
Ese es el fix que debes validar. NO empieces con cualquier otro.

Forma de trabajo (obligatoria, no asumas victoria sin evidencia):
  1. Pre-checks: docker ps, curl /health, BD limpia (verify_clean_state).
  2. Leer el codigo del fix (frontend + backend) ANTES de probar.
  3. Reproducir el escenario ORIGINAL con Chrome MCP (login, navegacion, accion).
  4. Validar visualmente (take_snapshot o take_screenshot).
  5. Validar en BD con psql (persistencia, no solo UI).
  6. Si el fix involucra varios casos, simular TODOS los escenarios
     (crear/actualizar/cancelar/persistir tras refresh) y validar cada uno.
  7. Si valida OK: reportar al usuario como lo validaste + como lo puede validar el,
     y ESPERAR su OK antes de continuar.
  8. Si valida FAIL: analizar codigo, hipotetizar causa raiz, aplicar correccion
     minima, re-validar end-to-end, recien reportar.
  9. Cuando el usuario apruebe: agregar "RESUELTO" arriba del fix en
     FIXES-SESION-25.md, ejecutar restore_clean_state.bat para limpiar BD,
     hacer commit atomico, y pasar al siguiente fix.

Estado actual: Issue 1.1 (Ausencia con motivo != vacaciones) RESUELTO.
Pendientes: 21 fixes (siguiente: 4.3).
```

---

## Forma de trabajo en detalle

### Stack y credenciales
- Frontend: `http://localhost:8080` (Nginx) o `http://localhost:5173` (Vite dev)
- Backend: `http://localhost:18000/api/v1/...` (FastAPI)
- BD: `postgresql://sgd:sgd_dev_only_change_in_prod@localhost:25432/sgd`
- 5 usuarios locales para login (BD Local): admin_local, eto_test, elaborador_revisor, elab._revisor_aprob., visualizador_cl (password: `cofar.2026`, excepto admin_local: `admin.2026`)
- aromero (id=1) es usuario AD, requiere `auth_source: "cofar"` con password real del AD

### Pre-flight (antes del primer fix)
1. `docker ps --filter "name=sgd-"` → 8 servicios Up
2. `curl.exe -s http://localhost:18000/api/v1/health` → `{"status":"ok","database":"ok"}`
3. `docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT * FROM verify_clean_state();"` → audit_log=0 esperado
4. **Si nginx da 502**: `docker restart sgd-nginx` (recarga DNS de containers tras stop/start)

### Trucos de Chrome MCP que aprendimos en Issue 1.1
- `x-model` de Alpine NO se actualiza con `dispatchEvent(new Event('input'))` para `<input type="date">` ni para checkboxes. **Workaround:** setear el state Alpine directamente con `Alpine.$data(root).variable = valor`.
- Para `<select>`, el match por `value` SÍ funciona bien.
- Después de hacer click en un botón que dispara un POST, el snapshot puede tener uids viejos (Alpine re-renderiza). Hacer `take_snapshot` antes del próximo click.
- Para evitar `confirm()` del browser: `window.confirm = () => true;` antes del click.

### Validación end-to-end (NO skip ningún paso)
- **Visual**: `take_snapshot` o `take_screenshot` y verificar texto exacto
- **BD**: query a la tabla afectada + tabla relacionada (ej: `usuarios.ausente` cuando se crea ausencia)
- **Audit**: si la acción involucra mutación, verificar que `audit_log` registre con `detalles` antes/después
- **Persistencia**: hacer `navigate_page type=reload` y reabrir el modal/form, verificar que sigue
- **Tests pytest** (si existen): correr y validar 100% PASS

### Reporte al usuario (template)
```
# 🟢/🟠/🔴 Issue X.Y — [VALIDADO EXITOSAMENTE / FALLO + fix aplicado]

## Lo que hice
1. [paso]
2. [paso]
3. [paso]

## Validación visual (Chrome MCP)
- [elemento visible 1]
- [elemento visible 2]

## Validación en BD
[query + resultado]

## Validación con tests pytest (si aplica)
[nombre test] PASSED/FAILED

## Cómo podés validarlo vos
1. [paso manual]
2. [paso manual]

¿Doy OK y procedo a marcar como RESUELTO + commit + restore?
```

### Al cerrar sesión
1. Agregar `✅ RESUELTO (sesión N)` arriba del fix en FIXES-SESION-25.md
2. `scripts\restore_clean_state.bat` (limpia BD al estado del snapshot)
3. `git add -A` + `git commit -m "fix(docs+restore): Issue X.Y RESUELTO + BD clean state"`
4. Actualizar `docs/PR/ORQUESTADOR-FIXES-25.md` con el nuevo "próximo fix"

---

## Estado de los 22 fixes

| # | Issue | Sev | Estado | Sesión |
|---|---|---|---|---|
| 1.1 | Ausencia motivo!=vacaciones NO marca ausente | 🟠 | ✅ **RESUELTO** | 28 |
| 4.3 | ychavez sin Área en Mi Perfil | 🟠 | ⏳ **PRÓXIMO** | — |
| 3.1 | Delegado obligatorio al asignar eto/revisor | 🟠 | pendiente | — |
| 4.1 | Botón Sincronizar AD 403 para ETO | 🟠 | pendiente | — |
| 10.1 | Política de Descargas hardcodeada | 🟠 | pendiente | — |
| 11.1 | Quitar Analista ETO del wizard paso 1 | 🟠 | pendiente | — |
| 11.2 | UI Reemplazo o baja + sub-bug | 🟠 | pendiente | — |
| 11.3 | Wizard no persiste en `documento_flujo` (NO-BUG) | 🟠 | pendiente | — |
| 4.2 | `soporteglpi` sin SAP se loguea | 🟡 | pendiente | — |
| 4.4 | Sync AD mapping `ad_info`→`area_id` | 🟡 | pendiente | — |
| 8.1 | Filtros activos/inactivos/ausentes | 🟡 | pendiente | — |
| 8.4 | REPORTES en Excel para elaboradores | 🟡 | pendiente | — |
| 5.1 | Selector Estados con 4 opciones | 🟡 | pendiente | — |
| 1.2 | Lista delegados corta | 🟡 | pendiente | — |
| 7.1 | Matriz ETO dropdown delegado solo ETO | 🟡 | pendiente | — |
| 2.1 | Performance login (Promise.all) | 🟡 | pendiente | — |
| 8.3 | Header "Área" | 🟢 | pendiente | — |
| 8.5 | KPI inactivos + desvinculados | 🟢 | pendiente | — |
| 9.1 | /plantillas vista tienda responsive | 🟢 | pendiente | — |
| 9.2 | Quitar bloque "IA — Recomendación" | 🟢 | pendiente | — |
| 6.1 | Ocultar columna SLUG en tipos_documento | 🟢 | pendiente | — |

**Progreso**: 1/22 (4.5%).

---

## Sesión de validación de Issue 1.1 (2026-06-18) — log completo

**Escenarios validados** (todos OK):
1. ✅ Crear ausencia con motivo `capacitacion` (no vacaciones) → `usuarios.ausente=true`
2. ✅ Actualizar vacaciones: cambiar `fecha_hasta` 18-06 → 23-06 → BD + historial + audit_log (antes/después)
3. ✅ Refresh (F5) post-update: persistencia verificada
4. ✅ Cancelar vacaciones: borrado lógico (`activo=false`), `usuarios.ausente=false`, audit_log DELETE
5. ✅ Refresh post-cancelar: persistencia de cancelación verificada

**Tests pytest**: 7/7 PASS en `tests/test_ausencias.py`

**Bug colateral detectado y arreglado**: `restore_clean_state.bat` no reiniciaba nginx → 502 Bad Gateway en proxy_pass tras `docker stop/start` del backend. Fix: agregar `docker restart sgd-nginx` al script.

**Hallazgo técnico**: el state Alpine no se bindea con `dispatchEvent(new Event('input'))` para inputs date/checkbox. Workaround: setear `Alpine.$data(root).variable` directamente.

**Commit pendiente al cierre de esta sesión**: orquestador + RESUELTO 1.1 + restore.
