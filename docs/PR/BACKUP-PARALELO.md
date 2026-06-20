# BACKUP PARALELO — Stack aislado en puertos 8081/5174/18001

> **Generado:** 2026-06-16 sesion 10
> **Proposito:** Permitir mostrar el estado actual de la aplicacion en otro puerto,
> **mientras se sigue desarrollando en el stack original** (8080/5173/18000)
> sin riesgo de romper la demo.

---

## TL;DR

| Item | Stack original | Stack backup |
|---|---|---|
| **App (Nginx)** | http://localhost:8080 | http://localhost:8081 |
| **Frontend (Vite)** | http://localhost:5173 | http://localhost:5174 |
| **Backend (FastAPI)** | http://localhost:18000 | http://localhost:18001 |
| **Backend docs (Swagger)** | http://localhost:18000/docs | http://localhost:18001/docs |
| **MailHog UI** | http://localhost:8025 | http://localhost:8026 |
| **Postgres host port** | 25432 (db: `sgd`) | 25433 (db: `sgd_backup`) |
| **Redis host port** | 26379 | 26380 |
| **Container prefix** | `sgd-*` | `sgd-bk-*` |
| **Volume prefix** | `sgd-des_*` | `sgd-des-bk_*` |
| **Network** | `sgd-des_net` | `sgd-des-bk_net` |
| **`.env` file** | `.env` | `.env.backup` |
| **Compose file** | `deploy/docker-compose.yml` | `deploy/docker-compose.backup.yml` |

Ambos stacks pueden correr en paralelo, comparten el mismo codigo fuente (montado desde
`../backend` y `../frontend`) pero tienen **datos, redes y volumenes completamente aislados**.

---

## Como levantar el backup

### 1. Una sola vez: crear el dump (snapshot de la BD)

```bash
# Crea un dump de la BD del stack original en backups/<timestamp>/sgd_pre_refactor.dump
mkdir -p backups/20260616_manual
docker exec sgd-postgres pg_dump -U sgd -d sgd -Fc -f /tmp/x.dump
docker cp sgd-postgres:/tmp/x.dump backups/20260616_manual/sgd_pre_refactor.dump
```

### 2. Levantar el stack backup

```bash
scripts\start-stack-backup.bat
# o especificando un dump concreto:
scripts\start-stack-backup.bat backups\20260616_manual\sgd_pre_refactor.dump
```

El script:
1. Verifica `.env.backup` y Docker up.
2. Levanta `postgres` y `redis` del backup (crea volumenes nuevos `sgd-des-bk_*`).
3. Espera a que `sgd-bk-postgres` este healthy.
4. Copia el dump al contenedor y aplica `pg_restore --no-owner --role=sgd --clean --if-exists`.
5. Levanta el resto (backend, celery-W/B, frontend, nginx, mailhog).
6. Espera a que `sgd-bk-backend` este healthy.
7. Imprime las URLs del backup.

### 3. Verificar

```bash
# Backend directo
curl.exe -fsS http://localhost:18001/api/v1/health
# Via Nginx (entrypoint principal)
curl.exe -fsS http://localhost:8081/health
# Login funcional
curl.exe -X POST http://localhost:8081/api/v1/login -H "Content-Type: application/json" -d "{\"username\":\"aromero\",\"password\":\"cofar.2026\",\"auth_source\":\"local\"}"
```

Login esperado: `aromero / cofar.2026` (rol ETO) o cualquier stub DES.

### 4. Apagar el backup (conserva datos)

```bash
scripts\stop-stack-backup.bat              # baja containers, mantiene volumenes
scripts\stop-stack-backup.bat --purge      # baja containers + BORRA volumenes
```

---

## Que pasa si edito codigo en el original?

Ambos stacks montan el mismo codigo fuente del repo:
- Backend: `../backend:/app` (volume mount en compose)
- Frontend: `../frontend:/app` (volume mount en compose)

Esto significa que:
- **Si edito un .py del backend** → uvicorn --reload detecta el cambio en AMBOS stacks
  (cada uno con su propio proceso uvicorn, en su propia red). El original Y el backup
  reflejan el cambio.
- **Si edito un .js del frontend** → Vite HMR lo refleja en ambos servidores de dev
  (5173 y 5174), pero el navegador de cada uno esta conectado a su propio Vite server.

**Esto es INTENCIONAL**: el backup es un espejo de la demo, no un sandbox separado.

**Si queres hacer cambios sin afectar el backup:**
1. Apaga el backup (`scripts\stop-stack-backup.bat`).
2. Edita el codigo en el original.
3. Verifica en el original.
4. Cuando estes conforme con el estado nuevo, genera un dump nuevo y re-eleva el backup.

---

## Estructura de archivos del backup

