# PLAN DEPLOY QAS — Sesión 18

> **Propósito:** Plan completo (sin ejecutar todavía) para desplegar la versión R1 cerrada (sesión 18 con refresh fix) en https://sgdqas.cofar.com.bo, validando que TODO funcione: código nuevo, librerías (openpyxl, tiptap, alpine, dompurify, xlsx, ldap3, etc.), datos de la BD, sync AD real, fix refresh post-refresh, impersonate, Tiptap, etc.
>
> **Diferencia clave QAS vs DES:** QAS conecta al DC en `10.10.0.2` (no al RODC `172.16.10.17` que usamos en DES), porque la VPN de COFAR no enruta al RODC desde el server QAS.
>
> **Estado actual de QAS** (inspeccionado por SSH en sesión 18):
> - 8 contenedores Up, backend healthy, 14h uptime
> - BD head alembic: `b397cd9bfb91` (010) ← **DES está en 6451593bcab5 (013), faltan 3 migraciones**
> - Falta tabla `semaforizacion_tarea` ← QAS no la tiene
> - `tipos_documento` aún tiene columna `codigo_doc` (será removida por migración 011)
> - `configuracion_global`: 0 filas ← **seed no se corrió**
> - `email_templates`: 6 (DES tiene 10, con enum expandido en migración 013)
> - Login + /me funciona con cookies HttpOnly
> - 754 usuarios sincronizados desde AD
> - `sgd-qas.conf` activo en conf.d/ (no .bk, quedó del deploy pre-sesión 14)

---

## 1. Estado actual DEL SERVIDOR QAS (lectura SSH, NO ejecución)

### 1.1 Stack Docker
```
sgd-qas-backend         Up 14h (healthy)    8000/tcp
sgd-qas-celery-beat     Up 13h (unhealthy)  8000/tcp   (no healthcheck definido, normal)
sgd-qas-celery-worker   Up 14h (unhealthy)  8000/tcp   (no healthcheck definido, normal)
sgd-qas-frontend        Up 14h              5173/tcp
sgd-qas-mailhog         Up 14h              1025/tcp, 8025/tcp
sgd-qas-nginx           Up 14h              0.0.0.0:80->80, 0.0.0.0:443->443
sgd-qas-postgres        Up 14h (healthy)
sgd-qas-redis           Up 14h (healthy)
```

### 1.2 BD (alembic head 010 `b397cd9bfb91`, **3 migraciones atrasadas**)

| Tabla | QAS count | DES count | Delta |
|---|---|---|---|
| roles | 5 | 5 | ✓ |
| modulos | 11 | 11 | ✓ |
| gerencias | 10 | 14 | +4 (DES tiene extras de pruebas) |
| areas | 50 | 56 | +6 (DES tiene extras) |
| **usuarios** | **754** | 764 | +10 (DES tiene 10 stubs extra de pruebas manuales) |
| **tipos_documento** | 13 | 14 | +1 (DES tiene 1 extra) |
| estados | 5 | 5 | ✓ |
| feriados | 20 | 23 | +3 (DES tiene 3 extras) |
| **email_templates** | **6** | **11** | **+5 (migración 013 expande enum 6→10)** |
| matriz_eto | 10 | 10 | ✓ |
| **configuracion_global** | **0** | **11** | **FALTA seed_configuracion_global.py** |
| audit_log | 1 | ~50 | 1 vs muchos (DES tiene mucha actividad) |
| **semaforizacion_tarea** | **NO EXISTE** | 4 | **Falta migración 012** |
| alembic | b397cd9bfb91 (010) | 6451593bcab5 (013) | **3 migraciones pendientes** |

### 1.3 Tablas faltantes / diferentes
- QAS NO tiene `semaforizacion_tarea` (migración 012 la crea)
- QAS `tipos_documento` aún tiene columna `codigo_doc` (migración 011 la elimina)
- QAS `email_templates.codigo` es enum con 6 valores; DES tiene 10 valores (migración 013)

### 1.4 Configuración (.env.qas)
- `ENVIRONMENT=qas`
- `LDAP_SERVER=10.10.0.2` ← DC interno, no RODC ← **CRÍTICO**
- `LDAP_BIND_USER=soporteglpi@cofar.com` (service account COFAR)
- `LDAP_ENABLED=true`
- `GRAPH_ENABLED=false` (no M365 aún, esperado)
- `SMTP_ENABLED=false` (usa MailHog interno, esperado)
- `CORS_ORIGINS=https://sgdqas.cofar.com.bo,http://localhost:5173,http://localhost:8080`
- SSL cert autofirmado vigente (365 días desde 16-jun)

