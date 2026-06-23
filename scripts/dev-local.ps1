# AAKP local development helper (Windows PowerShell)
# Usage:
#   .\scripts\dev-local.ps1                  # cluster API/UI via port-forward + manual instructions
#   .\scripts\dev-local.ps1 -StartApi      # local uvicorn + infra port-forwards
#   .\scripts\dev-local.ps1 -StartFrontend # vite dev server (proxies /api -> localhost:8000)
#   .\scripts\dev-local.ps1 -StartApi -StartFrontend

param(
    [switch]$StartApi,
    [switch]$StartFrontend
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$ApiDir = Join-Path $Root "services\api"
$FeDir = Join-Path $Root "services\frontend"

function Write-Step { param([string]$Msg) Write-Host "`n=== $Msg ===" -ForegroundColor Cyan }

function Stop-Port {
    param([int[]]$Ports)
    foreach ($port in $Ports) {
        Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
            ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    }
}

function Start-HiddenPortForward {
    param(
        [string]$Resource,
        [string]$Namespace,
        [string]$LocalPort,
        [string]$RemotePort
    )
    Start-Process kubectl -ArgumentList @(
        "port-forward", "-n", $Namespace, $Resource, "${LocalPort}:${RemotePort}", "--address", "127.0.0.1"
    ) -WindowStyle Hidden
}

function Start-InfraPortForwards {
    Write-Step "Starting infra port-forwards (PG, Fuseki, Qdrant, Redis)"
    Stop-Port -Ports @(5433, 3030, 6333, 6379)
    Start-HiddenPortForward -Resource "svc/aakp-postgresql" -Namespace "aakp-information" -LocalPort "5433" -RemotePort "5432"
    Start-HiddenPortForward -Resource "svc/aakp-fuseki" -Namespace "aakp-knowledge" -LocalPort "3030" -RemotePort "3030"
    Start-HiddenPortForward -Resource "svc/aakp-qdrant" -Namespace "aakp-information" -LocalPort "6333" -RemotePort "6333"
    Start-HiddenPortForward -Resource "svc/aakp-redis" -Namespace "aakp-agent" -LocalPort "6379" -RemotePort "6379"
    Start-Sleep -Seconds 2
    Write-Host "  PostgreSQL  localhost:5433" -ForegroundColor Gray
    Write-Host "  Fuseki      localhost:3030" -ForegroundColor Gray
    Write-Host "  Qdrant      localhost:6333" -ForegroundColor Gray
    Write-Host "  Redis       localhost:6379" -ForegroundColor Gray
}

function Show-LocalApiEnv {
    Write-Host ""
    Write-Host "Local API env (cluster deps via port-forward):" -ForegroundColor Yellow
    Write-Host '  $env:DATABASE_URL = "postgresql+asyncpg://aakp:aakp-pg-secret@localhost:5433/aakp"'
    Write-Host '  $env:FUSEKI_URL = "http://localhost:3030"'
    Write-Host '  $env:QDRANT_URL = "http://localhost:6333"'
    Write-Host '  $env:REDIS_URL = "redis://:aakp-redis-secret@localhost:6379/0"'
    Write-Host '  $env:ANTHROPIC_API_KEY = "<from cluster secret or .env>"'
    Write-Host ""
}

if ($StartApi) {
    Start-InfraPortForwards
    Stop-Port -Ports @(8000)
    Show-LocalApiEnv

    Write-Step "Starting local API (uvicorn)"
    $apiCmd = @"
Set-Location '$ApiDir'
`$env:DATABASE_URL = 'postgresql+asyncpg://aakp:aakp-pg-secret@localhost:5433/aakp'
`$env:FUSEKI_URL = 'http://localhost:3030'
`$env:QDRANT_URL = 'http://localhost:6333'
`$env:REDIS_URL = 'redis://:aakp-redis-secret@localhost:6379/0'
Write-Host 'AAKP local API — http://127.0.0.1:8000' -ForegroundColor Cyan
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@
    Start-Process powershell -ArgumentList @("-NoExit", "-Command", $apiCmd)
    Write-Host "OK  uvicorn started in new window (port 8000)" -ForegroundColor Green
} else {
    Write-Step "Cluster API + frontend port-forwards"
    & (Join-Path $PSScriptRoot "start-port-forwards.ps1")
}

if ($StartFrontend) {
    Write-Step "Starting frontend (vite dev — proxies /api to localhost:8000)"
    $feCmd = @"
Set-Location '$FeDir'
Write-Host 'AAKP Vite dev — http://127.0.0.1:5173 (API proxy -> :8000)' -ForegroundColor Cyan
npm run dev
"@
    Start-Process powershell -ArgumentList @("-NoExit", "-Command", $feCmd)
    Write-Host "OK  vite started in new window (port 5173)" -ForegroundColor Green
}

if (-not $StartApi -and -not $StartFrontend) {
    Write-Step "Manual local dev (separate terminals)"
    Write-Host ""
    Write-Host "Option A — cluster API/UI (already port-forwarded):" -ForegroundColor Cyan
    Write-Host "  Frontend: http://127.0.0.1:8088"
    Write-Host "  API:      http://127.0.0.1:8000"
    Write-Host ""
    Write-Host "Option B — local API + vite:" -ForegroundColor Cyan
    Write-Host "  .\scripts\dev-local.ps1 -StartApi -StartFrontend"
    Write-Host ""
    Write-Host "Or start manually:" -ForegroundColor Cyan
    Write-Host "  1. Infra forwards: run this script with -StartApi (infra only) or use tests/run_tests.ps1 pattern"
    Write-Host "  2. API terminal:"
    Write-Host "       cd services/api"
    Show-LocalApiEnv
    Write-Host "       py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    Write-Host "  3. Frontend terminal:"
    Write-Host "       cd services/frontend"
    Write-Host "       npm run dev"
    Write-Host "     Vite proxies /api, /ws, /health -> http://localhost:8000 (see vite.config.ts)"
    Write-Host "     UI: http://127.0.0.1:5173"
}

Write-Host ""
