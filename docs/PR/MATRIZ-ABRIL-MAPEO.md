# MATRIZ ABRIL — Mapeo de normalización

> **Fecha:** 2026-06-16 (sesión 8)
> **Fuente analizada:** `docs/Diagramas_Matrices/MATRICES/USUARIOS EXISTENTES A ABRIL.xlsx` (hoja "LISTA PERSONAL")
> **Propósito:** Documentar el mapeo exacto Excel → BD para la tarea #12 (asignación masiva).

---

## 1. Resumen del Excel

| Métrica | Valor |
|---|---|
| Filas totales (max_row - 1) | 733 |
| Filas con COFAR no nulo | **729** (4 filas vacías al final) |
| COFARs únicos | 729 (sin duplicados) |
| Columnas | 8 (COFAR, NOMBRE, POSICION, ROL EN EL FLUJO, MODULOS HABILITADOS, ¿VISUALIZA O EXPORTA REPORTES?, ¿REQUIERE DELEGADO?, NOMBRE DELEGADO) |
| Filas incompletas (sin COFAR/rol/modulos) | 0 |

### Distribución de roles (en el Excel)

| Rol | Cantidad | % | En catálogo `CodigoRol` |
|---|---:|---:|---|
| `VISUALIZADOR (CL-EVAL)` | 573 | 78.6% | ✅ |
| `ELABORADOR - REVISOR` | 146 | 20.0% | ✅ |
| `ELABORADOR - REVISOR - APROBADOR` | 8 | 1.1% | ✅ |
| `ETO` | 2 | 0.3% | ✅ |
| `ADMIN` | **0** | 0% | n/a (no aparece en la matriz) |

> **⚠️ Diferencia con plan original:** el plan decía 730 filas y 1 ADMIN. La realidad es 729 filas y 0 ADMIN. El admin del sistema (usuario `admin` stub) no está en la matriz y NO será tocado por este import.

### Módulos en el Excel (formato UI legible)

| Módulo (texto del Excel) | Apariciones | Mapeo → `CodigoModulo` |
|---|---:|---|
| `LISTA MAESTRA` | 727 | `LISTA_MAESTRA` |
| `MIS EVALUACIONES` | 727 | `MIS_EVALUACIONES` |
| `ASISTENTE IA` | 727 | `ASISTENTE_IA` |
| `BANDEJA DE TAREAS` | 573 | `BANDEJA_TAREAS` |
| `MI BANDEJA` | 154 | `MI_BANDEJA` |
| `CONSULTAR DOCUMENTOS` | 154 | `CONSULTAR_DOCUMENTOS` ⚠️ **normalizar** |
| `PLANTILLAS DOCUMENTALES` | 154 | `PLANTILLAS_DOCUMENTALES` ⚠️ **normalizar** |
| `NUEVA SOLICITUD` | 154 | `NUEVA_SOLICITUD` |
| `TODOS` | 2 | `TODOS` (bypass, solo ETO) |

**Normalización necesaria:** reemplazar `" "` (espacio) por `"_"` (guion_bajo) en los 2 módulos con espacio.

### Flags de comportamiento (SI/NO)

| Campo | SI | NO |
|---|---:|---:|
| ¿REQUIERE DELEGADO? | 156 | 573 |
| ¿VISUALIZA O EXPORTA REPORTES? | 156 | 573 |

Correlación: 100% con `rol ≠ VISUALIZADOR`. Los 156 no-visualizadores (146 ELAB + 8 APROB + 2 ETO) tienen ambos flags en SI.

### Delegados mencionados (texto libre)

| Métrica | Valor |
|---|---|
| Usuarios que requieren delegado | 156 |
| Usuarios con nombre concreto en `NOMBRE DELEGADO` | 17 |
| Usuarios con `NA` o vacío (a pesar de requerir) | 139 |
| Delegados únicos (case-insensitive) | 13 |

**Top delegados más frecuentes** (riesgo de cuello de botella):

| Delegado | Cantidad |
|---|---:|
| `SUSANA BLANCO` | **5** ← punto crítico |
| `MILTON MANOTAS`, `JOSUE CACHI`, `ELBA CAMARGO`, `ERICK VALDEZ`, `DANIELA MIRANDA`, `GINA ESCOBAR`, `ARACELY ROMERO`, `CECILIA ESPINOZA`, `OSIRIS MURILLO`, ... | 1 c/u |

> **Decisión (ver § 3):** por la baja cobertura (17/156 = 11%) y los nombres en MAYÚSCULAS vs MAYÚSCULAS-Y-titleCase en BD, **no se resuelve delegado en este import**. Queda como **deuda técnica #13**.

