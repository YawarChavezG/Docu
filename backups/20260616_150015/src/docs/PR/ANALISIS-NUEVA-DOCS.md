# ANÁLISIS COMPARATIVO — Documentación nueva vs Plan actual

> **Fecha:** 2026-06-14
> **Fuente nueva:** `docs/Diagramas_Matrices/` (10 diagramas de casos de uso, 20 diagramas de flujo, 7 excels de matrices, 1 word de plantillas, 7 plantillas documentales reales).
> **Propósito:** Detectar huecos y alinear el plan + BD antes de escribir código que luego haya que refactorizar.

---

## 1. Resumen ejecutivo

| Categoría | Hallazgos |
|---|---|
| ✅ Cosas que SÍ coinciden | ~16 (stack, 9 épicas, login AD, wizard, workflow paralelo, bypass, SLA base, inmutabilidad, etc.) |
| 🟡 Refinamientos necesarios (no rompen plan, ajustan) | 7 (umbral IA 70%→60%, SLA 10 hábiles→"10 hábiles o 15 calendario", límite 20MB→20MB+20archivos, etc.) |
| 🔴 Cambios estructurales a la BD | 7 (5 roles reales, 13 tipos doc, 8 gerencias, 25 áreas, tabla `usuario_modulos`, catálogo de vigencias, catálogo de límites de descarga) |
| ⚪ Cosas que faltan en la doc nueva | 6 (sync AD, firma digital, desvinculación, paginación, etc.) — **no rompen, se llenan con supuestos** |

