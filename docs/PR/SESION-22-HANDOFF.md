# SESIÓN 22 — HANDOFF (continuación de R2 FASE 2)

> **Documento de arranque para la próxima sesión.** Léelo COMPLETO al inicio.
> **Sesión anterior:** 21 (R2 FASE 1 cerrada al 100%, 7/21 tareas R2).
> **Esta sesión debe arrancar en:** rama `r2/wizard-y-version-editable`, head `e176b79`.
> **Objetivo de esta sesión:** cerrar R2 FASE 2 (wizard E2E + firma 2FA + refactor frontend).
> **Última actualización:** 2026-06-17 (cierre de sesión 21).

---

## 1. PROMPT DE INICIO DE SESIÓN (copiar y pegar al chat)

```
Actua como Tech Lead senior del proyecto COFAR SGD. Realiza el siguiente ritual de
inicio de sesion y arranca la FASE 2 de R2:

1. LEE en este orden:
   a) docs/PR/INICIO-SESION.md (ritual maestro)
   b) docs/PR/R2-PLAN-EJECUCION.md (plan completo de R2 en 2 fases)
   c) docs/PR/SESION-22-HANDOFF.md (este archivo - estado y plan inmediato)
   d) docs/PR/ESTADO.md (estado REAL del codigo)
   e) docs/PR/BITACORA.md (especialmente sesion 21)
   f) docs/PR/DECISIONES.md (ADRs activos, ultimos 5)

2. DIAGNOSTICA el ambiente:
   - git status y git log --oneline -5 (validar rama r2/wizard-y-version-editable)
   - docker info y docker ps --filter "name=sgd-" (stack debe estar Up)
   - curl.exe http://localhost:18000/api/v1/health (debe devolver {"status":"ok"})
   - docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT count(*) FROM documentos"
     (debe devolver 10)
   - .\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_documentos.py
     backend/tests/test_correlativo_service.py (33/33 deben pasar)
   - Si algo falla, usar el custom tool build-error-resolver agent

3. IDENTIFICA la siguiente tarea PENDIENTE:
   - FASE 2 de R2 (segun docs/PR/R2-PLAN-EJECUCION.md § 4.2)
   - 10 sub-tareas (2.1 a 2.10)
   - Estimado: 5.5h
   - Riesgo principal: firma 2FA atomica (no se debe persistir si BD falla)

4. PROPON al usuario:
   - "La siguiente tarea es FASE 2 R2 (10 sub-tareas del plan)"
   - "Tiempo estimado: 5.5 horas"
   - "Riesgos: firma 2FA no atomica, refactor profundo de AprobacionDocumento.js"
   - "Como lo voy a ejecutar: backend primero (storage + POST/enviar), luego frontend
     (autocomplete + refactor wizard), finalmente E2E + tests"
   - PREGUNTAR: "Procedo con FASE 2 o queres priorizar otra cosa?"

5. Si el usuario aprueba, EJECUTA:
   - Empezar por Tarea 2.3 (storage service) que es prerequisito para 2.2 (upload)
   - Tarea 2.1 (POST/PATCH /documentos) se puede hacer en paralelo
   - Tarea 2.4 (POST /enviar con firma 2FA) es la MAS CRITICA - aqui es donde se puede romper
   - Tarea 2.6 (frontend autocomplete) es la mas visible - buen momento para grabar demo
   - Tarea 2.7 (refactor AprobacionDocumento.js) es la mas larga - 1h30min
   - Documentar paso a paso con outputs visibles
   - Si te trabas >15 min, salir del loop y consultar

6. ANTES de cerrar sesion, ACTUALIZA:
   - docs/PR/ESTADO.md (marcar tareas de FASE 2 completadas)
   - docs/PR/BITACORA.md (entrada sesion 22 con lo que se hizo)
   - docs/PR/DECISIONES.md (agregar ADRs 042-045 que quedaron como draft)
   - Hacer commit con conventional commit
   - Reportar resumen al usuario: que se hizo, que quedo pendiente, si hay bloqueos
```

---

## 2. ESTADO VERIFICADO AL CIERRE DE SESIÓN 21

### 2.1 Git

```bash
$ git branch --show-current
r2/wizard-y-version-editable

$ git log --oneline -5
e176b79 docs(pr): sesion 21 - entrada BITACORA con 13 sub-tareas + 5 bugs + 5 ADRs
c9aaea1 docs(pr): sesion 21 R2 - plan ejecucion + ESTADO + BITACORA actualizados
68030d9 feat(backend+frontend): R2 fase 1 - documentos modelos + endpoints lectura + seed + tests
737574b fix(deploy)+feat(validation): 6 fixes preventivos del deploy pipeline + plan reescrito
1b1fbf3 docs(pr): sesion 19 - DEPLOY QAS v1.0.0-qas (12/12 validaciones PASS)

$ git status
On branch r2/wizard-y-version-editable
nothing to commit, working tree clean
```

### 2.2 Stack

- **8 contenedores DES Up** (backend, frontend, postgres, redis, mailhog, celery-W, celery-B, nginx)
- **Backend healthy:** `curl http://localhost:18000/api/v1/health` → `{"status":"ok","database":"ok"}`
- **PostgreSQL:** 20 tablas originales + 3 nuevas (documentos, documento_flujo, archivos_adjuntos) = 23 totales
- **Alembic head:** `b88801d59687` (migración 014)
- **Tests pytest:** 33/33 nuevos passing (4.07s)

### 2.3 Base de datos (verificado con psql)

```
documentos:         10 filas
documento_flujo:    10 filas
archivos_adjuntos:   0 filas (sin uploads aun, esperado en FASE 2)
audit_log:         118 filas (incluye 14 nuevas de la sesion 21)
```

