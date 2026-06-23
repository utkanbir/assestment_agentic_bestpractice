# AAKP quick deploy - build selected images, patch manifests, apply, rollout
# Usage:
#   .\scripts\deploy-quick.ps1
#   .\scripts\deploy-quick.ps1 -Target api -Tag dev-fix
#   .\scripts\deploy-quick.ps1 -Target frontend

param(
    [ValidateSet("api", "frontend", "both")]
    [string]$Target = "both",
    [string]$Tag = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$ManifestDir = Join-Path $Root "infra\helm\information-layer"
$Ns = "aakp-information"

if (-not $Tag) {
    $Tag = "dev-$(Get-Date -Format 'yyyyMMdd-HHmm')"
}

function Write-Step { param([string]$Msg) Write-Host "`n=== $Msg ===" -ForegroundColor Cyan }
function Write-OK   { param([string]$Msg) Write-Host "OK  $Msg" -ForegroundColor Green }

function Set-ManifestImageTag {
    param(
        [string]$Path,
        [string]$ImagePrefix,
        [string]$NewTag
    )
    $content = Get-Content -Path $Path -Raw -Encoding UTF8
    $pattern = "(image:\s*$([regex]::Escape($ImagePrefix)):)[^\s#]+"
    $updated = [regex]::Replace($content, $pattern, "`${1}$NewTag")
    if ($updated -eq $content) {
        throw "No image line matching '$ImagePrefix' found in $Path"
    }
    Set-Content -Path $Path -Value $updated -Encoding UTF8 -NoNewline
}

Write-Step "Quick deploy - Target=$Target Tag=$Tag"

$built = @()
$applied = @()

if ($Target -in @("api", "both")) {
    Write-Step "Building aakp/api:$Tag"
    docker build -t "aakp/api:$Tag" (Join-Path $Root "services\api")
    if ($LASTEXITCODE -ne 0) { throw "docker build api failed" }
    Write-OK "aakp/api:$Tag"

    $apiManifest = Join-Path $ManifestDir "api-manifest.yaml"
    Set-ManifestImageTag -Path $apiManifest -ImagePrefix "aakp/api" -NewTag $Tag
    Write-OK "Patched api-manifest.yaml -> aakp/api:$Tag (init + main)"

    Write-Step "Applying api-manifest.yaml"
    kubectl apply -f $apiManifest
    if ($LASTEXITCODE -ne 0) { throw "kubectl apply api-manifest failed" }

    Write-Step "Waiting for aakp-api rollout (180s)"
    kubectl rollout status deployment/aakp-api -n $Ns --timeout=180s
    if ($LASTEXITCODE -ne 0) { throw "aakp-api rollout failed" }

    $built += "aakp/api:$Tag"
    $applied += "api-manifest.yaml"
}

if ($Target -in @("frontend", "both")) {
    Write-Step "Building aakp/frontend:$Tag"
    docker build -t "aakp/frontend:$Tag" (Join-Path $Root "services\frontend")
    if ($LASTEXITCODE -ne 0) { throw "docker build frontend failed" }
    Write-OK "aakp/frontend:$Tag"

    $feManifest = Join-Path $ManifestDir "frontend-manifest.yaml"
    Set-ManifestImageTag -Path $feManifest -ImagePrefix "aakp/frontend" -NewTag $Tag
    Write-OK "Patched frontend-manifest.yaml -> aakp/frontend:$Tag"

    Write-Step "Applying frontend-manifest.yaml"
    kubectl apply -f $feManifest
    if ($LASTEXITCODE -ne 0) { throw "kubectl apply frontend-manifest failed" }

    Write-Step "Waiting for aakp-frontend rollout (180s)"
    kubectl rollout status deployment/aakp-frontend -n $Ns --timeout=180s
    if ($LASTEXITCODE -ne 0) { throw "aakp-frontend rollout failed" }

    $built += "aakp/frontend:$Tag"
    $applied += "frontend-manifest.yaml"
}

Write-Step "Restarting port-forwards"
& (Join-Path $PSScriptRoot "start-port-forwards.ps1")

Write-Host ""
Write-Host "=== Deploy summary ===" -ForegroundColor Green
Write-Host "Tag:       $Tag"
Write-Host "Built:     $($built -join ', ')"
Write-Host "Applied:   $($applied -join ', ')"
Write-Host "Frontend:  http://127.0.0.1:8088"
Write-Host "API:       http://127.0.0.1:8000/api/v1/assessments"
