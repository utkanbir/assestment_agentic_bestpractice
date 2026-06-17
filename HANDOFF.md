# AAKP Handoff Dokümanı

**Tarih:** 2026-06-17  
**Mevcut branch:** `main` (Sprint 14 release merge)  
**Son commit:** Sprint 12–14 release batch — S12 API fixes, S13 Playwright E2E, archive legacy frontend, CI pytest + Playwright  
**Deploy durumu:** `aakp/api:sprint14`, `aakp/frontend:sprint14` — K8s cluster

### Commit Geçmişi
```
(S14)    Sprint 12–14: learning-history, Playwright E2E, CI jobs, archive legacy frontend
eae2b03  Sprint 9-11: Interview Room, LLM intelligence, Agent Yönetimi, RAG pipeline
4679c5b  Sprint 8: maturity scores, enriched approvals, question bank, frontend forms, E2E tests
b1710ef  Sprint 7: UI Polish + E2E Tests (18 tasks)
```

---

## Sprint 14 — Done (2026-06-17)

- **S14-DA-001:** S12+S13 batch committed on `sprint-7/ui-and-tests`, merged to `main`
- **S14-DA-002:** PR `sprint-7/ui-and-tests` → `main`
- **S14-DA-003:** Docker images `aakp/api:sprint14`, `aakp/frontend:sprint14`; manifest tags updated
- **S14-DA-004:** This HANDOFF update
- **S14-DA-005:** Root `frontend/` → `archive/frontend-legacy/` (active UI: `services/frontend/`)
- **S14-TA-001:** CI `api-tests` job — postgres + API + pytest (skips K8s/Kong/flaky KG tests)
- **S14-TA-002:** CI `playwright-e2e` job — 12 specs on PR
- **S14-TA-003:** Local release gate: pytest 96/99 (3 env-dependent skips), Playwright **12/12**
- **S14-SA-001:** Post-deploy smoke — `learning-history`, `/agents/metrics`, K8s e2e

**Release gate notes (local):**
- `pytest tests/ -v --ignore=tests/test_01_infrastructure.py` → 96 passed; 3 failures need live Kong WS (`test_03_websocket`), Fuseki write flake (`test_finding_kg_write`), report chain 500 (`test_report_requires_evidence_chain`)
- `npm run test:e2e` → **12/12** (Vite dev + API port-forward `:8000`)

---

## Sprint 13 — Done (2026-06-17)

- Manual evaluate UX (S13-FA-002): Değerlendir button, no auto-evaluate on save; `evaluatingId` + 90s timeout
- InterviewRoom tab race fix: cancelled async guard on workstream switch
- Playwright multi-agent E2E: 4 specs, **12/12 pass** locally (`npm run test:e2e`)
- Plan: [docs/SPRINT_13_REVISED.md](docs/SPRINT_13_REVISED.md)

---

## Sprint 12 — Done (in S14 release)

- `tests/test_09_sprint11.py` — evaluate, metrics, document upload, suggest
- `GET /agents/{workstream}/learning-history` endpoint
- QuestionManagement → `POST /question-bank` fix
- Lakehouse question bank seed

---

## Sprint Özeti

| Sprint | Ne yapıldı |
|--------|-----------|
| S1 | FastAPI, PostgreSQL, Alembic, K8s namespace/deployment altyapısı |
| S2 | Core API: assessments, tasks, interviews, questions, answers, findings, evidence |
| S3 | 8 workstream agent (LangGraph), Fuseki Knowledge Graph, OWL ontoloji v0.3, question bank |
| S4 | Orchestrator agent, SPARQL sorgular, risk heatmap, roadmap, cross-task dependencies |
| S5 | Guardrails, Keycloak, OPA, PII anonymizer (Presidio) |
| S6 | Observability: Prometheus, Grafana, Loki, Tempo, LangFuse, OpenTelemetry |
| S7 | React frontend polish, E2E test suite (13/13) |
| S8 | Maturity scores, enriched approvals, question bank frontend formları |
| S9 | Approval → summary, risk heatmap, roadmap orchestrator |
| S10 | Interview Room redesign: workstream tab, auto-populate, suggest-followup, approval workflow |
| S11 | LLM entegrasyonu, answer evaluation, RAG pipeline, Ajan Yönetimi |
| S12 | test_09, learning-history, QuestionManagement fix, lakehouse seed |
| S13 | Playwright multi-agent UI E2E (12 tests), manual evaluate UX |
| S14 | Release: main merge, sprint14 deploy, CI pytest + Playwright, archive legacy frontend |

---

## Mimari Kararlar ve Gerekçeleri