### 2.4 Documentos sembrados (idempotente)

| Código | Título | Estatus | Vigencia | Regla validada |
|---|---|---|---|---|
| CC-5-001/00 | Procedimiento de Control de Documentos del SIG | APROBADO | VIGENTE | |
| DT-3-001/00 | Política de Dirección Técnica | APROBADO | VIGENTE | |
| EST-7-001/00 | Especificación de Estabilidad Acelerada | APROBADO | VIGENTE | |
| **PRO-5-001/00** | Procedimiento Operativo de Producción | **APROBADO** | **VENCIDO** | ✓ VENCIDO implica APROBADO |
| BET-7-001/00 | Especificación de Betalactamicos | APROBADO | POR_VENCER | |
| ACD-5-001/00 | Procedimiento de Acondicionamiento | EN_ELABORACION | VIGENTE | |
| VAL-5-001/00 | Procedimiento de Validaciones | EN_ELABORACION | VIGENTE | |
| REG-4-001/00 | Plan Regulatorio 2026 | EN_REVISION | VIGENTE | |
| GAC-3-001/00 | Política de Garantía de Calidad | EN_REVISION | VIGENTE | |
| MCB-6-001/00 | Instructivo de Microbiología vAntigua | OBSOLETO | OBSOLETO | |

**Idempotencia verificada:** 1ra corrida=10 insertados, 2da corrida=10 skipped, 3ra=10 skipped.

---

## 3. RESUMEN DE LO QUE SE HIZO EN SESIÓN 21

### 3.1 Backend (12 archivos nuevos/modificados)

| Archivo | Líneas | Descripción |
|---|---|---|
| `backend/app/models/documento.py` | 175 | Modelo CORE con 18 columnas + 2 UK + 1 CHECK |
| `backend/app/models/documento_flujo.py` | 180 | Instancia del wizard con 5 JSONB |
| `backend/app/models/archivo_adjunto.py` | 110 | Storage de archivos con MIME/tamaño |
| `backend/app/models/__init__.py` | +24 | Registra 3 modelos nuevos + 5 enums |
| `backend/app/schemas/documento.py` | 175 | 11 schemas Pydantic v2 (solo lectura) |
| `backend/app/services/correlativo_service.py` | 130 | SELECT FOR UPDATE + advisory lock fallback |
| `backend/app/services/vigencia_service.py` | 150 | calcular_vigencia con regla del usuario |
| `backend/app/api/v1/documentos.py` | 290 | Router con 4 endpoints de lectura |
| `backend/app/main.py` | +3 | Registra router /documentos |
| `backend/alembic/versions/2026_06_17_1023-b88801d59687_*.py` | 175 | Migración 014 (3 tablas + 17 índices) |
| `backend/scripts/seed_documentos.py` | 235 | Seed idempotente de 10 docs |
| `backend/tests/test_documentos.py` | 360 | 23 tests del router |
| `backend/tests/test_correlativo_service.py` | 180 | 10 tests del service |
| `backend/tests/conftest.py` | +48 | Registra 3 modelos + stubs SQLite |

### 3.2 Frontend (1 archivo modificado)

| Archivo | Cambio |
|---|---|
| `frontend/src/pages/VersionEditable.js` | Placeholder `PRO-CAL-005` → `CC-3-005/01` (1 línea) |

### 3.3 Documentación (3 archivos)

| Archivo | Contenido |
|---|---|
| `docs/PR/R2-PLAN-EJECUCION.md` | Plan completo de R2 en 2 fases (437 líneas) |
| `docs/PR/ESTADO.md` | Actualizado con 7/21 tareas R2 completadas |
| `docs/PR/BITACORA.md` | Entrada de sesión 21 con 13 sub-tareas, 5 bugs, 5 ADRs |

### 3.4 Bugfixes de sesión 21

1. **Alembic detectó cambios colaterales** en `email_templates.variables_json` y `tipos_documento.uq_tipos_documento_codigo` (de sesiones 13/14 no propagados). **Fix:** removidos manualmente del archivo de migración.
2. **Seed NO era idempotente en 1ra versión** (correlativo se incrementaba en cada corrida). **Fix:** usar `(area, tipo, titulo)` como clave de detección en vez de `(area, tipo, correlativo)`.
3. **Tests fallaban en SQLite** por funciones PostgreSQL `hashtext` y `pg_try_advisory_xact_lock`. **Fix:** registrados como custom functions en conftest.py.
4. **`register_adapter` rompió el adapter de SQLAlchemy** para enums. **Fix:** eliminado el register_adapter; las funciones custom funcionan sin él.
5. **`siguiente_correlativo_advisory` no filtraba por `activo=True`** (incluía borrados lógicos en el MAX). **Fix:** agregado `.where(Documento.activo == True)`.

### 3.5 Validación empírica

- 33/33 tests pytest nuevos passing (4.07s)
- 6/6 smoke tests E2E con curl-style + cookies reales
- 10/10 documentos sembrados con claves foráneas válidas
- 1/1 regla de negocio validada (PRO-5-001/00 VENCIDO con estatus=APROBADO)
- 1/1 check constraint aplicado (vigencia != VENCIDO OR estatus IN (APROBADO, OBSOLETO))
- 1/1 placeholder fix (CC-3-005/01 visible en browser)

---

## 4. DECISIONES TOMADAS (ADRs a formalizar en sesión 22)

> Todos estos ADRs están documentados en `BITACORA.md` sesión 21 como "candidatos".
> La nueva sesión debe **formalizarlos** en `docs/PR/DECISIONES.md` con el formato estándar
> contexto/decisión/consecuencia.