### 1.5 nginx conf.d en QAS (dentro del container)
- `sgd-qas.conf` (2726 bytes, activo) ← quedó del deploy pre-sesión 14
- `sgd.conf` (2617 bytes, TAMBIÉN cargado) ← server block de DES, no debería estar en QAS (code smell preexistente)
- El archivo en repo `deploy/nginx/conf.d/sgd-qas.conf.bk` está deshabilitado en DES pero al deployarlo a QAS nginx NO lo cargaría (sufijo .bk)

### 1.6 Validación HTTP desde afuera (curl)
- `GET /api/v1/health` → 200 OK `{"status":"ok","service":"cofar-sgd-api","database":"ok"}`
- `GET /` (frontend) → 200 OK HTML Vite
- `POST /api/v1/login` con aromero local → 200 OK + cookies + user JSON ✓
- `GET /api/v1/me` con cookies → 200 OK con user completo ✓

---

## 2. Cambios desde último deploy QAS (commit 9e2dbbd, sesión 11)

22 commits, **33 archivos cambiados, 3,512 líneas añadidas, 939 removidas** (rama `epica-1/rama-1`):

### 2.1 Backend (Python)
- **3 migraciones Alembic nuevas** (críticas para QAS):
  - `6b244889632f` refactor tipos_documento: codigo int UNIQUE + slug + nombre UNIQUE, drop codigo_doc
  - `f04b96c6dff2` add semaforizacion_tarea table (4 endpoints nuevos)
  - `6451593bcab5` expand plantillas enum to 10 codes
- `app/api/v1/admin_impersonate.py` (134 cambios) — impersonate funcional
- `app/api/v1/audit_log.py` (122) — GET /api/v1/audit-log con filtros
- `app/api/v1/semaforizacion_tarea.py` (179 nuevo) — 4 endpoints
- `app/api/v1/tipos_documento.py` (67) — refactor
- `app/api/v1/usuarios.py` (9) — PATCH /{id} con rol_codigo/delegado_id
- `app/main.py` (3) — startup CORS X-CSRF-Token
- `app/models/__init__.py` (3) — registra semaforizacion_tarea
- `app/models/email_template.py` (34) — enum 10 codigos
- `app/models/semaforizacion_tarea.py` (85 nuevo)
- `app/models/tipo_documento.py` (44) — drop codigo_doc
- `app/schemas/semaforizacion_tarea.py` (50 nuevo)
- `app/schemas/tipo_documento.py` (23)
- `app/services/impersonate_service.py` (2)
- `app/scripts/seed_configuracion_global.py` (101 nuevo) ← **CRÍTICO: QAS no lo tiene**
- `app/scripts/seed_email_templates.py` (328) — 10 plantillas
- `app/scripts/seed_tipos_documento.py` (61) — refactor

### 2.2 Frontend (JS/HTML)
- `package.json` (6) — Tiptap 3.26.1 deps (5 paquetes)
- `package-lock.json` (856) — lockfile actualizado
- `src/components/PlantillaEditor.js` (60 nuevo) — wrapper Tiptap
- `src/layouts/AppLayout.js` (44) — banner impersonate sticky
- **`src/pages/DebugSession.js` (350 nuevo)** ← debug page /_debug/session
- `src/pages/Parametrizacion.js` (1373) — refactor masivo Tiptap + filtros
- **`src/router/index.js` (57)** ← **fix refresh bug #15**
- `src/services/parametrizacionApi.js` (15) — API client
- **`src/store/auth.js` (88)** ← **fix refresh bug #15 (cache + isReady)**
- `src/utils/config.js` (14) — API_BASE relativa

### 2.3 Deploy
- `deploy/docker-compose.yml` (79) — env vars con defaults
- `deploy/nginx/conf.d/{sgd-qas.conf => sgd-qas.conf.bk}` (rename)
- `deploy/nginx/conf.d/sgd.conf` (8) — rate limit burst=20→100
- `deploy/nginx/nginx.conf` (5) — rate limit zones

