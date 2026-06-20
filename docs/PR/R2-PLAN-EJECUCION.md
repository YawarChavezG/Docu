# R2-PLAN-EJECUCION — Wizard de Creación + Versión Editable

> **Documento de planificación operativa de R2 (sesión 21 en adelante).**
> **Alcance:** las 2 páginas `Nueva Solicitud` del sidebar (`/version-editable` + `/aprobacion-documento`) consumidas 100% desde BD, más la tabla CORE `documentos` con su seed, más la tabla `documento_flujo` que persiste el wizard completo.
> **Estado:** 📋 PLAN APROBADO — pendiente ejecución.
> **Última actualización:** 2026-06-17 (sesión 21, día 1 de R2).
> **Rama de trabajo:** `r2/wizard-y-version-editable` (basada en `epica-1/rama-1`, head `737574b`).

---

## 1. Contexto y motivación

R1 está **100% cerrado y desplegado en QAS** (tag `v1.0.0-qas`, ver `ESTADO.md` §"Progreso QAS"). El stack DES tiene 8 servicios Up + 8 backup paralelo, backend healthy (`{"status":"ok","database":"ok"}`).

El usuario (Y. Chávez, COFAR) solicita que las 2 rutas del menú desplegable "Nueva Solicitud" pasen a consumir backend real, no mocks:

- **`/version-editable`** → buscar documento por código con autocomplete desde BD
- **`/aprobacion-documento`** → wizard de 3 pasos que persiste el documento + flujo completo en BD

Las páginas existen en `frontend/src/pages/` pero actualmente usan mocks hardcoded de `frontend/src/data/`. La BD tiene 20 tablas y los 5 catálogos base listos (`gerencias`, `areas`, `usuarios`, `tipos_documento`, `estados`, `configuracion_global`, `semaforizacion_tarea`, `roles`, `modulos`).

---

## 2. Decisiones de diseño (validadas en sesión 21)

### 2.1 Nomenclatura de código (ADR-011 ratificado + ajuste sesión 21)

**Formato:** `{sigla_area}-{codigo_tipo}-{correlativo_3_digitos}/{version_2_digitos}`

**Ejemplo:** `CC-3-005/01` se desglosa:

| Segmento | Significado | Origen en BD |
|---|---|---|
| `CC` | sigla del **área** | `areas.sigla` (donde `gerencia_id=1`=CAL) |
| `3` | código numérico del **tipo de documento** | `tipos_documento.codigo` (POLITICA) |
| `005` | correlativo de 3 dígitos dentro de (área, tipo) | `MAX(correlativo) + 1` en `documentos` |
| `01` | versión de 2 dígitos (default `"00"` para creación nueva) | `documento_flujo.version_snapshot` |

**Separador de versión:** barra `/` (según ejemplo del usuario en sesión 21). El ADR-011 decía `v01` con letra `v`, pero el usuario lo cambió explícitamente.

**Almacenamiento en BD:**
- `documentos.codigo` guarda el segmento `CC-3-005` (sin versión).
- `documento_flujo.version_snapshot` guarda la versión `"00"`.
- El código completo mostrado al usuario se concatena en backend al servir.

### 2.2 Catálogo `tipo_solicitud`

**Decisión:** enum SQLAlchemy en el modelo `DocumentoFlujo`, no tabla aparte.

```python
class TipoSolicitud(str, enum.Enum):
    CREACION = "CREACION"
    ACTUALIZACION = "ACTUALIZACION"
```

**Razón:** solo 2 valores, no cambian nunca, no necesitan FK ni catálogo editable.

**Implicación:** la lógica "es creación → versión `00`" vive en el endpoint, no en BD. En creación, `version_snapshot = "00"` siempre. En actualización, se calcula como `ultima_version + 1` y se permite cualquier valor 2 dígitos.

### 2.3 Trigger SQL de obsolescencia (R2 plan oficial #30)

**Decisión:** DIFERIDO a R5.

**Razón:** el trigger requiere diseño cuidadoso (cálculo de `vigencia` según `aprobacion_at + tipos_documento.periodo_vigencia`), testing de bordes (zonas horarias, fechas límite, etc.), y queremos cerrar R2 sin acoplar el wizard a la lógica de obsolescencia.

**Workaround para Fase 1:** la vigencia se calcula en backend (Python) al servir el endpoint `GET /documentos/{id}`. La columna `documentos.vigencia` se persiste con el valor calculado en ese momento. NO se recalcula en cada lectura (sería costoso).

### 2.4 Refactor frontend: mínima invasión vs completo

**Decisión para Fase 1:** placeholder de `/version-editable` se arregla en Fase 1 (cambio trivial de 1 string). El refactor profundo del wizard queda para Fase 2.