### ADR-042: JSONB para N:M en `documento_flujo` (R2 → tablas N:M en R3)

**Contexto:** El wizard de aprobación necesita persistir revisores, aprobadores y alcance de
difusión como sets de IDs. La forma tradicional sería tablas N:M (revisor_id, aprobador_id,
difusion_id). Pero para R2 el alcance es limitado (los IDs se muestran pero las bandejas
reales de revisores son R3).

**Decisión:** Almacenar como JSONB en `documento_flujo.revisor_ids`, `aprobador_ids`,
`alcance_difusion_ids`, `reemplaza_documento_ids`.

**Consecuencia:**
- (+) Simplicidad: 0 tablas extra en R2.
- (+) Performance: queries de "mis docs en revisión" (R3) leen un solo campo.
- (-) Migración a R3 cuando se necesite historial/timestamps individuales por revisor.

### ADR-043: Trigger SQL de obsolescencia DIFERIDO a R5

**Contexto:** El plan R2 oficial #30 propone un trigger SQL que recalcula `vigencia` cuando
cambia `aprobacion_at` o `expira_at`. La sesión 21 creó `vigencia_service.py` con la
misma lógica en Python.

**Decisión:** Mantener el cálculo en backend Python. NO crear trigger SQL en R2.

**Consecuencia:**
- (+) R2 entrega rápido, sin riesgo de tests complejos de bordes (zonas horarias, etc.).
- (-) BD tiene el campo `vigencia` desincronizado si cambia `aprobacion_at` o `expira_at`
  sin pasar por el servicio. Se mitiga recalculando en endpoints críticos.

### ADR-044: `tipo_solicitud` como enum SQLAlchemy, no tabla catálogo

**Contexto:** El wizard necesita 2 valores (CREACION, ACTUALIZACION) que no cambian nunca.

**Decisión:** `class TipoSolicitud(str, enum.Enum)` en `app/models/documento_flujo.py`.

**Consecuencia:**
- (+) 0 tablas extra. 0 endpoints extra.
- (-) Si en el futuro se agregan más tipos (ej: ANULACION), requiere migración Alembic.

### ADR-045: Separador de versión es `/` (no `v`)

**Contexto:** El plan R2 original (ADR-011) decía `v01`. El usuario en sesión 21 pidió
explícitamente `CC-3-005/01` con barra.

**Decisión:** Sobreescribe ADR-011. Formato final: `{codigo}/{version}` (sin letra `v`).

**Consecuencia:**
- (+) Coherencia con el ejemplo del usuario.
- (+) El `model_dump` JSON ya devuelve `version` separado (no se concatena con `v`).
- (-) Código legacy que asumía `v01` debe ser actualizado (no hay código legacy aún).

---

## 5. RIESGOS IDENTIFICADOS (continúan activos en sesión 22)

### R1: Firma 2FA NO atómica (CRÍTICO)

**Riesgo:** `POST /documentos/{id}/enviar` debe validar password, transicionar estatus y
crear tareas en bandejas. Si algo falla DESPUÉS de validar password, no debe quedar como
firmado.

**Mitigación propuesta:** Transacción única con `write_audit()` + `db.commit()` al final.
Si falla, rollback total. Implementar en `app/services/envio_service.py` (nuevo).

**Validación en sesión 22:** Test que simule falla de BD post-firma → verificar que
NO se persistió el flujo.

### R2: Refactor profundo de `AprobacionDocumento.js` (485 líneas)

**Riesgo:** Es el archivo más grande del frontend. Refactor completo puede romper 7 botones
del wizard, 3 áreas de drag&drop, y los 3 chips (revisores, aprobadores, alcance).

**Mitigación:** Hacer el refactor EN PASOS (commitear cada paso funcional):
1. Reemplazar imports de mocks por `await ...list()` — compilación OK
2. Reemplazar hardcoded `revisores` por selector real — paso 3 funcional
3. Reemplazar `arbolOutlookDB` por árbol dinámico — paso 2 funcional
4. Reemplazar `firmarEnviar` por POST real con firma 2FA — paso 3 E2E

### R3: `vigencia` desincronizada si cambia `aprobacion_at` directamente

**Riesgo:** Como NO hay trigger SQL (ADR-043), si un endpoint futuro cambia
`aprobacion_at` sin recalcular `vigencia`, la BD queda inconsistente.

**Mitigación:** Centralizar el cambio de `aprobacion_at` en un helper
`aprobar_documento(doc, fecha)` que recalcula `vigencia` + `expira_at` en la misma
transacción. Documentar en el ADR-043.

### R4: Storage stub en DES, SharePoint en QAS (R4 plan)

**Riesgo:** El `LocalStorage` que se implemente en sesión 22 será el real para DES y QAS
local. SharePoint en QAS/PROD. Si la abstracción está mal, el cambio a SharePoint
romperá el wizard.

**Mitigación:** Diseñar `StorageBackend` como Protocol con 2 implementaciones.
Tests con `LocalStorage` (real, escribe en /app/storage/uploads) y
`SharePointStorage` (stub que loguea). En QAS, `SHAREPOINT_ENABLED=true` activa el real.

### R5: Almacenamiento de archivos en tests pytest

**Riesgo:** Los tests con `LocalStorage` van a escribir en `/app/storage/uploads/` del
contenedor. Si los tests corren en el host (no en Docker), la ruta no existe.

**Mitigación:** Usar `tmp_path` fixture de pytest que crea un directorio temporal por
test. Configurar el storage via env var `STORAGE_ROOT=tmp_path`.

---

