# Agentic Assessment Knowledge Platform (AAKP)
## Mimari Karar Dokümanı
**Versiyon:** 0.2 | **Durum:** Devam Ediyor | **Tarih:** 2026-06-14

---

## 1. Proje Vizyonu

### Amaç
Danışmanlık ekiplerinin müşteri assessment'larını AI agent'lar, knowledge management, ontoloji-güdümlü akıl yürütme ve governed enterprise knowledge kullanarak yapılandırılmış biçimde yürütmesini sağlayan enterprise-grade bir platform.

### Temel Prensip
Geleneksel veri yönetiminden bilgi yönetimine geçiş:
```
Eski:  Data Sources → Data Warehouse → Reports
Yeni:  Data Layer → Information Layer → Knowledge Layer → Agent Layer
```

Agent'lar ham veri üzerinde değil, ontoloji → knowledge graph → semantic layer → data products zinciri üzerinden akıl yürütür.

### Kapsam
- İlk engagement: Migros enterprise data platform assessment
- 8 workstream, 8 uzman danışman, her birine bir AI assessment agent
- İnsan her zaman loop içinde — agent augments, human decides
- Uzun vadede: her danışmanlık engagement'ına uygulanabilir reusable blueprint

### Mimari Hedefler
- Open Source
- Container Native
- Kubernetes Ready
- OWL/RDF Based
- Vendor Independent
- Agent Ready
- Knowledge-Centric
- **Best Practice Showcase** — MVP değil, tam kapsamlı referans mimari

---

## 2. Assessment Kapsamı: 8 Workstream → 8 Agent

| Agent | Workstream | Süre |
|---|---|---|
| Kubernetes Agent | Analitik Platform: Business Continuity & K8s Resilience | 2 saat |
| Cloud Strategy Agent | Cloud Dönüşüm Strateji & Yol Haritası (GCP) | 2 saat |
| Ingestion Agent | Data Ingestion & ETL Katmanı (NiFi / DataStage / Airflow) | 2 saat |
| Teradata DR Agent | Teradata EDW: DR Senaryosu & Cloud Opsiyon | 2 saat |
| Lakehouse Agent | Lakehouse Mimarisi Yaklaşımı | 2 saat |
| Governance Agent | Data Governance Yaklaşımı | 2 saat |
| Data Product Agent | Data Product Yaklaşımı | 2 saat |
| CDP Agent | CDP & Customer 360 Yaklaşımı | 2 saat |

> **Not:** Lakehouse workstream soruları henüz oluşturulmadı — platform geliştirme sürecinde birlikte oluşturulacak.

---

## 3. Mimari: 4 Katman

### Genel Görünüm

```
┌─────────────────────────────────────────────────┐
│                  AGENT LAYER                    │
│   Orchestration │ Memory │ Guardrails │ Tools   │
├─────────────────────────────────────────────────┤
│               KNOWLEDGE LAYER                   │
│  Semantic Mapping │ Ontology │ KG │ Reasoning   │
├─────────────────────────────────────────────────┤
│              INFORMATION LAYER                  │
│  Data Products │ Contracts │ Catalog │ Vector   │
├─────────────────────────────────────────────────┤
│                 DATA LAYER                      │
│   Lakehouse │ Streaming │ Operational │ IoT     │
└─────────────────────────────────────────────────┘
```

---

## 4. Katman Detayları

### 4.1 Data Layer

> **Durum:** Tasarım tamamlandı ✓

#### Data Layer'ın AAKP'deki Rolü

Geleneksel platformdan farklı olarak iki tip veri saklar:

```
Tip 1 — Assessment Artifact'ları (platformun topladığı):
  → Interview transkriptleri, ses/video kayıtları
  → Yüklenen dokümanlar (mimari diyagramlar, config dosyaları, policy'ler)
  → Müşterinin export ettiği metrikler ve loglar
  → Geçmiş engagement kayıtları

Tip 2 — Müşteri Ortamından Gelen Materyaller:
  → Canlı DB bağlantısı YOK
  → Müşteri export eder, consultant yükler, platform alır
  → NiFi logları, Kubernetes metrikleri, Teradata sorgu logları
```

#### Teknoloji Stack

| Bileşen | Teknoloji | Rol |
|---|---|---|
| Object Storage | MinIO | S3-compatible, tüm ham dosyalar |
| Table Format | Apache Iceberg | Schema evolution, time travel |
| Table Catalog | Iceberg REST Catalog | Iceberg metadata yönetimi |
| Query Engine | Trino | Cross-source federation |
| Event Bus | Kafka | Async agent pipeline (slow path) |
| Real-time | WebSocket (FastAPI) | Interview fast path |

#### Karar: Bronze / Silver Sınırı

**Karar:** Data Layer = sadece Bronze. Silver Information Layer'da başlar.

**Gerekçe:** Silver'a geçmek — transcript'i Q&A yapısına çevirmek — domain knowledge gerektirir. Bu Information Layer'ın sorumluluğu.

```
Data Layer:        Bronze (raw files — transcript, PDF, CSV, log, config)
Information Layer: Silver (structured assessment objects) + Gold (data products)
```

#### Karar: Apache Iceberg

**Karar:** Evet, hacim küçük olsa da Iceberg kullanılır.

**Gerekçe:**
- Schema evolution — ontoloji değiştikçe tablo şemaları da değişir
- Time travel — geçmiş assessment snapshot'larına bakma
- Trino entegrasyonu — cross-source federation için gerekli
- Best practice blueprint — reusable, büyüyebilir mimari

#### Karar: Trino'nun Rolü

**Karar:** Cross-source federation — sadece Iceberg değil, tüm kaynakları birleştirir.

