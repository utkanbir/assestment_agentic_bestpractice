# Semantic Intelligence Framework

**Best Practice Architecture Blueprint for Enterprise Knowledge Management**

Trusted context layer for agents and enterprise knowledge.

Reference implementation: **Agentic Assessment Knowledge Platform (AAKP)**

| Field | Value |
|-------|-------|
| Document Type | Internal Best Practice Architecture / Reference Framework |
| Primary Goal | Define how ontology, knowledge graph, semantic layer, published data products, agents and governance work together as a reusable enterprise framework. |
| Reference Use Case | Assessment is only an example implementation, not the final product boundary. |
| Target Audience | Enterprise architects, data architects, platform teams, governance teams, AI/agent teams, consulting/product teams. |
| Version | **v1.3** — simplified Data Layer (§4); lakehouse stack moved to Appendix B |

**Related repo docs:** `ARCHITECTURE_DECISIONS.md` §4.2, `DATA_PRODUCTS_SEMANTIC_LAYER_DISCUSSION.md`, `data_products_catalog.yaml`

---

## 1. Executive Summary

This document defines a **Semantic Intelligence Framework** for building governed, reusable, ontology-driven knowledge systems inside the enterprise. The framework is not an assessment product by itself. Assessment is used as a reference implementation to demonstrate how the same architectural concepts can be applied to any enterprise domain.

The central idea: AI agents, applications and users should not reason directly on raw data. Enterprise reasoning happens through a governed semantic chain:

**raw data → Domain Information Objects → ontology mapping → Knowledge Graph → Published Data Products → governed agent/application interfaces**

---

## 2. Strategic Positioning

| Not This | But This |
|----------|----------|
| Traditional RAG stack | Ontology-driven semantic intelligence framework |
| BI/dashboard layer | Reusable knowledge and reasoning layer |
| Data catalog only | Catalog + ontology + knowledge graph + published data product governance |
| Agent framework only | Governed agent access to semantic enterprise knowledge |
| Assessment tool | Assessment as reference implementation of the framework |

---

## 3. Framework Thesis

- Every domain has raw artifacts, structured objects, semantic concepts, relationships, governed outputs and consumers.
- **Ontology** provides shared meaning and vocabulary.
- **Knowledge Graph** connects objects, concepts, evidence, ownership, dependencies and reasoning paths.
- **Published Data Products** provide governed consumption surfaces for users, applications and agents.
- Knowledge certification and composition are **attributes of a Published Data Product**, not separate top-level product categories.
- Agents consume published and governed semantic assets instead of raw tables or files.
- Human-in-the-loop governance controls sensitive actions, product certification and semantic model evolution.

---

## 4. Reference Layered Architecture

| Layer | Purpose | Core capabilities (technology-agnostic) |
|-------|---------|----------------------------------------|
| Data Layer | Raw and bronze-level artifacts | Object storage, files, exports, logs; optional event streams |
| Information Layer | Domain Information Objects + Published Data Products | Operational store, contracts, lineage, REST/MCP API, vector index |
| Knowledge Layer | Meaning, constraints, relationships | Ontology (OWL/RDF), graph store, SPARQL, validation (SHACL) |
| Semantic Intelligence Layer | Retrieval, reasoning, semantic services (logical plane) | Hybrid retrieval, GraphRAG, semantic search, inference |
| Agent Layer | Agent reasoning over governed semantic assets | Orchestrator, specialized agents, MCP tools/resources |
| Experience Layer | Workflows and products for humans | Workbench, dashboards, report studio |
| Governance & Security | Trust and compliance (cross-cutting) | RBAC/ABAC, policy engine, audit, approval workflows |

**AAKP reference stack (minimum proven loop):** PostgreSQL, Fuseki, FastAPI/MCP, Qdrant. Question Bank is the first end-to-end product slice.

The Semantic Intelligence Layer does **not** replace operational databases, object storage, or graph stores. It defines how business objects are understood, mapped, published and consumed across those systems.

Lakehouse technologies (MinIO, Iceberg, Trino, Kafka) are **optional** — see Appendix B. They are not required to explain or implement the semantic intelligence loop.

---

## 5. Generic Semantic Intelligence Pipeline