## 6. PLAN DE EJECUCIÓN PARA SESIÓN 22 (FASE 2)

> Plan detallado en `docs/PR/R2-PLAN-EJECUCION.md` § 4.2. Resumen operativo aquí.

### Orden de ejecución recomendado (5.5h estimadas)

```
1. [20min] Tarea 2.3 - Storage service (LocalStorage + SharePointStorage stub)
2. [30min] Tarea 2.1 - POST/PATCH /documentos (sin firma 2FA todavía)
3. [20min] Tarea 2.2 - POST /documentos/{id}/archivos (upload stub)
4. [40min] Tarea 2.4 - POST /documentos/{id}/enviar CON firma 2FA ← MÁS CRÍTICA
5. [30min] Tarea 2.5 - Endpoints /bandeja (4 tipos)
6. [25min] Tarea 2.6 - Refactor VersionEditable.js (autocomplete real)
7. [30min] Tarea 2.8 - Frontend documentosApi.js
8. [1h30min] Tarea 2.7 - Refactor AprobacionDocumento.js completo ← MÁS LARGA
9. [30min] Tarea 2.9 - Validación E2E con Chrome DevTools
10. [20min] Tarea 2.10 - Commit + docs + ADRs 042-045 en DECISIONES.md
```

### Criterio de cierre de FASE 2

- [ ] 5/10 tests de storage + POST/enviar pasan
- [ ] Login aromero + completar wizard paso 1+2+3 + firmar → doc persistido
- [ ] Firmar con password incorrecta → 401 + toast
- [ ] Wizard frontend sin errores en consola
- [ ] Autocomplete en /version-editable muestra BD real
- [ ] Working tree limpio + 2-3 commits atómicos
- [ ] ESTADO + BITACORA + DECISIONES actualizados

---

## 7. DETALLE DE CADA TAREA DE FASE 2

### Tarea 2.1 — POST /documentos + PATCH /documentos/{id}

**Archivos:** `backend/app/api/v1/documentos.py`, `backend/app/schemas/documento.py`

**Schemas a agregar:**
```python
class DocumentoCreate(BaseModel):
    gerencia_id: int
    area_id: int
    tipo_documento_id: int
    titulo: str = Field(min_length=3, max_length=200)
    codigo_antiguo: Optional[str] = None
    comentarios_eto: Optional[str] = Field(None, max_length=50)

class DocumentoUpdate(BaseModel):
    titulo: Optional[str]
    codigo_antiguo: Optional[str]
    comentarios_eto: Optional[str] = Field(None, max_length=50)
    estatus: Optional[EstatusDocumento]  # solo ADMIN/ETO pueden cambiar
```

**Lógica POST:**
1. Validar que `gerencia_id` y `area_id` existen y son consistentes
2. Validar que `tipo_documento_id` existe y está activo
3. Generar correlativo con `siguiente_correlativo_advisory()` (dentro de transacción)
4. Calcular `codigo = formatear_codigo(area.sigla, tipo.codigo, correlativo)`
5. Crear Documento con `version="00"`, `estatus=EN_ELABORACION`, `vigencia=VIGENTE`
6. Crear DocumentoFlujo inicial con `estado_actual_id=ELABORACION`
7. `write_audit()` con accion CREATE_DOCUMENTO
8. Retornar DocumentoOut

**Endpoint:** `POST /api/v1/documentos` (auth: ETO o ELABORADOR)

### Tarea 2.2 — POST /documentos/{id}/archivos

**Archivos:** `backend/app/api/v1/documentos.py`, `backend/app/services/storage.py` (nuevo)

**Lógica:**
1. Validar que documento existe y activo=True
2. Validar `count(archivos del doc) <= config_global.max_archivos_por_solicitud`
3. Validar `tamano_bytes <= config_global.max_tamano_archivo_mb * 1024 * 1024`
4. Validar `mime_type IN whitelist`
5. Llamar `storage.save(archivo, destino)` → devuelve `path`
6. Crear `ArchivoAdjunto(StorageBackend.LOCAL, storage_path=path)`
7. `write_audit()` con accion UPLOAD_ARCHIVO

**Endpoint:** `POST /api/v1/documentos/{id}/archivos` (multipart/form-data, auth: elaborador)

### Tarea 2.3 — Storage service (LocalStorage + SharePointStorage stub)

**Archivo:** `backend/app/services/storage.py` (nuevo)

**Diseño:**
```python
class StorageBackend(Protocol):
    def save(self, file_bytes: bytes, dest_filename: str) -> str: ...  # retorna path
    def delete(self, path: str) -> None: ...
    def get_url(self, path: str) -> str: ...  # para download

class LocalStorage:
    ROOT = Path(os.getenv("STORAGE_ROOT", "/app/storage/uploads"))
    def save(self, file_bytes, dest_filename) -> str:
        # Genera UUID + extension
        # Escribe en ROOT
        # Retorna path absoluto

class SharePointStorage:
    """Stub en DES. En QAS/PROD: implementa Microsoft Graph API."""
    def save(self, file_bytes, dest_filename) -> str:
        logger.info(f"[STUB] SharePoint: subiendo {dest_filename}")
        return f"sharepoint://{dest_filename}"  # path ficticio
```

**Tests:** 5 tests (save/delete/get_url con LocalStorage + stub SharePoint)

### Tarea 2.4 — POST /documentos/{id}/enviar (FIRMA 2FA) ← CRÍTICA

**Archivos:** `backend/app/api/v1/documentos.py`, `backend/app/services/envio_service.py` (nuevo)

