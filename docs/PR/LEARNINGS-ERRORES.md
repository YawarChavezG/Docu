# LEARNINGS & ERRORES — COFAR SGD

> **Catálogo de errores cometidos, bugs encontrados, y lecciones aprendidas durante 29 sesiones de desarrollo.**
> **Propósito:** que ninguna IA cometa el mismo error dos veces.
> **Organización:** por categoría (frontend, backend, API, BD, Docker, lógica, tests, tooling).

---

## Categoría: Frontend (Alpine.js + Tailwind)

### F01 — Inline CSS vence a Tailwind classes
**Error:** `style="grid-template-columns:1fr"` inline tiene mayor especificidad que `class="sm:grid-cols-2"`.
**Síntoma:** Las clases responsive jamás se aplican. El layout siempre se ve en 1 columna.
**Fix:** Usar `class="grid grid-cols-1 sm:grid-cols-2 ... gap-4"` — puras clases Tailwind, cero inline.
**Referencia:** Issue 9.1 — `Plantillas.js:100`

### F02 — `x-show` sin `display:none` fallback
**Error:** `x-show="rolRequiereDelegado"` sin valor inicial — Alpine arranca con el elemento visible hasta que init() termina.
**Síntoma:** Se ve un flash del contenido antes de que Alpine lo oculte.
**Fix:** Doble control: `x-show="condicion" style="display:none" :style="condicion ? '' : 'display:none'"`.
**Referencia:** Sesión 24 F4 — `ProfileModal.js`

