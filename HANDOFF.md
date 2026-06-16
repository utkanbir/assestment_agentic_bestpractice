# AAKP Handoff Dokümanı

**Tarih:** 2026-06-17  
**Mevcut branch:** `sprint-7/ui-and-tests` (isim yanıltıcı — Sprint 8-11 kodu burada)  
**Son commit:** Sprint 9-11 (`eae2b03`) — 45 dosya, 5285 ekleme  
**Deploy durumu:** Sprint 11 kodu K8s'de canlı ve git'te commit edildi.

### Commit Geçmişi
```
eae2b03  Sprint 9-11: Interview Room, LLM intelligence, Agent Yönetimi, RAG pipeline
4679c5b  Sprint 8: maturity scores, enriched approvals, question bank, frontend forms, E2E tests
b1710ef  Sprint 7: UI Polish + E2E Tests (18 tasks)
```

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
| S9 | (test_07_sprint9.py mevcut ama içeriği bilinmiyor — kontrol et) |
| S10 | Interview Room redesign: workstream tab, auto-populate questions, suggest-followup, approval workflow, agent-status endpoint, ontology v0.4 |
| S11 | LLM entegrasyonu (Claude API), answer evaluation, agent soru önerisi, RAG pipeline, Ajan Yönetimi sayfası — **commit edilmedi** |

---

## Şu An Yarım Kalan / Dikkat Gerektiren

### 1. ~~GİT'E HİÇBİR ŞEY COMMIT EDİLMEDİ (S9-S11)~~ ✅ TAMAMLANDI
`eae2b03` commit'i ile 45 dosya, Sprint 9-11 arası tüm değişiklik commit edildi (2026-06-17).
Branch: `sprint-7/ui-and-tests` — henüz main'e merge edilmedi.

### 2. Sprint 11 E2E Testi Yok
`tests/test_09_sprint11.py` hiç oluşturulmadı. Test edilmesi gereken endpointler:
- `POST /interviews/answers/{id}/evaluate`
- `GET /agents/metrics` ve `GET /agents/metrics/{workstream}`
- `POST /agents/{workstream}/documents`
- `POST /question-bank/suggest`

### 3. QuestionManagement "Soru Ekle" Çakışması
`handleAddQuestion` içinde `interviewId` yoksa alert fırlatıyor (`"Soru eklemek için URL'de interview_id gerekli"`). Soru bankası sayfası interview context'siz de çalışmalı — şu an `WorkstreamQuestion` (question_bank tablosu) değil, `Question` (interviews tablosuna bağlı) yaratıyor. Bu yanlış. Düzeltme: `POST /question-bank` endpoint'ini çağırmalı.

### 4. İki Ayrı Frontend Var
- `frontend/` (proje kökünde) → farklı bir kodebase, `client.ts`/`Layout.tsx` yapısı var, kimin yazdığı belirsiz, deployed değil
- `services/frontend/` → aktif, Vite + React, K8s'de deploy edilen bu

`git status`'ta `frontend/src/App.tsx` modified görünüyor — bu başka biri tarafından değiştiriliyor olabilir. Birleştirme sırasında çakışma çıkarabilir.

---

## Mimari Kararlar ve Gerekçeleri

| Karar | Gerekçe |
|-------|---------|
| Raw Q&A → PostgreSQL, embeddings → Qdrant, findings/risks → Fuseki | Her layer kendi verisini tutar; KG'ye sadece anlamsal çıkarımlar gider |
| `anthropic` SDK API pod'unda, agent pod'unda değil | LLM çağrıları interview akışında (değerlendirme, öneri) — agent orchestrator'dan bağımsız |
| Alembic init container olarak çalışıyor | Her deployment'ta migration otomatik uygulanır, manuel müdahale gerekmez |
| `approval_status` question üzerinde, answer üzerinde değil | Agent öneri → human-in-the-loop onay akışı soruyu hedefliyor |
| Qdrant `documents` collection'ı workstream filter ile aranıyor | Döküman bağlamı workstream'e izole — farklı ajanlar birbirinin dökümanlarından etkilenmiyor |
| `llm_client.py` servisi ayrı tutuldu | Router'dan bağımsız test edilebilir; model/prompt değişikliği tek yerden yapılıyor |

