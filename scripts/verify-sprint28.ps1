# Sprint 28 verification script
$ErrorActionPreference = "Stop"

if (-not $env:API_BASE) {
    $env:API_BASE = "http://localhost:8000/api/v1"
}

Write-Host "=== Sprint 28 API tests ===" -ForegroundColor Cyan
py -m pytest tests/test_23_sprint28.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== Sprint 28 Playwright e2e ===" -ForegroundColor Cyan
Push-Location services/frontend
$env:PLAYWRIGHT_BASE_URL = "http://localhost:8088"
npm run test:e2e -- -c playwright.k8s.config.ts e2e/sprint28
$e2eExit = $LASTEXITCODE
Pop-Location
exit $e2eExit
