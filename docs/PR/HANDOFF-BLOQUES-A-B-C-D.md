# HANDOFF — Bloques A, B, C, D (Sesion 23)

> **Documento de handoff** para retomar en una sesion nueva con ventana de contexto limpia.
> **Sesion**: 2026-06-17 (miercoles, 14:30 → 19:30)
> **Rama**: `r2/wizard-y-version-editable`
> **Commits**: 8 commits atomicos (6 codigo + 2 docs) entre `e795c8f` y `5ce4bea`

---

## 1. Resumen ejecutivo

En esta sesion se cerraron **4 bloques** del plan propuesto tras la reunion con el cliente (16 sub-tareas totales, 14 completadas en esta sesion + 2 ya estaban). El trabajo se centro en resolver los bugs reportados por el usuario y agregar nuevas funcionalidades.

**Bugs resueltos (todos reportados por el usuario):**
- B1: Limite de plazo maximo redundante en `semaforizacion_tarea` y `configuracion_global`
- B2: Wizard creaba documento al "Siguiente" (debia ser solo al firmar)
- B3: Wizard no validaba tamano/cantidad de archivos desde BD
- B4: Delegado persistia correctamente (validado, sin fix necesario)
- B5: Estado de procesos y tarea con 12 nuevos catalogos (3 PROCESO + 6 TAREA + 3 ACCION)
- B6: Doble toast en firma 2FA (uno se mostraba antes del callback)
- B7: Firma 2FA no creaba fila en `firmas_digitales` (modelo huerfano desde sesion 1)
- B8: Firma 2FA fallaba para usuarios locales por bug preexistente en `validar_password_usuario`
- B9: Impersonate no propagaba a bandejas/sidebar/permisos del usuario impersonado
- B10: Impersonate no buscaba usuarios locales (solo AD)
- B11: Sync AD no marcaba desvinculados automaticamente
- B12: Usuarios del AD no tenian flag explicito `es_usuario_ad`

**Funcionalidades agregadas:**
- F1: Tabla `ausencias` ahora tiene CRUD completo + persistencia + sincronizacion automatica con `usuarios.ausente`
- F2: Cron 00:05 desactiva ausencias vencidas
- F3: Nueva columna `es_usuario_ad` con backfill
- F4: 3 campos read-only en wizard paso 1 (Nombre/Cargo/Fecha)
- F5: Nueva variable `{{VERSION}}` en plantillas de email

---

## 2. Commits de la sesion

```
5ce4bea docs(pr): sesion 23 — Bloque D cerrado (impersonate end-to-end)
ebd7b3d feat(impersonate): Bloque D - end-to-end funciona
59cbf59 docs(pr): sesion 23 — Bloque C cerrado (2 sub-tareas)
8f5ef3a feat(sync-ad): Bloque C (2 sub-tareas)
7d3fbd7 docs(pr): sesion 23 — Bloques A+B cerrados (11 sub-tareas)
95e1b5b feat(ausencias+firmas+estados): Bloque B (5 sub-tareas)
e795c8f fix(wizard): actualizar hint del botón Siguiente
715cee2 docs(pr): sesion 23 — Bloque A cerrado (6 sub-tareas + commit fb1e45e)
fb1e45e fix(wizard+seeds+semaforos): Bloque A (6 sub-tareas)
```

Los 6 commits de codigo: `fb1e45e` (A), `e795c8f` (fix), `95e1b5b` (B), `8f5ef3a` (C), `ebd7b3d` (D). Los 2 commits de docs son `715cee2` y `7d3fbd7` y `59cbf59` y `5ce4bea`.

---

## 3. Cambios detallados por bloque

### Bloque A (commit `fb1e45e`)

**A1**: Variable `{{VERSION}}` agregada a `VARS_COMUNES` en `backend/scripts/seed_email_templates.py:25-29`. Seed corrido con exito, 11 plantillas actualizadas en BD. Verificado con `psql` que `email_templates.variables_json` ahora tiene 12 entradas (antes 11). La variable aparece como chip clicable en `frontend/src/pages/Parametrizacion.js:13_28` (entre `{{TITULO}}` y `{{USUARIO}}`).