### 2.4 Dependencias (importante para que la imagen rebuild funcione)
- `backend/requirements/base.txt` — openpyxl==3.1.5 agregado (ya está)
- `frontend/package.json` — @tiptap/* 3.26.1 agregados (5 paquetes)
- `frontend/package-lock.json` — regenerado
- **NO hay nuevas deps de Python** (alembic, fastapi, sqlalchemy, ldap3, openpyxl ya estaban)

### 2.5 Resumen de qué hace falta en QAS
- 3 migraciones pendientes (010 → 013)
- 1 seed nuevo (configuracion_global)
- Código de: impersonate, audit_log, semaforizacion_tarea, tipos_documento refactor, plantillas 10, Tiptap, refresh fix, DebugSession
- 5 paquetes npm nuevos (Tiptap 3.26.1)
- Rebuild de imagen Docker backend + frontend (cambios en requirements + package.json)

---

## 3. PLAN DE DEPLOY (sin ejecutar)

### 3.1 PRE-FLIGHT (verificaciones previas, todas de solo lectura)

```bash
# 1. Conectividad SSH + espacio en disco
ssh sistemas@sgdqas.cofar.com.bo "df -h /opt/sgd && free -h && docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Size}}'"

# 2. Verificar .env.qas (NO TOCAR, solo leer)
ssh sistemas@sgdqas.cofar.com.bo "grep -E '^(LDAP_SERVER|LDAP_BIND|JWT_SECRET|POSTGRES_PASSWORD|CORS_ORIGINS|ENVIRONMENT)' /opt/sgd/.env.qas | sed 's/PASSWORD=.*/PASSWORD=***/; s/SECRET=.*/SECRET=***/'"

# 3. Verificar cert SSL vigente
ssh sistemas@sgdqas.cofar.com.bo "openssl x509 -in /opt/sgd/deploy/nginx/ssl/sgdqas.crt -noout -dates -subject"

# 4. Backup de BD (OBLIGATORIO antes de cualquier cambio)
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker exec sgd-qas-postgres pg_dump -U sgd -d sgd -Fc -f /tmp/qas_pre_deploy.dump && docker cp sgd-qas-postgres:/tmp/qas_pre_deploy.dump /opt/sgd/backups/qas_$(date +%Y%m%d_%H%M%S)_pre_sesion18.dump && ls -la /opt/sgd/backups/"

# 5. Backup de nginx configs actuales
ssh sistemas@sgdqas.cofar.com.bo "cp -a /opt/sgd/deploy/nginx/conf.d /tmp/conf.d.bak.$(date +%Y%m%d_%H%M%S) && cp -a /opt/sgd/deploy/nginx/nginx.conf /tmp/nginx.conf.bak.$(date +%Y%m%d_%H%M%S) && echo BACKUP_NGINX_OK"

