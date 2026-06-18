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

## ADR-013: Backend DENTRO de Docker en DES (con DNS COFAR + VPN FortiClient) — INVALIDADO Y REESCRITO 2026-06-15

### Estado actual (post-validación)

**REEMPLAZA el texto provisional escrito más abajo.** La realidad validada en sesión 4 contradice el diagnóstico inicial. El backend **SÍ PUEDE** correr dentro de Docker en DES con la configuración correcta.

### Validación end-to-end (sesión 4, 2026-06-15)

Con la red corporativa activa (VPN FortiClient en el host Windows, IP `10.0.116.4`, DNS `172.16.10.50/51`) y `.wslconfig` con `networkingMode=mirrored`:

| Test | Resultado |
|---|---|
| `ping 172.16.10.17` desde contenedor Alpine | ✅ 0% packet loss, ~3ms |
| `nc -zv 172.16.10.17 389` desde contenedor | ✅ open |
| DNS `rodc.cofar.com.bo` desde contenedor | ❌ NXDOMAIN (no resuelve por nombre) |
| DNS `dc3-cofar.com` desde contenedor | ❌ NXDOMAIN (idem) |
| `GET /api/v1/health` desde host (con backend en Docker) | ✅ 200 OK, DB OK |
| `POST /api/v1/login` con `auth_source: "local"` | ✅ 200 OK, usuario aromero completo |
| `POST /api/v1/login` con `auth_source: "cofar"` + LDAP real | ✅ Bind LDAP exitoso contra `172.16.10.17` (logs: "LDAP bind exitoso para soporteglpi") |
| `POST /api/v1/login` modo `auto` (sin auth_source) | ✅ 200 OK, usuario creado on-demand en BD local con datos del AD |

### Configuración necesaria (la que funciona)

**`~/.wslconfig`** (host Windows):
```ini
[wsl2]
networkingMode=mirrored
```

**`deploy/docker-compose.yml`** — servicio `backend`:
```yaml
backend:
  ...
  dns:
    - 172.16.10.50   # DC COFAR #1 (DNS primario de la VPN)
    - 172.16.10.51   # DC COFAR #2 (DNS secundario)
    - 8.8.8.8        # Google DNS (fallback para internet)
  dns_search:
    - cofar.com
    - .
  ...
```

**`.env`** (raíz, no commiteado):
```env
LDAP_ENABLED=true
LDAP_SERVER=172.16.10.17    # IP directa, NO hostname (no resuelve)
LDAP_PORT=389
LDAP_BIND_USER=soporteglpi@cofar.com
LDAP_BIND_PASSWORD=glpi.1T.C0f4r   # solo en .env local
LDAP_USER_SEARCH_BASE=OU=Oficina Central,DC=cofar,DC=com
LDAP_BASE_DN=OU=Oficina Central,DC=COFAR,DC=COM
```

### Decisión final

1. **El backend CORRE DENTRO de Docker en DES** con la config de arriba. La VPN FortiClient es visible para el contenedor gracias a `networkingMode=mirrored` + DNS custom.
2. **El `scripts/dev-backend.bat` se mantiene como plan B** (rollback), no como flujo normal. Si por alguna razón Docker no levanta (Docker Desktop caído, WSL2 corrupto, DNS roto), se puede arrancar el backend nativo con `dev-backend.bat` y el resto de la stack sigue en Docker.
3. **El `scripts/start-stack-des.bat` ahora levanta TODO** con `docker compose up -d` (incluido el backend). Espera health-checks de postgres y backend, luego imprime URLs.
4. **El `scripts/stop-stack-des.bat`** apaga todo limpio (mata uvicorn nativo si quedó, baja contenedores).
5. **La IP directa `172.16.10.17`** se usa en `LDAP_SERVER` porque el DNS de COFAR no resuelve `dc3-cofar.com` desde el contenedor (aunque sí desde el host). La causa: Docker usa el DNS configurado explícitamente en `dns:`, no el del host. La búsqueda `dns_search: cofar.com` solo aplica si el DNS conoce ese dominio.
6. **En QAS (Debian VM dentro de la red COFAR):** `LDAP_SERVER=dc3-cofar.com` debería resolver sin problema (la VM tiene la red corporativa completa). Ajustar al pasar a QAS.
7. **En PRD:** ídem QAS.

