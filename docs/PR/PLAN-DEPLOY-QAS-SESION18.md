# PLAN DEPLOY QAS — Versión consolidada (sesiones 18-20)

> **Propósito:** Plan completo, ejecutable y verificado, para desplegar el código R1+R1-fixes en `https://sgdqas.cofar.com.bo`. Incluye los bugs descubiertos durante el deploy de sesión 19 y los fixes preventivos aplicados en sesión 20.
>
> **Diferencias QAS vs DES:**
> - QAS conecta al DC `10.10.0.2` (no al RODC `172.16.10.17` que usa DES).
> - QAS usa HTTPS con cert autofirmado.
> - QAS NO importa la matriz abril (solo en DES).
> - QAS ejecuta 8 seeds (incluido `seed_configuracion_global.py`).
>
> **URL post-deploy:** https://sgdqas.cofar.com.bo
>
> **Tiempo total estimado:** 60-75 min (incluyendo 3 fixes preventivos de sesión 20).

---

## 0. TABLA DE CONTENIDOS

1. [Pre-requisitos](#1-pre-requisitos)
2. [Bugs conocidos con fix aplicado en sesión 20](#2-bugs-conocidos-con-fix-aplicado)
3. [Estado actual del servidor QAS](#3-estado-actual-del-servidor-qas)
4. [Cambios desde último deploy QAS](#4-cambios-desde-último-deploy-qas)
5. [Plan de deploy paso a paso](#5-plan-de-deploy-paso-a-paso)
6. [Validaciones A-L (12 categorías)](#6-validaciones-a-l)
7. [Comandos de troubleshooting](#7-comandos-de-troubleshooting)
8. [Escenarios especiales](#8-escenarios-especiales)
9. [Rollback](#9-rollback)
10. [Riesgos identificados](#10-riesgos-identificados)
11. [Diferencias QAS vs DES esperadas](#11-diferencias-qas-vs-des)
12. [Backlog pre-PROD](#12-backlog-pre-prod)
13. [Resumen ejecutivo](#13-resumen-ejecutivo)

---

## 1. PRE-REQUISITOS

Antes de empezar, verificar que TODO esté listo:

| # | Requisito | Comando de verificación |
|---|---|---|
| 1 | Docker Desktop corriendo local | `docker info` |
| 2 | Stack DES local Up (no bloqueante) | `docker ps --filter "name=sgd-"` (debería mostrar 8 contenedores DES + 8 backup) |
| 3 | SSH key instalada para QAS | `ssh -o BatchMode=yes sistemas@sgdqas.cofar.com.bo "echo OK"` debe responder `OK` |
| 4 | `.env.qas` existe en `/opt/sgd/` del QAS | `ssh sistemas@sgdqas.cofar.com.bo "ls -la /opt/sgd/.env.qas"` |
| 5 | Docker ya instalado en QAS | `ssh sistemas@sgdqas.cofar.com.bo "docker --version"` debe responder `Docker 29.x` |
| 6 | Working tree limpio en DES | `git status` debe decir `nothing to commit, working tree clean` |
| 7 | Cert autofirmado en QAS | `ssh sistemas@sgdqas.cofar.com.bo "ls /opt/sgd/deploy/nginx/ssl/sgdqas.crt"` debe existir |
| 8 | Compress-Archive O Python disponible local | `python -c "import shutil; print('OK')"` debe responder `OK` |

Si ALGUNO falla, NO continuar. Resolver primero.

---

## 2. BUGS CONOCIDOS CON FIX APLICADO

Estos son los bugs que se descubrieron durante el deploy de sesión 19 y los fixes preventivos aplicados en sesión 20. **El plan actual los tiene todos resueltos.**

### 2.1 FIX 1: rename sgd-qas.conf.bk → sgd-qas.conf (sesión 19, commit `5b22bde`)

**Bug:** El repo tenía `sgd-qas.conf` con sufijo `.bk` para que nginx en DES no lo cargara. Pero al deployar a QAS, nginx solo carga archivos `*.conf` (no `*.conf.bk`), por lo que QAS quedaba sin server block → `ERR_CONNECTION_REFUSED`.

**Fix:** agregado paso `3.5/6` en `deploy-qas.bat` que renombra el archivo post-extracción:
```bat
ssh %QAS_USER%@%QAS_HOST% "cd /opt/sgd && if [ -f deploy/nginx/conf.d/sgd-qas.conf.bk ]; then mv deploy/nginx/conf.d/sgd-qas.conf.bk deploy/nginx/conf.d/sgd-qas.conf; fi"
```

### 2.2 FIX 2: `INSTRUCTIVO_TECNICO` codigo=6 vs 15 (sesión 19, commit `5b22bde`)

**Bug:** La migración 011 (`6b244889632f`) reasigna `INSTRUCTIVO_TECNICO` de codigo 6 → 15 para resolver UNIQUE constraint con `INSTRUCTIVO`. Pero el seed `seed_tipos_documento.py` seguía sembrándolo con codigo=6. En QAS (orden migración → seed, primera vez), el seed regresaba silenciosamente 15 → 6.

**Fix:** modificado el seed (línea 36):
```python
# Antes:
(6,  "INSTRUCTIVO_TECNICO", ...)
# Después:
(15, "INSTRUCTIVO_TECNICO", ...)
```

### 2.3 FIX 3: `/worktrees` inválido en robocopy (sesión 19, commit `d183ead`)

**Bug:** El comando `robocopy frontend ... /XD node_modules .git dist .agents .claude /worktrees /NFL ...` fallaba porque `/worktrees` no es parámetro válido de robocopy (debería ser `worktrees` sin slash). Robocopy abortaba silenciosamente y el frontend NUNCA se copiaba. Bug arrastrado desde sesión 14 (4 deploys con frontend desactualizado).

**Fix:** cambiar a `worktrees` (sin slash) en `deploy-qas.bat` línea 51.

### 2.4 FIX 4: `find -prune -delete` (sesión 20)

**Bug:** El comando `find . -mindepth 1 -path './backups' -prune -o -path './deploy/nginx/ssl' -prune -o -path './.env.qas' -prune -o -delete` da un warning `find: The -delete action automatically turns on -depth, but -prune does nothing when -depth is in effect`. En deploys anteriores el comportamiento fue correcto (los backups no se borraron), pero el código es FRÁGIL.

**Fix:** cambiar a `find -not -path` que NO usa `-prune`:
```bash
find . -mindepth 1 \
  -not -path './backups' -not -path './backups/*' \
  -not -path './deploy/nginx/ssl' -not -path './deploy/nginx/ssl/*' \
  -not -path './.env.qas' \
  -delete 2>/dev/null
```

### 2.5 FIX 5: `frontend/.dockerignore` (sesión 20)

**Bug:** El `COPY . .` en el Dockerfile del frontend incluía `node_modules/` del contexto (si existía en el host de `npm ci` local), sobrescribiendo el `node_modules/` que `npm install` había creado. Luego el bind mount del compose `../frontend:/app` pisaba todo en runtime, dejando el container con `node_modules` vacío.

**Fix:** crear `frontend/.dockerignore` con exclusiones de `node_modules`, `dist`, `.git`, worktrees, etc.

### 2.6 FIX 6: pre-flight checks en `deploy-qas.bat` (sesión 20)

**Bug:** El script original NO validaba pre-flight (SSH, disco, cert SSL, backup) antes de empezar. El plan `PLAN-DEPLOY-QAS-SESION18.md` sección 3.1 los listaba como obligatorios, pero el script no los ejecutaba.

**Fix:** agregar paso `0/6` "Pre-flight checks + backup pre-deploy" que valida:
1. Conectividad SSH (timeout 10s)
2. Espacio en disco QAS > 2GB
3. Cert SSL vigente > 30 días
4. Backup pre-deploy obligatorio (pg_dump + docker cp)

Si ALGUNO falla, el script aborta con `exit /b 1`.

### 2.7 FIX 7: `docker restart sgd-qas-nginx` post-deploy (sesión 20)

**Bug:** Después del deploy, el container backend se recrea con nueva IP en la red Docker. Nginx cachea la IP del upstream `backend:8000` y sigue intentando la IP vieja → `502 Bad Gateway`.

**Fix:** agregar `docker restart sgd-qas-nginx` después del `up -d` en `deploy-qas.bat` (paso 5/6).

### 2.8 FIX 8: `scripts/validate-qas.sh` (sesión 20)

**Nuevo:** script ejecutable en cualquier momento en QAS que valida las 12 categorías A-L. Imprime tabla PASS/FAIL con conteos y exit codes:
- `0` = todas PASS
- `1` = alguna FAIL
- `2` = error de conexión

**Uso:**
```bash
ssh sistemas@sgdqas.cofar.com.bo "bash /opt/sgd/scripts/validate-qas.sh"
```

---

## 3. ESTADO ACTUAL DEL SERVIDOR QAS (lectura SSH, NO ejecución)

### 3.1 Stack Docker esperado

```
sgd-qas-nginx          Up X (healthy)    0.0.0.0:80->80, 0.0.0.0:443->443
sgd-qas-celery-beat    Up X (unhealthy)  8000/tcp   (sin healthcheck, normal)
sgd-qas-celery-worker  Up X (unhealthy)  8000/tcp   (sin healthcheck, normal)
sgd-qas-backend        Up X (healthy)    8000/tcp
sgd-qas-frontend       Up X              5173/tcp
sgd-qas-mailhog        Up X              1025/tcp, 8025/tcp
sgd-qas-postgres       Up X (healthy)
sgd-qas-redis          Up X (healthy)
```

### 3.2 BD esperada (alembic head post-deploy R1)

| Tabla | Count esperado |
|---|---|
| roles | 5 |
| modulos | 11 |
| gerencias | 10 |
| areas | 50 |
| usuarios | ≥750 (4 stubs DES + ≥746 AD) |
| tipos_documento | 13 (INSTRUCTIVO_TECNICO.codigo = 15) |
| estados | 5 |
| feriados | 20 |
| email_templates | 10 (después de migración 013) |
| matriz_enrutamiento_eto | 10 |
| configuracion_global | 11 (NUEVO desde sesión 12) |
| semaforizacion_tarea | 4 (NUEVO desde sesión 13) |
| audit_log | ≥1 (1 por cada mutación) |
| alembic | `6451593bcab5` (head 013) |

### 3.3 Variables críticas esperadas en `.env.qas`

```bash
ENVIRONMENT=qas
LDAP_ENABLED=true
LDAP_SERVER=10.10.0.2  # DC interno, no RODC
LDAP_BIND_USER=soporteglpi@cofar.com
GRAPH_ENABLED=false
SMTP_ENABLED=false
CORS_ORIGINS=https://sgdqas.cofar.com.bo,http://localhost:5173,http://localhost:8080
POSTGRES_DB=sgd
```

### 3.4 Cert SSL esperado

- Subject: `C=BO, ST=La_Paz, L=La_Paz, O=COFAR, OU=SIGDOC, CN=sgdqas.cofar.com.bo`
- notAfter: > 30 días desde el deploy
- Vigencia: 365 días desde generación

### 3.5 nginx configs esperadas

```
/etc/nginx/conf.d/sgd-qas.conf   (activo, server block QAS)
/etc/nginx/conf.d/sgd.conf       (preexistente, catch-all DES — code smell, documentar)
```

**NUNCA debe haber `*.conf.bk`** en `/etc/nginx/conf.d/`.

---

## 4. CAMBIOS DESDE ÚLTIMO DEPLOY QAS

Para cada deploy, listar:
- Commits nuevos (vs último deploy)
- Archivos cambiados
- Migraciones nuevas
- Seeds nuevos/modificados
- Dependencias nuevas

Ejemplo (sesión 19):

| Categoría | Cambio | Commit |
|---|---|---|
| Backend | admin_impersonate refactor | (sesión 17) |
| Backend | audit_log.py + write_audit() helper | (sesión 6) |
| Backend | semaforizacion_tarea.py | (sesión 13) |
| Backend | tipos_documento refactor (codigo int + slug) | (sesión 13) |
| Backend | email_template enum expandido 6→10+1 | (sesión 13) |
| Backend | refresh fix + impersonate | (sesión 17-18) |
| Frontend | Tiptap 3.26.1 (5 paquetes) | (sesión 14-16) |
| Frontend | PlantillaEditor.js (closure pattern) | (sesión 16) |
| Frontend | AppLayout.js (banner impersonate) | (sesión 17) |
| Frontend | DebugSession.js (refresh fix diagnostic) | (sesión 18) |
| Frontend | router/index.js (refresh fix guard isReady) | (sesión 18) |
| Frontend | store/auth.js (init sincrono desde localStorage) | (sesión 18) |
| Scripts | deploy-qas.bat + start-stack-qas.sh (FIX 1) | `5b22bde` |
| Scripts | deploy-qas.bat (fix /worktrees) | `d183ead` |
| Scripts | deploy-qas.bat (pre-flight + restart nginx) | (sesión 20) |
| Scripts | frontend/.dockerignore | (sesión 20) |
| Scripts | validate-qas.sh | (sesión 20) |
| Migración | 6b244889632f refactor tipos_documento | sesión 13 |
| Migración | f04b96c6dff2 add semaforizacion_tarea | sesión 13 |
| Migración | 6451593bcab5 expand plantillas enum | sesión 13 |
| Seed | seed_configuracion_global.py (11 params) | sesión 12 |
| Dep | openpyxl==3.1.5 | sesión 6 |
| Dep | Tiptap 3.26.1 (5 paquetes) | sesión 14-16 |

---

## 5. PLAN DE DEPLOY PASO A PASO

### 5.1 Pre-flight LOCAL (en la laptop)

```powershell
# 1. Verificar Docker
docker info

# 2. Verificar stack DES (no bloqueante)
docker ps --filter "name=sgd-"

# 3. Verificar working tree limpio
git status
# Esperado: "nothing to commit, working tree clean"

# 4. Verificar último commit
git log --oneline -1

# 5. Verificar Python (para shutil.make_archive)
python -c "import shutil; print('OK')"
```

### 5.2 Ejecutar deploy (en la laptop)

```cmd
cd "C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES"
scripts\deploy-qas.bat
```

El script ejecuta automáticamente:

1. **[0/6] Pre-flight + backup** (NUEVO sesión 20):
   - SSH reachable
   - Disco QAS > 2GB
   - Cert SSL vigente > 30 días
   - Backup pre-deploy (`pg_dump` + `docker cp`)

2. **[1/6] Empaquetar** código local con `robocopy` + `shutil.make_archive` (zip)

3. **[2/6] SCP** del zip a QAS

4. **[3/6] Extract** con `find -not -path` (FIX 4) + `python3 zipfile.extractall`

5. **[3.5/6] Rename** sgd-qas.conf.bk → sgd-qas.conf (FIX 1)

6. **[4/6] Rebuild** imágenes Docker con `--no-cache` (backend, celery-W, celery-B, frontend)

7. **[5/6] Restart** servicios + `docker restart sgd-qas-nginx` (FIX 7) + esperar health checks

8. **[6/6] `start-stack-qas.sh`** (8 seeds idempotentes + sync AD)

### 5.3 Flags opcionales del script

```cmd
scripts\deploy-qas.bat                  # deploy + restart + seeds + sync AD (default)
scripts\deploy-qas.bat --no-restart    # solo sube codigo, no restart
scripts\deploy-qas.bat --no-seed       # deploy + restart, sin correr seeds
```

---

## 6. VALIDACIONES A-L (12 categorías)

### 6.1 Ejecución rápida (todo en uno)

```bash
ssh sistemas@sgdqas.cofar.com.bo "bash /opt/sgd/scripts/validate-qas.sh"
```

El script imprime tabla PASS/FAIL/WARN con conteos. Exit code:
- `0` = todas PASS
- `1` = alguna FAIL
- `2` = error de conexión

### 6.2 Detalle de cada categoría

| # | Categoría | Validación | Comando |
|---|---|---|---|
| A.1 | Health | Backend directo 200 | `docker exec sgd-qas-backend curl -fsS http://localhost:8000/api/v1/health` |
| A.2 | Health | HTTPS via nginx 200 | `curl -kfsS -o /dev/null -w '%{http_code}\n' https://localhost/api/v1/health` |
| A.3 | Health | 8 servicios Up | `docker ps --filter "name=sgd-qas-" --format '{{.Names}}' \| wc -l` |
| B.1 | Librerías | openpyxl 3.1.5 | `docker exec sgd-qas-backend python -c 'import openpyxl; print(openpyxl.__version__)'` |
| B.2 | Librerías | Tiptap >= 5 packages | `docker exec sgd-qas-frontend sh -c 'ls -d /app/node_modules/@tiptap/* 2>/dev/null \| wc -l'` |
| C.1 | Migraciones | alembic 6451593bcab5 | `docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c "SELECT version_num FROM alembic_version"` |
| C.2 | Migraciones | semaforizacion_tarea existe | `docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c "SELECT count(*) FROM information_schema.tables WHERE table_name='semaforizacion_tarea'"` |
| C.3 | Migraciones | tipos_documento sin codigo_doc, con slug | (ver script) |
| C.4 | Migraciones | enum email_templates con 11 valores | (ver script) |
| D | Datos BD | 13 tablas con conteos esperados | (ver script tabla) |
| D.13 | Datos BD | INSTRUCTIVO_TECNICO.codigo=15 | `docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c "SELECT codigo FROM tipos_documento WHERE slug='INSTRUCTIVO_TECNICO'"` |
| E.1 | Login | BD Local (aromero) 200 | `curl -kfsS -X POST https://localhost/api/v1/login -H "Content-Type: application/json" -d '{"username":"aromero","password":"cofar.2026","auth_source":"local"}'` |
| E.2 | Login | /me con cookies authenticated | `curl -kfsS -b /tmp/cookies.txt https://localhost/api/v1/me` |
| F.1 | Endpoints | /audit-log 200 | `curl -kfsS -b /tmp/cookies.txt "https://localhost/api/v1/audit-log?limit=5"` |
| F.2 | Endpoints | /semaforizacion-tarea 200 | `curl -kfsS -b /tmp/cookies.txt https://localhost/api/v1/semaforizacion-tarea` |
| F.3 | Endpoints | /admin/impersonate/list 200 | `curl -kfsS -b /tmp/cookies.txt https://localhost/api/v1/admin/impersonate/list` (path real con slash, no guion como dice el plan original) |
| G | Refresh fix | URL se mantiene post-reload (validar en Chrome MCP) | hard reload en /bandeja, verificar Alpine.store('auth').isReady=true |
| H | Tiptap | 11 plantillas + toolbar completa | Click en tab Plantillas, verificar editor + toolbar |
| I | Impersonate | Banner sticky + audit dedicado | Click en Impersonar, verificar banner |
| J | Sync AD | CSV con >=750 lineas | `docker exec sgd-qas-backend sh -c 'wc -l < /app/storage/usuarios_sap_FINAL2026.csv'` |
| K.1 | nginx | HTTP→HTTPS 301 | `curl -kfsS -o /dev/null -w '%{http_code}\n' http://localhost/` |
| K.2 | nginx | HTTPS health 200 | `curl -kfsS -o /dev/null -w '%{http_code}\n' https://localhost/api/v1/health` |
| K.3 | nginx | sgd-qas.conf activo (no .bk) | `docker exec sgd-qas-nginx ls /etc/nginx/conf.d/` |
| L.1 | Seguridad | CORS preflight 200 | `curl -kfsS -o /dev/null -w '%{http_code}\n' -X OPTIONS https://localhost/api/v1/login -H 'Origin: https://sgdqas.cofar.com.bo' -H 'Access-Control-Request-Method: POST'` |
| L.2 | Seguridad | CSRF cookie no HttpOnly | (ver script) |

### 6.3 Validaciones que requieren Chrome MCP (no automatizables)

- **G (refresh fix):** abrir Chrome en `https://sgdqas.cofar.com.bo/`, login, hard reload en /bandeja, verificar que URL no cambia a /login. Inspeccionar `Alpine.store('auth').isReady`, `isAuthenticated`, `localStorage.getItem('cofar_session')`.
- **H (Tiptap):** ir a /parametrizacion, tab Plantillas, verificar 11 plantillas, toolbar completa (B/I/U/S/H1-3/listas/code/color/fontSize/undo/redo), 11 variables clicables.
- **I (Impersonate):** ir a /parametrizacion, tab Gestión de Usuarios, click Impersonar, verificar banner sticky con gradiente amber→orange→red.

NOTA: Chrome MCP no carga el cert autofirmado de QAS. Validar G/H/I en DES local (mismo código frontend) o en corp con VPN que acepte el cert.

---

## 7. COMANDOS DE TROUBLESHOOTING

### 7.1 Si el pre-flight falla

```bash
# SSH no reachable
ssh -v sistemas@sgdqas.cofar.com.bo "echo OK"

# Disco bajo
ssh sistemas@sgdqas.cofar.com.bo "du -sh /opt/sgd/* | sort -h | tail -20"

# Cert SSL expirado
ssh sistemas@sgdqas.cofar.com.bo "openssl x509 -in /opt/sgd/deploy/nginx/ssl/sgdqas.crt -noout -dates"
# Si expira pronto: regenerar cert autofirmado (ver docs/PR/DEPLOY-QAS.md seccion SSL)

# Backup pre-deploy manual
ssh sistemas@sgdqas.cofar.com.bo "TS=\$(date -u +%Y%m%d_%H%M%S); docker exec sgd-qas-postgres pg_dump -U sgd -d sgd -Fc -f /tmp/qas_\${TS}.dump && docker cp sgd-qas-postgres:/tmp/qas_\${TS}.dump /opt/sgd/backups/ && ls -la /opt/sgd/backups/qas_\${TS}.dump"
```

### 7.2 Si el deploy falla a mitad

```bash
# Ver logs del backend
ssh sistemas@sgdqas.cofar.com.bo "docker logs sgd-qas-backend --tail 50"

# Ver logs de nginx
ssh sistemas@sgdqas.cofar.com.bo "docker logs sgd-qas-nginx --tail 20"

# Ver estado de los 8 contenedores
ssh sistemas@sgdqas.cofar.com.bo "docker ps -a --filter name=sgd-qas- --format 'table {{.Names}}\t{{.Status}}'"
```

### 7.3 Si 502 Bad Gateway (nginx)

```bash
# El nginx cacheo IP vieja del backend
ssh sistemas@sgdqas.cofar.com.bo "docker restart sgd-qas-nginx && sleep 5 && curl -kfsS -o /dev/null -w 'HTTPS: %{http_code}\n' https://localhost/api/v1/health"
```

### 7.4 Si Tiptap falla en frontend (node_modules vacio)

```bash
# El bind mount del compose pisa node_modules. Workaround:
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-frontend sh -c 'cd /app && npm install --no-audit --no-fund'"
# Luego validar de nuevo:
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-frontend sh -c 'ls -d /app/node_modules/@tiptap/* | wc -l'"
# Esperado: >= 5

# PERMANENTE: ver seccion 12 backlog (cambiar Dockerfile o compose)
```

### 7.5 Si las migraciones fallan

```bash
# Ver el alembic head actual
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c 'SELECT version_num FROM alembic_version'"

# Ver logs del backend al arrancar (muestra las migraciones aplicadas)
ssh sistemas@sgdqas.cofar.com.bo "docker logs sgd-qas-backend --tail 100 | grep -i alembic"

# Re-aplicar migraciones manualmente
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-backend alembic upgrade head"
```

### 7.6 Si un seed falla

```bash
# Re-correr el seed manualmente (es idempotente)
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-backend python scripts/seed_configuracion_global.py"
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-backend python scripts/seed_email_templates.py"
# etc.
```

### 7.7 Si la BD se corrompe

```bash
# Restaurar desde backup pre-deploy
TS=<TIMESTAMP_BACKUP>
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker cp backups/qas_\${TS}_pre_sesion.dump sgd-qas-postgres:/tmp/restore.dump && docker exec sgd-qas-postgres pg_restore -U sgd -d sgd --clean --if-exists --no-owner --role=sgd /tmp/restore.dump"

# Verificar conteos
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-postgres psql -U sgd -d sgd -tA -c 'SELECT count(*) FROM usuarios'"
```

### 7.8 Verificar logs en vivo

```bash
# Backend
ssh sistemas@sgdqas.cofar.com.bo "docker logs sgd-qas-backend -f --tail 100"

# nginx
ssh sistemas@sgdqas.cofar.com.bo "docker logs sgd-qas-nginx -f --tail 50"

# Postgres
ssh sistemas@sgdqas.cofar.com.bo "docker logs sgd-qas-postgres -f --tail 50"
```

---

## 8. ESCENARIOS ESPECIALES

### 8.1 Solo subir codigo (no restart)

```cmd
scripts\deploy-qas.bat --no-restart
```

Útil cuando:
- Solo quieres actualizar archivos sin reiniciar (e.g., actualizar la imagen sin downtime)
- Vas a reiniciar manualmente después

### 8.2 Deploy sin correr seeds

```cmd
scripts\deploy-qas.bat --no-seed
```

Útil cuando:
- Las migraciones ya están aplicadas y solo quieres re-deployar código
- Vas a correr seeds manualmente

### 8.3 Restaurar backup pre-deploy

Ver sección 7.7.

### 8.4 Forzar rebuild de una imagen específica

```bash
# Solo rebuild backend
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml --env-file .env.qas build --no-cache backend"

# Solo rebuild frontend
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml --env-file .env.qas build --no-cache frontend"
```

### 8.5 Forzar reinicio de un servicio

```bash
# Reiniciar backend
ssh sistemas@sgdqas.cofar.com.bo "docker compose -f /opt/sgd/deploy/docker-compose.qas.yml --env-file /opt/sgd/.env.qas restart backend"

# Reiniciar nginx (refresca cache DNS)
ssh sistemas@sgdqas.cofar.com.bo "docker restart sgd-qas-nginx"
```

### 8.6 Re-sync AD manual

```bash
# Borra el CSV y re-sincroniza
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-backend rm -f /app/storage/usuarios_sap_FINAL2026.csv && docker exec --env-file /opt/sgd/.env.qas sgd-qas-backend python scripts/sync_ad_oficial.py"
```

### 8.7 Re-import matriz abril (NO en QAS, solo DES)

```bash
# Solo para DES
cd /opt/sgd  # o donde esté el repo en DES
docker exec sgd-backend python scripts/run_matriz_import.py --excel "/ruta/al/USUARIOS EXISTENTES A ABRIL.xlsx" --update-existing
```

### 8.8 Validar QAS en cualquier momento (no solo post-deploy)

```bash
ssh sistemas@sgdqas.cofar.com.bo "bash /opt/sgd/scripts/validate-qas.sh"
```

Exit codes:
- `0` = OK
- `1` = alguna validación falló
- `2` = error de conexión

---

## 9. ROLLBACK

### 9.1 Rollback de CÓDIGO

```bash
# En DES, volver al commit anterior al deploy
git checkout HEAD~1
scripts\deploy-qas.bat
git checkout -
```

### 9.2 Rollback de BD (último recurso)

```bash
TS=<TIMESTAMP_BACKUP>
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker cp backups/qas_\${TS}_pre_sesion.dump sgd-qas-postgres:/tmp/restore.dump && docker exec sgd-qas-postgres pg_restore -U sgd -d sgd --clean --if-exists --no-owner --role=sgd /tmp/restore.dump"
```

### 9.3 Rollback de NGINX

```bash
ssh sistemas@sgdqas.cofar.com.bo "cp -a /tmp/conf.d.bak.\${TS}/* /opt/sgd/deploy/nginx/conf.d/ && cp /tmp/nginx.conf.bak.\${TS} /opt/sgd/deploy/nginx/nginx.conf && docker restart sgd-qas-nginx"
```

### 9.4 Rollback completo (último recurso)

Si NADA funciona, restaurar TODO desde el último deploy conocido:

1. Rollback de código: `git checkout <commit_del_último_deploy_OK>`
2. Re-deploy: `scripts\deploy-qas.bat --no-seed` (sin seeds para no aplicar nuevas)
3. Restaurar BD desde backup
4. Validar con `validate-qas.sh`

---

## 10. RIESGOS IDENTIFICADOS

| # | Riesgo | Severidad | Mitigación |
|---|---|---|---|
| 1 | Migración 011 (refactor tipos_documento) rompe datos | 🟠 Alta | Backup pre-deploy obligatorio (FIX 6) |
| 2 | Migración 013 (expand enum) falla | 🟡 Media | Downgrade -1 + restaurar backup |
| 3 | openpyxl no se instala en rebuild | 🟢 Baja | requirements/base.txt commiteado, mismo Dockerfile |
| 4 | Tiptap falla al instalar | 🟡 Media | package-lock.json commiteado, npm ci debería funcionar |
| 5 | sgd-qas.conf.bk no se renombra | 🟠 Alta | FIX 1 (paso 3.5/6) + validación K.3 |
| 6 | nginx cachea IP vieja del backend | 🟠 Alta | FIX 7 (docker restart sgd-qas-nginx) |
| 7 | node_modules vacio en container | 🟠 Alta | FIX 5 (.dockerignore) + workaround `docker exec npm install` |
| 8 | Sync AD genera CSV vacio | 🟡 Media | Validar J.1. Si falla, QAS queda con usuarios previos |
| 9 | CORS rompe después del deploy | 🟢 Baja | CORS_ORIGINS en .env.qas tiene https://sgdqas.cofar.com.bo |
| 10 | Refresh bug #15 sigue presente | 🟢 Baja | Fix commiteado. Validar G.1-G.8 con Chrome MCP |
| 11 | DNS interno no responde en pre-flight (problema de red corp) | 🟡 Media | El script continúa y avisa. Validar manualmente si pasa |
| 12 | Plazo 42 invalid (cosmetic) | 🟢 Baja | El seed dice 25, pero si se ejecutó con valor previo no se actualiza. Backlog próxima sesión |

---

## 11. DIFERENCIAS QAS VS DES ESPERADAS (NO BUGS)

| Item | QAS | DES | Por qué |
|---|---|---|---|
| Gerencias | 10 | 14 | QAS solo siembra 10 (seed_data.py), DES tiene 4 extras de pruebas |
| Areas | 50 | 56 | Similar a gerencias |
| Usuarios | ≥750 | 764 | QAS tiene 4 stubs DES + ≥746 AD, DES tiene 10 extras de pruebas |
| Tipos doc | 13 | 14 | Similar (INSTRUCTIVO_TECNICO puede tener diferente codigo) |
| Feriados | 20 | 23 | Similar |
| audit_log | ≥1 | ≥50 | Continúa acumulando |
| plazo_revision_aprobacion_dias | 25 (seed) | 42 (legacy) | Diferente: QAS ejecutó seed, DES tiene valor legacy |

---

## 12. BACKLOG PRE-PROD

Tareas que DEBEN hacerse antes de pasar a producción (PRD):

| # | Tarea | Sesión sugerida | Esfuerzo |
|---|---|---|---|
| 1 | Fix permanente bind mount node_modules (cambiar compose o Dockerfile) | 21 | 2h |
| 2 | Cert HTTPS válido (Let's Encrypt o cert corporativo) | pre-PROD | 4h |
| 3 | Sudo NOPASSWD restringido a comandos específicos | pre-PROD | 1h |
| 4 | Password SSH rotada + SSH key-only (ya hecho en sesión 11) | ✅ | — |
| 5 | Activar GRAPH_ENABLED (Office 365) | R4 | 1 semana |
| 6 | Activar SMTP real corporativo | pre-PROD | 1h |
| 7 | Backups automáticos en QAS (cron + pg_dump) | 21 | 1h |
| 8 | Monitoring Prometheus/Grafana | pre-PROD | 1 día |
| 9 | Fix Plazo 42 invalid (seed dice 25, BD tiene 42) | 21 | 5 min |
| 10 | Code smell `sgd.conf` en QAS (catch-all de DES) | 22 | 30 min |

---

## 13. RESUMEN EJECUTIVO

### 13.1 Lo que se va a hacer (deploy típico)

1. **Pre-flight** (FIX 6): SSH + disco + cert + backup
2. **Deploy** (FIX 1+2+3+4+5+7): zip + scp + extract + rename + rebuild + restart
3. **Migraciones**: 3 nuevas (010 → 013)
4. **Seeds**: 8 idempotentes (incluido `seed_configuracion_global.py`)
5. **Sync AD**: real contra DC `10.10.0.2` (≥750 usuarios)
6. **Validación**: 12 categorías A-L (script `validate-qas.sh`)

### 13.2 Lo que NO se hace en este deploy

- ❌ Cambiar a cert HTTPS válido (queda para sesión pre-PROD)
- ❌ Cambiar a NOPASSWD sudo restringido
- ❌ Cambiar password SSH (ya es key-only desde sesión 11)
- ❌ Activar GRAPH_ENABLED (Office 365)
- ❌ Activar SMTP real corporativo
- ❌ Importar matriz abril (NO se ejecuta en QAS, solo en DES)
- ❌ Backups automáticos en cron (queda para pre-PROD)
- ❌ Monitoring Prometheus/Grafana

### 13.3 Criterio de éxito

`bash /opt/sgd/scripts/validate-qas.sh` debe retornar exit code 0 (todas las validaciones A-L PASS). Si retorna 1, rollback según sección 9.

### 13.4 Tiempo estimado

60-75 min total (incluyendo FIX 1+2+3+4+5+6+7+8 y validaciones).

### 13.5 Archivos clave del deploy

| Archivo | Función |
|---|---|
| `scripts/deploy-qas.bat` | Empaqueta + SCP + extract + rebuild + restart |
| `scripts/start-stack-qas.sh` | 8 seeds + sync AD + resumen |
| `scripts/validate-qas.sh` | 12 validaciones A-L (ejecutable en cualquier momento) |
| `deploy/docker-compose.qas.yml` | 8 servicios, network sgd-qas-net, vol sgd-qas_* |
| `deploy/Dockerfile` (backend) | Python 3.12 + openpyxl + alembic + uvicorn |
| `frontend/Dockerfile` | node:22 + Vite + (después de FIX 5: respeta .dockerignore) |
| `frontend/.dockerignore` (NUEVO sesión 20) | Excluye node_modules, dist, .git, worktrees, etc. |
| `backend/scripts/seed_*.py` | 8 seeds idempotentes |
| `backend/alembic/versions/*.py` | 13 migraciones (001-013) |
| `docs/PR/PLAN-DEPLOY-QAS-SESION18.md` | Este documento |

---

**Fin del plan.** Para cualquier duda, revisar la bitácora de la sesión 19 (entrada completa en `docs/PR/BITACORA.md`).