# 6. Validar que el head de DES está 3 commits adelante de QAS
#    (lo confirmamos via git log en DES — QAS no tiene git)
#    DES head: 1186fab
#    QAS en BD: b397cd9bfb91 (010)
#    DES en BD: 6451593bcab5 (013)
```

**Criterio de Go/No-Go:**
- ✅ Disco QAS > 2 GB libres (las imágenes Docker pueden pesar 500MB c/u)
- ✅ Cert SSL vigente > 30 días
- ✅ Backup de BD exitoso y descargable
- ✅ Todos los contenedores "Up" (celery-W/B "unhealthy" es esperado, no bloqueante)

### 3.2 FIXES PRE-DEPLOY (en DES, ANTES de subir a QAS)

**FIX 1: deploy-qas.bat — rename de nginx config**

`scripts/deploy-qas.bat` línea 75: el find/delete actual borra `conf.d/` y luego extrae del zip que tiene `sgd-qas.conf.bk` (sufijo que nginx no carga). Necesito agregar rename post-extracción:

```bat
REM DespuEs de la linea de extract (linea 75) y ANTES del build:
ssh %QAS_USER%@%QAS_HOST% "cd /opt/sgd && if [ -f deploy/nginx/conf.d/sgd-qas.conf.bk ]; then mv deploy/nginx/conf.d/sgd-qas.conf.bk deploy/nginx/conf.d/sgd-qas.conf; echo RENAMED_BK_TO_CONF; fi"
```

**FIX 2: start-stack-qas.sh — verificar que seed_configuracion_global.py está en REQUIRED_FILES**

Verificar que la lista REQUIRED_FILES (líneas 99-109) ya incluye `seed_configuracion_global.py` — ya está desde sesión 12. OK.

Verificar que SEEDS array (líneas 211-220) lo incluye — ya está. OK.

**FIX 3: .env.qas en QAS — verificar LDAP_SERVER=10.10.0.2**

Ya está correcto (verificado en 1.4). OK.

**FIX 4: nueva flag para NO sobreescribir sgd.conf en QAS**

El code smell preexistente: el zip incluye `sgd.conf` (que es de DES) y se monta en `/etc/nginx/conf.d/`. En QAS, `sgd.conf` también se carga (server_name `_;` catch-all). Esto es funcional pero confuso. **Decisión:** dejarlo en esta iteración (no es bloqueante), documentar en BACKLOG.

### 3.3 DEPLOY (modificado, con los fixes)

```cmd
scripts\deploy-qas.bat
```

El script modificado automáticamente:
1. Empaqueta código local (excluyendo node_modules, .venv, etc.)
2. SCP a /tmp/sgd_deploy.zip
3. Extrae en /opt/sgd (preserva .env.qas y ssl/)
4. **FIX 1: rename sgd-qas.conf.bk → sgd-qas.conf** ← nuevo
5. Rebuild imágenes Docker (backend: pip install -r requirements/base.txt — openpyxl está; frontend: npm install — tiptap 3.26.1 está)
6. `docker compose up -d` (restart servicios, BD no se toca)
7. Espera health checks
8. Invoca start-stack-qas.sh:
   - Verifica archivos
   - Provisiona storage
   - Levanta stack
   - Espera health (postgres + backend)
   - **Aplica permisos storage (chown 1000:1000 + chmod 755/644)**
   - **Reinicia celery-beat**
   - Aplica 7+1 seeds (incluyendo seed_configuracion_global) — todos idempotentes
   - Si LDAP_ENABLED=true: corre sync_ad_oficial.py → CSV en /app/storage/
   - Resumen con conteos de BD

**Tiempo estimado:** 5-8 minutos (rebuild de imágenes backend + frontend puede tomar 2-3 min, seeds + sync AD otros 2-3 min)

### 3.4 POST-DEPLOY: Validación completa (smoke test exhaustivo)

**A. Validación de HEALTH (sin browser):**
```bash
# Health HTTPS via nginx
curl -sk -o /dev/null -w "HTTPS health: %{http_code} (%{time_total}s)\n" https://sgdqas.cofar.com.bo/api/v1/health
# Esperado: 200, < 1s

# Health via backend directo (interno)
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-backend curl -fsS http://localhost:8000/api/v1/health"
# Esperado: 200

# 8 servicios Up
ssh sistemas@sgdqas.cofar.com.bo "docker compose -f /opt/sgd/deploy/docker-compose.qas.yml --env-file /opt/sgd/.env.qas ps"
# Esperado: 8/8 servicios Up
```

**B. Validación de LIBRERÍAS nuevas (en container):**
```bash
# openpyxl (export XLSX/CSV)
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-backend python -c 'import openpyxl; print(openpyxl.__version__)'"
# Esperado: 3.1.5

# Tiptap (frontend) — via curl al container
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-frontend sh -c 'ls /app/node_modules/@tiptap | head -10'"
# Esperado: core, extension-color, extension-text-style, extension-underline, pm, starter-kit

# Alpine.js, DOMPurify, xlsx (frontend)
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-frontend sh -c 'cat /app/package.json | grep -E \"(alpinejs|dompurify|xlsx|@tiptap)\"'"
# Esperado: todas las deps presentes
```

**C. Validación de MIGRACIONES (BD):**
```bash
# Head de alembic
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c 'SELECT version_num FROM alembic_version'"
# Esperado: 6451593bcab5 (no b397cd9bfb91)

# Tabla semaforizacion_tarea creada
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c \"SELECT count(*) FROM information_schema.tables WHERE table_name='semaforizacion_tarea'\""
# Esperado: 1

