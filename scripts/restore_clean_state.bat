@echo off
REM ============================================================
REM  restore_clean_state.bat
REM  Restaura la BD al estado "limpio" (snapshot del 2026-06-18)
REM  Uso: scripts\restore_clean_state.bat [ruta-al-dump]
REM  Default: backups\clean_state_20260618\clean_state.dump
REM ============================================================

setlocal

set "DUMP_PATH=%~1"
if "%DUMP_PATH%"=="" set "DUMP_PATH=%~dp0..\backups\clean_state_20260618\clean_state.dump"

echo [restore] Dump a restaurar: %DUMP_PATH%
if not exist "%DUMP_PATH%" (
    echo [ERROR] No existe el archivo: %DUMP_PATH%
    echo         Verifica que el backup este presente.
    exit /b 1
)

REM --- Cargar vars del .env (PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE) ---
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    set "line=%%a=%%b"
    call set "%%a=%%b" 2>nul
)

REM Defaults si .env no tiene
if "%HOST_PORT_POSTGRES%"=="" set "HOST_PORT_POSTGRES=25432"
if "%POSTGRES_USER%"=="" set "POSTGRES_USER=sgd"
if "%POSTGRES_DB%"=="" set "POSTGRES_DB=sgd"

set "PGHOST=localhost"
set "PGPORT=%HOST_PORT_POSTGRES%"
set "PGUSER=%POSTGRES_USER%"
set "PGDATABASE=%POSTGRES_DB%"
set "PGPASSWORD=%POSTGRES_PASSWORD%"

echo [restore] Conectando a %PGUSER%@%PGHOST%:%PGPORT%/%PGDATABASE%

REM --- Detener backend para liberar conexiones a la BD ---
echo [restore] Deteniendo sgd-backend (libera conexiones a la BD)...
docker stop sgd-backend >nul 2>&1
docker stop sgd-celery-worker >nul 2>&1
docker stop sgd-celery-beat >nul 2>&1
timeout /t 2 /nobreak >nul

REM --- Copiar dump al container postgres ---
echo [restore] Copiando dump al container postgres...
docker cp "%DUMP_PATH%" sgd-postgres:/tmp/restore.dump

REM --- DROP + RECREATE schema (lo mas limpio: --clean --if-exists) ---
echo [restore] Ejecutando pg_restore --clean --if-exists --single-transaction...
echo           (los WARNING de pg_restore sobre objetos no encontrados son NORMALES con --clean)
docker exec -e PGPASSWORD=%POSTGRES_PASSWORD% sgd-postgres pg_restore -U %POSTGRES_USER% -d %POSTGRES_DB% --clean --if-exists --single-transaction --no-owner --no-acl /tmp/restore.dump 2>nul
set "RESTORE_EXIT=%ERRORLEVEL%"

docker exec sgd-postgres rm /tmp/restore.dump 2>nul

REM --- Levantar backend de nuevo ---
echo [restore] Levantando sgd-backend y celery...
docker start sgd-backend >nul 2>&1
docker start sgd-celery-worker >nul 2>&1
docker start sgd-celery-beat >nul 2>&1

REM --- Reiniciar nginx para que recargue la IP del backend (puede cambiar tras stop/start) ---
echo [restore] Reiniciando sgd-nginx (recarga DNS de containers)...
docker restart sgd-nginx >nul 2>&1
timeout /t 3 /nobreak >nul

echo.
if %RESTORE_EXIT% neq 0 (
    echo [WARN] pg_restore termino con codigo %RESTORE_EXIT%.
    echo        Verifica con: docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT * FROM verify_clean_state();"
) else (
    echo [OK] Restore completado. Verificando estado...
    timeout /t 3 /nobreak >nul
    docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT tabla, filas FROM verify_clean_state() WHERE tabla IN ('audit_log','gerencias','usuarios','documentos');"
)

endlocal & exit /b %RESTORE_EXIT%
