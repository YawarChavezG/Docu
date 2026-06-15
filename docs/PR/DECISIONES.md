# DECISIONES — COFAR SGD (ADR-style)

> **Architecture Decision Records**. Cada decisión importante del proyecto se documenta aquí con el formato:
> - **Contexto:** por qué hubo que decidir.
> - **Decisión:** qué se eligió.
> - **Consecuencia:** qué implica.

---

## ADR-001: Stack FastAPI + PostgreSQL (2026-06-14)

**Contexto:** Necesitábamos elegir el stack del backend. Las opciones eran Node/Express, Django, FastAPI, NestJS, Spring Boot.

**Decisión:** **FastAPI 0.137 + SQLAlchemy 2.0 async + PostgreSQL 16**.

**Consecuencia:**
- ✅ Tipado fuerte en Python con Pydantic 2.
- ✅ Async nativo (importante para 750 usuarios).
- ✅ OpenAPI auto-generado (frontend puede consumir el spec).
- ✅ Ecosistema rico (langchain, sentence-transformers para IA futura).
- ❌ Python es más lento que Go/Node para CPU-bound, pero nuestra carga es I/O.
- ❌ Curva de aprendizaje si el equipo no conoce Python async.

---

## ADR-002: Monorepo con frontend/ y backend/ separados (2026-06-14)

**Contexto:** Había dos opciones: monorepo único, o repos separados.

**Decisión:** **Monorepo único con `frontend/` y `backend/` como carpetas separadas**.

**Consecuencia:**
- ✅ Un solo `git clone` para todo el equipo.
- ✅ CI/CD más simple (un solo pipeline).
- ✅ Coordinación de cambios cross-stack más fácil.
- ❌ Para escalar a múltiples equipos, habría que separar.

---

## ADR-003: Docker Compose en lugar de Kubernetes (2026-06-14)

**Contexto:** 750 usuarios en 1 servidor Debian. ¿K8s o Compose?

**Decisión:** **Docker Compose con stack completa en un solo servidor**.

**Consecuencia:**
- ✅ Mucho menos overhead operacional.
- ✅ El cliente no necesita aprender K8s.
- ✅ Suficiente para 750 usuarios con un backend de 4 workers.
- ❌ Si crece, migrar a K8s es un trabajo de 2-3 semanas.
- ❌ Sin auto-scaling horizontal nativo.

---

## ADR-004: LDAP stub en DES, real en QAS (2026-06-14)

**Contexto:** El cliente tiene AD pero no nos ha dado credenciales aún. ¿Construimos contra AD desde el día 1 o stub?

**Decisión:** **DES con stub de 4 usuarios hardcoded; QAS con bind real a AD vía ldap3**.

**Consecuencia:**
- ✅ Podemos desarrollar sin esperar a TI.
- ✅ El switch de DES a QAS es solo cambiar 3 variables de entorno.
- ❌ El stub no prueba el caso real de AD (grupos, kerberos, etc.).
- ❌ Si el AD tiene schema distinto, hay código de adapter a reescribir.

---

## ADR-005: Office 365 / Graph como stub en DES (2026-06-14)

**Contexto:** No hay tenant de Microsoft 365 asignado. No podemos probar edición en línea real.

**Decisión:** **DES con `GRAPH_ENABLED=false` y stub que descarga localmente el archivo. QAS con `GRAPH_ENABLED=true` y permisos delegados.**

**Consecuencia:**
- ✅ Desarrollo no se bloquea.
- ✅ El frontend tiene un placeholder que muestra "Edición en línea (próximamente)".
- ❌ Hasta QAS no probamos la integración real.

---

## ADR-006: redis-py 5.2.1 (no 8.x) por compat con Celery 5.6 (2026-06-14)

**Contexto:** PyPI muestra redis-py 8.0 como última, pero Celery 5.6 aún no la soporta oficialmente.

**Decisión:** **Fijar redis-py 5.2.1 hasta que Celery 5.7+ salga con soporte oficial de redis-py 8.x.**

