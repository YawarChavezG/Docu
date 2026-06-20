@echo off
REM ==============================================
REM  RESTAURACION COMPLETA DE BD
REM  Correr DESPUES de docker compose up
REM ==============================================

set API_BASE=http://localhost:18000/api/v1
set MATRIZ_EXCEL=docs\Diagramas_Matrices\MATRICES\USUARIOS EXISTENTES A ABRIL.xlsx
set COOKIE_FILE=%TEMP%\sgd_admin_cookies.txt

echo.
echo [1/5] Login como admin_local...

curl.exe -s -c "%COOKIE_FILE%" -X POST "%API_BASE%/login" -H "Content-Type: application/json" -d "{\"username\":\"admin_local\",\"password\":\"admin.2026\",\"auth_source\":\"local\"}" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Login fallo. Verifica que el backend este corriendo.
    exit /b 1
)
REM Extraer CSRF token del cookie jar
for /f "tokens=7" %%a in ('findstr /C:"csrf_token" "%COOKIE_FILE%"') do set CSRF=%%a
if "%CSRF%"=="" (
    echo ERROR: No se pudo obtener CSRF token
    exit /b 1
)
echo  Login OK

echo.
echo [2/5] Sincronizando con Active Directory...
curl.exe -s -X POST "%API_BASE%/usuarios/sync-ad" -b "%COOKIE_FILE%" -H "X-CSRF-Token: %CSRF%" -H "Content-Type: application/json"
echo.

echo.
echo [3/5] Copiando matriz Excel al container...
docker cp "%MATRIZ_EXCEL%" sgd-backend:/tmp/matriz.xlsx
echo  Ejecutando import masivo de roles...
docker exec sgd-backend python scripts/run_matriz_import.py --excel /tmp/matriz.xlsx --yes 2>nul
echo.

echo.
echo [4/5] Sembrando documentos de prueba...
docker exec sgd-backend python scripts/seed_documentos.py 2>nul
echo.

echo.
echo [5/5] Verificando estado final...
docker exec sgd-postgres psql -U sgd -d sgd -c "SELECT 'usuarios', count(*) FROM usuarios UNION ALL SELECT 'usuario_roles', count(*) FROM usuario_roles UNION ALL SELECT 'documentos', count(*) FROM documentos;"

del "%COOKIE_FILE%" 2>nul
echo.
echo =============================================
echo  RESTAURACION COMPLETA
echo =============================================
