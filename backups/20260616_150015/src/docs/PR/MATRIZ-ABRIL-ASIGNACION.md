# Asignación masiva de roles/módulos desde matriz de ABRIL

> **Fecha:** 2026-06-15 (sesión 4)
> **Fuente:** `docs/Diagramas_Matrices/MATRICES/USUARIOS EXISTENTES A ABRIL.xlsx` (hoja "LISTA PERSONAL", 730 usuarios)
> **Objetivo:** Cargar los roles, módulos y delegaciones de los 730 usuarios a la BD local del SGD, basándose en la matriz de Abril que el cliente validó.

---

## 📊 Resumen de la matriz

| Métrica | Valor |
|---|---|
| Total usuarios | **730** |
| Roles definidos | **5** (VISUALIZADOR, ELABORADOR-REVISOR, ELABORADOR-REVISOR-APROBADOR, ETO, ADMIN) |
| Módulos definidos | **10** (BANDEJA, MI BANDEJA, LISTA MAESTRA, CONSULTAR DOC, MIS EVAL, PLANTILLAS, NUEVA SOL, ASISTENTE IA, TODOS, PARAMETRIZACION) |
| Requieren delegado | **156** (correlaciona 100% con rol ≠ VISUALIZADOR) |
| Visualizan reportes | **157** (correlaciona 100% con rol ≠ VISUALIZADOR) |
| Gerencia/Área en la matriz | ❌ No incluida (hay que derivarla de POSICION o de un mapeo externo) |

### Distribución por rol
```
VISUALIZADOR (CL-EVAL)             573  (78.5%)
ELABORADOR - REVISOR               146  (20.0%)
ELABORADOR - REVISOR - APROBADOR     8  ( 1.1%)
ETO                                  2  ( 0.3%)
ADMIN                                1  ( 0.1%)
```

---

## 🔑 Mapeo crítico (cómo hacemos el JOIN con la BD)

La matriz NO tiene `sAMAccountName` directamente. Pero **el `COFAR` del Excel = el `postalCode` del AD = `ad_postal_code` en la tabla `usuarios`**.

```
Excel.USUARIOS_EXISTENTES.cofar  ←→  AD.postalCode  ←→  BD.usuarios.ad_postal_code
       (8 dígitos, ej: 10001607)         (8 dígitos)              (8 dígitos)
```

**Por lo tanto:** el algoritmo de carga es:

```python
for row in matriz:
    cofar = row["COFAR"]                          # 10001607
    rol = row["ROL EN EL FLUJO"]                  # "ETO"
    modulos = parsear(row["MODULOS HABILITADOS"])  # ["MI BANDEJA", "LISTA MAESTRA", ...]
    requiere_delegado = row["¿REQUIERE DELEGADO?"] == "SI"
    nombre_delegado = row["NOMBRE DELEGADO"]

    # 1. Buscar usuario en BD por ad_postal_code
    usuario = db.query(Usuario).filter_by(ad_postal_code=cofar).first()
    if not usuario:
        log_warning(f"COFAR {cofar} no encontrado en BD")
        continue

    # 2. Asignar rol
    rol_obj = db.query(Rol).filter_by(nombre=normalizar(rol)).first()
    usuario.roles = [rol_obj]

    # 3. Asignar módulos
    modulos_obj = db.query(Modulo).filter(Modulo.nombre.in_(modulos)).all()
    usuario.modulos = modulos_obj

    # 4. Asignar delegado si requiere
    if requiere_delegado and nombre_delegado:
        # Resolver el nombre del delegado a un COFAR
        # (la matriz tiene "NOMBRE DELEGADO" como texto libre, no ID)
        delegado = buscar_delegado_por_nombre(nombre_delegado)
        if delegado:
            usuario.delegado_id = delegado.id
```

---

## 📋 Plan de implementación (sub-tareas de la tarea #12)

| Sub | Tarea | Tiempo | Dependencias |
|---|---|---|---|
| 12.1 | **Cargar el Excel de Abril como seed de Python** (`backend/scripts/seed_matriz_abril.py`) | 30 min | — |
| 12.2 | **Endpoint `POST /api/v1/admin/asignar-roles-desde-matriz`** que ejecuta la carga | 45 min | 12.1 |
| 12.3 | **Función de resolución de delegados** (texto libre → usuario en BD) | 30 min | 12.1 |
| 12.4 | **Endpoint `GET /api/v1/admin/preview-asignacion`** que muestra diff (qué se asignaría, sin aplicar) | 30 min | 12.1 |
| 12.5 | **UI: botón "Asignar Roles desde Matriz" en Parametrizacion > Gestión de Usuarios** | 45 min | 12.4 |
| 12.6 | **Reporte de diff**: cuántos usuarios asignados, cuántos sin match, cuántos con errores | 30 min | 12.2 |
| 12.7 | **Tests pytest** de la carga completa (con Excel de prueba) | 45 min | 12.2 |

**Tiempo total tarea #12:** ~4-5 horas.

---

## ⚠️ Decisiones críticas a tomar

### D1: ¿Cómo se carga el Excel? (3 opciones)

| Opción | Pro | Contra |
|---|---|---|
| **A. Script standalone** (como `sync_ad_oficial.py`) | Simple, testeable, idempotente | Hay que correrlo fuera del flujo normal |
| **B. Endpoint POST** con upload del Excel | Operable desde la UI (botón "Cargar matriz") | Más código, riesgo de XLSX malformado |
| **C. Seed Alembic** (lee el Excel al hacer `alembic upgrade`) | Idempotente, reproducible | Acopla migraciones con datos, no ideal |

