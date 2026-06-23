# AAKP — Data Products, Domain Objects & Semantic Layer

**Tarih:** 2026-06-18 (rev. 1.2)  
**Amaç:** Mimari tartışmayı başka bir AI veya ekip üyesiyle sürdürebilmek için özet.  
**Otorite:** `ARCHITECTURE_DECISIONS.md` §4.2 ADR — çelişki durumunda ADR geçerlidir.  
**Framework:** `knowledge/architecture/SEMANTIC_INTELLIGENCE_FRAMEWORK.md` (v1.3)

---

## 1. Bağlam: 4 Katmanlı Mimari

```
Data Layer → Information Layer → Knowledge Layer → Agent Layer
```

**Temel prensip:** Agent'lar ham veri üzerinde değil; **domain objects → published products → semantic mapping → knowledge graph** zinciri üzerinden akıl yürütür.

| Katman | Namespace | Medallion |
|--------|-----------|-----------|
| **Data** | `aakp-data` | Bronze |
| **Information** | `aakp-information` | Silver (domain objects) + Gold (published products) |
| **Knowledge** | `aakp-knowledge` | Ontology, KG, semantic mapping |
| **Agent** | `aakp-agent` | Orchestration, LLM |

---

## 2. Information Layer — İç Yapı (ADR v1.1)

```
Information Layer
├── Business Semantic Layer
├── Domain Information Objects      ← Silver
├── Published Data Products         ← Gold
├── Data Contracts
├── Metadata & Lineage
├── Vector Store
└── API Layer (REST + MCP + Kafka)
```

### 2.1 Domain Information Objects (Silver)

Structured, validated, workflow-aware domain entities. Domain logic, human-in-the-loop ve internal API bu seviyede çalışır.

| Nesne | Not |
|-------|-----|
| Assessment | **Container — data product değil** |
| Task | Container |
| Interview | Oturum |
| **Question (canonical)** | Global soru bankası satırı (`WorkstreamQuestion`) — assessment'tan **bağımsız**; Soru Yönetimi ekranı |
| Question (session copy) | Interview oturum kopyası (`questions` tablosu) — cevap/evidence zinciri için; **framework'te ayrı DIO değil** |
| Answer | Müşteri cevabı |
| Answer Evaluation | AI yorumu (`answers.evaluation`) |
| Evidence | Kanıt (+ Bronze pointer) |
| Finding | Bulgu |
| Risk | Risk |
| Recommendation | Öneri |
| Consultant Comment | Danışman yorumu |
| Maturity Score | WS olgunluk değerlendirmesi |
| Interview Q&A bundle | Session copy + Answer + Evaluation — **default product değil** |

### 2.2 Published Data Products (Gold)

Contract, lineage, ownership, discoverability ve consumption port gerektiren publish edilmiş ürünler.

| Ürün | Classification |
|------|----------------|
| Question Bank | `published_data_product` |
| Finding Library | `published_data_product` |
| Risk Register | `published_data_product` |
| Recommendation Catalog | `published_data_product` |
| Maturity Scorecard | `published_data_product` |
| Evidence Catalog | `published_data_product` |
| Executive Summary | `composite_published_data_product` |
| Assessment Results View | `composite_published_data_product` |
| Assessment Report | `composite_published_data_product` |

**Product maturity tiers:** L0 (listed) → L1 (contracted) → L2 (governed). Şu an çoğu ürün L0.

### 2.3 Terim sözlüğü

| Terim | Anlam |
|-------|--------|
| Maturity Score | Domain object — tek workstream skoru |
| Maturity Scorecard | Published product — tüm WS aggregate |
| Answer Evaluation | Domain object — AI interview yorumu |
| Finding Library | Published product — Finding aggregate + discovery |

---

## 3. Semantic Layer — İki Ayrı Kavram

| Semantic Layer | Konum | Amaç |
|----------------|-------|------|
| **Business Semantic** | Information Layer | KPI kuralları, composite read model logic |
| **Ontological Semantic** | Knowledge Layer tabanı | OWL/RDF mapping, reasoner |

**KG mapping önceliği:** Domain Information Objects (1:1 instance). Published products catalog/compose seviyesinde; her composite için ayrı KG individual şart değil.

```
Domain Object → Semantic Mapping → RDF → Fuseki → Agent
Published Product → REST/MCP port → (compose internal read) → Agent
```

---

## 4. Agent Erişim Kuralları

