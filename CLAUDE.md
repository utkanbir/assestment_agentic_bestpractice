# AAKP Project — Claude Code Instructions

## GitHub Project Board Sync (ZORUNLU)

Her task tamamlandığında veya yeni bir task başladığında GitHub Project board'u güncelle.
**Bunu kullanıcının hatırlatmasını bekleme — otomatik yap.**

### Board Bilgileri
- Development Board ID: `PVT_kwHOAP6I-M4Bap_H`
- Sprint Board ID: `PVT_kwHOAP6I-M4BaqBj`
- Status Field ID: `PVTSSF_lAHOAP6I-M4Bap_HzhVf91g`
- Status Option IDs:
  - Backlog: `3496bf1c`
  - Planned: `85b8f020`
  - In Progress: `47fc9ee4`
  - Review: `e77224fd`
  - Done: `98236657`

### Board Güncelleme Fonksiyonu (PowerShell)

```powershell
function Set-TaskStatus {
    param([string]$itemId, [string]$status)
    $statusMap = @{
        "Done"        = "98236657"
        "In Progress" = "47fc9ee4"
        "Review"      = "e77224fd"
        "Planned"     = "85b8f020"
        "Backlog"     = "3496bf1c"
    }
    $token = gh auth token
    $optionId = $statusMap[$status]
    $mutation = "mutation { updateProjectV2ItemFieldValue(input: { projectId: `"PVT_kwHOAP6I-M4Bap_H`" itemId: `"$itemId`" fieldId: `"PVTSSF_lAHOAP6I-M4Bap_HzhVf91g`" value: { singleSelectOptionId: `"$optionId`" } }) { projectV2Item { id } } }"
    $body = @{ query = $mutation } | ConvertTo-Json -Compress
    Invoke-RestMethod -Uri "https://api.github.com/graphql" -Method Post `
        -Headers @{ Authorization = "Bearer $token"; Accept = "application/vnd.github+json" } `
        -Body $body -ContentType "application/json" | Out-Null
    Write-Host "Board: $status <- $itemId"
}
```

### Kurallar

1. **Task başlarken**: `Set-TaskStatus <itemId> "In Progress"` çağır
2. **Task bitince**: `Set-TaskStatus <itemId> "Done"` çağır
3. **Sprint başında**: O sprint'in tüm task'larını `Planned` olarak işaretle (henüz başlamadıkları için)
4. **Task ID'lerini bulmak için**: `gh project item-list 1 --owner utkanbir --format json --limit 200`

### Sprint 2 Item ID'leri

| Task | Item ID |
|------|---------|
| S2-KA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMNY |
| S2-KA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMNs |
| S2-KA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMOA |
| S2-KA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuMOU |
| S2-KA-005 | PVTI_lAHOAP6I-M4Bap_HzgvuMO0 |
| S2-KA-006 | PVTI_lAHOAP6I-M4Bap_HzgvuMPA |
| S2-KA-007 | PVTI_lAHOAP6I-M4Bap_HzgvuMPY |
| S2-KA-008 | PVTI_lAHOAP6I-M4Bap_HzgvuMP0 |
| S2-KA-009 | PVTI_lAHOAP6I-M4Bap_HzgvuMQE |
| S2-KA-010 | PVTI_lAHOAP6I-M4Bap_HzgvuMQg |
| S2-BA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMQ4 |
| S2-BA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMRY |
| S2-BA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMRs |
| S2-BA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuMSQ |
| S2-BA-005 | PVTI_lAHOAP6I-M4Bap_HzgvuMSY |
| S2-BA-006 | PVTI_lAHOAP6I-M4Bap_HzgvuMTQ |
| S2-BA-007 | PVTI_lAHOAP6I-M4Bap_HzgvuMTw |
| S2-BA-008 | PVTI_lAHOAP6I-M4Bap_HzgvuMT4 |
| S2-BA-009 | PVTI_lAHOAP6I-M4Bap_HzgvuMUU |
| S2-AA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMUg |
| S2-AA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMU4 |
| S2-AA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMVM |
| S2-AA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuMVc |
| S2-AA-005 | PVTI_lAHOAP6I-M4Bap_HzgvuMVo |

## Security

- `ANTHROPIC_API_KEY` asla dosyaya yazılmaz, git'e commit edilmez
- K8s secret olarak yönetilir: `kubectl create secret generic aakp-k8s-agent-secret -n aakp-agent --from-literal=ANTHROPIC_API_KEY=sk-ant-...`

## Docker Image Tag Kuralı

- Sprint1: `sprint1-fix`
- Sprint2: `sprint2-<taskid>` (örn. `sprint2-aa002b`)
- Init container (`alembic-migrate`) ve main container her zaman **aynı tag** kullanmalı
- `kubectl set image deployment/aakp-api alembic-migrate=aakp/api:<tag> api=aakp/api:<tag>`

## Test Komutu

```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_02_api.py -v
```
Hedef: 13/13 passed

## Port-Forward Yeniden Başlatma

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
$pod = kubectl get pod -n aakp-information -l app=aakp-api -o jsonpath='{.items[0].metadata.name}'
Start-Process -FilePath "kubectl" -ArgumentList "port-forward -n aakp-information pod/$pod 8000:8000" -WindowStyle Hidden -PassThru
```
