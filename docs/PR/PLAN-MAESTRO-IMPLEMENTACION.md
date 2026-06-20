# PLAN MAESTRO DE IMPLEMENTACIÓN — COFAR SGD

> **Documento técnico definitivo.**
> Contiene todas las fases de implementación del flujo documental completo (R2 + R3 + integraciones), ordenadas lógicamente para no romper nada en el camino.
>
> **Basado en:**
> - URS original (2916 líneas de Historias de Usuario)
> - Know-how del dueño del producto (Y. Chávez)
> - Código actual del monorepo (30 tablas, 337 tests PASS)
> - ADRs y LEARNINGS de 39 sesiones previas
>
> **Última actualización:** 2026-06-20
> **Rama de trabajo:** `r3/workflow-revision-aprobacion`

---

## Índice de Fases

| Fase | Nombre | Depende de | Riesgo |
|------|--------|-----------|--------|
| 0 | Correcciones Inmediatas (Hotfixes) | Nada | 🟢 Bajo |
| 1 | Almacenamiento y Nomenclatura Definitiva | Fase 0 | 🟡 Medio |
| 2 | Control de Descargas de Editables | Fase 0 | 🟡 Medio |
| 3 | Catálogo de Procesos | Fase 0 | 🟢 Bajo |
| 4 | Timeline / Bitácora del Flujo Documental | Fase 1, 0 | 🟠 Medio-Alto |
| 5 | Servicios Core del Workflow (R3 Fase 2) | Fase 4 | 🔴 Alto |
| 6 | Integración Flujo ETO → Revisores → Aprobadores | Fase 5 | 🔴 Alto |
| 7 | Delegación y Timeout | Fase 5 | 🟠 Medio |
| 8 | Sistema de Notificaciones por Correo | Fase 5 | 🟡 Medio |
| 9 | Integración Microsoft Graph / SharePoint | Fase 1 | 🟠 Medio |
| 10 | PDF Final, Carátula y Carimbo | Fase 6 | 🟠 Medio |
| 11 | Limpieza de Datos Mock y Migraciones | Fase 6 | 🟡 Medio |
| 12 | Módulo de Reasignación ETO | Fase 7 | 🟡 Medio |
| T-A | Seguridad y Hardening | Transversal | 🟠 Medio |
| T-B | Performance y Escalabilidad | Transversal | 🟢 Bajo |
| T-C | Monitoreo y Operaciones | Transversal | 🟢 Bajo |
| T-D | Testing Integral y Migración de Datos | Transversal | 🟡 Medio |
| T-E | Documentación y API | Transversal | 🟢 Bajo |

---

## Convenciones usadas en este documento

```
📁 backend/app/api/v1/...  → archivo backend
📁 frontend/src/pages/...  → archivo frontend
🔧                            → tarea técnica
✅                            → criterio de cierre / verificación
🧪                            → escenario de prueba
🐳                            → comando Docker
```

---

# FASE 0: CORRECCIONES INMEDIATAS (HOTFIXES)

> **Objetivo:** Corregir errores existentes que impactan la UX y la consistencia de datos. Son cambios pequeños, localizados, con riesgo mínimo.
>
> **Duración estimada:** 2-3h
> **Riesgo:** 🟢 Bajo — ningún cambio rompe BD ni altera flujos existentes.
> **Prerrequisitos:** Stack DES arriba, 337 tests PASS.

---

## Tarea 0.1 — Separador de versión: `/` → ` ` (espacio + V)

### Descripción
El formato actual muestra `CC-3-005/00`. Debe ser `CC-3-005 V00`. El cambio afecta displays, no la BD (los campos `codigo` y `version` están separados en BD y no se tocan).

### Archivos a modificar

**Backend:**

1. `📁 backend/app/services/correlativo_service.py` — función `formatear_codigo_completo()` (línea 129)
   ```python
   # ANTES:
   return f"{codigo}/{version}"
   # DESPUÉS:
   return f"{codigo} V{version}"
   ```

2. `📁 backend/app/services/correlativo_service.py` — función `generar_nombre_completo()` (línea 141)
   Ya genera correctamente `{codigo} {TITULO} V{version}`. **No tocar.**

3. `📁 backend/app/api/v1/documentos.py` — endpoints que construyen `codigo_completo`:
   - `GET /actualizables` → línea `codigo_completo=f"{r.codigo}/{r.version}"` → cambiar a `f"{r.codigo} V{r.version}"`
   - `GET /documentos` (lista paginada) → línea similar → cambiar
   - `GET /documentos/buscar` → `codigo_completo` ya se genera con `formatear_codigo_completo()` → ✅ automático

**Frontend:**

4. `📁 frontend/src/pages/VersionEditable.js` — línea 227:
   ```javascript
   // ANTES: (r.codigo_completo || r.cod + ' ' + ...)
   // El backend ya devolverá el formato correcto si usamos codigo_completo
   // VERIFICAR que el frontend no construya manualmente con "/"
   ```

5. `📁 frontend/src/pages/ListaMaestra.js` — línea 272:
   ```javascript
   // Buscar title con "... V" + d.ver → verificar que no use "/"
   ```

6. `📁 frontend/src/pages/Bandeja.js` — líneas 17, 28, 38:
   Verificar que `title` no renderice formato con barra.

### Validación

```bash
# 1. pytest debe seguir pasando
cd backend && .venv\Scripts\python -m pytest tests/ -q --tb=short

# 2. Verificar endpoint devuelve nuevo formato
curl.exe http://localhost:18000/api/v1/documentos/1
# Buscar "codigo_completo": "CC-5-001 V00"

# 3. Verificar preview-codigo
curl.exe "http://localhost:18000/api/v1/documentos/preview-codigo?tipo_id=5&area_id=1&tipo_solicitud=CREACION"
# Debe mostrar "codigo_completo": "CC-5-XXX V00"
```

### 🧪 Escenario de prueba (Chrome MCP)

```
1. Login como eto_test
2. Navegar a /#/aprobacion-documento
3. Seleccionar: Tipo=Procedimiento, Gerencia=CAL, Area=CC
4. Verificar que el código automático muestra: "CC-5-XXX V00" (con espacio + V, sin /)
5. Navegar a /#/bandeja
6. Verificar que los códigos en la tabla muestran formato correcto
```

### ✅ Criterio de cierre
- `pytest` 337/337 PASS (o 340+)
- `curl /documentos/1` → `codigo_completo: "CC-5-001 V00"`
- `curl /documentos/preview-codigo` → `codigo_completo: "CC-5-XXX V00"`
- Frontend no muestra ninguna barra `/` en códigos de documento

---

## Tarea 0.2 — Agregar credenciales Microsoft Graph + SMTP al `.env`

### Descripción
Persistir las credenciales en el archivo `.env` y en `Settings` de config.py para que estén disponibles cuando implementemos las integraciones. No se activan todavía (`GRAPH_ENABLED=false`, `SMTP_ENABLED=false`).

### Archivos a modificar

1. `📁 .env` (raíz del repo) — agregar:
```env
# ─── Microsoft Graph API ───
MS_TENANT_ID=<tu-tenant-id>
MS_CLIENT_ID=<tu-client-id>
MS_CLIENT_SECRET=<tu-client-secret>
GRAPH_SCOPES=https://graph.microsoft.com/.default
SHAREPOINT_SITE_ID=<tu-sharepoint-site-id>
GRAPH_ENABLED=false

# ─── SMTP / Correo ───
SMTP_ENABLED=false
SMTP_HOST=mail.corporacioncofar.com
SMTP_PORT=465
SMTP_USERNAME=gestiondocumental@corporacioncofar.com
SMTP_PASSWORD=<tu-smtp-password>
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=gestiondocumental@corporacioncofar.com
SMTP_FROM_NAME="SGD COFAR"
```

2. `📁 backend/app/core/config.py` — agregar campo `sharepoint_site_id`:
```python
# En la clase Settings, después de graph_scopes:
sharepoint_site_id: str = ""
```

### Validación
```bash
# Verificar que el backend arranca con las nuevas variables
docker restart sgd-backend
curl.exe http://localhost:18000/api/v1/health
# Debe responder 200 OK
```

### ✅ Criterio de cierre
- `.env` tiene las 12 líneas nuevas
- `config.py` tiene `sharepoint_site_id`
- Backend healthy después del restart

---

## Tarea 0.3 — Ocultar LIBERACION de la UI de semaforización

### Descripción
La fila `LIBERACION` con valores 999/999/999 se muestra en Parametrización General > Tiempos y SLAs. ETO no tiene plazo (es indefinido), y estos valores confunden al usuario. El backend debe filtrar `tipo_tarea != 'LIBERACION'` en el endpoint de listado.

### Archivos a modificar

1. `📁 backend/app/api/v1/semaforizacion_tarea.py` — en el endpoint `GET /`:
   Agregar filtro `where(SemaforizacionTarea.tipo_tarea != TipoTarea.LIBERACION)` o alternativamente `where(SemaforizacionTarea.tipo_tarea != 'LIBERACION')`.

### Validación
```bash
curl.exe http://localhost:18000/api/v1/semaforizacion-tarea
# Debe devolver 5 filas (REVISION, APROBACION, CONTROL_LECTURA, EVALUACION, CORRECCION)
# NO debe incluir LIBERACION
```

### 🧪 Escenario de prueba (Chrome MCP)

```
1. Login como admin_local
2. Navegar a /#/parametrizacion
3. Ir al tab "Tiempos y SLAs"
4. Verificar que NO aparece la fila "LIBERACION"
5. Verificar que las 5 filas restantes se muestran correctamente
```

### ✅ Criterio de cierre
- `GET /semaforizacion-tarea` retorna 5 filas, no 6
- UI de Parametrización no muestra LIBERACION

---

## Tarea 0.4 — Filtrar usuarios AUSENTES de dropdowns de revisores/aprobadores