**Razón:** Fase 1 valida el backend (modelos + endpoints + seed + tests) sin acoplar el éxito de Fase 1 al refactor del wizard (más riesgoso). Fase 2 hace el refactor con backend ya estable.

### 2.5 JSONB vs tabla N:M para revisores/aprobadores/difusión

**Decisión:** JSONB en `documento_flujo` para esta iteración.

```python
revisor_ids: Mapped[list[int]] = mapped_column(JSONB, default=list)
aprobador_ids: Mapped[list[int]] = mapped_column(JSONB, default=list)
alcance_difusion_ids: Mapped[list[int]] = mapped_column(JSONB, default=list)
reemplaza_documento_ids: Mapped[Optional[list[int]]] = mapped_column(JSONB, default=None)
```

**Razón:** en R3 las bandejas individuales necesitarán tablas N:M (con timestamps, estados individuales, etc.). Hacer doble trabajo ahora es ineficiente. ADR candidato para documentar en `DECISIONES.md`.

---

## 3. Mapeo del requerimiento → modelo

### 3.1 Tabla `documentos` (CORE — la pieza central del SGD)

Mapeo de los 13 campos pedidos por el usuario:

| # | Campo pedido | Columna BD | Tipo SQLAlchemy | Constraints |
|---|---|---|---|---|
| 1 | `id` | `id` | `Mapped[int] PK` | autoincrement |
| 2 | `gerencia` | `gerencia_id` | `Mapped[int] FK gerencias.id` | NOT NULL, ON DELETE RESTRICT |
| 3 | `areas` | `area_id` | `Mapped[int] FK areas.id` | NOT NULL, ON DELETE RESTRICT |
| 4 | `proceso` | `proceso_id` | `Mapped[Optional[int]]` | sin FK (sin tabla por ahora) |
| 5 | `tipo` | `tipo_documento_id` | `Mapped[int] FK tipos_documento.id` | NOT NULL, ON DELETE RESTRICT |
| 6 | `codigo` | `codigo` | `Mapped[str](20)` | NOT NULL, INDEX (para autocomplete) |
| 7 | `version` | `version` | `Mapped[str](2)` | NOT NULL, default `"00"` |
| 8 | `titulo` | `titulo` | `Mapped[str](200)` | NOT NULL |
| 9 | `aprobacion` | `aprobacion_at` | `Mapped[Optional[datetime]]` | null hasta que se aprueba |
| 10 | `expira` | `expira_at` | `Mapped[Optional[datetime]]` | calculado: `aprobacion_at + tipo.periodo_vigencia` años (si `indefinido=False`) |
| 11 | `vigencia` | `vigencia` | `Mapped[Enum]` | `VIGENTE / POR_VENCER / VENCIDO / OBSOLETO`, default `VIGENTE` |
| 12 | `estatus` | `estatus` | `Mapped[Enum]` | `EN_ELABORACION / EN_REVISION / APROBADO / OBSOLETO`, default `EN_ELABORACION` |
| 13 | `codigo_antiguo` | `codigo_antiguo` | `Mapped[Optional[str](50)]` | manual, legacy |
| 14 | `comentarios_eto` | `comentarios_eto` | `Mapped[Optional[str](50)]` | **CHECK LENGTH(comentarios_eto) <= 50** |

**Columnas de auditoría (estándar del codebase):**
- `created_at`, `updated_at` (timestamps)
- `created_by_id`, `updated_by_id` (FK `usuarios.id`, SET NULL)
- `activo` (bool, default True — borrado lógico)

**Constraints únicos e índices:**
- `UNIQUE(area_id, tipo_documento_id, correlativo)` — define el correlativo monotónico
- `INDEX(codigo)` — para autocomplete `LIKE 'CC-3-%'`
- `INDEX(vigencia, expira_at)` — para querys "por vencer" en ListaMaestra (R3-R5)
- `INDEX(estatus)` — para filtros de bandejas

**Constraint adicional CHECK:**
- `CHECK (vigencia != 'VENCIDO' OR estatus IN ('APROBADO', 'OBSOLETO'))` — regla del usuario: "Un documento que esté vencido, sí o sí debe estar aprobado u Obsoleto."

### 3.2 Tabla `documento_flujo` (instancia del wizard)

Snapshot del wizard completo ligado a un documento. Permite que el documento histórico preserve el contexto (área renombrada, etc.).