---

## Tuzaklar

### Deployment
- Docker image tag kuralı: `sprint<N>-<taskid>` — alembic-migrate ve api container **aynı tag** kullanmalı (`kubectl set image` ikisini birden güncelle)
- `ANTHROPIC_API_KEY`: `aakp-information` namespace'ine `aakp-k8s-agent-secret` olarak kopyalandı ve API deployment'ına inject edildi. Namespace silinirse/yeniden kurulursa yeniden yapılmalı
- Port-forward: API pod değişince `8000` port-forward ölür. Kontrol: `Get-NetTCPConnection -LocalPort 8000`

### Kod Bağımlılıkları
- `InterviewRoom.tsx` → `addAnswerFull` + `listAnswers` + `evaluateAnswer` (api.ts'deki yeni fonksiyonlar). `addAnswer` (eski) hâlâ var ama InterviewRoom artık onu kullanmıyor
- `agent_mgmt.py` → `qdrant_client.search_documents` + `qdrant_client.upsert_document_chunks` — Qdrant erişilemezse 500 değil, loglama yapıp devam ediyor (non-fatal)
- `suggest_followup` endpoint'i `selectinload(Question.answers)` kullanıyor — async SQLAlchemy'de lazy load çalışmaz, bunu kaldırma

### Veritabanı
- Migration 0007-0009 untracked ama K8s'de zaten çalıştı. Yeni ortamda `alembic upgrade head` sorunsuz çalışır
- `Answer.evaluation` nullable — değerlendirme başarısız olursa null kalır, frontend bunu handle ediyor

### Test
- `$env:API_BASE = "http://localhost:8000/api/v1"` ve port-forward aktif olmalı
- `test_08_sprint10.py` → PATCH task status fix içeriyor (`patch(f"/tasks/{task1['id']}", {"status": "in_progress"})`) — `createTask` status ignore ediyor
- Sprint 11 testleri yokken `py -m pytest tests/ -v` komutunda Sprint 11 endpoint'leri test edilmiyor

---

## Sonraki Adımlar (Öncelik Sırasıyla)

1. **Git commit**: Tüm uncommitted değişiklikleri commit et, branch'i main'e merge et veya yeni sprint branch'i aç
2. **`test_09_sprint11.py` yaz**: evaluate, agent metrics, document upload endpoint testleri (13/13 hedefi)
3. **QuestionManagement soru ekleme düzelt**: `addQuestion` yerine `POST /question-bank` çağır; `interviewId` bağımlılığını kaldır
4. **Lakehouse soru bankası doldur**: `assessment-kapsam-ciktilar-v2.docx`'tan sorular çıkarılıp `/question-bank/bulk` ile yüklenmeli — bu workstream hâlâ boş
5. **Agent self-learning geçmişi**: `GET /agents/{ws}/learning-history` endpoint'i — geçmiş değerlendirme özetlerini LLM bağlamına ekleme (S11'de RAG var, evaluation history yok)
6. **`frontend/` kökündeki eski codebase kararı**: Sil ya da aktif yap — şu haliyle karışıklık yaratıyor
7. **Fuseki ontoloji yükle**: `scripts/fuseki_upload_ontology.ps1` çalıştır; ontoloji v0.4 K8s'de henüz yüklü değil

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

**Aktif image'lar:** `aakp/api:sprint11`, `aakp/frontend:sprint11`

## Kritik Komutlar

```powershell
# Test
$env:API_BASE = "http://localhost:8000/api/v1"
py -m pytest tests/ -v

# Port-forward yenile
$pod = kubectl get pod -n aakp-information -l app=aakp-api -o jsonpath='{.items[0].metadata.name}'
kubectl port-forward -n aakp-information pod/$pod 8000:8000

# Deploy (her zaman aynı tag, her zaman ikisini birden)
kubectl set image deployment/aakp-api alembic-migrate=aakp/api:<tag> api=aakp/api:<tag> -n aakp-information
```
