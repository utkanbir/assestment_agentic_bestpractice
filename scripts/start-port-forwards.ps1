# AAKP local port-forwards (run this when UI/API unreachable)
$ErrorActionPreference = "Stop"
$ns = "aakp-information"

Write-Host "Stopping old port-forwards on 8000, 8080, 8088, 3030..."
foreach ($port in 8000, 8080, 8088, 3030, 8585) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

$apiPod = kubectl get pod -n $ns -l app=aakp-api -o jsonpath='{.items[0].metadata.name}'
if (-not $apiPod) { throw "aakp-api pod not found" }

Write-Host "API pod: $apiPod"
Start-Process kubectl -ArgumentList @(
    "port-forward", "-n", $ns, "pod/$apiPod", "8000:8000", "--address", "127.0.0.1"
) -WindowStyle Hidden

Start-Process kubectl -ArgumentList @(
    "port-forward", "-n", $ns, "svc/aakp-frontend", "8088:80", "--address", "127.0.0.1"
) -WindowStyle Hidden

$fusekiNs = "aakp-knowledge"
$fusekiSvc = kubectl get svc -n $fusekiNs -l app.kubernetes.io/name=fuseki -o jsonpath='{.items[0].metadata.name}' 2>$null
if ($fusekiSvc) {
    Write-Host "Fuseki svc: $fusekiSvc (ns: $fusekiNs)"
    Start-Process kubectl -ArgumentList @(
        "port-forward", "-n", $fusekiNs, "svc/$fusekiSvc", "3030:3030", "--address", "127.0.0.1"
    ) -WindowStyle Hidden
} else {
    Write-Host "WARNING - Fuseki service not found in $fusekiNs"
}

$omSvc = kubectl get svc -n $ns aakp-openmetadata -o jsonpath='{.metadata.name}' 2>$null
if ($omSvc) {
    Write-Host "OpenMetadata svc: $omSvc (ns: $ns)"
    Start-Process kubectl -ArgumentList @(
        "port-forward", "-n", $ns, "svc/aakp-openmetadata", "8585:8585", "--address", "127.0.0.1"
    ) -WindowStyle Hidden
} else {
    Write-Host "WARNING - OpenMetadata service not found in $ns"
}

Start-Sleep -Seconds 3

$apiOk = $false
$feOk = $false
try {
    $apiOk = (Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/assessments" -UseBasicParsing -TimeoutSec 8).StatusCode -eq 200
} catch { Write-Host "API check failed: $($_.Exception.Message)" }
try {
    $feOk = (Invoke-WebRequest -Uri "http://127.0.0.1:8088/" -UseBasicParsing -TimeoutSec 8).StatusCode -eq 200
} catch { Write-Host "Frontend check failed: $($_.Exception.Message)" }

Write-Host ""
if ($apiOk -and $feOk) {
    Write-Host "OK - Open in browser: http://127.0.0.1:8088"
    Write-Host "API direct:          http://127.0.0.1:8000/api/v1/assessments"
    if ($fusekiSvc) {
        Write-Host 'Fuseki UI:           http://127.0.0.1:3030/#/dataset/aakp/query'
    }
    if ($omSvc) {
        Write-Host 'OpenMetadata UI:     http://127.0.0.1:8585  (admin@open-metadata.org / admin)'
        Write-Host 'OpenMetadata (fe):     http://127.0.0.1:8088/openmetadata/'
    }
} else {
    Write-Host "WARNING - port-forward may have failed. Is kubectl cluster running?"
    Write-Host ('  API ok: ' + $apiOk + ' | Frontend ok: ' + $feOk)
}
