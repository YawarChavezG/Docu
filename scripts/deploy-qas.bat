@echo off
REM ════════════════════════════════════════════════════════════════
REM COFAR SGD — Despliega codigo en QAS (sgdqas.cofar.com.bo)
REM
REM 1. Empaqueta codigo local (sin node_modules, .venv, etc.)
REM 2. Lo sube a /opt/sgd en QAS via scp
REM 3. Rebuild imagenes Docker (si hay cambios en Dockerfiles/requirements)
REM 4. Restart servicios (NO toca la BD a menos que se especifique --migrate)
REM 5. Invoca start-stack-qas.sh en el server (aplica seeds + sync AD
REM    si LDAP_ENABLED=true). Idempotente.
REM
REM Requisitos:
REM   - SSH key ya instalada (ver scripts/install-ssh-key-qas.ps1)
REM   - .env.qas ya en /opt/sgd/ (NO se commitea)
REM   - Docker ya instalado y corriendo en QAS (ver scripts/qas-setup-docker.sh)
REM
REM Uso:
REM   scripts\deploy-qas.bat                       (deploy + restart + seeds + sync AD)
REM   scripts\deploy-qas.bat --no-restart         (solo sube codigo, no restart)
REM   scripts\deploy-qas.bat --no-seed             (deploy + restart, sin correr seeds)
REM
REM Ver: docs/PR/DEPLOY-QAS.md
REM ════════════════════════════════════════════════════════════════

setlocal EnableDelayedExpansion

set REPO_ROOT=%~dp0..
set QAS_USER=sistemas
set QAS_HOST=sgdqas.cofar.com.bo
set QAS_DIR=/opt/sgd

REM ─── Args ───
set "DO_RESTART=1"
set "DO_SEED=1"
for %%a in (%*) do (
    if "%%a"=="--no-restart" set "DO_RESTART=0"
    if "%%a"=="--no-seed" set "DO_SEED=0"
)

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  COFAR SGD — Deploy a QAS                                       ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM ─── 1. Empaquetar codigo local (excluyendo pesados) ───
echo [1/6] Empaquetando codigo local...
set "TEMP_DIR=%TEMP%\sgd_deploy_%RANDOM%"
mkdir "!TEMP_DIR!" 2>nul
robocopy "%REPO_ROOT%\backend" "!TEMP_DIR!\backend" /E /XD node_modules .venv __pycache__ .git postgres_data redis_data .pytest_cache /XF celerybeat-schedule .coverage *.pid *.err *.out /NFL /NDL /NJH /NJS /NP >nul
robocopy "%REPO_ROOT%\frontend" "!TEMP_DIR!\frontend" /E /XD node_modules .git dist .agents .claude /worktrees /NFL /NDL /NJH /NJS /NP >nul
robocopy "%REPO_ROOT%\deploy" "!TEMP_DIR!\deploy" /E /NFL /NDL /NJH /NJS /NP >nul
robocopy "%REPO_ROOT%\scripts" "!TEMP_DIR!\scripts" /E /NFL /NDL /NJH /NJS /NP >nul
copy "%REPO_ROOT%\.env.example" "!TEMP_DIR!\.env.example" >nul
copy "%REPO_ROOT%\.gitignore" "!TEMP_DIR!\.gitignore" >nul

REM Zip con Python (usa /, no \)
python -c "import shutil; shutil.make_archive(r'!TEMP_DIR!', 'zip', r'!TEMP_DIR!')"
set "ZIP_PATH=!TEMP_DIR!.zip"
echo       OK: !ZIP_PATH!
echo.

REM ─── 2. Subir a QAS ───
echo [2/6] Subiendo ZIP a %QAS_USER%@%QAS_HOST%...
scp "!ZIP_PATH!" %QAS_USER%@%QAS_HOST%:/tmp/sgd_deploy.zip
if errorlevel 1 (
    echo [ERROR] Fallo scp. Verifica conectividad SSH.
    exit /b 1
)
echo       OK
echo.

REM ─── 3. Extraer en QAS (preserva .env.qas y ssl/) ───
echo [3/6] Extrayendo en QAS...
ssh %QAS_USER%@%QAS_HOST% "cd /opt/sgd && cp -a .env.qas /tmp/.env.qas.bak 2>/dev/null; cp -a deploy/nginx/ssl /tmp/ssl.bak 2>/dev/null; find . -mindepth 1 -path './backups' -prune -o -path './deploy/nginx/ssl' -prune -o -path './.env.qas' -prune -o -delete; python3 -c 'import zipfile; zipfile.ZipFile(chr(47)+chr(116)+chr(109)+chr(112)+chr(47)+chr(115)+chr(103)+chr(100)+chr(95)+chr(100)+chr(101)+chr(112)+chr(108)+chr(111)+chr(121)+chr(46)+chr(122)+chr(105)+chr(112)).extractall(chr(46))'; cp -a /tmp/.env.qas.bak .env.qas 2>/dev/null; mkdir -p deploy/nginx/ssl && cp -a /tmp/ssl.bak/. deploy/nginx/ssl/ 2>/dev/null; chmod +x scripts/*.sh 2>/dev/null; rm -f /tmp/sgd_deploy.zip /tmp/.env.qas.bak; echo OK_EXTRACT"
echo.