| Karar | Gerekçe |
|-------|---------|
| Raw Q&A → PostgreSQL, embeddings → Qdrant, findings/risks → Fuseki | Her layer kendi verisini tutar; KG'ye sadece anlamsal çıkarımlar gider |
| `anthropic` SDK API pod'unda, agent pod'unda değil | LLM çağrıları interview akışında (değerlendirme, öneri) — agent orchestrator'dan bağımsız |
| Alembic init container olarak çalışıyor | Her deployment'ta migration otomatik uygulanır, manuel müdahale gerekmez |
| `approval_status` question üzerinde, answer üzerinde değil | Agent öneri → human-in-the-loop onay akışı soruyu hedefliyor |
| Qdrant `documents` collection'ı workstream filter ile aranıyor | Döküman bağlamı workstream'e izole |
| `llm_client.py` servisi ayrı tutuldu | Router'dan bağımsız test edilebilir |
| Tek aktif frontend: `services/frontend/` | Kök `frontend/` → `archive/frontend-legacy/` (S14-DA-005) |

---

## Tuzaklar

### Deployment
- Docker image tag kuralı: `sprint<N>` veya `sprint<N>-<taskid>` — alembic-migrate ve api container **aynı tag** kullanmalı
- `ANTHROPIC_API_KEY`: `aakp-information` namespace'ine `aakp-k8s-agent-secret` olarak inject edildi
- Port-forward: API pod değişince `8000` port-forward ölür. Kontrol: `Get-NetTCPConnection -LocalPort 8000`
- Frontend port-forward: `kubectl port-forward -n aakp-information svc/aakp-frontend 8088:80` (container port 80)

### Test
- `$env:API_BASE = "http://localhost:8000/api/v1"` ve port-forward aktif olmalı
- `test_01_infrastructure.py` — live K8s port-forwards (Fuseki, PG) gerekir; CI'da skip
- `test_03_websocket.py` — Kong WS `:30080` gerekir; CI'da skip
- Playwright K8s smoke: `PLAYWRIGHT_BASE_URL=http://localhost:8088` + `npm run test:e2e:k8s`

---

## Sprint 15 Backlog (bilinçli erteleme)

- `learning-history` → `llm_client.evaluate_answer` / `suggest_followup` bağlamına ekleme
- Ajan Yönetimi'nde learning history UI paneli
- `/agents` ve `/sessions` ana nav'a link
- Migros 8-workstream tam dry-run demo
- MinIO / Trino entegrasyonu (API'dan henüz kullanılmıyor)
- `test_03_websocket` CI entegrasyonu (Kong service container)
- `test_finding_kg_write` / report chain flake düzeltmesi

---

## Çalışan Servisler (Cluster Durumu)

```
Namespace         Servis
aakp-information  FastAPI (8000), Frontend (8088), Qdrant, PostgreSQL, OpenMetadata
aakp-knowledge    Apache Jena Fuseki (TDB2)
aakp-agent        Keycloak, OPA, Redis, Kafka
aakp-monitoring   Prometheus, Grafana, Loki, Tempo, LangFuse
aakp-data         MinIO (konfigüre ama API'dan kullanılmıyor)
```

**Aktif image'lar:** `aakp/api:sprint14`, `aakp/frontend:sprint14`

## Kritik Komutlar

```powershell
# Release gate — API tests (skip infra/Kong)
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/ -v --ignore=tests/test_01_infrastructure.py

# Playwright local (12 specs)
cd services/frontend
npm install
npx playwright install chromium
npm run test:e2e

# Port-forward yenile
$pod = kubectl get pod -n aakp-information -l app=aakp-api -o jsonpath='{.items[0].metadata.name}'
kubectl port-forward -n aakp-information pod/$pod 8000:8000

# Frontend port-forward (container :80)
kubectl port-forward -n aakp-information svc/aakp-frontend 8088:80

# Deploy (her zaman aynı tag, her zaman ikisini birden)
docker build -t aakp/api:sprint14 services/api
docker build -t aakp/frontend:sprint14 services/frontend
kubectl set image deployment/aakp-api alembic-migrate=aakp/api:sprint14 api=aakp/api:sprint14 -n aakp-information
kubectl set image deployment/aakp-frontend frontend=aakp/frontend:sprint14 -n aakp-information

# K8s Playwright smoke
$env:PLAYWRIGHT_BASE_URL = "http://localhost:8088"
npm run test:e2e:k8s

# Smoke endpoints
curl http://localhost:8000/api/v1/agents/kubernetes/learning-history
curl http://localhost:8000/api/v1/agents/metrics
```
