# ════════════════════════════════════════════════════════════════
# validar_stack.ps1 — Smoke test rápido de toda la stack SGD
# Uso: .\validar_stack.ps1
# ════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"
$ok = $true

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  COFAR SGD - Validacion de Stack (DES)" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Docker ──
Write-Host "[1/5] Verificando Docker..." -NoNewline
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0 -and $dockerInfo -match "Server Version") {
        $version = ($dockerInfo | Select-String "Server Version" | Select-Object -First 1).ToString().Trim()
        Write-Host " OK ($version)" -ForegroundColor Green
    } else {
        Write-Host " FAIL Docker NO responde" -ForegroundColor Red
        $ok = $false
    }
} catch {
    Write-Host " FAIL Docker no disponible" -ForegroundColor Red
    $ok = $false
}

# ── 2. Contenedores ──
Write-Host ""
Write-Host "[2/5] Verificando contenedores..." -ForegroundColor Yellow
$expectedServices = @("sgd-postgres", "sgd-redis", "sgd-mailhog", "sgd-backend", "sgd-nginx", "sgd-frontend")
foreach ($svc in $expectedServices) {
    Write-Host "   $svc ..." -NoNewline
    $status = docker ps --format "{{.Status}}" --filter "name=^${svc}$" 2>&1
    if ($status -match "Up") {
        if ($status -match "healthy") {
            Write-Host " UP (healthy)" -ForegroundColor Green
        } else {
            Write-Host " UP (sin healthcheck)" -ForegroundColor Yellow
        }
    } elseif ($status -match "Exited") {
        Write-Host " EXited" -ForegroundColor Red
        $ok = $false
    } else {
        Write-Host " NO existe" -ForegroundColor Red
        $ok = $false
    }
}

# ── 3. Health del backend ──
Write-Host ""
Write-Host "[3/5] Health del backend (http://localhost:18000/health)..." -NoNewline
try {
    $health = curl.exe -s --max-time 5 http://localhost:18000/health 2>&1
    if ($health -match '"status":"ok"') {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "        Respuesta: $health" -ForegroundColor Gray
    } else {
        Write-Host " FAIL Backend no responde" -ForegroundColor Red
        Write-Host "        Respuesta: $health" -ForegroundColor Gray
        $ok = $false
    }
} catch {
    Write-Host " FAIL Error de conexion" -ForegroundColor Red
    $ok = $false
}

# ── 4. Login real ──
Write-Host ""
Write-Host "[4/5] Login de prueba (aromero)..." -NoNewline
try {
    $loginFile = New-TemporaryFile
    @'
{"username":"aromero","password":"cofar.2026"}
'@ | Set-Content -Path $loginFile -NoNewline
    $loginResp = curl.exe -s --max-time 5 -X POST `
        -H "Content-Type: application/json" `
        --data-binary "@$($loginFile.FullName)" `
        http://localhost:18000/api/v1/login 2>&1
    Remove-Item $loginFile -Force -ErrorAction SilentlyContinue
    if ($loginResp -match '"message":"Login exitoso') {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "        Respuesta: $loginResp" -ForegroundColor Gray
    } else {
        Write-Host " FAIL Login fallo" -ForegroundColor Red
        Write-Host "        Respuesta: $loginResp" -ForegroundColor Gray
        $ok = $false
    }
} catch {
    Write-Host " FAIL Error de conexion" -ForegroundColor Red
    $ok = $false
}

# ── 5. Login a través de Nginx ──
Write-Host ""
Write-Host "[5/5] Login via Nginx (http://localhost:8080/api/v1/login)..." -NoNewline
try {
    $loginFile = New-TemporaryFile
    @'
{"username":"admin","password":"cofar.2026"}
'@ | Set-Content -Path $loginFile -NoNewline
    $nginxResp = curl.exe -s --max-time 5 -X POST `
        -H "Content-Type: application/json" `
        --data-binary "@$($loginFile.FullName)" `
        http://localhost:8080/api/v1/login 2>&1
    Remove-Item $loginFile -Force -ErrorAction SilentlyContinue
    if ($nginxResp -match '"message":"Login exitoso') {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " FAIL Nginx no proxy correctamente" -ForegroundColor Red
        Write-Host "        Respuesta: $nginxResp" -ForegroundColor Gray
        $ok = $false
    }
} catch {
    Write-Host " FAIL Error de conexion" -ForegroundColor Red
    $ok = $false
}

# ── Resumen ──
Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
if ($ok) {
    Write-Host "  STACK FUNCIONANDO CORRECTAMENTE" -ForegroundColor Green
} else {
    Write-Host "  HAY PROBLEMAS - Revisa los logs:" -ForegroundColor Red
    Write-Host "        docker logs sgd-backend --tail 30" -ForegroundColor Gray
    Write-Host "        docker logs sgd-nginx --tail 30" -ForegroundColor Gray
}
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# URLs útiles
Write-Host "URLs disponibles:" -ForegroundColor Yellow
Write-Host "   App (Nginx):       http://localhost:8080"
Write-Host "   Vite directo:      http://localhost:5173"
Write-Host "   Backend Swagger:   http://localhost:18000/docs"
Write-Host "   Backend ReDoc:     http://localhost:18000/redoc"
Write-Host "   MailHog UI:        http://localhost:8025"
Write-Host "   Postgres:          localhost:25432 (user: sgd, pass: sgd_dev_only_change_in_prod)"
Write-Host "   Redis:             localhost:26379"
Write-Host ""