REM ─── 3.5. Renombrar sgd-qas.conf.bk a .conf (FIX 1) ──────────────
REM    El repo tiene sgd-qas.conf con sufijo .bk para que nginx en DES
REM    no lo cargue (ahi corre sgd.conf catch-all). Pero al deployar a
REM    QAS, nginx solo carga archivos *.conf (no *.conf.bk), por lo
REM    que sin este rename QAS queda sin server block -> ERR_CONNECTION_REFUSED.
echo [3.5/6] Renombrando sgd-qas.conf.bk -> .conf para nginx...
ssh %QAS_USER%@%QAS_HOST% "cd /opt/sgd && if [ -f deploy/nginx/conf.d/sgd-qas.conf.bk ]; then mv deploy/nginx/conf.d/sgd-qas.conf.bk deploy/nginx/conf.d/sgd-qas.conf; echo RENAMED_BK_TO_CONF; else echo ALREADY_CONF_OR_MISSING; fi"
echo.

REM ─── 4. Rebuild imagenes si hay cambios ───
echo [4/6] Rebuild imagenes Docker (si hay cambios)...
ssh %QAS_USER%@%QAS_HOST% "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml --env-file .env.qas build --pull --no-cache backend celery-worker celery-beat frontend 2>&1 | tail -10"
if errorlevel 1 (
    echo [WARN] Rebuild con warnings. Continuando.
)
echo.

REM ─── 5. Restart servicios (si --no-restart NO fue pasado) ───
if "%DO_RESTART%"=="1" (
    echo [5/6] Reiniciando servicios...
    ssh %QAS_USER%@%QAS_HOST% "cd /opt/sgd && docker compose -f deploy/docker-compose.qas.yml --env-file .env.qas up -d"
    echo       Esperando health checks...
    ssh %QAS_USER%@%QAS_HOST% "for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do sleep 3; if curl -fsS -k https://localhost/api/v1/health 2>/dev/null; then echo; echo BACKEND_READY; break; fi; echo -n '.'; done"
    echo.
) else (
    echo [5/6] SKIP restart (--no-restart especificado)
)

REM ─── 6. Invocar start-stack-qas.sh (seeds + sync AD + URLs) ───
if "%DO_SEED%"=="1" (
    if "%DO_RESTART%"=="0" (
        echo [6/6] SKIP start-stack-qas.sh (--no-restart, no se reinicio nada)
        echo       Para correr manualmente: ssh %QAS_USER%@%QAS_HOST% "bash /opt/sgd/scripts/start-stack-qas.sh"
    ) else (
        echo [6/6] Corriendo start-stack-qas.sh (seeds + sync AD + URLs)...
        echo       Esto aplica los 7 seeds idempotentes y, si LDAP_ENABLED=true,
        echo       genera el CSV desde el AD de COFAR.
        echo.
        ssh %QAS_USER%@%QAS_HOST% "bash /opt/sgd/scripts/start-stack-qas.sh"
        if errorlevel 1 (
            echo [WARN] start-stack-qas.sh reporto errores. Revisar arriba.
            echo        Si los seeds fallaron pero la app esta Up, se puede reintentar:
            echo          ssh %QAS_USER%@%QAS_HOST% "bash /opt/sgd/scripts/start-stack-qas.sh"
        )
    )
) else (
    echo [6/6] SKIP seeds (--no-seed especificado)
    echo       Para correr manualmente: ssh %QAS_USER%@%QAS_HOST% "bash /opt/sgd/scripts/start-stack-qas.sh"
)

echo.
echo   ╔════════════════════════════════════════════════════════╗
echo   ║  QAS desplegado                                       ║
echo   ║                                                        ║
echo   ║  App:        https://sgdqas.cofar.com.bo               ║
echo   ║  Health:     https://sgdqas.cofar.com.bo/api/v1/health ║
echo   ║  Logs:       docker compose -f deploy/docker-compose.qas.yml logs -f
echo   ╚════════════════════════════════════════════════════════╝
echo.

REM ─── Cleanup local ───
rd /s /q "!TEMP_DIR!" 2>nul
del /f /q "!ZIP_PATH!" 2>nul

endlocal