| Columna | Tipo | Origen | Notas |
|---|---|---|---|
| `id` | `int PK` | autoincrement | |
| `documento_id` | `int FK documentos.id` | al crear flujo | ON DELETE CASCADE (si se borra el doc, se borra el flujo) |
| `tipo_solicitud` | `Enum` (`CREACION`/`ACTUALIZACION`) | wizard paso 1 | |
| `estado_actual_id` | `int FK estados.id` | default `ELABORACION` (id=1) | transiciona con el workflow |
| `gerencia_id` | `int FK gerencias.id` | snapshot | del wizard paso 1 |
| `area_id` | `int FK areas.id` | snapshot | del wizard paso 1 |
| `tipo_documento_id` | `int FK tipos_documento.id` | snapshot | del wizard paso 1 |
| `codigo_snapshot` | `str(20)` | generado al crear | `CC-3-005` (sin versión) |
| `version_snapshot` | `str(2)` | default `"00"` (creación) o `ultima+1` (actualización) | |
| `titulo` | `str(200)` | wizard paso 1 | |
| `elaborador_id` | `int FK usuarios.id` | del `auth.user.id` al firmar | SET NULL |
| `cargo_elaborador` | `str(100)` | snapshot de `auth.user.cargo` | |
| `fecha_solicitud` | `datetime` | `NOW()` | |
| `justificacion` | `Optional[str](1000)` | wizard paso 1 (opcional) | |
| `tiempo_vigencia_anos` | `int` | snapshot del `tipo_documento.periodo_vigencia` | se congela al firmar |
| `requiere_evaluacion` | `bool` | wizard paso 2 | |
| `requiere_control_lectura` | `bool` | wizard paso 2 | |
| `alcance_difusion_ids` | `JSONB list[int]` | wizard paso 2 | array de gerencia_id/area_id |
| `revisor_ids` | `JSONB list[int]` | wizard paso 3 | mínimo 1 |
| `aprobador_ids` | `JSONB list[int]` | wizard paso 3 | mínimo 1 |
| `reemplaza_documento_ids` | `Optional[JSONB list[int]]` | wizard paso 3 (condicional) | si `reemplaza='si'` |
| `firma_usuario_id` | `int FK usuarios.id` | auth del que firma | |
| `firma_at` | `datetime` | `NOW()` | |
| `firma_ip` | `str(45)` | del request | |
| `firma_user_agent` | `str(500)` | del request | |
| `created_at`, `updated_at`, `created_by_id` | timestamps + FK | estándar | |
| `activo` | `bool` | default True | borrado lógico |

### 3.3 Tabla `archivos_adjuntos` (storage)

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `int PK` | |
| `documento_flujo_id` | `int FK documento_flujo.id` | ON DELETE CASCADE |
| `usuario_id` | `int FK usuarios.id` | quien subió |
| `nombre_original` | `str(255)` | nombre con el que subió el usuario |
| `nombre_storage` | `str(255)` | UUID + extensión interna |
| `mime_type` | `str(100)` | validado contra whitelist |
| `tamano_bytes` | `int` | validado contra `configuracion_global.max_tamano_archivo_mb * 1024 * 1024` |
| `tipo_adjunto` | `Enum` | `PRINCIPAL` o `FORMULARIO` |
| `storage_backend` | `str(50)` | `LOCAL` (DES) o `SHAREPOINT` (QAS/PROD) |
| `storage_path` | `str(500)` | ruta interna |
| `created_at` | `datetime` | |

**Validaciones en endpoint de upload:**
- `tamano_bytes <= configuracion_global.max_tamano_archivo_mb * 1024 * 1024` (20MB por defecto)
- `count(archivos_por_flujo) <= configuracion_global.max_archivos_por_solicitud` (20 por defecto)
- `mime_type IN whitelist`: `application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel, image/png, image/jpeg`

### 3.4 Storage service (stub para DES)

```python
# backend/app/services/storage.py

class StorageBackend(Protocol):
    def save(self, file: UploadFile, destino: str) -> tuple[str, int]: ...
    def delete(self, path: str) -> None: ...

class LocalStorage:
    """DES: persiste en /app/storage/uploads/{uuid}.{ext}. Real."""
    ROOT = "/app/storage/uploads"

class SharePointStorage:
    """DES: stub. QAS/PROD: implementación con Microsoft Graph API."""
```

**Para Fase 1:** `LocalStorage` funciona, `SharePointStorage` solo loguea la intención.

### 3.5 Servicio `correlativo_service.py`

Necesario para la **autogeneración atómica del correlativo** dentro de `(area_id, tipo_documento_id)`.

```python
async def siguiente_correlativo(
    db: AsyncSession,
    area_id: int,
    tipo_documento_id: int,
) -> int:
    """SELECT COALESCE(MAX(correlativo), 0) + 1
       FROM documentos
       WHERE area_id = :a AND tipo_documento_id = :t
       FOR UPDATE  -- lock pesimista en la fila para concurrencia"""
```

**Implementación en SQLAlchemy 2.0 async:**
```python
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

stmt = (
    select(func.coalesce(func.max(Documento.correlativo), 0) + 1)
    .where(Documento.area_id == area_id)
    .where(Documento.tipo_documento_id == tipo_documento_id)
    .with_for_update()
)
result = await db.execute(stmt)
return result.scalar_one()
```

