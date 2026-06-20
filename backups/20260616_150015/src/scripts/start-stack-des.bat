@echo off
REM ════════════════════════════════════════════════════════════════
REM COFAR SGD — Orquestador de stack para DES (Windows 10 + VPN)
REM
REM Este script es el PUNTO ÚNICO DE ENTRADA para arrancar el
REM entorno de desarrollo en DES. Hace 4 cosas en orden:
REM
REM   1. Verifica prerequisitos (.env existe, Docker up, Python 3.12).
REM   2. Levanta la stack Docker (postgres, redis, mailhog, frontend,
REM      nginx, celery-worker, celery-beat) SIN el contenedor backend.
REM   3. Activa el venv de Python y lanza uvicorn nativo (backend).
REM   4. Espera el health-check y muestra las URLs.
REM
REM Por que el backend va fuera de Docker en DES, ver:
REM   docs/PR/DECISIONES.md  ADR-013
REM
REM En QAS/PRD este script NO se usa. Ahi todo va en Docker via
REM `docker compose up -d` directamente.
REM
REM Uso:
REM   scripts\start-stack-des.bat
REM
REM Detener todo:
REM   scripts\stop-stack-des.bat   (apaga Docker + mata uvicorn)
REM   Ctrl+C en esta ventana       (apaga uvicorn, deja Docker Up)
REM ════════════════════════════════════════════════════════════════

setlocal EnableDelayedExpansion

set REPO_ROOT=%~dp0..
set SCRIPTS_DIR=%~dp0
set BACKEND_DIR=%REPO_ROOT%\backend
set VENV_PY=%BACKEND_DIR%\.venv\Scripts\python.exe

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  COFAR SGD — Stack DES (Windows 10 + VPN FortiClient)          ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM ─── 1. Prerequisitos ───
echo [1/4] Verificando prerequisitos...

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

if not exist "%VENV_PY%" (
    echo [ERROR] No existe el venv de Python en %VENV_PY%
    echo         Crealo con:  cd backend ^&^& python -m venv .venv
    echo         Luego:       .venv\Scripts\python.exe -m pip install -r requirements\base.txt
    exit /b 1
)

echo       OK: .env existe, Docker up, venv presente
echo.

REM ─── 2. Stack Docker (incluye backend) ───
echo [2/4] Levantando servicios Docker (incluye backend)...
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

REM ─── 3. Esperar health-checks ───
echo [3/4] Esperando health-checks (postgres + backend)...
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

REM ─── 4. URLs finales ───
echo [4/4] Stack completo.
echo.
echo   ╔════════════════════════════════════════════════════════╗
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
echo.