**Flujo atómico:**
```python
@router.post("/documentos/{id}/enviar")
async def enviar_a_liberacion(
    id: int,
    body: EnviarRequest,  # {password: str, revisor_ids: [...], aprobador_ids: [...]}
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await require_authenticated(request, db)

    # 1. Validar password contra verify-password (REUTILIZAR endpoint existente)
    async with db.begin():  # TRANSACCION UNICA
        # 2. Re-leer documento con FOR UPDATE (lock pesimista)
        doc = await db.execute(
            select(Documento).where(Documento.id == id).with_for_update()
        )
        doc = doc.scalar_one()
        if doc.estatus != EstatusDocumento.EN_ELABORACION:
            raise HTTPException(409, "Solo se pueden enviar docs en ELABORACION")

        # 3. Validar password
        if not await verify_user_password(user, body.password, db):
            raise HTTPException(401, "Password invalido")

        # 4. Crear/actualizar DocumentoFlujo con los revisores/aprobadores del wizard
        flujo = await _crear_o_actualizar_flujo_envio(doc, user, body, db)

        # 5. Transicionar estatus
        doc.estatus = EstatusDocumento.EN_REVISION
        doc.firma_usuario_id = user.id  # se setea en el flujo, no en doc
        doc.firma_at = datetime.now(timezone.utc)
        doc.firma_ip = request.client.host
        doc.firma_user_agent = request.headers.get("user-agent", "")[:500]

        # 6. write_audit() con accion ENVIAR_LIBERACION
        # 7. db.commit() AUTOMATICO al salir del async with

    # 8. Si llegamos aca, todo OK. Retornar 200.
    return {"ok": True, "documento_id": id, "flujo_id": flujo.id, "estatus": doc.estatus.value}
```

**Tests críticos:**
- Test 1: Login aromero + wizard completo + password correcta → 200 + doc persistido
- Test 2: Login aromero + wizard + password incorrecta → 401 + NADA persistido
- Test 3: Re-enviar un doc ya enviado → 409 (estatus != EN_ELABORACION)
- Test 4: Verificar firma_ip y firma_user_agent correctos

### Tarea 2.5 — Endpoints /bandeja (4 tipos)

**Archivo:** `backend/app/api/v1/bandeja.py` (nuevo)

**Endpoints:**
```
GET /api/v1/bandeja?tipo=elaboracion → mis docs EN_ELABORACION
GET /api/v1/bandeja?tipo=revision → docs donde soy revisor
GET /api/v1/bandeja?tipo=aprobacion → docs donde soy aprobador
GET /api/v1/bandeja?tipo=liberacion → docs finalizados (cualquier ETO)
```

**Lógica:**
- `elaboracion`: `Documento.estatus == EN_ELABORACION AND Documento.created_by_id == user.id`
- `revision`: `DocumentoFlujo.revisor_ids CONTAINS user.id AND Documento.estatus == EN_REVISION`
- `aprobacion`: `DocumentoFlujo.aprobador_ids CONTAINS user.id AND Documento.estatus == EN_REVISION`
- `liberacion`: `Documento.estatus == APROBADO`

**Schemas:** `BandejaItem` con joins a gerencia/area/tipo, `BandejaResponse` con paginación.

**Tests:** 8 tests (4 endpoints × 2 escenarios: con docs, sin docs)

### Tarea 2.6 — Refactor VersionEditable.js (autocomplete real)

**Archivo:** `frontend/src/pages/VersionEditable.js`

**Cambios:**
1. Reemplazar `setTimeout` mock por `await apiGet('/documentos/buscar?q=...')`
2. Implementar autocomplete con `<datalist>` (patrón ya en AprobacionDocumento.js)
3. Mostrar tipo + título + vigencia + estatus en el resultado
4. Reemplazar el "resultadoEditable" mock por el response de la API
5. El botón "Descargar" queda como placeholder (FASE 3)

**Antes vs después:**
```javascript
// ANTES (mock)
buscarEditable() {
  setTimeout(() => {
    this.resultadoEditable = {
      archivo: this.codBuscar + '_v01.docx',
      nombre: 'Documento Principal + Formularios adjuntos',
      limite: ...
    }
  }, 1200)
}

// DESPUES (real)
async buscarEditable() {
  this.cargando = true
  try {
    const res = await apiGet(`/documentos/buscar?q=${encodeURIComponent(this.codBuscar)}`)
    if (res.items.length === 0) {
      window.toast?.('No se encontraron documentos', 'warn')
      this.resultadoEditable = null
    } else {
      // Tomar el primer match exacto
      const match = res.items.find(d => d.codigo_completo === this.codBuscar) || res.items[0]
      this.resultadoEditable = {
        archivo: match.codigo_completo + '.docx',
        nombre: match.titulo,
        tipo: match.tipo.nombre,
        area: `${match.gerencia.sigla} / ${match.area.sigla}`,
        vigencia: match.vigencia,
        limite: match.tipo.max_descargas_dia
      }
    }
  } catch (e) {
    window.toast?.(e.message, 'error')
  } finally {
    this.cargando = false
  }
}
```

### Tarea 2.7 — Refactor AprobacionDocumento.js completo

**Archivo:** `frontend/src/pages/AprobacionDocumento.js` (485 líneas)

**Cambios ordenados (commitear por paso):**

**Paso A (10min):** Reemplazar imports de mocks
```javascript
// ANTES
import { gerenciasDB, arbolOutlookDB, tiposDocDB } from '../data/gerencias.js'
import { listaEmpleados } from '../data/users.js'

// DESPUES
import { gerencias, tiposDocumento, usuarios, areas as areasApi } from '../services/documentosApi.js'
```