**Por qué `FOR UPDATE` y no `INSERT...RETURNING`:** queremos que el correlativo sea monotónicamente creciente dentro de (área, tipo), sin huecos, aún si se hace rollback. El `FOR UPDATE` bloquea las filas del rango consultado para que otro worker no lea el mismo MAX hasta que commiteemos.

**Fallback si `FOR UPDATE` async da problemas:** usar `pg_try_advisory_xact_lock(hashtext('correlativo:' || area_id || ':' || tipo_documento_id))` al inicio de la transacción. Más portable.

### 3.6 Endpoints nuevos (Fase 1 + Fase 2)

**Fase 1 (backend, lo que se hace en sesión 21):**

| Método | Path | Auth | Función |
|---|---|---|---|
| GET | `/api/v1/documentos/buscar?q={texto}` | autenticado | autocomplete para /version-editable. Top 10 matches por `codigo ILIKE q%` o `titulo ILIKE %q%`. Devuelve `[{id, codigo, titulo, tipo, vigencia}]` |
| GET | `/api/v1/documentos/preview-codigo?tipo_id=X&area_id=Y&tipo_solicitud=Z` | autenticado | genera código sin persistir. Devuelve `{codigo, version, correlativo_sugerido}`. Usa `correlativo_service` |
| GET | `/api/v1/documentos/{id}` | autenticado | detalle completo + joins a gerencia/area/tipo/estado |
| GET | `/api/v1/documentos?gerencia_id=&area_id=&vigencia=&estatus=&page=` | autenticado | filtros para ListaMaestra (paginado) |

**Fase 2 (wizard completo, sesión 22):**

| Método | Path | Auth | Función |
|---|---|---|---|
| POST | `/api/v1/documentos` | ETO/ELABORADOR | crea documento (EN_ELABORACION) + flujo inicial |
| PATCH | `/api/v1/documentos/{id}` | elaborador/ETO | edita campos antes de firmar |
| POST | `/api/v1/documentos/{id}/archivos` | elaborador | upload archivo (stub) |
| DELETE | `/api/v1/documentos/{id}/archivos/{archivo_id}` | elaborador | borra archivo |
| POST | `/api/v1/documentos/{id}/enviar` | elaborador | **firma 2FA** + transición a EN_REVISION |
| GET | `/api/v1/bandeja?tipo=elaboracion` | elaborador | mis docs en elaboración |
| GET | `/api/v1/bandeja?tipo=revision` | revisor | docs a revisar |
| GET | `/api/v1/bandeja?tipo=aprobacion` | aprobador | docs a aprobar |
| GET | `/api/v1/bandeja?tipo=liberacion` | ETO | docs finalizados |

**RBAC enforcement:** helper `require_role(rol_codes=[...])` que reutiliza el patrón de `require_eto_or_admin` (ya existe en `app/core/permissions.py`).

### 3.7 Refactor frontend (Fase 2)

**`/version-editable` (93 líneas):**
- `setTimeout` mock → `await apiGet('/documentos/buscar?q=...')`
- Autocomplete con `<datalist>` (patrón ya usado en `AprobacionDocumento.js` línea 469)
- Placeholder cambiado a `CC-3-005/01` (Fase 1: solo string; Fase 2: lógica completa)
- Mostrar tipo + título en el dropdown

**`/aprobacion-documento` (485 líneas):**
- Reemplazar imports de mocks por `await gerencias.list()`, `tiposDocumento.list()`, `usuarios.listActivos()`, etc.
- `revisores/aprobadores`: selector que filtre `GET /usuarios?rol=ELABORADOR - REVISOR` o `ELABORADOR - REVISOR - APROBADOR`
- `codigoAuto`: llamar a `GET /documentos/preview-codigo` (no persiste, solo calcula)
- `firmarEnviar`: `POST /documentos/{id}/enviar` con body `{password: "..."}` (validación 2FA vía `POST /verify-password`)
- Reemplazar `arbolOutlookDB` por árbol construido dinámicamente desde `/gerencias?con_areas=true`
- `requiere_vigencia`: leer de `tipos_documento.periodo_vigencia` (no hardcoded "4 años")
- `reemplaza/chipsReemplazo`: nueva lógica que al confirmar llama a `POST /documentos/{id}/reemplazar`

### 3.8 Seed de 10 documentos (Fase 1, después de migración)

**`backend/scripts/seed_documentos.py`** — idempotente, basado en BD real.

**Lógica de selección:**
- 10 áreas elegidas al azar de las 49 sembradas (CC, DT, EST, PRO, BET, ACD, etc.)
- 10 tipos distribuidos de los 13 sembrados
- 10 títulos coherentes con el área (templates parametrizados)
- Códigos autogenerados por `correlativo_service` (no hardcoded)

