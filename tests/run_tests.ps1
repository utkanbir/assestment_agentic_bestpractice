# AAKP Test Runner
# Usage:
#   .\tests\run_tests.ps1              # infra only (Fuseki + PG)
#   .\tests\run_tests.ps1 -Suite all  # tum testler (Sprint 1 deploy lazim)
#   .\tests\run_tests.ps1 -Suite api  # sadece API testleri

param(
    [ValidateSet("infra","api","ws","kg","all")]
    [string]$Suite = "infra"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent

function Write-Step { param([string]$Msg) Write-Host "`n=== $Msg ===" -ForegroundColor Cyan }

Write-Step "Setting up port-forwards"

# Port-forward Fuseki (background)
$fusekiJob = Start-Job -ScriptBlock {
    kubectl port-forward svc/aakp-fuseki -n aakp-knowledge 3030:3030 2>$null
}
# Port-forward PostgreSQL (background)
$pgJob = Start-Job -ScriptBlock {
    kubectl port-forward svc/aakp-postgresql -n aakp-information 5432:5432 2>$null
}

Start-Sleep -Seconds 3
Write-Host "Port-forwards started (Fuseki:3030, PG:5432)" -ForegroundColor Gray

Write-Step "Installing test dependencies"
pip install -q -r "$Root\tests\requirements.txt"

Write-Step "Running test suite: $Suite"

$testFiles = switch ($Suite) {
    "infra" { "tests/test_01_infrastructure.py" }
    "api"   { "tests/test_02_api.py" }
    "ws"    { "tests/test_03_websocket.py" }
    "kg"    { "tests/test_04_knowledge_graph.py" }
    "all"   { "tests/" }
}

Set-Location $Root
pytest $testFiles -v --tb=short --asyncio-mode=auto

$exitCode = $LASTEXITCODE

Write-Step "Cleaning up port-forwards"
Stop-Job $fusekiJob, $pgJob -ErrorAction SilentlyContinue
Remove-Job $fusekiJob, $pgJob -ErrorAction SilentlyContinue

exit $exitCode
