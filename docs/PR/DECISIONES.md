# DECISIONES — COFAR SGD (ADR-style)

> **Architecture Decision Records.** Versión resumida — los ADRs detallados originales están en `RADIOGRAFIA-TOTAL-18-06-2026.md` §10. Se conserva detalle completo de ADR-059+ (sesiones 26-28).
> **Ultima actualización:** 2026-06-18 (sesión 29).

---

## ADRs fundacionales (001-058) — Resumen ejecutivo

| ADR | Decisión | Consecuencia clave |
|-----|----------|-------------------|
| 001 | FastAPI 0.137 + SQLAlchemy 2.0 async + PostgreSQL 16 | Tipado fuerte, async nativo, OpenAPI |
| 002 | Monorepo frontend/ + backend/ | Un solo clone + pipeline |
| 003 | Docker Compose (no K8s) | Suficiente para 750 usuarios |
| 004 | LDAP stub en DES, real en QAS | Desarrollo sin esperar TI |
| 005 | Graph/365 stub en DES | No bloquea desarrollo |
| 006 | redis-py 5.2.1 (no 8.x) | Compatibilidad con Celery 5.6 |
| 007-008 | Vite 8.x + Tailwind 3.4.19 | Stack frontend actual |
| 009 | R1 antes que R2 (reordenamiento) | Parametrización operativa desde día 1 |
| 010 | 24 tablas en R1+R2 (no 7) | BD consistente desde inicio |
| 011 | Nomenclatura códigos: sigla_area-codigo_tipo-correlativo vXX | Compatibilidad legacy COFAR |
| 012 | Sync AD: botón manual + job 00:05 | Doble trigger, reasignación inmediata |
| 013 | Backend dentro de Docker con DNS corporativo | Validado en sesión 4, IP directa para AD |
| 014 | AuditLog append-only via write_audit() no-bloqueante | Atómico, queryable, JSONB flexible |
| 015 | areas.sigla UNIQUE(gerencia_id, sigla) compuesto | Permite revivir sigla en otra gerencia |
| 016 | Mapeo EXPLÍCITO de normalización de módulos | 100% predecible para Excel |
| 017 | id ASC para duplicados de ad_postal_code | 98.4% match en import masivo |
| 018 | Skip delegado con warning (no fuzzy match) | 156 usuarios quedan pendientes (#13) |
| 026 | start-stack-qas.sh como punto único de entrada QAS | Deploy 1-click, idempotente |
| 027 | Sync AD output path = /app/storage/ | Permisos correctos en container |
| 042 | JSONB para N:M en documento_flujo (tablas N:M en R3) | 4 campos JSONB, 0 tablas extra en R2 |
| 043 | Trigger obsolescencia DIFERIDO a R5 | Cálculo en Python por ahora |
| 044 | TipoSolicitud como enum (no tabla) | 0 tablas extra, validado por Pydantic |
| 045 | Separador versión: `/` (no `v`) | Código completo: CC-3-005/01 |

---

## ADR-004 a ADR-012: Ver resumen ejecutivo arriba.

---



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

## ADR-013 a ADR-058: Ver resumen ejecutivo arriba o `RADIOGRAFIA-TOTAL-18-06-2026.md` §10.

---



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

## ADR-026, 027, 042-045: Ver resumen ejecutivo arriba.

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