**Mi recomendación:** A + B. El script standalone para el primer load (rápido, seguro), y el endpoint para recargas futuras desde la UI.

### D2: Resolución de delegados (texto libre → usuario)

La columna `NOMBRE DELEGADO` es texto libre (ej: "ROMERO PLATA, ARACELY CAROL"). Hay 156 usuarios que requieren delegado. Opciones:

| Opción | Pro | Contra |
|---|---|---|
| **A. Búsqueda exacta por `nombre_completo`** | Simple | Falla con typos, abreviaciones |
| **B. Búsqueda fuzzy** (difflib.SequenceMatcher o similar) | Tolera typos | Más lento, falsos positivos |
| **C. Match por código COFAR** (vincular primero `COFAR <-> usuario` y después `COFAR delegado <-> usuario`) | Robusto | Requiere que la matriz tenga el COFAR del delegado (no lo tiene) |

**Mi recomendación:** B con threshold de similitud ≥ 0.85. Si no matchea, dejar el delegado en NULL y mostrar warning. El admin puede corregir manualmente después.

### D3: ¿Actualiza o solo crea?

| Opción | Pro | Contra |
|---|---|---|
| **A. Solo crea** (skip si ya tiene rol) | Seguro, no pisa decisiones manuales | Si la matriz cambia, no se refleja |
| **B. Sobrescribe siempre** | La matriz es la fuente de verdad | Pisa correcciones manuales del admin |
| **C. Modo dual** (--update-existing, default false) | Flexible | Más código |

**Mi recomendación:** C con default `--update-existing=false`. El admin decide explícitamente.

### D4: ¿Gerencia/Área de la matriz?

La matriz NO tiene gerencia/área explícita. Solo `POSICION` (cargo). Para asignar `area_id`:

| Opción | Pro | Contra |
|---|---|---|
| **A. Mapeo hardcodeado por cargo** (VISITADOR MÉDICO → gerencia COMERCIAL) | Simple | Acopla código con datos |
| **B. Tabla nueva `cargos_a_areas`** en BD | Mantenible, actualizable | Una tabla más |
| **C. No asignar área** (queda NULL) | Cero código | El sistema no sabe a qué área pertenece el usuario |

**Mi recomendación:** B. Crear tabla `cargos_a_areas` con un seed inicial basado en las 194 cargos distintos. Actualizable vía UI después.

---

## 🧪 Datos para tests (muestra del Excel)

Los 15 usuarios de muestra tienen esta distribución:

| Rol | Cantidad en muestra | Módulos típicos |
|---|---|---|
| VISUALIZADOR (CL-EVAL) | 3 | BANDEJA, LISTA MAESTRA, MIS EVAL, ASISTENTE IA |
| ELABORADOR - REVISOR | 5 | MI BANDEJA, LISTA MAESTRA, CONSULTAR DOC, MIS EVAL, PLANTILLAS, NUEVA SOL, ASIST IA |
| ELABORADOR - REVISOR - APROBADOR | 3 | (mismo que ELABORADOR) |
| ETO | 2 | TODOS (bypass) |
| ADMIN | 1 | PARAMETRIZACIÓN GENERAL |

**Pares de delegación recíprocos identificados:**
- ESPINOZA PAREDES CECILIA ↔ ROMERO PLATA ARACELY (Eto Aracely)
- (probablemente más — detectar automáticamente con un script)

---

## 📋 Riesgos y mitigaciones

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | El `COFAR` del Excel no matchea con el `ad_postal_code` de la BD (algunos usuarios no sincronizados) | Reporte de diff + log de warnings. El admin puede sincronizar manualmente con sync-ad. |
| 2 | El nombre del delegado no se puede resolver (typos, mayúsculas, abreviaciones) | Búsqueda fuzzy con threshold. Warning en log. El admin corrige después. |
| 3 | El Excel se actualiza en el futuro (no es estática la fuente de verdad) | Modo `--update-existing` opt-in. El admin decide qué versión es la buena. |
| 4 | Conflictos con asignaciones manuales previas | Antes de aplicar, hacer `GET /preview` que muestra el diff. El admin confirma. |
| 5 | Carga masiva tarda mucho (730 usuarios con N:M) | Usar `db.bulk_save_objects` o `INSERT ... ON CONFLICT DO NOTHING` para velocidad. |

---

## 🎯 Resultado esperado al cerrar tarea #12

Después de ejecutar la carga, la pantalla de **Parametrización > Gestión de Usuarios** debe mostrar:

- **753 usuarios** en la BD (730 de la matriz + 23 del AD sin matchear + 10 locales)
- De los 730 de la matriz, **~700 con rol asignado**, **~30 con warnings** (no matchearon)
- De los 156 que requieren delegado, **~140 con delegado asignado**, **~16 con warning** (nombre no resuelto)
- Los 2 ETO (Aracely y Cecilia) con módulo `TODOS` y sus delegaciones cruzadas
- El ADMIN (1) con módulo `PARAMETRIZACIÓN GENERAL`

Y en el UI se ve claramente el warning amarillo "Sin codigo SAP" para los 44 usuarios del AD sin postalCode, vs los usuarios de la matriz que SÍ tienen rol asignado.