### Descripción
En el wizard paso 3 y en Liberación ETO, las listas desplegables de revisores y aprobadores deben excluir usuarios con `ausente=true`. Un usuario de vacaciones no debe poder ser seleccionado.

### Archivos a modificar

1. `📁 backend/app/api/v1/usuarios.py` — endpoint `GET /usuarios/por-rol` y `GET /usuarios/por-cualquier-rol`:
   Agregar condición `where(Usuario.ausente == False)` en los queries de selección.

2. `📁 frontend/src/pages/AprobacionDocumento.js` — líneas donde se llenan `revisoresList` y `aprobadoresList` (alrededor de línea 90-120):
   Ya llama a `usuariosApi.listPorCualquierRol()`. El backend hará el filtro.

### Validación
```bash
# Verificar que un usuario ausente no aparece
curl.exe "http://localhost:18000/api/v1/usuarios/por-cualquier-rol?roles=ELABORADOR%20-%20REVISOR"
# No debe incluir usuarios con ausente=true
```

### 🧪 Escenario de prueba (Chrome MCP)

```
PRE-CONDICIÓN: Asegurar que hay al menos 1 usuario con ausente=true
1. Login como admin_local
2. Ir a Parametrización > tabla Usuarios
3. Marcar a un usuario como ausente
4. Login como eto_test
5. Ir a /#/aprobacion-documento
6. Paso 3 — Agregar Revisor
7. Verificar que el usuario ausente NO aparece en el dropdown
```

### ✅ Criterio de cierre
- El endpoint de listado por rol excluye `ausente=true`
- Frontend no muestra usuarios ausentes en ningún dropdown de selección

---

# FASE 1: ALMACENAMIENTO Y NOMENCLATURA DEFINITIVA

> **Objetivo:** Definir e implementar la estructura de directorios definitiva en el servidor, el formato de nombres de archivo, y migrar el storage actual al nuevo esquema.
>
> **Duración estimada:** 4-6h
> **Riesgo:** 🟡 Medio — cambios en storage service requieren validar uploads existentes.
> **Prerrequisitos:** Fase 0 completa.
> **Relaciones:** Fase 9 (SharePoint) depende de tener la nomenclatura definida.

---

## Tarea 1.1 — Implementar nueva estructura de directorios en storage service

### Descripción
Crear la estructura de carpetas en el servidor:
```
/app/storage/documentos/{gerencia_sigla}/{area_sigla}/{codigo}/V{version}/
```

Ejemplo completo:
```
/app/storage/documentos/CC/CC/CC-5-001/V00/
  └── CC-5-001 PROCEDIMIENTO DE CONTROL DE DOCUMENTOS DEL SIG V00.docx
/app/storage/documentos/CC/CC/CC-5-001/V00/
  └── CC-5-001-F01 PROGRAMA DE EVALUACIÓN DE HABILIDADES TÉCNICAS V01.xlsx
/app/storage/documentos/PRO/PRO/PRO-5-001/V00/
  └── PRO-5-001 PROCEDIMIENTO OPERATIVO DE PRODUCCIÓN V00.docx
```

### Archivos a modificar

1. `📁 backend/app/services/storage.py` — modificar `LocalStorage.save()`:
   - Recibir parámetros adicionales: `gerencia_sigla`, `area_sigla`, `codigo`, `version`, `tipo_adjunto`, `titulo`, `correlativo_formulario`
   - Construir path: `{ROOT}/{gerencia_sigla}/{area_sigla}/{codigo}/V{version}/`
   - Crear directorios con `os.makedirs(path, exist_ok=True)`
   - Generar filename según tipo:
     - PRINCIPAL: `{codigo} {titulo} V{version}{ext}`
     - FORMULARIO: `{codigo}-F{corr:02d} {titulo} V{version}{ext}`
   - Retornar el path completo

2. `📁 backend/app/api/v1/documentos.py` — endpoint `POST /documentos/{id}/archivos`:
   - Pasar los nuevos parámetros al storage service
   - Obtener `gerencia_sigla`, `area_sigla`, `codigo`, `version` del documento/flujo

### Lógica de creación de directorios

```python
import os
from pathlib import Path

def _ensure_dir(path: str) -> str:
    """Crea el directorio si no existe. Retorna el path."""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

def _build_storage_path(gerencia_sigla: str, area_sigla: str, codigo: str, version: str) -> str:
    """Construye: {ROOT}/{gerencia_sigla}/{area_sigla}/{codigo}/V{version}/"""
    return _ensure_dir(
        os.path.join(settings.documentos_storage_path, gerencia_sigla, area_sigla, codigo, f"V{version}")
    )
```

### Validación
```bash
# Subir un archivo via API
curl.exe -X POST http://localhost:18000/api/v1/documentos/1/archivos \
  -H "Cookie: session=...; user_id=1; csrf_token=..." \
  -F "archivo=@test.docx" -F "tipo_adjunto=PRINCIPAL"

# Verificar que el archivo se creó en la nueva estructura
docker exec sgd-backend ls -la /app/storage/documentos/CC/CC/CC-5-001/V00/
```

### ✅ Criterio de cierre
- Upload crea archivos en `{gerencia_sigla}/{area_sigla}/{codigo}/V{version}/`
- El filename sigue el formato: `CC-5-001 PROCEDIMIENTO DE MUESTREO V00.docx`
- Los directorios se crean automáticamente si no existen

---

## Tarea 1.2 — Contador de descargas de plantillas (métrica)

### Descripción
Agregar un reporte/kpi que muestre cuántas descargas de plantillas ha hecho cada usuario. No hay límite, solo es métrica. La info ya está en `audit_log` (cada descarga registra `accion='DOWNLOAD', recurso='plantilla_documental'`).

### Archivos a modificar

1. `📁 backend/app/api/v1/audit_log.py` — agregar endpoint `GET /audit-log/descargas-plantillas`:
   ```python
   @router.get("/descargas-plantillas", summary="Métrica de descargas de plantillas")
   async def descargas_plantillas(...):
       """Agrupa por usuario_id y cuenta las descargas de plantillas en un rango de fechas."""
   ```

2. `📁 frontend/src/pages/Plantillas.js` — agregar un mini KPI o badge:
   ```html
   <div class="kpi-card">
     <span class="kpi-value" x-text="descargasCount"></span>
     <span class="kpi-label">Descargas de plantillas (este mes)</span>
   </div>
   ```

### ✅ Criterio de cierre
- Endpoint devuelve conteo agrupado por usuario
- Frontend muestra el KPI en la página de Plantillas

---

# FASE 2: CONTROL DE DESCARGAS DE EDITABLES

> **Objetivo:** Implementar el límite de 1 descarga/día/usuario para documentos editables, con excepción para tipos Metodología (cod=1) y Especificación (cod=7) que pueden descargar hasta `max_descargas_editables_dia` (10).
>
> **Duración estimada:** 4-6h
> **Riesgo:** 🟡 Medio — requiere nueva tabla o columna de contador.
> **Prerrequisitos:** Fase 0 completa.

---

## Tarea 2.1 — Crear tabla de conteo diario de descargas

### Descripción
Crear una tabla `descargas_contador` (o usar `audit_log` con consultas agregadas). Opción recomendada: tabla dedicada para performance.

### Migración Alembic

```sql
CREATE TABLE descargas_contador (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    documento_id    INTEGER REFERENCES documentos(id) ON DELETE SET NULL,
    fecha           DATE NOT NULL DEFAULT CURRENT_DATE,
    -- tipo de descarga: 'EDITABLE' o 'FORMULARIO'
    tipo_descarga   VARCHAR(20) NOT NULL DEFAULT 'EDITABLE',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(usuario_id, documento_id, fecha, tipo_descarga)
);

CREATE INDEX ix_descargas_usuario_fecha ON descargas_contador(usuario_id, fecha);
```

### Alternativa (sin tabla nueva)
Si se prefiere no crear tabla, usar `audit_log`:
```sql
SELECT COUNT(*) FROM audit_log 
WHERE usuario_id = X 
  AND accion = 'DOWNLOAD' 
  AND recurso = 'documento_editable' 
  AND created_at::date = CURRENT_DATE;
```

### Archivos a modificar

1. `📁 backend/app/models/descarga_contador.py` — nuevo modelo
2. `📁 backend/app/models/__init__.py` — registrar modelo
3. Migración Alembic
4. `📁 backend/app/services/descarga_service.py` — nuevo servicio con:
   - `contar_descargas_hoy(usuario_id, db) -> int`
   - `puede_descargar(usuario_id, documento_id, db) -> tuple[bool, str]`
   - `registrar_descarga(usuario_id, documento_id, db)`
   - `limite_diario(documento) -> int`: retorna 1 si el tipo NO está excluido, `max_descargas_editables_dia` si está excluido

### Lógica de `limite_diario()`

```python
async def limite_diario(db, documento) -> int:
    """
    Retorna el límite de descargas diarias para un documento.
    - Si el tipo está en `tipos_excluidos_limite_descarga`: retorna `max_descargas_editables_dia`
    - Si no: retorna 1
    """
    # Leer configuración
    cfg = await db.execute(
        select(ConfiguracionGlobal)
        .where(ConfiguracionGlobal.clave.in_([
            "max_descargas_editables_dia",
            "tipos_excluidos_limite_descarga",
        ]))
    )
    configs = {c.clave: c.valor for c in cfg.scalars().all()}
    
    max_excepcion = int(configs.get("max_descargas_editables_dia", "10"))
    tipos_excluidos_str = configs.get("tipos_excluidos_limite_descarga", "[]")
    
    import json
    tipos_excluidos = json.loads(tipos_excluidos_str)  # ["METODOLOGIA", "ESPECIFICACION"]
    
    # Verificar si el tipo del documento está excluido
    tipo = documento.tipo_documento
    if tipo and tipo.slug in tipos_excluidos:
        return max_excepcion
    
    return 1
```