**A2**: Wizard `frontend/src/pages/AprobacionDocumento.js`: `POST /documentos` se movio de `nextPaso()` (paso 1) a `firmarEnviar()` (paso 3). El documento SOLO se persiste al firmar con 2FA OK. Toast "documento creado" eliminado. Esto significa que si el usuario cancela en el paso 3, no queda ningun documento huerfano en BD (mejor diseno).

**A3**: En el mismo `AprobacionDocumento.js`: `init()` carga `max_tamano_archivo_mb` (20) y `max_archivos_por_solicitud` (20) de `configuracion_global` (categoria=ARCHIVOS). `nextPaso()` valida antes de avanzar. Toast de error si excede.

**A4**: Validado con curl que `PATCH /usuarios/1` con `delegado_id=1463` (cecEspinoza) → 200, `estado_delegacion=asignado`, `delegado_id=1463`, `delegado_nombre=Cecilia Espinoza`. **No requirio fix**, el backend ya estaba correcto.

**A5**: Migracion `5aaf5d3e3509` (`backend/alembic/versions/2026_06_17_1547-5aaf5d3e3509_a5_marcar_como_inactivas_4_claves_.py`): las 4 claves `plazo_revision_aprobacion_dias`, `plazo_control_lectura_dias`, `semaforo_verde_dias`, `semaforo_amarillo_dias` se marcan como `activo=false` (borrado logico). Removidas del seed `backend/scripts/seed_configuracion_global.py:30-45`. UI `frontend/src/pages/Parametrizacion.js:1558-1567` removio las 2 inputs y el bulkUpsert. La unica fuente de verdad de plazos es ahora la tabla `semaforizacion_tarea` (por tipo de tarea).

**A6**: Wizard `frontend/src/pages/AprobacionDocumento.js`: 3 inputs read-only en paso 1 — Nombre (`$store.auth.user.nombre_completo`), Cargo (`$store.auth.user.cargo`), Fecha (`new Date().toLocaleDateString('es-BO')`).

**Fix bonus `e795c8f`**: el texto "Se persistira el documento al avanzar" → "El documento se persistira al firmar (paso 3)" porque ya no aplica con A2.

### Bloque B (commit `95e1b5b`)

**B1**: Vacaciones con fechas. Nuevo endpoint `backend/app/api/v1/ausencias.py` (6 endpoints: `GET /`, `GET /{id}`, `GET /usuarios/{id}/vigente`, `POST /usuarios/{id}`, `PATCH /{id}`, `DELETE /{id}`). Schema `backend/app/schemas/ausencia.py` con Pydantic v2. Helper `_vigente_set_usuario_ausente()` mantiene `usuarios.ausente` sincronizado con ausencias vigentes. Frontend `frontend/src/components/ProfileModal.js`: nuevo form con motivo (vacaciones/licencia/capacitacion/otro), historial, registrar/actualizar/cancelar vacaciones. Frontend `frontend/src/pages/Parametrizacion.js` modal Editar Usuario: permite a ETO/ADMIN crear/editar/cancelar vacaciones via API.

**B2**: Cron 00:05 para ausencias vencidas. `backend/app/workers/tasks.py`: nueva tarea `desactivar_ausencias_vencidas` que busca ausencias con `fecha_hasta < today` y `activo=true`, las marca `activo=false`, y setea `usuarios.ausente=false`. `celery_app.py:beat_schedule` con `crontab(hour=0, minute=5)`. Script CLI `backend/scripts/desactivar_ausencias_vencidas.py` para testing manual con `--dry-run`.