**Paso B (20min):** `init()` async carga catalogos
```javascript
init() {
  window.Alpine?.data('wizardAprobacion', () => ({
    paso: 1,
    tiposList: [], gerenciasList: [], empleadosList: [],
    async init() {
      this.tiposList = (await tiposDocumento.list()).items
      this.gerenciasList = (await gerencias.list()).items
      this.empleadosList = (await usuarios.listActivos()).items
    },
    // ...
  }))
}
```

**Paso C (20min):** `areasList` dinámico
```javascript
get areasList() {
  // ANTES: filtro local de gerenciasDB
  // DESPUES: await areas.list({gerencia_id: this.gerencia})
}
```

**Paso D (20min):** `codigoAuto` y `versionAuto` reales
```javascript
get codigoAuto() {
  if (!this.tipodoc || !this.area) return '---'
  // Llamar al endpoint preview-codigo
  return this._codigoCache || '...'
}
async _recalcularCodigo() {
  const res = await apiGet(`/documentos/preview-codigo?tipo_id=${this.tipodoc}&area_id=${this.area}&tipo_solicitud=${this.tipoSolicitud || 'CREACION'}`)
  this._codigoCache = res.codigo_completo
}
```

**Paso E (15min):** `arbolOutlookDB` → árbol dinámico
- Llamar `gerencias.list({con_areas: true})` (necesita extensión del endpoint)
- Construir árbol gerencia → areas en Alpine

**Paso F (15min):** `firmarEnviar` con POST real + firma 2FA
- Reemplazar `window.authModal?.abrir({...})` por POST a `/documentos/{id}/enviar` con `body.password`
- Usar `authModal` solo para capturar el password
- Después del 200, navegar a /bandeja

### Tarea 2.8 — Frontend `documentosApi.js`

**Archivo:** `frontend/src/services/documentosApi.js` (nuevo)

**Contenido:**
```javascript
import { apiGet, apiPost, apiPatch, apiDelete, apiUpload } from '../utils/api.js'

export const documentos = {
  buscar: (q, limit = 10) => apiGet(`/documentos/buscar?q=${encodeURIComponent(q)}&limit=${limit}`),
  previewCodigo: (tipo_id, area_id, tipo_solicitud = 'CREACION') =>
    apiGet(`/documentos/preview-codigo?tipo_id=${tipo_id}&area_id=${area_id}&tipo_solicitud=${tipo_solicitud}`),
  get: (id) => apiGet(`/documentos/${id}`),
  list: (filtros = {}) => {
    const params = new URLSearchParams()
    Object.entries(filtros).forEach(([k, v]) => { if (v) params.set(k, v) })
    return apiGet(`/documentos?${params.toString()}`)
  },
  create: (payload) => apiPost('/documentos', payload),
  update: (id, payload) => apiPatch(`/documentos/${id}`, payload),
  uploadArchivo: (id, file, tipo_adjunto = 'FORMULARIO') => {
    const formData = new FormData()
    formData.append('archivo', file)
    formData.append('tipo_adjunto', tipo_adjunto)
    return apiUpload(`/documentos/${id}/archivos`, formData)
  },
  enviar: (id, body) => apiPost(`/documentos/${id}/enviar`, body),
}

export const bandejas = {
  elaboracion: (page = 1) => apiGet(`/bandeja?tipo=elaboracion&page=${page}`),
  revision: (page = 1) => apiGet(`/bandeja?tipo=revision&page=${page}`),
  aprobacion: (page = 1) => apiGet(`/bandeja?tipo=aprobacion&page=${page}`),
  liberacion: (page = 1) => apiGet(`/bandeja?tipo=liberacion&page=${page}`),
}
```

### Tarea 2.9 — Validación E2E con Chrome DevTools

**Pasos:**
1. `docker restart sgd-frontend` (limpia cache Vite)
2. Abrir `http://localhost:8080/#/login`
3. Login aromero / cofar.2026
4. Navegar a `#/version-editable`
5. Escribir "CC-3" en el input → ver autocomplete con datos reales
6. Click "Buscar" → ver resultado con tipo, titulo, vigencia
7. Navegar a `#/aprobacion-documento`
8. Completar paso 1: seleccionar tipo, gerencia, area, tipo_solicitud="Creación", titulo
9. Verificar que "Código (automático)" muestra `XX-X-XXX/00`
10. Completar paso 2: vigencia auto, requiere evaluacion, requiere lectura, alcance
11. Completar paso 3: 1+ revisores, 1+ aprobadores
12. Click "Firmar y Enviar a Liberación"
13. Modal pide password → escribir "cofar.2026"
14. Verificar toast "Solicitud enviada a ETO correctamente"
15. Verificar en BD: `SELECT * FROM documento_flujo WHERE created_at > NOW() - INTERVAL '5 minutes'`
16. Verificar que `documentos.estatus = EN_REVISION`
17. Capturar screenshots para evidencia

### Tarea 2.10 — Commit + docs

**Commits esperados (2-3):**
- `feat(backend): R2 fase 2 - storage + POST/enviar con firma 2FA + bandejas`
- `feat(frontend): R2 fase 2 - refactor wizard + autocomplete real + documentosApi`
- `docs(pr): sesion 22 R2 fase 2 - cierre FASE 2 + ADRs 042-045 en DECISIONES`

---

## 8. TESTS A ESCRIBIR EN SESIÓN 22

### Tests de storage (5 tests)
- `test_local_storage_save_creates_file` — guarda un bytes y verifica que existe
- `test_local_storage_save_generates_uuid` — verifica que el nombre tiene UUID
- `test_local_storage_delete_removes_file` — borra y verifica que no existe
- `test_local_storage_get_url_returns_path` — devuelve path correcto
- `test_sharepoint_storage_stub_logs_only` — verifica que NO escribe nada