# tipos_documento sin codigo_doc, con slug
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c \"SELECT count(*) FROM information_schema.columns WHERE table_name='tipos_documento' AND column_name='codigo_doc'\""
# Esperado: 0

ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c \"SELECT count(*) FROM information_schema.columns WHERE table_name='tipos_documento' AND column_name='slug'\""
# Esperado: 1
```

**D. Validación de DATOS (BD):**
```bash
# Conteos esperados post-seeds
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-postgres psql -U sgd -d sgd -tA <<'EOF'
SELECT 'roles: ' || count(*) FROM roles
UNION ALL SELECT 'modulos: ' || count(*) FROM modulos
UNION ALL SELECT 'gerencias: ' || count(*) FROM gerencias
UNION ALL SELECT 'areas: ' || count(*) FROM areas
UNION ALL SELECT 'usuarios: ' || count(*) FROM usuarios
UNION ALL SELECT 'tipos_documento: ' || count(*) FROM tipos_documento
UNION ALL SELECT 'estados: ' || count(*) FROM estados
UNION ALL SELECT 'feriados: ' || count(*) FROM feriados
UNION ALL SELECT 'email_templates: ' || count(*) FROM email_templates
UNION ALL SELECT 'matriz_eto: ' || count(*) FROM matriz_enrutamiento_eto
UNION ALL SELECT 'configuracion_global: ' || count(*) FROM configuracion_global
UNION ALL SELECT 'semaforizacion_tarea: ' || count(*) FROM semaforizacion_tarea
UNION ALL SELECT 'audit_log: ' || count(*) FROM audit_log
UNION ALL SELECT 'alembic: ' || version_num FROM alembic_version;
EOF"

# Esperado:
# roles: 5
# modulos: 11
# gerencias: 10 (QAS tiene menos que DES porque el seed matriz abril NO se ejecuta en QAS)
# areas: 50
# usuarios: 754+ (sync AD puede haber agregado)
# tipos_documento: 13
# estados: 5
# feriados: 20
# email_templates: 10 (NUEVO, antes 6, seed expande enum 6→10)
# matriz_eto: 10
# configuracion_global: 11 (NUEVO, antes 0)
# semaforizacion_tarea: 4 (NUEVO, antes tabla no existía)
# audit_log: muchos (cada refresh, login, etc genera entradas)
# alembic: 6451593bcab5
```

**E. Validación de LOGIN (BD Local + AD real):**
```bash
# Login con usuario BD Local (aromero) — modo dev/stub
curl -sk -X POST https://sgdqas.cofar.com.bo/api/v1/login \
    -H "Content-Type: application/json" \
    -d '{"username":"aromero","password":"cofar.2026","auth_source":"local"}' \
    -c /tmp/cookies_local.txt | jq '.message, .user.username'
# Esperado: "Login exitoso", "aromero"

# Login con usuario AD real (soporteglpi) — modo cofar
curl -sk -X POST https://sgdqas.cofar.com.bo/api/v1/login \
    -H "Content-Type: application/json" \
    -d '{"username":"soporteglpi","password":"<password>","auth_source":"cofar"}' \
    -c /tmp/cookies_ad.txt | jq '.message, .user.username'
# Esperado: 200 OK, "soporteglpi" (usuario sincronizado de AD)

# /me con cookies del login
curl -sk https://sgdqas.cofar.com.bo/api/v1/me -b /tmp/cookies_local.txt | jq '.authenticated, .user.username'
# Esperado: true, "aromero"
```

**F. Validación de NUEVAS FEATURES (endpoints que no existían antes):**
```bash
# Impersonate (necesita cookies de admin o ETO)
curl -sk https://sgdqas.cofar.com.bo/api/v1/admin-impersonate/list -b /tmp/cookies_local.txt | jq '.items | length'
# Esperado: > 0 (lista de usuarios impersonables)

# Audit log
curl -sk "https://sgdqas.cofar.com.bo/api/v1/audit-log?limit=5" -b /tmp/cookies_local.txt | jq '.items | length, .items[0].accion'
# Esperado: > 0 items

# Semaforizacion por tipo de tarea
curl -sk https://sgdqas.cofar.com.bo/api/v1/semaforizacion-tarea -b /tmp/cookies_local.txt | jq '.items | length'
# Esperado: 4 (REVISION, APROBACION, CONTROL_LECTURA, EVALUACION)

# PATCH /usuarios/{id} (override estado/ausente/delegacion)
curl -sk -X PATCH "https://sgdqas.cofar.com.bo/api/v1/usuarios/1" \
    -H "Content-Type: application/json" \
    -b /tmp/cookies_local.txt \
    -d '{"ausente": false}' | jq '.username, .ausente'
