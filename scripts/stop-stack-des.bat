@echo off
REM ════════════════════════════════════════════════════════════════
REM COFAR SGD — Apagado limpio de stack DES
REM
REM Cierra el backend nativo (uvicorn) si esta corriendo, y baja
REM todos los contenedores Docker de la stack. NO borra volumenes.
REM
REM Uso:
REM   scripts\stop-stack-des.bat
REM ════════════════════════════════════════════════════════════════

setlocal
set REPO_ROOT=%~dp0..

echo.
echo [1/2] Deteniendo backend nativo (uvicorn) en puerto 18000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :18000 ^| findstr LISTENING') do (
    echo       Matando PID %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Tambien matar cualquier python -m uvicorn que quede huerfano
taskkill /IM "python.exe" /FI "WINDOWTITLE eq *uvicorn*" /F >nul 2>&1
echo       OK
echo.

echo [2/2] Bajando contenedores Docker...
cd /d "%REPO_ROOT%"
docker compose -f deploy/docker-compose.yml --env-file .env down
if errorlevel 1 (
    echo [WARN] Algunos contenedores no bajaron. Revisa con `docker ps`.
)

echo.
echo Listo. Para volver a arrancar: scripts\start-stack-des.bat
echo.
