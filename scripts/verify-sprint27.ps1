# Sprint 27 verification script
$ErrorActionPreference = "Stop"

if (-not $env:API_BASE) {
    $env:API_BASE = "http://localhost:8000/api/v1"
}

Write-Host "=== Sprint 27 API tests ===" -ForegroundColor Cyan
py -m pytest tests/test_22_sprint27.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== Sprint 27 Playwright e2e ===" -ForegroundColor Cyan
Push-Location services/frontend
$env:PLAYWRIGHT_BASE_URL = "http://localhost:8088"
npm run test:e2e -- -c playwright.k8s.config.ts e2e/sprint27
$e2eExit = $LASTEXITCODE
Pop-Location
exit $e2eExit