# Esperado: "aromero", false (200 OK)
```

**G. Validación del FIX REFRESH (smoke test en browser):**

En Chrome DevTools MCP (usar mcp__chrome-devtools):
1. Navegar a `https://sgdqas.cofar.com.bo/`
2. Login con aromero / cofar.2026 / BD Local
3. Verificar que redirige a /bandeja
4. **Hard reload (Ctrl+Shift+R) en /bandeja**
5. Verificar que la URL sigue en /bandeja (no salta a /login)
6. Inspeccionar `Alpine.store('auth').isReady` → debe ser `true`
7. Inspeccionar `Alpine.store('auth').isAuthenticated` → debe ser `true`
8. Inspeccionar `Alpine.store('auth').user.username` → debe ser "aromero"
9. Inspeccionar `localStorage.getItem('cofar_session')` → debe tener el JSON del user

**H. Validación de PLANTILLAS (Tiptap):**
1. En el browser, ir a /parametrizacion
2. Click en "Plantillas de Notificacion"
3. Verificar que se ven **11 plantillas** (no 6 — el seed expande de 6 a 10, más las que estén)
4. Click en una plantilla, verificar que el editor Tiptap carga
5. Verificar toolbar con B/I/U/S/H1-3/listas/code/blockquote/undo/redo
6. Verificar que no hay error "Applying a mismatched transaction" en consola

**I. Validación de IMPERSONATE:**
1. En /parametrizacion, buscar la columna DELEGADO o la sección de usuarios
2. Click en "Impersonar" de un usuario (como admin/eto)
3. Verificar que aparece el banner sticky de impersonate
4. Verificar que el audit_log tiene entradas con `recurso='impersonate'`

**J. Validación de SYNC AD:**
```bash
# Verificar CSV generado
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-backend ls -la /app/storage/usuarios_sap_FINAL2026.csv 2>&1; head -3 /app/storage/usuarios_sap_FINAL2026.csv 2>&1"
# Esperado: archivo existe, header + filas de usuarios COFAR

# Conteos del sync
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-backend wc -l < /app/storage/usuarios_sap_FINAL2026.csv"
# Esperado: 753+ (header + 753 usuarios aprox)
```

**K. Validación de NGINX:**
```bash
# HTTP → HTTPS redirect
curl -sk -o /dev/null -w "HTTP→HTTPS redirect: %{http_code}\n" http://sgdqas.cofar.com.bo/
# Esperado: 301

# Frontend SPA sirve HTML
curl -sk -o /dev/null -w "Frontend HTML: %{http_code}\n" https://sgdqas.cofar.com.bo/
# Esperado: 200

# API via HTTPS
curl -sk -o /dev/null -w "API via HTTPS: %{http_code}\n" https://sgdqas.cofar.com.bo/api/v1/health
# Esperado: 200

# /mailhog/ (no debe estar en QAS, es dev only)
curl -sk -o /dev/null -w "MailHog UI: %{http_code}\n" https://sgdqas.cofar.com.bo/mailhog/
# Esperado: 502 o 404 (NO debe estar accesible en QAS)

# Verificar que sgd-qas.conf está activo (no .bk) en el container
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-nginx ls -la /etc/nginx/conf.d/"
# Esperado: sgd-qas.conf y sgd.conf (ambos), NUNCA .bk
```

**L. Validación de SEGURIDAD:**
```bash
# CORS preflight
curl -sk -X OPTIONS https://sgdqas.cofar.com.bo/api/v1/login \
    -H "Origin: https://sgdqas.cofar.com.bo" \
    -H "Access-Control-Request-Method: POST" \
    -o /dev/null -w "CORS preflight: %{http_code}\n"
# Esperado: 200

# Verificar que CSRF cookie existe (no HttpOnly)
curl -sk -i https://sgdqas.cofar.com.bo/ 2>&1 | grep -i "set-cookie"
# Esperado: csrf_token=... (NO HttpOnly)
```

### 3.5 POST-DEPLOY: Reporte al usuario

Generar un resumen con tabla PASS/FAIL de todos los checks anteriores + capturas de pantalla (Chrome MCP) de:
- Pantalla de login
- Dashboard /bandeja
- Pantalla de parametrización con Tiptap
- Banner de impersonate (si se probó)
- /_debug/session mostrando isReady=true, isAuthenticated=true

---

## 4. Rollback (si algo falla)

### 4.1 Rollback de CÓDIGO
```bash
# En DES, volver al commit anterior al deploy
git checkout HEAD~1
scripts\deploy-qas.bat
git checkout -

# Si el problema fue una migración rota:
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker exec sgd-qas-backend alembic downgrade -1"
# (o -2, -3 según cuántas migraciones necesite rollback)
```

