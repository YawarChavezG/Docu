@echo off
REM ════════════════════════════════════════════════════════════════
REM COFAR SGD — Dev Backend (nativo Windows)
REM Levanta el backend FastAPI con uvicorn en Windows nativo,
REM apuntando a Postgres/Redis que corren en Docker.
REM
REM ¿Por qué nativo y no en Docker?
REM En DES (Windows 10 + FortiClient VPN), Docker Desktop + WSL2
REM no ven la VPN corporativa (FortiClient corre en el host Windows).
REM Por eso el backend debe correr nativo para alcanzar el AD
REM (172.16.10.17 = dc3-cofar) y poder hacer bind LDAP.
REM
REM En QAS (VM Debian dentro de la red COFAR) esto no aplica:
REM todo el stack corre en Docker, incluyendo el backend.
REM ════════════════════════════════════════════════════════════════

setlocal

REM ─── Paths ───
set REPO_ROOT=%~dp0..
set BACKEND_DIR=%REPO_ROOT%\backend
set VENV_DIR=%BACKEND_DIR%\.venv

REM ─── Python 3.12 (forzamos el path para evitar conflictos con Inkscape y otros) ───
set PYTHON_EXE=C:\Users\ychavez\AppData\Local\Programs\Python\Python312\python.exe
if not exist "%PYTHON_EXE%" (
    echo [ERROR] No se encontro Python 3.12 en %PYTHON_EXE%.
    echo Ajusta PYTHON_EXE en este script al path real.
    pause
    exit /b 1
)

REM ─── Cargar .env raiz (mismas vars que Docker) ───
if not exist "%REPO_ROOT%\.env" (
    echo [ERROR] No se encontro %REPO_ROOT%\.env
    echo Copia .env.example a .env y completa las variables.
    pause
    exit /b 1
)

REM Cargar vars del .env al entorno actual
REM IMPORTANTE: usar tokens=1* (no 1,2) y delims==. Asi se parte en el
REM PRIMER '=' y el resto del valor (que puede contener mas '=' como
REM en LDAP_USER_SEARCH_BASE=OU=Usuarios,DC=cofar,DC=com) queda intacto
REM en %%b. Con tokens=1,2 el batch se cortaba en el segundo '=' y
REM LDAP_USER_SEARCH_BASE quedaba como literal "OU" -> LDAP fallaba
REM con "attribute type not present".
for /f "usebackq tokens=1* delims==" %%a in ("%REPO_ROOT%\.env") do (
    set "%%a=%%b"
)

REM ─── Validar venv ───
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [WARN] No hay venv en %VENV_DIR%. Creando con Python 3.12...
    cd /d "%BACKEND_DIR%"
    "%PYTHON_EXE%" -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el venv.
        pause
        exit /b 1
    )
    echo [INFO] Venv creado. Si las dependencias no estan instaladas, correr:
    echo        %VENV_DIR%\Scripts\python.exe -m pip install fastapi==0.137.0 uvicorn ...
)

REM ─── Activar venv ───
call "%VENV_DIR%\Scripts\activate.bat"

REM ─── Validar que el venv tiene los paquetes clave ───
"%VENV_DIR%\Scripts\python.exe" -c "import fastapi, uvicorn, sqlalchemy, ldap3" 2>nul
if errorlevel 1 (
    echo [WARN] Faltan paquetes en el venv. Instalando los minimos...
    "%VENV_DIR%\Scripts\python.exe" -m pip install fastapi==0.137.0 "uvicorn[standard]==0.49.0" pydantic==2.13.4 pydantic-settings==2.6.1 python-dotenv==1.0.1 "sqlalchemy[asyncio]==2.0.50" asyncpg==0.31.0 alembic==1.18.4 psycopg2-binary==2.9.10 "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" python-multipart==0.0.17 ldap3==2.9.1 httpx==0.27.2 aiohttp==3.11.10 msal==1.37.0 aiosmtplib==3.0.1 jinja2==3.1.4 "celery[redis]==5.6.3" redis==5.2.1
)

REM ─── Override de URLs para apuntar a 127.0.0.1:puerto_host ───
set DATABASE_URL=postgresql+asyncpg://%POSTGRES_USER%:%POSTGRES_PASSWORD%@127.0.0.1:%HOST_PORT_POSTGRES%/%POSTGRES_DB%
set REDIS_URL=redis://127.0.0.1:%HOST_PORT_REDIS%/0
set CELERY_BROKER_URL=redis://127.0.0.1:%HOST_PORT_REDIS%/1
set CELERY_RESULT_BACKEND=redis://127.0.0.1:%HOST_PORT_REDIS%/2

REM ─── Aviso si LDAP esta habilitado ───
if /i "%LDAP_ENABLED%"=="true" (
    echo [INFO] LDAP_ENABLED=true ^— el backend intentara bind contra %LDAP_SERVER%:%LDAP_PORT%
    echo [INFO]   Asegurate de tener la VPN corporativa activa.
) else (
    echo [INFO] LDAP_ENABLED=false ^— login con stubs (admin/aromero/solicitante/visualizador + cofar.2026)
)

echo.
echo ══════════════════════════════════════════════════════════════
echo  Backend nativo en http://localhost:18000
echo  Hot-reload activado — los cambios en .py se aplican solos
echo  Ctrl+C para detener
echo ══════════════════════════════════════════════════════════════
echo.

cd /d "%BACKEND_DIR%"
"%VENV_DIR%\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 18000 --reload

pause