---

## Tarea 2.2 — Validar límite en endpoint de descarga / VersionEditable

### Descripción
Antes de permitir la descarga de un documento editable, validar que el usuario no haya excedido su límite diario.

### Archivos a modificar

1. `📁 backend/app/api/v1/documentos.py` — en el endpoint `GET /documentos/{id}/descargar` (o el que sirva el archivo):
   - Agregar validación: `puede_descargar(user.id, documento_id, db)`
   - Si no puede: retornar HTTP 429 Too Many Requests con mensaje:
     ```json
     {"detail": "Ha superado el límite diario de descargas permitidas para su perfil."}
     ```
   - Si puede: registrar la descarga y servir el archivo

2. `📁 frontend/src/pages/VersionEditable.js`:
   - Manejar error 429: mostrar toast rojo "Ha superado el límite diario de descargas permitidas para su perfil."
   - Mostrar contador de descargas restantes del día

### 🧪 Escenario de prueba (Chrome MCP)

```
PRECONDICIÓN: tipos_excluidos_limite_descarga = ["METODOLOGIA","ESPECIFICACION"]
PRECONDICIÓN: max_descargas_editables_dia = 10

ESCENARIO A: Documento normal (tipo Procedimiento, cod=5)
1. Login como eto_test
2. Ir a /#/version-editable
3. Buscar "CC-5-001" (Procedimiento)
4. Descargar → OK (1ra descarga del día)
5. Descargar otra vez → ❌ 429 "Ha superado el límite diario"

ESCENARIO B: Documento excepción (tipo Metodología, cod=1)
1. Descargar documento de tipo Metodología
2. Debe permitir hasta 10 descargas
3. La 11ra descarga → ❌ 429

ESCENARIO C: Documento OBSOLETO
1. Buscar "MCB-6-001" (MCB-6-001, OBSOLETO)
2. NO debe aparecer en resultados de búsqueda
```

### ✅ Criterio de cierre
- Descarga de documento normal: 1ra OK, 2da 429
- Descarga de excepción (Metodología): permite 10
- Descarga de OBSOLETO: bloqueada
- Contador se resetea al día siguiente
- Tests pytest del servicio (8-10 tests)

---

# FASE 3: CATÁLOGO DE PROCESOS

> **Objetivo:** Agregar códigos numéricos a la tabla `procesos`, exponer un selector searchable en la pantalla de Liberación ETO, y mostrar el proceso en Lista Maestra y Consultar Documentos.
>
> **Duración estimada:** 3-4h
> **Riesgo:** 🟢 Bajo — tabla ya existe, solo se agregan campos y UI.
> **Prerrequisitos:** Fase 0 completa.

---

## Tarea 3.1 — Agregar columna `codigo` a tabla `procesos`

### Migración SQL
```sql
ALTER TABLE procesos ADD COLUMN codigo VARCHAR(4) UNIQUE;
-- Asignar códigos a los 10 procesos existentes
UPDATE procesos SET codigo = '0001' WHERE nombre = 'Analisis';
UPDATE procesos SET codigo = '0002' WHERE nombre = 'Capacitacion';
UPDATE procesos SET codigo = '0003' WHERE nombre = 'Compras';
UPDATE procesos SET codigo = '0004' WHERE nombre = 'Fabricacion';
UPDATE procesos SET codigo = '0005' WHERE nombre = 'Investigacion';
UPDATE procesos SET codigo = '0006' WHERE nombre = 'Logistica';
UPDATE procesos SET codigo = '0007' WHERE nombre = 'Mantenimiento';
UPDATE procesos SET codigo = '0008' WHERE nombre = 'Produccion';
UPDATE procesos SET codigo = '0009' WHERE nombre = 'Seguridad';
UPDATE procesos SET codigo = '0010' WHERE nombre = 'Ventas';
ALTER TABLE procesos ALTER COLUMN codigo SET NOT NULL;
```

### Archivos a modificar

1. `📁 backend/app/models/proceso.py` — agregar campo:
   ```python
   codigo: Mapped[str] = mapped_column(String(4), unique=True, nullable=False)
   ```

2. `📁 backend/app/schemas/proceso.py` — agregar `codigo` a los schemas

3. `📁 backend/app/api/v1/procesos.py` — CRUD básico (GET list, GET by id)

---

## Tarea 3.2 — Selector de Proceso en LiberacionDetalle.js

### Descripción
Agregar un dropdown searchable ANTES de la sección "Decisión de Liberación" (línea 372) en `LiberacionDetalle.js`, para que ETO seleccione el proceso al cual corresponde el documento.

### Archivos a modificar

1. `📁 frontend/src/pages/LiberacionDetalle.js` — entre la línea 370 y 372, agregar:
```html
<!-- Selector de Proceso (ETO) -->
<div class="bg-white border border-slate-200 rounded-xl px-5 py-4 shadow-card mb-3.5">
  <div class="text-[11.5px] font-bold text-slate-600 uppercase tracking-wider mb-3.5 pb-2.5 border-b border-slate-100">
    Asignación de Proceso
  </div>
  <div class="relative">
    <label class="form-label">Proceso al que corresponde el documento *</label>
    <input type="text" class="form-input text-xs" x-model="procesoInput"
           placeholder="Buscar proceso por código o nombre..."
           @focus="procesoOpen=true" @input="procesoOpen=true" @click.stop>
    <div x-show="procesoOpen && procesosFiltrados.length > 0"
         class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl max-h-[200px] overflow-y-auto"
         style="display:none"
         :style="(procesoOpen && procesosFiltrados.length > 0) ? 'display:block' : 'display:none'" @click.stop>
      <template x-for="p in procesosFiltrados" :key="p.id">
        <button @click="seleccionarProceso(p)" type="button"
                class="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-slate-100 last:border-b-0 transition-colors text-[11px]">
          <span class="font-mono font-semibold" x-text="p.codigo"></span>
          <span class="text-slate-500 ml-2" x-text="p.nombre"></span>
        </button>
      </template>
    </div>
  </div>
  <div x-show="procesoSeleccionado" class="mt-2">
    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-brand-50 text-brand-700 border border-brand-200">
      <span class="font-mono font-semibold" x-text="procesoSeleccionado.codigo"></span>
      <span x-text="procesoSeleccionado.nombre"></span>
      <span @click="procesoSeleccionado=null;procesoInput=''" class="cursor-pointer opacity-60 hover:opacity-100 ml-1">✕</span>
    </span>
  </div>
</div>
```

2. `📁 frontend/src/pages/LiberacionDetalle.js` — agregar en el objeto Alpine:
```javascript
// ─── Procesos ───
procesosList: [],
procesoInput: '',
procesoOpen: false,
procesoSeleccionado: null,

async init() {
  // ... init existente ...
  // Cargar procesos
  const res = await apiGet('/procesos')
  if (res.ok) this.procesosList = res.data?.items || []
},

get procesosFiltrados() {
  const q = (this.procesoInput || '').toLowerCase().trim()
  if (!q) return this.procesosList
  return this.procesosList.filter(p => 
    (p.codigo || '').toLowerCase().includes(q) ||
    (p.nombre || '').toLowerCase().includes(q)
  )
},

seleccionarProceso(p) {
  this.procesoSeleccionado = p
  this.procesoInput = `${p.codigo} — ${p.nombre}`
  this.procesoOpen = false
  // Aquí luego se persistirá: POST /documentos/{id}/asignar-proceso
},
```

3. `📁 frontend/src/services/documentosApi.js` — agregar:
```javascript
async listarProcesos() { return apiGet('/procesos') }
```

### ✅ Criterio de cierre
- Selector visible en LiberacionDetalle.js antes de "Decisión de Liberación"
- Busca por código (0001) y por nombre (Analisis)
- Al seleccionar, muestra chip con código + nombre
- El proceso se persiste en `documentos.proceso_id` (cuando se integre con el backend real)

---

# FASE 4: TIMELINE / BITÁCORA DEL FLUJO DOCUMENTAL

> **Objetivo:** Poblar la tabla `bitacora_timeline` (ya existe) con cada evento del flujo documental: creación, liberación ETO, asignación a revisor, aprobación, rechazo, corrección, reasignación, publicación, obsolescencia.
>
> **Duración estimada:** 6-8h
> **Riesgo:** 🟠 Medio-Alto — es la columna vertebral de la trazabilidad.
> **Prerrequisitos:** Fase 0, Fase 1 completas.

---

## Tarea 4.1 — Crear `timeline_service.py`

### Descripción
Servicio centralizado que escribe en la tabla `bitacora_timeline`. Un único punto de entrada para toda la bitácora del flujo documental.

### Archivo nuevo

`📁 backend/app/services/timeline_service.py`:

```python
"""
Servicio: timeline_service
Registra cada evento del flujo documental en bitacora_timeline (append-only).

La bitácora es INMUTABLE: nunca se UPDATE ni DELETE. Solo INSERT.
Cada evento tiene un color_nodo según la acción (US-8.01):
  - Azul:   CREADO, CORREGIDO
  - Verde:  LIBERADO_ETO, APROBADO, PUBLICADO
  - Rojo:   RECHAZADO, ELIMINADO, OBSOLETO, VENCIDO
  - Ámbar:  PENDIENTE (tarea asignada)
  - Gris:   REASIGNADO
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bitacora_timeline import BitacoraTimeline
from app.models.usuario import Usuario

# Mapeo de acciones a colores (US-8.01)
COLOR_MAP = {
    "CREADO": "azul",
    "CORREGIDO": "azul",
    "LIBERADO_ETO": "verde",
    "APROBADO": "verde",
    "RECHAZADO": "rojo",
    "ELIMINADO": "rojo",
    "OBSOLETO": "rojo",
    "VENCIDO": "rojo",
    "PENDIENTE": "ambar",
    "EN_REVISION": "ambar",
    "EN_CORRECCION": "ambar",
    "REASIGNADO": "gris",
    "PUBLICADO": "verde",
    "ENVIADO": "azul",
}


async def escribir_bitacora(
    db: AsyncSession,
    *,
    documento_flujo_id: int,
    tarea_id: Optional[int] = None,
    usuario: Usuario,
    accion: str,
    estado_origen: Optional[str] = None,
    estado_destino: Optional[str] = None,
    observacion: Optional[str] = None,
    adjunto_url: Optional[str] = None,
) -> BitacoraTimeline:
    """
    Escribe un nodo en la bitácora del documento.
    
    Args:
        db: sesión de BD
        documento_flujo_id: ID del flujo documental
        tarea_id: ID de la tarea (opcional, para eventos de tarea específica)
        usuario: usuario que ejecuta la acción (o None para 'SISTEMA')
        accion: código de la acción (CREADO, LIBERADO_ETO, APROBADO, etc.)
        estado_origen: estado anterior (opcional)
        estado_destino: estado nuevo (opcional)
        observacion: texto libre (obligatorio en RECHAZADO)
        adjunto_url: URL a evidencia (opcional)
    
    Returns:
        BitacoraTimeline creada
    """
    color = COLOR_MAP.get(accion, "azul")
    
    entry = BitacoraTimeline(
        documento_flujo_id=documento_flujo_id,
        tarea_id=tarea_id,
        usuario_id=usuario.id if usuario else None,
        accion=accion,
        estado_origen=estado_origen,
        estado_destino=estado_destino,
        color_nodo=color,
        observacion=observacion,
        adjunto_url=adjunto_url,
    )
    db.add(entry)
    await db.flush()
    return entry
```

---

## Tarea 4.2 — Integrar timeline en cada etapa del flujo

### Puntos de integración

| Evento | Dónde | Acción | Color |
|--------|-------|--------|-------|
| Wizard firmado | `envio_service.enviar_a_liberacion()` | CREACIÓN | azul |
| ETO libera | `documentos.py POST /liberar` | LIBERADO_ETO | verde |
| Tarea asignada | `tarea_service.crear_tarea()` | PENDIENTE | ámbar |
| Revisor aprueba | `tarea_service.completar_tarea()` | APROBADO | verde |
| Revisor rechaza | `tarea_service.rechazar_tarea()` | RECHAZADO | rojo |
| Corrección enviada | `tarea_service.correccion_enviada()` | CORREGIDO | azul |
| Reasignación | `tarea_service.reasignar_tarea()` | REASIGNADO | gris |
| Documento aprobado | `envio_service.publicar_documento()` | PUBLICADO | verde |
| Obsolescencia | servicio dedicado | OBSOLETO | rojo |
| Vencimiento | cron job | VENCIDO | rojo |

### Integración en `envio_service.py`

```python
# Al final de enviar_a_liberacion(), después del commit:
from app.services.timeline_service import escribir_bitacora

await escribir_bitacora(
    db=db,
    documento_flujo_id=flujo.id,
    usuario=user,
    accion="CREADO",
    estado_origen="EN_ELABORACION",
    estado_destino="LIBERACION_ETO",
)
```

---

## Tarea 4.3 — Endpoint GET /bitacora para el frontend

### Archivo nuevo

`📁 backend/app/api/v1/bitacora.py`:

```python
@router.get("/bitacora", summary="Timeline del documento")
async def get_bitacora(
    request: Request,
    documento_flujo_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna todos los nodos de la bitácora para un flujo documental,
    ordenados por created_at ASC.
    """
    await require_authenticated(request, db)
    
    result = await db.execute(
        select(BitacoraTimeline)
        .where(BitacoraTimeline.documento_flujo_id == documento_flujo_id)
        .order_by(BitacoraTimeline.created_at.asc())
    )
    return {"items": result.scalars().all()}
```

Registrar en `main.py`.

---

## Tarea 4.4 — Refactor visual de timeline en Revision.js

### Descripción
La página `Revision.js` ya tiene la estructura visual del timeline (el div que mencionaste: `Historial del documento en este ciclo`). Hay que reemplazar el mock actual por datos reales del endpoint `/bitacora`.

### 🧪 Escenario de prueba (Chrome MCP)

```
1. Login como eto_test
2. Ir a /#/aprobacion-documento
3. Crear un documento y firmar (completar wizard)
4. Verificar en BD que se creó nodo en bitacora_timeline

docker exec sgd-postgres psql -U sgd -d sgd -c \
  "SELECT accion, color_nodo, created_at FROM bitacora_timeline WHERE documento_flujo_id=1;"

5. Navegar a /#/revision
6. Verificar que el timeline muestra "CREADO" en azul
```

### ✅ Criterio de cierre
- Cada evento del flujo genera un nodo en `bitacora_timeline`
- El timeline se muestra correctamente en la UI
- Los colores corresponden al tipo de acción (US-8.01)
- Tests del servicio: 8-10 tests

---

# FASE 5: SERVICIOS CORE DEL WORKFLOW (R3 FASE 2)

> **Objetivo:** Implementar `tarea_service.py`, `notificacion_service.py`, y los endpoints POST de aprobar/rechazar/reasignar tareas. Esta es la fase más crítica de R3.
>
> **Duración estimada:** 8-10h
> **Riesgo:** 🔴 Alto — cambios en el flujo principal del documento.
> **Prerrequisitos:** Fase 4 completa (timeline debe estar listo).

---

## Tarea 5.1 — Crear `tarea_service.py`

### Archivo nuevo

`📁 backend/app/services/tarea_service.py` con las funciones:

```python
async def crear_tarea(
    db, *, documento_flujo_id, usuario_id, tipo_tarea,
    delegado_origen_id=None, fecha_asignacion=None
) -> Tarea:
    """Crea una tarea y registra en timeline: PENDIENTE (ámbar)."""
    
async def completar_tarea(
    db, request, user, tarea_id, firma_password
) -> tuple[Tarea, str]:
    """
    Completa una tarea como APROBADO.
    - Valida firma 2FA
    - Cambia estado a COMPLETADO
    - Registra timeline: APROBADO (verde)
    - Verifica si todas las tareas del mismo tipo están completas
    - Si todas completas y sin rechazos: avanza a siguiente etapa
    - Si hay rechazos: transiciona a EN_CORRECCION
    Returns: (tarea, accion_siguiente)
    """
    
async def rechazar_tarea(
    db, request, user, tarea_id, observacion, firma_password
) -> tuple[Tarea, str]:
    """
    Rechaza una tarea con observación.
    - Valida observacion >= 10 caracteres
    - Valida firma 2FA
    - Cambia estado a RECHAZADO
    - Crea TareaObservacion
    - Registra timeline: RECHAZADO (rojo)
    Returns: (tarea, accion_siguiente)
    """
    
async def reasignar_tarea(
    db, request, user, tarea_id, nuevo_usuario_id, motivo
) -> Tarea:
    """
    Reasigna una tarea a otro usuario.
    - Marca tarea original como REASIGNADA
    - Crea nueva tarea para nuevo usuario
    - Registra timeline: REASIGNADO (gris)
    """
```

### Lógica de propagación (la más crítica)

```python
async def _verificar_y_avanzar(db, documento_flujo_id, tipo_tarea):
    """
    Verifica si todas las tareas de un tipo están completadas.
    Si es así, determina el siguiente paso.
    """
    # Contar tareas PENDIENTE + RECHAZADO del mismo tipo
    tareas = await db.execute(
        select(Tarea)
        .where(Tarea.documento_flujo_id == documento_flujo_id)
        .where(Tarea.tipo_tarea == tipo_tarea)
        .where(Tarea.activo == True)
    )
    todas = tareas.scalars().all()
    
    pendientes = [t for t in todas if t.estado in ("PENDIENTE",)]
    rechazados = [t for t in todas if t.estado == "RECHAZADO"]
    completados = [t for t in todas if t.estado == "COMPLETADO"]
    
    # Si aún hay pendientes, no avanzar
    if pendientes:
        return None
    
    # Si hay rechazos: ir a CORRECCION
    if rechazados:
        return await _transicionar_a_correccion(db, documento_flujo_id, rechazados)
    
    # Todos completados sin rechazos: avanzar
    if tipo_tarea == TipoTarea.REVISION:
        return await _iniciar_aprobacion(db, documento_flujo_id)
    elif tipo_tarea == TipoTarea.APROBACION:
        return await _publicar_documento(db, documento_flujo_id)
    elif tipo_tarea == TipoTarea.CORRECCION:
        # Bypass directo: volver al revisor que observó
        return await _reenviar_a_observador(db, documento_flujo_id)
    
    return None
```

---

## Tarea 5.2 — Endpoints REST de tareas

### Archivo nuevo

`📁 backend/app/api/v1/tareas.py`:

```python
@router.get("/tareas", summary="Lista tareas del usuario")
@router.get("/tareas/{id}", summary="Detalle de tarea")
@router.post("/tareas/{id}/aprobar", summary="Aprobar tarea (firma 2FA)")
@router.post("/tareas/{id}/rechazar", summary="Rechazar tarea con observación")
@router.post("/tareas/{id}/reasignar", summary="Reasignar tarea (solo ETO)")
```

Registrar en `main.py`.

---

## Tarea 5.3 — Endpoints de notificaciones

### Archivo nuevo

`📁 backend/app/api/v1/notificaciones.py`:

```python
@router.get("/notificaciones", summary="Lista notificaciones del usuario")
@router.get("/notificaciones/no-leidas/count", summary="Conteo de no leídas")
@router.post("/notificaciones/{id}/leer", summary="Marcar como leída")
```