```
Trino federasyonu:
  Iceberg (assessment records)
  + PostgreSQL (structured objects)
  + OpenMetadata (catalog metadata)
  → "Tüm finding'leri + ilgili evidence dosyalarını birlikte getir"
```

Orchestrator Agent cross-task analiz için Trino'yu kullanır.

#### Karar: İki Hızlı Akış (Fast Path + Slow Path)

**Karar:** Kafka event bus olarak kalır — data streaming değil. Gerçek zamanlı interview için WebSocket eklendi.

**Gerekçe:** Interview sırasında müşteri yanıtı girildiğinde agent anında karar vermeli:
- Sonraki soruyu atla
- Yeni follow-up soru üret
- Finding sinyali ver

Bu kararın saniyeler içinde gelmesi gerekiyor. Kafka + LLM overhead birleşirse gecikme artar, consultant bekler.

```
Müşteri yanıtı girildi
        │
        ├── FAST PATH — WebSocket (saniyeler)
        │   Agent analiz eder:
        │   → Sonraki soru hala gerekli mi?
        │   → Yeni follow-up soru üret
        │   → Finding sinyali
        │   → UI'da suggestion paneli anında güncellenir
        │
        └── SLOW PATH — Kafka (dakikalar)
            answer.submitted event → Evidence oluşturulur
            → Finding analizi → Risk değerlendirmesi
            → UI'da findings paneli güncellenir
```

#### MinIO Bucket Yapısı

```
MinIO
├── bronze/
│   ├── transcripts/     ← ham interview metinleri
│   ├── documents/       ← PDF, diyagram, config, policy
│   ├── metrics/         ← export edilmiş CSV/JSON/log
│   └── recordings/      ← ses/video (opsiyonel)
└── archive/
    └── historical/      ← geçmiş engagement'lar
```

#### Kafka Topic Listesi

```
interview.answer.submitted       ← slow path tetikler
assessment.evidence.created      ← finding analizi tetikler
assessment.finding.created       ← risk değerlendirmesi tetikler
assessment.interview.completed   ← report generation tetikler
assessment.task.status.changed   ← orchestrator bilgilenir
```

---

### 4.2 Information Layer

> **Durum:** Tasarım tamamlandı ✓

#### Bileşenler

```
Information Layer
├── Business Semantic Layer     ← KPI, maturity rules, dashboard/read model logic
├── Domain Information Objects  ← Silver: workflow-aware structured domain entities
├── Published Data Products     ← Gold: contract, lineage, discoverable consumption ports
├── Data Contracts              ← OpenMetadata quality guarantees
├── Metadata & Lineage          ← Interview → Evidence → Finding → Risk → Recommendation
├── Vector Store                ← Qdrant embeddings (derived index ports)
└── API Layer                   ← REST + MCP + Kafka
```

| Bileşen | Açıklama | Teknoloji |
|---|---|---|
| Business Semantic Layer | Assessment metrikleri, KPI'lar, maturity skorları — dashboard ve raporlar için | FastAPI views |
| Domain Information Objects | Assessment domain structured entities (Silver) — workflow, validation, human-in-the-loop | PostgreSQL |
| Published Data Products | Contract'lı, lineage'lı, discoverable Gold ürünler — agent/UI tüketimi | PostgreSQL + FastAPI + MCP |
| Data Contracts | Her published product'ın kalite garantisi — guardrail'e doğrudan bağlı | OpenMetadata |
| Metadata & Lineage | Interview → Evidence → Finding → Risk → Recommendation izlenebilirliği | OpenMetadata |
| Data Catalog & Marketplace | Cross-engagement knowledge reuse, assessment artifact discovery | OpenMetadata |
| Vector Store | Assessment content embedding'leri — semantic search, RAG için | Qdrant |
| API Layer | Üçlü arayüz (bkz. aşağıda) | FastAPI + MCP + Kafka |

#### ADR: Domain Information Objects vs Published Data Products

**Durum:** Onaylandı ✓ | **Tarih:** 2026-06-18

**Karar:** Information Layer içindeki assessment domain varlıkları ikiye ayrılır:

1. **Domain Information Objects** — sistemin structured, validated, workflow-aware domain nesneleri (Medallion: **Silver**)
2. **Published Data Products** — contract'lı, lineage'lı, discoverable ve agent/UI/external consumer tarafından tüketilebilir **Gold** ürünleri

**Gerekçe:**

- Her tabloyu veya entity'yi data product olarak adlandırmak data product kavramını sulandırır.
- Data product kavramı **ownership, contract, SLA, lineage, discoverability** ve **reusable consumption port** gerektirir.
- Assessment domainindeki Answer, Evidence, Finding gibi nesneler önce **domain object**'tir.
- Bu nesnelerden türetilen Finding Library, Risk Register, Assessment Results View gibi publish edilmiş read model'lar gerçek **data product**'tır.
- Bu ayrım Data Mesh prensiplerine daha uygundur.
- Agent erişimi daha kontrollü olur: agent raw tablo yerine **published product port**undan okur.
- OpenMetadata catalog daha anlamlı kalır.
- Knowledge Layer mapping öncelikle domain object instance'larına odaklanır (1:1 RDF); published product'lar catalog/compose seviyesinde temsil edilir.

**Domain Information Objects (Silver):**

| Nesne | Açıklama |
|---|---|
| Assessment | Engagement container — **data product değil** |
| Task | Workstream scope container |
| Interview | Interview oturumu |
| **Question (canonical)** | Global soru bankası — `WorkstreamQuestion`, assessment'tan bağımsız |
| Question (session copy) | Interview oturum kopyası — cevap/evidence zinciri; framework'te ayrı DIO değil |
| Answer | Müşteri cevabı |
| Evidence | Kanıt kaydı (bronze pointer + metadata) |
| Finding | Yapılandırılmış bulgu |
| Risk | Finding'den türeyen risk |
| Recommendation | Finding'den türeyen öneri |
| Consultant Comment | Danışman yorumu (answer üzerinde) |
| Maturity Score | Workstream olgunluk değerlendirmesi |