**Consecuencia:**
- ✅ Builds reproducibles sin sorpresas.
- ❌ Upgrade de redis-py requiere upgrade de Celery (lo cual we'll do en QAS).

---

## ADR-007: Vite 8.x (no 6.x) — confirmado 2026-06-14 (2026-06-14)

**Contexto:** El package.json original tenía `vite: ^8.0.10` que parecia version imaginaria. Verificado contra npm: vite 8.0.16 es la última estable.

**Decisión:** **Mantener Vite 8.0.16** (lo que el original del equipo había intentado usar).

**Consecuencia:**
- ✅ Última versión con HMR rápido.
- ✅ Soporta plugins modernos.
- ❌ Algunos plugins de Vite aún no compatibles con v8 (no aplica en nuestro caso).

---

## ADR-008: Tailwind 3.4.19 (no 4.x) (2026-06-14)

**Contexto:** Tailwind 4.x salió pero cambió la API: ahora es CSS-first con `@theme`, ya no usa `tailwind.config.js` con `module.exports`.

**Decisión:** **Tailwind 3.4.19** (la que el proyecto ya tiene).

**Consecuencia:**
- ✅ El `tailwind.config.js` actual sigue funcionando.
- ✅ No hay que reescribir nada.
- ❌ Nos quedamos sin las novedades de v4 (mejor tree-shaking).
- 📝 Migrar a v4 será un worktree separado post-R2.

---

## ADR-009: R1 antes que R2 en R3 del Gantt original (2026-06-14)

**Contexto:** El Gantt original ponía la Épica 9 (Parametrización) al final. Pero la R1 la necesita.

**Decisión:** **Reordenar: Parametrización va en R1, no al final.**

**Consecuencia:**
- ✅ R1 ya tiene Parametrización operativa desde día 1.
- ✅ El SLA cron se puede probar desde R1.
- ❌ El equipo de TI no se "aburre" al final.

---

## ADR-010: 24 tablas en R1+R2 (no 7 como Gemini/Antigravity) (2026-06-14)

**Contexto:** El plan de Gemini proponía 7 tablas en el DDL inicial. Pero si el backend es la única fuente de verdad desde día 1, necesitamos las 24 (incluyendo audit_log, configuracion_global, email_templates, etc.).

**Decisión:** **Migrar las 24 tablas en R1+R2, no las 7 de Gemini.**

**Consecuencia:**
- ✅ Backend consistente desde día 1.
- ✅ No hay que rehacer migraciones.
- ❌ Migración inicial más larga (~2-3 horas).

---

## ADR-011: Nomenclatura de códigos = sigla_area + codigo_tipo + correlativo (2026-06-14)

**Contexto:** El sistema legacy de COFAR usaba códigos como `CC-5-001` donde:
- `CC` = sigla del **área** (Control de Calidad)
- `5` = código numérico del **tipo de documento** (PROCEDIMIENTO)
- `001` = correlativo secuencial dentro de (área, tipo)
- `v01` = versión de 2 dígitos

La US-2.02 del nuevo sistema sugería `PRO-CAL-001` (sigla del tipo + sigla del área + número), pero el cliente confirmó en sesión 2 que la nomenclatura **se mantiene idéntica al legacy** para no tener que renombrar masivamente los documentos antiguos.

**Decisión:** Mantener nomenclatura legacy: `{sigla_area}-{codigo_tipo}-{correlativo_3_digitos} v{version_2_digitos}`.

Ejemplo: `CC-5-001 v01`, `PRO-9-001 v00` (PRO = Producción, 9 = Protocolo, v00 = creación).

**Consecuencia:**
- ✅ Compatibilidad con sistema legacy de COFAR.
- ✅ Coincide con la nomenclatura de los archivos Excel de matrices.
- ✅ Búsquedas de usuarios por código funcionan intuitivamente.
- ❌ El correlativo es por (área, código_numérico), no por sigla del tipo. Más campos en `codigo_contador`.
- ❌ La tabla `tipos_documento` tiene `codigo` (INT) y `sigla_legacy` (string) separados. La sigla NO se usa para correlativos, solo para display/export.
- 📝 CC-1 (Metodología) y CC-7 (Especificación) tienen `max_descargas_dia = 10` por la US-2.01.

---

## ADR-012: Sync AD vía botón manual + job diario a las 00:05 (2026-06-14)

**Contexto:** El sistema debe sincronizar usuarios desde Active Directory para detectar altas, bajas, y cambios de cargo/área. Pero el cliente no especificó el mecanismo.

**Decisión:**
1. **Botón manual** en la pantalla `Parametrización > Usuarios` con etiqueta "Sincronizar AD".
2. **Job diario automático** vía Celery Beat a las **00:05 hrs** (antes del job de SLA a las 23:59, para que la reasignación por desvinculación del día siguiente use la data más fresca).

**Lógica del sync:**
- Por cada usuario en `usuarios`, comparar con su entrada en AD.
- Si el usuario en AD no existe o `userAccountControl` tiene `ACCOUNTDISABLE` → marcar `estado='desvinculado'`.
- Si el usuario existe en AD pero no en SGD → insertar como `rol='visualizador'`, `estado='activo'`, `requiere_delegado=false` (los visualizadores no requieren delegado).
- Actualizar: `email`, `nombre_completo`, `cargo`, `area` (resolución de área vía `memberOf` o un mapeo manual de `OU → area_id`).
- NO tocar: `rol`, `modulos_habilitados`, `delegado_id`, `ausente`. Esos son exclusivos de SGD.
- Disparar reasignación inmediata si tenía tareas pendientes.

**Credenciales del service account (DES):**
- `LDAP_USER=soporteglpi@cofar.com`
- `LDAP_PASSWORD=glpi.1T.C0f4r` (en `.env`, NO en repo)
- `LDAP_SERVER=rodc.cofar.com.bo` (RODC = read-only domain controller)
- `LDAP_DOMAIN=cofar.com`

⚠️ **Importante:** `rodc.cofar.com.bo` es un RODC, lo que significa que la cuenta de servicio tiene permisos limitados. Solo lectura. Suficiente para bind + enumerar usuarios, pero no para escribir.

**Consecuencia:**
- ✅ Doble trigger: manual (admin puede forzar) + automático (no se olvida).
- ✅ Reasignación inmediata cuando hay desvinculación.
- ✅ La password no se commitea al repo (`.env` en `.gitignore`).
- ❌ Si el RODC cae, el sync falla. Mitigación: log a `log_sincronizacion_ad` con error y notificación al admin.
- ❌ El mapeo `OU → area_id` requiere configuración manual o un mapeo hardcoded inicial.
