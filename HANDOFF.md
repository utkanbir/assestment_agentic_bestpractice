# AAKP Handoff Dokümanı

**Tarih:** 2026-06-18  
**Mevcut branch:** `main`  
**Deploy durumu:** `aakp/api:sprint28-fix`, `aakp/frontend:sprint28-v2` — K8s cluster

**Dev note:** Agent'lar uzun testleri (pytest sprint/integration, Playwright e2e, verify-sprint scriptleri) otomatik koşmaz — yalnızca kullanıcı açıkça istediğinde (`CLAUDE.md` → Testing Workflow).

---

## Sprint 28+ — Multi-consultant interview comments (2026-06-18)

- **DB:** `answer_consultant_comments` table (migration `0018_answer_consultant_comments`); legacy `answers.consultant_*` synced from first row
- **API:** `GET` answers include `consultant_comments[]`; `POST/PATCH .../consultant-comments`; `POST .../consultant-comments/{id}/consultant-review`
- **UI:** Interview uses global registry (`listAllConsultants` / `/consultants`); multiple comment rows per answer; no assessment-assignment gate

---

## Sprint 28 — Done (2026-06-18)

- **S28-FA-001:** Çoklu uzmanlık kataloğu (`expertise_catalog.yaml`) + `GET /consultants/expertise-catalog`; `expertise` JSONB array
- **S28-FA-002:** `/danisman` yalnızca **Oluştur** (havuz); atama `AssessmentConsultantPicker` Genel Bakış'ta; `DELETE` unassign
- **S28-FA-003:** Interview `QuestionCard` sırası: Müşteri yanıtı → danışman → AI Yorum + AI Kontrol; `PATCH /answers/{id}`, `POST .../consultant-review`
- **S28-TA:** `tests/test_23_sprint28.py` (6/6), `e2e/sprint28/*` (3/3), `scripts/verify-sprint28.ps1`, CI `test_23`

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_23_sprint28.py -v
.\scripts\verify-sprint28.ps1
```

---

## Sprint 27 — Done (2026-06-18)

- **S27-BA-001:** Simulation stop — task/interview not marked completed mid-workstream; InterviewRoom stop-only + optional "Raporu Oluştur"; poll only while running; WS debounce
- **S27-FA-002:** AssessmentOverview — removed Workstream grid + ConsultantPanel
- **S27-FA-003:** `/danisman` ConsultantManagement page + sidebar nav; Interview add-consultant → `/danisman`
- **S27-FA-004:** Doc upload `preview` in learning_summary; AjanYonetimi summary card + auto docs tab
- **S27-FA-005:** OWL export rdflib merge + `include_instances=true`
- **S27-DA-006:** layers OpenMetadata `/openmetadata/`; KnowledgeArchitecture resolveLink; kong `/health/` Prefix; vite proxy
- **S27-FA-007:** ReportStudio `listConsultants(assessmentId)`; seed opinions on compose; remove batch toolbar button; default first text section
- **S27-TA:** `tests/test_22_sprint27.py` (7/7), `e2e/sprint27/*` (8/8), `scripts/verify-sprint27.ps1`

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_22_sprint27.py -v
.\scripts\verify-sprint27.ps1
```

---

## Sprint 26 — Done (2026-06-18)

- **S26-FA-001:** AssessmentOverview — kart üzerinde Kopyala/Yapıştır; sessionStorage `aakp_last_copied_assessment_id`; kart tıklama = seçim; Interview'a git butonu; `listAgents` kaldırıldı
- **S26-BA-002:** `simulation_runner` — `asyncio.wait_for` evaluate 120s; WS `primary_interview_id`; InterviewRoom timeline replay + stop progress bar
- **S26-BA-003:** `generate-summary` try/except mock 200; ExecutiveSummary `.txt` export; `fetchJSON` ApiError + detail parse
- **S26-FA-004:** `ConsultantPanel` overview'da; InterviewRoom her zaman yorum alanı + danışman seç/link
- **S26-FA-005:** Agent training `consultant_id`; doc upload `learning_summary`; AjanYonetimi history + OWL export `GET /knowledge/ontology/export.ttl`
- **S26-FA-006:** `agent_type` kubernetes/workstream tutarlılığı Overview + InterviewRoom
- **S26-DA-007:** nginx `/health/` proxy; `layers.yaml` link_mode/internal; TechStackPage system URL fix
- **S26-FA-008:** ReportStudio `consultant_opinions[]`; mor "Tüm Raporu AI ile Yaz" üst CTA
- **S26 duplicate:** `consultant_id` + `consultant_comment` answer kopyası
- **S26-TA:** `tests/test_21_sprint26.py` (15/15), `e2e/sprint26/*` (12/12), `scripts/verify-sprint26.ps1`, CI `test_21`
- **S26 hotfix:** `agent_mgmt` doc upload `db.flush()`; simülasyon navigate `assessment_id` doğrudan URL

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_21_sprint26.py -v
.\scripts\verify-sprint26.ps1
cd services/frontend && npm run test:e2e -- e2e/sprint26
```

---

## Sprint 25 — Done (2026-06-17)

- **S25-FA-001:** Lazy `GraphCanvas` (`@xyflow/react`); OntologyBrowser Liste|Graf; KnowledgeGraphExplorer Graf|Tablo; simulated assessment mor node
- **S25-FA-002:** ApprovalQueue HITL banner + Roadmap/Heatmap linkleri; ConsolidatedRoadmap empty-state wizard; `POST /orchestrator/{id}/generate-recommendations`
- **S25-FA-003:** Report section `consultant_comment` / `consultant_approved`; ReportStudio danışman textarea + AI kontrol + onay; `POST /reports/{id}/consultant-review`
- **S25-FA-004:** `/teknoloji` route + `TechStackPage` (GET `/architecture/layers` tablo)
- **S25-DA-001:** `layers.yaml` PG `/health/db`, Qdrant env override, MinIO/Kafka `active_in_api`; `deploy.ps1` OpenMetadata + Trino; Kong/nginx OpenMetadata route; KnowledgeArchitecture assessment banner; `GET /health/db`
- **S25-TA-001:** `tests/test_20_sprint25.py`

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_20_sprint25.py -v
```

---

## Sprint 24 — Done (2026-06-17)

- **S24-BA-001:** Migration `0015` — `agent_learning_events` (mode: aaha|text|document); `POST /agents/{ws}/train/aaha` (LLM soru); `POST .../train/aaha/answer` (Qdrant embed + KG `TrainingInteraction` + layer touch)
- **S24-BA-002:** `POST /agents/{ws}/train/text` — chunk, Qdrant embed, KG `AgentKnowledge`, learning event
- **S24-FA-001:** `AjanYonetimi.tsx` — AAHA Eğitimi, Metin Bilgi, Bilgi Tabanı sekmeleri
- **S24-FA-002:** `GET /agents/{ws}/graph`; lazy `AgentOntologyGraph` (`@xyflow/react`) — Ontoloji Grafiği sekmesi
- **Ontology:** `TrainingInteraction`, `AgentKnowledge` sınıfları + property'ler (`assessment.ttl`)
- **S24-TA-001:** `tests/test_19_sprint24.py`

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_19_sprint24.py -v
```

---

## Sprint 23 — Done (2026-06-17)

- **S23-BA-001:** Migration `0014` — `consultants`, `assessment_consultants`, answer `consultant_id`/`consultant_comment`, `assessment.consultant_synthesis`; `/consultants` CRUD + `POST /assessments/{id}/consultants`; ontology `Consultant`, `hasConsultant`, `consultantComment`; KG `insert_consultant` + `write_consultant_on_answer`
- **S23-FA-001:** InterviewRoom `QuestionCard` — danışman dropdown + yorum alanı; `api.ts` `listConsultants`, `assignConsultant`, genişletilmiş `addAnswerFull`
- **S23-BA-002:** `POST /assessments/{id}/consultant-synthesis` — LLM toplu özet → `consultant_synthesis`; InterviewRoom footer "AI Toplu Değerlendirme"
- **S23-FA-002:** InterviewRoom collapsible "Bulgu Oluştur" — `POST /evidences` + `POST /findings`
- **S23-BA-003:** `POST /assessments/{id}/maturity/{workstream}/ai-suggest`; MaturityDashboard "AI Öner"
- **S23-FA-003:** SuggestionCard "Bankaya da ekle" checkbox — onayda `POST /question-bank`
- **S23 global bank UX:** QuestionManagement subtitle + `deleteWorkstreamQuestion` (DELETE `/question-bank/{id}`)
- **S23-TA-001:** `tests/test_18_sprint23.py`

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_18_sprint23.py -v
```

---

## Sprint 22 — Done (2026-06-17)

- **S22-BA-001:** `POST /assessments/{id}/duplicate` — metadata kopyası; opsiyonel task + interview + Q&A (findings hariç)
- **S22-BA-002:** `generate-summary` findings yokken 422 yerine Q&A + maturity özeti (`build_simulation_exec_summary`); `GET /assessments/{id}/interviews/latest`
- **S22-FA-001:** AssessmentOverview — kart tıklama → interview; ⋮ menü (Sil/Kopyala); workstream interview `?workstream=`
- **S22-FA-002:** InterviewRoom — URL workstream; eksik soru bankası senkronu + "Eksik soruları yükle"
- **S22-FA-003:** QuestionManagement — `getLatestInterview` auto-resolve; InterviewRoom → Sorular linki
- **S22-FA-004:** InterviewRoom simülasyon timeline paneli (steps + WS), auto-scroll, tek Durdur butonu, mount replay
- **S22-TA-001:** `tests/test_17_sprint22.py`

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_17_sprint22.py -v
```

---

## Sprint 21 — Done (2026-06-17)

- **S21-BA-001:** Migration `0013` — `assessment_mode`, `simulation_status`, `simulation_progress`, `company_profile`
- **S21-BA-002:** `simulation_runner.py` — 8 workstream sequential Q&A + evaluate + KG writes; stop checkpoint; SQL `update()` for `simulation_progress` (JSONB in-place mutation fix)
- **S21-BA-003:** `POST /assessments/simulated`, `.../simulation/stop|status|finalize`
- **S21-BA-004:** `generate_simulated_answer()` + ontology `Evaluation`, `isSimulated`, `assessmentMode`
- **S21-BA-005:** WS events: `question.asked`, `answer.evaluated`, `simulation.progress|stopped|completed`, `kg.updated`
- **S21-FA-001:** AssessmentOverview AI Simülasyon modal + purple simulated cards
- **S21-FA-002:** InterviewRoom watch mode (`?simulation=1`), stop button, redirect to report
- **S21-FA-003:** KnowledgeGraphExplorer auto-refresh + simulated banner
- **S21-TA-001:** `tests/test_16_sprint21.py` + `e2e/simulation/*.spec.ts` + CI `test_16`
- **S21-DA-001:** Manifest `sprint21-fix` (API), `sprint21` (frontend)

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_16_sprint21.py -v
cd services/frontend && npm run test:e2e -- e2e/simulation
```

---

## Sprint 20 — Done (2026-06-17)

- **S20-BA-001:** `report_ai.py` — assessment context + per-section generation + mock fallback
- **S20-BA-002:** `POST /reports/{id}/ai-generate` — text/table body, chart/kpi `commentary`, cover `subtitle`
- **S20-FA-001:** ReportStudio per-section ✨ AI + batch "Tüm Bölümleri AI ile Yaz" + auto-save
- **S20-FA-002:** Commentary textarea (chart/kpi) + export HTML/PDF/DOCX commentary desteği
- **S20-FA-003:** Sol sidebar navigasyon (`AppSidebar` + `navIcons.tsx`), üst bar yalnızca assessment seçici
- **S20-TA-001:** `tests/test_15_sprint20.py` + `e2e/report/report-ai-generate.spec.ts` + `e2e/navigation/sidebar.spec.ts`
- **S20-DA-001:** Manifest `sprint20`, CI `test_15`

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_15_sprint20.py tests/test_13_sprint18.py -v
cd services/frontend && npm run test:e2e
```

---

## Sprint 19 — Done (2026-06-17)

- **S19-FA-001:** Chat optimistic user bubble + `loadMessages` race guard
- **S19-FA-002:** Workstream seçici kaldırıldı; `general` oturum
- **S19-BA-001:** `chat_platform.py` — assessment count + platform context
- **S19-BA-002:** `explain_narrative.py` + `GET /transactions/{id}` narrative alanı
- **S19-FA-003:** Yürütme Planı cümle bazlı EXPLAIN PLAN + collapsible teknik tablo
- **S19-DA-001:** sprint19 image tag + ReportStudio boş state CTA
- **S19-TA-001:** `tests/test_14_sprint19.py` + e2e güncellemeleri

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_14_sprint19.py tests/test_13_sprint18.py -v
```

---

## Sprint 18 — Done (2026-06-17)

- **S18-BA-001:** `content_json` şeması + `POST /reports/assessment/{id}/compose` + `PATCH` (`ReportUpdate`)
- **S18-BA-002:** `POST /reports/{id}/ai-edit` — bölüm bazlı AI düzenleme
- **S18-BA-003:** `POST /reports/{id}/export/pdf` (xhtml2pdf) + `export/docx` (python-docx)
- **S18-BA-004:** `GET /chat/sessions/{id}`, `GET .../messages`, `PATCH` session; çok turlu LLM history
- **S18-FA-001/002:** `ReportStudio` hibrit editör — bölüm listesi, text/table/chart/kpi blokları, kaydet
- **S18-FA-003:** AI düzenleme UI (mod seçici + bölüm bazlı)
- **S18-FA-004:** PDF/Word indirme butonları
- **S18-FA-005:** `/chat` tam sayfa + nav + FAB → `/chat` redirect
- **S18-FA-006:** `validate_evidence_chain` Task join fix
- **S18-TA-001:** `tests/test_13_sprint18.py`
- **S18-TA-002:** `e2e/report/report-studio.spec.ts` + `e2e/chat/chat-page.spec.ts`
- **S18-DA-001:** Manifest `sprint18`, CI `test_13`, HANDOFF

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_13_sprint18.py -v
cd services/frontend && npm run test:e2e
```

---

## Sprint 17 — Done (2026-06-17)

- **S17-FA-001:** Tüm route'larda `RequireAssessment` + `AssessmentPageHeader`; sayfalar `useAssessment` kullanır
- **S17-FA-002:** `/agents` ve `/sessions` kaldırıldı; workstream ajan başlatma Genel Bakış'a taşındı
- **S17-FA-003:** İnceleme Merkezi (3 sekme: ajan önerileri, bulgu/risk/öneri) + nav badge
- **S17-BA-003:** `GET /approvals/pending-questions`, approval filter fix, `reviewer_note` persist
- **S17-BA-001:** Enriched executive summary API (workstream summaries, top risks, maturity, deps)
- **S17-FA-006:** Yönetici Özeti sayfası redesign
- **S17-BA-002 + S17-FA-007:** Roadmap horizon/title + `POST generate-roadmap` + 3-şerit UI
- **S17-FA-004:** Risk Heatmap KPI + finding drill-down endpoint
- **S17-FA-005:** Olgunluk radar chart + workstream kartları + `target_score`
- **S17-TA-001:** `tests/test_12_sprint17.py` + `e2e/knowledge/sprint17-assessment-ux.spec.ts`
- **S17-DA-001:** Migration `0012`, manifest `sprint17`

---

## Sprint 16 — Done (2026-06-17)

- **S16-FA-001:** Global `AssessmentContext` (URL `assessment_id` + localStorage fallback), global nav selector, `RequireAssessment`
- **S16-FA-002/003:** Yeni sayfalar: `/ontoloji` (TBox schema browser), `/knowledge-graph` (assessment graph explorer)
- **S16-BA-001/002:** Q&A KG write (`insert_question`, `insert_answer`) + evaluate adiminda ontology context read (knowledge/fuseki touch)
- **S16-FA/BA-004/005:** Mimari drill-down: layer click -> teknoloji linkleri + `layer` filtresi ile touch timeline
- **S16-BA/FA-003/005:** Standalone chat API (`/chat/sessions`, `/chat/sessions/{id}/messages`) + App shell `ChatWidget`
- **S16-BA/FA-006:** Transaction modeli (`layer_transactions`, `transaction_id`, `step_order`) + `/yurutme-plani` execution plan UI
- **S16-TA-001/002:** `tests/test_11_sprint16.py` + `e2e/knowledge/sprint16-knowledge.spec.ts`; CI job `test_11` dahil
- **S16-DA-001:** Manifest image tagleri `sprint16`

---

## Sprint 15 — Done (2026-06-17)

- **S15-BA-001:** `layers.yaml` registry + `GET /api/v1/architecture/layers` (4 katman)
- **S15-BA-002:** `layer_touch_events` tablosu + `LayerTouchService`
- **S15-BA-003–006:** Golden-path instrumentation (evaluate, suggest, save answer, kg_writer) + touch API + WS `layer.touch`
- **S15-FA-001/002:** `/mimari` Knowledge Architecture sayfası — katman stack + canlı timeline
- **S15-FA-003:** InterviewRoom mini trace panel + nav (`Mimari`, `Ajanlar`, `Oturumlar`)
- **S15-TA-001:** `tests/test_10_sprint15.py`
- **S15-TA-002:** `e2e/architecture/layer-touch.spec.ts`
- **S15-DA-001:** CI genişletildi, manifest `sprint15`, HANDOFF güncellendi

**Test komutları:**
```powershell
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/test_10_sprint15.py -v
cd services/frontend && npm run test:e2e
```

**Mimari sayfa:** `/mimari?assessment_id=...&interview_id=...`

---
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
- **S14-TA-003:** Local release gate: pytest **77/77** (release subset), Playwright **12/12** local + **12/12** K8s
- **S14-SA-001:** Post-deploy smoke — `learning-history` 200, `/agents/metrics` 8 workstreams, `aakp-api-secret` present, K8s e2e **12/12**

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
| S15 | Knowledge Architecture UI, layer touch instrumentation, `/mimari` |

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

## Sprint 16 Backlog (bilinçli erteleme)

- `learning-history` → LLM prompt bağlamı
- MinIO / Trino gerçek API entegrasyonu
- `evaluate_answer`'a ontology snippet (Fuseki) — Knowledge katman touch
- Tüm endpoint instrumentation
- react-flow KG graph görselleştirmesi

---

## Sprint 15 Backlog (tamamlandı — S16'ya taşınanlar yukarıda)

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
