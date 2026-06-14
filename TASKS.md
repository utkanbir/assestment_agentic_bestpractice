# AAKP — Development Backlog
**Versiyon:** 1.0 | **Tarih:** 2026-06-15 | **Metodoloji:** Vertical Slice

---

## Development Agent'ları

| Kod | Agent | Sorumluluk |
|---|---|---|
| DA | DevOps Agent | Kubernetes, Helm, CI/CD, infrastructure, gateway |
| BA | Backend Agent | FastAPI, PostgreSQL, REST API, MCP Server |
| KA | Knowledge Agent | Fuseki, OWL, SPARQL, SHACL, Reasoner |
| AA | Agent Dev Agent | LangGraph, assessment agent'ları, orchestrator |
| FA | Frontend Agent | React UI, WebSocket, dashboards |
| SA | Security Agent | Keycloak, OPA, Presidio, audit log |
| TA | Test Agent | E2E tests, validation, performance |

---

## Durum Tanımları

`[ ]` Backlog | `[~]` In Progress | `[x]` Done | `[!]` Blocked

---

## Sprint 0 — Foundation
> **Hedef:** Tüm servisler Kubernetes'te ayakta, healthcheck geçiyor, CI/CD çalışıyor.
> Hiçbir iş mantığı yok — sadece iskelet.

### DA — DevOps Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S0-DA-001 | Kubernetes cluster namespace'lerini oluştur (6 namespace) | Kritik | — |
| S0-DA-002 | RBAC policy'lerini her namespace için tanımla | Kritik | S0-DA-001 |
| S0-DA-003 | 5 Helm chart iskeletini oluştur (data/info/knowledge/agent/monitoring) | Kritik | S0-DA-001 |
| S0-DA-004 | CI/CD pipeline kur (Helm deploy otomatik) | Yüksek | S0-DA-003 |
| S0-DA-005 | Kong Gateway deploy et, temel routing kurallarını tanımla | Kritik | S0-DA-001 |
| S0-DA-006 | MinIO deploy et (standalone, bronze + archive bucket) | Kritik | S0-DA-001 |
| S0-DA-007 | PostgreSQL deploy et (aakp-information namespace) | Kritik | S0-DA-001 |
| S0-DA-008 | Apache Jena Fuseki deploy et (aakp-knowledge namespace) | Kritik | S0-DA-001 |
| S0-DA-009 | Redis deploy et (aakp-agent namespace) | Kritik | S0-DA-001 |
| S0-DA-010 | Kafka deploy et + temel topic'leri oluştur | Kritik | S0-DA-001 |
| S0-DA-011 | Qdrant deploy et (aakp-information namespace) | Yüksek | S0-DA-001 |
| S0-DA-012 | Tüm servisler için healthcheck endpoint'lerini doğrula | Kritik | S0-DA-006..011 |
| S0-DA-013 | PersistentVolume ve StorageClass tanımlarını yap | Kritik | S0-DA-001 |

---

## Sprint 1 — Tek Agent, End-to-End Interview
> **Hedef:** K8s Agent ile tam bir interview yapılabiliyor.
> Soru sor → yanıt al → evidence yakala → finding üret → KG'ye yaz → task raporu çık.
> Mimarinin tamamı doğrulanmış olacak.

### DA — DevOps Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S1-DA-001 | FastAPI container image oluştur, aakp-information'a deploy et | Kritik | S0 complete |
| S1-DA-002 | MCP Server container image oluştur, deploy et | Kritik | S0 complete |
| S1-DA-003 | LangGraph worker pool deploy et (aakp-agent, 2 replica) | Kritik | S0 complete |
| S1-DA-004 | Kong routing: /api → FastAPI, /mcp → MCP Server, /ws → WebSocket | Kritik | S0-DA-005 |

