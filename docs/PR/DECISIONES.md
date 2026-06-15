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

---

## ADR-013: Backend fuera de Docker en DES (2026-06-15)

**Contexto:** El backend FastAPI se levanta con `scripts/dev-backend.bat` (uvicorn nativo en Windows) en lugar de como contenedor en el stack Docker Compose. Esto rompe el principio de "toda la stack en compose" que defendimos en ADR-003. Se intentó diagnosticar y resolver en varias sesiones, sin éxito. La raíz del problema es la **VPN FortiClient** que usa COFAR para acceder a su intranet.

**Diagnóstico del problema (verificado):**
- FortiClient VPN corre como aplicación en el host Windows (no como servicio de red).
- Cuando se activa, crea una interfaz de red virtual y rutea el tráfico corporativo (incluyendo `rodc.cofar.com.bo` y `dc3-cofar` = 172.16.10.17).
- Docker Desktop sobre WSL2 crea una VM Linux aislada con su propio stack de red. Las interfaces de red del host Windows (incluida la de FortiClient) **no son visibles** dentro de los contenedores Docker por defecto.
- Opciones evaluadas y descartadas:
  - `network_mode: "host"` en Docker Compose: solo aplica a Docker Engine sobre Linux nativo, **no a Docker Desktop sobre WSL2**. No funciona.
  - `extra_hosts: ["host.docker.internal:host-gateway"]`: hace que el contenedor pueda resolver `host.docker.internal` al gateway del host, pero ese gateway es WSL2, no Windows. La VPN sigue sin ser visible.
  - `networkingMode: "mirrored"` en Docker Desktop: en teoría comparte la red del host, pero FortiClient está en la capa de aplicación y enruta por nombre de proceso, no por interfaz. No resuelve el caso.
  - Mover el backend a WSL2 directamente: WSL2 tampoco ve la VPN porque está en la capa de Windows.
- Conclusión técnica: **no es viable** correr el backend dentro de Docker en DES mientras la VPN FortiClient esté activa y el backend necesite llegar al RODC.

**Decisión:**
1. **En DES (Windows 10 + FortiClient VPN):** el backend corre nativo con `scripts/dev-backend.bat` (uvicorn). El resto de la stack (postgres, redis, mailhog, nginx, frontend, celery) sí corre en Docker. La conectividad nativa ↔ Docker se hace vía `127.0.0.1:25432` (postgres) y `127.0.0.1:26379` (redis), que son los puertos host mapeados en `.env`.
2. **En QAS (VM Debian dentro de la red COFAR):** la VPN no es un problema porque la VM ya está en la red corporativa. Todo el stack corre en Docker, incluyendo el backend. Se usa el `docker-compose.prod.yml` o el mismo `.yml` de DES sin cambios.
3. **En PRD (servidor de producción):** ídem QAS.
4. **Punto único de entrada:** se crea `scripts/start-stack-des.bat` (orquestador) que en una sola acción: (a) verifica que el `.env` existe y tiene `LDAP_ENABLED` coherente, (b) hace `docker compose up -d` para los 7 servicios de Docker, (c) activa el venv de Python, (d) lanza uvicorn nativo. El orquestador documenta el contrato de "cómo arrancar el proyecto" sin tener que recordar 2 comandos separados.
5. **No se intenta más** meter el backend a Docker en DES. Es deuda técnica aceptada y documentada.

**Implicaciones operativas:**
- El backend en DES tiene acceso directo a la VPN → puede hacer bind LDAP real cuando `LDAP_ENABLED=true`.
- El backend en DES NO está aislado en un contenedor → tiene acceso al filesystem completo de Windows. Mitigación: solo el dev de confianza lo corre, y `.env` ya está en `.gitignore`.
- Los logs del backend nativo van a `backend.out` y `backend.err` (ya en `.gitignore`). El orquestador puede redirigirlos a un directorio `logs/` versionado-solo-local.
- Las migraciones Alembic se deben aplicar DOS veces si los modelos cambian: (a) `alembic upgrade head` desde el venv nativo para que la BD se actualice, (b) `alembic upgrade head` dentro del contenedor del backend cuando se rebuildee la imagen Docker. Para evitarlo, **la migración se corre solo en el venv nativo** y la imagen Docker no incluye el comando `alembic` (lo saca para que sea responsabilidad del orquestador).

**Consecuencia:**
- ✅ El dev puede trabajar con LDAP real (validación contra `dc3-cofar`) sin pelearse con Docker.
- ✅ El resto de la stack sigue siendo "infraestructura como código" via Docker Compose.
- ✅ El contrato operacional es claro: un solo script arranca todo (`start-stack-des.bat`).
- ✅ QAS y PRD no sufren esta limitación, así que el resto del diseño (todo-en-Docker) sigue siendo válido.
- ❌ El backend en DES NO es reproducible por terceros sin el script `start-stack-des.bat` y el `.env` correcto. Aceptable: es DES, no se distribuye.
- ❌ Si en el futuro COFAR cambia FortiClient por otra VPN o sale del entorno corporativo, hay que re-evaluar.
- ❌ El backend nativo ocupa un puerto de Windows (18000) que podría colisionar con otra app. Mitigación: configurado en `.env` con `HOST_PORT_BACKEND`.