Registrar en `main.py`.

---

## Tarea 5.4 — Refactor `envio_service.py` para integrar tareas

### Descripción
Al liberar documento (ETO hace clic en "Liberar"), el servicio debe:
1. Crear N tareas de tipo REVISION (una por revisor)
2. Crear notificaciones para cada revisor
3. Registrar timeline: LIBERADO_ETO (verde)
4. Registrar timeline por cada tarea: PENDIENTE (ámbar)
5. Transicionar estatus del documento a EN_REVISION

### 🧪 Escenario de prueba

```
1. Login como eto_test
2. Ir a /#/bandeja (sección liberación pendiente)
3. Atender una tarea de liberación
4. Hacer clic en "Liberar Documento"
5. Verificar:
   - Se crearon N tareas en tabla `tareas` (1 por revisor)
   - Se crearon N notificaciones en `notificaciones`
   - Timeline tiene: LIBERADO_ETO (verde) + N x PENDIENTE (ámbar)
   - Documento pasó a EN_REVISION
```

### ✅ Criterio de cierre
- 8-10 tests de servicios
- Todos los endpoints responden 200/401/403/404/409 según corresponda
- La propagación funciona: último revisor OK → pasa a aprobación
- Bypass directo: corrección va solo al revisor que observó

---

# FASE 6: INTEGRACIÓN FLUJO ETO → REVISORES → APROBADORES

> **Objetivo:** Refactorizar las pantallas frontend que consumen mock data para que consuman datos reales del backend. Incluye LiberacionDetalle.js, Bandeja.js, Revision.js, AprobacionFinal.js, Correccion.js.
>
> **Duración estimada:** 12-16h
> **Riesgo:** 🔴 Alto — toca 5 páginas frontend con lógica compleja.
> **Prerrequisitos:** Fase 5 completa.

*Nota: El detalle de cada página se desarrollará en documentos específicos por fase. Aquí se listan los hitos.*

| Tarea | Archivo | Descripción |
|-------|---------|-------------|
| 6.1 | `LiberacionDetalle.js` | Reemplazar mocks por API real. ETO ve datos reales del flujo + documentos via SharePoint + selector de proceso + decisión de liberación |
| 6.2 | `Bandeja.js` | Reemplazar `data/tasks.js` por `GET /tareas?usuario_id=X&estado=PENDIENTE` |
| 6.3 | `Revision.js` | Revisor ve documento + timeline + botones aprobar/rechazar |
| 6.4 | `AprobacionFinal.js` | Aprobador ve documento + timeline + botones aprobar/rechazar |
| 6.5 | `Correccion.js` | Solicitante ve observación + corrige + reenvía (bypass directo) |
| 6.6 | `notificaciones.js` (store) | Reemplazar polling mock por `GET /notificaciones/no-leidas/count` |

---

# FASE 7: DELEGACIÓN Y TIMEOUT

> **Objetivo:** Implementar el cron job de reasignación automática por SLA vencido, delegación por desvinculación y por vacaciones.
>
> **Duración estimada:** 4-6h
> **Riesgo:** 🟠 Medio — cron job puede afectar performance si no está bien indexado.

---

## Tarea 7.1 — Cron `reasignar_tareas_vencidas`

```python
# backend/app/workers/tasks.py

@celery_app.task(name="reasignar_tareas_vencidas")
async def reasignar_tareas_vencidas():
    """
    Cron diario a las 23:59.
    1. Busca tareas PENDIENTE con fecha_vencimiento < NOW()
    2. Excluye tipo LIBERACION (ETO no tiene plazo)
    3. Por cada tarea vencida:
       a. Buscar delegado del usuario
       b. Si no tiene delegado: reasignar a ETO (según matriz_enrutamiento_eto)
       c. Max 3 intentos de reasignación
       d. Marcar original como VENCIDO + timeline gris
       e. Crear nueva tarea para delegado/ETO
    """
```

## Tarea 7.2 — Delegación por desvinculación

En el servicio `sync_ad_service.py`, después de marcar usuarios como desvinculados, ejecutar `transferir_tareas_pendientes(usuario_id)`.

## Tarea 7.3 — Delegación por vacaciones

En `ausencias.py` (CRUD), al crear una ausencia vigente, ejecutar `transferir_tareas_pendientes(usuario_id)`.

---

# FASE 8: SISTEMA DE NOTIFICACIONES POR CORREO

> **Objetivo:** Activar SMTP y enviar correos en cada etapa del flujo.
>
> **Duración estimada:** 4-6h
> **Riesgo:** 🟡 Medio

---

## Tarea 8.1 — Configurar SMTP en `.env`

Cambiar `SMTP_ENABLED=false` → `true`. Verificar conectividad.

## Tarea 8.2 — Crear `email_service.py`

Servicio que usa `smtplib` + `email.mime` para enviar correos HTML con las plantillas de `email_templates`.

## Tarea 8.3 — Integrar en cada etapa

| Evento | Para quién | Plantilla |
|--------|-----------|-----------|
| Tarea asignada | Al usuario | ASIG_REVISION, ASIG_APROBACION |
| Tarea reasignada | Al nuevo responsable | REASIGNACION |
| Documento liberado | ETO | (notificación interna) |
| Corrección solicitada | Al solicitante | CORRECCION |
| Documento publicado | Grupo difusión | PUBLICACION |
| Control de lectura | Grupo difusión | CONTROL_LECTURA |
| Evaluación asignada | Usuarios designados | EVALUACION |

---

# FASE 9: INTEGRACIÓN MICROSOFT GRAPH / SHAREPOINT

> **Objetivo:** Subir documentos a SharePoint al crearse, obtener enlaces directos, y permitir edición online.
>
> **Duración estimada:** 6-8h
> **Riesgo:** 🟠 Medio — depende de API externa.

---

## Tarea 9.1 — Implementar `SharePointStorage` real

Remplazar el stub actual por implementación real usando `httpx` + Graph API:

```python
# backend/app/services/storage.py

class SharePointStorage(StorageBackend):
    """Real: Microsoft Graph API."""
    
    async def _get_access_token(self) -> str:
        """Obtiene token usando client credentials flow."""
    
    async def save(self, file_bytes: bytes, filename: str, 
                   gerencia_sigla: str, area_sigla: str, 
                   codigo: str, version: str) -> str:
        """Sube a SharePoint en la estructura de directorios correspondiente.
        Retorna el driveItem ID o URL."""
    
    async def get_share_link(self, drive_item_id: str) -> str:
        """Obtiene enlace de edición del documento en SharePoint."""
```

## Tarea 9.2 — Guardar enlace de SharePoint en BD

Agregar columna `sharepoint_drive_id` y `sharepoint_link` en `archivos_adjuntos`.

---

# FASE 10: PDF FINAL, CARÁTULA Y CARIMBO

> **Objetivo:** Al aprobarse un documento, generar el PDF oficial con carátula (logo, código, versión, tabla de firmas) y carimbo en cada página.
>
> **Duración estimada:** 6-8h
> **Riesgo:** 🟠 Medio — librería de manipulación de PDF.

---

## Tarea 10.1 — Evaluar librería

Opciones:
- **python-docx** + **docx2pdf** (requiere Word instalado → no en Linux)
- **python-docx-template** + **WeasyPrint** (HTML → PDF, más control)
- **ReportLab** (PDF nativo, más complejo)
- **LibreOffice** headless (convertir .docx → .pdf)

**Recomendación:** WeasyPrint + python-docx-template. Se genera HTML con logo + tabla de firmas + carimbo, se convierte a PDF.

## Tarea 10.2 — Implementar `pdf_service.py`

```python
async def generar_pdf_aprobado(documento_id, db) -> str:
    """
    1. Obtener datos del documento + firmantes del timeline
    2. Generar carátula (HTML): logo COFAR, título, código, versión, tabla de firmas
    3. Convertir .docx original a PDF (via LibreOffice o WeasyPrint)
    4. Insertar carátula como página 0
    5. Insertar carimbo en header de cada página
    6. Guardar en /app/storage/pdf-aprobados/{codigo}_V{version}.pdf
    7. Registrar en BD (nuevo campo documentos.pdf_path)
    """
```

---

# FASE 11: LIMPIEZA DE DATOS MOCK Y MIGRACIONES

> **Objetivo:** Eliminar dependencia de datos mock en frontend y preparar migraciones para códigos antiguos.
>
> **Duración estimada:** 4-6h
> **Riesgo:** 🟡 Medio

---

## Tarea 11.1 — Reuso de correlativos (tabla independiente)

Crear migración y servicio `correlativo_disponible_service.py`:

```sql
CREATE TABLE correlativos_disponibles (
    id                  SERIAL PRIMARY KEY,
    area_id             INTEGER NOT NULL REFERENCES areas(id) ON DELETE CASCADE,
    tipo_documento_id   INTEGER NOT NULL REFERENCES tipos_documento(id) ON DELETE CASCADE,
    correlativo         INTEGER NOT NULL,
    liberado_en_flujo_id INTEGER REFERENCES documento_flujo(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(area_id, tipo_documento_id, correlativo)
);
```

**Algoritmo de `siguiente_correlativo_con_reuso()`:**
```
1. Buscar en correlativos_disponibles WHERE area_id=X AND tipo_documento_id=Y
   ORDER BY correlativo ASC LIMIT 1
2. Si existe: retornar ese correlativo y eliminarlo de la tabla
3. Si no existe: MAX(correlativo) + 1 (algoritmo actual)
```

**Al cancelar un flujo:**
```
1. Obtener el correlativo del documento cancelado
2. INSERT en correlativos_disponibles(area_id, tipo_documento_id, correlativo, liberado_en_flujo_id)
```

---

## Tarea 11.2 — Limpiar archivos mock de `frontend/src/data/`

