<#
.SYNOPSIS
    Restaura la BD a estado completo: catálogos + usuarios AD + roles desde matriz.
    Se ejecuta DESPUES de docker compose up, si la BD esta vacia o incompleta.

.DESCRIPTION
    Corre en orden:
    1. Seeds de catálogos (gerencias, areas, roles, tipos_doc, estados, etc.)
    2. Sync AD (trae ~750 usuarios desde LDAP)
    3. Import de matriz abril (asigna roles a los usuarios)
    4. Seed de documentos (10 docs de prueba)

    Ejemplo:
        scripts\seed_full_restore.ps1
#>

$ErrorActionPreference = "Stop"
$API_BASE = "http://localhost:18000/api/v1"
$MATRIZ_EXCEL = "docs/Diagramas_Matrices/MATRICES/USUARIOS EXISTENTES A ABRIL.xlsx"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  RESTAURACION COMPLETA DE BD" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# ─── 1. Login como admin_local ───
Write-Host "`n[1/5] Login como admin_local..." -ForegroundColor Yellow
$login = @{username="admin_local";password="admin.2026";auth_source="local"} | ConvertTo-Json
$loginFile = "$env:TEMP\login_admin.json"
Set-Content -Path $loginFile -Value $login
$headers = @{"Content-Type"="application/json"}
$resp = curl.exe -s -c "$env:TEMP\cookies_admin.txt" -X POST "$API_BASE/login" -H "Content-Type: application/json" --data-binary "@$loginFile"
Remove-Item $loginFile -ErrorAction SilentlyContinue
$csrf = ((Get-Content "$env:TEMP\cookies_admin.txt" | Select-String "csrf_token").Line -replace '.*csrf_token\s+','')
if (-not $csrf) { Write-Host "ERROR: No se pudo obtener CSRF token" -ForegroundColor Red; exit 1 }
Write-Host "  Login OK" -ForegroundColor Green

# ─── 2. Sync AD ───
Write-Host "[2/5] Sincronizando con Active Directory..." -ForegroundColor Yellow
$syncResp = curl.exe -s -X POST "$API_BASE/usuarios/sync-ad" -b "$env:TEMP\cookies_admin.txt" -H "X-CSRF-Token: $csrf" -H "Content-Type: application/json"
$syncData = $syncResp | ConvertFrom-Json
Write-Host "  Creados: $($syncData.creados) | Actualizados: $($syncData.actualizados) | Total AD: $($syncData.total_ad)" -ForegroundColor Green

# ─── 3. Import matriz ───
Write-Host "[3/5] Copiando matriz Excel al container..." -ForegroundColor Yellow
docker cp "$MATRIZ_EXCEL" sgd-backend:/tmp/matriz.xlsx
Write-Host "  Ejecutando import masivo de roles..." -ForegroundColor Yellow
$importResp = docker exec sgd-backend python scripts/run_matriz_import.py --excel /tmp/matriz.xlsx --yes 2>&1 | Select-String -Pattern "Roles asignados|Delta|Warnings"
Write-Host "  $importResp" -ForegroundColor Green

# ─── 4. Seed documentos ───
Write-Host "[4/5] Sembrando documentos de prueba..." -ForegroundColor Yellow
docker exec sgd-backend python scripts/seed_documentos.py 2>&1 | Select-String -Pattern "Inserted|Skipped|Errors"

# ─── 5. Verificacion final ───
Write-Host "[5/5] Verificando estado final..." -ForegroundColor Yellow
docker exec sgd-postgres psql -U sgd -d sgd -c "
SELECT 'usuarios' as tbl, count(*) FROM usuarios
UNION ALL SELECT 'usuario_roles', count(*) FROM usuario_roles
UNION ALL SELECT 'documentos', count(*) FROM documentos
UNION ALL SELECT 'gerencias', count(*) FROM gerencias
UNION ALL SELECT 'semaforizacion_tarea', count(*) FROM semaforizacion_tarea;
"
Remove-Item "$env:TEMP\cookies_admin.txt" -ErrorAction SilentlyContinue
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  RESTAURACION COMPLETA" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Cyan
