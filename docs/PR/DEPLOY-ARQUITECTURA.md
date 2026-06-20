# ARQUITECTURA DE DEPLOY — COFAR SGD

> **Ultima actualizacion:** 2026-06-20 (sesion 39 — CI/CD pipeline + entrypoint unificado)
> **Objetivo:** Deploys predecibles, automatizados, sin sorpresas en QAS.

---

## 1. Filosofia

### Antes (sesiones 1-38)
```
Codigo en DES  ──> commit ──> tag ──> deploy-qas.bat ──> ???? ──> QAS roto
                                       (zip + scp + rebuild + restart)
```
Los errores de migration se ocultaban en DES por el `||` en el entrypoint.
Solo se detectaban en QAS, donde el `&&` hacia fallar el startup.

### Despues (sesion 39+)
```
Codigo en DES  ──> git push tag ──> CI/CD Pipeline ──> QAS OK
                                        │
                                        ├─ 1. BD fresh + alembic upgrade head
                                        ├─ 2. pytest (337+ tests)
                                        ├─ 3. Build imagenes
                                        └─ 4. Deploy automatico a QAS
```

**Principio:** "Lo que pasa en CI, pasa en QAS." Si las migrations pasan
contra una BD PostgreSQL fresh en CI, pasaran en QAS. Si no, el tag se
rechaza antes de llegar a produccion.

---

## 2. Componentes

### 2.1 Entrypoint compartido (`backend/scripts/entrypoint.sh`)

Unico entrypoint para DES, QAS y CI. Reemplaza el `command:` inline
de ambos docker-compose.yml.

| Environment | Comportamiento |
|---|---|
| `development` | `alembic upgrade head` + `uvicorn --reload` |
| `qas` | `alembic upgrade head` + `uvicorn --workers 2` |
| `ci` | `alembic upgrade head` + exit 0 (no arranca servidor) |

**Regla:** Si `alembic upgrade head` falla, el entrypoint ABORTA.
No hay `||` que esconda errores. Esto aplica IGUAL en DES y QAS.

### 2.2 Pre-deploy validator (`scripts/validate-deploy.sh`)

Script local para validar ANTES de pushear un tag:
1. Crea BD PostgreSQL fresh en Docker (puerto 25433)
2. Corre `alembic upgrade head` (validacion real contra PG)
3. Corre entrypoint modo CI
4. Corre seeds clave

**Exit code:** 0 = OK, 1 = fallo (no deployar).

### 2.3 CI/CD Pipeline (`.github/workflows/deploy-qas.yml`)

Trigger: push de tag `v*-qas` (ej: `v1.1.1-qas`).

| Fase | Que hace | Detecta |
|---|---|---|
| **validate** | Crea BD fresh + alembic + pytest + seeds | Migraciones rotas, tests fallidos, seeds no idempotentes |
| **build** | Build + push imagenes a ghcr.io | Errores de build (Dockerfile, dependencias) |
| **deploy** | SSH a QAS → pull imagenes → restart → seeds → validate | Errores de configuracion en QAS |

### 2.4 Imagenes Docker en registro (ghcr.io)

Las imagenes ya no se construyen en QAS. Se construyen en CI y se
publican en GitHub Container Registry. QAS solo hace `docker pull`.

---

## 3. Flujo de trabajo para el desarrollador

Hay 3 opciones. La recomendada es la **Opcion B** (funciona hoy sin GitHub Actions).

### Opcion A: Con CI/CD (recomendado a futuro — requiere configurar GitHub Secrets una vez)

```
1. Desarrollo en DES
       │
2. pytest + entrypoint CI (validacion local)
       │
3. git tag vX.Y.Z-qas && git push origin vX.Y.Z-qas
       │
4. GitHub Actions ejecuta automaticamente:
       ├─ validate: BD fresh + alembic + pytest + seeds
       ├─ build: imagenes Docker a ghcr.io
       └─ deploy: SSH a QAS → pull + restart + seeds
       │
5. QAS actualizado
```

### Opcion B: Manual con validacion (recomendado HOY)

