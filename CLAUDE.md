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

### Sprint 2 Item ID'leri (tamamlandı)

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

### Sprint 3 Item ID'leri

| Task | Item ID |
|------|---------|
| S3-AA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuNAs |
| S3-AA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMYA |
| S3-AA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMYg |
| S3-AA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuMY4 |
| S3-AA-005 | PVTI_lAHOAP6I-M4Bap_HzgvuMZc |
| S3-AA-006 | PVTI_lAHOAP6I-M4Bap_HzgvuMZw |
| S3-AA-007 | PVTI_lAHOAP6I-M4Bap_HzgvuMaM |
| S3-AA-008 | PVTI_lAHOAP6I-M4Bap_HzgvuMaY |
| S3-AA-009 | PVTI_lAHOAP6I-M4Bap_HzgvuMa4 |
| S3-AA-010 | PVTI_lAHOAP6I-M4Bap_HzgvuMbQ |
| S3-AA-011 | PVTI_lAHOAP6I-M4Bap_HzgvuMbw |
| S3-AA-012 | PVTI_lAHOAP6I-M4Bap_HzgvuMcM |
| S3-AA-013 | PVTI_lAHOAP6I-M4Bap_HzgvuMco |
| S3-AA-014 | PVTI_lAHOAP6I-M4Bap_HzgvuMdE |
| S3-BA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMd0 |
| S3-BA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMeI |
| S3-BA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMeg |
| S3-BA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuMfA |
| S3-BA-005 | PVTI_lAHOAP6I-M4Bap_HzgvuMfQ |
| S3-BA-006 | PVTI_lAHOAP6I-M4Bap_HzgvuMf8 |
| S3-KA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMgA |
| S3-KA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMgQ |
| S3-KA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMgU |
| S3-FA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMgo |
| S3-FA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMg8 |
| S3-FA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMhE |

### Sprint 4 Item ID'leri

| Task | Item ID |
|------|---------|
| S4-AA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMhg |
| S4-AA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMhs |
| S4-AA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMiA |
| S4-AA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuMiM |
| S4-AA-005 | PVTI_lAHOAP6I-M4Bap_HzgvuMig |
| S4-AA-006 | PVTI_lAHOAP6I-M4Bap_HzgvuNA0 |
| S4-AA-007 | PVTI_lAHOAP6I-M4Bap_HzgvuMkQ |
| S4-AA-008 | PVTI_lAHOAP6I-M4Bap_HzgvuMks |
| S4-KA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMk8 |
| S4-KA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMlY |
| S4-KA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMlg |
| S4-KA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuMmA |
| S4-FA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMmc |
| S4-FA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMmk |
| S4-FA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMnM |
| S4-FA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuNBQ |

### Sprint 5 Item ID'leri

| Task | Item ID |
|------|---------|
| S5-SA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMpw |
| S5-SA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMqA |
| S5-SA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMqc |
| S5-SA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuMqs |
| S5-SA-005 | PVTI_lAHOAP6I-M4Bap_HzgvuMq8 |
| S5-SA-006 | PVTI_lAHOAP6I-M4Bap_HzgvuMrc |
| S5-SA-007 | PVTI_lAHOAP6I-M4Bap_HzgvuMrs |
| S5-SA-008 | PVTI_lAHOAP6I-M4Bap_HzgvuMr4 |
| S5-SA-009 | PVTI_lAHOAP6I-M4Bap_HzgvuMsU |
| S5-SA-010 | PVTI_lAHOAP6I-M4Bap_HzgvuMsg |
| S5-BA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMs0 |
| S5-BA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMs8 |
| S5-BA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMtU |
| S5-BA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuMtw |
| S5-BA-005 | PVTI_lAHOAP6I-M4Bap_HzgvuMt8 |
| S5-AA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMuQ |
| S5-AA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMuw |
| S5-AA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMvA |
| S5-AA-004 | PVTI_lAHOAP6I-M4Bap_HzgvuMvM |
| S5-AA-005 | PVTI_lAHOAP6I-M4Bap_HzgvuMvk |
| S5-AA-006 | PVTI_lAHOAP6I-M4Bap_HzgvuMvs |
| S5-AA-007 | PVTI_lAHOAP6I-M4Bap_HzgvuMwM |
| S5-KA-001 | PVTI_lAHOAP6I-M4Bap_HzgvuMwU |
| S5-KA-002 | PVTI_lAHOAP6I-M4Bap_HzgvuMwk |
| S5-KA-003 | PVTI_lAHOAP6I-M4Bap_HzgvuMww |

### Sprint 22 Item ID'leri (22-madde plan — Planned)