### 4.2 Rollback de BD (último recurso)
```bash
# Restaurar desde el backup pre-deploy
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker cp backups/qas_<TIMESTAMP>_pre_sesion18.dump sgd-qas-postgres:/tmp/restore.dump && docker exec sgd-qas-postgres pg_restore -U sgd -d sgd --clean --if-exists --no-owner --role=sgd /tmp/restore.dump"

# Verificar conteos
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c 'SELECT count(*) FROM usuarios'"
# Esperado: 754 (volver al estado pre-deploy)
```

### 4.3 Rollback de NGINX
```bash
# Restaurar configs
ssh sistemas@sgdqas.cofar.com.bo "cp -a /tmp/conf.d.bak.<TIMESTAMP>/* /opt/sgd/deploy/nginx/conf.d/ && cp /tmp/nginx.conf.bak.<TIMESTAMP> /opt/sgd/deploy/nginx/nginx.conf && docker restart sgd-qas-nginx"
```

---

## 5. Riesgos identificados + mitigaciones

| # | Riesgo | Severidad | Mitigación |
|---|---|---|---|
| 1 | Migración 011 (refactor tipos_documento) rompe datos existentes | 🟠 Alta | El seed actualiza los datos ANTES de dropear codigo_doc. Verificar 2 veces. Backup pre-deploy obligatorio. |
| 2 | Migración 013 (expand enum) falla porque hay datos con codigos viejos | 🟡 Media | El seed_tipos_documento.py + seed_email_templates.py ya generan los 10 codigos. Si la migración falla, downgrade -1 + restaurar backup |
| 3 | openpyxl no se instala en rebuild (dependencias del sistema) | 🟢 Baja | Ya está en base.txt desde sesión 6. Rebuild usa el mismo Dockerfile. |
| 4 | Tiptap 3.26.1 falla al instalar (peer deps, npm conflicts) | 🟡 Media | package-lock.json está commiteado. npm ci debería funcionar. Si falla, usar npm install --legacy-peer-deps |
| 5 | sgd-qas.conf.bk no se renombra → nginx sin server block → ERR_CONNECTION_REFUSED | 🟠 Alta | FIX 1 en deploy-qas.bat (rename post-extract). Backup del .conf pre-deploy. |
| 6 | Sync AD genera CSV vacio o incompleto | 🟡 Media | Validar en J.1. Si falla, QAS queda con usuarios previos (no se borra nada) |
| 7 | CORS rompe después del deploy (frontend vs backend) | 🟢 Baja | CORS_ORIGINS en .env.qas ya tiene https://sgdqas.cofar.com.bo. Verificar en L.1 |
| 8 | Refresh bug #15 sigue presente después del fix | 🟢 Baja | El fix está en repo y se deploya. Validar en G.1-G.8 con Chrome MCP |
| 9 | Los 754 usuarios en QAS se duplican después de sync AD | 🟢 Baja | sync_ad_oficial.py es idempotente (sesión 11 lo verificó) |
| 10 | celery-beat entra en loop "Permission denied" en /app/storage | 🟢 Baja | Fix de sesión 11: `-s /app/storage/celerybeat-schedule` está en docker-compose.qas.yml. start-stack-qas.sh hace chown 1000:1000 + chmod 755/644 antes de levantar. |

---

## 6. Tiempo estimado total

| Fase | Tiempo |
|---|---|
| Pre-flight (verificaciones + backup) | 5 min |
| Fix deploy-qas.bat (FIX 1) + commit | 5 min |
| Deploy + rebuild imágenes | 5-8 min |
| Migraciones automáticas (start-stack-qas.sh) | 1 min |
| Seeds (8) + sync AD | 2-3 min |
| Validación A-L completa | 15-20 min |
| Reporte final | 5 min |
| **Total** | **~40-50 min** |

---

## 7. Orden de ejecución recomendado

1. **DES**: Aplicar FIX 1 (rename de .bk en deploy-qas.bat) → commit
2. **DES**: git push (si hay remote) o backup del working tree
3. **QAS**: Pre-flight (verificaciones + backup BD)
4. **QAS**: `scripts\deploy-qas.bat` (todo automático: deploy + rebuild + start)
5. **QAS**: Validación A → B → C → D (HEALTH, libs, migraciones, datos)
6. **DES/Laptop**: Validación E (login curl) + F (endpoints nuevos)
7. **Chrome MCP**: Validación G (refresh fix) + H (Tiptap) + I (impersonate)
8. **QAS**: Validación J (sync AD) + K (nginx) + L (seguridad)
9. **Reporte final** al usuario con tabla PASS/FAIL + screenshots
10. **Si TODO PASS**: commit final con tag de release + actualizar ESTADO.md + BITACORA.md
11. **Si algún FAIL**: rollback según sección 4 + documentar