**Distribución de estatus y vigencia:**

| estatus | count | vigencias | comentarios |
|---|---|---|---|
| `APROBADO` | 5 | 3 VIGENTE, 1 POR_VENCER, 1 VENCIDO | `aprobacion_at` entre hace 3 años y hoy, `expira_at` calculado |
| `EN_ELABORACION` | 2 | 2 VIGENTE | sin `aprobacion_at` ni `expira_at` |
| `EN_REVISION` | 2 | 2 VIGENTE | igual sin aprobar |
| `OBSOLETO` | 1 | 1 OBSOLETO | `aprobacion_at` hace 5 años |

**Regla del usuario enforced:** el único VENCIDO está con `estatus=APROBADO` (no `EN_ELABORACION`).

**`codigo_antiguo`:** formato `LEG-{area_id}-{tipo_id}-{i}` (legacy ficticio).
**`comentarios_eto`:** rotación de 3 mensajes cortos: `"OK primera versión"`, `"Pendiente firma ETO"`, `"Aprobado en sesión X"`.

### 3.9 Datos de sesión para el wizard (cómo se obtiene el usuario actual)

El wizard ya tiene acceso a `Alpine.store('auth').user` con los campos:
- `username`, `nombre_completo`, `cargo`, `iniciales`, `email`
- `area_id`, `gerencia_sigla`, `area_sigla`

El campo `Elaborador responsable` se jala de `auth.user.nombre_completo`.
El campo `Cargo` se jala de `auth.user.cargo`.

Esto YA FUNCIONA en el frontend actual (solo lo conectamos al submit del wizard en Fase 2).

---

## 4. Plan de ejecución dividido en 2 FASES

### 4.1 FASE 1 — Backend + BD + validación E2E (sesión 21)

**Objetivo:** dejar la BD lista con las 3 tablas nuevas + migración + seed + 4 endpoints de lectura + correlativo atómico + 1 fix trivial de placeholder. Validar con tests pytest + queries directas a BD.

**Duración estimada:** 3.5h.

**Tareas (en orden estricto):**

| # | Tarea | Archivos | Tiempo |
|---|---|---|---|
| 1.1 | Crear modelos SQLAlchemy 2.0: `Documento`, `DocumentoFlujo`, `ArchivoAdjunto` + enums `VigenciaDocumento`, `EstatusDocumento`, `TipoSolicitud`, `TipoAdjunto` | `backend/app/models/documento.py`, `documento_flujo.py`, `archivo_adjunto.py` | 25min |
| 1.2 | Registrar los 3 modelos nuevos en `app/models/__init__.py` | `backend/app/models/__init__.py` | 5min |
| 1.3 | Crear schemas Pydantic v2 para input/output (DocumentoCreate, DocumentoOut, DocumentoFlujoOut, etc.) | `backend/app/schemas/documento.py` | 15min |
| 1.4 | Crear `correlativo_service.py` con `SELECT FOR UPDATE` async | `backend/app/services/correlativo_service.py` | 30min |
| 1.5 | Crear endpoint router `/api/v1/documentos` con los 4 endpoints de lectura (buscar, preview-codigo, GET by id, GET filtros) | `backend/app/api/v1/documentos.py` + registrar en `main.py` | 45min |
| 1.6 | Crear servicio `vigencia_service.py` con función `calcular_vigencia(documento)` (Python puro, no trigger SQL) | `backend/app/services/vigencia_service.py` | 15min |
| 1.7 | Generar migración Alembic 014 (autogenerate) | `backend/alembic/versions/` (nuevo archivo) | 10min |
| 1.8 | Aplicar migración + verificar schema con `\d` en psql | `docker exec sgd-backend alembic upgrade head` | 5min |
| 1.9 | Crear `backend/scripts/seed_documentos.py` (idempotente) | nuevo archivo | 30min |
| 1.10 | Correr seed + verificar counts con `SELECT COUNT(*) FROM documentos` | bash | 5min |
| 1.11 | Tests pytest de los 4 endpoints + correlativo_service | `backend/tests/test_documentos.py` | 30min |
| 1.12 | Validar con curl: GET /documentos/buscar?q=CC-3 + preview-codigo | bash + curl | 10min |
| 1.13 | Fix trivial placeholder de `/version-editable` (solo el string) | `frontend/src/pages/VersionEditable.js` línea 54 | 2min |
| 1.14 | Commit atómico + actualizar ESTADO + BITACORA (sesión 21) | git + docs | 10min |