| Task | Issue | Item ID |
|------|-------|---------|
| S22-FA-001 | #251 | PVTI_lAHOAP6I-M4Bap_HzgwE0aU |
| S22-FA-002 | #252 | PVTI_lAHOAP6I-M4Bap_HzgwE0a8 |
| S22-FA-003 | #253 | PVTI_lAHOAP6I-M4Bap_HzgwE0bs |
| S22-FA-004 | #254 | PVTI_lAHOAP6I-M4Bap_HzgwE0cY |
| S22-BA-001 | #255 | PVTI_lAHOAP6I-M4Bap_HzgwE0do |
| S22-BA-002 | #256 | PVTI_lAHOAP6I-M4Bap_HzgwE0e8 |

### Sprint 23 Item ID'leri (Planned)

| Task | Issue | Item ID |
|------|-------|---------|
| S23-BA-001 | #257 | PVTI_lAHOAP6I-M4Bap_HzgwE0f0 |
| S23-FA-001 | #258 | PVTI_lAHOAP6I-M4Bap_HzgwE0g8 |
| S23-BA-002 | #259 | PVTI_lAHOAP6I-M4Bap_HzgwE0h4 |
| S23-FA-002 | #260 | PVTI_lAHOAP6I-M4Bap_HzgwE0jA |
| S23-BA-003 | #261 | PVTI_lAHOAP6I-M4Bap_HzgwE0kc |
| S23-FA-003 | #262 | PVTI_lAHOAP6I-M4Bap_HzgwE0l0 |

### Sprint 24 Item ID'leri (Done)

| Task | Issue | Item ID |
|------|-------|---------|
| S24-BA-001 | #263 | PVTI_lAHOAP6I-M4Bap_HzgwE0nA |
| S24-BA-002 | #264 | PVTI_lAHOAP6I-M4Bap_HzgwE0oQ |
| S24-FA-001 | #265 | PVTI_lAHOAP6I-M4Bap_HzgwE0pY |
| S24-FA-002 | #266 | PVTI_lAHOAP6I-M4Bap_HzgwE0qc |

### Sprint 25 Item ID'leri (Done)

| Task | Issue | Item ID |
|------|-------|---------|
| S25-FA-001 | #267 | PVTI_lAHOAP6I-M4Bap_HzgwE0sI |
| S25-FA-002 | #268 | PVTI_lAHOAP6I-M4Bap_HzgwE0s8 |
| S25-FA-003 | #269 | PVTI_lAHOAP6I-M4Bap_HzgwE0uU |
| S25-FA-004 | #270 | PVTI_lAHOAP6I-M4Bap_HzgwE0vI |
| S25-DA-001 | #271 | PVTI_lAHOAP6I-M4Bap_HzgwE0wk |

## Dev & Deploy Workflow

**Günlük geliştirme (local veya cluster port-forward):**
```powershell
.\scripts\dev-local.ps1                        # cluster API/UI + manual instructions
.\scripts\dev-local.ps1 -StartApi -StartFrontend # local uvicorn + vite (infra via port-forward)
```

**Cluster'a hızlı deploy (build + patch manifest + apply):**
```powershell
.\scripts\deploy-quick.ps1                       # both, tag dev-yyyyMMdd-HHmm
.\scripts\deploy-quick.ps1 -Target frontend      # sadece frontend
.\scripts\deploy-quick.ps1 -Target api -Tag dev-fix
```

## Security

- `ANTHROPIC_API_KEY` asla dosyaya yazılmaz, git'e commit edilmez
- K8s secret olarak yönetilir: `kubectl create secret generic aakp-k8s-agent-secret -n aakp-agent --from-literal=ANTHROPIC_API_KEY=sk-ant-...`

## Docker Image Tag Kuralı

- Sprint1: `sprint1-fix`
- Sprint2: `sprint2-<taskid>` (örn. `sprint2-aa002b`)
- Sprint3: `sprint3-<taskid>` (örn. `sprint3-aa001`)
- Init container (`alembic-migrate`) ve main container her zaman **aynı tag** kullanmalı
- `kubectl set image deployment/aakp-api alembic-migrate=aakp/api:<tag> api=aakp/api:<tag>`

## Testing Workflow

**Agent default:** Uzun testleri otomatik çalıştırma — kullanıcı açıkça istemedikçe.

**Do NOT automatically run:**
- pytest integration / sprint testleri (`test_23_sprint28.py`, `test_22_sprint27.py`, vb.)
- Playwright e2e (`npm run test:e2e`, `e2e/sprint*/`, `scripts/verify-sprint*.ps1`)
- Tam test suite'leri (`pytest tests/`, CI equivalent local runs)

**Only run long tests when the user explicitly asks**, e.g. "testleri çalıştır", "e2e koş", "verify sprint".

**Quick local checks OK** when needed for a fix: single targeted unit test, lint/typecheck.

## Test Komutu (manuel — agent otomatik koşmaz)

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
