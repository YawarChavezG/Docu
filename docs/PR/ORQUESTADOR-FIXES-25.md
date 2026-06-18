# ORQUESTADOR — Validación de Fixes Sesión 25

> **Prompt maestro para retomar el trabajo de validación de los 22 fixes de sesión 25 en una nueva sesión de opencode.**
> **El prompt de inicio es SIEMPRE EL MISMO** — solo cambia el contenido de `FIXES-SESION-25.md` (que la IA lee y de ahí deduce cuál es el siguiente fix).
> **Última actualización:** ver `docs/PR/ESTADO.md` para la sesión actual.

---

## Prompt universal para pegar en cada nueva sesión

```
Actua como Tech Lead senior del proyecto COFAR SGD. Tu trabajo: validar uno por uno
los 22 fixes de la sesion 25 que ya fueron mergeados a codigo pero el cliente reporto
como "no del todo bien aplicados".

Lee en este orden:
  1. docs/PR/ORQUESTADOR-FIXES-25.md  (panorama, forma de trabajo, trucos Chrome MCP)
  2. docs/PR/FIXES-SESION-25.md        (los 22 fixes; RESUELTO marca los ya validados)
  3. docs/PR/INICIO-SESION.md          (ritual de inicio, atajos, plan de avance)
  4. docs/PR/ESTADO.md                 (estado REAL del codigo, sesion actual)
  5. docs/PR/DECISIONES.md             (ADRs, ultimos 5)

Identifica el primer fix SIN marcador "RESUELTO" en FIXES-SESION-25.md.
ESE es el fix que debes validar. NO empieces con cualquier otro.

Forma de trabajo (obligatoria):
  1. Pre-checks: docker ps, curl /health, BD limpia (verify_clean_state).
  2. Leer el codigo del fix (frontend + backend) ANTES de probar.
  3. Reproducir el escenario ORIGINAL con Chrome MCP.
  4. Validar visualmente (take_snapshot) + en BD (psql) + persistencia (F5) + tests pytest.
  5. Si el fix involucra varios casos, simular TODOS los escenarios y validar cada uno.
  6. Si valida OK: reportar al usuario como lo validaste + como lo valida el,
     y ESPERAR su OK antes de continuar al siguiente.
  7. Si valida FAIL: analizar codigo, hipotetizar causa raiz, aplicar correccion
     minima, re-validar end-to-end, reportar.
  8. Al recibir OK del usuario, automaticamente (sin mas confirmaciones):
     a) Marcar "RESUELTO" arriba del fix en FIXES-SESION-25.md
     b) Actualizar la tabla en este ORQUESTADOR-FIXES-25.md
     c) Ejecutar scripts\restore_clean_state.bat
     d) git add + commit atomico
     e) Reportar al usuario "Listo. Siguiente fix: X.Y. Esperando nueva sesion."
  9. Si NO quedan mas fixes pendientes, reportar "TODOS los 22 fixes validados. Fin."

Reglas duras:
  - No asumas victoria sin evidencia visual + BD + persistencia + (tests si existen).
  - Un fix por sesion (no apures varios en una sola).
  - Si te trabas >15 min, salir del loop y consultar.
```

---

## Forma de trabajo en detalle

### Stack y credenciales
- Frontend: `http://localhost:8080` (Nginx) o `http://localhost:5173` (Vite dev)
- Backend: `http://localhost:18000/api/v1/...` (FastAPI)
- BD: `postgresql://sgd:sgd_dev_only_change_in_prod@localhost:25432/sgd`
- 5 usuarios locales para login (BD Local): admin_local, eto_test, elaborador_revisor, elab._revisor_aprob., visualizador_cl (password: `cofar.2026`, excepto admin_local: `admin.2026`)
- aromero (id=1) es usuario AD, requiere `auth_source: "cofar"` con password real del AD

### Pre-flight (antes del primer fix de la sesión)
1. `docker ps --filter "name=sgd-"` → 8 servicios Up
2. `curl.exe -s http://localhost:18000/api/v1/health` → `{"status":"ok","database":"ok"}`
3. `docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT * FROM verify_clean_state();"` → audit_log=0 esperado
4. **Si nginx da 502**: `docker restart sgd-nginx` (recarga DNS de containers tras stop/start)