**Criterio de cierre de Fase 1:**
- Migración 014 aplicada.
- 4 endpoints responden 200 con datos reales.
- Seed corre idempotente (segunda corrida = 0 inserts).
- 10 documentos sembrados con códigos como `CC-3-001/00`, `DT-5-001/00`, etc.
- `pytest tests/test_documentos.py` pasa 100%.
- `curl /api/v1/documentos/buscar?q=CC-3` devuelve resultados.
- `curl /api/v1/documentos/preview-codigo?tipo_id=3&area_id=1&tipo_solicitud=CREACION` devuelve código nuevo.
- Placeholder de `/version-editable` muestra `CC-3-005/01` en el browser.

### 4.2 FASE 2 — Frontend wizard + endpoints POST + E2E (sesión 22)

**Objetivo:** wizard completo funcional end-to-end con persistencia en BD + firma 2FA + 1 caso de demo verificado.

**Duración estimada:** 5.5h.

**Tareas (en orden estricto):**

| # | Tarea | Archivos | Tiempo |
|---|---|---|---|
| 2.1 | Extender router con POST /documentos + PATCH /documentos/{id} | `backend/app/api/v1/documentos.py` | 30min |
| 2.2 | Extender router con POST /documentos/{id}/archivos (upload stub) | `backend/app/api/v1/documentos.py` | 20min |
| 2.3 | Crear storage service (`LocalStorage` real + `SharePointStorage` stub) | `backend/app/services/storage.py` | 20min |
| 2.4 | Endpoint POST /documentos/{id}/enviar con firma 2FA (cadena con /verify-password) | `backend/app/api/v1/documentos.py` | 40min |
| 2.5 | Endpoints de bandeja (4 GET /bandeja?tipo=X) | `backend/app/api/v1/bandeja.py` (nuevo) | 30min |
| 2.6 | Frontend: refactor `VersionEditable.js` con autocomplete real | `frontend/src/pages/VersionEditable.js` | 25min |
| 2.7 | Frontend: refactor `AprobacionDocumento.js` completo (3 pasos) | `frontend/src/pages/AprobacionDocumento.js` | 1h30min |
| 2.8 | Frontend: nuevo servicio `frontend/src/services/documentosApi.js` | nuevo archivo | 30min |
| 2.9 | Validar wizard E2E con login (aromero) + crear doc + firmar + ver en BD | Chrome DevTools | 30min |
| 2.10 | Tests pytest adicionales (POST + firma 2FA) | `backend/tests/test_documentos_enviar.py` | 30min |
| 2.11 | Commit atómico + actualizar ESTADO + BITACORA (sesión 22) + ADR-042 en DECISIONES | git + docs | 20min |

**Criterio de cierre de Fase 2:**
- Wizard `/aprobacion-documento` funciona end-to-end: login → completar 3 pasos → firmar → documento persistido en BD con todos los campos del wizard.
- Búsqueda en `/version-editable` muestra resultados reales de BD.
- POST /enviar rechaza con 401 si la password es incorrecta.
- POST /enviar transiciona estatus a EN_REVISION.
- Tests pytest de enviar (con mock de verify-password) pasan 100%.
- Demo verificada: aromero crea doc "PR-5-001/00" → ETO lo ve en su "bandeja de liberación" (aunque sea un array de IDs en JSONB por ahora).

---

## 5. Cuidados, riesgos y trampas

### 5.1 Trampas conocidas (de BITACORA anteriores)

1. **`AsyncSession` no es Pydantic field** (sesión 6): usar `await require_eto_or_admin(request, db)` DENTRO del endpoint, NO como `Depends()`.
2. **`Area` import local en if-block** (sesión 6): importar al top del archivo.
3. **Rutas genéricas al final** (sesión 6): `/{user_id}` DEBE ir al final del router, sino captura paths específicos.
4. **MissingGreenlet con PATCH** (sesión 6): `expire_on_commit=True` invalida selectinload. Fix: nuevo query con selectinload post-commit.
5. **Borrado lógico NO cascade** (ADR-015, sesión 6): `areas.sigla UNIQUE(gerencia_id, sigla)`. Lo mismo aplica a `documentos`: usar `activo=False` para borrado, no DELETE físico.
6. **CSRF**: api.js envía `X-CSRF-Token` pero backend aún no lo valida (B3, pre-QAS-public). NO bloquea para DES.
7. **Backend EN Docker en DES** (ADR-013 ratificado): `--reload` activo, cambios en `backend/app/*.py` se reflejan sin reiniciar.
8. **PowerShell + http.client filtra cookies** (B6): usar `urllib.request.Request` con headers manuales o `test_*.py` con fix.
9. **Cache Vite agresivo** (sesión 9): `docker restart sgd-frontend` limpia. Usar `?_v=N` en URL para forzar reload.

### 5.2 Riesgos específicos de R2