**Published Data Products (Gold):**

| Ürün | Classification | Açıklama |
|---|---|---|
| Question Bank | `published_data_product` | Global bank aggregate — canonical `WorkstreamQuestion` DIO'lardan publish; agent primary port |
| Finding Library | `published_data_product` | Keşfedilebilir bulgu koleksiyonu |
| Risk Register | `published_data_product` | Risk koleksiyonu |
| Recommendation Catalog | `published_data_product` | Öneri koleksiyonu |
| Maturity Scorecard | `published_data_product` | Tüm workstream olgunluk aggregate |
| Assessment Results View | `composite_published_data_product` | Chat/agent birincil composite read model |
| Executive Summary | `composite_published_data_product` | KPI + narrative özet |
| Assessment Report | `composite_published_data_product` | Report Studio `content_json` |
| Evidence Catalog | `published_data_product` | Keşfedilebilir evidence metadata |

**Önemli sınırlar:**

- **Assessment** bir data product değildir; engagement container / domain root olarak kalır.
- **Interview Q&A** default olarak published product değildir; session copy + `Answer`, `Evaluation` workflow içi Silver'dır. Canonical **Question** soru bankasındadır (`WorkstreamQuestion`). Dış tüketim + MCP resource + contract tanımlanırsa ayrı export product'a terfi edebilir.
- **MCP Resources/Tools** birincil consumption port olarak **Published Data Products** için kullanılır.
- **Domain Information Objects** erişimi internal service/API seviyesinde kalır; agent'lar normalde doğrudan bu seviyeye inmez (workflow write path hariç).
- Product servisleri compose sırasında internal olarak PG okuyabilir; yasak olan agent-facing raw table erişimidir.

**Product maturity tiers (hedef):**

| Seviye | Gereksinim |
|---|---|
| L0 — Listed | Catalog'da isim + owner |
| L1 — Contracted | Schema + freshness/completeness expectation |
| L2 — Governed | SLA, quality checks, approval workflow |

**Semantic Layer ilişkisi:**

- Business Semantic Layer → Published Data Products ve dashboard/read model üretimi (Information Layer)
- Ontological Semantic Layer → Knowledge Layer tabanı (OWL/RDF mapping, reasoner)
- Domain Information Objects → Semantic Mapping ile 1:1 KG instance (`kg_writer` / R2RML)
- Published Data Products → OpenMetadata catalog + REST/MCP port; KG'de opsiyonel aggregate metadata

**Kaynak:** `knowledge/architecture/SEMANTIC_INTELLIGENCE_FRAMEWORK.md`, `knowledge/architecture/data_products_catalog.yaml`, `knowledge/architecture/DATA_PRODUCTS_SEMANTIC_LAYER_DISCUSSION.md`

#### Karar: Vector Store Yerleşimi

**Karar:** Vector store Information Layer'da — Agent Layer'da değil.

**Gerekçe:** İki farklı vector kullanımı ayrıştırıldı:

| Kullanım | Katman | Teknoloji | Açıklama |
|---|---|---|---|
| Content Embeddings | Information Layer | Qdrant | Finding, transcript, doküman embedding'leri. Governed, persistent, lineage'a tabi. Birden fazla agent tüketiyor. |
| Agent Working Memory | Agent Layer | LangGraph / Redis | Session-scoped, ephemeral. Tek agent'a ait. Governance gerekmez. |

**Prensip:** Agent Layer hiçbir zaman kendi başına veri üretip saklamaz. Veri üretimi Information Layer'ın sorumluluğu.

#### Karar: API Tasarımı — Üçlü Mimari

**Karar:** REST + MCP + Event Stream

**Gerekçe:** Her consumer'ın ihtiyacı farklı.

```
Information Layer API Layer
├── REST API (FastAPI)
│   → React UI, Knowledge Layer ingestion, external sistemler
│   → Standard CRUD, OpenAPI spec
│
├── MCP Server (Model Context Protocol)
│   → Tüm assessment agent'ları
│   → Semantic interface: Resources + Tools + Prompts
│   → Agent ne yapabileceğini anlıyor, raw endpoint parse etmiyor
│   → LangGraph + Claude native desteği
│
└── Event Stream (Kafka)
    → Gerçek zamanlı interview desteği
    → "Yeni finding oluştu" → UI anında güncellenir
    → "Interview tamamlandı" → Orchestrator tetiklenir
```

**REST vs MCP Farkı:**
- REST = veri arayüzü (CRUD), herkes tüketir
- MCP = yetenek arayüzü (agent-native), agent'lar tüketir

**Örnek — Kubernetes Agent interview sırasında:**
```
MCP Resources:   current_task_findings, question_bank/kubernetes, similar_findings
MCP Tools:       create_finding(), add_evidence(), flag_risk(), suggest_next_question()
Event akışı:     add_evidence → event → create_finding → SSE → UI güncellenir
```

#### Karar: Data Catalog Araç Seçimi

**Karar:** OpenMetadata (open source)

**Gerekçe:**

| Kriter | OpenMetadata | DataHub | Apache Atlas |
|---|---|---|---|
| Data Contracts | Native | Kısıtlı | Yok |
| Kubernetes | Native Helm | Native | Ağır |
| Lineage API | Erişilebilir | GraphQL | Kısıtlı |
| Informatica geçişi | Kolay (OpenLineage) | Orta | Zor |
| Operasyon zorluğu | Düşük | Orta | Yüksek |

