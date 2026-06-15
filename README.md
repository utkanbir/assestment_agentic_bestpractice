# Agentic Assessment Knowledge Platform (AAKP)

> Enterprise-grade AI-assisted consulting assessment platform.  
> 8 AI agents, ontology-driven reasoning, evidence-mandatory findings, human-in-the-loop knowledge governance.

---

## What Is This?

AAKP enables consulting teams to conduct structured technology assessments with the help of AI agents. Each workstream (e.g. Kubernetes resilience, data governance, cloud strategy) gets its own dedicated agent that conducts interviews, captures evidence, detects findings, flags risks, and generates recommendations — all grounded in a shared enterprise ontology.

**Core principles:**
- No finding without evidence (0 tolerance enforced at guardrail level)
- All knowledge changes require human approval before entering the Knowledge Graph
- Confidence propagates from evidence to findings to risks (inference rules)
- Every agent is human-supervised, not autonomous

---

## Architecture — 4 Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  AGENT LAYER       LangGraph · 8 Assessment Agents · Orchestrator│
│                    Guardrails · Agent Memory · MCP Tools         │
├─────────────────────────────────────────────────────────────────┤
│  KNOWLEDGE LAYER   Apache Jena Fuseki · OWL/RDF · SPARQL        │
│                    SHACL Validation · Inference Rules · Reasoner │
├─────────────────────────────────────────────────────────────────┤
│  INFORMATION LAYER PostgreSQL · Qdrant · FastAPI · MCP Server   │
│                    Kafka · WebSocket · OpenMetadata              │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER        MinIO · Apache Iceberg · Trino · Kafka        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8 Assessment Agents

| Agent | Workstream |
|---|---|
| `kubernetes-agent` | Business Continuity & K8s Resilience |
| `cloud-strategy-agent` | Cloud Transformation (GCP) |
| `ingestion-agent` | Data Ingestion & ETL (NiFi / DataStage / Airflow) |
| `teradata-dr-agent` | Teradata EDW DR & Cloud Options |
| `lakehouse-agent` | Lakehouse Architecture |
| `governance-agent` | Data Governance |
| `data-product-agent` | Data Product Approach |
| `cdp-agent` | CDP & Customer 360 |

---

## Project Structure

```
assestment_best_practice/
│
├── infra/                          # Kubernetes & infrastructure (Sprint 0)
│   ├── namespaces/                 # 6 namespace definitions
│   ├── rbac/                       # RBAC policies per namespace
│   ├── helm/                       # Helm charts (one per architecture layer)
│   │   ├── data-layer/             # MinIO, Iceberg, Kafka
│   │   ├── information-layer/      # PostgreSQL, Qdrant, FastAPI
│   │   ├── knowledge-layer/        # Apache Jena Fuseki
│   │   ├── agent-layer/            # LangGraph workers, Redis
│   │   └── monitoring/             # Prometheus, Grafana, Loki, Tempo, LangFuse
│   └── gateway/                    # Kong Gateway routing rules
│
├── services/                       # Backend services (Sprint 1)
│   ├── api/                        # FastAPI — REST + WebSocket
│   └── mcp-server/                 # MCP Server — agent tools & resources
│
├── agents/                         # LangGraph agent implementations (Sprint 1–3)
│   ├── base/                       # Agent base class, scope loader, checkpoint
│   ├── kubernetes-agent/
│   ├── cloud-strategy-agent/
│   ├── ingestion-agent/
│   ├── teradata-dr-agent/
│   ├── lakehouse-agent/
│   ├── governance-agent/
│   ├── data-product-agent/
│   ├── cdp-agent/
│   └── orchestrator/               # Supervisor orchestrator (Sprint 4)
│
├── knowledge/                      # Ontology, SPARQL, SHACL (Sprint 1–2)
│   ├── ontology/                   # OWL files (v0.2 → v0.3)
│   ├── sparql/                     # Query templates per agent
│   └── shacl/                      # Validation shapes
│
├── frontend/                       # React UI — interview + dashboards (Sprint 1)
│
├── tests/                          # E2E & integration tests (Sprint 7)
│
├── docs/                           # Source documents & reference materials
│   ├── Agentic Assessment Knowledge Platform.docx
│   ├── Assessment Domain Ontology.docx
│   └── assessment-kapsam-ciktilar-v2.docx
│
├── ARCHITECTURE_DECISIONS.md       # All architectural decisions with rationale
├── TASKS.md                        # Development backlog — 8 sprints, 164 tasks
└── README.md
```

---

## Development Roadmap

| Sprint | Goal | Tasks |
|---|---|---|
| **Sprint 0** | Foundation — all services running in K8s, healthchecks pass | 13 |
| **Sprint 1** | Single agent E2E — K8s Agent full interview cycle | 37 |
| **Sprint 2** | Knowledge Graph full integration — SHACL, reasoner, inference | 18 |
| **Sprint 3** | All 8 agents + full MCP tool set | 20 |
| **Sprint 4** | Orchestrator + cross-task analysis | 15 |
| **Sprint 5** | Guardrails full implementation | 22 |
| **Sprint 6** | Monitoring & observability | 21 |
| **Sprint 7** | Frontend UX polish + E2E tests | 18 |
| | **Total** | **164** |

Full task breakdown → [`TASKS.md`](TASKS.md)

---

## Tech Stack

| Category | Technology |
|---|---|
| Agents | LangGraph (Supervisor pattern), Claude API |
| Agent Protocol | MCP (Model Context Protocol) |
| API | FastAPI, WebSocket |
| Event Bus | Apache Kafka |
| Knowledge Graph | Apache Jena Fuseki, OWL, SPARQL, SHACL |
| Vector Store | Qdrant |
| Relational DB | PostgreSQL |
| Object Storage | MinIO (Apache Iceberg on top) |
| Query Engine | Trino |
| Data Catalog | OpenMetadata |
| Security | Keycloak (AuthN), OPA (AuthZ), Presidio (PII) |
| Monitoring | Prometheus, Grafana, Loki, Tempo |
| LLM Observability | LangFuse |
| Frontend | React, Vite, TypeScript, Tailwind |
| Deployment | Kubernetes, Helm, Kong Gateway |

---

## Local Development Setup

### Prerequisites

- Docker Desktop (Kubernetes enabled)
- `kubectl` and `helm` (bundled with Docker Desktop)
- 32 GB RAM recommended

### Enable Kubernetes in Docker Desktop

1. Docker Desktop → Settings → Kubernetes → Enable Kubernetes
2. Apply & Restart
3. Verify: `kubectl get nodes`

### Deploy Sprint 0 (Foundation)

```bash
# Create namespaces
kubectl apply -f infra/namespaces/

# Apply RBAC
kubectl apply -f infra/rbac/

# Deploy all services
helm install aakp-data infra/helm/data-layer/
helm install aakp-info infra/helm/information-layer/
helm install aakp-knowledge infra/helm/knowledge-layer/
helm install aakp-agent infra/helm/agent-layer/
helm install aakp-monitoring infra/helm/monitoring/

# Verify all pods healthy
kubectl get pods -A
```

---

## Documentation

| Document | Description |
|---|---|
| [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) | All architectural decisions with rationale |
| [`TASKS.md`](TASKS.md) | Development backlog — 8 sprints, 164 tasks |
| [`knowledge/ontology/`](knowledge/ontology/) | Domain ontology (OWL, v0.2+) |
| [`docs/`](docs/) | Source documents and reference materials |
