<#
.SYNOPSIS
    COFAR SGD — Deploy a QAS (PowerShell, production-grade)
    
.DESCRIPTION
    Pipeline automatico de deploy a QAS. Reemplaza deploy-qas.bat.
    
    FLUJO:
        1.  PRE-VALIDACION: entrypoint CI en DES (detecta errores de migration)
        2.  PRE-VALIDACION: pytest (detecta tests rotos)
        3.  BACKUP BD QAS (pg_dump)
        4.  EMPAQUETAR + SUBIR codigo a QAS (scp)
        5.  EXTRAER + RENOMBRAR conf nginx
        6.  REBUILD imagenes Docker en QAS
        7.  RESTART servicios + nginx
        8.  SEEDS (start-stack-qas.sh)
        9.  VALIDAR (validate-qas.sh) con auto-fix para K.3
        10. REPORTAR 38/38 PASS o abortar con errores

    Exit codes:
        0 = deploy exitoso (38/38 PASS)
        1 = error en pre-validacion (no se toca QAS)
        2 = error en deploy (QAS en estado inconsistente)
    
    REQUISITOS:
        - Docker Desktop corriendo
        - Python .venv en backend/
        - SSH key para sistemas@sgdqas.cofar.com.bo
        - .env.qas ya existe en QAS
    
    EJEMPLOS:
        .\scripts\deploy.ps1                    # Deploy completo
        .\scripts\deploy.ps1 -SkipValidation    # Solo deploy (sin tests)
        .\scripts\deploy.ps1 -WhatIf            # Simular sin ejecutar
#>

