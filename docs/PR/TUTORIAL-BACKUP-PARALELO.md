# TUTORIAL — Stack BACKUP paralelo (encender / apagar / verificar)

> **TL;DR:** Para encender: `scripts\start-stack-backup.bat`. Para apagar: `scripts\stop-stack-backup.bat`.
> Todo lo demás (puertos, URLs, troubleshooting) está acá.

---

## 1. Encender el stack backup

### Comando simple (usa el dump mas reciente)

```cmd
scripts\start-stack-backup.bat
```

El script automaticamente:
1. Busca el dump mas reciente en `backups\<timestamp>\sgd_pre_refactor.dump` (ordenado por fecha)
2. Levanta postgres y redis del backup (crea volumenes nuevos `sgd-des-bk_*` si no existen)
3. Espera a que postgres este healthy (~5-10s)
4. Copia el dump al contenedor y aplica `pg_restore`
5. Levanta backend, celery-W/B, frontend, nginx, mailhog
6. Espera a que el backend responda health check
7. Imprime las URLs

**Tiempo total:** ~3-5 minutos la primera vez (incluye build de imagenes Docker).
**Runs siguientes:** ~1-2 minutos (imagenes ya construidas, solo restaura dump).

### Comando con dump especifico

```cmd
scripts\start-stack-backup.bat backups\20260616_150015\sgd_pre_refactor.dump
```

Util cuando tenes varios snapshots y queres restaurar uno en particular.

### Especificar .env distinto (raro, pero posible)

Por defecto usa `.env.backup` de la raiz. Si queres otro .env:

```cmd
set COMPOSE_ENV_FILE=.env.backup-otra-version
scripts\start-stack-backup.bat
```

---

## 2. Verificar que esta funcionando

### Health checks

```cmd
REM Backend directo (puerto 18001)
curl.exe -fsS http://localhost:18001/api/v1/health

REM Via nginx (puerto 8081 - el que usarias en el browser)
curl.exe -fsS http://localhost:8081/health

REM Frontend (puerto 5174)
curl.exe -fsS http://localhost:5174/
```

Respuesta esperada del health: `{"status":"ok","service":"cofar-sgd-api","database":"ok"}`

### Login funcional

```cmd
echo {"username":"aromero","password":"cofar.2026","auth_source":"local"} > %TEMP%\test_login.json
curl.exe -X POST http://localhost:8081/api/v1/login -H "Content-Type: application/json" --data-binary @%TEMP%\test_login.json
```

Si retorna 200 OK con cookies + JSON del usuario, todo OK.

### Ver contenedores activos

```cmd
docker ps --filter "name=sgd-bk-"
```

Deberias ver 8 contenedores con status `Up` o `healthy`:
- sgd-bk-postgres
- sgd-bk-redis
- sgd-bk-mailhog
- sgd-bk-backend
- sgd-bk-celery-worker
- sgd-bk-celery-beat
- sgd-bk-frontend
- sgd-bk-nginx

### Comparar datos con el original

```cmd
docker exec sgd-postgres psql -U sgd -d sgd -tA -c "SELECT 'usuarios: ' || count(*) FROM usuarios"
docker exec sgd-bk-postgres psql -U sgd -d sgd_backup -tA -c "SELECT 'usuarios: ' || count(*) FROM usuarios"
```

Los dos comandos deben retornar el mismo numero.

---

## 3. Acceder desde el navegador

Abrir: **http://localhost:8081**

Login con cualquiera de los stubs DES:
- `aromero / cofar.2026` → rol ETO
- `admin / cofar.2026` → rol ADMIN
- `solicitante / cofar.2026` → rol estandar
- `visualizador / cofar.2026` → rol visualizador

> **IMPORTANTE:** el navegador NO debe tener cookies del stack original (8080).
> Si acabas de loguearte en 8080, las cookies pueden confundir. Solucion:
> - Usar ventana de incognito
> - O: DevTools > Application > Cookies > borrar `user_id`, `session`, `csrf_token`
> - O: otro navegador

---

## 4. Apagar el stack backup (cuando termines la demo/reunion)

### Apagar containers, MANTENER datos (recomendado)

```cmd
scripts\stop-stack-backup.bat
```

Esto baja los 8 contenedores. Los volumenes `sgd-des-bk_*` quedan en disco.
**Espacio liberado:** ~0 MB (los volumenes pesan igual).
**Tiempo para volver a encender:** ~1-2 min (no rebuild).

### Apagar containers Y BORRAR volumenes (purga total)

```cmd
scripts\stop-stack-backup.bat --purge
```

Esto baja los contenedores y **borra** los volumenes:
- `sgd-des-bk_postgres_data` (BD)
- `sgd-des-bk_redis_data` (cache)
- `sgd-des-bk_backend_storage` (archivos)
- `sgd-des-bk_frontend_node_modules` (deps npm)