### Tests de POST /documentos (6 tests)
- `test_crear_documento_eto_201` — ETO crea doc → 201 con código
- `test_crear_documento_elaborador_201` — ELABORADOR crea doc → 201
- `test_crear_documento_visualizador_403` — VISUALIZADOR → 403
- `test_crear_documento_sin_titulo_422` — validación Pydantic
- `test_crear_documento_codigo_autogenerado_unico` — 2 docs en misma (area, tipo) → códigos distintos
- `test_crear_documento_audita_create` — `audit_log` tiene entrada CREATE

### Tests de POST /documentos/{id}/archivos (4 tests)
- `test_upload_archivo_valido_201` — archivo .docx de 1MB → 201
- `test_upload_archivo_excede_max_413` — archivo de 25MB → 413
- `test_upload_archivo_mime_invalido_415` — .exe → 415
- `test_upload_archivo_audita_upload` — audit log

### Tests de POST /documentos/{id}/enviar (6 tests) ← LOS MÁS IMPORTANTES
- `test_enviar_password_correcta_200` — 200 + flujo creado + estatus=EN_REVISION
- `test_enviar_password_incorrecta_401` — 401 + NADA persistido (rollback)
- `test_enviar_sin_revisores_422` — wizard sin revisores → 422
- `test_enviar_sin_aprobadores_422` — sin aprobadores → 422
- `test_enviar_doc_ya_enviado_409` — re-enviar → 409
- `test_enviar_captura_ip_y_user_agent` — verificar metadata de firma

### Tests de /bandeja (8 tests)
- 4 endpoints × 2 escenarios cada uno (con docs, sin docs)

### Tests de frontend (3 tests con jsdom)
- VersionEditable renderiza autocomplete después de buscar
- AprobacionDocumento muestra código automático cuando se llenan los campos
- AprobacionDocumento.firmarEnviar llama al endpoint correcto

**Total nuevos tests sesión 22:** ~30 tests. **Cobertura esperada:** 80% del nuevo código.

---

## 9. PROBLEMAS CONOCIDOS Y WORKAROUNDS

### P1: `register_adapter` en conftest.py fue eliminado

**Contexto:** Sesión 21 tuvo que quitar `sqlite3.register_adapter(str, ...)` porque rompía
el adapter de SQLAlchemy para enums. Las funciones custom `hashtext` y
`pg_try_advisory_xact_lock` se registran via `event.listens_for(test_engine.sync_engine,
"connect")`.

**Workaround:** Si en sesión 22 se necesita otra función PostgreSQL en tests, usar el
mismo patrón (event listener + create_function). NUNCA volver a usar `register_adapter`
para str.

### P2: Dependency cycle entre `areas` y `usuarios`

**Contexto:** `areas.jefe_id` FK a `usuarios.id` Y `usuarios.area_id` FK a `areas.id`.
Alembic autogenerate NO puede ordenar las tablas.

**Workaround:** `SAWarning: Cannot correctly sort tables; there are unresolvable cycles...`
es esperado. Se ignora. No intentar fixear con `use_alter=True` (introduce otros bugs).

### P3: Backend corre con `--reload` (cambios se reflejan sin restart)

**Contexto:** El backend en DES corre con `uvicorn --reload`. Cambios en archivos Python
bajo `backend/app/*.py` se reflejan automáticamente.

**Implicación:** En sesión 22, después de cambiar `documentos.py` o cualquier service, el
backend se reinicia solo. NO necesita `docker restart sgd-backend`.

### P4: Vite HMR agresivo

**Contexto:** El frontend en DES usa Vite con HMR. A veces cachea versiones viejas de
los archivos JS.

**Workaround:** Si los cambios no se ven, `docker restart sgd-frontend` y `?_v=N` en la URL.

### P5: Cache de cookies de test

**Contexto:** En sesión 21 se creó `backend/cookies.txt` para smoke tests. Está en
`.gitignore`. Si necesitas volver a crearlo, usar el script Python (no curl directo por
problemas de PowerShell).

**Snippet útil:**
```python
import urllib.request, json
data = json.dumps({'username':'aromero','password':'cofar.2026','auth_source':'local'}).encode()
req = urllib.request.Request('http://localhost:18000/api/v1/login', data=data, headers={'Content-Type':'application/json'}, method='POST')
r = urllib.request.urlopen(req)
with open('backend/cookies.txt', 'w') as f:
    for c in r.headers.get_all('Set-Cookie'):
        f.write(c + '\n')
```

---

## 10. ARCHIVOS A CREAR/MODIFICAR EN SESIÓN 22

### 10.1 Backend (5 archivos nuevos, 1 modificado)

**Nuevos:**
- `backend/app/services/storage.py` (LocalStorage + SharePointStorage stub)
- `backend/app/services/envio_service.py` (lógica atómica de firma 2FA)
- `backend/app/api/v1/bandeja.py` (4 endpoints)
- `backend/app/schemas/bandeja.py` (BandejaItem, BandejaResponse)
- `backend/tests/test_storage.py`
- `backend/tests/test_documentos_enviar.py`
- `backend/tests/test_bandeja.py`

**Modificados:**
- `backend/app/api/v1/documentos.py` (+ 3 endpoints: POST, PATCH, /archivos, /enviar)
- `backend/app/schemas/documento.py` (+ DocumentoCreate, DocumentoUpdate, EnviarRequest)
- `backend/app/main.py` (registrar router /bandeja)

### 10.2 Frontend (2 archivos nuevos, 2 modificados)