```
.
├── .env.backup                              # Variables de entorno del backup
├── deploy/
│   ├── docker-compose.yml                   # Original (NO TOCADO)
│   ├── docker-compose.backup.yml            # Compose del backup (8 servicios)
│   └── nginx/
│       ├── nginx.conf                       # Original (NO TOCADO)
│       ├── conf.d/
│       │   └── sgd.conf                     # Original (NO TOCADO)
│       └── conf.d.bk/                       # Backup (AISLADO del original)
│           └── sgd-backup.conf
├── scripts/
│   ├── start-stack-des.bat                  # Original (NO TOCADO)
│   ├── stop-stack-des.bat                   # Original (NO TOCADO)
│   ├── start-stack-backup.bat               # NUEVO: levanta backup
│   └── stop-stack-backup.bat                # NUEVO: baja backup
├── backups/
│   └── 20260616_150015/
│       ├── sgd_pre_refactor.dump            # Dump pg_dump del estado
│       └── src/                             # Working tree (393 archivos)
│           ├── backend/
│           ├── frontend/
│           ├── deploy/
│           └── docs/
└── docs/PR/
    └── BACKUP-PARALELO.md                   # Este archivo
```

---

## Aislamiento tecnico: por que NO chocan

| Recurso | Original | Backup | Aislado por |
|---|---|---|---|
| Host ports | 8080/5173/18000/25432/26379 | 8081/5174/18001/25433/26380 | `.env` vs `.env.backup` |
| Container names | `sgd-postgres`, `sgd-backend` | `sgd-bk-postgres`, `sgd-bk-backend` | `container_name:` en compose |
| Volume names | `sgd-des_postgres_data` | `sgd-des-bk_postgres_data` | `volumes:` en compose |
| Network | `sgd-des_net` | `sgd-des-bk_net` | `networks:` en compose |
| DB name | `sgd` | `sgd_backup` | `POSTGRES_DB` en .env |
| CORS origins | `localhost:8080/5173/18000` | + `localhost:8081/5174/18001` | `CORS_ORIGINS` en .env |
| Service names | `postgres`, `redis`, `backend` | IGUALES (resueltos por red Docker) | Aislamiento por red |
| Nginx conf | `conf.d/sgd.conf` | `conf.d.bk/sgd-backup.conf` | Volume mount distinto |
| Vite API URL | `http://localhost:18000/api/v1` | `http://localhost:18001/api/v1` | `VITE_API_URL` en compose |

**Docker DNS es por red**, no global. Cada contenedor resuelve `backend` al servicio
de SU red (la unica que tiene un contenedor con ese nombre en su scope).

---

## Troubleshooting

### El backup no arranca: "container name already in use"

Algun container `sgd-bk-*` quedo de un intento previo. Limpiar:
```bash
docker ps -a --filter "name=sgd-bk-" --format "{{.Names}}" | ForEach-Object { docker rm -f $_ }
```

### El backup no responde en :8081

Verificar que `sgd-bk-nginx` este corriendo:
```bash
docker ps --filter "name=sgd-bk-nginx"
docker logs sgd-bk-nginx --tail 20
```

Si nginx no arranca por config invalida, ver logs y comparar con `sgd.conf` (original).

### `pg_restore` falla con "ERROR: role sgd does not exist"

Esto no deberia pasar (la imagen postgres:16-alpine crea el role automaticamente),
pero si pasa:
```bash
docker exec sgd-bk-postgres createuser -s sgd
docker exec sgd-bk-postgres createdb -O sgd sgd_backup
docker exec -i sgd-bk-postgres pg_restore -U sgd -d sgd_backup --no-owner --clean --if-exists < /tmp/sgd_pre_refactor.dump
```

### El backup arranca pero los datos no son los esperados

Re-correr `pg_restore` manualmente:
```bash
docker cp backups/20260616_150015/sgd_pre_refactor.dump sgd-bk-postgres:/tmp/x.dump
docker exec sgd-bk-postgres pg_restore -U sgd -d sgd_backup --no-owner --role=sgd --clean --if-exists /tmp/x.dump
docker restart sgd-bk-backend sgd-bk-celery-worker sgd-bk-celery-beat
```

### Quiero comparar datos entre original y backup

```bash
docker exec sgd-postgres psql -U sgd -d sgd -tA -c "SELECT 'usuarios: ' || count(*) FROM usuarios"
docker exec sgd-bk-postgres psql -U sgd -d sgd_backup -tA -c "SELECT 'usuarios: ' || count(*) FROM usuarios"
```

Los conteos deben ser identicos despues del restore.

---

## Limitaciones conocidas

1. **Memoria Docker**: ambos stacks = 16 contenedores. Con 16GB RAM host alcanza justo.
   Si hay presion de memoria, bajar celery-W/B del backup (no son necesarios para la demo).
2. **Vite HMR duplicado**: el navegador SI se conecta al Vite correcto (5173 o 5174 segun
   el puerto), pero si abres los DOS a la vez veras 2 sesiones Vite activas consumiendo CPU.
3. **pg_restore warnings**: el script filtra los warnings esperados pero algunos errores
   reales (constraints, sequences) pueden aparecer. Validar siempre con un query de conteo.
4. **El dump pesa ~120KB** (BD chica). Para QAS/PRD el dump pesara MBs y el restore
   tardara mas. El timeout del script es de 10 min, ajustable si hace falta.

---

## Cuando dejar de usar el backup

- Cuando termines la demo/reunion.
- Cuando quieras hacer cambios grandes en el codigo del original y necesites que el
  backup NO los refleje (apagar backup antes de tocar codigo).
- Cuando ya no necesites comparar "como estaba" vs "como esta".

Para apagarlo definitivamente: `scripts\stop-stack-backup.bat --purge`
(borra los volumenes, libera espacio en disco).