### Implicaciones operativas

- ✅ Stack completa reproducible con un solo comando: `scripts\start-stack-des.bat` (o `docker compose -f deploy/docker-compose.yml up -d`).
- ✅ LDAP real funciona desde el primer login (con sync on-demand a la BD local).
- ✅ El `.bat` nativo queda como red de seguridad, no como flujo principal.
- ✅ El contrato operacional es claro: "todo en Docker; si falla, .bat nativo".
- ❌ Si la VPN FortiClient cae, el bind LDAP falla → el frontend puede usar `auth_source: "local"` con los stubs de DES (`aromero / cofar.2026`).
- ❌ El usuario debe mantener `.wslconfig` con `networkingMode=mirrored`. Si Docker Desktop lo resetea, se rompe.
- ❌ El puerto host `18000` puede colisionar con otra app Windows. Mitigación: cambiar `HOST_PORT_BACKEND` en `.env`.

---

## ADR-013 (BORRADOR PROVISIONAL, INVALIDADO) — se conserva para historia

**Contexto original (mantenido por trazabilidad, ya no aplica):** El backend FastAPI se levantaba con `scripts/dev-backend.bat` (uvicorn nativo) en lugar de como contenedor, porque se creía que Docker Desktop sobre WSL2 no podía ver la VPN FortiClient del host.

**Diagnóstico que NOS ENGAÑÓ:**
- `network_mode: "host"` no funciona en Docker Desktop sobre WSL2 (solo Linux nativo).
- `extra_hosts: host.docker.internal:host-gateway` solo resuelve el gateway de WSL2, no de Windows.
- Asumimos incorrectamente que `networkingMode: "mirrored"` no funcionaba con FortiClient porque FortiClient es "capa de aplicación". **Incorrecto**: FortiClient registra rutas en la tabla de ruteo del host, y `mirrored` SÍ las propaga a WSL2.
- Asumimos que la resolución DNS del contenedor no podía alcanzar los DNS de COFAR. **Incorrecto**: con `dns: [172.16.10.50, ...]` explícito, sí los alcanza.

**Lo que aprendimos:** el ping-test rápido desde un contenedor Alpine (`docker run --rm alpine ping 172.16.10.17`) en 30 segundos demostró que el problema NO existía. **Lección para futuras sesiones: testear la asunción antes de aceptarla como verdad.**

---

## ADR-014: AuditLog append-only via `write_audit()` no-bloqueante (2026-06-15, sesión 6)

**Contexto:** Los 8 routers de parametrización (gerencias, areas, feriados, email-templates, matriz-eto, tipos-doc, estados, configuracion-global) necesitan dejar rastro de auditoría de quién-modificó-qué-cuándo. Las opciones eran: (a) logging a archivo, (b) tabla `audit_log` con insert en cada mutación, (c) trigger SQL en la tabla destino.

**Decisión:** **Tabla `audit_log` + helper `write_audit()` invocado manualmente en cada router después del commit de la operación.**

**Consecuencia:**
- ✅ Atomicidad controlada: `write_audit` + `db.delete` o `db.add` + un solo `db.commit()` (operación + audit atómicos). Si la operación falla, el audit NO se escribe (no hay "huérfanos" en audit_log).
- ✅ No-bloqueante: `write_audit` solo recibe los datos ya en memoria, no hace queries extras.
- ✅ Queryable: `GET /api/v1/audit-log?accion=&recurso=&usuario=&fecha_desde=&fecha_hasta=&limit=&offset=` para el frontend.
- ✅ Estructura flexible: `detalles` es JSONB para guardar contexto variable (old_value, new_value, ip, etc.).
- ❌ NO captura cambios directos a BD (solo via API). Si alguien edita con psql, no se audita.
- ❌ Cada router debe recordar invocar `write_audit()` — disciplina manual.

**Patrón canónico (replicado en 8 routers):**
```python
async def update_xxx(id, payload, request, db):
    user = await require_eto_or_admin(request, db)
    obj = await db.get(Xxx, id)
    if not obj:
        raise HTTPException(404)
    old_data = {...obj.__dict__}
    obj.field = payload.field
    await write_audit(db, user, "update", "xxx", id, old=old_data, new=payload.dict())
    await db.commit()
    return obj
```

