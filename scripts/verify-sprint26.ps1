# Sprint 26 verification script
$ErrorActionPreference = "Stop"

if (-not $env:API_BASE) {
    $env:API_BASE = "http://localhost:8000/api/v1"
}

Write-Host "=== Sprint 26 API tests ===" -ForegroundColor Cyan
py -m pytest tests/test_21_sprint26.py -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== Sprint 26 Playwright e2e ===" -ForegroundColor Cyan
Push-Location services/frontend
npm run test:e2e -- e2e/sprint26
$e2eExit = $LASTEXITCODE
Pop-Location
exit $e2eExit