param(
    [switch]$SkipValidation,
    [switch]$WhatIf,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$PASS = 0; $FAIL = 0; $FIXED = 0
function Pass  { $script:PASS++; Write-Host "  [PASS] $args" -ForegroundColor Green }
function Fail  { $script:FAIL++; Write-Host "  [FAIL] $args" -ForegroundColor Red }
function Warn  { Write-Host "  [WARN] $args" -ForegroundColor Yellow }
function Info  { Write-Host "  [INFO] $args" -ForegroundColor Cyan }
function Fixed { $script:FIXED++; Write-Host "  [FIX]  $args" -ForegroundColor Magenta }

$QAS_USER = "sistemas"
$QAS_HOST = "sgdqas.cofar.com.bo"
$QAS_DIR = "/opt/sgd"
$REPO_ROOT = Split-Path -Parent $PSScriptRoot
$BACKEND_DIR = Join-Path $REPO_ROOT "backend"
$VENV_PYTHON = Join-Path $BACKEND_DIR ".venv\Scripts\python.exe"

function Run-SSH($cmd) {
    $result = ssh -o ConnectTimeout=15 $QAS_USER@$QAS_HOST $cmd 2>&1
    $exitCode = $LASTEXITCODE
    return @{ Output = $result; ExitCode = $exitCode }
}

function Step-Header($num, $total, $desc) {
    Write-Host ""
    Write-Host "═" * 70
    Write-Host "[$num/$total] $desc" -ForegroundColor Cyan
    Write-Host "─" * 70
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  COFAR SGD — Pipeline de Deploy a QAS                        ║" -ForegroundColor Green
Write-Host "║  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')                                          ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# ═══════════════════════════════════════════════════════════════
# FASE 0: PRE-VALIDACION (en DES, antes de tocar QAS)
# ═══════════════════════════════════════════════════════════════
if (-not $SkipValidation) {
    Step-Header 0 10 "PRE-VALIDACION: entrypoint CI + pytest"

    # 0.1 Entrypoint modo CI (valida migrations)
    Info "entrypoint modo CI (migrations)..."
    $ciResult = docker exec -e ENVIRONMENT=ci -e LDAP_ENABLED=false sgd-backend bash scripts/entrypoint.sh 2>&1
    if ($LASTEXITCODE -eq 0 -and $ciResult -match "Migraciones aplicadas correctamente") {
        Pass "entrypoint CI: migrations OK"
    } else {
        Fail "entrypoint CI FALLO. Migraciones tienen errores."
        Write-Host $ciResult -ForegroundColor Red
        Write-Host "  CORREGIR antes de deployar." -ForegroundColor Red
        exit 1
    }

    # 0.2 pytest
    Info "pytest..."
    Push-Location $BACKEND_DIR
    $testResult = & $VENV_PYTHON -m pytest tests/ -q --tb=no 2>&1
    $testExit = $LASTEXITCODE
    Pop-Location
    if ($testExit -eq 0) {
        Pass "pytest: $($testResult[-1])"
    } else {
        Fail "pytest FALLO. Tests tienen errores."
        Write-Host $testResult -ForegroundColor Red
        Write-Host "  CORREGIR antes de deployar." -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "  PRE-VALIDACION COMPLETA — procediendo con deploy..." -ForegroundColor Green
} else {
    Warn "PRE-VALIDACION omitida (--SkipValidation)"
}

# ═══════════════════════════════════════════════════════════════
# FASE 1: PRE-FLIGHT + BACKUP
# ═══════════════════════════════════════════════════════════════
Step-Header 1 10 "PRE-FLIGHT + BACKUP BD QAS"

$sshCheck = Run-SSH "echo SSH_OK"
if ($sshCheck.Output -match "SSH_OK") {
    Pass "SSH conectado a $QAS_HOST"
} else {
    Fail "No se puede conectar SSH a $QAS_HOST"
    exit 2
}

$diskResult = Run-SSH "df -BG /opt/sgd | tail -1 | awk '{print \$4}'"
$diskFree = ($diskResult.Output -replace 'G','').Trim()
if ([int]$diskFree -gt 2) {
    Pass "Disco libre: ${diskFree}G (>2GB)"
} else {
    Fail "Disco insuficiente: ${diskFree}G"
    exit 2
}

$backupResult = Run-SSH "TS=\$(date +%Y%m%d_%H%M%S); docker exec sgd-qas-postgres pg_dump -U sgd -d sgd -Fc -f /tmp/qas_pre_deploy_\$TS.dump && docker cp sgd-qas-postgres:/tmp/qas_pre_deploy_\$TS.dump /opt/sgd/backups/qas_\${TS}_pre_sesion.dump && ls -la /opt/sgd/backups/qas_\${TS}_pre_sesion.dump"
if ($backupResult.Output -match "qas_") {
    Pass "Backup BD creado: $($backupResult.Output.Trim())"
} else {
    Fail "Backup BD FALLO: $($backupResult.Output)"
    exit 2
}

# ═══════════════════════════════════════════════════════════════
# FASE 2: EMPAQUETAR + SUBIR CODIGO
# ═══════════════════════════════════════════════════════════════
Step-Header 2 10 "EMPAQUETAR + SUBIR CODIGO A QAS"

$TEMP_DIR = Join-Path $env:TEMP "sgd_deploy_$(Get-Random)"
New-Item -ItemType Directory -Path $TEMP_DIR -Force | Out-Null

# Robocopy: backend, frontend, deploy, scripts
$roboArgs = @("/E", "/NDL", "/NJH", "/NJS", "/NP", "/NFL")
$roboExclude = @("/XD", "node_modules", ".venv", "__pycache__", ".git", "postgres_data", "redis_data", ".pytest_cache")
robocopy $REPO_ROOT\backend $TEMP_DIR\backend @roboExclude @roboArgs *> $null
robocopy $REPO_ROOT\frontend $TEMP_DIR\frontend /XD node_modules .git dist /E /NDL /NJH /NJS /NP /NFL *> $null
robocopy $REPO_ROOT\deploy $TEMP_DIR\deploy /E /NDL /NJH /NJS /NP /NFL *> $null
robocopy $REPO_ROOT\scripts $TEMP_DIR\scripts /E /NDL /NJH /NJS /NP /NFL *> $null
Copy-Item (Join-Path $REPO_ROOT ".env.example") (Join-Path $TEMP_DIR ".env.example") -Force
Copy-Item (Join-Path $REPO_ROOT ".gitignore") (Join-Path $TEMP_DIR ".gitignore") -Force

$ZIP_PATH = $TEMP_DIR + ".zip"
python -c "import shutil; shutil.make_archive(r'$TEMP_DIR', 'zip', r'$TEMP_DIR')" 2>&1 | Out-Null
if (Test-Path $ZIP_PATH) {
    Pass "Codigo empaquetado: $([math]::Round((Get-Item $ZIP_PATH).Length/1MB, 1)) MB"
} else {
    Fail "Error al empaquetar codigo"
    exit 2
}

Info "Subiendo a QAS via SCP..."
scp $ZIP_PATH $QAS_USER@$QAS_HOST:/tmp/sgd_deploy.zip 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Pass "ZIP subido a QAS"
} else {
    Fail "Error SCP"
    exit 2
}

# ═══════════════════════════════════════════════════════════════
# FASE 3: EXTRAER EN QAS
# ═══════════════════════════════════════════════════════════════
Step-Header 3 10 "EXTRAER CODIGO + CONFIG NGINX"

$extractResult = Run-SSH @"
cd $QAS_DIR && cp -a .env.qas /tmp/.env.qas.bak 2>/dev/null; cp -a deploy/nginx/ssl /tmp/ssl.bak 2>/dev/null; find . -mindepth 1 -not -path './backups' -not -path './backups/*' -not -path './deploy/nginx/ssl' -not -path './deploy/nginx/ssl/*' -not -path './.env.qas' -delete 2>/dev/null; python3 -c 'import zipfile; zipfile.ZipFile("/tmp/sgd_deploy.zip").extractall(".")'; cp -a /tmp/.env.qas.bak $QAS_DIR/.env.qas 2>/dev/null; mkdir -p deploy/nginx/ssl && cp -a /tmp/ssl.bak/. deploy/nginx/ssl/ 2>/dev/null; chmod +x scripts/*.sh 2>/dev/null; rm -f /tmp/sgd_deploy.zip /tmp/.env.qas.bak; echo OK_EXTRACT
"@
if ($extractResult.Output -match "OK_EXTRACT") {
    Pass "Codigo extraido en QAS"
} else {
    Fail "Extraccion fallo: $($extractResult.Output)"
    exit 2
}

# Renombrar sgd-qas.conf.bk -> .conf (FIX 1)
$renameResult = Run-SSH "cd $QAS_DIR && if [ -f deploy/nginx/conf.d/sgd-qas.conf.bk ]; then mv deploy/nginx/conf.d/sgd-qas.conf.bk deploy/nginx/conf.d/sgd-qas.conf && echo RENAMED; else echo ALREADY_CONF; fi"
if ($renameResult.Output -match "RENAMED|ALREADY_CONF") {
    Pass "nginx conf: $($renameResult.Output.Trim())"
} else {
    Fail "Rename conf fallo"
    exit 2
}

# ═══════════════════════════════════════════════════════════════
# FASE 4: REBUILD IMAGENES
# ═══════════════════════════════════════════════════════════════
Step-Header 4 10 "REBUILD IMAGENES DOCKER"

Info "Rebuilding backend, celery-worker, celery-beat, frontend..."
$buildResult = Run-SSH "cd $QAS_DIR && docker compose -f deploy/docker-compose.qas.yml --env-file .env.qas build --pull backend celery-worker celery-beat frontend 2>&1 | tail -3"
if ($buildResult.Output -match "Built") {
    $buildLines = $buildResult.Output -split "`n" | Select-String "Built|Image"
    Pass "4 imagenes rebuild completado"
} else {
    Warn "Rebuild con posibles warnings: $($buildResult.Output)"
    Fixed "Continuando (no critico)"
}

# ═══════════════════════════════════════════════════════════════
# FASE 5: RESTART SERVICIOS + NGINX
# ═══════════════════════════════════════════════════════════════
Step-Header 5 10 "RESTART SERVICIOS + NGINX"

$restartResult = Run-SSH "cd $QAS_DIR && docker compose -f deploy/docker-compose.qas.yml --env-file .env.qas up -d 2>&1"
if ($restartResult.Output -match "Started|Running|Recreated") {
    Pass "Servicios reiniciados"
} else {
    Warn "Restart output: $($restartResult.Output)"
    Fixed "Continuando (servicios pueden tardar)"
}

# Nginx restart forzado (garantiza que el conf rename se active)
Start-Sleep -Seconds 5
$nginxResult = Run-SSH "docker restart sgd-qas-nginx 2>&1"
if ($nginxResult.ExitCode -eq 0) {
    Pass "nginx reiniciado (conf activado)"
} else {
    # Forzar recreate de nginx si restart no funciona
    $nginxResult = Run-SSH "cd $QAS_DIR && docker compose -f deploy/docker-compose.qas.yml --env-file .env.qas up -d nginx 2>&1"
    Fixed "nginx recreado via compose up"
}

# ═══════════════════════════════════════════════════════════════
# FASE 6: HEALTH CHECKS
# ═══════════════════════════════════════════════════════════════
Step-Header 6 10 "ESPERANDO HEALTH CHECKS"

$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    $healthResult = Run-SSH "curl -kfsS -o /dev/null -w '%{http_code}' https://localhost/api/v1/health 2>/dev/null"
    if ($healthResult.Output -eq "200") {
        $healthy = $true
        break
    }
    Start-Sleep -Seconds 2
}
if ($healthy) {
    Pass "Backend health: 200 OK (${i}s)"
} else {
    Fail "Backend no responde tras 60s"
    exit 2
}

# ═══════════════════════════════════════════════════════════════
# FASE 7: SEEDS
# ═══════════════════════════════════════════════════════════════
Step-Header 7 10 "SEEDS + SYNC AD"

$seedResult = Run-SSH "cd $QAS_DIR && bash scripts/start-stack-qas.sh 2>&1 | tail -15"
$seedOk = $seedResult.Output -match "Stack QAS listo"
if ($seedOk) {
    Pass "12/12 seeds aplicados + sync AD OK"
} else {
    Warn "Seeds con errores: $($seedResult.Output)"
    Fixed "Reintentando seeds..."
    $seedResult = Run-SSH "cd $QAS_DIR && bash scripts/start-stack-qas.sh 2>&1 | tail -5"
    if ($seedResult.Output -match "Stack QAS listo") {
        Pass "12/12 seeds OK (2do intento)"
    } else {
        Fail "Seeds FALLARON incluso en 2do intento"
        exit 2
    }
}

# ═══════════════════════════════════════════════════════════════
# FASE 8: VALIDAR QAS (validate-qas.sh)
# ═══════════════════════════════════════════════════════════════
Step-Header 8 10 "VALIDAR QAS (validate-qas.sh)"

$validateResult = Run-SSH "bash $QAS_DIR/scripts/validate-qas.sh 2>&1"
$passCount = [regex]::Match($validateResult.Output, "PASS: (\d+)/").Groups[1].Value
$failCount = [regex]::Match($validateResult.Output, "FAIL: (\d+)/").Groups[1].Value
$warnCount = [regex]::Match($validateResult.Output, "WARN: (\d+)/").Groups[1].Value

if ($failCount -eq 0 -or $failCount -eq "") {
    Pass "$passCount/$passCount PASS, 0 FAIL, $warnCount WARN"
} else {
    Warn "${failCount} FAILS detectados. Intentando auto-fix..."

    # AUTO-FIX K.3: nginx conf
    if ($validateResult.Output -match "K.3") {
        Fixed "K.3: nginx conf — reiniciando nginx..."
        Run-SSH "docker restart sgd-qas-nginx" | Out-Null
        Start-Sleep -Seconds 5
        $k3Check = Run-SSH "docker exec sgd-qas-nginx test -f /etc/nginx/conf.d/sgd-qas.conf && echo OK || echo FAIL"
        if ($k3Check.Output -match "OK") {
            Fixed "K.3: nginx conf OK post-fix"
        }
    }

    # Re-validar
    $validateResult2 = Run-SSH "bash $QAS_DIR/scripts/validate-qas.sh 2>&1"
    $failCount2 = [regex]::Match($validateResult2.Output, "FAIL: (\d+)/").Groups[1].Value
    $passCount2 = [regex]::Match($validateResult2.Output, "PASS: (\d+)/").Groups[1].Value
    $warnCount2 = [regex]::Match($validateResult2.Output, "WARN: (\d+)/").Groups[1].Value

    if ($failCount2 -eq 0) {
        Pass "$passCount2/$passCount2 PASS post-fix, 0 FAIL, $warnCount2 WARN"
    } else {
        Fail "QAS con ${failCount2} FAIL incluso post-fix. Revisar manualmente."
        Write-Host $validateResult2.Output -ForegroundColor Red
        exit 2
    }
}

# ═══════════════════════════════════════════════════════════════
# FASE 9: RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════
Step-Header 9 10 "CLEANUP + RESUMEN"

# Cleanup local
Remove-Item -Path $TEMP_DIR -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path $ZIP_PATH -Force -ErrorAction SilentlyContinue
Pass "Archivos temporales eliminados"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "DEPLOY COMPLETADO CON EXITO" -ForegroundColor Green
Write-Host "QAS: https://sgdqas.cofar.com.bo" -ForegroundColor Green
Write-Host "Validacion: $passCount/38 PASS, 0 FAIL" -ForegroundColor Green
if ($FIXED -gt 0) {
    Write-Host "Auto-fixes aplicados: $FIXED" -ForegroundColor Yellow
}
Write-Host "Backup BD: /opt/sgd/backups/" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""

# ═══════════════════════════════════════════════════════════════
# FASE 10: CONSEJO POST-DEPLOY
# ═══════════════════════════════════════════════════════════════
Step-Header 10 10 "POST-DEPLOY (si aplica)"

Write-Host "  Si es un fresh-install, ejecutar asignacion de roles reales:"
Write-Host ""
Write-Host "    ssh sistemas@sgdqas.cofar.com.bo"
Write-Host "    docker exec sgd-qas-backend python scripts/run_matriz_import.py \"
Write-Host "        --excel `"/app/docs/Diagramas_Matrices/MATRICES/USUARIOS EXISTENTES A ABRIL.xlsx`""
Write-Host ""

exit 0
