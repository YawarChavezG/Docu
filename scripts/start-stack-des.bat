@echo off
REM ════════════════════════════════════════════════════════════════
REM COFAR SGD — Orquestador de stack para DES (Windows 10 + VPN)
REM
REM Este script es el PUNTO ÚNICO DE ENTRADA para arrancar el
REM entorno de desarrollo en DES. Hace 5 cosas en orden:
REM
REM   1. Verifica prerequisitos (.env existe, Docker up, Python 3.12).
REM   2. Provisiona el storage del backend (limpia archivos corruptos
REM      de celerybeat-schedule con permisos inconsistentes).
REM   3. Levanta la stack Docker (postgres, redis, mailhog, frontend,
REM      nginx, celery-worker, celery-beat, backend) con docker compose.
REM   4. Espera el health-check de postgres y backend.
REM   5. Aplica permisos correctos a /app/storage DENTRO del container
REM      (chown 1000:1000 + chmod 755/644). NO usa chmod 777.
REM
REM Por que el backend va dentro de Docker en DES, ver:
REM   docs/PR/DECISIONES.md  ADR-013
REM
REM Por que celery-beat usa -s /app/storage/celerybeat-schedule, ver:
REM   docs/PR/DECISIONES.md  ADR-024
REM
REM En QAS/PRD este script NO se usa. Ahi todo va en Docker via
REM `bash /opt/sgd/scripts/start-stack-qas.sh` (o su equivalente PRD).
REM
REM Uso:
REM   scripts\start-stack-des.bat
REM
REM Detener todo:
REM   scripts\stop-stack-des.bat   (apaga Docker limpio)
REM   Ctrl+C en esta ventana       (apaga solo si hay backend nativo)
REM ════════════════════════════════════════════════════════════════

setlocal EnableDelayedExpansion

set REPO_ROOT=%~dp0..
set SCRIPTS_DIR=%~dp0
set BACKEND_DIR=%REPO_ROOT%\backend
set STORAGE_DIR=%BACKEND_DIR%\storage

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  COFAR SGD — Stack DES (Windows 10 + VPN FortiClient)          ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM ─── 1. Prerequisitos ───
echo [1/5] Verificando prerequisitos...

if not exist "%REPO_ROOT%\.env" (
    echo [ERROR] No existe %REPO_ROOT%\.env
    echo         Copia .env.example a .env y completa las variables.
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop no esta corriendo.
    echo         Abre Docker Desktop y vuelve a intentar.
    exit /b 1
)

echo       OK: .env existe, Docker up
echo.

REM ─── 2. Provisionar storage (limpiar archivos corruptos) ───
echo [2/5] Provisionando %STORAGE_DIR%...

if not exist "%STORAGE_DIR%" mkdir "%STORAGE_DIR%"

REM Si existe un celerybeat-schedule corrupto (sin permisos de escritura
REM o dejado por una sesion anterior), lo eliminamos. celery-beat lo
REM regenera automaticamente al siguiente start. Ver ADR-024.
if exist "%STORAGE_DIR%\celerybeat-schedule" (
    echo       [WARN] celerybeat-schedule existe. Verificando integridad...
    REM En Windows no podemos usar test -w; usamos un intento de delete+create
    REM como proxy: si no se puede escribir, lo borramos.
    copy /y NUL "%STORAGE_DIR%\celerybeat-schedule.test" >nul 2>&1
    if errorlevel 1 (
        echo       [WARN] Sin permisos de escritura en storage. Eliminando archivo corrupto.
        del /f /q "%STORAGE_DIR%\celerybeat-schedule" 2>nul
        del /f /q "%STORAGE_DIR%\celerybeat-schedule.bak" 2>nul
    ) else (
        del /f /q "%STORAGE_DIR%\celerybeat-schedule.test" >nul 2>&1
        echo       OK: celerybeat-schedule presente y escribible.
    )
)
echo       OK: storage provisionado.
echo.

REM ─── 3. Stack Docker ───
echo [3/5] Levantando servicios Docker (8 contenedores)...
echo       Servicios: postgres, redis, mailhog, frontend, backend, nginx, celery-worker, celery-beat
echo.

cd /d "%REPO_ROOT%"
docker compose -f deploy/docker-compose.yml --env-file .env up -d
if errorlevel 1 (
    echo [ERROR] Fallo `docker compose up`. Revisa los logs.
    exit /b 1
)

echo       OK: 8 contenedores iniciandose
echo.

REM ─── 4. Esperar health-checks ───
echo [4/5] Esperando health-checks (postgres + backend)...
echo       PostgreSQL (puerto 25432)...
:wait_pg
timeout /t 2 /nobreak >nul
docker exec sgd-postgres pg_isready -U sgd >nul 2>&1
if errorlevel 1 goto wait_pg
echo       OK: PostgreSQL ready
echo.

echo       Backend (puerto 18000)...
:wait_backend
timeout /t 2 /nobreak >nul
curl.exe -fsS http://localhost:18000/api/v1/health >nul 2>&1
if errorlevel 1 goto wait_backend
echo       OK: Backend ready
echo.

REM ─── 5. Permisos correctos de /app/storage DENTRO del container ───
echo [5/5] Aplicando permisos correctos a /app/storage dentro del container...
echo       (chown 1000:1000 + chmod 755/644 — forma correcta, no chmod 777)
echo.

docker exec --user root sgd-backend sh -c ^
    "mkdir -p /app/storage && chown -R 1000:1000 /app/storage && find /app/storage -type d -exec chmod 755 {} + && find /app/storage -type f -exec chmod 644 {} +"
if errorlevel 1 (
    echo [WARN] No se pudieron aplicar permisos dentro del container. celery-beat puede fallar.
    echo        Revisar manualmente: docker exec --user root sgd-backend ls -la /app/storage
) else (
    echo       OK: storage con permisos correctos (owner sgduser 1000:1000).
)

REM Reiniciar celery-beat para que regenere el schedule file con los nuevos perms
echo.
echo       Reiniciando celery-beat para regenerar schedule file...
docker restart sgd-celery-beat >nul 2>&1
timeout /t 3 /nobreak >nul

echo.
echo   ╔════════════════════════════════════════════════════════╗
echo   ║  Stack DES completo.                                   ║
echo   ║                                                        ║
echo   ║  App           http://localhost:8080                    ║
echo   ║  Frontend      http://localhost:5173                    ║
echo   ║  Backend       http://localhost:18000                   ║
echo   ║  Backend docs  http://localhost:18000/docs              ║
echo   ║  MailHog UI    http://localhost:8025                    ║
echo   ║  Postgres      127.0.0.1:25432 (user: sgd)              ║
echo   ║  Redis         127.0.0.1:26379                         ║
echo   ╚════════════════════════════════════════════════════════╝
echo.
echo   Para detener todo: scripts\stop-stack-des.bat
echo.
echo   Monitoreo (en otra terminal):
echo     docker compose -f deploy/docker-compose.yml logs -f backend
echo     docker logs sgd-celery-beat -f --tail 50
echo.
