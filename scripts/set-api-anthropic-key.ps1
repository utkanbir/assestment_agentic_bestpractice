param(
    [Parameter(Mandatory = $true)]
    [string]$ApiKey
)

$ErrorActionPreference = "Stop"
$ns = "aakp-information"
$secret = "aakp-api-secret"

Write-Host "Updating $secret in $ns (key value not printed)..."
kubectl create secret generic $secret -n $ns `
    --from-literal=ANTHROPIC_API_KEY=$ApiKey `
    --dry-run=client -o yaml | kubectl apply -f -

Write-Host "Restarting aakp-api deployment..."
kubectl rollout restart deployment/aakp-api -n $ns
kubectl rollout status deployment/aakp-api -n $ns --timeout=120s

$root = Split-Path $PSScriptRoot -Parent
Write-Host "Restarting port-forwards (pod restart drops localhost tunnels)..."
& "$root\scripts\start-port-forwards.ps1"

Start-Sleep -Seconds 2
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 10
    Write-Host "Health OK — llm_mode: $($health.llm_mode)"
} catch {
    Write-Host "WARN: API not reachable on :8000 yet. Run: .\scripts\start-port-forwards.ps1"
}