```
1. Desarrollo en DES
       │
2. cd backend && .venv\Scripts\python -m pytest tests/ -q
       │
3. docker exec sgd-backend env ENVIRONMENT=ci bash scripts/entrypoint.sh
   (Esto corre alembic upgrade head contra la BD real de DES.
    Si hay error de migration, lo ves AQUI, no en QAS)
       │
4. git add + git commit + git push
       │
5. git tag vX.Y.Z-qas && git push origin vX.Y.Z-qas
       │
6. .\scripts\deploy-qas.bat
       ├─ Backup BD
       ├─ Sube codigo
       ├─ Rebuild imagenes
       ├─ Restart servicios
       └─ start-stack-qas.sh (seeds + sync AD)
       │
7. ssh qas "bash /opt/sgd/scripts/validate-qas.sh"
   (38/38 PASS = deploy exitoso)
```

### Opcion C: Script todo-en-uno (validate-and-deploy.ps1)

```powershell
# Solo validar (recomendado antes de commitear)
.\scripts\validate-and-deploy.ps1

# Validar + crear tag + pushear
.\scripts\validate-and-deploy.ps1 -Tag v1.2.0-qas

# Validar + tag + deploy completo a QAS
.\scripts\validate-and-deploy.ps1 -Tag v1.2.0-qas -Deploy
```

### Checklist del desarrollador

| Que verificar | Como | Ataja errores como... |
|---|---|---|
| Tests pasan? | `cd backend && .venv\Scripts\python -m pytest tests/ -q` | Tests rotos |
| Migraciones funcionales? | `docker exec sgd-backend env ENVIRONMENT=ci bash scripts/entrypoint.sh` | `sa.Enum` conflict, `||` oculto |
| Entrypoint funciona? | `docker logs sgd-backend \| grep ENTRYPOINT` debe mostrar "Environment: development" | Entrypoint roto |
| QAS sano post-deploy? | `ssh qas "bash validate-qas.sh"` debe dar 38/38 PASS | Todo lo anterior |

---

## 4. Lo que ya no existe

| Antes | Ahora |
|---|---|
| `deploy-qas.bat` (zip + scp manual) | CI/CD automatico |
| `start-stack-qas.sh` (orquestador manual) | CI/CD orquesta todo |
| `||` en entrypoint DES (oculta errores) | `&&` en AMBOS (error fatal) |
| Dos entrypoints divergentes | Un solo `entrypoint.sh` |
| Seeds hardcodeados en bash | CI valida seeds automaticamente |

---

## 5. Como se previenen los 3 errores del deploy v1.1.1

| Error | Prevencion en la nueva arquitectura |
|---|---|
| `sa.Enum` crea type ya existente | CI crea BD fresh + alembic → detecta el `DuplicateObjectError` inmediatamente |
| `ContextoEstado.AMBOS` en datos legacy | CI valida seeds contra BD fresh → detecta `LookupError` |
| Asimetria DES vs QAS (`||` vs `&&`) | Entrypoint unico, mismo comportamiento en ambos entornos |

---

## 6. Configuracion inicial unica (primera vez)

```bash
# 1. Agregar secrets a GitHub (Settings > Secrets and variables > Actions)
#    - SSH_PRIVATE_KEY: clave privada SSH para sistemas@sgdqas.cofar.com.bo
#    - QAS_HOST: sgdqas.cofar.com.bo
#    - QAS_USER: sistemas

# 2. Verificar que ghcr.io esta habilitado
#    Settings > Packages > Packages: Enabled

# 3. En QAS, ajustar docker-compose.qas.yml para usar imagenes de ghcr.io
#    en vez de build local
```

---

## 7. Dependencias

| Componente | Version minima | Notas |
|---|---|---|
| PostgreSQL | 16-alpine | Fresh BD en CI |
| Python | 3.12 | Misma version que DES |
| Docker | 24+ | En QAS y runner CI |
| GitHub Actions | — | Incluido en plan gratis |
| ghcr.io | — | Incluido en GitHub |