**Veredicto:** El plan está **80% alineado**. Los cambios necesarios son **todos asimilables antes de la primera migración Alembic** (tarea #8). **No hay que reescribir nada todavía.**

---

## 2. Hallazgos críticos que cambian la BD

### 🔴 H-01: 5 roles reales, no 4

**Origen:** `USUARIOS EXISTENTES A ABRIL.xlsx` columna "ROL EN EL FLUJO"

| # | Rol real | Equivalencia en mi plan | Permisos implícitos |
|---|---|---|---|
| 1 | `ADMIN` | `admin` | Configuración + Parametrización + ver todo |
| 2 | `ETO` | `eto` | Liberación + Liberación + Generación copias + Parámetros ETO |
| 3 | `ELABORADOR - REVISOR` | parte de `estandar` | Crear + Revisar (NO aprobar) |
| 4 | `ELABORADOR - REVISOR - APROBADOR` | parte de `estandar` | Crear + Revisar + Aprobar |
| 5 | `VISUALIZADOR (CL-EVAL)` | `visualizador` + (CL-EVAL) | Solo lectura + Control de Lectura + Examen (capacitación) |

**Cambio en BD:** Tabla `roles` tendrá 5 entradas exactas. El "rol 5" lleva "(CL-EVAL)" porque también hace Control de Lectura y Evaluación, no solo lectura. La sigla `CL-EVAL` debería abreviarse a `cl_eval` en el enum de BD.

**Impacto en código:** Cambiar el stub de `auth.py` y el frontend `store/auth.js`. El roleLabel en el frontend se mantiene en español.

---

### 🔴 H-02: 10 módulos por usuario, no permisos derivados del rol

**Origen:** `USUARIOS EXISTENTES A ABRIL.xlsx` columna "MODULOS HABILITADOS"

```
Módulos reales:
- BANDEJA DE TAREAS, MI BANDEJA
- LISTA MAESTRA
- CONSULTAR DOCUMENTOS
- MIS EVALUACIONES
- ASISTENTE IA
- NUEVA SOLICITUD
- PLANTILLAS DOCUMENTALES
- PARAMETRIZACIÓN GENRAL
- REPORTES (no en mi plan original)
- TODOS
```

**Diferencia con mi plan:** Yo asumía RBAC basado en el rol. La realidad es que COFAR quiere un **N:M** usuario→módulo. Mismo usuario puede tener módulos distintos a otro con el mismo rol.

**Cambio en BD:** Crear tabla `usuario_modulos` (usuario_id, modulo_id). Módulo como catálogo aparte.

**Tablas nuevas:**
- `modulos` — catálogo: `id, codigo, nombre, descripcion, ruta_ui`
- `usuario_modulos` — N:M

**Endpoints nuevos:**
- `GET /api/v1/usuarios/{id}/modulos`
- `PUT /api/v1/usuarios/{id}/modulos` (admin)

**Nota:** El módulo "TODOS" indica un superusuario (probablemente ADMIN o ETO). La lógica: si el usuario tiene el módulo "TODOS" en `usuario_modulos`, no se valida por módulo específico (es bypass).

---

### 🔴 H-03: 13 tipos de documento, no 6 — CON NOMENCLATURA CORREGIDA

**Origen:** `TIPOS DE DOCUMENTO, CÓDIGO Y VIGENCIA.xlsx` + confirmación del cliente en sesión 2.

**13 tipos confirmados, con sus códigos numéricos:**

| Cód | Nombre | Vigencia | Sigla legacy | Max descargas/día |
|---|---|---|---|---|
| 1 | METODOLOGÍA | 4 años | MET | 10 |
| 2 | MANUAL DE FUNCIONES | INDEFINIDO | MAF | 3 |
| 3 | POLÍTICA | 4 años | POL | 1 |
| 4 | PLAN | 4 años | PLA | 1 |
| 5 | PROCEDIMIENTO | 4 años | PRO | 1 |
| 6a | INSTRUCTIVO | 4 años | INS | 1 |
| 6b | INSTRUCTIVO TÉCNICO | INDEFINIDO (solo Mant.) | ITM | 1 |
| 7 | ESPECIFICACIÓN | 4 años | ESP | 10 |
| 9 | PROTOCOLO | INDEFINIDO | PRT | 1 |
| 10 | MANUAL DE PROCESO | 4 años | MAP | 1 |
| 12 | MANUAL | 4 años | MAN | 1 |
| 13 | MANUALES DE USUARIO | INDEFINIDO | MAU | 1 |
| 14 | FICHA DE CARACTERIZACIÓN | 4 años | FIC | 1 |

**NOMENCLATURA DEL CÓDIGO DE DOCUMENTO (decidida en sesión 2):**
```
{sigla_area}-{codigo_tipo}-{correlativo_3_digitos}  v{version_2_digitos}
```

**Ejemplo:** `CC-5-001 v01`
- `CC` = sigla del área (Control de Calidad)
- `5` = código numérico del tipo de documento (PROCEDIMIENTO)
- `001` = correlativo de 3 dígitos dentro de (área, tipo)
- `v01` = versión de 2 dígitos (v00 = creación, v01+ = actualización)

**Razón:** compatibilidad con el sistema legacy de COFAR. Los documentos antiguos tienen esta nomenclatura y se mantiene en el nuevo sistema para evitar renombrar masivamente.

**CC-1 = Metodología, CC-7 = Especificación** (confirmado por el cliente en sesión 2). Por eso tienen `max_descargas_dia = 10` (US-2.01 lo mencionaba).

**Cambio en BD:** Tabla `tipos_documento` con:
```
id, codigo (1-14, INT), nombre, sigla_legacy (MET, PRO, etc.), 
vigencia_anos (nullable), es_indefinido (bool),
max_descargas_dia (default 1), observacion, activo
```

**Cambio en `codigo_contador`:** ahora la secuencia atómica es por `(area_id, tipo_documento_codigo)`, no por sigla.

**Cambio en US-2.05 (Reemplazos):** los códigos se guardan como `string` completo (ej: "CC-5-001") y se validan con regex `^[A-Z]{2,4}-\d{1,2}-\d{3}$`.

**Reglas especiales:**
- `INSTRUCTIVO TÉCNICO` (cód 6b) tiene código numérico igual a `INSTRUCTIVO` (6) pero se diferencia por tener `es_indefinido = true` y `observacion = "Solo Mantenimiento"`. **Mismo correlativo, distinto tipo.** El sistema permite que existan CC-6-001 (Instructivo) y CC-6-002 (Instructivo Técnico) coexistiendo.

---

### 🔴 H-04: 8 gerencias, ~25 áreas con siglas

**Origen:** `GERENCIAS, AREAS Y SIGLAS.xlsx` + `ASIGNACION AUTOMATICA ANALISTAS ETO.xlsx`

| Gerencia | Sigla gerencia | Áreas | Siglas áreas |
|---|---|---|---|
| CALIDAD | CAL | 11 (CC, DT, EST, GAC, MCB, REG, VAL, FV, BEQ, IDF, DEI) | 2-3 chars |
| PLANTA | PLA | 9 (ACD, BET, LE, LNE, SIMA, SMS, SNE, CB, PRO) | |
| RECURSOS HUMANOS | RRH | 3 (MLB, TAL, ADM) | |
| ADMIN-FINANCIERA | ADM | (en matriz ETO, no detallado) | |
| COMERCIAL | COM | (en matriz ETO, no detallado) | |
| GENERAL | GEN | (en matriz ETO, no detallado) | |
| TERCIA | TER | (en matriz ETO, no detallado) | |
| LOGISTICA | LOG | (en matriz ETO, no detallado) | |
| OPERACIONES | OPS | (en matriz ETO, no detallado) | |
| AUDITORIA INTERNA | AUD | (en matriz ETO, no detallado) | |

**Cambio en BD:** Tabla `gerencias` (id, sigla, nombre). Tabla `areas` (id, sigla, nombre, gerencia_id FK). Sembrar las 10 gerencias y ~25 áreas.

**Nota:** La matriz de gerencias tiene 4 gerencias con áreas; la matriz de asignación ETO añade 6 gerencias sin áreas específicas (probablemente áreas que están dentro de las primeras 4 pero se enrutan a un ETO distinto).

---

### 🔴 H-05: Límite de descarga por TIPO de documento, no global

**Origen:** `MAXIMA DESCARGA DE EDITABLES.xlsx`

| Tipo | Max descargas/día | Observación |
|---|---|---|
| METODOLOGÍA | 10 | |
| ESPECIFICACIÓN | 10 | |
| MANUAL DE FUNCIONES | 3 | |
| POLÍTICA | 1 | doc + formularios |
| PLAN | 1 | doc + formularios |
| PROCEDIMIENTO | 1 | doc + formularios |
| INSTRUCTIVO | 1 | doc + formularios |
| INSTRUCTIVO TÉCNICO | 1 | doc + formularios |
| PROTOCOLO | 1 | |
| MANUAL DE PROCESO | 1 | doc + formularios |
| MANUAL | 1 | doc + formularios |
| MANUALES DE USUARIO | 1 | |
| FICHA DE CARACTERIZACIÓN | 1 | |

**Cambio en BD:** Agregar columna `max_descargas_dia INT DEFAULT 1` a `tipos_documento`. La lógica de validación consulta este campo, no una constante hardcoded.

**Lógica en backend:**
```python
tipo_doc = db.query(TipoDocumento).filter_by(codigo=tipo_doc_codigo).first()
if descargas_hoy_usuario >= tipo_doc.max_descargas_dia:
    raise HTTPException(429, "Límite diario de descargas alcanzado")
```

---

### 🔴 H-06: 2 analistas ETO con 7+ gerencias asignadas

**Origen:** `ASIGNACION AUTOMATICA ANALISTAS ETO.xlsx`

| ETO | Gerencias atendidas |
|---|---|
| ARACELY ROMERO | CALIDAD, PLANTA, GENERAL, TERCIA |
| CECILIA ESPINOZA | ADMIN-FINANCIERA, COMERCIAL, RECURSOS HUMANOS, LOGISTICA, OPERACIONES, AUDITORIA INTERNA |

**Cambio en BD:** Sembrar `matriz_enrutamiento_eto` con 10 filas (no 1 fila por gerencia). La tabla tendrá:
```
matriz_enrutamiento_eto
├── id
├── gerencia_id (FK)
├── analista_eto_id (FK a usuarios donde rol='ETO')
├── fecha_desde (opcional, para histórico)
├── fecha_hasta (NULL = vigente)
├── activo BOOL
```

**Lógica de fallback (US-1.07):**
1. Buscar ETO asignado a la gerencia del documento.
2. Si ETO está ausente (campo `usuarios.ausente = true`):
   - Verificar si tiene delegado configurado.
   - Si no → Round-Robin entre los OTROS ETOs del sistema.
3. Si no hay otros ETOs disponibles → ETO cualquiera (alerta).

---

### 🔴 H-07: 156 usuarios con rol activo, 139 SIN delegado

**Origen:** `USUARIOS EXISTENTES A ABRIL.xlsx`

```
Usuarios con rol activo (que REQUIEREN delegado): 156
  - Con delegado asignado: 17 (10.9%)
  - Sin delegado (alerta): 139 (89.1%)
```

**Esto es un problema operativo real.** La US-1.03 preveía una alerta en el perfil; en la realidad el 89% de los usuarios con tareas tienen la alerta activa.

**Cambio en BD:** Tabla `delegaciones` ya estaba en mi plan, pero ahora con volúmenes esperados:
- 156 usuarios con rol activo → 156 entradas en `delegaciones` (muchas NULL por ahora, hasta que completen la asignación).
- La alerta visual en el frontend no es opcional, es prioritaria en R1.

**Endpoint crítico en R1:**
- `GET /api/v1/usuarios/{id}/estado-delegacion` que devuelve `{ tiene_delegado: bool, alerta: bool }`.

---

## 3. Refinamientos (no rompen BD, ajustan lógica)

### 🟡 H-08: SLA = 10 días hábiles **O** 15 calendario (lo primero)

**Origen:** `PLAZOS PARA LA EJECUCIÓN DE TAREAS.xlsx`

```
REVISION: 10 DIAS HABILES o 15 DIAS CALENDARIO (lo que ocurra primero)
APROBACION: 10 DIAS HABILES o 15 DIAS CALENDARIO
CONTROL DE LECTURA: 30 DIAS CALENDARIO
EVALUACIONES: SEGÚN PLAZO DEFINIDO EN EVALUACIÓN
```

**Cambio en `configuracion_global`:** Mantener `plazo_revision_dias_habiles=10` y `plazo_revision_dias_calendario=15`. La lógica del cron evalúa AMBOS y dispara reasignación cuando se cumpla el primero.

**Semáforo en bandeja:**
- Verde: día 0-4 (hábil)
- Amarillo: día 5-7
- Rojo: día 8-10

(El plan original ya contemplaba el semáforo, esto lo confirma.)

---

### 🟡 H-09: Doble límite: 20 archivos por solicitud Y 20 MB por archivo

**Origen:** `LIMITE ARCHIVOS.xlsx` (CORREGIDO en sesión 2)

```
- 20 ARCHIVOS por solicitud en total (1 doc "padre" + formularios/anexos)
- 20 MB de tamaño MÁXIMO POR CADA ARCHIVO INDIVIDUAL (NO del total)
- Ejemplo: 8.3 MB / 75 hojas (de un solo archivo)
```

**NO es "20 archivos Y 20 MB total".** Es:
- Límite 1: cantidad de archivos en la solicitud ≤ 20
- Límite 2: tamaño de cada archivo individual ≤ 20 MB

**Cambio en `configuracion_global`:**
- `max_archivos_por_solicitud = 20` (default)
- `max_mb_por_archivo = 20` (default)

**Lógica en upload endpoint (validar AMBOS, errores distintos):**
```python
if file.size_mb > settings.max_mb_por_archivo:
    raise HTTPException(413, f"Archivo '{file.name}' excede {max_mb_per_file}MB")
if total_files_in_request > settings.max_archivos_por_solicitud:
    raise HTTPException(413, f"Solicitud excede {max_files} archivos totales")
```

---

### 🟡 H-10: Umbral de IA similitud 60%, no 70%

**Origen:** `Diagrama EPICA 4` (US-4.02)

Texto literal: *"Si el riesgo es > 60%: Muestra una tabla con los documentos conflictivos"*.

**Mi plan decía 70%** (lo copié de Gemini/Antigravity). **Debe ser 60%.**

**Cambio:** `configuracion_global.umbral_similitud_ia = 0.60` (default 0.60, ajustable).

---

### 🟡 H-11: Vigencia por defecto = 4 años, pero 4 tipos son INDEFINIDOS

**Origen:** `TIPOS DE DOCUMENTO, CÓDIGO Y VIGENCIA.xlsx` columna "Observación"

Tipos con `vigencia INDEFINIDO`:
- MANUAL DE FUNCIONES (cód 2)
- INSTRUCTIVO TÉCNICO (cód 6b, solo Mantenimiento)
- PROTOCOLO (cód 9)
- MANUALES DE USUARIO (cód 13)

**Cambio en BD:** Columna `es_indefinido BOOL` en `tipos_documento`. Cuando se crea un documento, si `es_indefinido=true`, el `documento_versiones.fecha_expiracion = NULL`.

**Lógica frontend:** El campo "Tiempo de vigencia" en el Paso 2 del wizard debe ser **readonly** para los 4 tipos indefinidos, con texto "INDEFINIDO" visible.

---

### 🟡 H-12: 7 plantillas documentales reales (archivos .docx/.xlsx)

**Origen:** `MATRICES/PLANTILLAS DOCUMENTALES/` contiene 7 archivos:
- 3 FORMATO PARA M...
- 4 FORMATO PARA PL...
- 5 FORMATO PARA PR...
- 6 FORMATO PARA IN... (2 archivos)
- 10 FORMATO PARA M...
- 13 FORMATO PARA M...
- 14 FORMATO PARA F...

**Cambio en BD:** Tabla `plantillas_documentales` ya estaba en mi plan. Ahora con los 7 archivos reales:
- id, tipo_documento (FK), nombre, ruta_storage, version, fecha_subida, subido_por, activo

**En R1** (tarea #14 del plan): seed de estas 7 plantillas copiándolas al volumen de Docker.

---

### 🟡 H-13: Rango de fechas "dd/mm/aaaa" en UI (formato Bolivia)

**Origen:** Múltiples diagramas: "DESDE: DD/MM/AAAA"

**Cambio:** El frontend ya usa `es-BO` locale, pero hay que asegurar que los inputs de fecha nativos usen ese formato. En Alpine, agregar `:placeholder="'DD/MM/AAAA'"` y `formatDate()` en utilidades.

---

## 4. Hallazgos de alcance (R6 Reportes)

### 🟡 H-14: 4 KPIs + 2 series temporales definidos

**Origen:** `REPORTES GRAFICOS.xlsx`

```
KPI 1: DOCUMENTOS EN REVISION (count)
KPI 2: DOCUMENTOS EN APROBACIÓN (count)
KPI 3: DOCUMENTOS OBSERVADOS (EN CORRECCIÓN) (count)
KPI 4: EN LIBERACIÓN POR ETO (count)

Serie temporal 1: DOCUMENTOS APROBADOS POR MES (total)
Serie temporal 2: APROBADOS POR MES, SEPARADOS en "generales" vs "met y especificaciones"
```

**Drill-down:** al hacer clic en un KPI, se abre el detalle (código, título, versión, responsables).

**Cambio en plan:** Agregar al alcance de R6 (Épica 8) los endpoints:
- `GET /api/v1/reportes/kpis` → 4 KPIs
- `GET /api/v1/reportes/aprobados-por-mes?year=2026&tipo=general` → serie temporal
- `GET /api/v1/reportes/kpi-detalle?kpi=revision` → drill-down

**Implementación:** Vistas SQL agregadas (no tablas adicionales). E.g.:
```sql
CREATE VIEW v_kpis_documentos AS
SELECT
  COUNT(*) FILTER (WHERE etapa_actual = 'En Revision') AS en_revision,
  ...
FROM documento_versiones;
```

---

## 5. Lo que NO encontré en la doc nueva (huecos) — RESUELTOS en sesión 2

| Tema | Estado final | Implementación |
|---|---|---|
| Sync AD → tabla `usuarios` | Resuelto | **Botón manual** en `Parametrización > Usuarios` (`POST /api/v1/admin/sync-ad`) + **Job diario a las 00:05** via Celery Beat. Sincroniza: inserta nuevos, marca desvinculados, actualiza email/cargo/área. Los módulos/roles NO se tocan desde AD (son exclusivos de SGD). |
| Mecanismo de "Firma Digital" (Doble Auth) | Resuelto | **2FA simple: usuario + password** (mismo que login). Endpoint `POST /api/v1/auth/verify-password` valida credenciales. Todos los flujos de firma (US-2.06, 3.03, 3.04, 6.03, 7.03, 7.06) llaman a este endpoint. Se loggea en tabla `firmas_digitales` (id, usuario_id, accion, recurso_tipo, recurso_id, timestamp, ip, resultado_exito) para auditoría. En QAS se podría escalar a MFA con AD. |
| Flujo de reasignación por desvinculación (US-1.06) | Resuelto | **Inmediata**. Cuando el sync detecta `estado='desvinculado'` y el usuario tiene tareas pendientes, inmediatamente: (1) reasigna a delegado, (2) notifica al delegado, (3) registra en bitácora, (4) actualiza `workflow_tareas.usuario_asignado_id`. Sin esperar al cron. Si el sync es manual (botón), también dispara inmediatamente. |
| Definición de "Jefe inmediato" | Diferido | **NO se implementa en R1.** TODO con prioridad baja. Por ahora la fallback chain de reasignación es: delegado → otro ETO round-robin → cola ETO. Se documenta en `DECISIONES.md` como decisión de diferimiento. |
| Paginación de Mi Bandeja | Resuelto | **Parámetro configurable** en `configuracion_global` (default 10). Endpoint CRUD `PUT /api/v1/parametrizacion/paginacion-bandeja` para que el admin lo cambie. El frontend lo lee al iniciar. |
| Ancho de banda de carga de archivos | Resuelto | **20 MB POR ARCHIVO** (no total). Y **20 archivos MÁXIMO POR SOLICITUD**. Ver H-09 corregido. |

---

## 6. Cambios concretos al plan y a la BD

### Plan (PRD.md)

| Tarea original | Cambio |
|---|---|
| #7 Schema Organización (5 tablas) | **+ tabla `modulos` (catálogo) + tabla `usuario_modulos` (N:M) + tabla `delegaciones` con FK a `usuarios` + tabla `ausencias`** |
| #23 Schema Documentos (3 tablas) | **+ tabla `tipos_documento` (con vigencias) + tabla `limite_descarga_tipo` (o columna en `tipos_documento`)** |
| #29 SELECT FOR UPDATE correlativos | La sigla ahora se deriva de `tipos_documento.sigla` (ej: "MET" para Metodología), NO hardcoded |
| #30 Trigger obsolescencia | Sin cambios |
| #32 Upload archivos | **Doble validación: 20 archivos Y 20 MB** (no solo MB) |
| #36 Liberar (Fan-Out) | **Buscar ETO via `matriz_enrutamiento_eto` por gerencia_id, NO hardcoded** |
| R6 Reportes | **4 KPIs + 2 series temporales definidos explícitamente** (no genérico) |

### Estructura de tablas (24 → 30 tablas estimadas)

Las 24 originales + 6 nuevas:
- `modulos` (catálogo)
- `usuario_modulos` (N:M)
- `tipos_documento` (catálogo con vigencias)
- `plantillas_documentales` (catálogo de archivos físicos)
- `v_kpis_documentos` (vista SQL)
- `v_aprobados_por_mes` (vista SQL)

**Las vistas no cuentan como tablas; son queries materializadas.** Así que en realidad son **28 tablas**.

### Sembrado (seed) adicional

- 5 roles (en `roles`)
- 10 módulos (en `modulos`)
- 10 gerencias (en `gerencias`)
- ~25 áreas (en `areas`)
- 13 tipos de documento (en `tipos_documento`)
- 7 plantillas documentales (en `plantillas_documentales`)
- 10 filas de matriz de enrutamiento ETO

---

## 7. Cuestiones para confirmar con el cliente

Antes de la primera migración, son necesarias estas 4 confirmaciones (no bloquean desarrollo, pero las pongo en el backlog):

1. **"CC-1" y "CC-7" en US-2.01** — ¿es referencia legacy (sistema viejo) o se refiere a tipos de documento (1=Metodología, 7=Especificación)? Si es lo segundo, ya está cubierto por `tipos_documento.max_descargas_dia`. Si es lo primero, hay que mantener compatibilidad con códigos viejos.
2. **"Jefe inmediato"** — ¿se llena manualmente o se infiere del organigrama de AD?
3. **Sync AD** — ¿qué atributos copiar? (propuesta: username, email, nombre_completo, cargo, area; los módulos/roles/delegados NO se tocan desde AD)
4. **Plantillas de notificación** (Word) — ¿se suben como archivos binarios a un storage y se renderizan con Jinja2, o se guardan como HTML en la BD?

---

## 8. Veredicto final

**El plan NO necesita reescribirse.** Las 7 correcciones estructurales se aplican **agregando tablas/catalogos a la tarea #7 y #23**, no cambiando el orden ni el alcance.

**Siguiente paso recomendado:** Actualizar el archivo `docs/PR/PRD.md` § 5 (tablas BD) con la nueva lista de tablas (28) y los catalogos a sembrar. Luego arrancar con la tarea #7.

**No hay que rehacer nada de lo ya construido.** La pila Docker, el auth stub, la configuración — todo sigue siendo válido.