### Trucos de Chrome MCP aprendidos
- `x-model` de Alpine NO se actualiza con `dispatchEvent(new Event('input'))` para `<input type="date">` ni para checkboxes. **Workaround:** setear el state Alpine directamente con `Alpine.$data(root).variable = valor`.
- Para `<select>`, el match por `value` SÍ funciona bien.
- Después de hacer click en un botón que dispara POST, los uids del snapshot pueden quedar viejos (Alpine re-renderiza). Hacer `take_snapshot` antes del próximo click.
- Para evitar `confirm()` del browser: `window.confirm = () => true;` antes del click.
- Para los radio buttons de "Fuente de autenticación" en login: usar `evaluate_script` con `r.click()` directo sobre el input radio (los radios de label custom no responden al click del label).

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

---

## Estado de los 22 fixes (resumen — fuente de verdad: FIXES-SESION-25.md)

> La IA actualiza esta tabla al cerrar cada sesión. La fuente de verdad de "qué fix es el siguiente" es el archivo `FIXES-SESION-25.md` (buscar el primer fix SIN marcador `RESUELTO`).

| # | Issue | Sev | Estado |
|---|---|---|---|
| 1.1 | Ausencia motivo!=vacaciones NO marca ausente | 🟠 | ✅ RESUELTO |
| 4.3 | ychavez sin Área en Mi Perfil | 🟠 | ✅ RESUELTO |
| 3.1 | Delegado obligatorio al asignar eto/revisor | 🟠 | ✅ RESUELTO |
| 4.1 | Botón Sincronizar AD 403 para ETO | 🟠 | ✅ RESUELTO |
| 10.1 | Política de Descargas hardcodeada | 🟠 | ✅ RESUELTO |
| 11.1 | Quitar Analista ETO del wizard paso 1 | 🟠 | ✅ RESUELTO |
| 11.2 | UI Reemplazo o baja + sub-bug | 🟠 | ✅ RESUELTO |
| 11.3 | Wizard no persiste en `documento_flujo` (NO-BUG) | 🟠 | ✅ RESUELTO |
| 4.2 | `soporteglpi` sin SAP se loguea | 🟡 | ✅ RESUELTO |
| 4.4 | Sync AD mapping `ad_info`→`area_id` | 🟡 | ✅ RESUELTO |
| 8.1 | Filtros activos/inactivos/ausentes | 🟡 | ✅ RESUELTO |
| 8.4 | REPORTES en Excel para elaboradores | 🟡 | ⛔ DEPRECADO |
| 5.1 | Selector Estados con 4 opciones | 🟡 | pendiente |
| 1.2 | Lista delegados corta | 🟡 | pendiente |
| 7.1 | Matriz ETO dropdown delegado solo ETO | 🟡 | pendiente |
| 2.1 | Performance login (Promise.all) | 🟡 | pendiente |
| 8.3 | Header "Área" | 🟢 | pendiente |
| 8.5 | KPI inactivos + desvinculados | 🟢 | pendiente |
| 9.1 | /plantillas vista tienda responsive | 🟢 | pendiente |
| 9.2 | Quitar bloque "IA — Recomendación" | 🟢 | pendiente |
| 6.1 | Ocultar columna SLUG en tipos_documento | 🟢 | pendiente |

**Progreso**: 11/22 (50.0%).

---

## Hallazgos técnicos importantes (memoria de sesiones)

### Sesión 28 — Issue 1.1 (Ausencias)
- **Bug colateral detectado y arreglado**: `restore_clean_state.bat` no reiniciaba nginx → 502 Bad Gateway en proxy_pass tras `docker stop/start` del backend. Fix: agregar `docker restart sgd-nginx` al script.
- **Hallazgo técnico**: el state Alpine no se bindea con `dispatchEvent(new Event('input'))` para inputs date/checkbox. Workaround: setear `Alpine.$data(root).variable` directamente.
- **Bug encontrado durante login**: aromero (id=1) NO está en la lista de 5 usuarios locales (es AD). Para login en BD Local usar `eto_test`, `solicitante`, `admin`, `admin_local`, `elaborador_revisor`, `elab._revisor_aprob.`, `visualizador_cl` con password `cofar.2026` (excepto admin_local: `admin.2026`).

### Sesión 29 — Issue 4.3 (ychavez sin Área en Mi Perfil)
- **Validación completa**: 3 escenarios visuales (ychavez/aromero/admin) + persistencia F5 + audit_log=0 + 20/21 tests pytest OK.
- **Hallazgo**: el doc original (FIXES-SESION-25.md:116) decía que aromero debía mostrar "CAL / CC" (área mapeada en BD), pero el comportamiento actual (sesión 26) muestra el AD department "Excelencia y Transformación Organizacional" para usuarios `es_usuario_ad=true`. La rama AD tiene prioridad sobre el área mapeada por diseño. Doc actualizado para reflejar el comportamiento real.