### F03 — Backticks en comentarios HTML dentro de template strings JS
**Error:** `` ` `` dentro de un comentario HTML `<!-- `texto` -->` que está dentro de una template string JS (`` `...` ``) cierra la template prematuramente.
**Síntoma:** SyntaxError en la consola: `Unexpected identifier 'analistas'`.
**Fix:** Usar comillas simples dentro de comentarios HTML cuando están dentro de template strings JS: `<!-- texto 'variable' aqui -->`.
**Referencia:** ADR-064 — `Parametrizacion.js:1878`

### F04 — `dispatchEvent(new Event('input'))` NO funciona con Alpine + `<input type="date">` ni checkboxes
**Error:** Alpine `x-model` no detecta eventos `input` disparados manualmente en inputs date o checkbox.
**Síntoma:** El state de Alpine no se actualiza aunque el input visualmente cambie.
**Fix:** Setear el state Alpine directamente: `Alpine.$data(root).variable = valor`.
**Referencia:** Sesión 28 — hallazgo durante validación de ausencias

### F05 — `<select>` con `x-model`: el match por `value` SÍ funciona
**Lección:** A diferencia de date/checkbox, los select reaccionan correctamente a cambios programáticos de value.
**Referencia:** Sesión 28

### F06 — `confirm()` nativo rompe la UX
**Error:** `confirm()` del browser no se puede estilizar, no muestra contexto, y bloquea el hilo.
**Fix:** Usar modal personalizado (ej: `ConfirmImpersonateModal.js`, `ConfirmDelegadoModal.js`) con `z-index: 8600`.
**Referencia:** ADR-062 — Sesión 27

### F07 — Template string JS con Alpine: NO usar `{#each}` ni `{#if}`
**Lección:** Alpine.js usa `x-for` y `x-if`, no Handlebars/Mustache. Usar `template x-for` o `template x-if`.
**Referencia:** Sesión 10.1 — Issue 10.1

### F08 — `api.js` NUNCA debe modificar `API_BASE`
**Error:** `normalizePath()` removía el prefijo `/api/v1` del path.
**Síntoma:** 404 en todas las requests.
**Fix:** Dejar `API_BASE` intacto. No normalizar paths que ya vienen con prefijo.
**Referencia:** Sesión 7 bug #1

### F09 — Shape de datos del template debe coincidir con el backend
**Error:** El template usaba `g.areas.length` pero el backend retorna `areas_count`.
**Síntoma:** `undefined.length` → TypeError silencioso.
**Fix:** Mapear response en el frontend: `areas_count: g.areas_count ?? 0`.
**Referencia:** Sesión 7 bug #3

### F10 — Data mock NO debe mezclarse con API real
**Error:** Se declaró "completo" un refactor que dejó referencias huérfanas a `data/parametrosSistema.js`.
**Síntoma:** 10+ errores en consola, páginas que no cargan.
**Fix:** Validar CADA tab individualmente, no asumir que porque una funciona todas funcionan.
**Referencia:** Sesión 7 — lección crítica

### F11 — `Promise.all` con requests que pueden fallar requiere `.catch()`
**Error:** Si una request en `Promise.all` falla (ej: 403), toda la promesa se rechaza y ninguna respuesta se procesa.
**Síntoma:** El modal de perfil no carga si la lista de delegados da error.
**Fix:** Agregar `.catch(() => [])` a cada promesa individual dentro del array.
**Referencia:** Issue 2.1 — `ProfileModal.js`

---

## Categoría: Backend (FastAPI + SQLAlchemy)

### B01 — `AsyncSession` NO es Pydantic field
**Error:** Usar `current_user: Usuario = Depends(require_eto_or_admin)` con `response_model=...` causa error 500 porque `AsyncSession` no es serializable.
**Síntoma:** 500 Internal Server Error sin mensaje claro.
**Fix:** Llamar `await require_eto_or_admin(request, db)` DENTRO del endpoint, NO como `Depends()`.
**Referencia:** Sesión 6 bug #1, repetido en R2-PLAN §5.1

### B02 — `/{user_id}` genérico DEBE ir al final del router
**Error:** Tener `GET /usuarios/{user_id}` antes de `GET /usuarios/export` hace que `user_id="export"` capture la ruta de export.
**Síntoma:** Export devuelve 422 o datos de un usuario inexistente.
**Fix:** Rutas específicas (`/export`, `/sync-ad`) primero, `/{user_id}` al final.
**Referencia:** Sesión 6 bug #8

### B03 — `expire_on_commit=True` invalida `selectinload` (MissingGreenlet)
**Error:** Después de `await db.commit()`, las relaciones lazy-load dan MissingGreenlet porque la sesión expiró.
**Síntoma:** `MissingGreenletError` al acceder a `usuario.roles` post-commit.
**Fix:** Hacer un nuevo query con `selectinload` post-commit, o usar `await db.refresh(objeto)`.
**Referencia:** Sesión 6 bug #7

### B04 — `write_audit` + `db.delete` + doble commit no escribe audit
**Error:** Hacer `db.delete(obj)`, `commit()`, `write_audit()`, `commit()` — el segundo commit no persiste porque la transacción ya cerró.
**Síntoma:** Audit log no se escribe.
**Fix:** `write_audit()` + `db.delete()` + un solo `db.commit()` (atómico). Si la operación falla, el audit NO se escribe.
**Referencia:** Sesión 6 bug #5, ADR-014

### B05 — PK de `ConfiguracionGlobal` es `clave` (str), no `id`
**Error:** Usar `cfg.id` en el audit_log cuando la PK es `clave`.
**Síntoma:** AttributeError: 'ConfiguracionGlobal' object has no attribute 'id'
**Fix:** Usar `recurso_id=cfg.clave` o `None` y poner la clave en `detalles`.
**Referencia:** Sesión 6 bug #4

### B06 — SQLAlchemy 2.0 NO acepta `description=` en `String()`/`Text()`
**Error:** `String(100, description="mi campo")` — `description` no es un kwarg de `String` en SQLAlchemy 2.0.
**Síntoma:** TypeError al importar el modelo.
**Fix:** Quitar `description=` de todas las columnas.
**Referencia:** Sesión 5 bug #1

### B07 — `cascade="all, delete-orphan"` en `Gerencia.areas` es incompatible con borrado lógico
**Error:** Si se hace DELETE físico desde el ORM (aunque no se use), se borran áreas hijas.
**Síntoma:** Pérdida de datos si alguien hace `db.delete(gerencia)`.
**Fix:** Usar borrado lógico siempre (`activo=False`). No hacer DELETE físico.
**Referencia:** Bug B1, sesión 6

### B08 — `areas.sigla` UNIQUE global impide re-crear área tras borrado lógico
**Error:** `UniqueConstraint('sigla')` global — si se "revive" un área con misma sigla en otra gerencia, da IntegrityError.
**Síntoma:** 409 Conflict al hacer PATCH activo=True.
**Fix:** `UniqueConstraint('gerencia_id', 'sigla')` compuesto. Migración 010.
**Referencia:** ADR-015, sesión 6

### B09 — Modelo `reemplaza_documento_ids` era `list[int]` pero frontend envía strings
**Error:** El modelo SQLAlchemy esperaba `list[int]` pero el frontend envía códigos como `"CC-3-005/00"`.
**Síntoma:** 422 Validation Error al enviar wizard.
**Fix:** Cambiar a `list[str]` (JSONB acepta cualquier tipo).
**Referencia:** Issue 11.3, sesión 25

### B10 — Area_mapping false positive: "cc" matcheaba en "direccion"
**Error:** El match por subsecuencia encontraba "cc" dentro de "direccion".
**Síntoma:** Asignación incorrecta de área_id.
**Fix:** Match por PALABRA COMPLETA (split por espacios), no por subsecuencia.
**Referencia:** Issue 4.4, sesión 25

### B11 — Filtro SAP en login on-demand faltaba (solo sync-ad lo tenía)
**Error:** `sync_ad` filtraba por `postalCode` pero `login on-demand` no.
**Síntoma:** Usuarios sin SAP se logueaban y se creaban en BD.
**Fix:** `ldap_get_user_by_samaccountname` retorna `None` si no tiene `postalCode`.
**Referencia:** Issue 4.2, sesión 25

---

## Categoría: API / Endpoints

### A01 — No usar `Depends()` con helpers que necesitan `request` y `db`
**Error:** `require_eto_or_admin` usa `request` y `db` como argumentos, no como dependencias inyectables.
**Síntoma:** 500 error.
**Fix:** Llamar manualmente dentro del endpoint: `user = await require_eto_or_admin(request, db)`.
**Ver:** B01

### A02 — Las rutas específicas van antes que las genéricas
**Error:** Ver B02.
**Regla:** Orden dentro de cada router: rutas fijas (`/export`, `/sync-ad`) → rutas con parámetro (`/{id}`).

### A03 — Los enums en schemas Pydantic deben coincidir exactamente con los del modelo
**Error:** Schema usa `ContextoEstado.PROCESO` pero el modelo tiene `ContextoEstado.PROCESO` — si difieren en case o valor, da 422.
**Síntoma:** ValidationError al hacer POST/PATCH.
**Fix:** Reutilizar los mismos enums del modelo en los schemas.

---

## Categoría: Base de Datos (PostgreSQL)

### D01 — `SELECT FOR UPDATE` async con SQLAlchemy 2.0 puede dar MissingGreenlet
**Error:** El lock pesimista en async session requiere manejo cuidadoso.
**Síntoma:** MissingGreenletError.
**Fix:** Usar `pg_try_advisory_xact_lock(hashtext(...))` como fallback portable.
**Referencia:** R2-PLAN §3.5, `correlativo_service.py`

### D02 — JSONB con SQLAlchemy async requiere `JSON().with_variant(JSONB(), "postgresql")`
**Error:** Usar `JSONB` directamente no funciona con SQLite en tests.
**Síntoma:** Test falla porque SQLite no tiene JSONB.
**Fix:** Usar `JSON().with_variant(JSONB(), "postgresql")` (patrón de `audit_log.py`).
**Referencia:** R2-PLAN §5.2 R2

### D03 — Alembic autogenerate a veces no captura CHECK constraints custom
**Error:** `CHECK (vigencia != 'VENCIDO' OR estatus IN ('APROBADO', 'OBSOLETO'))` no se genera automáticamente.
**Síntoma:** Migración generada no incluye el CHECK.
**Fix:** Escribir CHECK constraints manualmente en la migración, no en el modelo.
**Referencia:** R2-PLAN §5.2 R3

### D04 — DROP TABLE con CASCADE rompe seeds que importan la tabla
**Error:** Se eliminó `usuario_modulos` con CASCADE pero 3 scripts seed la importaban.
**Síntoma:** ImportError en seeds (B7, P0).
**Fix:** Actualizar los 3 scripts seed antes de deployar a QAS fresh-install.
**Referencia:** ADR-059, sesión 26

---

## Categoría: Docker / Infraestructura

### X01 — Puerto 15432 da error de binding en Docker Desktop sobre Windows
**Error:** El puerto 15432 no se puede bindear en Windows (conflicto con algún servicio del SO).
**Síntoma:** `Error response from daemon: port is already allocated`.
**Fix:** Usar 25432 para PostgreSQL y 26379 para Redis. Documentado en `.env` como default.
**Referencia:** Sesión 1

### X02 — DNS corporativo NO resuelve desde contenedor Docker (solo IP directa)
**Error:** `rodc.cofar.com.bo` no se resuelve desde dentro del contenedor aunque sí desde el host.
**Síntoma:** LDAP bind falla con NXDOMAIN.
**Fix:** Usar IP directa `172.16.10.17` en `LDAP_SERVER`. Configurar DNS explícito en docker-compose: `dns: [172.16.10.50, 172.16.10.51, 8.8.8.8]`.
**Referencia:** ADR-013

### X03 — nginx da 502 Bad Gateway tras docker stop/start del backend
**Error:** Nginx cachea la IP del backend. Al reiniciar el backend, nginx intenta con la IP vieja.
**Síntoma:** 502 Bad Gateway después de `docker restart sgd-backend`.
**Fix:** `docker restart sgd-nginx` después de reiniciar backend.
**Referencia:** Sesión 28

### X04 — Volumen Docker vs bind mount: archivos en host NO se ven en container
**Error:** `backend/storage/plantillas/` es un named volume. Copiar archivos al host no los hace visibles dentro del container.
**Síntoma:** Plantillas no aparecen en el listado.
**Fix:** Usar `docker cp` para copiar archivos al volume dentro del container.
**Referencia:** Sesión 24 E1, `start-stack-des.bat`

### X05 — `--reload` de uvicorn puede dejar procesos zombies en el container
**Error:** Con `--reload` activo, cambios en el código reinician uvicorn pero a veces quedan procesos hijos.
**Síntoma:** El container responde lento, consume más memoria.
**Fix:** Usar `exec uvicorn ...` en lugar de solo `uvicorn ...` en el CMD. En QAS no hay `--reload`.

### X06 — Healthchecks en compose: asumir binarios disponibles es trampa
**Error:** Spec de healthcheck con `curl` en container `node:22-alpine` → `curl: not found`. Spec con `ps aux` en `python:3.12-slim` → `ps: not found`. Spec con `service nginx status` en `nginx:1.27-alpine` → `service: not found` (Alpine usa OpenRC, no SysV init).
**Síntoma:** Healthchecks siempre unhealthy aunque el servicio esté funcionando.
**Fix:** Usar comandos Alpine-safe según imagen base:
- node:22-alpine → `wget -q --spider http://localhost:PORT` o `nc -z localhost PORT` (no curl, sí wget/nc).
- python:3.12-slim → `xargs -0 echo < /proc/1/cmdline | grep -q 'patron'` o `pgrep -f patron` (no ps aux).
- nginx:1.27-alpine → `pgrep -f 'nginx: master'` (no service).
- *:alpine genérico → preferir leer `/proc/1/cmdline` (siempre disponible) sobre `ps`.
**Regla:** Antes de escribir un healthcheck, validar con `docker exec <container> sh -c 'which <tool>'` que el binario existe. Si no, usar `/proc/1/cmdline` o instalar el paquete en el Dockerfile.
**Referencia:** ADR-067, sesión 32. Afectó a 3/4 healthchecks de QAS compose v1.1.0-qas.

### X07 — TZ env var: se pasa OK pero Go y Node no la aplican a `date(1)` automáticamente
**Error:** Setear `TZ=America/La_Paz` en mailhog (Go) o frontend (Node) → `docker exec ... date` muestra `UTC` aunque el tiempo (epoch) sea correcto.
**Causa:** Go no llama `time.LoadLocation` por default. Node respeta `process.env.TZ` solo si está seteada antes del primer import que cachea zona. El PID 1 de mailhog es el binario Go, no una shell.
**Síntoma:** Confusión del operador al validar TZ con `docker exec ... date`.
**Fix:** TZ funciona para todos los efectos prácticos (logs Python, timestamps BD, nginx). NO intentar hacer que `date(1)` muestre `-04` en mailhog/frontend — requeriría rebuild de las imágenes base o instalar `tzdata`. Documentar como limitación.
**Verificación:** `docker exec <container> sh -c 'date; echo "TZ=$TZ"'` muestra tiempo correcto + env var seteada.
**Referencia:** ADR-066, sesión 32.

### X08 — `localhost` en healthcheck: puede resolver a `::1` (IPv6) si la imagen no tiene `getent`
**Error:** `wget -q --spider http://localhost:5173` falla con "Connection refused" aunque el servicio esté escuchando en `0.0.0.0:5173` (IPv4).
**Causa:** El resolver DNS interno de Docker (127.0.0.11) puede devolver `::1` para `localhost` en lugar de `127.0.0.1`, especialmente si el container no tiene `getent` o si /etc/hosts está en formato reducido. El binario (Vite/Go) escucha en IPv4, no IPv6.
**Síntoma:** Healthcheck unhealthy aunque `curl 127.0.0.1:5173` funcione desde dentro del container.
**Fix:** Usar SIEMPRE `127.0.0.1` (o `0.0.0.0`) en healthchecks de compose, NUNCA `localhost`. El test rápido: `docker exec <container> sh -c 'wget -q -O - http://127.0.0.1:PORT'` vs `http://localhost:PORT`.
**Verificación empírica (sesión 32):**
```
docker exec sgd-qas-frontend wget -q -O - http://127.0.0.1:5173 | head -3   # OK (devuelve HTML)
docker exec sgd-qas-frontend wget -q -O - http://localhost:5173 | head -3    # Connection refused
```
**Referencia:** Sesión 32, fix del healthcheck del frontend.

---

## Categoría: Lógica de negocio

### L01 — Ausencias con fechas futuras NO marcan ausente
**Error:** El cliente reportó que "solo vacaciones marca ausente". La causa real era que las fechas eran futuras.
**Síntoma:** `usuario.ausente=false` aunque haya una ausencia registrada.
**Diagnóstico:** El helper `_vigente_set_usuario_ausente` cuenta ausencias con `fecha_desde<=hoy AND fecha_hasta>=hoy`. Si la ausencia es futura, no es vigente → `ausente=false`. Comportamiento correcto.
**Referencia:** Issue 1.1 (NO-BUG)

### L02 — Wizard crea documento al firmar, no al hacer click en Siguiente
**Decisión:** El `POST /documentos` solo ocurre en `firmarEnviar()`, no en `nextPaso()`. Esto evita documentos huérfanos.
**Síntoma esperado:** Si el usuario cierra el navegador antes de firmar, no queda ningún documento en BD.
**Referencia:** Sesión 23 A2

### L03 — Roles: 5 en total, con delegado requerido para 3
**Roles:** ADMIN (no requiere), ETO (sí), ELABORADOR-REVISOR (sí), ELABORADOR-REVISOR-APROBADOR (sí), VISUALIZADOR (no).
**Regla:** Si el rol requiere delegado y no hay delegado asignado, mostrar "PENDIENTE" pero no bloquear.

### L04 — Código de documento NUNCA debe cambiar
**Regla:** Una vez asignado, el código `CC-3-005` es inmutable. Solo cambia la versión.
**Validación:** `UNIQUE(area_id, tipo_documento_id, correlativo)` en BD.

---

## Categoría: Tests (pytest)

### T01 — SQLite in-memory NO soporta JSONB, enums PostgreSQL, ni `with_for_update()`
**Error:** Usar SQLite para tests cuando el modelo usa `JSONB`, `ENUM` de PostgreSQL, o `SELECT FOR UPDATE`.
**Síntoma:** Tests fallan con errores de sintaxis SQL.
**Fix:** Usar `JSON().with_variant(JSONB(), "postgresql")` para JSONB, `TEXT` con check constraints para enums, y mockear `correlativo_service` para tests. O usar `testcontainers` con PostgreSQL real.
**Referencia:** conftest.py, R2-PLAN §5.2

### T02 — Tests que dependen del orden de ejecución pueden fallar intermitentemente
**Error:** `test_usuarios.py` espera 403 pero retorna 200 si otro test creó un usuario admin antes.
**Síntoma:** Tests pasan en aislamiento pero fallan en suite completa.
**Fix:** Usar `@pytest.mark.usefixtures("seed_catalogos")` y fixtures que garanticen estado conocido.

### T03 — Falla preexistente NO debe ignorarse sin documentar
**Error:** 11 tests fallan por refs a enums/campos antiguos. Se documentaron como "preexistentes" pero nunca se fixearon.
**Regla:** Cada test fallido debe tener un issue o un comentario con root cause y plan de fix.
**Referencia:** Sesiones 24-29

### T04 — Tests con campos renombrados/rotos deben actualizarse al refactor de schema
**Error:** Tests creados con `codigo_doc` (int, campo viejo de `TipoDocumento` pre-sesion 13) seguian construyendo instancias con ese kwarg despues de que el modelo lo eliminara. SQLAlchemy lanza `TypeError: 'codigo_doc' is an invalid keyword argument for TipoDocumento`.
**Síntoma:** Tests fallan con TypeError en `db_session.add(TipoDocumento(...))`.
**Fix:** Adaptar tests al nuevo schema: `codigo=int` + `slug=str MAYUSCULAS` + `nombre=str`. NO re-añadir el campo viejo al modelo "por compat".
**Referencia:** Sesion 31, `test_tipos_documento.py` (4 tests).

### T05 — Tests con enums renombrados deben actualizarse al refactor
**Error:** Tests usaban `CodigoPlantilla.NUEVA_TAREA` (enum antiguo pre-sesion 13) despues de que el catalogo se renombrara a 11 codigos nuevos (ASIG_REVISION, ASIG_APROBACION, etc.).
**Síntoma:** `AttributeError: type object 'CodigoPlantilla' has no attribute 'NUEVA_TAREA'`.
**Fix:** Usar uno de los codigos vigentes (`ASIG_REVISION` es el primero). NO añadir el viejo al enum "por compat".
**Referencia:** Sesion 31, `test_email_templates.py` (3 tests).

### T06 — Tests deben reflejar comportamiento actual, no el "ideal" historico
**Error:** Test `test_listar_usuarios_eto_403` esperaba 403 para ETO, pero el endpoint se relajo intencionalmente en sesion 9 para admitir ETO/ADMIN/roles-delegables (ver `usuarios.py:245-249`).
**Síntoma:** `assert 200 == 403`.
**Diagnostico:** El test describia el comportamiento original. La relajacion fue intencional y esta documentada. El test quedo desactualizado.
**Fix:** Renombrar test a `test_listar_usuarios_eto_200` y actualizar aserciones. NO revertir la relajacion del endpoint.
**Referencia:** Sesion 31, `test_usuarios.py` (1 test).

### T07 — Búsqueda en catálogos: preferir tolerante a estricto entre test y prod
**Error:** `envio_service.py` busca `Estado.codigo == "REVISION"` (codigo post data-migration B3 sesion 23). Pero el conftest de pytest tiene `EN_REVISION` (codigo pre-B3) por compat con `test_bandeja.py:65` que hardcodea el id=2.
**Síntoma:** Tests fallan con `500 "Estado REVISION no encontrado en catalogo"`.
**Fix:** Buscar ambos codigos: `Estado.codigo.in_(["REVISION", "EN_REVISION"])`. Produccion sigue encontrando "REVISION" (id=7), test encuentra "EN_REVISION" (id=2). Es una mejora defensiva: si alguien migra el codigo en el futuro, el servicio sigue funcionando.
**Regla:** Cuando codigo de test diverge de codigo de produccion por una data-migration historica, preferir lookup tolerante en el servicio antes que reescribir el conftest (que cascadearia a otros tests).
**Referencia:** Sesion 31, `envio_service.py`.

---

## Categoría: Tooling / PowerShell

### P01 — PowerShell aliasa `curl` a `Invoke-WebRequest`
**Error:** `curl` en PowerShell no es curl.exe. `Invoke-WebRequest` tiene sintaxis y output diferente.
**Síntoma:** Las requests fallan o el output no es parseable.
**Fix:** Usar SIEMPRE `curl.exe` en PowerShell.
**Referencia:** AGENTS.md

### P02 — JSON inline en PowerShell falla por comillas
**Error:** `curl.exe -d '{"key":"value"}'` — PowerShell convierte las comillas simples.
**Síntoma:** El backend recibe `{key:value}` sin comillas.
**Fix:** Usar archivo: `echo '{"key":"value"}' > tmp.json` y luego `--data-binary @tmp.json`.

### P03 — `&&` NO funciona en PowerShell como en bash
**Error:** `cmd1 && cmd2` no es válido en PowerShell (5.1).
**Síntoma:** Error de sintaxis.
**Fix:** Usar `cmd1; if ($?) { cmd2 }`.
**Referencia:** AGENTS.md

### P04 — Vite HMR cache agresivo a veces no refleja cambios en JS
**Error:** Alpine `Alpine.data()` registrado en `init()` no se actualiza con HMR si el componente ya fue registrado.
**Síntoma:** Cambios en JS no se ven incluso tras F5.
**Fix:** `docker restart sgd-frontend` o borrar `node_modules/.vite` dentro del container.
**Referencia:** Sesión 7

---

## Categoría: Chrome MCP (testing)

### M01 — Tomar snapshot DESPUÉS de cada click que dispara POST
**Error:** Alpine re-renderiza el DOM después de un POST. Los uids del snapshot anterior quedan inválidos.
**Síntoma:** Click en uid antiguo falla (elemento no encontrado).
**Fix:** Siempre hacer `take_snapshot` fresco antes del próximo click.

### M02 — `window.confirm = () => true;` antes de click en botón destructivo
**Error:** `confirm()` nativo bloquea el hilo de Chrome MCP.
**Síntoma:** El test se cuelga sin respuesta.
**Fix:** Ejecutar `window.confirm = () => true;` via evaluate_script antes del click.

### M03 — Para radio buttons custom, NO usar click en label
**Error:** Labels custom con `:style` no disparan el change del radio.
**Síntoma:** Click en el label no cambia el valor.
**Fix:** Usar `evaluate_script` con `document.querySelector('input[value="X"]').click()` directo.

### M04 — Verificar 4 breakpoints responsive NO solo desktop
**Regla:** Para issues responsive, verificar:
1. Mobile (< 640px): `chrome-devtools_resize_page width=375`
2. Tablet (768px): `width=768`
3. Desktop (1024px): `width=1024`  
4. Large (1280+): `width=1280`

### M05 — Usar computedStyle, no solo snapshot, para verificar layout
**Regla:** `getComputedStyle(el).gridTemplateColumns` es más confiable que la a11y tree (que siempre lista secuencial).
**Fix:** Usar `chrome-devtools_evaluate_script` con función que retorne estilos computados.