| # | Riesgo | Mitigación |
|---|---|---|
| R1 | `SELECT FOR UPDATE` async con SQLAlchemy 2.0 puede dar `MissingGreenlet` | Fallback: `pg_try_advisory_xact_lock(hashtext(...))` |
| R2 | JSONB con SQLAlchemy async: requiere `JSON().with_variant(JSONB(), "postgresql")` (patrón ya en `audit_log`) | Replicar patrón de `app/models/audit_log.py` |
| R3 | `vigencia != VENCIDO OR estatus IN (APROBADO, OBSOLETO)` CHECK constraint: Alembic autogenerate a veces no captura CHECKs custom | Escribir el CHECK manualmente en la migración, no en el modelo |
| R4 | Firma 2FA debe ser **atómica**: si la BD falla después de validar password, no debe quedar como firmado | Transacción única con `write_audit` + commit al final; rollback en excepción borra la firma |
| R5 | `correlativo_service` con concurrencia: si 2 requests simultáneos del mismo (área, tipo) leen el mismo MAX, pueden colisionar | `SELECT FOR UPDATE` con `await db.execute()` dentro de `async with db.begin()` |
| R6 | Upload de archivos: el `max_tamano_archivo_mb` se lee de BD al vuelo, no hardcoded | Helper `await get_config(db, "max_tamano_archivo_mb")` cacheado en memoria por request |
| R7 | `seed_documentos.py` debe ser idempotente: 2da corrida no debe duplicar | Usar `INSERT ... ON CONFLICT (area_id, tipo_documento_id, correlativo) DO NOTHING` |
| R8 | Wizard frontend usa mocks de `data/users.js` para revisores; si se cambia el seed, los mocks quedan inconsistentes | En Fase 2, reemplazar TODO `listaEmpleados` por `await usuarios.list({rol: 'ELABORADOR - REVISOR'})` |
| R9 | `auth.user.cargo` puede no estar en /me si el usuario no hizo refresh | El `refreshFromBackend()` en sesión 18 ya carga cargo. Verificar antes de Fase 2. |
| R10 | El árbol de difusión (gerencias → areas) requiere endpoint que devuelva jerarquía | `GET /gerencias?con_areas=true` (extensión del endpoint existente) |

### 5.3 Reglas de oro para esta sesión

1. **NO inventar datos.** Si una tabla no existe, crearla con Alembic. No hardcodear arrays.
2. **NO usar mocks del frontend en backend.** La BD es la única fuente de verdad.
3. **Toda mutación pasa por API.** El frontend NUNCA escribe directamente a BD.
4. **Tests antes de marcar como hecho.** Cada endpoint nuevo tiene su test pytest.
5. **Documentar decisiones en `DECISIONES.md`** (formato ADR: contexto, decisión, consecuencia).
6. **Idempotencia en seeds:** correr 2 veces = 0 cambios netos.
7. **Borrado lógico siempre** (`activo=False`), nunca DELETE físico.
8. **Audit log con `write_audit()`** en toda mutación (patrón de sesión 6).
9. **Commits atómicos y convencionales** (`feat(...)`, `fix(...)`, `chore(...)`).
10. **Working tree limpio antes de cerrar sesión** (commit + push al final).

---

## 6. Archivos a crear / modificar

### 6.1 Archivos NUEVOS (Fase 1)

```
backend/app/models/documento.py
backend/app/models/documento_flujo.py
backend/app/models/archivo_adjunto.py
backend/app/schemas/documento.py
backend/app/schemas/documento_flujo.py
backend/app/schemas/archivo_adjunto.py
backend/app/services/correlativo_service.py
backend/app/services/vigencia_service.py
backend/app/api/v1/documentos.py
backend/scripts/seed_documentos.py
backend/tests/test_documentos.py
backend/alembic/versions/<timestamp>-<hash>_add_documentos_y_flujo.py
docs/PR/R2-PLAN-EJECUCION.md  ← este archivo
```

### 6.2 Archivos MODIFICADOS (Fase 1)

```
backend/app/models/__init__.py          # registrar 3 modelos nuevos
backend/app/main.py                     # registrar router /documentos
frontend/src/pages/VersionEditable.js   # placeholder
docs/PR/ESTADO.md                       # marcar tareas 23, 24, 28
docs/PR/BITACORA.md                     # entrada sesión 21
```

### 6.3 Archivos NUEVOS (Fase 2)

```
backend/app/services/storage.py
backend/app/api/v1/bandeja.py
backend/app/schemas/bandeja.py
backend/tests/test_documentos_enviar.py
frontend/src/services/documentosApi.js
```

### 6.4 Archivos MODIFICADOS (Fase 2)

```
backend/app/api/v1/documentos.py        # extender con POST/PATCH/enviar
backend/app/main.py                     # registrar router /bandeja
frontend/src/pages/VersionEditable.js   # autocomplete real
frontend/src/pages/AprobacionDocumento.js  # refactor completo
docs/PR/ESTADO.md                       # marcar tareas 25-27, 29-41
docs/PR/BITACORA.md                     # entrada sesión 22
docs/PR/DECISIONES.md                  # ADR-042 JSONB vs N:M
```

