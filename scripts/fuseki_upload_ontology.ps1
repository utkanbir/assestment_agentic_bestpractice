#!/usr/bin/env pwsh
# Fuseki'ye AAKP ontoloji dosyalarini yukler.
# Kimlik bilgisi: aakp-knowledge namespace'indeki aakp-fuseki-secret'tan okunur.
# Kullanim: .\scripts\fuseki_upload_ontology.ps1

param(
    [string]$FusekiUrl   = "http://localhost:3030",
    [string]$Dataset     = "aakp",
    [string]$Namespace   = "aakp-knowledge",
    [string]$SecretName  = "aakp-fuseki-secret",
    [string]$SecretKey   = "admin-password"
)

Set-StrictMode -Off

# 1. Port-forward yoksa ac
$pf = Get-NetTCPConnection -LocalPort 3030 -ErrorAction SilentlyContinue
if (-not $pf) {
    Write-Host "Port-forward baslatiliyor (localhost:3030 -> aakp-knowledge svc/aakp-fuseki)..."
    $pod = kubectl get pod -n $Namespace -l app=aakp-fuseki -o jsonpath='{.items[0].metadata.name}' 2>$null
    if (-not $pod) {
        Write-Error "Fuseki pod bulunamadi. Kubernetes baglantisini kontrol edin."
        exit 1
    }
    Start-Process pwsh -ArgumentList "-Command kubectl port-forward -n $Namespace pod/$pod 3030:3030" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# 2. Admin sifresini secret'tan oku
$b64 = kubectl get secret $SecretName -n $Namespace -o "jsonpath={.data.$SecretKey}" 2>$null
if (-not $b64) {
    Write-Error "Secret '$SecretName' okunamadi. kubectl erisimi kontrol edin."
    exit 1
}
$password = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($b64))
$cred     = "admin:$password"
$encoded  = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($cred))
$headers  = @{
    Authorization = "Basic $encoded"
    Accept        = "application/json"
}

# 3. Fuseki'nin ayakta oldugunu dogrula
try {
    Invoke-RestMethod -Uri "$FusekiUrl/`$/ping" -TimeoutSec 5 | Out-Null
    Write-Host "Fuseki erisim OK: $FusekiUrl"
} catch {
    Write-Error "Fuseki'ye ulasilamadi: $FusekiUrl — port-forward calistigindan emin olun."
    exit 1
}

# 4. Yuklenecek dosyalar: graph URI -> dosya yolu
$uploads = @(
    @{
        file  = "knowledge/ontology/assessment.ttl"
        graph = "https://aakp.ai/ontology/assessment"
    }
    @{
        file  = "knowledge/ontology/architecture.ttl"
        graph = "https://aakp.ai/ontology/architecture"
    }
    @{
        file  = "knowledge/ontology/maturity.ttl"
        graph = "https://aakp.ai/ontology/maturity"
    }
    @{
        file  = "knowledge/ontology/organization.ttl"
        graph = "https://aakp.ai/ontology/organization"
    }
    @{
        file  = "knowledge/shacl/full_entity_shapes.ttl"
        graph = "https://aakp.ai/shacl/full"
    }
)

$ok    = 0
$fail  = 0

foreach ($u in $uploads) {
    $path = Join-Path (Get-Location) $u.file
    if (-not (Test-Path $path)) {
        Write-Warning "Dosya bulunamadi, atlaniyor: $($u.file)"
        $fail++
        continue
    }
    $body = Get-Content $path -Raw -Encoding UTF8
    $uri  = "$FusekiUrl/$Dataset/data?graph=$([System.Uri]::EscapeDataString($u.graph))"
    try {
        Invoke-RestMethod -Uri $uri -Method Put -Body $body `
            -ContentType "text/turtle; charset=utf-8" `
            -Headers $headers | Out-Null
        Write-Host "  OK  $($u.file) -> $($u.graph)"
        $ok++
    } catch {
        Write-Warning "  FAIL $($u.file): $($_.Exception.Message)"
        $fail++
    }
}

Write-Host ""
Write-Host "Sonuc: $ok basarili / $fail basarisiz"
if ($fail -gt 0) { exit 1 }