### BA — Backend Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S1-BA-001 | FastAPI proje yapısını kur (router, models, services, db) | Kritik | S1-DA-001 |
| S1-BA-002 | PostgreSQL schema: Assessment, Task, Interview, Question, Answer | Kritik | S1-BA-001 |
| S1-BA-003 | PostgreSQL schema: Evidence, Finding, Risk, Recommendation, Report | Kritik | S1-BA-002 |
| S1-BA-004 | Alembic migration pipeline kur | Yüksek | S1-BA-003 |
| S1-BA-005 | REST API: Assessment CRUD | Kritik | S1-BA-003 |
| S1-BA-006 | REST API: Task CRUD | Kritik | S1-BA-003 |
| S1-BA-007 | REST API: Interview CRUD | Kritik | S1-BA-003 |
| S1-BA-008 | REST API: Question / Answer CRUD | Kritik | S1-BA-003 |
| S1-BA-009 | REST API: Evidence CRUD | Kritik | S1-BA-003 |
| S1-BA-010 | REST API: Finding CRUD | Kritik | S1-BA-003 |
| S1-BA-011 | WebSocket endpoint: real-time interview fast path | Kritik | S1-BA-001 |
| S1-BA-012 | MCP Server: temel setup, tool manifest | Kritik | S1-DA-002 |
| S1-BA-013 | MCP Tool: create_finding(evidence_id, description, confidence) | Kritik | S1-BA-012 |
| S1-BA-014 | MCP Tool: add_evidence(source, content, type, interview_id) | Kritik | S1-BA-012 |
| S1-BA-015 | MCP Tool: suggest_next_question(context, task_id) | Kritik | S1-BA-012 |
| S1-BA-016 | MCP Resource: current_task_findings | Yüksek | S1-BA-012 |
| S1-BA-017 | MCP Resource: question_bank/kubernetes | Yüksek | S1-BA-012 |
| S1-BA-018 | Kafka producer: interview.answer.submitted event | Yüksek | S0-DA-010 |
| S1-BA-019 | Kafka producer: assessment.finding.created event | Yüksek | S0-DA-010 |

### KA — Knowledge Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S1-KA-001 | OWL ontoloji v0.2'yi Fuseki'ye deploy et (4 .owl dosyası) | Kritik | S0-DA-008 |
| S1-KA-002 | K8s Agent için SPARQL sorgu şablonları yaz | Yüksek | S1-KA-001 |
| S1-KA-003 | SHACL shape: Finding (supportedByEvidence zorunlu) | Kritik | S1-KA-001 |
| S1-KA-004 | SPARQL: Finding'leri task bazında getir | Yüksek | S1-KA-001 |
| S1-KA-005 | Fuseki SPARQL endpoint'ini FastAPI'a bağla | Kritik | S1-KA-001 |