---

## 8. Lo que NO se hace en este deploy

- ❌ Cambiar a cert HTTPS válido (queda para sesión pre-PROD)
- ❌ Cambiar a NOPASSWD sudo restringido (queda para sesión pre-PROD)
- ❌ Cambiar password SSH (queda para sesión pre-PROD)
- ❌ Activar GRAPH_ENABLED (Office 365) — sigue en false
- ❌ Activar SMTP real corporativo — sigue en false (usa MailHog interno)
- ❌ Importar matriz abril (NO se ejecuta en QAS, solo en DES)
- ❌ Backups automáticos en cron (queda para sesión pre-PROD)
- ❌ Monitoring Prometheus/Grafana (queda para sesión pre-PROD)

---

## 9. Diferencias que quedarán QAS vs DES después del deploy (esperadas, NO bugs)

| Item | QAS | DES | Por qué |
|---|---|---|---|
| Gerencias | 10 | 14 | QAS solo siembra 10 (seed_data.py), DES tiene 4 extras de pruebas manuales |
| Areas | 50 | 56 | Similar a gerencias |
| Usuarios | 754 | 764 | QAS tiene 754 (4 stubs DES + 750 AD), DES tiene 10 extras de pruebas |
| Tipos doc | 13 | 14 | Similar |
| Feriados | 20 | 23 | Similar |
| audit_log | Muchos | Muchos | Continúa acumulando |

---

## 10. Anexo: archivos a cambiar en DES antes del deploy

### 10.1 `scripts/deploy-qas.bat` — agregar FIX 1

Después de la línea 75 (extract), antes de la línea 79 (rebuild):

```bat
REM ─── 3.5. Renombrar sgd-qas.conf.bk a .conf (FIX 1) ───────────
echo [3.5/6] Renombrando sgd-qas.conf.bk → .conf para nginx...
ssh %QAS_USER%@%QAS_HOST% "cd /opt/sgd && if [ -f deploy/nginx/conf.d/sgd-qas.conf.bk ]; then mv deploy/nginx/conf.d/sgd-qas.conf.bk deploy/nginx/conf.d/sgd-qas.conf; echo RENAMED_BK_TO_CONF; else echo ALREADY_CONF_OR_MISSING; fi"
echo.
```

### 10.2 Commit del fix
```bash
git add scripts/deploy-qas.bat
git commit -m "fix(deploy): rename sgd-qas.conf.bk → .conf post-extract en QAS

El archivo nginx sgd-qas.conf.bk existe en el repo con sufijo .bk para
NO ser cargado en DES (donde hay sgd.conf que es catch-all). Pero al
deployar a QAS, nginx solo carga *.conf (no *.conf.bk) → ERR_CONNECTION_REFUSED.

Fix: despues de la extraccion del zip en QAS, renombrar el archivo
.bk → .conf para que nginx lo cargue.

Validado: QAS actual tiene sgd-qas.conf (no .bk) del deploy pre-sesion 14.
Este fix previene que el proximo deploy rompa nginx."
```

### 10.3 Tag de release post-deploy exitoso
```bash
git tag -a v1.0.0-qas -m "R1 cerrado + refresh fix #15 deployed to QAS"
git log --oneline -1
```

---

## 11. Resumen ejecutivo

**Lo que se va a hacer:**
1. Fix menor en `deploy-qas.bat` (rename de nginx config)
2. Pre-flight checks + backup de BD en QAS
3. Deploy del código nuevo (22 commits desde sesión 11)
4. 3 migraciones de Alembic (010 → 013)
5. 7+1 seeds (incluyendo el faltante `seed_configuracion_global.py`)
6. Sync AD real (DC 10.10.0.2)
7. Validación exhaustiva de 12 categorías (A-L) con Chrome MCP
8. Reporte final con screenshots

**Lo que está en riesgo:** 2 issues preexistentes (sgd.conf de DES en QAS, code smell) que se documentan pero NO se arreglan en este deploy.

**Tiempo:** 40-50 minutos total.

**Criterio de éxito:** TODOS los checks A-L en PASS. Si 1 falla, rollback según sección 4.