1. Ingest raw domain artifacts.
2. Normalize into **Domain Information Objects** with validation, ownership and lifecycle state.
3. Map objects to ontology classes, properties and controlled vocabularies.
4. Materialize semantic relationships in the **Knowledge Graph**.
5. Publish governed **Published Data Products** with contracts, ownership, lineage and quality expectations.
6. Optionally enrich products with attributes: `knowledge_certified`, `composite`, `reusable`, `marketplace_visible`.
7. Expose products through APIs, MCP resources, semantic search and UIs.
8. Allow agents to reason through ontology, graph paths and Published Data Products.
9. Require human approval for governance-sensitive actions.
10. Capture feedback and evolve ontology, knowledge, products and agent behavior.

### 5.1 Example: Questions and Question Bank (simplified)

Questions illustrate the two-concept model without extra categories or over-engineering.

| Component | Role |
|-----------|------|
| **Question** | **Domain Information Object** — reusable prompt in the global library, scoped by workstream. Assessment-independent canonical record (`workstream_questions` in AAKP). |
| **Question Bank** | **Published Data Product** — governed API/MCP port exposing approved/active questions to users and agents. |
| **Assessment session copy** | Runtime copy of question text into an interview session so answers and evidence attach to that engagement. **Implementation detail**, not a separate framework concept (`questions` table in AAKP). |

**Flow (5 steps):**

1. Consultant creates a question in Question Management → stored as a **Question** domain object (global bank, assessment-independent).
2. Optional: map to ontology/workstream semantics in the Knowledge Layer.
3. Active questions are exposed through the **Question Bank** product (`GET /api/v1/question-bank`, MCP `resource://question_bank/{workstream}`).
4. When an assessment interview starts, questions are **copied** from the bank into the session (not linked by reference).
5. Agents consume questions through the **Question Bank** port, not raw database tables.

**AAKP mapping:**

| Framework | AAKP |
|-----------|------|
| Question (canonical) | `WorkstreamQuestion` — Soru Yönetimi ekranı |
| Question Bank (product) | `GET /api/v1/question-bank` + MCP resource |
| Session copy | `Question` per interview — cevap/evidence zinciri için |

**Not in scope for this example (Phase 2+):** raw file ingest to object storage, capability/finding-pattern ontology properties, product certification attributes on Question Bank.

A single question row is **not** a data product. The **Question Bank** aggregate is the product.

---

## 6. Domain Information Objects vs Published Data Products

Avoid calling every entity a data product. The framework uses **two first-class concepts**:

| Concept | Definition | Assessment Example |
|---------|------------|-------------------|
| **Domain Information Object** | Structured, validated domain object used internally by workflows | Finding, Evidence, **Question** (bank) |
| **Published Data Product** | Contracted, discoverable consumption surface with owner, contract, lineage, access interface | **Question Bank**, Finding Library, Risk Register, Assessment Results View |

**Published Data Product attributes** (optional metadata flags, not separate types):

| Attribute | Meaning |
|-----------|---------|
| `knowledge_certified` | Reviewed, reusable, evidence-backed semantic asset |
| `composite` | Read model derived from multiple objects or products |
| `reusable` | Reusable across engagements, domains or teams |
| `marketplace_visible` | Discoverable in internal marketplace/catalog |

Question Bank v1: `reusable: true` is sufficient; other attributes optional or Phase 2.

---

## 7. Core Framework Meta-Model

| Concept | Meaning |
|---------|---------|
| Domain | Bounded enterprise area (Data Governance, Risk, Architecture, …) |
| Capability | Business/technical capability that can be assessed, owned, measured |
| Domain Information Object | Structured object representing domain knowledge |
| Semantic Concept | Ontology class or controlled vocabulary term |
| Relationship | Typed semantic link between objects, capabilities, evidence, outcomes |
| Evidence | Traceable support artifact |
| Published Data Product | Governed product with contract, lineage, owner, consumption interface |
| Agent Capability | Governed agent function (inspect, reason, recommend, generate) |
| Policy | Machine-enforceable rule for access, validation, lifecycle, approval |

---

## 8. Assessment as Reference Implementation

Assessment is the first reference implementation, not the platform boundary.