| Archivo | Estado | Reemplazado por |
|---------|--------|-----------------|
| `data/gerencias.js` | En uso por LiberacionDetalle.js, otras | API real |
| `data/documents.js` | En uso por ListaMaestra.js | API real |
| `data/tasks.js` | En uso por Bandeja.js | API real |
| `data/bitacora.js` | En uso por ConsultaDocumentos.js | API real |
| `data/parametrosSistema.js` | No usado | Eliminar |
| `data/evaluaciones.js` | En uso | API real |
| `data/copias.js` | En uso | API real |
| `data/plantillas.js` | No usado (reemplazado sesión 24) | Eliminar |

---

# FASE 12: MÓDULO DE REASIGNACIÓN ETO

> **Objetivo:** Interfaz para que ETO reasigne tareas manualmente desde el timeline de Consultar Documentos (US-8.02).
>
> **Duración estimada:** 4-6h
> **Riesgo:** 🟡 Medio

---

## Tarea 12.1 — Backend: endpoint de reasignación ETO

```python
@router.post("/tareas/{id}/reasignar-eto")
async def reasignar_por_eto(
    tarea_id: int,
    body: ReasignarRequest,  # nuevo_usuario_id, motivo, password (2FA)
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Solo ETO/ADMIN. Reasigna una tarea a otro usuario."""
```

## Tarea 12.2 — Frontend: botón de reasignar en timeline (Consultar Documentos)

En `ConsultaDocumentos.js`, en el timeline de cada tarea, si el usuario es ETO, mostrar botón "Reasignar" en nodos con estado "PENDIENTE".

---

# MAPA DE DEPENDENCIAS ENTRE FASES

```
Fase 0: Hotfixes ──────────────────────────────────────────────────────────┐
                         │                                                   │
                    ┌────┴────┐                                              │
                    ▼         ▼                                              │
              Fase 1:      Fase 2:                                           │
              Storage      Control Descargas                                │
                    │         │                                              │
                    ▼         ▼                                              │
              Fase 3: Procesos                                               │
                    │                                                        │
                    ▼                                                        │
              Fase 4: Timeline ─────────────────────┐                       │
                    │                                │                       │
                    ▼                                ▼                       │
              Fase 5: Servicios Core R3           Fase 9: SharePoint         │
                    │                                │                       │
                    ▼                                ▼                       │
              Fase 6: Flujo Completo                                         │
               (Bandeja, Rev, Aprob, Corr, Liberac)                         │
                    │                                                        │
              ┌────┴────┐                                                   │
              ▼         ▼                                                   │
         Fase 7:     Fase 8:                                                │
         Delegación  Notificaciones                                         │
         y Timeout  por Correo                                              │
              │         │                                                   │
              ▼         ▼                                                   │
         Fase 10: PDF + Carátula                                            │
              │                                                            │
              ▼                                                            │
         Fase 11: Migraciones + Cleanup                                     │
              │                                                            │
              ▼                                                            │
         Fase 12: Reasignación ETO                                          │
              │                                                            │
              ▼                                                            │
         FIN 🎯 Flujo documental completo                                   │
              │                                                            │
              └────────────────────────────────────────────────────────────┘
```

---

# FASE TRANSVERSAL A: SEGURIDAD Y HARDENING

> **Naturaleza:** Transversal — aplica a TODAS las fases. No es una fase separada sino un conjunto de reglas que deben implementarse dentro de cada fase.
>
> **Riesgo:** 🟠 Medio — omitir estos puntos introduce vulnerabilidades.
> **Prerrequisitos:** Ninguno, aplica durante toda la ejecución.

---

## Tarea A.1 — Prevención de Path Traversal en storage

### Descripción
Cuando se construyen rutas de archivo concatenando datos del usuario (código, título, siglas), un atacante podría intentar un path traversal (`../../../etc/passwd`).

### Regla obligatoria en cada escritura de archivo

```python
import os
from pathlib import Path

def safe_filename(nombre: str) -> str:
    """
    Sanitiza un nombre de archivo: elimina caracteres peligrosos,
    previene path traversal.
    
    - Elimina: / \ .. : * ? " < > |
    - Reemplaza espacios por underscores
    - Limita largo a 200 caracteres
    """
    import re
    # Eliminar caracteres peligrosos
    safe = re.sub(r'[/\\:*?"<>|]', '', nombre)
    # Prevenir .. (path traversal)
    safe = safe.replace('..', '')
    # Recortar a 200 chars
    safe = safe[:200]
    return safe.strip()

def build_storage_path(base: str, *components: str) -> str:
    """
    Construye path de almacenamiento de forma segura.
    Cada componente es sanitizado individualmente.
    """
    safe_components = [safe_filename(c) for c in components]
    full_path = os.path.join(base, *safe_components)
    # Verificar que el path resultante está dentro del base (prevenir traversal)
    resolved = os.path.realpath(full_path)
    base_real = os.path.realpath(base)
    if not resolved.startswith(base_real):
        raise ValueError("Path traversal detectado")
    return full_path
```

### Aplica a
- `📁 backend/app/services/storage.py` — Tarea 1.1
- `📁 backend/app/services/caratula_service.py` — lectura de archivos
- Cualquier endpoint que reciba filenames del usuario

---

## Tarea A.2 — Validación real de MIME type (no confiar en el header)

### Descripción
El `content-type` del header HTTP puede ser falseado. Usar `python-magic` (libmagic) para detectar el tipo real del archivo por su contenido binario.

### Implementación

```python
# backend/app/services/file_validator.py

import magic
from typing import Set

# Whitelist de MIME types reales (detectados por contenido)
ALLOWED_MIME_REAL: Set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/msword",
    "image/png",
    "image/jpeg",
}

def detectar_mime_real(file_bytes: bytes) -> str:
    """
    Detecta el MIME type real usando libmagic.
    Retorna el MIME type o 'application/octet-stream' si falla.
    """
    try:
        mime = magic.from_buffer(file_bytes, mime=True)
        return mime.decode() if isinstance(mime, bytes) else mime
    except Exception:
        return "application/octet-stream"

def validar_archivo(file_bytes: bytes, content_type_header: str) -> tuple[bool, str, str]:
    """
    Valida un archivo: detecta MIME real y compara con el header.
    Returns: (es_valido, mime_real, mensaje_error)
    """
    mime_real = detectar_mime_real(file_bytes)
    
    if mime_real not in ALLOWED_MIME_REAL:
        return False, mime_real, f"Tipo de archivo no permitido: {mime_real}"
    
    # Log warning si no coincide con el header (posible intento de engaño)
    if mime_real != content_type_header:
        import logging
        logging.warning(f"MIME mismatch: header={content_type_header}, real={mime_real}")
    
    return True, mime_real, ""
```

### Instalación
```bash
# En requirements/base.txt agregar:
python-magic==0.4.27

# En Dockerfile del backend (instalar libmagic):
RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 && rm -rf /var/lib/apt/lists/*
```

### Aplica a
- `📁 backend/app/api/v1/documentos.py` — endpoint `POST /documentos/{id}/archivos`

---

## Tarea A.3 — Rate limiting real

### Descripción
El archivo `config.py` ya tiene `rate_limit_download: int = 30` pero no está implementado. Usar `slowapi` para rate limiting en endpoints de descarga.

### Implementación

```python
# backend/app/middleware/rate_limit.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    # Los límites se definen por endpoint vía decorador
    response = await call_next(request)
    return response
```

### Endpoints a rate-limitear

| Endpoint | Límite | Período |
|----------|--------|---------|
| `GET /documentos/{id}/descargar` | `rate_limit_download` (30) | 1 minuto |
| `POST /login` | `rate_limit_login` (10) | 1 minuto |
| `POST /verify-password` | 5 | 1 minuto |

---

## Tarea A.4 — Log de seguridad (auditoría de accesos sospechosos)

### Descripción
Agregar logging adicional cuando se detecten:
- Múltiples intentos de login fallidos (>5 en 1 minuto)
- Path traversal attempts
- MIME mismatches
- CSRF token inválidos

### Implementación
```python
# backend/app/core/security_logger.py

import logging

security_logger = logging.getLogger("cofar.security")

def log_security_event(event: str, detail: str, request):
    security_logger.warning(
        f"[SECURITY] {event} | {detail} | IP={request.client.host} | UA={request.headers.get('user-agent')}"
    )
```

### ✅ Criterio de cierre
- No se puede hacer path traversal via filenames (test automatizado)
- Subir un .exe con content-type "application/pdf" es rechazado
- Rate limiting funciona: 31ra descarga en 1 minuto → 429
- Logs de seguridad se escriben en `cofar.security` logger

---

# FASE TRANSVERSAL B: PERFORMANCE Y ESCALABILIDAD

> **Naturaleza:** Transversal — medidas de performance que deben aplicarse al implementar cada fase.
>
> **Riesgo:** 🟢 Bajo — no añade funcionalidad, pero previene problemas de performance a futuro.

---

## Tarea B.1 — Índices de performance para tablas R3

### Descripción
Las tablas nuevas (tareas, bitacora_timeline, notificaciones) necesitan índices adicionales para las queries más comunes del flujo documental.

### Migración SQL

```sql
-- tareas: búsqueda por usuario + estado (bandeja)
CREATE INDEX IF NOT EXISTS ix_tareas_usuario_estado 
ON tareas(usuario_id, estado) WHERE activo = TRUE;

-- tareas: búsqueda por flujo + tipo (propagación)
CREATE INDEX IF NOT EXISTS ix_tareas_flujo_tipo 
ON tareas(documento_flujo_id, tipo_tarea);

-- tareas: búsqueda de vencidas (cron)
CREATE INDEX IF NOT EXISTS ix_tareas_vencimiento 
ON tareas(fecha_vencimiento) WHERE estado = 'PENDIENTE' AND activo = TRUE;

-- bitacora_timeline: timeline de un flujo
CREATE INDEX IF NOT EXISTS ix_bitacora_flujo_fecha 
ON bitacora_timeline(documento_flujo_id, created_at);

-- notificaciones: bandeja de no leídas
CREATE INDEX IF NOT EXISTS ix_notif_usuario_no_leidas 
ON notificaciones(usuario_destino_id, leida) WHERE leida = FALSE;
```