---

## 2. Validación contra la BD

| Métrica | Valor |
|---|---:|
| Total usuarios en BD | 764 |
| Con `ad_postal_code` no vacío | 754 |
| COFARs del Excel | 729 |
| **Matchean `ad_postal_code == str(COFAR)`** | **717 (98.4%)** |
| **NO matchean** | **12** |

### 12 COFARs del Excel sin match en BD (ordenados)

```
10001634, 10001729, 10002504, 10002811, 10002875, 10002880,
10002968, 10003198, 10003200, 10003207, 10003230, 10003237
```

> **Interpretación:** estos 12 usuarios están en la matriz del cliente pero NO fueron sincronizados desde AD. Posibles causas: desvinculados recientemente, cuentas bloqueadas, o dados de alta después del último sync. **El import los reporta como warning y los SKIP** (no se pueden crear usuarios nuevos sin email/cargo/area — info incompleta para SGD).

### Catálogos en BD que el import usará

**Roles (5/5):**

| `CodigoRol` (BD) | id |
|---|---:|
| `ADMIN` | 1 |
| `ETO` | 2 |
| `ELABORADOR - REVISOR` | 3 |
| `ELABORADOR - REVISOR - APROBADOR` | 4 |
| `VISUALIZADOR (CL-EVAL)` | 5 |

**Módulos (9/11 relevantes):**

| `CodigoModulo` (BD) | id | Mapeo desde Excel |
|---|---:|---|
| `BANDEJA_TAREAS` | 1 | `BANDEJA DE TAREAS` |
| `MI_BANDEJA` | 2 | `MI BANDEJA` |
| `LISTA_MAESTRA` | 3 | `LISTA MAESTRA` |
| `CONSULTAR_DOCUMENTOS` | 4 | `CONSULTAR DOCUMENTOS` ⚠️ |
| `MIS_EVALUACIONES` | 5 | `MIS EVALUACIONES` |
| `ASISTENTE_IA` | 6 | `ASISTENTE IA` |
| `NUEVA_SOLICITUD` | 7 | `NUEVA SOLICITUD` |
| `PLANTILLAS_DOCUMENTALES` | 8 | `PLANTILLAS DOCUMENTALES` ⚠️ |
| `REPORTES` | 10 | (no usado por matriz, se asigna por `visualiza_reportes=True`) |
| `PARAMETRIZACION` | 9 | (no usado, solo ADMIN) |
| `TODOS` | 11 | `TODOS` (bypass) |

---

## 3. Decisiones del import (las 5 que importan)

### D1: Tipo de carga → **CLI script standalone**

- Coincide con pivot de sesión 6. Sin endpoint nuevo, sin UI.
- Idempotente (re-correr no duplica N:M ni pisa si `--update-existing=false`).
- Argumentos: `--excel PATH [--dry-run] [--update-existing] [--verbose]`

### D2: Resolución de delegados → **SKIP con warning**

- 17/156 = 11% con nombre concreto en el Excel. Insuficiente.
- Nombres en MAYÚSCULAS en el Excel vs Title Case en BD (riesgo de fuzzy match bajo).
- **No se asigna `delegado_id` en este import.**
- **Todos los 156 no-visualizadores quedan con `estado_delegacion='pendiente'`** (alerta amarilla en UI).
- Backlog: tarea #13 (resolver delegado desde otra fuente, p.ej. AD `manager` attribute, o carga manual del admin).

### D3: ¿Crear o actualizar? → **Modo dual con default seguro**

- Default `--update-existing=false`: skip si el usuario ya tiene rol asignado (no pisa decisiones manuales).
- Con `--update-existing=true`: pisa rol, modulos, requiere_delegado, visualiza_reportes, estado_delegacion. NO toca `delegado_id` (es decisión humana, protegida).
- 2da corrida sin flag → no debería cambiar nada (idempotencia).

### D4: ¿Asignar `area_id`? → **NO**

- El Excel no tiene gerencia ni área explícita (solo `POSICION` = cargo).
- Tabla `cargos_a_areas` no existe; crearla ahora sería desviar #12.
- Quedan `area_id=NULL` para los 717 usuarios a actualizar (algunos ya tenían `area_id` previo y NO se pisa).
- Backlog: tarea #14 (seed de `cargos_a_areas` con los 194 cargos distintos).

### D5 (nueva): Dry-run obligatorio por seguridad