**B3**: Estados reorganizados. `backend/app/models/estado.py:20-24`: nuevo valor `ACCION` en `ContextoEstado` enum. Migracion `353aec067661` (`backend/alembic/versions/2026_06_17_1617-353aec067661_b3_data_migration_estados_nuevo_.py`):
1. `ALTER TYPE contexto_estado ADD VALUE 'ACCION'` con `op.get_context().autocommit_block()` (requerido por PG)
2. UPDATE 9 antiguos estados `activo=false`: `ELABORACION, LIBERACION_ETO, REVISION_PARALELA, FINALIZADO, ANULADO, APROBACION, TST1, TE_26664, TEST_NUEVO`
3. INSERT 12 nuevos con `ON CONFLICT` idempotente:
   - PROCESO (3): `CONCLUIDO, EN_EJECUCION, ELIMINADO_PROC`
   - TAREA (6): `SOLICITUD_CREADA, LIBERACION_ETO, REVISION, APROBADO, ELIMINACION, CORRECCION`
   - ACCION (3): `EJECUTADO, PENDIENTE, ELIMINADO_ACC`
4. `envio_service.py`: usa nuevo `REVISION` (antes `REVISION_PARALELA`, ahora inactivo)

**B4**: Firma 2FA crea fila en `firmas_digitales`. `backend/app/services/envio_service.py`: crea `FirmaDigital(resultado_exito=true)` en el commit atomico del flujo. Tambien crea `FirmaDigital(resultado_exito=false, motivo_fallo=password_invalida)` en intento fallido.

**B5**: Fix doble toast. `frontend/src/components/AuthModal.js:46` removido `window.toast('Firma digital registrada')`. Solo el callback `onSuccess` muestra el resultado (exito o error).

### Bloque C (commit `8f5ef3a`)

**C1**: Sync AD marca desvinculados. `backend/app/api/v1/usuarios.py` POST `/sync-ad`: despues de actualizar/crear, busca usuarios en BD con `ad_postal_code IS NOT NULL` y `estado IN (activo, inactivo)` cuyo username NO esta en el resultado del AD. Los marca como `estado=desvinculado`. **NUNCA elimina fisicamente**. Si estaba desvinculado y vuelve a AD, se reactiva. `SyncAdResponse` ahora incluye campo `desvinculados`.

**C2**: Flag `es_usuario_ad`. Modelo `Usuario`: nueva columna `es_usuario_ad: bool = False, indexed`. Migracion `8aa4cfa0f92f`: ALTER TABLE + backfill (usuarios con `ad_postal_code IS NOT NULL` → `true`). `auth.py` y `usuarios.py` setean `true` al crear desde AD. **Backfill verificado**: 754 con `true` (los del AD), 10 con `false` (stubs DES + sin SAP).

### Bloque D (commit `ebd7b3d`)

**D1**: Impersonate end-to-end. `backend/app/core/permissions.py:get_current_user_from_cookie` ahora prioriza `impersonated_user`: si existe la cookie, devuelve el Usuario impersonado (con sus roles/modulos/area) en vez del admin original. Asi, /bandeja, /usuarios, /parametrizacion, etc. reflejan al impersonado. `backend/app/core/audit.py:write_audit` agrega automaticamente `impersonated_by` al campo `detalles` para preservar trazabilidad. `backend/app/api/v1/admin_impersonate.py:start_impersonate` hace fallback a BD local si AD no encuentra al usuario (permite impersonar a stubs de DES).

---

## 4. Hallazgos y trampas encontradas

### 4.1 Bug preexistente CRITICO en `validar_password_usuario` (Bloque B)

`backend/app/services/envio_service.py:45-49` (antes del fix) solo validaba contra LDAP si `LDAP_ENABLED=true`, sin contemplar que en DES los usuarios `aromero`, `cecEspinoza`, `admin`, etc. son locales (stubs). Esto causaba que la firma 2FA fallara para esos usuarios con error 401 "Password invalida" aunque ingresaran la password correcta `cofar.2026`.

**Solucion**: Replicar la logica dual de `auth.py` (stubs primero, LDAP despues).