**Verificar índices existentes primero:**
```bash
docker exec sgd-postgres psql -U sgd -d sgd -c "
SELECT indexname, indexdef FROM pg_indexes 
WHERE tablename IN ('tareas', 'bitacora_timeline', 'notificaciones');
"
```

---

## Tarea B.2 — Cache de feriados en Redis para cálculo de SLA en días hábiles

### Descripción
El cálculo de días hábiles (excluyendo fines de semana + feriados) es la operación más costosa del SLA. Cachear la lista de feriados del año en Redis reduce la latencia de 50ms a <1ms por consulta.

### Implementación

```python
# backend/app/services/feriado_cache.py

import json
from datetime import date
from typing import List
from sqlalchemy import select
from app.core.redis import redis_client
from app.models.feriado import Feriado

CACHE_KEY = "feriados:all"
CACHE_TTL = 3600 * 24  # 24 horas

async def get_feriados_cached(db) -> List[date]:
    """Retorna lista de fechas feriadas, con cache en Redis."""
    cached = await redis_client.get(CACHE_KEY)
    if cached:
        return [date.fromisoformat(d) for d in json.loads(cached)]
    
    result = await db.execute(select(Feriado.fecha))
    fechas = [row[0] for row in result.all()]
    
    await redis_client.setex(CACHE_KEY, CACHE_TTL, 
                             json.dumps([d.isoformat() for d in fechas]))
    return fechas

def contar_dias_habiles(desde: date, hasta: date, feriados: List[date]) -> int:
    """
    Cuenta días hábiles entre dos fechas (excluye sábados, domingos y feriados).
    """
    count = 0
    current = desde
    while current <= hasta:
        if current.weekday() < 5 and current not in feriados:
            count += 1
        current += timedelta(days=1)
    return count
```

### Aplica a
- Helper `calcular_color_sla()` de Fase 5
- Cron de reasignación de Fase 7

---

## Tarea B.3 — Paginación con cursor (keyset pagination) para bandejas grandes

### Descripción
Cuando un usuario tenga 500+ tareas en su bandeja, `OFFSET/LIMIT` se vuelve lento. Implementar cursor-based pagination para `GET /tareas`.

### Implementación
```python
@router.get("/tareas")
async def list_tareas(
    request: Request,
    cursor: Optional[int] = Query(None, description="ID de la última tarea vista"),
    limit: int = Query(20, le=100),
    ...
):
    if cursor:
        stmt = stmt.where(Tarea.id > cursor)
    stmt = stmt.order_by(Tarea.id.asc()).limit(limit)
```

### ✅ Criterio de cierre
- Las queries de bandeja se ejecutan en <10ms con 1000 tareas simuladas
- El cron de reasignación encuentra tareas vencidas en <50ms
- El cache de feriados reduce latencia del cálculo de SLA

---

# FASE TRANSVERSAL C: MONITOREO Y OPERACIONES

> **Naturaleza:** Transversal — scripts, health checks y procedimientos operativos para mantener el sistema saludable en producción.
>
> **Riesgo:** 🟢 Bajo

---

## Tarea C.1 — Health checks para nuevos servicios

### Descripción
Agregar health checks en `docker-compose.qas.yml` para:
- Celery periodic tasks (que el beat schedule está activo)
- Graph API connectivity (si está habilitado)
- SMTP connectivity (si está habilitado)
- Storage write test

### Ejemplo para health check del storage
```yaml
backend:
  healthcheck:
    test: ["CMD-SHELL", "python -c \"from pathlib import Path; exit(0 if Path('/app/storage/documentos').is_dir() else 1)\""]
    interval: 60s
    timeout: 10s
    retries: 3
```

---

## Tarea C.2 — Script de backup de documentos

### Descripción
Los documentos físicos en `/app/storage/documentos/` no están incluidos en el backup de BD. Crear script que backupée el storage.

### Script
```bash
#!/bin/bash
# scripts/backup_documentos.sh
BACKUP_DIR="/opt/sgd/backups/documentos"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

tar -czf "${BACKUP_DIR}/documentos_${TIMESTAMP}.tar.gz" \
  -C /app/storage/documentos .

# Mantener solo los últimos 30 backups
find "${BACKUP_DIR}" -name "documentos_*.tar.gz" -mtime +30 -delete
```

Agregar al crontab del servidor QAS:
```bash
0 3 * * * bash /opt/sgd/scripts/backup_documentos.sh
```

---

## Tarea C.3 — Script de rollback por fase

### Descripción
Cada fase debe tener un procedimiento de rollback documentado. Crear script genérico `rollback_fase.sh` que reciba el número de fase y ejecute las acciones de reversión.

### Ejemplo de rollback para Fase 2 (Control Descargas)
```bash
#!/bin/bash
# scripts/rollback_fase.sh
# Uso: bash scripts/rollback_fase.sh <numero_fase>

FASE=$1

case $FASE in
  2)
    echo "[ROLLBACK] Fase 2: Eliminando tabla descargas_contador..."
    docker exec sgd-postgres psql -U sgd -d sgd -c "DROP TABLE IF EXISTS descargas_contador CASCADE;"
    docker exec sgd-backend alembic downgrade -1
    echo "[ROLLBACK] Fase 2: Hecho."
    ;;
  *)
    echo "Fase $FASE no tiene rollback automatizado. Revertir manualmente."
    ;;
esac
```

---

## Tarea C.4 — Logs estructurados (JSON) para el cron

### Descripción
Los logs del cron de reasignación deben ser en formato JSON para poder ser ingeridos por herramientas de monitoreo (ELK, Datadog, etc.).

### Implementación
```python
import json, logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra"):
            log_entry.update(record.extra)
        return json.dumps(log_entry)
```

### ✅ Criterio de cierre
- Todos los servicios nuevos tienen health checks en QAS
- Backup de documentos se ejecuta diariamente
- Rollback script existe para cada fase
- El cron loggea en formato JSON

---

# FASE TRANSVERSAL D: TESTING INTEGRAL Y MIGRACIÓN DE DATOS

> **Naturaleza:** Transversal — asegura que los datos existentes (10 documentos seed, usuarios, configuraciones) no se pierdan ni corrompan al implementar nuevas fases.
>
> **Riesgo:** 🟡 Medio — si no se migran los datos existentes, los documentos creados antes de R3 no tendrán tareas, timeline, etc.

---

## Tarea D.1 — Script de migración de datos existentes a R3

### Descripción
Los 10 documentos seed actuales (más los que se hayan creado durante testing) no tienen:
- Tareas en `tareas` (los revisores/aprobadores están en JSONB de `documento_flujo`)
- Timeline en `bitacora_timeline`
- Notificaciones

### Script: `backend/scripts/migrar_jsonb_a_r3.py`

```python
"""
Script idempotente para migrar datos del schema R2 (JSONB) a R3 (tablas N:M).

Qué hace:
1. Por cada DocumentoFlujo con revisor_ids != []:
   - Crear N tareas de tipo REVISION (una por revisor)
   - Si el documento está APROBADO → estado=COMPLETADO
   - Si está EN_REVISION → estado=PENDIENTE
2. Por cada DocumentoFlujo con aprobador_ids != []:
   - Crear N tareas de tipo APROBACION
3. Poblar documento_reemplazos desde reemplaza_documento_ids
4. Poblar documento_alcance_difusion desde alcance_difusion_ids
5. Crear nodo inicial en bitacora_timeline para cada documento

Es IDEMPOTENTE: si se corre 2 veces, no duplica datos.
"""

async def migrar_jsonb_a_r3(db: AsyncSession):
    """Ejecuta la migración. Idempotente."""
    
    # Verificar si ya se ejecutó
    count = await db.execute(select(func.count(Tarea.id)))
    if count.scalar_one() > 0:
        logging.info("Migración R3 ya ejecutada. Saltando.")
        return
    
    flujos = await db.execute(
        select(DocumentoFlujo)
        .where(DocumentoFlujo.activo == True)
        .options(selectinload(DocumentoFlujo.documento))
    )
    
    for flujo in flujos.scalars():
        doc = flujo.documento
        
        # 1. Migrar revisores
        for revisor_id in (flujo.revisor_ids or []):
            estado = "COMPLETADO" if doc.estatus == EstatusDocumento.APROBADO else "PENDIENTE"
            tarea = Tarea(
                documento_flujo_id=flujo.id,
                usuario_id=revisor_id,
                tipo_tarea=TipoTarea.REVISION,
                estado=estado,
                fecha_asignacion=flujo.fecha_solicitud,
            )
            db.add(tarea)
        
        # 2. Migrar aprobadores
        for aprobador_id in (flujo.aprobador_ids or []):
            estado = "COMPLETADO" if doc.estatus == EstatusDocumento.APROBADO else "PENDIENTE"
            tarea = Tarea(
                documento_flujo_id=flujo.id,
                usuario_id=aprobador_id,
                tipo_tarea=TipoTarea.APROBACION,
                estado=estado,
                fecha_asignacion=flujo.fecha_solicitud,
            )
            db.add(tarea)
        
        # 3. Crear timeline inicial
        bitacora = BitacoraTimeline(
            documento_flujo_id=flujo.id,
            usuario_id=flujo.elaborador_id or 1,
            accion="CREADO",
            color_nodo="azul",
            created_at=flujo.created_at,
        )
        db.add(bitacora)
    
    await db.commit()
    logging.info(f"Migración R3 completada. Tareas creadas: {count_inserted}")
```