| Framework Concept | Assessment Implementation |
|-------------------|---------------------------|
| Domain | Enterprise Assessment |
| Domain Information Objects | **Question** (bank), Answer, Evidence, Finding, Risk, Recommendation, Maturity Score |
| Published Data Products | **Question Bank**, Finding Library, Risk Register, Maturity Scorecard, Assessment Results View |
| Agents | Assessment agents, orchestrator, research agent |
| Governance | Consultant approval, evidence validation, report approval |

---

## 9. Minimum Viable Framework Loop

1. Define one domain ontology and one capability taxonomy.
2. Create a few Domain Information Objects with lifecycle state.
3. Map them to ontology concepts.
4. Materialize relationships in the Knowledge Graph.
5. Publish one or two governed Published Data Products.
6. Expose through API/MCP.
7. Let one agent recommend using evidence, graph paths and product contracts.
8. Require human approval for sensitive output.
9. Capture feedback and update the knowledge lifecycle.

**Question Bank is a suitable first vertical slice** for steps 2–6 in AAKP.

**AAKP today:** the proven loop runs on PostgreSQL + Fuseki + MCP (Question Bank, Finding Library ports) + Qdrant for embeddings. Lakehouse components are deployed in cluster but not on the critical path for this slice — see Appendix B.

---

## 10. Architecture Rules

- Do not let agents directly query raw tables or files for governed reasoning.
- Do not call every entity a data product.
- Use only **Domain Information Object** and **Published Data Product** as first-class information concepts.
- Knowledge-certified and composite behavior = **attributes** of Published Data Products, not separate top-level types.
- Every Published Data Product must have owner, contract, lineage, freshness expectation and consumption interface (target state; L0 may start minimal).
- Agent consumption must go through Published Data Product ports such as **Question Bank**.
- Assessment remains a reference implementation, not the platform boundary.
- Governance must be runtime-enforced, not only documented.

---

## 11. Recommended Naming

| Item | Name |
|------|------|
| Umbrella framework | **Semantic Intelligence Framework** |
| Reference implementation | **Agentic Assessment Knowledge Platform (AAKP)** |

**Positioning sentence:**

> Semantic Intelligence Framework is an internal best practice architecture that defines how ontology, knowledge graph, semantic layer, Published Data Products, agents and governance work together to create reusable, trusted and agent-readable enterprise knowledge systems.

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| Semantic Intelligence | Reasoning over enterprise knowledge using meaning, relationships, evidence and governed products |
| Domain Information Object | Structured internal object representing domain knowledge |
| Published Data Product | Governed, discoverable output with contract and consumption interface |
| Question (canonical) | Reusable assessment prompt in the global bank — assessment-independent |
| Question Bank | Published Data Product exposing approved questions via API/MCP |
| Ontology | Formal definition of concepts, properties, constraints |
| Knowledge Graph | Graph of entities, relationships, evidence and reasoning paths |
| MCP Resource | Governed interface through which agents access Published Data Products |

---

## Appendix B: Reference Lakehouse Stack (optional)

Use this stack when the engagement is data-platform-heavy (lakehouse, federation, bronze ingestion). It extends the Data Layer but is **not** part of the minimum Semantic Intelligence Framework loop.

| Technology | Typical role | AAKP status |
|------------|--------------|-------------|
| MinIO (or S3-class) | Bronze object storage for raw files and exports | Deployed; API integration planned |
| Apache Iceberg | Table format with schema evolution | Deployed; not on critical path |
| Trino | Cross-source SQL federation | Deployed; not used in current API loop |
| Kafka | Async event bus (slow path) | Deployed; MCP/event publish only |

**When to include in a domain design:** large file ingest, cross-system analytics, batch pipelines, data mesh product ops.

**When to omit from framework narrative:** explaining Question Bank, Finding Library, ontology mapping, or agent consumption ports.

Operational registry (full cluster inventory): `knowledge/architecture/layers.yaml`, `ARCHITECTURE_DECISIONS.md` Data Layer ADRs.

---

*Rev. 1.3 — §4 Data Layer technology-agnostic; MinIO/Trino/Iceberg/Kafka → Appendix B. Rev. 1.2 — §5.1 Questions simplified.*