| İşlem | Yol |
|-------|-----|
| **Agent read** | Published Data Products — REST/MCP primary port |
| **Agent write** | Domain objects — MCP tools (guardrail'li workflow) |
| **UI CRUD** | Domain objects — internal REST |
| **Product compose** | Internal service PG okuyabilir — agent-facing raw table yasak |

**Chat örneği:** “Bu assessment sonuçlarını göster”

```
Chat → Assessment Results View (composite_published_data_product)
     → (detay) Finding Library / Maturity Scorecard
     → (ilişki) Knowledge Layer SPARQL
```

Implementasyon: `GET /api/v1/assessments/{id}/data-products/assessment-results`, MCP `get_assessment_results`.

---

## 5. Questions — Sadeleştirilmiş model (v1.2)

Framework'te **tek Question kavramı** vardır: global soru bankasındaki canonical kayıt.

```
Soru Yönetimi → Question (DIO, WorkstreamQuestion) → assessment'tan bağımsız
                      ↓ publish
              Question Bank (Published Data Product, API/MCP)
                      ↓ interview başlangıcında kopyala
              Session copy (questions tablosu) → Answer → Evidence → …
```

| Soru | Cevap |
|------|-------|
| Soru girince assessment'a bağlı mı kaydedilir? | **Hayır** — `createWorkstreamQuestion` → `workstream_questions` |
| Assessment'a nasıl gelir? | Interview açılınca bank **kopyalanır** (referans link değil) |
| Tek soru product mı? | **Hayır** — Question Bank aggregate product |
| Agent nereden okur? | Question Bank port (`/question-bank`, MCP) — raw tablo değil |

**Interview Q&A neden product değil?** Session copy + Answer + Evaluation workflow içi Silver'dır. Dış tüketim + MCP resource + contract tanımlanırsa ayrı export product'a terfi edebilir.

---

## 6. Finding Embeddings — Product Değil, Port

Qdrant semantic search, **Finding Library**'nin `derived_index_port`'udur (`finding_semantic_search`). Ayrı standalone product değil.

---

## 7. Medallion Eşlemesi

```
Bronze  → Data Layer (raw files, exports — object storage when needed)
Silver  → Domain Information Objects (PostgreSQL entities)
Gold    → Published Data Products (API + MCP + catalog)
```

Silver → Gold: domain logic, aggregation, publish pipeline.

---

## 8. Örnek lineage

```
Evidence (domain) → Finding (domain) → Finding Library (product)
Maturity Score (domain) × N → Maturity Scorecard (product)
Finding + Maturity + Risk → Executive Summary (composite product)
Executive Summary + ... → Assessment Results View (composite product)
```

---

## 9. Classification enum (katalog)

```yaml
container
domain_information_object
published_data_product
composite_published_data_product
derived_index_port
derived_snapshot      # opsiyonel export bundle
knowledge_asset       # Fuseki / agent training — Knowledge Layer
```

Kaynak: `knowledge/architecture/data_products_catalog.yaml`

---

## 10. Açık / sonraki adımlar

1. OpenMetadata custom entities — published products için L1 contract
2. R2RML domain object → RDF otomasyonu (S2-KA-007)
3. Interview Q&A export product — ihtiyaç halinde terfi
4. Assessment Snapshot — `derived_snapshot`, planned
5. Catalog API'nin yeni şemayı expose etmesi (containers + domain + published ayrı listeler)

---

## 11. Tartışma soruları (başka AI için)

1. Executive Summary vs Assessment Report — aynı composite family mi, kardeş product mı?
2. L0 listed products agent'a açık mı, yoksa minimum L1 mi zorunlu?
3. Simülasyon Q&A otomatik üretildiğinde Finding Library'ye ne zaman publish sayılır?
4. Consultant Comment KG'ye ne zaman map edilir?
5. Data mesh domain ownership — consultant mı platform mu?

---

## 12. İlgili dosyalar

| Dosya | İçerik |
|-------|--------|
| `ARCHITECTURE_DECISIONS.md` | Resmi ADR §4.2 |
| `knowledge/architecture/SEMANTIC_INTELLIGENCE_FRAMEWORK.md` | Enterprise framework v1.3 |
| `knowledge/architecture/data_products_catalog.yaml` | Tam katalog v1.2 |
| `knowledge/architecture/layers.yaml` | UI layer registry |
| `services/api/app/services/assessment_results_product.py` | Composite product compose |
| `services/mcp-server/app/server.py` | MCP ports |

---

*Rev. 1.2 — Questions sadeleştirildi; Data Layer MinIO referansı kaldırıldı (framework v1.3).*
