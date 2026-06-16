# DEPLOY QAS — Cómo migrar código al servidor QAS

> **TL;DR:**
> - Para deployar cambios: `scripts\deploy-qas.bat` (desde la laptop)
> - Para ver logs: `ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml logs -f"`
> - Para entrar al QAS: `ssh sistemas@sgdqas.cofar.com.bo`
> - URL: **https://sgdqas.cofar.com.bo** (HTTPS con cert autofirmado)
>
> **Server:** SRVQAS-SIGDOC (10.11.0.11), Debian 12, 2 vCPU, 16GB RAM, 250GB disco

---

## 1. Setup inicial (ya hecho en sesion 10, 2026-06-16)

| Item | Estado | Notas |
|---|---|---|
| SSH key (laptop → QAS) | ✅ Instalada | `~/.ssh/id_rsa.pub` en `/home/sistemas/.ssh/authorized_keys` |
| Sudo NOPASSWD | ✅ Instalado | `/etc/sudoers.d/sistemas-nopasswd` |
| Docker + compose | ✅ Instalado | Docker 29.5.3, Compose v5.1.4 |
| DNS COFAR | ✅ Config | `172.16.10.50, 172.16.10.51, 8.8.8.8, 1.1.1.1` en `/etc/resolv.conf` |
| Codigo en /opt/sgd | ✅ Copiado | 369 archivos, sin node_modules/.venv/etc |
| Cert autofirmado | ✅ Generado | `deploy/nginx/ssl/sgdqas.{crt,key}` (365 dias, SAN para sgdqas.cofar.com.bo + 10.11.0.11) |
| .env.qas | ✅ Config | En `/opt/sgd/.env.qas` (NO en git, chmod 600) |
| Stack corriendo | ✅ 8/8 servicios | nginx (80+443), backend, postgres, redis, mailhog, celery-W, celery-B, frontend |
| BD sembrada | ✅ 5 users, 10 ger, 50 areas, 13 tipos, 5 estados, 20 feriados | + seeds email/matriz |
| AD real (COFAR) | ✅ Config | Mismo RODC que DES (172.16.10.17), funcional en corp network |

---

## 2. Arquitectura del deploy

```
LAPTOP (DES)                                  QAS (Debian 12)
C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES\    sgdqas.cofar.com.bo (10.11.0.11)
                                            
scripts\deploy-qas.bat ─── tar+scp ─────────> /opt/sgd/
   (excluye node_modules,                      ├── backend/  (Python source)
    .venv, __pycache__)                        ├── frontend/ (JS source)
                                                ├── deploy/   (compose, nginx, ssl)
   ssh + docker compose                        ├── scripts/  (seed_*, etc)
   build + up -d                                ├── .env.qas  (chmod 600, NO git)
                                                ├── backups/
                                                └── deploy/
                                                    ├── docker-compose.qas.yml
                                                    ├── nginx/conf.d/sgd-qas.conf
                                                    └── nginx/ssl/sgdqas.{crt,key}

                                              8 contenedores Docker:
                                              sgd-qas-postgres, sgd-qas-redis, sgd-qas-backend,
                                              sgd-qas-frontend, sgd-qas-nginx, sgd-qas-mailhog,
                                              sgd-qas-celery-worker, sgd-qas-celery-beat
```

---

## 3. Workflow de migración (cómo deployar nuevos features)

### Paso 1: desarrollar en DES (laptop)

1. Editar codigo en `C:\Users\ychavez\PROYECTOS-DOCKER\SGD-DES\`
2. Validar localmente con `scripts\start-stack-des.bat`
3. Commit con conventional commit:
   ```bash
   git add .
   git commit -m "feat(backend): nuevo endpoint X"
   ```

### Paso 2: deployar a QAS

**Desde la laptop:**

```cmd
scripts\deploy-qas.bat
```

Esto hace automaticamente:
1. Empaqueta el codigo local (excluyendo node_modules, .venv, etc.)
2. Lo sube a QAS via scp a `/tmp/sgd_deploy.zip`
3. Extrae en `/opt/sgd/` (preserva `.env.qas` y `ssl/`)
4. Rebuild imagenes Docker (`docker compose build`)
5. `docker compose up -d` (restart servicios)
6. Espera al health check

**Tiempo:** 1-3 minutos (depende de si hay cambios en Dockerfiles/requirements).

### Paso 3: validar en QAS

**Health check (sin browser):**
```cmd
curl -sk https://sgdqas.cofar.com.bo/api/v1/health
```

**Login test:**
```cmd
echo {"username":"aromero","password":"cofar.2026","auth_source":"local"} > %TEMP%\login.json
curl -sk -X POST https://sgdqas.cofar.com.bo/api/v1/login -H "Content-Type: application/json" -d @%TEMP%\login.json
```

**Browser:** https://sgdqas.cofar.com.bo (cert autofirmado, click "Avanzado" → "Continuar")

**Logs en vivo:**
```cmd
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml logs -f backend"
```

### Paso 4: migracion de BD (si hubo cambios en modelos)

El backend ejecuta `alembic upgrade head` automaticamente en cada startup. Si agregaste una migracion nueva:

```cmd
REM Opcion A: deploy normal (backend corre alembic al arrancar)
scripts\deploy-qas.bat

