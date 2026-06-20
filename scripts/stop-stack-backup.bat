@echo off
REM ════════════════════════════════════════════════════════════════
REM COFAR SGD — Apaga el stack BACKUP (paralelo)
REM
REM NO toca el stack original.
REM Por defecto mantiene los volumenes (datos persisten).
REM
REM Uso:
REM   scripts\stop-stack-backup.bat              (apaga containers, mantiene datos)
REM   scripts\stop-stack-backup.bat --purge     (apaga containers + BORRA volumenes)
REM ════════════════════════════════════════════════════════════════

setlocal
set REPO_ROOT=%~dp0..

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║  COFAR SGD — Apagando stack BACKUP                            ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d "%REPO_ROOT%"
docker compose -f deploy/docker-compose.backup.yml --env-file .env.backup down

if "%~1"=="--purge" (
    echo.
    echo [PURGE] Borrando volumenes sgd-des-bk_* ...
    docker volume rm sgd-des-bk_postgres_data sgd-des-bk_redis_data sgd-des-bk_backend_storage sgd-des-bk_frontend_node_modules 2>nul
    echo       OK: volumenes eliminados
) else (
    echo.
    echo Los volumenes sgd-des-bk_* se MANTIENEN (datos persisten).
    echo Para borrarlos: scripts\stop-stack-backup.bat --purge
)

echo.
echo Stack backup detenido. El stack original sigue intacto.
echo.
endlocal