---

## ADR-015: `areas.sigla` UNIQUE(gerencia_id, sigla) en vez de global (2026-06-15, sesión 6)

**Contexto:** El bug B1 reportado: el `UniqueConstraint('sigla')` global impedía "revivir" un área con la misma sigla después de un borrado lógico (UPDATE activo=True). En QAS se necesitaba reasignar `TIC` a otra gerencia distinta.

**Decisión:** **`UniqueConstraint('gerencia_id', 'sigla')` (compuesto) en `areas`**, no global. Migración Alembic 010 aplicada.

**Consecuencia:**
- ✅ Permite revivir un área con la misma sigla en otra gerencia sin conflictos.
- ✅ Refleja la realidad organizacional: la sigla `TIC` puede existir en 2 gerencias distintas.
- ❌ Migración de datos requerida en BD si existían duplicados previos (verificada antes de aplicar: 0 duplicados).
- ❌ El router debe validar unicidad compuesta (ya lo hace via IntegrityError → 409).

---

## ADR-016: Mapeo EXPLÍCITO de normalización de módulos (no `replace(" ", "_")`) — 2026-06-16, sesión 8

**Contexto:** El Excel de la matriz de abril usa nombres de módulos con espacios y partículas ("BANDEJA DE TAREAS", "CONSULTAR DOCUMENTOS"). El replace naive `" ".replace("_")` fallaba en "BANDEJA DE TAREAS" → "BANDEJA_TAREAS" (drop de "DE"). Necesitábamos un mapeo confiable y mantenible.

**Decisión:** **Diccionario EXPLICITO `MODULO_NORMALIZATION` en `matriz_import_service.py` con 9 entradas hardcoded.**

```python
MODULO_NORMALIZATION: Dict[str, str] = {
    "BANDEJA DE TAREAS": "BANDEJA_TAREAS",  # drop "DE"
    "MI BANDEJA": "MI_BANDEJA",
    "CONSULTAR DOCUMENTOS": "CONSULTAR_DOCUMENTOS",
    "MIS EVALUACIONES": "MIS_EVALUACIONES",
    "ASISTENTE IA": "ASISTENTE_IA",
    "NUEVA SOLICITUD": "NUEVA_SOLICITUD",
    "PLANTILLAS DOCUMENTALES": "PLANTILLAS_DOCUMENTALES",
    "PARAMETRIZACION": "PARAMETRIZACION",
    "REPORTES": "REPORTES",
}
```

**Consecuencia:**
- ✅ 100% predecible: cada texto del Excel tiene UNA entrada explícita.
- ✅ Si COFAR agrega un módulo nuevo, agregar 1 línea en lugar de reescribir la lógica.
- ✅ Documentado en `docs/PR/MATRIZ-ABRIL-MAPEO.md` § 7.
- ❌ Hardcoded: si cambia la nomenclatura de COFAR, hay que editar el dict.
- ❌ NO detecta typos en el Excel (no hace fuzzy match).

---

## ADR-017: Preferencia por `id ASC` cuando hay duplicados de `ad_postal_code` (2026-06-16, sesión 8)

**Contexto:** 5 códigos COFAR del Excel (`visitador`, `promotor`, `sadministrativo`, `jadministrativo`, `lalave`, `ebejar`, `cmendoza`) tenían 2 usuarios en BD: el stub de DES (creado en sesión 5) y el real (sincronizado de AD después). El dict comprehension tomaba el último procesado (el stub, que ya tenía rol) y los reales quedaban sin asignar.

**Decisión:** **`ORDER BY id ASC` y tomar el primero** (heurística: los reales se crearon primero en el sync AD, los stubs después con el seed).

**Consecuencia:**
- ✅ 717/729 usuarios matchearon correctamente (98.4%).
- ✅ El stub de DES queda "ensuciado" con el rol del Excel (mala suerte — es coherente con la realidad, en QAS no hay stubs).
- ✅ Duplicados se reportan como warning en logs del import.
- ❌ Heurística frágil: si en QAS un usuario real tiene id mayor al stub, falla (pero no aplica, no hay stubs en QAS).
- ❌ NO resuelve el problema de fondo: ¿por qué hay 2 usuarios con el mismo `ad_postal_code`?