**Nuevos:**
- `frontend/src/services/documentosApi.js`

**Modificados:**
- `frontend/src/pages/VersionEditable.js` (autocomplete real)
- `frontend/src/pages/AprobacionDocumento.js` (refactor completo 485 líneas)

### 10.3 Documentación (3 archivos)

**Modificados:**
- `docs/PR/ESTADO.md` (marcar tareas 2.x completadas)
- `docs/PR/BITACORA.md` (entrada sesión 22)
- `docs/PR/DECISIONES.md` (formalizar ADRs 042-045)

---

## 11. CHECKLIST PRE-INICIO (5 min)

Antes de empezar la primera tarea de sesión 22:

- [ ] Stack Up: 8 contenedores DES + backend healthy
- [ ] Rama actual: `r2/wizard-y-version-editable` (NO main, NO epica-1/rama-1)
- [ ] `git log --oneline -1` muestra `e176b79` (último commit de sesión 21)
- [ ] Working tree limpio (`git status` sin cambios)
- [ ] `docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT count(*) FROM documentos"` devuelve 10
- [ ] `curl /api/v1/health` devuelve `{"status":"ok"}`
- [ ] 33 tests nuevos pasan (`pytest backend/tests/test_documentos.py backend/tests/test_correlativo_service.py`)
- [ ] TODOs creados en `todowrite` con este plan (10 tareas de FASE 2)
- [ ] Leí `docs/PR/R2-PLAN-EJECUCION.md` § 4.2 (plan oficial de FASE 2)

---

## 12. CRITERIO DE CIERRE DE FASE 2 (validar antes de cerrar sesión 22)

- [ ] Storage service (LocalStorage + SharePointStorage stub) funcional y testeado
- [ ] POST /documentos + PATCH /documentos/{id} funcionando con RBAC
- [ ] POST /documentos/{id}/archivos con validación MIME + tamaño
- [ ] POST /documentos/{id}/enviar con firma 2FA atómica (PASSWORD OK → 200, PASSWORD FAIL → 401 NADA PERSISTIDO)
- [ ] 4 endpoints /bandeja funcionando
- [ ] VersionEditable.js con autocomplete real (datos de BD)
- [ ] AprobacionDocumento.js refactor completo (3 pasos con datos de BD)
- [ ] Validación E2E con Chrome DevTools: aromero crea doc + firma + aparece en BD
- [ ] 30+ tests nuevos pasando
- [ ] Working tree limpio
- [ ] 2-3 commits atómicos
- [ ] ESTADO + BITACORA + DECISIONES actualizados
- [ ] Tag `v1.1.0-qas` (opcional, solo si se va a deploy a QAS inmediatamente)

---

## 13. NOTAS PARA LA IA (patrones del codebase)

### Backend

- **Patrón de router con RBAC:** `await require_authenticated(request, db)` DENTRO del endpoint, NO como `Depends()`. Ver `app/api/v1/areas.py` y `app/api/v1/gerencias.py`.
- **Patrón de write_audit:** Después de `db.add(obj)` + `db.flush()` + `db.commit()`, llamar `await write_audit(accion, recurso, recurso_id, ...)`. Ver `app/core/audit.py`.
- **Patrón de schema Pydantic v2:** `model_config = ConfigDict(from_attributes=True)` para Output schemas. Ver `app/schemas/gerencia.py`.
- **Patrón de modelo SQLAlchemy 2.0:** `Mapped[T]` y `mapped_column(...)`, NO `Column(...)`. `Mapped[Optional[T]]` para NULLables. `server_default=func.now()` para timestamps. `__tablename__` en plural.
- **Patrón de transacción atómica:** `async with db.begin():` para operaciones multi-write. Ver `app/services/matriz_import_service.py` línea ~80.

### Frontend

- **Patrón de página con Alpine:** `export const page = { init() { ... }, template: \`...\` }`. `init()` registra `Alpine.data('nombre', () => ({...}))`.
- **Patrón de API service:** Cada recurso tiene un archivo en `frontend/src/services/`. Usar atajos `apiGet/Post/Patch/Delete` de `utils/api.js`. Ver `services/parametrizacionApi.js`.
- **Patrón de wizard:** State en el objeto Alpine, `paso` (int), navegación con `nextPaso()`/`prevPaso()`. Ver `pages/AprobacionDocumento.js` líneas 116-121.
- **Patrón de firma 2FA:** `window.authModal?.abrir({titulo, mensaje, onSuccess})` con password. Ver `AprobacionDocumento.js` línea 122-132.

### Convenciones

- **Type hints obligatorios en Python.**
- **Docstrings en español (Google style).**
- **Commits conventional (feat/fix/chore/docs/test/refactor).**
- **Mensajes de commit en inglés.**
- **No agregar emojis a archivos (solo en chat).**

---

## 14. RESUMEN EJECUTIVO PARA EMPEZAR

> **Una frase:** Sesión 22 arranca en la rama `r2/wizard-y-version-editable` con 10 documentos
> en BD, 4 endpoints de lectura funcionando, y 33 tests pasando. El objetivo es cerrar FASE 2
> de R2: storage + POST/enviar con firma 2FA + refactor frontend del wizard + 4 endpoints
> /bandeja. Estimado: 5.5h. Riesgo principal: atomicidad de la firma 2FA. El plan completo
> está en `docs/PR/R2-PLAN-EJECUCION.md` § 4.2 y los detalles por tarea están arriba.

**Próximo paso concreto:** Tarea 2.3 (Storage service) — es prerequisito para 2.2 (upload) y
2.4 (enviar). 20 minutos. Bajo riesgo. Buena forma de entrar en calor.