REM Opcion B: forzar solo migracion (sin deploy de codigo)
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker exec sgd-qas-backend alembic upgrade head"
```

### Paso 5: rollback si algo sale mal

```cmd
REM El deploy NO borra datos, solo actualiza imagenes y reinicia containers.
REM Para volver atras un commit:
git checkout HEAD~1
scripts\deploy-qas.bat
git checkout -

REM La BD NO se toca. Si hay una migracion que rompio, podes hacer downgrade:
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker exec sgd-qas-backend alembic downgrade -1"
```

---

## 4. Comandos utiles (cheat sheet)

### Ver estado del stack
```bash
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml ps"
```

### Ver logs de un servicio
```bash
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml logs -f --tail 100 backend"
# Cambiar "backend" por: postgres, redis, nginx, frontend, mailhog, celery-worker, celery-beat
```

### Reiniciar un servicio
```bash
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml restart backend"
```

### Conectarse a la BD
```bash
ssh sistemas@sgdqas.cofar.com.bo "docker exec -it sgd-qas-postgres psql -U sgd -d sgd"
```

### Correr un seed
```bash
ssh sistemas@sgdqas.cofar.com.bo "docker exec sgd-qas-backend python /app/scripts/seed_data.py"
```

### Backup rapido de la BD
```bash
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker exec sgd-qas-postgres pg_dump -U sgd -d sgd -Fc -f /tmp/qas_backup.dump && docker cp sgd-qas-postgres:/tmp/qas_backup.dump /opt/sgd/backups/qas_$(date +%Y%m%d).dump"
```

### Ver espacio en disco
```bash
ssh sistemas@sgdqas.cofar.com.bo "df -h /opt/sgd && du -sh /opt/sgd/*/ | sort -h"
```

### Ver memoria y CPU
```bash
ssh sistemas@sgdqas.cofar.com.bo "docker stats --no-stream"
```

---

## 5. Troubleshooting

### "container name already in use" en restart
```bash
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml down"
# NO usar -v (eso borra volumenes/BD)
scripts\deploy-qas.bat
```

### "ECONNREFUSED 172.16.10.17:389" (LDAP no reachable)
El contenedor no llega al AD. Causas:
- No esta en la red corporativa (verificar VPN)
- DNS no resuelve el dominio
- Firewall del corp bloquea el puerto 389

**Fix temporal:** cambiar a `LDAP_ENABLED=false` en `.env.qas` y reiniciar:
```bash
ssh sistemas@sgdqas.cofar.com.bo "sed -i 's/^LDAP_ENABLED=true/LDAP_ENABLED=false/' /opt/sgd/.env.qas && cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml restart backend"
```

### El browser dice "certificado invalido"
Es esperado, el cert es autofirmado. Click en "Avanzado" → "Continuar a sgdqas.cofar.com.bo".

### Nginx no arranca: "bind() to 0.0.0.0:80 failed"
Otro proceso usa el puerto. Ver:
```bash
ssh sistemas@sgdqas.cofar.com.bo "ss -tlnp | grep -E ':80|:443'"
```

### Backend reinicia en loop
```bash
ssh sistemas@sgdqas.cofar.com.bo "docker logs sgd-qas-backend --tail 50"
```

### Celery-beat en restart loop
```bash
ssh sistemas@sgdqas.cofar.com.bo "docker logs sgd-qas-celery-beat --tail 30"
```
Causa comun: error de import. Verificar logs.

### Celery-beat "Permission denied: celerybeat-schedule"
El fix `-s /app/storage/celerybeat-schedule` ya esta aplicado en la version actual.
Si vuelve a aparecer, verificar que el comando del container incluye `-s /app/storage/celerybeat-schedule`.

---

## 6. Arquitectura de seguridad

### IMPORTANTE — lee esto antes de hacer cambios

1. **La password del server esta en texto plano** (`D3s4rr0*2026*` en este chat).
   - **Recomendacion:** cambiar la password y migrar a SSH key-only auth.
   - Mientras tanto, NOPASSWD sudo + SSH key ya esta configurado (la password solo se usa para login inicial).

2. **El cert es autofirmado.**
   - Los browsers mostraran warning.
   - Aceptable para QAS interno, NO para produccion.
   - En PROD, usar cert valido (Let's Encrypt o cert corporativo de COFAR).

3. **El `.env.qas` tiene secretos en texto plano.**
   - JWT secret: random de 32 bytes (unico por entorno)
   - POSTGRES password: random de 16 chars (unico por entorno)
   - LDAP_BIND_PASSWORD: misma que DES (es el service account de COFAR, no es del server)
   - **NO commitear este archivo.** Ya esta en `.gitignore` via chmod 600.

4. **NOPASSWD sudo es amplio** (`sistemas ALL=(ALL) NOPASSWD: ALL`).
   - Aceptable para QAS (1 user, 1 server).
   - En PROD, restringir a comandos especificos (apt, systemctl, etc).

5. **DNS a 172.16.10.17 (RODC) hardcodeado** en .env.qas.
   - Si el corp cambia la IP del RODC, hay que actualizar.
   - Alternativa: usar DNS interno (`dc3-cofar.com` o `rodc.cofar.com.bo`) que ya esta en `dns_search: cofar.com`.

---

## 7. Backup de QAS

### Backup manual (cuando quieras)
```bash
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker exec sgd-qas-postgres pg_dump -U sgd -d sgd -Fc -f /tmp/qas_backup.dump && docker cp sgd-qas-postgres:/tmp/qas_backup.dump /opt/sgd/backups/qas_$(date +%Y%m%d_%H%M%S).dump"
```

### Backup automatico (cron, recomendado para PROD)
En QAS como sistemas:
```bash
ssh sistemas@sgdqas.cofar.com.bo
crontab -e
# Agregar linea (todos los dias a las 02:00):
0 2 * * * cd /opt/sgd && docker exec sgd-qas-postgres pg_dump -U sgd -d sgd -Fc -f /tmp/qas_backup.dump && docker cp sgd-qas-postgres:/tmp/qas_backup.dump /opt/sgd/backups/qas_$(date +\%Y\%m\%d).dump && find /opt/sgd/backups -mtime +30 -delete
```

### Restaurar un backup
```bash
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker cp backups/qas_20260616.dump sgd-qas-postgres:/tmp/restore.dump && docker exec sgd-qas-postgres pg_restore -U sgd -d sgd --clean --if-exists --no-owner --role=sgd /tmp/restore.dump"
```

---

## 8. Migrar a PROD (cuando llegue el momento)

QAS es la antesala de PROD. El deploy a PROD sera similar pero con:
- Cert HTTPS valido (no autofirmado)
- DNS publico (no `sgdqas.cofar.com.bo` interno)
- JWT secret y POSTGRES password diferentes
- LDAP apuntando al PDC (no RODC)
- Backups automaticos configurados
- Monitoring (Prometheus, Grafana, etc)

El `scripts/deploy-qas.bat` se puede generalizar a `scripts/deploy-{env}.bat`
aceptando el entorno como parametro.

---

## 9. Archivos clave en QAS

| Path local (laptop) | Path en QAS | Funcion |
|---|---|---|
| `deploy/docker-compose.qas.yml` | `/opt/sgd/deploy/docker-compose.qas.yml` | Compose del stack QAS |
| `deploy/nginx/conf.d/sgd-qas.conf` | `/opt/sgd/deploy/nginx/conf.d/sgd-qas.conf` | Config nginx HTTPS |
| `scripts/qas-setup-docker.sh` | `/opt/sgd/scripts/qas-setup-docker.sh` | Setup inicial de Docker (ejecutar UNA vez) |
| `scripts/deploy-qas.bat` | N/A (corre en laptop) | Deploy nuevos features |
| N/A | `/opt/sgd/.env.qas` | Variables de entorno (NO en git) |
| N/A | `/opt/sgd/deploy/nginx/ssl/sgdqas.crt` | Cert autofirmado |
| N/A | `/opt/sgd/deploy/nginx/ssl/sgdqas.key` | Key del cert |
| N/A | `/opt/sgd/backups/` | Backups de BD |

---

## 10. Comandos para tu reunion

Para mostrar el deploy funcionando en la reunion:

```cmd
REM Abrir browser
start https://sgdqas.cofar.com.bo

REM Login
echo {"username":"aromero","password":"cofar.2026","auth_source":"local"} > %TEMP%\login.json
curl -sk -X POST https://sgdqas.cofar.com.bo/api/v1/login -H "Content-Type: application/json" -d @%TEMP%\login.json

REM Health check
curl -sk https://sgdqas.cofar.com.bo/api/v1/health

REM Ver logs en vivo (para impresionar)
ssh sistemas@sgdqas.cofar.com.bo "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml ps"
```

---

## 11. Para recordar

- **QAS URL:** https://sgdqas.cofar.com.bo
- **Stubs login:** aromero / cofar.2026 (rol ETO)
- **Server:** sgdqas.cofar.com.bo = 10.11.0.11 (usuario: sistemas)
- **BD:** postgres 16, db=sgd, user=sgd
- **Stack name prefix:** `sgd-qas-*` (NO `sgd-` ni `sgd-bk-`)
- **Volumenes:** `sgd-qas_*` (vs `sgd-des_*` local, `sgd-des-bk_*` backup)
- **NUNCA** commitear `.env.qas` ni `nginx/ssl/sgdqas.key`
