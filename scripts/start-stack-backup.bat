@echo off
REM ════════════════════════════════════════════════════════════════
REM COFAR SGD — Orquestador de stack BACKUP (paralelo al original)
REM
REM Levanta un entorno AISLADO del stack original en otros puertos.
REM Mismo codigo, BD restaurada desde un dump pg_dump, sin colisionar.
REM
REM   - Stack original: 8080 / 5173 / 18000 / 25432 / 26379
REM   - Stack backup:   8081 / 5174 / 18001 / 25433 / 26380
REM
REM Uso:
REM   scripts\start-stack-backup.bat                              (usa el dump mas reciente)
REM   scripts\start-stack-backup.bat backups\20260616_150015\sgd_pre_refactor.dump
REM
REM Detener:
REM   scripts\stop-stack-backup.bat
REM
REM Ver: docs/PR/BACKUP-PARALELO.md
REM ════════════════════════════════════════════════════════════════

setlocal EnableDelayedExpansion

set REPO_ROOT=%~dp0..
set SCRIPTS_DIR=%~dp0
set DEPLOY_DIR=%REPO_ROOT%\deploy

REM ─── Resolver path del dump ───
if "%~1"=="" (
    REM Buscar el backup mas reciente por timestamp
    set "DUMP_REL="
    for /f "delims=" %%d in ('dir /b /ad /o-n "%REPO_ROOT%\backups" 2^>nul') do (
        if "!DUMP_REL!"=="" set "DUMP_REL=%%d"
    )
    if "!DUMP_REL!"=="" (
        echo [ERROR] No hay directorios en backups\. Crea uno con pg_dump primero.
        echo         Ejemplo: docker exec sgd-postgres pg_dump -U sgd -d sgd -Fc -f /tmp/x.dump ^&^& docker cp sgd-postgres:/tmp/x.dump backups\MANUAL\x.dump
        exit /b 1
    )
    set "DUMP_PATH=%REPO_ROOT%\backups\!DUMP_REL!\sgd_pre_refactor.dump"
) else (
    set "DUMP_PATH=%~1"
)

if not exist "%DUMP_PATH%" (
    echo [ERROR] No existe el dump: %DUMP_PATH%
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  COFAR SGD — Stack BACKUP (paralelo al original)                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Dump a restaurar: %DUMP_PATH%
echo.

REM ─── 1. Prerequisitos ───
echo [1/6] Verificando prerequisitos...

if not exist "%REPO_ROOT%\.env.backup" (
    echo [ERROR] No existe %REPO_ROOT%\.env.backup
    echo         Copialo desde .env y ajusta los puertos.
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop no esta corriendo.
    exit /b 1
)

echo       OK: .env.backup existe, Docker up, dump presente
echo.

REM ─── 2. Levantar SOLO postgres y redis primero (para crear volumenes y DB) ───
echo [2/6] Levantando postgres + redis del stack backup (volumenes nuevos)...
cd /d "%REPO_ROOT%"
docker compose -f deploy/docker-compose.backup.yml --env-file .env.backup up -d postgres redis
if errorlevel 1 (
    echo [ERROR] Fallo al levantar postgres/redis del backup.
    exit /b 1
)
echo       OK: 2 contenedores iniciandose
echo.

REM ─── 3. Esperar postgres healthy ───
echo [3/6] Esperando PostgreSQL backup (puerto 25433)...
:wait_pg_bk
timeout /t 2 /nobreak >nul
docker exec sgd-bk-postgres pg_isready -U sgd -d sgd_backup >nul 2>&1
if errorlevel 1 goto wait_pg_bk
echo       OK: PostgreSQL backup ready
echo.

REM ─── 4. Restaurar dump en sgd_backup ───
echo [4/6] Restaurando dump en sgd_backup...
echo       Copiando dump al contenedor...
docker cp "%DUMP_PATH%" sgd-bk-postgres:/tmp/sgd_pre_refactor.dump
if errorlevel 1 (
    echo [ERROR] No se pudo copiar el dump al contenedor.
    exit /b 1
)
echo       Aplicando pg_restore (puede tardar 1-3 min)...
docker exec sgd-bk-postgres pg_restore -U sgd -d sgd_backup --no-owner --role=sgd --clean --if-exists /tmp/sgd_pre_refactor.dump 2>&1 | findstr /v "WARNING\|pg_restore: warning" | findstr /v "^$" | findstr /v "pg_restore: from TOC entry"
if errorlevel 1 (
    echo [WARN] pg_restore reporto errores. Verificar con: docker exec sgd-bk-postgres psql -U sgd -d sgd_backup -c "SELECT count(*) FROM usuarios"
)
docker exec sgd-bk-postgres rm -f /tmp/sgd_pre_refactor.dump
echo       OK: dump restaurado
echo.

REM ─── 5. Levantar el resto de la stack ───
echo [5/6] Levantando backend, celery-W, celery-B, frontend, nginx, mailhog...
docker compose -f deploy/docker-compose.backup.yml --env-file .env.backup up -d
if errorlevel 1 (
    echo [ERROR] Fallo al levantar el resto del stack.
    exit /b 1
)
echo       OK: 8 contenedores iniciandose
echo.

REM ─── 6. Esperar backend healthy ───
echo [6/6] Esperando backend backup (puerto 18001)...
:wait_backend_bk
timeout /t 2 /nobreak >nul
curl.exe -fsS http://localhost:18001/api/v1/health >nul 2>&1
if errorlevel 1 goto wait_backend_bk
echo       OK: Backend backup ready
echo.

echo   ╔════════════════════════════════════════════════════════╗
echo   ║  Stack BACKUP (paralelo al original)                  ║
echo   ║                                                        ║
echo   ║  App (Nginx)    http://localhost:8081                  ║
echo   ║  Frontend       http://localhost:5174                  ║
echo   ║  Backend        http://localhost:18001                 ║
echo   ║  Backend docs   http://localhost:18001/docs            ║
echo   ║  MailHog UI     http://localhost:8026                  ║
echo   ║  Postgres       127.0.0.1:25433 (db: sgd_backup)       ║
echo   ║  Redis          127.0.0.1:26380                        ║
echo   ║                                                        ║
echo   ║  Stack original sigue en 8080/5173/18000 (intacto)     ║
echo   ╚════════════════════════════════════════════════════════╝
echo.
echo   Para detener: scripts\stop-stack-backup.bat
echo.
echo   Monitoreo (en otra terminal):
echo     docker compose -f deploy/docker-compose.backup.yml --env-file .env.backup logs -f backend
echo.
endlocal