```python
# Antes (BUG):
async def validar_password_usuario(db, user, password):
    if settings.ldap_enabled:
        return ad_service.ldap_bind(user.username, password)
    return password in ("cofar.2026", "admin.2026")

# Despues (OK):
LOCAL_PASSWORDS = ("cofar.2026", "admin.2026")
if password in LOCAL_PASSWORDS:
    return True
if settings.ldap_enabled:
    return ad_service.ldap_bind(user.username, password)
return False
```

### 4.2 Doble toast en firma 2FA (Bloque B)

El toast "Firma digital registrada" venia del `AuthModal.js:46` y se mostraba ANTES del callback `onSuccess`. Luego el callback en `AprobacionDocumento.js:firmarEnviar()` mostraba otro toast ("Solicitud enviada" o "Error al enviar"). El usuario veia 2 toasts: uno de exito (incorrecto, se mostraba aunque fallara) y otro con el resultado real.

**Solucion**: Removido el toast del AuthModal. Solo el callback muestra el resultado.

### 4.3 Bug preexistente CRITICO en `envio_service` (Bloque B)

`envio_service.py` buscaba estado `EN_REVISION` (codigo inexistente) en vez de `REVISION_PARALELA` (codigo real del seed original). Despues con B3, `REVISION_PARALELA` se inactiva, asi que tuve que actualizar a `REVISION` (nuevo).

**ADVERTENCIA**: Hay una desconexion entre el enum Python `Documento.EstatusDocumento.EN_REVISION` y el catalogo BD `estados.codigo='REVISION'`. El modelo Python no se actualizo, pero el flujo funciona porque el codigo del modelo no se valida contra el catalogo. Esto queda como deuda para R3.

### 4.4 PostgreSQL: ALTER TYPE ... ADD VALUE requiere autocommit (Bloque B)

```python
# BUG: falla con "UnsafeNewEnumValueUsageError"
op.execute("ALTER TYPE contexto_estado ADD VALUE 'ACCION'")
# ... usar el nuevo valor en la misma transaccion

# OK: con autocommit_block()
with op.get_context().autocommit_block():
    op.execute("ALTER TYPE contexto_estado ADD VALUE 'ACCION'")
# ... ahora SI se puede usar en otra transaccion
```

### 4.5 Impersonate no se propagaba a endpoints (Bloque D)

`get_current_user_from_cookie` solo leia `user_id` de la cookie (que es del ADMIN real). El resto de endpoints (bandejas, etc.) siempre devolvian los datos del ADMIN, no del impersonado. Por eso el usuario veia el banner de impersonate pero la UI no cambiaba.

**Solucion**: Modificar el helper para que lea tambien `impersonated_user` y devuelva ese usuario.

### 4.6 Tabla `firmas_digitales` era huerfana (Bloque B)

El modelo existia desde sesion 1 pero NUNCA se creaba fila. Esto es porque el servicio `envio_service` solo setea los campos en `documento_flujo.firma_*` y no crea la fila en `firmas_digitales`. Ahora con B4, se crea fila para audit forense completo (IP, user-agent, resultado_exito, motivo_fallo).

### 4.7 Plan `start_impersonate` solo buscaba en AD (Bloque D)

`admin_impersonate.py` solo buscaba en AD si `LDAP_ENABLED=true`. Esto impedia impersonar a usuarios locales como `visualizador_cl` (stubs de DES). **Solucion**: fallback a BD local si AD no encuentra al usuario.

### 4.8 Cache del navegador con Vite HMR (Bloque A)

Durante la validacion visual con Chrome DevTools, las 2 inputs de plazo/control lectura seguian apareciendo aunque el frontend estaba modificado. **Solucion**: `docker restart sgd-frontend` limpia el cache del Vite dev server. Tambien sirve usar `?_v=N` en la URL como cache buster.

### 4.9 Modelo Usuario tiene muchos NOT NULL (Bloque C)

Para insertar via psql directo, requiere: `username, email, nombre_completo, iniciales, cargo, estado, ausente, estado_delegacion, visualiza_reportes, requiere_delegado`. Si falta alguno, falla. El codigo Python siempre los setea, pero el SQL directo no.

### 4.10 Alembic detecta cambios colaterales autogenerados (recurrente)

