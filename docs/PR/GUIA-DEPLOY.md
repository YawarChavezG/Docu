# GUÍA DE DEPLOY — COFAR SGD

> **Documento definitivo para desplegar código a QAS.**
> Cubre: CI (validación automática en GitHub) + CD (deploy manual con `deploy_qas.py`)
> 
> **Versión:** 1.2.0-qas (Junio 2026)
> **Mantenedor:** Equipo SGD

---

## Índice

1. [Arquitectura de Deploy](#1-arquitectura-de-deploy)
2. [Requisitos](#2-requisitos)
3. [Flujo completo paso a paso](#3-flujo-completo-paso-a-paso)
4. [El script deploy_qas.py](#4-el-script-deploy_qaspy)
5. [Validación CI en GitHub Actions](#5-validación-ci-en-github-actions)
6. [Referencia rápida de comandos](#6-referencia-rápida-de-comandos)
7. [Solución de problemas](#7-solución-de-problemas)
8. [Learnings & Errores Conocidos](#8-learnings--errores-conocidos)
9. [Arquitectura futura: CI/CD completo](#9-arquitectura-futura-cicd-completo)

---

## 1. Arquitectura de Deploy

```
DES (tu laptop Windows)
  │
  ├─ Código, commits, pruebas locales
  │
  ├─ [1] git tag vX.Y.Z-qas && git push origin vX.Y.Z-qas
  │     └─ GitHub Actions: CI (migrations + tests en BD PostgreSQL fresh)
  │         └─ Si falla → ❌ Corregir, NO deployar
  │
  ├─ [2] python scripts\deploy_qas.py --skip-validation
  │     └─ Backup BD → SCP código → Rebuild → Restart → Seeds → Validate
  │         └─ 38/38 PASS → ✅ QAS actualizado
  │
  QAS (sgdqas.cofar.com.bo / 10.11.0.11)
      └─ Debian 12, Docker, 30 tablas, 754 usuarios
```

### Por qué CI + deploy manual (y no deploy automático)

QAS está en la red interna de COFAR (`10.11.0.11`). GitHub Actions (nube pública) **no puede iniciar conexión SSH** hacia QAS porque la IP es privada. Soluciones:

| Opción | Estado |
|---|---|
| **CI en GitHub + deploy manual con script** | ✅ **Funciona HOY** (recomendado) |
| Self-hosted runner en QAS | Pendiente (cuando se necesite automatización total) |
| VPN / IP pública para QAS | Requiere gestión de infraestructura |

---

## 2. Requisitos

### En DES (tu laptop Windows)

| Requisito | Verificación |
|---|---|
| Git | `git --version` |
| Python 3.12+ | `python --version` |
| .venv en `backend/` | `ls backend\.venv\Scripts\python.exe` |
| Dependencias instaladas | `cd backend && pip install -r requirements/base.txt` |
| pytest pasa | `cd backend && python -m pytest tests/ -q` → 337 passed |
| Docker Desktop | `docker info` → Server Version |
| SSH key instalada | `ssh sistemas@sgdqas.cofar.com.bo "echo OK"` |

### En QAS (servidor)

| Requisito | Versión |
|---|---|
| OS | Debian 12 (bookworm) |
| Docker | 29.5.3 |
| Docker Compose | v5.1.4 |
| Python | 3.11.2 |
| Git | 2.39.5 |
| Disco | 14G/245G usado (6%) |
| RAM | 1.4G/15G usado |
| 8 contenedores | ✅ Todos healthy |

---

## 3. Flujo completo paso a paso

### Paso 0: Desarrollo local en DES

```powershell
# Trabajar normalmente en tu rama
git checkout r3/workflow-revision-aprobacion
# ... hacer cambios, agregar migrations, tests, etc.
```

### Paso 1: Validación pre-deploy (local)

```powershell
# 1.1 Verificar que migrations se aplican (entrypoint CI)
docker exec sgd-backend env ENVIRONMENT=ci bash scripts/entrypoint.sh
# Debe mostrar: "[ENTRYPOINT] Migraciones aplicadas correctamente."
# Si falla → hay error de migration, corregir antes de deployar

# 1.2 Verificar que tests pasan
cd backend
.venv\Scripts\python -m pytest tests/ -q --tb=short
# Debe mostrar: "337 passed"
```

### Paso 2: Tag + CI en GitHub

```powershell
# 2.1 Commit y push
git add -A
git commit -m "feat: descripción de los cambios"
git push origin r3/workflow-revision-aprobacion

# 2.2 Crear tag y pushear (dispara el CI en GitHub)
git tag vX.Y.Z-qas
git push origin vX.Y.Z-qas

# 2.3 Verificar CI en GitHub
# Ir a: https://github.com/YawarChavezG/Docu/actions
# Verificar que el workflow "Deploy a QAS" se ejecuta y pasa:
#   ✓ CI - Validar migrations + tests (1m:10s)
#   ✓ CD - Deploy a QAS (se salta porque no hay runner en QAS)
```

### Paso 3: Deploy a QAS

```powershell
# 3.1 Ejecutar deploy (sin validación porque CI ya validó)
python scripts\deploy_qas.py --skip-validation
# Salida esperada:
#   ✓ 12/12 PASS
#   ✓ QAS: https://sgdqas.cofar.com.bo
```

### Paso 4: Verificar QAS

```powershell
ssh sistemas@sgdqas.cofar.com.bo "bash /opt/sgd/scripts/validate-qas.sh"
# Debe mostrar: "38/38 PASS, 0 FAIL, 0 WARN"
#  ✓ QAS OK. Todas las validaciones criticas PASS.
```

---

## 4. El script `deploy_qas.py`

### Ubicación
`scripts/deploy_qas.py`

### Qué hace (10 fases)

| Fase | Descripción | Si falla |
|---|---|---|
| 0. PRE-VALIDACION | Entrypoint CI + pytest | ❌ Aborta, NO toca QAS |
| 1. BACKUP | pg_dump de BD QAS | ❌ Aborta |
| 2. EMPAQUETAR | Crea ZIP con código | ❌ Aborta |
| 3. EXTRAER | SCP + Python extract en QAS | ❌ Aborta |
| 4. REBUILD | docker compose build (4 imágenes) | ⚠️ Warn, continúa |
| 5. RESTART | docker compose up -d + nginx | ❌ Aborta |
| 6. HEALTH | Espera HTTPS 200 OK | ❌ Aborta |
| 7. SEEDS | 12 seeds + sync AD | ⚠️ Reintento |
| 8. VALIDAR | validate-qas.sh (38 checks) | ❌ Aborta + auto-fix K.3 |
| 9. CLEANUP | Builder prune + temporales | Siempre OK |

### Uso

```powershell
# Deploy completo (con validación local)
python scripts\deploy_qas.py

# Solo deploy (sin validación local, si CI ya pasó)
python scripts\deploy_qas.py --skip-validation

# Simular (no ejecuta nada)
python scripts\deploy_qas.py --dry-run
```

---

## 5. Validación CI en GitHub Actions

El workflow `.github/workflows/deploy-qas.yml` se activa automáticamente al pushear un tag `v*-qas`.

### Qué valida el CI

```
1. Crea BD PostgreSQL 16 fresh (servicio Docker)
2. Instala dependencias (requirements/base.txt)
3. Corre alembic upgrade head
4. Corre entrypoint en modo CI
5. Corre pytest (340+ tests)
```

### Qué NO hace (por diseño)

❌ **No deploya a QAS automáticamente** — porque GitHub no llega a la red interna.
✅ **Valida que el tag sea seguro para deployar.**

### Cómo ver el resultado

```
https://github.com/YawarChavezG/Docu/actions
```

---

## 6. Referencia rápida de comandos

### Deploy

```powershell
# Rápido (si CI ya pasó)
python scripts\deploy_qas.py --skip-validation

# Completo (con validación local)
python scripts\deploy_qas.py

# Simulación
python scripts\deploy_qas.py --dry-run
```

### Validación

```powershell
# Validar migrations local
docker exec sgd-backend env ENVIRONMENT=ci bash scripts/entrypoint.sh

# Tests
cd backend && .venv\Scripts\python -m pytest tests/ -q

# Validar QAS post-deploy
ssh sistemas@sgdqas.cofar.com.bo "bash /opt/sgd/scripts/validate-qas.sh"
```

### Git

```powershell
git tag vX.Y.Z-qas && git push origin vX.Y.Z-qas    # Dispara CI
git push --delete origin vX.Y.Z-qas                  # Borrar tag remoto
git tag -d vX.Y.Z-qas                                 # Borrar tag local
```

---

## 7. Solución de problemas

### Error: PostgreSQL no responde tras 30s

**Causa:** El entrypoint espera a PostgreSQL pero no encuentra el host.
**Fix:** Asegurar `POSTGRES_HOST` esté configurado:
- En Docker Compose (DES/QAS): `POSTGRES_HOST=postgres`
- En CI (GitHub Actions): `POSTGRES_HOST=localhost` (job en runner)

### Error: `on: push tags:` no funciona

**Causa:** Bug en GitHub Actions con el trigger `on: push tags:`.
**Fix:** Usar `on: push` con `if: startsWith(github.ref, 'refs/tags/v')`.

### Error: Merge conflict en deploy-qas.yml

**Causa:** `git stash` + `git checkout` entre ramas deja marcadores.
**Fix:** `git add .github/workflows/deploy-qas.yml` y commitear.

### Error: SCP falla con "Permission denied"

**Causa:** La clave SSH privada no se carga correctamente.
**Fix:** Usar `appleboy/ssh-action` que maneja la key automáticamente.

### Error: Docker compose build tarda mucho

**Causa:** El timeout del SSH action es muy corto.
**Fix:** Agregar `command_timeout: 600s` al step.

---

## 8. Learnings & Errores Conocidos

> Ver `docs/PR/LEARNINGS-ERRORES.md` para la lista completa.

### Categoría Base de Datos

- **B15**: `sa.Enum(name=X)` en migration falla si el ENUM ya existe en PG. Usar `sa.String()`.
- **D06**: Eliminar valores de un enum sin migrar datos legacy causa `LookupError`.

### Categoría Docker / Infraestructura

- **X09**: Asimetría DES vs QAS en entrypoint: `||` en DES oculta errores de migration.

### Categoría CI/CD

- **C01**: `on: push tags:` con `+` en glob patterns no funciona como se espera.
- **C02**: Merge conflicts pueden corromper el workflow YAML silenciosamente.
- **C03**: El runner de GitHub no puede acceder a IPs privadas (10.x.x.x).

---

## 9. Arquitectura futura: CI/CD completo

Para lograr deploy automático (sin intervención manual), hay 2 caminos:

### Opción A: Self-hosted runner en QAS (recomendada)

Instalar un runner de GitHub Actions dentro de la red COFAR:

```bash
ssh sistemas@sgdqas.cofar.com.bo
curl -O https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64-2.322.0.tar.gz
tar xzf actions-runner-linux-x64-2.322.0.tar.gz
./config.sh --url https://github.com/YawarChavezG/Docu --token <REG_TOKEN>
sudo ./svc.sh install && sudo ./svc.sh start
```

**Ventaja:** El workflow corre en QAS, puede acceder a Docker, BD, etc.
**Desventaja:** Hay que generar un token de registro desde GitHub.

### Opción B: Pull-based deploy

QAS verifica periódicamente si hay nuevos tags y se autodeploya:

```bash
# Cron job en QAS (cada 10 minutos)
#!/bin/bash
TAG=$(curl -s https://api.github.com/repos/YawarChavezG/Docu/git/refs/tags | \
  python3 -c "import sys,json; print(json.load(sys.stdin)[-1]['ref'].split('/')[-1])")
if [ -f /opt/sgd/.last_tag ] && [ "$(cat /opt/sgd/.last_tag)" = "$TAG" ]; then exit 0; fi
echo "$TAG" > /opt/sgd/.last_tag
cd /opt/sgd && git fetch origin refs/tags/$TAG && git checkout FETCH_HEAD
docker compose -f deploy/docker-compose.qas.yml --env-file .env.qas build
docker compose -f deploy/docker-compose.qas.yml --env-file .env.qas up -d
```

**Ventaja:** No requiere configuración de GitHub.
**Desventaja:** No es instantáneo (delay de hasta 10 min).

---

## Historial de cambios

| Fecha | Versión | Cambio |
|---|---|---|
| 2026-06-20 | v1.2.0-qas | Documentación inicial del pipeline CI/CD + deploy manual |
| 2026-06-20 | v1.3.0-qas | CI funcional, CD pendiente de self-hosted runner |