- Sin `--dry-run`: el script pide confirmación interactiva ("Aplicar a 717 usuarios? Escriba 'SI' para confirmar").
- Con `--dry-run`: ejecuta todo el pipeline (parser + match) pero NO hace commit. Imprime diff en consola.
- Esto evita el "lo corrí sin querer y me pisó 717 usuarios" clásico.

---

## 4. Campos que el import actualiza

Por cada usuario en BD que matchee un COFAR del Excel:

| Campo BD | Fuente Excel | Regla |
|---|---|---|
| `roles` (N:M via `usuario_roles`) | `ROL EN EL FLUJO` | match exacto `CodigoRol.codigo` |
| `modulos` (N:M via `usuario_modulos`) | `MODULOS HABILITADOS` (split `,`) | normalizar y matchear `CodigoModulo.codigo` |
| `requiere_delegado` (bool) | `¿REQUIERE DELEGADO?` == "SI" | True si rol ≠ VISUALIZADOR |
| `visualiza_reportes` (bool) | `¿VISUALIZA O EXPORTA REPORTES?` == "SI" | True si rol ≠ VISUALIZADOR |
| `estado_delegacion` (enum) | calculado | `NA` si VISUALIZADOR, `PENDIENTE` si no-visualizador (sin asignar delegado en este import) |
| `delegado_id` (FK a `usuarios.id`) | — | **NO se toca** (protegido) |

### Campos que el import NO toca (prohibidos)

- `delegado_id` — decisión humana, no automática
- `email`, `nombre_completo`, `cargo`, `area_id` — fuente de verdad es AD
- `password_hash`, `last_login_at` — datos de sesión
- `azure_oid`, `ad_postal_code`, `ad_info` — fuente de verdad es AD
- `estado` — solo sync AD lo cambia (no este import)

---

## 5. Estimaciones de output

Asumiendo default (no `--update-existing`):

| Métrica | Esperado |
|---|---:|
| Total COFARs procesados | 729 |
| Matchean en BD | 717 |
| Actualizaciones aplicadas (primera corrida) | **~717** (BD tiene 764 usuarios pero solo 717 matchean) |
| Roles asignados | 717 |
| Módulos asignados (suma N:M) | ~3.5K (≈5 modulos/usuario promedio) |
| `requiere_delegado=True` | 156 (los 2 ETO + 8 APROB + 146 ELAB) |
| `requiere_delegado=False` | 561 (los 573 VISUALIZ − 12 sin match) |
| `visualiza_reportes=True` | 156 |
| `estado_delegacion='pendiente'` (alerta UI) | 156 |
| `estado_delegacion='na'` | 561 |
| Warnings (COFAR sin match) | 12 |
| Warnings (rol no catalogado) | 0 |
| Warnings (módulo no catalogado) | 0 |
| Tiempo de ejecución estimado | < 30 s (bulk_save_objects + ON CONFLICT) |

---

## 6. Plan de sub-tareas restante (#12.2 → #12.5)

| # | Tarea | Output |
|---|---|---|
| 12.2 | `backend/app/services/matriz_import_service.py` | `parsear_excel()`, `match_usuarios()`, `aplicar_asignaciones()` con bulk + ON CONFLICT |
| 12.3 | `backend/scripts/run_matriz_import.py` | CLI argparse con `--excel --dry-run --update-existing --verbose` + confirmación interactiva |
| 12.4 | Ejecución real + dry-run previo + diff counts | Log con before/after |
| 12.5 | `pytest backend/tests/` en paralelo | 123/123 verde (sin regresión) |

---

## 7. Trampas/ensenanzas documentadas

1. **El Excel no incluye ADMIN** — el admin stub (`admin` / `cofar.2026`) NO será afectado por este import. Si querés que el admin también esté en la matriz, agregalo manualmente después.
2. **Los módulos vienen con espacio y la BD con guion_bajo** — siempre normalizar `m.replace(" ", "_")` antes del lookup.
3. **El Excel puede tener filas vacías al final** — el parser debe skipear filas con `COFAR is None`, no por conteo.
4. **El campo `MODULOS HABILITADOS` viene como string con comas** — `split(",")` + `strip()` por cada uno. NO usar `split(", ")` porque a veces hay dobles espacios.
5. **`requiere_delegado` en el Excel es 100% correlativo con rol ≠ VISUALIZADOR** — el `Rol.requiere_delegado` del modelo podría usarse como source of truth, pero por seguridad lo derivamos del Excel.
6. **Los 12 COFARs sin match** — NO se inventan usuarios. Se reportan y el admin decide si sincroniza AD después.