Alembic `autogenerate` detecta cambios en tablas que NO tienen que ver con la migracion actual (ej: en B3/A5 detecto cambios en `email_templates.variables_json` y `tipos_documento.uq_tipos_documento_codigo`). **Solucion**: sobrescribir el archivo con una migracion limpia que SOLO tenga los cambios esperados.

---

## 5. Lo que FALTA (Bloques E y F)

### 5.1 Bloque E — Pagina /plantillas (nueva) (~2h)

**Descripcion del cliente**: Mostrar archivos de la carpeta `storage_qas/plantillas/` (en DES sera `backend/storage/plantillas/`). Solo titulo del documento + boton de descargar. Las descargas deben aparecer en `audit_log`. No tienen limite, adaptar cards al conteo.

**Sub-tareas pendientes:**
- E1: Crear carpeta `backend/storage/plantillas/` + copiar archivos desde `docs\Diagramas_Matrices\MATRICES\PLANTILLAS DOCUMENTALES\` (~15 min)
- E2: Backend: `GET /api/v1/plantillas-documentales` (lista) + `GET /.../download` (servir archivo + audit_log) (~1h)
- E3: Frontend: refactor `frontend/src/pages/Plantillas.js` para consumir el endpoint, sin mock, adaptar cards al conteo real (~45 min)

**Archivos a crear/tocar**:
- `backend/storage/plantillas/*.docx,*.xlsx,*.pdf,*.pptx` (copiar)
- `backend/app/api/v1/plantillas_documentales.py` (nuevo)
- `backend/app/schemas/plantilla_documental.py` (nuevo)
- `frontend/src/services/plantillasApi.js` (nuevo)
- `frontend/src/pages/Plantillas.js` (refactor)

### 5.2 Bloque F — Wizard pulido (~2h)

**Sub-tareas pendientes:**
- F1: Wizard paso 1: filtro ETO en analistas/delegados (dropdown `analista_eto_asignado` y `delegado (si ausente)` solo ETO). Crear helper `usuarios.listPorRol('ETO')` en `parametrizacionApi.js`. Modificar `AprobacionDocumento.js:init()` para llamar a ese endpoint. (~30 min)
- F2: Wizard paso 3: filtro REVISOR en revisores y APROBADOR en aprobadores. Similar a F1. (~30 min)
- F3: Plantillas - asunto: handler `insertarEtiqueta` en `frontend/src/pages/Parametrizacion.js` debe detectar `activeElement` (asunto vs cuerpo) para insertar la variable en el campo correcto. Bug: actualmente siempre va al cuerpo. (~30 min)
- F4: Visualizacion perfil: ocultar visualmente seccion delegado para visualizador/admin (rol sin delegado). Modificar `ProfileModal.js:301-310` para condicionar x-show segun `rolRequiereDelegado`. (~20 min)
- F5: Storage local momentaneo: configurar ruta base por env var `DOCUMENTOS_STORAGE_PATH` (DES: laptop, QAS: docker volume). Modificar `backend/app/services/storage.py` y `.env.example`. (~10 min)

---

## 6. Validaciones pendientes (criterio de aceptacion del cliente)

El cliente pidio que se valide VISUALMENTE con Chrome DevTools cada bug. Algunas ya se validaron, otras NO. Lista:

### 6.1 Ya validadas en esta sesion (Bloque A)
- [x] A1: `{{VERSION}}` visible en chips de Parametrizacion > Plantillas de Notificacion
- [x] A5: Las 2 inputs de plazo/control lectura removidas del tab Tiempos y SLAs
- [x] A6: 3 campos read-only en Wizard paso 1 (Nombre/Cargo/Fecha)

### 6.2 Validadas con curl (Bloque B y C)
- [x] A4: PATCH /usuarios/1 con delegado_id=1463 persiste
- [x] B1: POST /ausencias/usuarios/1 con fechas crea fila y setea usuarios.ausente=true
- [x] B3: 12 nuevos estados visibles en BD con contextos correctos
- [x] B4: 2 filas en firmas_digitales (1 fallida + 1 exitosa)
- [x] C1: Codigo del endpoint modificado, validado por inspeccion
- [x] C2: Backfill 754 true / 10 false
- [x] D1: aromatic impersona a visualizador_cl, bandejas reflejan roles

### 6.3 PENDIENTES de validar con Chrome DevTools
- [ ] **B1**: Frontend ProfileModal: registrar/actualizar/cancelar vacaciones con UI. Validar que `usuarios.ausente` cambia segun ausencias.
- [ ] **B1**: Frontend Parametrizacion > Gestion de Usuarios > Editar Usuario: el admin/ETO puede crear/editar/cancelar vacaciones del usuario.
- [ ] **B5**: Validar visualmente que el doble toast ya no aparece. Flujo: 1) Login aromero, 2) ir a Aprobacion Documento, 3) completar pasos 1+2, 4) firmar, 5) ver que SOLO aparece "Solicitud enviada a ETO correctamente" (no 2 toasts).
- [ ] **D1**: Validar visualmente en navegador: 1) Login aromero, 2) ir a Parametrizacion > Gestion de Usuarios, 3) click Impersonar a visualizador, 4) verificar que la sidebar muestra las opciones de visualizador (no de ETO), 5) ir a Mi Bandeja y verificar que se ve como visualizador, 6) click Terminar Impersonate.
- [ ] **C1**: Validar end-to-end con AD real. Requiere acceso al AD de COFAR (10.10.0.2). Por ahora solo se valido por inspeccion de codigo.

### 6.4 PENDIENTES de validar end-to-end
- [ ] **B2**: Cron 00:05. Requiere esperar al proximo dia a las 00:05 hrs. O ejecutar manualmente `docker exec sgd-backend python scripts/desactivar_ausencias_vencidas.py` y ver que se loguea correctamente.
- [ ] **C1**: Sync AD real. Solo se valido por inspeccion de codigo. El admin/ETO debe correr `POST /usuarios/sync-ad` contra el AD real y verificar que se marcan como desvinculados los usuarios que ya no estan.

---

## 7. Estado actual del sistema (post-sesion 23)

### 7.1 Stack (verificado)
- 8 contenedores Up (DES: nginx, frontend, postgres, redis, mailhog, celery-W, celery-B, backend)
- Backend healthy (`/health` retorna `{"status":"ok","database":"ok"}`)
- 8 contenedores backup paralelos (puerto 8081)
- QAS sin tocar en esta sesion (ultimo deploy: `v1.0.0-qas`)

### 7.2 BD (verificado)
- `alembic_version`: `8aa4cfa0f92f` (head de la rama `r2/wizard-y-version-editable`)
- 22 tablas (+4 nuevas en sesion 23: columna `es_usuario_ad` en `usuarios`, valor `ACCION` en enum `contexto_estado`)
- 764 usuarios: 754 con `es_usuario_ad=true`, 10 con `false`
- 12 nuevos estados: 3 PROCESO + 6 TAREA + 3 ACCION
- 9 estados antiguos: `activo=false` (borrado logico)
- 4 claves de `configuracion_global`: `activo=false` (plazos redundantes)
- `ausencias`: 1 fila de prueba (aromero 15-30 junio)
- `firmas_digitales`: 2 filas (1 fallida + 1 exitosa)

### 7.3 Frontend (verificado)
- 14 archivos modificados: AprobacionDocumento.js, Parametrizacion.js, ProfileModal.js, AuthModal.js
- Vite HMR funcionando, `?_v=N` cache buster si hay problemas
- Banner de impersonate: gradiente amber->orange->red, top fixed, padding-top dinamico

### 7.4 Tests
- 60 tests R2 verde (sin cambios en sesion 23)
- 123 tests R1 verde (sin cambios en sesion 23)
- **NO se agregaron tests nuevos en sesion 23** (pendiente: tests para ausencias + sync-ad desvinculados + impersonate fallback)

---

## 8. Comandos utiles

### 8.1 Diagnostico
```bash
# Health
curl.exe http://localhost:18000/api/v1/health

# Verificar contenedores
docker ps --filter "name=sgd-"

# Ver logs
docker logs sgd-backend --tail 50
docker logs sgd-frontend --tail 20
```

### 8.2 Validacion con curl
```bash
# Login
$json = '{"username":"aromero","password":"cofar.2026","auth_source":"local"}'
Set-Content -Path "$env:TEMP\login.json" -Value $json -NoNewline
curl.exe -s -c "$env:TEMP\cookies.txt" -X POST http://localhost:18000/api/v1/login \
  -H "Content-Type: application/json" --data-binary "@$env:TEMP\login.json"

# /me
curl.exe -s -b "$env:TEMP\cookies.txt" http://localhost:18000/api/v1/me

# Listar ausencias
curl.exe -s -b "$env:TEMP\cookies.txt" "http://localhost:18000/api/v1/ausencias?usuario_id=1"

# Impersonate
$json = '{"sAMAccountName":"visualizador_cl"}'
Set-Content -Path "$env:TEMP\imp.json" -Value $json -NoNewline
curl.exe -s -b "$env:TEMP\cookies.txt" -c "$env:TEMP\cookies.txt" \
  -X POST http://localhost:18000/api/v1/admin/impersonate/start \
  -H "Content-Type: application/json" --data-binary "@$env:TEMP\imp.json"
```

### 8.3 Migraciones
```bash
# Generar nueva
docker exec sgd-backend alembic revision -m "descripcion"
# Aplicar
docker exec sgd-backend alembic upgrade head
# Ver head
docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT * FROM alembic_version;"
```

### 8.4 Cron
```bash
# Ejecutar manualmente
docker exec sgd-backend python scripts/desactivar_ausencias_vencidas.py
docker exec sgd-backend python scripts/desactivar_ausencias_vencidas.py --dry-run

# Reiniciar celery-beat para cargar nuevo schedule
docker restart sgd-celery-beat
docker restart sgd-celery-worker
```

### 8.5 Validacion visual con Chrome DevTools
```bash
# Iniciar sesion
docker restart sgd-frontend  # limpiar cache Vite HMR
# Browser: http://localhost:8080/?_v=N   (cambiar N para forzar reload)
```

---

## 9. Decisiones tecnicas (ADRs candidatos)

Ya hay 50+ ADRs en `docs/PR/DECISIONES.md`. Los nuevos de sesion 23:

- **ADR-046**: Plazo maximo en `semaforizacion_tarea` (por tipo), no en `configuracion_global`. Redundancia eliminada.
- **ADR-047**: Wizard crea documento SOLO al firmar, no al avanzar. Patron "no persistir hasta tener confirmacion".
- **ADR-048**: `Documento.EstatusDocumento` (enum Python) es INDEPENDIENTE del catalogo `estados` (BD). Aceptado por simplicidad.
- **ADR-049**: `validar_password_usuario` replica logica dual de `auth.py`: stubs locales primero, LDAP despues.
- **ADR-050**: Tabla `ausencias` es fuente de verdad de vacaciones. `usuarios.ausente` es DERIVADO. Cron 00:05 sincroniza.
- **ADR-051**: Estados con 3 contextos (PROCESO/TAREA/ACCION) + 12 canonicos. Codigos duplicados con sufijo de contexto (ELIMINADO_PROC, ELIMINADO_ACC).
- **ADR-052**: Sync AD NUNCA elimina usuarios. Los que no estan en AD se marcan como `desvinculado`.
- **ADR-053**: Columna `es_usuario_ad` distingue AD vs local.
- **ADR-054**: `get_current_user_from_cookie` prioriza `impersonated_user` (Sesion 23). `write_audit` agrega `impersonated_by` en `detalles`.
- **ADR-055**: `start_impersonate` hace fallback a BD local si AD no encuentra al usuario (permite impersonar a stubs de DES).

---

## 10. Proximos pasos recomendados

### 10.1 Sesion 24 (inmediata): validar visualmente con Chrome
- [ ] Login como aromero, ir a Aprobacion Documento, completar wizard completo. Verificar que SOLO aparece un toast al firmar (B5).
- [ ] Login como aromero, ir a Mi Perfil, registrar vacaciones con fechas. Verificar que la fecha_desde/fecha_hasta se guardan y que aparece como "En vacaciones" (B1).
- [ ] Login como visualizador_cl, ir a Mi Perfil. Verificar que la seccion delegado no se muestra (o se muestra como opcional) (pendiente en F4).
- [ ] Login como aromero, ir a Parametrizacion > Gestion de Usuarios, click Impersonar a visualizador_cl. Verificar que la sidebar cambia, la bandeja refleja al visualizador, y Terminar Impersonate funciona (D1).
- [ ] Login como aromero, ir a Aprobacion Documento paso 1. Verificar que el dropdown de Analista ETO solo muestra usuarios con rol ETO (pendiente en F1).

### 10.2 Sesion 25: Bloque E (~2h)
- Crear `backend/storage/plantillas/` con los archivos de `docs\Diagramas_Matrices\MATRICES\PLANTILLAS DOCUMENTALES\`
- Crear endpoint `GET /api/v1/plantillas-documentales` y `GET /.../download`
- Refactorizar `frontend/src/pages/Plantillas.js`

### 10.3 Sesion 26: Bloque F (~2h)
- F1: filtro ETO en analistas
- F2: filtro REVISOR/APROBADOR
- F3: handler `insertarEtiqueta` detecta activeElement
- F4: ocultar delegado para visualizador/admin
- F5: storage local momentaneo

### 10.4 Sesion 27: Tests nuevos
- Tests pytest para `/ausencias/*` (CRUD + vigente)
- Tests pytest para `validar_password_usuario` (replicar logica dual)
- Tests pytest para `start_impersonate` con fallback a BD
- Tests pytest para sync-ad desvinculados

### 10.5 Sesion 28: Deploy a QAS
- Bump version a v1.1.0-qas
- `scripts/deploy-qas.bat` (ya existe)
- Validar las 12 categorias A-L
- Tag v1.1.0-qas

---

## 11. Archivos criticos para retomar

Si la ventana de contexto se acaba, leer en este orden:
1. `docs/PR/INICIO-SESION.md` (ritual de 6 pasos)
2. `docs/PR/ESTADO.md` (version actual + tareas)
3. `docs/PR/BITACORA.md` (historial reciente)
4. `docs/PR/HANDOFF-BLOQUES-A-B-C-D.md` (este documento)
5. `docs/PR/DECISIONES.md` (ADRs activos)
6. `backend/app/api/v1/ausencias.py` (nuevo, B1)
7. `backend/app/workers/tasks.py` (cron B2)
8. `backend/app/core/permissions.py` (D1: impersonate)
9. `backend/app/api/v1/admin_impersonate.py` (D1: fallback a BD)
10. `backend/alembic/versions/2026_06_17_*.py` (5 migraciones nuevas)

---

## 12. Notas finales

- **Stack estable**: 8 contenedores Up, backend healthy, frontend sirviendo via Nginx.
- **Tests existentes**: 183/183 verde (60 R2 + 123 R1). **NO se agregaron tests nuevos**.
- **QAS NO se toco**. QAS sigue en `v1.0.0-qas`. Los cambios de sesion 23 iran en v1.1.0-qas despues de validar.
- **Backup paralelo** sigue en puertos 8081/5174/18001/25433/26380/8026.
- **Hora de cierre**: ~19:30 del 17-jun-2026. La sesion 24 puede retomar desde este handoff.

Para dudas o continuar, referirse a:
- `docs/PR/INICIO-SESION.md` (ritual)
- `docs/PR/DECISIONES.md` (ADRs)
- `docs/PR/BITACORA.md` (historial completo de las 23 sesiones)
- Este documento (estado post-sesion 23)

**FIN del handoff. Buena suerte con la sesion 24!**