**Informatica Migration Yolu:**
```
Şimdi:     OpenMetadata (open source, OpenLineage standard)
              ↓ parallel çalıştır, validate et
İleride:   Informatica IDMC (enterprise)
```

**OpenMetadata'da Custom Entities:**
- Finding (evidence link'leri, confidence, task)
- Risk Register (severity dağılımı, capability etkisi)
- Recommendation (horizon, priority, roadmap item)
- Question Bank (workstream bazlı, kullanım sayısı)

---

### 4.3 Knowledge Layer

> **Durum:** Tasarım tamamlandı ✓

#### Bileşenler

```
Knowledge Layer
├── Semantic Mapping Layer   ← ontological semantic layer (OBDA / R2RML)
│   Information Layer data product'larını ontolojik kavramlara çevirir
├── Enterprise Ontology      ← OWL, versiyonlanmış, human approval gerektirir
├── Knowledge Graph          ← RDF triples, gerçek varlıklar
├── Business Rules & Inference ← SHACL constraints, OWL axioms
└── Reasoning Engine         ← Apache Jena Reasoner
```

#### Karar: Semantic Mapping Layer Yerleşimi

**Karar:** Knowledge Layer'ın tabanında — Information Layer'da değil.

**Gerekçe:** Ontoloji değişince sadece mapping güncellenir, Information Layer dokunulmaz. Bağımlılık doğru yönde akar.

```
Akış:  Domain Object / Published Product → Semantic Mapping → RDF Triple → Knowledge Graph → Reasoner → Agent
```

**Not:** KG mapping önceliği **Domain Information Objects** (1:1 instance) üzerindedir. Published Data Products catalog ve compose seviyesinde temsil edilir; her composite product'ın ayrı KG individual'ı şart değildir.

#### Karar: AI Agent Orchestration Yerleşimi

**Karar:** Agent Layer'da — Knowledge Layer'da değil.

**Gerekçe:**
- Knowledge Layer sorusu: "Ne biliyoruz?" → statik, governance'a tabi
- Agent Orchestration sorusu: "Kim ne yapıyor?" → dinamik, execution-time

Aynı katmanda olmak bu farkı bulanıklaştırır, governance sınırını kaldırır.

#### Karar: İki Farklı Semantic Layer

| Semantic Layer | Konum | Amaç |
|---|---|---|
| Business Semantic Layer | Information Layer | BI metrikleri, KPI'lar, dashboard'lar için |
| Ontological Semantic Layer | Knowledge Layer tabanı | OWL/RDF mapping, agent ve reasoner için |

#### Teknoloji

| Bileşen | Teknoloji |
|---|---|
| Ontology & Knowledge Graph | Apache Jena Fuseki |
| Ontology Language | OWL |
| Data Format | RDF |
| Query Language | SPARQL |
| Validation | SHACL |
| Reasoning | Apache Jena Reasoner |
| Deployment | Docker / Kubernetes |

---

### 4.4 Agent Layer

> **Durum:** Tasarım tamamlandı ✓

#### Agent Taksonomisi

```
Assessment Agent'ları
├── Task Agent'ları (8 adet — workstream başına 1)
├── Orchestrator Agent (1 adet — cross-task koordinasyon)
├── Ontology Co-Pilot Agent (1 adet — ontoloji önerileri, human approval)
└── Research Agent'ları
    ├── Assessment Memory Agent (geçmiş engagement'lar — düşük risk)
    └── Domain Research Agent (best practice araştırması — human review zorunlu)

Development Agent'ları (ayrı — geliştirme metodolojisi, ürün mimarisi dışında)
```

#### Task Agent'ları — Scope ve Sorumluluklar

| Agent | Domain | Özel Not |
|---|---|---|
| Kubernetes Agent | K8s resilience, node topology, monitoring, incident history | Production analytics operasyonel kritiklik |
| Cloud Strategy Agent | Cloud transformation, GCP services, migration strategy | GCP servislerine alignment |
| Ingestion Agent | NiFi, DataStage, Airflow, XML parsing, ETL bottlenecks | Teradata domino etkisi analizi kritik |
| Teradata DR Agent | EDW DR, end-of-support risk, TPT, CIM, cloud DR | Active-Passive / Warm Standby / Hybrid karşılaştırması |
| Lakehouse Agent | Lakehouse architecture, data zones, query performance | Sorular henüz oluşturulmadı |
| Governance Agent | Governance maturity, roles, catalog, lineage, KVKK/GDPR | Research Agent tetikleyebilir |
| Data Product Agent | Data product operating model, domain ownership, data contracts | Data mesh prensipleri |
| CDP Agent | Customer 360, Teradata CIM, campaign, real-time activation | Ingestion Agent ile cross-task bağımlılık kritik |

#### Task Agent Lifecycle

```
PRE_INTERVIEW              DURING INTERVIEW              POST_INTERVIEW
─────────────              ────────────────              ──────────────
Question bank yükle        Yanıtı analiz et              Task raporu üret
Geçmiş bulguları tara      Sonraki soruyu öner           Recommendations
Workstream scope'u belirle Evidence yakala               Roadmap items
Checkpoint varsa devam et  Finding sinyali ver           Maturity skoru
                           Risk işaretle                 Knowledge Graph'a yaz
                           Eksik evidence uyar
```

#### Orchestrator Agent

```
Sorumluluklar:
  → Cross-task bağımlılık tespiti (Knowledge Graph üzerinden SPARQL)
  → Çelişen finding'leri tespit et → human review'a gönder
  → Risk konsolidasyonu → 8 workstream risk heatmap
  → Executive summary (C-level)
  → Consolidated roadmap (8 roadmap → öncelikli 1 plan)

Örnek cross-task tespiti:
  CDP Agent:       "Real-time activation gerekiyor"
  Ingestion Agent: "Batch only yapılabiliyor"
  Orchestrator:    "Mimari uyumsuzluk" → executive finding üretir
```

#### Orchestration Mimarisi (LangGraph)

**Pattern: Supervisor**

```
ORCHESTRATOR (Supervisor Graph)
       │ watches / coordinates
       ▼
Task Agent Pool (8 bağımsız graph — interview sırasında paralel çalışır)
```

**Task Agent LangGraph Graph:**
```
PRE_INTERVIEW
  └── context_loader → scope_setter → memory_restore
INTERVIEW_LOOP
  └── answer_processor → question_advisor (fast/WebSocket)
                       → evidence_capture → finding_detector
POST_INTERVIEW
  └── finding_analyzer → risk_assessor → recommendation_gen
                      → report_writer → knowledge_writer
```

**State Yönetimi:**

| State Tipi | Kapsam | Teknoloji |
|---|---|---|
| Private State | Agent'a özel, session-scoped | Redis |
| Shared State | Tüm agent'lar, kalıcı | Knowledge Graph + PostgreSQL |
| Checkpoint | Graph durumu, resume için | PostgreSQL (LangGraph native) |

**Human-in-the-Loop Interrupt Noktaları:**

| Tetikleyici | Aksiyon |
|---|---|
| Finding üretildi | Consultant onaylar / reddeder / düzenler |
| Risk flaglendi | Severity'yi consultant confirm eder |
| Soru atlanacak | "Atlayayım mı?" → consultant karar verir |
| Recommendation | Consultant validate eder |
| Ontoloji önerisi | Knowledge ekibi onaylar |

#### Agent Registry

**Karar:** Knowledge Graph'ta yaşar — SPARQL ile keşfedilir.

```turtle
aakp:KubernetesAgent rdf:type aakp:AssessmentAgent ;
    aakp:hasScope "kubernetes-resilience" ;
    aakp:hasWorkstream "k8s-assessment" ;
    aakp:hasQuestionBank "kb://questions/kubernetes" ;
    aakp:hasTool "create_finding" ;
    aakp:hasStatus "active" .
```

**Yeni agent ekleme:** SPARQL INSERT → registry'ye kayıt. Orchestrator kodu değişmez.

#### Genişletilebilirlik Prensipleri

- **Yeni yetenek:** Yeni MCP tool ekle → agent core değişmez
- **Yeni agent:** Agent Registry'ye kayıt → Orchestrator otomatik keşfeder
- **Agent iletişimi:** Doğrudan değil — Knowledge Graph veya Orchestrator üzerinden
- **Paralel interview:** Her consultant için bağımsız LangGraph instance

---

### 4.5 Guardrails

> **Durum:** Tasarım tamamlandı ✓

#### 5 Kategori

**1. Input Guardrails** — Sisteme giren her şeyi kapıda filtreler

```
Tetiklenme: doküman yükleme, yanıt girişi, research içeriği, evidence ekleme

Kontroller:
  PII Detection         → Presidio
  Sensitive Data        → credentials, gizli ticari bilgi
  Scope Validation      → içerik bu workstream'e ait mi?
  Format Validation     → desteklenen dosya tipi mi?
  Evidence Completeness → minimum alan dolu mu?

Teknoloji: Microsoft Presidio + FastAPI middleware
```

**2. Retrieval Guardrails** — Agent neye erişebilir, neye erişemez

```
Kurallar:
  → Her agent yalnızca kendi scope'undaki knowledge'a erişir
  → Agent'lar birbirinin working memory'sine erişemez
  → Research Agent Knowledge Graph'a yazamaz — sadece okur
  → Ontology Co-Pilot dışında hiçbir agent ontoloji değiştiremez

Teknoloji: OPA (Open Policy Agent) + Keycloak RBAC
```

**3. Reasoning Guardrails** — Desteklenmeyen sonuçları engeller

```
Temel kural: "No finding without evidence — 0 tolerance"

Zorunlu zincir:
  Answer → Evidence → Finding → Risk → Recommendation

LangGraph edge conditions:
  Finding node'una geçiş  → en az 1 evidence gerekli
  Risk node'una geçiş     → en az 1 finding gerekli
  Report node'una geçiş   → tüm findings validated
```

**4. Output Guardrails** — Rapor üretilmeden önce son kontrol

```
Kontroller:
  Evidence chain complete?    → her finding için
  Risk justification exists?  → her risk için finding var mı?
  Confidence score present?   → tüm finding'lerde mevcut mu?
  Sensitive info filtered?    → Presidio ile PII tarama
  Recommendation grounded?    → addressesGap veya mitigatesRisk var mı?

Teknoloji: SHACL shapes + custom validators + Presidio
```

**5. Governance Guardrails** — Enterprise knowledge'ı korur

```
Kurallar:
  → Otomatik ontoloji publish yok
  → Otomatik ontoloji silme yok
  → Her KG yazma → SHACL validation zorunlu
  → Research Agent çıktıları "candidate" statüsünde girer
  → Human approval olmadan "approved" olamaz
  → Her değişiklik immutable audit log'a yazılır

Teknoloji: OPA + SHACL + Keycloak + immutable audit log
```

#### Defense in Depth — "No Finding Without Evidence"

Aynı kural **5 farklı katmanda** uygulanır:

```
Katman 1 — MCP Tool (Input)
  create_finding(evidence_id: required) → evidence_id eksikse anında hata

Katman 2 — LangGraph Edge (Reasoning)
  Finding → Risk geçişi → evidence bağlı değilse traverse edilmez

Katman 3 — SHACL Validation (Governance)
  Finding triple'ı KG'ye yazılmak istiyor
  → supportedByEvidence zorunlu → fail → yazma bloklanır

Katman 4 — Output Validator (Output)
  Rapor üretilmeden önce → tüm finding'lerin evidence'ı kontrol
  → Eksik varsa rapor üretilmez

Katman 5 — Human Review (UI)
  Confidence renk kodu: kırmızı = evidence eksik
  → Görsel uyarı olmadan consultant onay veremiyor
```

#### Guardrail Akışı

```
Gelen İstek
     ↓
[Input Guardrail]      ← FastAPI middleware, Presidio
     ↓ geçti
[Retrieval Guardrail]  ← OPA, RBAC
     ↓ geçti
[Agent Reasoning]
     ↓
[Reasoning Guardrail]  ← LangGraph edge conditions, SHACL
     ↓ geçti
[Output Guardrail]     ← validators, Presidio, SHACL
     ↓ geçti
[Governance Guardrail] ← OPA, audit log, human approval
     ↓ geçti
Knowledge Graph / Report
```

#### Teknoloji Özeti

| Kategori | Teknoloji | Konum |
|---|---|---|
| Input | Microsoft Presidio + custom rules | FastAPI middleware |
| Retrieval | OPA + Keycloak RBAC | API Gateway |
| Reasoning | LangGraph edge conditions | Agent workflow |
| Output | SHACL + Presidio + validators | Report generator |
| Governance | OPA + SHACL + immutable audit log | Knowledge Layer |

---

### 4.6 Monitoring & Observability

> **Durum:** Tasarım tamamlandı ✓

#### İki Gözlemlenebilirlik Katmanı

```
Katman 1 — Infrastructure Observability
  Kubernetes pod'ları, CPU/Memory, storage, Kafka lag, DB performance

Katman 2 — Agent Observability (AAKP'ye özgü)
  Token kullanımı, maliyet, confidence score, guardrail ihlalleri,
  evidence coverage, hallucination detection
```

#### Teknoloji Stack

| Bileşen | Teknoloji | Açıklama |
|---|---|---|
| LLM / Agent Observability | LangFuse (open source, self-hosted) | Token, maliyet, trace, evaluation |
| Infrastructure Metrics | Prometheus + Grafana | Kubernetes, servis metrikleri |
| Log Aggregation | Loki | Grafana ekosistemi |
| Distributed Tracing | OpenTelemetry + Grafana Tempo | End-to-end request trace |
| Unified Dashboard | Grafana | Tüm kaynakları birleştirir |
| Alerting | Grafana Alerting | Kural bazlı uyarılar |

#### Neden LangFuse?

Klasik Prometheus LLM'e özgü metrikleri görmez. LangFuse her LLM çağrısını trace eder:
```
Assessment_Migros → Task_K8s → Interview_Session_1
  → suggest_next_question (245 token, 1.2sn)
  → analyze_evidence (612 token, 2.8sn)
  → create_finding (389 token, 1.9sn)
```
LangGraph native entegrasyon, Kubernetes Helm chart ile deploy edilir.

#### 4 İzleme Boyutu

```
1. LLM / Agent Calls    → token, latency, cost, error rate
2. Assessment Quality   → evidence coverage, confidence, violations
3. Infrastructure       → pod health, storage, DB, Kafka
4. Business             → finding sayısı, risk dağılımı, interview completion
```

#### En Kritik Metrik

```
Recommendation without evidence = 0   (0 tolerance)
Bu sayı > 0 olursa → CRITICAL alert → anlık investigation
```

#### AAKP Custom Prometheus Metrics

FastAPI `/metrics` endpoint'inden export edilir:

```
evidence_coverage_score           # evidence'lı finding / toplam — per assessment
guardrail_violations_total        # kategori bazında sayaç
recommendation_without_evidence   # 0 tolerance metriği
agent_confidence_avg              # agent başına ortalama confidence
unsupported_findings_blocked      # kural 7 ile kaç finding bloklandı
cross_task_dependencies_found     # orchestrator kaç bağımlılık buldu
```

#### Grafana Dashboard'ları

| Dashboard | İçerik |
|---|---|
| Agent Performance | Token, latency, error rate, confidence — agent bazında |
| Cost / Credit | Assessment bazında maliyet, token trend, projeksiyon |
| Task Activity Timeline | Gantt-style — her agent'ın pre/interview/post fazları |
| Guardrail Violations | Kategori bazında ihlal sayıları |
| Evidence Coverage | Workstream bazında coverage yüzdeleri |
| LLM Call Logs | Timestamp, agent, token, latency, trace link |

#### Alerting Stratejisi

| Severity | Kural | Açıklama |
|---|---|---|
| CRITICAL | recommendation_without_evidence > 0 | 0 tolerance ihlali |
| CRITICAL | guardrail_violations spike | Anormal artış |
| CRITICAL | agent_error_rate > %5 | Sistem sorunu |
| WARNING | evidence_coverage < %80 | Kalite riski |
| WARNING | agent_confidence_avg < 0.6 | Güvenilirlik düştü |
| WARNING | LLM latency p95 > 5sn | UX bozuluyor |
| INFO | Assessment tamamlandı | — |
| INFO | Cross-task dependency tespit edildi | — |

#### Kubernetes Deployment

```
monitoring namespace:
├── prometheus   (StatefulSet)
├── grafana      (Deployment)
├── loki         (StatefulSet)
├── tempo        (Deployment)
└── langfuse     (Deployment + PostgreSQL)

Her servis:
  → /metrics endpoint (Prometheus scrape)
  → OpenTelemetry SDK (trace gönderimi)
  → Structured logging (Loki ingestion)
```

---

### 4.7 Deployment Mimarisi

> **Durum:** Tasarım tamamlandı ✓

#### Namespace Organizasyonu

```
aakp-data          → MinIO, Iceberg REST Catalog
aakp-information   → PostgreSQL, Qdrant, Kafka, FastAPI, MCP Server, OpenMetadata
aakp-knowledge     → Fuseki, Trino
aakp-agent         → LangGraph workers, Redis, Keycloak, OPA
aakp-frontend      → React UI, Nginx
aakp-monitoring    → Prometheus, Grafana, Loki, Tempo, LangFuse
```

Her namespace kendi RBAC policy'sine sahip. `aakp-knowledge` namespace'ine sadece yetkili servisler erişebilir.

#### Karar: LangGraph Workers → Shared Worker Pool

```
LangGraph Worker Pool (Deployment + HPA)
├── worker-pod-1  → K8s Agent task'ı işliyor
├── worker-pod-2  → CDP Agent task'ı işliyor
├── worker-pod-3  → boşta, yeni task bekliyor
└── worker-pod-N  → HPA ile yük arttıkça açılır, azalınca kapanır
```

Pod, Agent Registry'den agent scope ve tool listesini yükleyerek rolünü alır. Dedicated pod'lar yerine shared pool — kaynak verimli, scale kolay.

#### Karar: MinIO → Standalone (Single Node)

```
MinIO (StatefulSet, 1 pod + PersistentVolume)
```

Assessment artifact hacimleri için yeterli. İleride ihtiyaç olursa distributed mode'a geçilebilir.

#### Karar: Helm Charts → Per-Namespace (5 Chart)

```
aakp-data-chart          → MinIO, Iceberg REST Catalog
aakp-information-chart   → PostgreSQL, Qdrant, Kafka, FastAPI, MCP, OpenMetadata
aakp-knowledge-chart     → Fuseki, Trino
aakp-agent-chart         → LangGraph workers, Redis, Keycloak, OPA
aakp-monitoring-chart    → Prometheus, Grafana, Loki, Tempo, LangFuse
```

**Deploy sırası:** data → information → knowledge → agent → monitoring

Her chart bağımsız `helm upgrade` alır. Knowledge Layer ontoloji değişikliğinde sadece `aakp-knowledge-chart` güncellenir.

#### Karar: API Gateway → Kong Gateway

```
İnternet / Consultant Browser
          ↓
    Kong Gateway (aakp-frontend namespace)
    ├── /api/*   → REST API (FastAPI)     — rate limit + JWT
    ├── /mcp/*   → MCP Server             — OPA scope kontrolü
    ├── /ws/*    → WebSocket (FastAPI)    — interview fast path
    └── /ui/*    → React UI (Nginx)
```

Kong seçim gerekçesi: MCP + REST + WebSocket üç farklı protokol, OPA plugin ile retrieval guardrail gateway'de uygulanır, Keycloak JWT native entegrasyonu, agent başına LLM rate limiting.

#### Servis Tipleri

| Tip | Servisler |
|---|---|
| StatefulSet + PV | MinIO, PostgreSQL, Fuseki, Qdrant, Kafka, Loki, Prometheus, Redis |
| Deployment | FastAPI, MCP Server, LangGraph workers, React UI, OpenMetadata, LangFuse, OPA, Trino |
| Singleton | Orchestrator Agent (tek instance) |

#### Genel Cluster Görünümü

```
┌─────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                     │
│                                                         │
│  Kong Gateway (/api /mcp /ws /ui)                       │
│         │                                               │
│  ┌──────┬──────┬──────┬──────┬──────┐                  │
│  │front │info  │agent │know  │data  │                  │
│  │React │FastAPI│LGraph│Fuseki│MinIO │                  │
│  │Nginx │MCP   │Redis │Trino │Iceberg                  │
│  │      │PG    │Keycl │      │      │                  │
│  │      │Qdrant│OPA   │      │      │                  │
│  │      │Kafka │      │      │      │                  │
│  │      │OMeta │      │      │      │                  │
│  └──────┴──────┴──────┴──────┴──────┘                  │
│                                                         │
│  ┌───────────────────────────────────┐                  │
│  │  monitoring                       │                  │
│  │  Prometheus  Grafana  Loki        │                  │
│  │  Tempo  LangFuse                  │                  │
│  └───────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Ontoloji

### Dosya Yapısı

```
assessment.owl    ← assessment süreci nesneleri
architecture.owl  ← enterprise mimari kavramları
maturity.owl      ← olgunluk, risk, öneri kavramları
organization.owl  ← insan ve organizasyon kavramları
```

### Merkezi Reasoning Zinciri

```
Capability → Gap → Risk (+ Severity) → Recommendation (+ Horizon) → RoadmapItem → Report
```

**Evidence chain (zorunlu — bypass yok):**
```
Interview → Question → Answer → Evidence → Finding → Risk → Recommendation
```

### Versiyon Durumu

| Versiyon | Durum | Konum |
|---|---|---|
| v0.1 | OpenAI üretimi, temel iskelet | Assessment Domain Ontology.docx |
| v0.2 | Genişletilmiş, 15 değişiklik | Assessment Domain Ontology v0.2.md |
| v0.3 | Planlanıyor | — |

**v0.2'de Eklenenler:**
- `Interview`, `Report`, `Roadmap`, `RoadmapItem` sınıfları
- `hasSeverity` (Risk), `hasHorizon` (Recommendation), `hasConfidence` (Finding)
- `relatedToFinding` cross-task ilişkisi
- `dependsOnTask` Task bağımlılığı
- `hasStatus` Task ve Assessment lifecycle
- `hasDimension` MaturityScore çok boyutlu skorlama
- Rule 5: Confidence propagation
- Rule 6: Cross-task risk propagation
- Rule 7: Evidence'sız finding = invalid (core guardrail)

**v0.3 Planı:**
- Migros-specific domain instance'ları
- SHACL validation shapes
- OWL formal syntax
- System subclass'ları (DataWarehouse, DataIngestion, StreamingPlatform vb.)

### TBox / ABox Ayrımı

| | Konum | Örnekler |
|---|---|---|
| **TBox (Ontoloji)** | OWL dosyaları | System, DataWarehouse, DataIngestion (kategoriler) |
| **ABox (Knowledge Graph)** | Fuseki instance'ları | Teradata, NiFi, Oracle, Kubernetes (ürünler) |

**Prensip:** Yeni bir teknoloji ürünü geldiğinde ontoloji değişmez — sadece Knowledge Graph'a individual eklenir.

---

## 6. Geliştirme Metodolojisi

### Mimari Tartışma Süreci
- Tüm layer'lar önce tartışılır, kararlar netleşir
- Sonra implementation subagent'larla başlar
- Architect rolü: tek konuşmada devam (context bütünlüğü için)

### Implementation Süreci
- Subagent'larla parallel build
- Her subagent kendi domain'inde çalışır:
  - Frontend Agent → React UI
  - Backend Agent → FastAPI
  - Knowledge Layer Agent → Fuseki + OWL setup
  - DevOps Agent → Kubernetes manifests
  - Test Agent → validasyon

### Sprint / Task Takibi
- Ürün özelliği değil — geliştirme süreci
- 4 katman tasarımı bittikten sonra backlog oluşturulacak
- Agent bazlı sprint planlaması yapılacak

---

## 7. Temel Tasarım Prensipleri

1. **Knowledge-centric, data-centric değil** — agent'lar ontoloji üzerinden akıl yürütür
2. **Evidence zorunlu** — finding'siz evidence, risk'siz finding kabul edilmez
3. **Human in the loop** — ontoloji değişikliği, knowledge approval insan onayı gerektirir
4. **Vendor independent** — open source, container-native, Kubernetes-ready
5. **Separation of concerns** — her katmanın tek sorumluluğu var
6. **Agent-native interface** — agent'lar MCP ile, insanlar REST ile erişir
7. **Confidence propagation** — evidence güveni finding'e akar
8. **Cross-task visibility** — Orchestrator tüm bağımlılıkları görür
9. **Reusable blueprint** — Migros'tan başlar, tüm engagement'lara uygulanır
10. **Defense in depth** — kritik kurallar tek değil 5 katmanda uygulanır
11. **Agent Registry** — agent'lar dinamik keşfedilir, hardcode yok
12. **Extensible by design** — yeni agent = registry kaydı, yeni yetenek = MCP tool

---

## 8. Teknoloji Stack Özeti

| Katman | Bileşen | Teknoloji | Durum |
|---|---|---|---|
| Information | Ana veritabanı | PostgreSQL | Onaylandı |
| Information | Vector Store | Qdrant | Onaylandı |
| Information | Data Catalog | OpenMetadata | Onaylandı |
| Information | REST API | FastAPI | Onaylandı |
| Information | Agent API | MCP Server | Onaylandı |
| Information | Event Stream (slow path) | Kafka | Onaylandı |
| Information | Real-time Interview (fast path) | WebSocket (FastAPI) | Onaylandı |
| Knowledge | Triple Store | Apache Jena Fuseki | Onaylandı |
| Knowledge | Ontology | OWL / RDF | Onaylandı |
| Knowledge | Query | SPARQL | Onaylandı |
| Knowledge | Validation | SHACL | Onaylandı |
| Agent | Orchestration | LangGraph (Supervisor pattern) | Onaylandı |
| Agent | Session Memory | Redis | Onaylandı |
| Agent | Checkpoint Store | PostgreSQL | Onaylandı |
| Agent | Registry | Knowledge Graph (SPARQL) | Onaylandı |
| Agent | PII Detection | Microsoft Presidio | Onaylandı |
| Agent | Access Control | OPA + Keycloak | Onaylandı |
| Monitoring | LLM Observability | LangFuse (self-hosted) | Onaylandı |
| Monitoring | Infrastructure | Prometheus + Grafana | Onaylandı |
| Monitoring | Logs | Loki | Onaylandı |
| Monitoring | Tracing | OpenTelemetry + Grafana Tempo | Onaylandı |
| Frontend | UI | React | Onaylandı |
| DevOps | Container | Docker | Onaylandı |
| DevOps | Orchestration | Kubernetes + Helm (5 chart) | Onaylandı |
| DevOps | API Gateway | Kong Gateway | Onaylandı |
| Data | Object Storage | MinIO (standalone) | Onaylandı |
| Data | Table Format | Apache Iceberg | Onaylandı |
| Data | Table Catalog | Iceberg REST Catalog | Onaylandı |
| Data | Query Engine | Trino | Onaylandı |

---

## 9. Açık Kararlar

| Konu | Durum |
|---|---|
| Data Layer tasarımı | Tamamlandı ✓ |
| Agent Layer detayları | Tamamlandı ✓ |
| Guardrail implementasyonu | Tamamlandı ✓ |
| Security (Keycloak / OPA) | Guardrails ile kapsandı ✓ |
| Monitoring & Observability | Tamamlandı ✓ |
| Lakehouse workstream soruları | Birlikte oluşturulacak |
| Ontoloji v0.3 (OWL syntax) | Implementation aşamasında |
| Deployment Mimarisi | Tamamlandı ✓ |
| Backlog & Sprint planı | Tamamlandı ✓ — TASKS.md |
| Domain Objects vs Published Products | Tamamlandı ✓ — §4.2 ADR |

---

*Bu doküman her mimari tartışma sonrası güncellenir.*