**Espacio liberado:** ~200-500 MB.
**Proxima vez que enciendas:** restaura el dump desde cero (~3-5 min).

### Apagado de emergencia (kill)

Si el script se cuelga o algo esta raro:

```cmd
docker ps -a --filter "name=sgd-bk-" --format "{{.Names}}" | ForEach-Object { docker rm -f $_ }
docker volume rm sgd-des-bk_postgres_data sgd-des-bk_redis_data sgd-des-bk_backend_storage sgd-des-bk_frontend_node_modules
docker network rm sgd-des-bk_net
```

---

## 5. Actualizar el dump (snapshotea el estado actual del ORIGINAL al backup)

Si hiciste cambios en el original y queres que el backup los refleje:

### Paso 1: generar nuevo dump del original

```cmd
mkdir backups\<nuevo_timestamp>
docker exec sgd-postgres pg_dump -U sgd -d sgd -Fc -f /tmp/x.dump
docker cp sgd-postgres:/tmp/x.dump backups\<nuevo_timestamp>\sgd_pre_refactor.dump
```

### Paso 2: re-levantar el backup con el nuevo dump

```cmd
scripts\start-stack-backup.bat backups\<nuevo_timestamp>\sgd_pre_refactor.dump
```

El script baja los contenedores, los vuelve a levantar y restaura el dump nuevo.
**Cuidado:** si hiciste cambios en el backup directamente, se pierden (es un snapshot, no merge).

---

## 6. Troubleshooting rapido

### "container name already in use"

```cmd
docker ps -a --filter "name=sgd-bk-" --format "{{.Names}}" | ForEach-Object { docker rm -f $_ }
```

### "bind: address already in use" al levantar

Otro proceso esta usando 8081, 5174, 18001, 25433, 26380 u 8026.

```cmd
netstat -ano | findstr "8081 5174 18001 25433 26380 8026"
```

Matar el PID que corresponda (o cambiar el puerto en `.env.backup`).

### El frontend del backup se ve raro / cacheado

Vite tiene cache agresivo. Refresca con:

```cmd
docker restart sgd-bk-frontend
```

Y en el browser: `Ctrl+Shift+R` (hard refresh) o `?_v=2` en la URL.

### Login devuelve 500

Probablemente el backend no se reinicio despues del pg_restore. Forzar restart:

```cmd
docker restart sgd-bk-backend sgd-bk-celery-worker sgd-bk-celery-beat
```

### Quiero ver que esta pasando (logs en vivo)

```cmd
docker compose -f deploy/docker-compose.backup.yml --env-file .env.backup logs -f backend
```

(Ctrl+C para salir).

### Reset total (volver a empezar desde cero)

```cmd
scripts\stop-stack-backup.bat --purge
scripts\start-stack-backup.bat
```

---

## 7. Referencia rapida de URLs y puertos

| Servicio | Puerto host | URL |
|---|---|---|
| Nginx (entrypoint principal) | **8081** | http://localhost:8081 |
| Frontend (Vite) | **5174** | http://localhost:5174 |
| Backend (FastAPI) | **18001** | http://localhost:18001 |
| Backend docs (Swagger) | **18001** | http://localhost:18001/docs |
| MailHog UI | **8026** | http://localhost:8026 |
| Postgres | **25433** | `postgresql://sgd:sgd_dev_only_change_in_prod@localhost:25433/sgd_backup` |
| Redis | **26380** | `redis://localhost:26380` |

> Original: 8080/5173/18000/25432/26379/8025/1025 (intacto).

---

## 8. Archivos importantes

| Archivo | Que tiene |
|---|---|
| `scripts\start-stack-backup.bat` | Script para encender |
| `scripts\stop-stack-backup.bat` | Script para apagar |
| `.env.backup` | Variables de entorno del backup (puertos, DB, secrets) |
| `deploy\docker-compose.backup.yml` | Compose del backup (8 servicios) |
| `deploy\nginx\conf.d.bk\sgd-backup.conf` | Config nginx del backup |
| `docs\PR\BACKUP-PARALELO.md` | Doc tecnica completa (arquitectura, riesgos) |
| `backups\<timestamp>\sgd_pre_refactor.dump` | Dump pg_dump del estado original |
| `backups\<timestamp>\src\` | Copia del codigo fuente (393 archivos) |

---

## 9. Cuando dejar de usar el backup

- Cuando termines la demo / reunion (apaga con `stop-stack-backup.bat`)
- Cuando hagas cambios grandes en el codigo del original y NO quieras que el backup los vea (apaga primero, edita, valida, re-levanta con dump nuevo)
- Cuando te mudes al servidor QAS (el backup DES ya no sera necesario)

**Para apagarlo definitivamente y liberar espacio en disco:**
```cmd
scripts\stop-stack-backup.bat --purge
```