---

## Tarea D.2 — Actualizar seed_documentos.py para crear tareas

### Descripción
El seed actual solo crea documentos. Debe también crear las tareas correspondientes para que los datos de prueba incluyan tareas.

```python
# En seed_documentos.py, después de crear cada documento:
# Crear tareas de revisión
for revisor_id in FLUJO_REVISORES[i]:
    tarea = Tarea(
        documento_flujo_id=flujo.id,
        usuario_id=revisor_id,
        tipo_tarea=TipoTarea.REVISION,
        estado="PENDIENTE" if estatus == "EN_REVISION" else "COMPLETADO",
        fecha_asignacion=flujo.fecha_solicitud,
    )
    db.add(tarea)
```

---

## Tarea D.3 — Población de datos de prueba para Testing

### Descripción
Crear script `seed_r3_test_data.py` que genere datos de prueba completos para validar el flujo:

| Dato | Cantidad | Propósito |
|------|----------|-----------|
| Documentos en LIBERACION_ETO | 2 | Para probar bandeja ETO |
| Documentos EN_REVISION con tareas | 3 | Para probar bandeja revisores |
| Documentos EN_CORRECCION | 1 | Para probar bypass directo |
| Documentos APROBADO sin publicar | 1 | Para probar publicación |
| Tareas vencidas | 2 | Para probar cron de reasignación |
| Notificaciones no leídas | 5 | Para probar badge de campana |

---

## Tarea D.4 — Suite de tests de integración (end-to-end)

### Descripción para cada fase

Cada fase debe incluir:
1. **Tests unitarios** de los nuevos servicios (pytest, SQLite)
2. **Tests de integración** con BD real (PostgreSQL via Docker)
3. **Tests de API** (cliente HTTP contra backend real)

### Estructura de tests sugerida

```
backend/tests/
├── test_tarea_service.py          # Fase 5: 15-20 tests
├── test_timeline_service.py       # Fase 4: 8-10 tests
├── test_notificacion_service.py   # Fase 5: 8-10 tests
├── test_descarga_contador.py      # Fase 2: 8-10 tests
├── test_flujo_completo.py         # Fase 6: 5 tests E2E
├── test_cron_reasignacion.py      # Fase 7: 5-6 tests
├── test_email_service.py          # Fase 8: 4-5 tests
├── test_graph_integration.py      # Fase 9: 3-4 tests (mockeados)
├── test_pdf_generation.py         # Fase 10: 4-5 tests
└── test_migracion_r3.py           # Fase D: 4-5 tests
```

### Requisito por fase
```
Cada fase DEBE mantener: pytest 340+ PASS (nunca bajar la cantidad)
Cada fase NUEVA agrega: mínimo 5-10 tests nuevos
```

### 🧪 Escenario de prueba E2E completo (post-Fase 6)

```
PRECONDICIÓN: Todos los servicios implementados

1. Login como elaborador_revisor (usuario local)
2. Ir a /#/aprobacion-documento
3. Completar wizard: Creación, Procedimiento, Gerencia CAL, Área CC
4. Subir documento principal .docx
5. Agregar 2 formularios
6. Paso 2: No requiere eval, No requiere control lectura
7. Difusión: seleccionar 2 áreas
8. Paso 3: Agregar 2 revisores + 1 aprobador
9. Firmar y enviar → ✅ documento creado en LIBERACION_ETO
10. ✅ Verificar: bitacora_timeline tiene nodo "CREADO" (azul)
11. ✅ Verificar: documento_flujo.estado_actual = LIBERACION_ETO

12. Login como eto_test
13. Ir a /#/bandeja → ver tarea de liberación
14. Atender → /#/liberacion-detalle
15. Ver formulario del solicitante
16. Seleccionar Proceso "0004 — Fabricacion"
17. Liberar documento → ✅
18. ✅ Verificar: se crearon 2 tareas REVISION (una por revisor)
19. ✅ Verificar: notificaciones creadas para cada revisor
20. ✅ Verificar: timeline tiene LIBERADO_ETO (verde) + 2x PENDIENTE (ámbar)

21. Login como elaborador_revisor (tiene rol revisor)
22. Ir a /#/bandeja → ver tarea de revisión
23. Atender → /#/revision
24. Ver documento (via SharePoint link)
25. Aprobar → ✅ tarea COMPLETADO
26. ✅ Verificar: timeline APROBADO (verde)

27. Login como otro revisor
28. Repetir: RECHAZAR con observación
29. ✅ Verificar: observación guardada en tarea_observaciones
30. ✅ Verificar: timeline RECHAZADO (rojo)

31. Login como elaborador_revisor original
32. Ir a /#/correccion
33. Ver observación
34. Corregir y reenviar → ✅ bypass directo al revisor que observó
35. ✅ Verificar: NO pasó por ETO
36. ✅ Verificar: timeline CORREGIDO (azul)

37. Login como revisor que observó
38. Aprobar la corrección → ✅
39. ✅ Verificar: al ser el último revisor OK, pasa a APROBACION

40. Login como aprobador
41. Aprobar → ✅
42. ✅ Verificar: documento APROBADO
43. ✅ Verificar: PDF generado con carátula
44. ✅ Verificar: timeline PUBLICADO (verde)
```

### ✅ Criterio de cierre
- Script de migración idempotente (corre 2 veces = mismo resultado)
- Seed de datos de prueba crea escenarios completos
- Tests de todas las fases suman 400+ PASS
- Escenario E2E completo verificado con Chrome MCP

---

# FASE TRANSVERSAL E: DOCUMENTACIÓN Y API

> **Naturaleza:** Transversal — mantener la documentación del proyecto actualizada con cada cambio.
>
> **Riesgo:** 🟢 Bajo

---

## Tarea E.1 — Actualizar `.env.example`

Agregar TODAS las variables nuevas:
```env
# Fase 0.2 — Microsoft Graph
MS_TENANT_ID=
MS_CLIENT_ID=
MS_CLIENT_SECRET=
GRAPH_SCOPES=https://graph.microsoft.com/.default
SHAREPOINT_SITE_ID=
GRAPH_ENABLED=false

# Fase 0.2 — SMTP
SMTP_ENABLED=false
SMTP_HOST=
SMTP_PORT=465
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=SGD COFAR
```

---

## Tarea E.2 — Actualizar `RADIOGRAFIA-TOTAL.md` al final de cada fase

### Checklist post-fase
```markdown
## Checklist de documentación post-fase

- [ ] ESTADO.md: marcar tareas completadas
- [ ] BITACORA.md: agregar entrada de sesión
- [ ] DECISIONES.md: nuevo ADR si hubo decisión técnica
- [ ] LEARNINGS-ERRORES.md: nuevos errores descubiertos
- [ ] RADIOGRAFIA-TOTAL.md: nuevas tablas, endpoints, servicios
- [ ] PLAN-MAESTRO-IMPLEMENTACION.md: marcar fase como completada
- [ ] GUIA-DEPLOY.md: si cambió el proceso de deploy
- [ ] .env.example: nuevas variables de entorno
```

---

## Tarea E.3 — OpenAPI docs para nuevos endpoints

### Descripción
FastAPI genera automáticamente OpenAPI. Pero hay que asegurar que los nuevos endpoints tengan:
- `summary` descriptivo (ya se usa en la codebase)
- `tags` correctas
- `response_model` definido
- Ejemplos de request/response en los schemas Pydantic

### Verificación
```bash
curl.exe http://localhost:18000/openapi.json | python -m json.tool | grep -E '"summary"|"tags"'
```

---

## Tarea E.4 — Mantenimiento del PLAN MAESTRO

### Reglas
1. Este documento es **vivo**: se actualiza al inicio de cada fase
2. Al completar una fase: marcar con ✅ en el índice
3. Si se descubre un impedimento: agregar nota al pie de la fase afectada
4. Si se cambia el orden: actualizar el mapa de dependencias

### ✅ Criterio de cierre
- `.env.example` actualizado con todas las variables
- Cada fase termina con su checklist de documentación cumplido
- OpenAPI docs accesible en `/docs`
- El PLAN MAESTRO refleja el estado actual del proyecto

---

## MAPA DE DEPENDENCIAS COMPLETO (con transversales)

```
Fase 0: Hotfixes ─────────────────────────────────────────────────────────────────────┐
  │                                                                                     │
  ├── Fase 1: Storage ───────────┐                                                     │
  ├── Fase 2: Control Descargas  │   ┌── T-A: Seguridad (aplica a 1,2,4,5,6,9,10) ──┤ │
  ├── Fase 3: Procesos           │   ├── T-B: Performance (aplica a 4,5,6,7) ────────┤ │
  └── Fase 4: Timeline ────────┐ │   ├── T-C: Monitoreo (aplica a 7,8,9) ───────────┤ │
                               ▼ ▼   ├── T-D: Testing (aplica a TODAS) ─────────────┤ │
                          Fase 5:     └── T-E: Documentación (aplica a TODAS) ──────┘ │
                       Servicios Core                                                    │
                          │                                                             │
               ┌──────────┼──────────┐                                                  │
               ▼          ▼          ▼                                                  │
          Fase 6:     Fase 7:    Fase 8:                                                │
       Flujo Completo Delegación  Notificaciones                                        │
               │          │                                                             │
               ▼          ▼                                                             │
          Fase 10:    Fase 9:                                                          │
       PDF + Carátula SharePoint                                                        │
               │          │                                                             │
               ▼          ▼                                                             │
          Fase 11: Limpieza y Migraciones                                               │
               │                                                                        │
               ▼                                                                        │
          Fase 12: Reasignación ETO                                                     │
               │                                                                        │
               ▼                                                                        │
          🎯 FLUJO DOCUMENTAL COMPLETO ◄────────────────────────────────────────────────┘
```

---

**Fin del documento.**