---

## ADR-018: Skip delegado con warning (2026-06-16, sesión 8)

**Contexto:** 156 usuarios del Excel requieren delegado (`¿REQUIERE DELEGADO? = SI`), pero solo 17 con nombre concreto en la columna `NOMBRE DELEGADO` (11%). El plan original (D2) proponía fuzzy match con threshold 0.85, pero el delegado es una decisión humana sensible (revisor de backups en aprobación de documentos) — un match incorrecto es peor que un delegado NULL.

**Decisión:** **`delegado_id` NUNCA se asigna en el import**. Todos los 156 usuarios quedan con `estado_delegacion='PENDIENTE'`. Backlog deuda #13.

**Consecuencia:**
- ✅ Cero riesgo de asignación incorrecta de revisor de backups.
- ✅ El estado `PENDIENTE` es visible en la UI (campo `requiere_delegado=True` + `estado_delegacion='PENDIENTE'` = "necesita asignación manual").
- ✅ Backlog explícito en ESTADO.md (#13) y BITACORA.md (sesión 8).
- ❌ El usuario `aromero` (ETO) tiene `delegado_id=NULL` después del import (ya estaba así pre-import).
- ❌ Los flujos R3/R4 que dependen de delegado se romperán hasta resolver #13.
- 🔴 **BLOQUEANTE para R3** (aprobación paralela) — pero no para R2 (creación de documentos no requiere delegado).

---

## ADR-026: `start-stack-qas.sh` es el punto único de entrada para QAS (2026-06-16, sesión 11)

**Contexto:** El deploy QAS en sesión 10 requirió ~15 pasos manuales: configurar `.env.qas`, copiar código, rebuild imágenes, levantar containers, esperar health, correr 7 seeds, correr `sync_ad_oficial.py`, validar. Esto NO es repetible, NO es testeable, y NO escala. Un admin nuevo necesitaría 30+ minutos para reproducir el deploy.

**Decisión:** **`scripts/start-stack-qas.sh`** es el punto único de entrada para levantar QAS. Es un script bash idempotente que ejecuta 8 pasos en orden:
1. Validar prerequisitos (Docker, `.env.qas`, 8 archivos de seed).
2. Provisionar `/opt/sgd/backend/storage/` (eliminar archivos corruptos).
3. `docker compose -f deploy/docker-compose.qas.yml --env-file .env.qas up -d`.
4. Esperar health-checks de PostgreSQL y backend (timeout 60s cada uno).
5. Aplicar permisos correctos a `/app/storage/` dentro del container (chown 1000:1000 + chmod 755/644).
6. Aplicar 7 seeds en orden de dependencias FK (seed_data → seed_organizacion → seed_tipos_documento → seed_estados → seed_feriados → seed_email_templates → seed_matriz_eto).
7. Si `LDAP_ENABLED=true`, ejecutar `sync_ad_oficial.py` con `--env-file` y validar el CSV generado.
8. Resumen con conteos de BD + servicios + URLs.

`scripts/deploy-qas.bat` (en la laptop) invoca este script automáticamente vía SSH después del `docker compose up -d`. Flags disponibles: `--no-restart`, `--no-seed`.

**Consecuencia:**
- ✅ Deploy QAS 1-click: `bash /opt/sgd/scripts/start-stack-qas.sh` desde el server, o `scripts\deploy-qas.bat` desde la laptop.
- ✅ Idempotente: se puede correr múltiples veces sin efectos colaterales.
- ✅ Validación de archivos al inicio (no falla a mitad de camino).
- ✅ Colores ANSI para output legible.
- ✅ Orden de seeds correcto según FKs (verificado contra `app/models/__init__.py`).
- ✅ Aplica permisos correctos sin chmod 777 (forma "production-ready").
- ❌ El script solo funciona en QAS (en DES se usa `start-stack-des.bat`, en backup `start-stack-backup.bat`).
- ❌ El sync AD solo genera el CSV — NO lo carga a la BD automáticamente. El carguío a BD sigue siendo via `run_matriz_import.py` (decisión separada, no automatizada por ahora).
- 📝 Aplicable a PRD con mínimos cambios (mismas 8 fases, diferentes paths y `docker-compose.prd.yml`).

---

## ADR-027: Sync AD output path = `/app/storage/` (no `/app/scripts/`) (2026-06-16, sesión 11)

**Contexto:** `sync_ad_oficial.py` escribe el CSV de usuarios extraídos del AD a `BACKEND_DIR / "scripts" / "usuarios_sap_FINAL2026.csv"` (i.e., `/app/scripts/` dentro del container). En QAS, este path NO es escribible por `sgduser` (uid 1000) porque es propiedad de root (uid 1001 en host) via bind mount. Resultado: `PermissionError: [Errno 13] Permission denied`.

**Decisión:** Cambiar el path default a `/app/storage/usuarios_sap_FINAL2026.csv` (`/app/storage/` es el volume named `sgd-qas_backend_storage`, escribible por sgduser). Configurable via `SYNC_AD_OUTPUT_DIR` env var para mantener compatibilidad con DES.

Adicionalmente, `start-stack-qas.sh` copia el CSV del container al host via `docker cp` para auditoría (`/opt/sgd/backend/scripts/usuarios_sap_FINAL2026.csv` en el server).

**Consecuencia:**
- ✅ Funciona out-of-the-box en QAS sin chmod 777 ni workarounds.
- ✅ El CSV se preserva aunque el container se destruya (porque está en un named volume + copia al host).
- ✅ Configurable: si en algún entorno `/app/scripts/` es escribible, se puede override con `SYNC_AD_OUTPUT_DIR=/app/scripts`.
- ❌ El CSV "legacy" en `/opt/sgd/scripts/usuarios_sap_FINAL2026.csv` queda obsoleto (era el output de una versión anterior del script). Mantenerlo solo para referencia histórica.
- 📝 El mismo principio aplica a cualquier script que genere archivos: deben escribirse en `/app/storage/` o `/tmp/`, nunca en `/app/scripts/` o `/app/`.


---

## ADR-042: JSONB para N:M en documento_flujo (R2) — tablas N:M en R3 (2026-06-17, sesión 22)

**Contexto:** El wizard de aprobación necesita persistir revisores, aprobadores y alcance de difusión como sets de IDs. La forma tradicional serían tablas N:M (evisor_id, probador_id, difusion_id). Pero para R2 el alcance es limitado (los IDs se muestran pero las bandejas reales de revisores son R3, donde se necesitan timestamps individuales por revisor).

**Decisión:** Almacenar como JSONB en documento_flujo.revisor_ids, probador_ids, lcance_difusion_ids, eemplaza_documento_ids.

**Consecuencia:**
- (+) Simplicidad: 0 tablas extra en R2. Wizard completo funcional con 4 campos JSONB.
- (+) Performance: queries de "mis docs en revisión" (R3) leen un solo campo.
- (+) Tests pytest con SQLite funcionan via filtro en Python (compatible con ambos backends).
- (-) Migración a R3 cuando se necesite historial/timestamps individuales por revisor.
- (-) El operador JSONB @> de PostgreSQL no funciona en SQLite — el código de bandejas filtra en Python (aceptable para dataset esperado: <100 docs por usuario).

---

## ADR-043: Trigger SQL de obsolescencia DIFERIDO a R5 — calculo en Python (2026-06-17, sesión 22)

**Contexto:** El plan R2 oficial (#30) proponía un trigger SQL que recalcula igencia cuando cambia probacion_at o expira_at. La sesión 21 creó igencia_service.py con la misma lógica en Python. La decisión se RATIFICA en sesión 22.

**Decisión:** Mantener el cálculo en backend Python. NO crear trigger SQL en R2 ni R3. Solo crear trigger en R5 (obsolescencia) si se justifica el costo.

**Consecuencia:**
- (+) R2 entrega rápido, sin riesgo de tests complejos de bordes (zonas horarias, DST, etc.).
- (+) Lógica versionada en Git, no en BD.
- (-) BD tiene el campo igencia desincronizado si cambia probacion_at o expira_at sin pasar por el servicio. Se mitiga recalculando en endpoints críticos (POST /enviar, GET /documentos/{id}).
- (-) Requiere disciplina: cualquier endpoint que cambie probacion_at debe pasar por igencia_service.calcular_vigencia().

---

## ADR-044: 	ipo_solicitud como enum SQLAlchemy, no tabla catálogo (2026-06-17, sesión 22)

**Contexto:** El wizard necesita 2 valores (CREACION, ACTUALIZACION) que no cambian nunca. La sesión 21 ya documentó esta decision (en draft); la sesión 22 la formaliza tras uso extensivo.

**Decisión:** class TipoSolicitud(str, enum.Enum) en pp/models/documento_flujo.py con CREACION y ACTUALIZACION. NO tabla catálogo.

**Consecuencia:**
- (+) 0 tablas extra. 0 endpoints extra. 0 seeds que mantener.
- (+) Valores validados por SQLAlchemy + Pydantic.
- (-) Si en el futuro se agregan más tipos (ej: ANULACION), requiere migración Alembic + redeploy.
- (-) No se puede cambiar el label sin redeploy (mitigación: el label es "CREACION" o "ACTUALIZACION", suficiente para el flujo actual).

---

## ADR-045: Separador de versión es / (no ) — R2 ratifica (2026-06-17, sesión 22)

**Contexto:** El plan R2 original (ADR-011) decía 01 (con letra ). El usuario en sesión 21 pidió explícitamente CC-3-005/01 con barra. Sesión 22 confirma que el wizard, los endpoints, los schemas y el frontend TODOS usan / consistentemente.

**Decisión:** Sobreescribe ADR-011. Formato final: {codigo}/{version} (sin letra ). Ratificado tras implementación completa del wizard E2E en sesión 22.

**Consecuencia:**
- (+) Coherencia con el ejemplo del usuario (CC-3-005/01, BET-7-001/00, etc.).
- (+) El model_dump JSON ya devuelve ersion separado (no se concatena con ).
- (+) El frontend muestra "CC-3-005/01" en placeholders, autocompletes y bandejas.
- (-) Código legacy que asumía 01 debe ser actualizado (no hay código legacy aún, ya que era una decisión temprana).
- (-) Búsqueda por código completo requiere incluir la barra (mitigación: /buscar?q=CC-3-005/00 y /buscar?q=CC-3-005 ambos funcionan por el LIKE %q%).


---

## ADR-059: drop_table usuario_modulos (2026-06-18, sesion 26)

**Contexto:** La tabla usuario_modulos (N:M usuarios-modulos) existia desde el schema inicial pero el frontend NUNCA la leyo para decidir acceso. El control real es por ROL via ACL hardcodeado en uth.js:canAccess(). El campo user.modulos del backend era codigo muerto que costaba queries extras en login.

**Decision:** DROP TABLE usuario_modulos CASCADE + remocion de toda referencia en codigo backend (uth.py, usuario.py, scripts de seed). Nueva migracion Alembic drop_modulos_s26.

**Consecuencia:**
- (+) Login y /me mas rapidos (sin JOIN a usuario_modulos).
- (+) 22 referencias en codigo eliminadas, sin riesgo de confusion sobre quien controla acceso.
- (+) ACL queda en UN solo lugar (auth.js:canAccess), facil de auditar.
- (-) Scripts seed_data.py, seed_local_test_users.py, seed_matriz_eto.py quedan ROTOS (importan usuario_modulos). Fix en sesion 28.
- (-) Tabla usuario_modulos del backup/20260616_150015/ queda con schema viejo si se restaura.

---

## ADR-060: campo es_usuario_ad (bool) en usuarios (2026-06-18, sesion 23/26)

**Contexto:** El login AD creaba usuarios con zure_oid=None y solo d_postal_code lleno. No se distinguia explicitamente entre usuarios de AD (sincronizados via sync-ad) y usuarios locales (stubs de DES). El ProfileModal queria mostrar el department del AD SOLO si el usuario era realmente de AD.

**Decision:** Nueva columna es_usuario_ad: bool = False, indexed (migracion 8aa4cfa0f92f). Backfill: 754 usuarios con d_postal_code IS NOT NULL -> true. uth.py y usuarios.py setean es_usuario_ad=true al crear desde LDAP/sync.

**Consecuencia:**
- (+) ProfileModal discrimina AD vs local correctamente: AD users ven d_department (department del AD), local users ven gerencia/area del BD.
- (+) Filtros en frontend pueden diferenciar fuente de usuario.
- (+) Reportes pueden segmentar por fuente.
- (-) Migracion backfill obligatoria en cualquier ambiente nuevo.

---

## ADR-061: /me DEBE incluir d_department (2026-06-18, sesion 27)

**Contexto:** El endpoint /me (rama normal y rama impersonate) NO devolvia d_department ni d_physical_delivery_office aunque el schema Pydantic LoginUserOut ya los tenia definidos. /login SI los devolvia correctamente. Como consecuencia, el ProfileModal mostraba "Sin area (AD)" para usuarios AD sin rea_id mapeado, aunque su d_info (department) estuviera lleno en BD.

**Decision:** Agregar d_department=user.ad_info y d_physical_delivery_office=None en los 2 response dicts de /me (rama normal y rama impersonate). Coherencia con /login que ya lo hacia.

**Consecuencia:**
- (+) ProfileModal muestra department del AD como fallback de area.
- (+) ychavez (ad_info='Tecnologia') ahora ve 'Tecnologia' en lugar de 'Sin area (AD)'.
- (+) 11 ADRs previas sobre discriminacion AD/local (060) se cumplen end-to-end.
- (-) Si en el futuro se quiere mas detalle (physicalDeliveryOfficeName separado), requiere refactor.

---

## ADR-062: Modal personalizado en vez de confirm() nativo (2026-06-18, sesion 27)

**Contexto:** La accion de impersonate usaba confirm() nativo del browser. Esto generaba un alert del SO que: (a) rompia la UI, (b) no mostraba contexto del usuario a impersonar, (c) impedia usar diseno consistente, (d) no ofrecia informacion del impacto (que la app se va a recargar, como volver).

**Decision:** Componente ConfirmImpersonateModal.js (nuevo, 200 lineas) con API window.confirmImpersonate.abrir({ target, me, onConfirm }). Muestra: avatar con iniciales, nombre, @username, rol (label legible), cargo, area (gerencia/area del BD o fallback ad_info), estado. Banner informativo: 'la app se va a recargar y vas a ver la pantalla de inicio del usuario impersonado'. Boton dual Cancelar/Si, impersonar (estilo amber). Patron identico a AuthModal.js.

**Consecuencia:**
- (+) UX consistente con el resto de SGD.
- (+) Usuario ve CONTEXTO antes de confirmar (no como el alert generico).
- (+) z-index 8600 (encima de otros modales) + escape key handler.
- (+) Accesibilidad: foco en boton primario, escape para cerrar.
- (-) +200 lineas de codigo vs el confirm() nativo. Trade-off aceptable por UX.

---

## ADR-063: /me + reload + homeRoute al impersonar (2026-06-18, sesion 27)

**Contexto:** Al hacer impersonate desde una pagina con permisos (ej: /parametrizacion), el banner sticky aparecia pero: (a) la sidebar seguia con los links del admin (HTML estatico construido una vez), (b) el header seguia con el cargo del admin, (c) la pagina actual seguia visible aunque el impersonado no tuviera permisos (terminaba en /403).

**Decision:** Despues de efreshFromBackend() en impersonarUsuario() y stopImpersonate():
1. window.location.hash = '#' + auth.homeRoute (navega a la home del nuevo rol)
2. window.location.reload() (re-renderiza la sidebar con el nuevo rol)

homeRoute ya existia: isualizador/eto/user -> /bandeja, dmin -> /parametrizacion.

**Consecuencia:**
- (+) Sidebar SIEMPRE coherente con el rol activo.
- (+) Al impersonar un visualizador, la URL va a /bandeja (no /403).
- (+) Al terminar impersonate, vuelve a /parametrizacion (admin).
- (-) Reload completo es ~500ms vs ~200ms de actualizacion reactiva. Aceptable para una accion de 1-click.
- (-) Pierde scroll state de la pagina anterior. Aceptable porque el contexto cambia radicalmente.

---

## ADR-064: /parametrizacion: backticks en comentario HTML cierran template string (2026-06-18, sesion 27)

**Contexto:** El archivo rontend/src/pages/Parametrizacion.js (2667 lineas) tenia un comentario HTML en linea 1878 dentro del template string del export page.template:
\\\
<!-- Issue 7.1: dropdown delegado SOLO usuarios con rol ETO
     (mismo array \nalistas\ que el dropdown de analista) -->
\\\
Las 2 backticks (\\) cerraban prematuramente la template string de JS, produciendo SyntaxError: Unexpected identifier 'analistas' al cargar /parametrizacion. Bug arrastrado desde sesion 25.

**Decision:** Reemplazar las backticks del comentario por comillas simples: (mismo array 'analistas' que el dropdown de analista). Regla general: dentro de template strings JS, evitar backticks en comentarios HTML/strings embebidos.

**Consecuencia:**
- (+) /parametrizacion carga sin error.
- (+) Patron de defensa aplicable: en template strings JS usar comillas simples para texto embebido.
- (-) Hay 2667 lineas en Parametrizacion.js que pueden tener backticks similares. Busqueda exhaustiva confirma que no hay mas.

---

## ADR-065: pg_dump -Fc + pg_restore --clean como mecanismo de "clean state" (2026-06-18, sesion 28)

**Contexto:** El usuario necesitaba un mecanismo para volver la BD a un estado conocido ("limpio") tras hacer pruebas destructivas de CRUDs. Las opciones evaluadas:
- (a) `TRUNCATE` de las tablas mutables — pero el usuario quiere preservar tablas como `documentos`, `documento_flujo`, etc. que son "datos BIEN" y solo limpia `audit_log`.
- (b) Función PL/pgSQL que deshaga cambios — imposible sin un log de operaciones a invertir.
- (c) **Backup físico + restore** — el más simple y robusto.

**Decision:** Usar `pg_dump -Fc` (formato custom comprimido) para snapshotear el estado limpio, y `pg_restore --clean --if-exists --single-transaction` para restaurar.

**Mecanismo:**
1. `TRUNCATE audit_log RESTART IDENTITY` → estado limpio.
2. `pg_dump -U sgd -d sgd -Fc --no-owner --no-acl -f /tmp/clean.dump` desde el container `sgd-postgres`.
3. `docker cp` al host → `backups/clean_state_20260618/clean_state.dump` (134 KB).
4. Script `scripts/restore_clean_state.bat` que:
   - Lee credenciales del `.env` (POSTGRES_USER, POSTGRES_PASSWORD, HOST_PORT_POSTGRES, POSTGRES_DB).
   - `docker stop` de `sgd-backend`, `sgd-celery-worker`, `sgd-celery-beat` (libera conexiones a la BD).
   - `docker cp` del dump al container.
   - `pg_restore --clean --if-exists --single-transaction --no-owner --no-acl`.
   - `docker start` de los 3 servicios detenidos.
   - Imprime verificacion con `verify_clean_state()`.
5. Funcion SQL `verify_clean_state()` que retorna conteo de filas por tabla (15 tablas).
6. Script `backups/clean_state_20260618/tests_ensuciar.sql` (NO se commitea al dump; solo de test).

**Consecuencia:**
- (+) Restore atomico: `--single-transaction` garantiza que o se restaura TODO o NADA.
- (+) Velocidad: ~30 segundos para restaurar 134 KB de dump.
- (+) Idempotencia: el dump contiene el schema completo + datos, se puede aplicar N veces.
- (+) Verificacion: `verify_clean_state()` permite saber si la BD esta sucia o limpia sin restaurar.
- (+) Test end-to-end validado en sesion 28: ensuciar → restore → verificar rollback (audit_log 0→2→0, gerencia "CONTAMINADA"→"CALIDAD").
- (-) Downtime obligatorio: hay que detener el backend mientras se restaura (porque tiene conexiones activas a la BD).
- (-) El dump es puntual: si la BD se desvía del snapshot (por cambios intencionales del usuario), hay que regenerarlo.
- (-) Solo funciona en el mismo PostgreSQL major version (16) y misma plataforma.