### AA — Agent Dev Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S1-AA-001 | LangGraph proje yapısını kur | Kritik | S1-DA-003 |
| S1-AA-002 | Agent base class: scope loader, tool initializer, checkpoint | Kritik | S1-AA-001 |
| S1-AA-003 | K8s Agent — PRE_INTERVIEW: context loader node | Kritik | S1-AA-002 |
| S1-AA-004 | K8s Agent — INTERVIEW_LOOP: answer processor node | Kritik | S1-AA-003 |
| S1-AA-005 | K8s Agent — INTERVIEW_LOOP: question advisor node (WebSocket fast path) | Kritik | S1-AA-004 |
| S1-AA-006 | K8s Agent — INTERVIEW_LOOP: evidence capture node | Kritik | S1-AA-004 |
| S1-AA-007 | K8s Agent — INTERVIEW_LOOP: finding detector node | Kritik | S1-AA-006 |
| S1-AA-008 | K8s Agent — POST_INTERVIEW: task report generator | Kritik | S1-AA-007 |
| S1-AA-009 | K8s Agent — POST_INTERVIEW: Knowledge Graph writer node | Kritik | S1-AA-008 |
| S1-AA-010 | LangGraph checkpoint setup (PostgreSQL store) | Kritik | S1-AA-001 |
| S1-AA-011 | Human-in-the-loop interrupt: finding approval | Yüksek | S1-AA-007 |
| S1-AA-012 | Agent Registry: K8s Agent kaydı (Fuseki'ye SPARQL INSERT) | Yüksek | S1-KA-001 |
| S1-AA-013 | K8s workstream question bank oluştur | Kritik | S1-AA-003 |
| S1-AA-014 | Kafka consumer: interview.answer.submitted → slow path tetikle | Yüksek | S0-DA-010 |

### FA — Frontend Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S1-FA-001 | React proje setup (Vite, TypeScript, Tailwind) | Kritik | — |
| S1-FA-002 | 3-panel interview layout (sol: tasks, orta: Q&A, sağ: agent) | Kritik | S1-FA-001 |
| S1-FA-003 | Soru/Cevap input formu + gönder | Kritik | S1-FA-001 |
| S1-FA-004 | WebSocket bağlantısı: agent suggestion real-time alım | Kritik | S1-BA-011 |
| S1-FA-005 | Agent suggestion panel: sonraki soru önerisi göster | Yüksek | S1-FA-004 |
| S1-FA-006 | Alt panel: findings listesi (basic) | Yüksek | S1-FA-001 |
| S1-FA-007 | Nginx deploy + Kong routing /ui/* | Yüksek | S1-DA-004 |

---

## Sprint 2 — Knowledge Graph Tam Entegrasyonu
> **Hedef:** Ontoloji tam deploy, SHACL validation aktif, reasoner çalışıyor.
> Finding → Risk zinciri KG üzerinden otomatik çıkarım yapıyor.

### KA — Knowledge Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S2-KA-001 | 4 OWL dosyasını formal OWL syntax'ına çevir (v0.3) | Kritik | S1 complete |
| S2-KA-002 | SHACL shapes: tüm entity'ler için validation (Risk, Evidence, Recommendation) | Kritik | S2-KA-001 |
| S2-KA-003 | Apache Jena Reasoner konfigürasyonu (Rule 1-7) | Kritik | S2-KA-001 |
| S2-KA-004 | Inference Rule 5: confidence propagation | Kritik | S2-KA-003 |
| S2-KA-005 | Inference Rule 7: unsupported finding → isInvalid | Kritik | S2-KA-003 |
| S2-KA-006 | System subclass taxonomy OWL'a ekle (DataWarehouse, DataIngestion vb.) | Yüksek | S2-KA-001 |
| S2-KA-007 | Ontological Semantic Layer: R2RML mappings (PostgreSQL → RDF) | Yüksek | S2-KA-001 |
| S2-KA-008 | SPARQL: Finding → Risk zinciri sorgusu | Kritik | S2-KA-003 |
| S2-KA-009 | SPARQL: Capability → Gap → Risk sorgusu | Yüksek | S2-KA-003 |
| S2-KA-010 | Fuseki versiyonlama stratejisi kur (named graph per assessment) | Yüksek | S2-KA-001 |

### BA — Backend Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S2-BA-001 | Qdrant koleksiyon yapısını kur (findings, evidence, transcripts) | Kritik | S1 complete |
| S2-BA-002 | Embedding pipeline: yeni finding oluşunca otomatik embed et | Kritik | S2-BA-001 |
| S2-BA-003 | Embedding pipeline: evidence metni embed et | Yüksek | S2-BA-001 |
| S2-BA-004 | MCP Tool: get_similar_findings(text) — Qdrant semantic search | Yüksek | S2-BA-001 |
| S2-BA-005 | MCP Resource: similar_findings (Qdrant'tan) | Yüksek | S2-BA-004 |
| S2-BA-006 | REST API: Risk CRUD | Kritik | S1 complete |
| S2-BA-007 | REST API: Recommendation CRUD | Kritik | S1 complete |
| S2-BA-008 | REST API: Report CRUD | Kritik | S1 complete |
| S2-BA-009 | KG writer service: PostgreSQL entity → Fuseki RDF triple | Kritik | S2-KA-007 |

### AA — Agent Dev Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S2-AA-001 | Finding → Risk reasoning node (SPARQL üzerinden) | Kritik | S2-KA-008 |
| S2-AA-002 | Confidence propagation implementasyonu (Rule 5) | Kritik | S2-KA-004 |
| S2-AA-003 | LangGraph edge: evidence yoksa finding node'a geçme | Kritik | S2-KA-005 |
| S2-AA-004 | KG writer node: finding/risk/recommendation → Fuseki | Kritik | S2-BA-009 |
| S2-AA-005 | Semantic search entegrasyonu: benzer geçmiş bulgular | Yüksek | S2-BA-004 |

---

## Sprint 3 — Tüm 8 Agent + Tam MCP Tool Seti
> **Hedef:** 8 workstream'in tamamı agent'larla yönetilebiliyor.
> Her agent kendi question bank'i ve MCP tool'larıyla çalışıyor.

### AA — Agent Dev Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S3-AA-001 | Cloud Strategy Agent implementasyonu | Kritik | S2 complete |
| S3-AA-002 | Ingestion Agent implementasyonu | Kritik | S2 complete |
| S3-AA-003 | Teradata DR Agent implementasyonu | Kritik | S2 complete |
| S3-AA-004 | Lakehouse Agent implementasyonu | Kritik | S2 complete |
| S3-AA-005 | Governance Agent implementasyonu | Kritik | S2 complete |
| S3-AA-006 | Data Product Agent implementasyonu | Kritik | S2 complete |
| S3-AA-007 | CDP Agent implementasyonu | Kritik | S2 complete |
| S3-AA-008 | Agent Registry: 7 yeni agent kaydı (Fuseki SPARQL INSERT) | Kritik | S3-AA-001..007 |
| S3-AA-009 | MCP Tool: flag_risk(finding_id, severity) | Kritik | S2 complete |
| S3-AA-010 | MCP Tool: generate_recommendation(gap_id, risk_id, horizon) | Kritik | S2 complete |
| S3-AA-011 | MCP Tool: compare_to_benchmark(capability, score) | Yüksek | S2 complete |
| S3-AA-012 | MCP Tool: detect_contradiction(answer_id, context) | Yüksek | S2 complete |
| S3-AA-013 | MCP Tool: update_task_status(task_id, status) | Yüksek | S2 complete |
| S3-AA-014 | Assessment Memory Agent implementasyonu (Qdrant semantic search) | Yüksek | S2-BA-004 |

### BA — Backend Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S3-BA-001 | OpenMetadata deploy ve konfigürasyonu | Yüksek | S2 complete |
| S3-BA-002 | OpenMetadata custom entity: Finding, Risk, Recommendation | Yüksek | S3-BA-001 |
| S3-BA-003 | OpenMetadata lineage: Interview → Evidence → Finding → Risk zinciri | Yüksek | S3-BA-002 |
| S3-BA-004 | Question bank API: workstream bazlı soru yönetimi | Kritik | S2 complete |
| S3-BA-005 | 7 yeni workstream question bank'ini yükle | Kritik | S3-BA-004 |
| S3-BA-006 | Kafka topic: assessment.task.status.changed | Yüksek | S2 complete |

### KA — Knowledge Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S3-KA-001 | Lakehouse workstream soruları oluştur (Tolga ile birlikte) | Kritik | S2 complete |
| S3-KA-002 | Migros-specific ABox instance'ları KG'ye ekle | Yüksek | S2-KA-001 |
| S3-KA-003 | System individuals: Teradata, NiFi, Kubernetes, DataStage vb. | Yüksek | S3-KA-002 |

### FA — Frontend Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S3-FA-001 | Assessment overview: 8 workstream task listesi | Kritik | S2 complete |
| S3-FA-002 | Agent selection UI: hangi agent aktif | Yüksek | S3-FA-001 |
| S3-FA-003 | Çoklu interview session yönetimi (paralel consultant desteği) | Yüksek | S3-FA-001 |

---

## Sprint 4 — Orchestrator + Cross-Task Analiz
> **Hedef:** Orchestrator 8 agent'ı koordine ediyor.
> Cross-task bağımlılıklar tespit ediliyor, executive summary ve consolidated roadmap üretiliyor.

### AA — Agent Dev Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S4-AA-001 | Orchestrator Agent LangGraph graph'ı (Supervisor pattern) | Kritik | S3 complete |
| S4-AA-002 | Task monitor node: hangi task'lar complete? | Kritik | S4-AA-001 |
| S4-AA-003 | Cross-task dependency checker (SPARQL + KG) | Kritik | S4-AA-001 |
| S4-AA-004 | Conflict detector: çelişen findings → human review | Kritik | S4-AA-001 |
| S4-AA-005 | Risk consolidation node: 8 workstream → unified risk list | Kritik | S4-AA-001 |
| S4-AA-006 | Executive summary generator | Kritik | S4-AA-005 |
| S4-AA-007 | Consolidated roadmap generator (8 roadmap → öncelikli 1 plan) | Kritik | S4-AA-005 |
| S4-AA-008 | Kafka consumer: assessment.interview.completed → orchestrator tetikle | Yüksek | S4-AA-001 |

### KA — Knowledge Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S4-KA-001 | Inference Rule 6: cross-task risk propagation | Kritik | S4-AA-003 |
| S4-KA-002 | SPARQL: cross-task dependency sorgusu (Task.dependsOnTask) | Kritik | S4-AA-003 |
| S4-KA-003 | SPARQL: risk heatmap veri sorgusu (severity × capability) | Yüksek | S4-AA-005 |
| S4-KA-004 | SPARQL: consolidated roadmap verisi (horizon × priority) | Yüksek | S4-AA-007 |

### FA — Frontend Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S4-FA-001 | Risk heatmap bileşeni (severity × capability matrisi) | Kritik | S4-AA-005 |
| S4-FA-002 | Executive summary sayfası | Yüksek | S4-AA-006 |
| S4-FA-003 | Consolidated roadmap görünümü (horizon bazlı) | Yüksek | S4-AA-007 |
| S4-FA-004 | Cross-task dependency panel | Yüksek | S4-AA-003 |

---

## Sprint 5 — Guardrails Tam İmplementasyon
> **Hedef:** 5 guardrail kategorisi tamamen aktif. Defense in depth çalışıyor.
> 0 tolerance metriği canlı. Ontology Co-Pilot ve Research Agent aktif.

### SA — Security Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S5-SA-001 | Keycloak deploy + realm ve client konfigürasyonu | Kritik | S4 complete |
| S5-SA-002 | Kong + Keycloak JWT validation entegrasyonu | Kritik | S5-SA-001 |
| S5-SA-003 | OPA policy engine deploy | Kritik | S4 complete |
| S5-SA-004 | OPA policy: retrieval guardrail (agent scope kontrolü) | Kritik | S5-SA-003 |
| S5-SA-005 | OPA policy: governance guardrail (ontoloji yazma kısıtı) | Kritik | S5-SA-003 |
| S5-SA-006 | Kong + OPA entegrasyonu (/mcp/* route'ları için) | Kritik | S5-SA-003 |
| S5-SA-007 | Presidio pipeline: doküman yükleme → PII tarama | Kritik | S4 complete |
| S5-SA-008 | Presidio pipeline: yanıt girişi → PII tarama | Kritik | S5-SA-007 |
| S5-SA-009 | Immutable audit log servisi | Kritik | S5-SA-001 |
| S5-SA-010 | Audit log: tüm KG değişiklikleri logla | Kritik | S5-SA-009 |

### BA — Backend Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S5-BA-001 | Input guardrail middleware: FastAPI'a Presidio entegrasyonu | Kritik | S5-SA-007 |
| S5-BA-002 | Output validator: rapor üretiminden önce evidence chain kontrolü | Kritik | S4 complete |
| S5-BA-003 | Output validator: PII filtreleme (rapordan) | Kritik | S5-SA-007 |
| S5-BA-004 | MCP Tool: create_finding() → evidence_id zorunlu (input guardrail) | Kritik | S4 complete |
| S5-BA-005 | Human approval workflow API: finding/risk/recommendation onayı | Kritik | S4 complete |

### AA — Agent Dev Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S5-AA-001 | LangGraph edge condition: evidence yoksa finding node'a geçme | Kritik | S5-BA-004 |
| S5-AA-002 | LangGraph edge condition: finding yoksa risk node'a geçme | Kritik | S5-AA-001 |
| S5-AA-003 | LangGraph edge condition: validation geçmezse report node'a geçme | Kritik | S5-AA-002 |
| S5-AA-004 | Ontology Co-Pilot Agent implementasyonu | Yüksek | S4 complete |
| S5-AA-005 | Ontology Co-Pilot: proposal → human review → Fuseki publish workflow | Yüksek | S5-AA-004 |
| S5-AA-006 | Domain Research Agent implementasyonu (web search + candidate KG) | Yüksek | S4 complete |
| S5-AA-007 | Research Agent: candidate knowledge human review workflow | Yüksek | S5-AA-006 |

### KA — Knowledge Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S5-KA-001 | SHACL: tüm entity'ler için tam validation shapes | Kritik | S4 complete |
| S5-KA-002 | SHACL validation'ı KG write pipeline'ına entegre et | Kritik | S5-KA-001 |
| S5-KA-003 | Candidate knowledge named graph (human approval öncesi staging) | Yüksek | S5-AA-006 |

---

## Sprint 6 — Monitoring + Observability
> **Hedef:** Tüm Grafana dashboard'ları canlı. LangFuse agent trace'leri görünüyor.
> 0 tolerance metriği alert'i çalışıyor.

### DA — DevOps Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S6-DA-001 | Prometheus deploy + tüm servislerden scrape config | Kritik | S5 complete |
| S6-DA-002 | Grafana deploy + datasource konfigürasyonu | Kritik | S6-DA-001 |
| S6-DA-003 | Loki deploy + log aggregation | Yüksek | S5 complete |
| S6-DA-004 | Grafana Tempo deploy + OpenTelemetry collector | Yüksek | S5 complete |
| S6-DA-005 | LangFuse deploy + PostgreSQL konfigürasyonu | Kritik | S5 complete |

### BA — Backend Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S6-BA-001 | Custom Prometheus metrics: /metrics endpoint | Kritik | S6-DA-001 |
| S6-BA-002 | Metrik: evidence_coverage_score | Kritik | S6-BA-001 |
| S6-BA-003 | Metrik: recommendation_without_evidence (0 tolerance) | Kritik | S6-BA-001 |
| S6-BA-004 | Metrik: guardrail_violations_total (kategori bazında) | Kritik | S6-BA-001 |
| S6-BA-005 | Metrik: agent_confidence_avg | Yüksek | S6-BA-001 |
| S6-BA-006 | OpenTelemetry SDK: FastAPI distributed tracing | Yüksek | S6-DA-004 |
| S6-BA-007 | Structured logging: tüm servisler JSON log formatına geçsin | Yüksek | S6-DA-003 |

### AA — Agent Dev Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S6-AA-001 | LangFuse + LangGraph entegrasyonu (her LLM çağrısı trace'lenir) | Kritik | S6-DA-005 |
| S6-AA-002 | Token ve maliyet tracking her agent için | Kritik | S6-AA-001 |
| S6-AA-003 | Agent confidence score LangFuse'a gönder | Yüksek | S6-AA-001 |

### FA — Frontend Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S6-FA-001 | Grafana: Agent Performance Dashboard | Kritik | S6-DA-002 |
| S6-FA-002 | Grafana: Cost / Credit Dashboard | Kritik | S6-DA-002 |
| S6-FA-003 | Grafana: Task Activity Timeline | Yüksek | S6-DA-002 |
| S6-FA-004 | Grafana: Guardrail Violations Panel | Kritik | S6-DA-002 |
| S6-FA-005 | Grafana: Evidence Coverage Panel | Kritik | S6-DA-002 |
| S6-FA-006 | Grafana: LLM Call Logs dashboard | Yüksek | S6-DA-002 |
| S6-FA-007 | Grafana Alerting: 0 tolerance kural tanımı | Kritik | S6-BA-003 |
| S6-FA-008 | Grafana Alerting: evidence coverage < %80 uyarısı | Yüksek | S6-BA-002 |

---

## Sprint 7 — Frontend UX + Polish + E2E Test
> **Hedef:** Tam interview deneyimi hazır. Sistem production-ready kalitede test edilmiş.

### FA — Frontend Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S7-FA-001 | Interview UI: alt panel — findings + evidence tam görünüm | Kritik | S6 complete |
| S7-FA-002 | Interview UI: sağ panel — agent suggestions tam (risk sinyali, eksik evidence uyarısı) | Kritik | S6 complete |
| S7-FA-003 | Human approval UI: finding/risk onay akışı | Kritik | S5-BA-005 |
| S7-FA-004 | Maturity dashboard: capability × dimension ısı haritası | Yüksek | S6 complete |
| S7-FA-005 | Report export: PDF üretimi | Yüksek | S6 complete |
| S7-FA-006 | Assessment overview: genel durum dashboard'u | Yüksek | S6 complete |
| S7-FA-007 | OpenMetadata catalog UI embed veya link | Orta | S3-BA-001 |
| S7-FA-008 | Responsive tasarım ve UX polish | Orta | S7-FA-001..006 |

### TA — Test Agent

| ID | Task | Öncelik | Bağımlılık |
|---|---|---|---|
| S7-TA-001 | E2E test: K8s Agent tam interview akışı | Kritik | S6 complete |
| S7-TA-002 | E2E test: finding → KG → report zinciri | Kritik | S6 complete |
| S7-TA-003 | Guardrail test: evidence'sız finding → blok | Kritik | S5 complete |
| S7-TA-004 | Guardrail test: PII içeren yanıt → filtreleme | Kritik | S5 complete |
| S7-TA-005 | Guardrail test: 0 tolerance metriği doğrulama | Kritik | S6-BA-003 |
| S7-TA-006 | Cross-task test: CDP ↔ Ingestion bağımlılık tespiti | Yüksek | S4 complete |
| S7-TA-007 | Orchestrator test: executive summary doğruluğu | Yüksek | S4 complete |
| S7-TA-008 | Performance test: 8 paralel interview session | Yüksek | S6 complete |
| S7-TA-009 | SHACL validation test: ontoloji constraint'leri | Yüksek | S5 complete |
| S7-TA-010 | Agent Registry test: yeni agent dinamik keşif | Orta | S3 complete |

---

## Özet

| Sprint | Hedef | Toplam Task | Kritik Task |
|---|---|---|---|
| Sprint 0 | Foundation | 13 | 12 |
| Sprint 1 | K8s Agent E2E | 37 | 28 |
| Sprint 2 | KG Entegrasyonu | 18 | 12 |
| Sprint 3 | 8 Agent + MCP | 20 | 13 |
| Sprint 4 | Orchestrator | 15 | 11 |
| Sprint 5 | Guardrails | 22 | 17 |
| Sprint 6 | Monitoring | 21 | 14 |
| Sprint 7 | UX + Test | 18 | 11 |
| **TOPLAM** | | **164** | **118** |

---

## Development Agent Yük Dağılımı

| Agent | Sprint 0 | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sprint 5 | Sprint 6 | Sprint 7 | Toplam |
|---|---|---|---|---|---|---|---|---|---|
| DA | 13 | 4 | — | — | — | — | 5 | — | 22 |
| BA | — | 19 | 9 | 3 | — | 5 | 7 | — | 43 |
| KA | — | 5 | 10 | 3 | 4 | 3 | — | — | 25 |
| AA | — | 14 | 5 | 14 | 8 | 7 | 3 | — | 51 |
| FA | — | 7 | — | 3 | 4 | — | 8 | 8 | 30 |
| SA | — | — | — | — | — | 10 | — | — | 10 |
| TA | — | — | — | — | — | — | — | 10 | 10 |

---

*Her sprint başında task'lar `[~]` In Progress, tamamlanınca `[x]` Done olarak işaretlenir.*
*Blocked task'lar `[!]` ile işaretlenir ve bağımlılık çözülene kadar bekler.*