---

## 7. Convenciones a respetar

### 7.1 Backend (Python / FastAPI / SQLAlchemy 2.0)

- PEP 8 + Black (line-length 100)
- Type hints obligatorios
- Docstrings en español (Google style)
- Imports: stdlib → third-party → local
- Nombres de modelos en singular (`Documento`, no `Documentos`)
- `__tablename__` en singular minúscula (`"documento"`)
- `Mapped[T]` y `mapped_column(...)` (no `Column(...)`)
- `Mapped[Optional[T]]` para NULLables
- `server_default=func.now()` para timestamps
- `ForeignKey("tabla.columna", ondelete="RESTRICT"|"CASCADE"|"SET NULL")`
- `relationship("Modelo", back_populates="atributo")`

### 7.2 Frontend (Alpine.js + Vite)

- ES modules (`type: module`)
- Sin TypeScript
- Componentes Alpine en `pages/*.js` (patrón original)
- 1 componente por archivo
- `init()` registra el componente con `Alpine.data('nombre', () => ({...}))`
- `template` es el HTML
- Usar `apiFetch` (o atajos `apiGet/Post/Patch/Delete`) de `utils/api.js`
- NUNCA `fetch(...)` directo en páginas

### 7.3 Migraciones Alembic

- Nombre: `<timestamp>-<hash>_descripcion_corta.py`
- Usar `alembic revision --autogenerate -m "descripcion"` para generar
- Revisar el archivo generado ANTES de commitear
- Para CHECK constraints custom, escribir manualmente
- Para enums, dejar que Alembic los cree
- Aplicar con `docker exec sgd-backend alembic upgrade head`

### 7.4 Commits

- Conventional commits: `tipo(scope): descripción`
- Tipos: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`
- 1 commit por tarea (no commits "WIP")
- Mensaje en inglés (es el estándar del proyecto)

---

## 8. Métricas de éxito

### 8.1 Fase 1 (cierre = migración 014 + 4 endpoints + seed + tests)

- [ ] 3 modelos nuevos creados + registrados en `__init__.py`
- [ ] Migración 014 aplicada con `alembic upgrade head`
- [ ] 4 endpoints devuelven 200 con datos reales
- [ ] 10 documentos sembrados (verificable con `SELECT COUNT(*) FROM documentos`)
- [ ] `correlativo_service` test pasa con concurrencia (10 inserts paralelos → 10 correlativos únicos)
- [ ] `pytest tests/test_documentos.py` 100% verde
- [ ] `curl /api/v1/documentos/buscar?q=CC` devuelve 1+ resultados
- [ ] `curl /api/v1/documentos/preview-codigo?tipo_id=3&area_id=1&tipo_solicitud=CREACION` devuelve `{"codigo":"CC-3-011/00", ...}`
- [ ] Placeholder de `/version-editable` muestra `CC-3-005/01` en el browser
- [ ] Working tree limpio + 1+ commits + ESTADO + BITACORA actualizados

### 8.2 Fase 2 (cierre = wizard E2E + firma 2FA + demo)

- [ ] Wizard `/aprobacion-documento` completa los 3 pasos sin errores en consola
- [ ] Login aromero + completar wizard + firmar con password correcta → documento persistido
- [ ] `SELECT * FROM documento_flujo WHERE elaborador_id=1` muestra el flujo nuevo
- [ ] Firmar con password incorrecta → 401 + toast de error (no se persiste nada)
- [ ] Tests pytest de POST/enviar pasan
- [ ] Demo grabada: video o screenshots de los 3 pasos + BD con datos
- [ ] 1+ commits + ESTADO + BITACORA + ADR-042 en DECISIONES

---

## 9. Checklist pre-Fase-1 (5 min)

Antes de arrancar la primera tarea de Fase 1, validar:

- [ ] Stack Up: 8 contenedores DES + backend healthy
- [ ] Rama actual: `r2/wizard-y-version-editable` creada desde `epica-1/rama-1`
- [ ] Working tree limpio
- [ ] `docker exec sgd-postgres psql -U sgd -d sgd -c "\dt"` muestra 20 tablas
- [ ] `curl /api/v1/health` devuelve `{"status":"ok"}`
- [ ] `git log --oneline -1` muestra el head actual
- [ ] TODOs creados en `todowrite` con este plan

---

## 10. Próxima sesión (sesión 22, si la hay)

- Ejecutar Fase 2 completa
- Si queda tiempo: tests E2E con Chrome MCP + grabar demo
- Si queda más tiempo: tag `v1.1.0-qas` + deploy a QAS con los fixes preventivos
- Backlog pre-PROD: trigger SQL obsolescencia, trigger de auditoría, security hardening (CSP, CSRF middleware)
