# Agentic Assessment Knowledge Platform (AAKP)

Enterprise-grade platform enabling consulting teams to conduct structured assessments using AI agents, knowledge management, ontology-driven reasoning, and governed enterprise knowledge.

## Architecture

4-layer knowledge management architecture:

```
Agent Layer        → LangGraph, 8 assessment agents, orchestrator, guardrails
Knowledge Layer    → Apache Jena Fuseki, OWL/RDF, SPARQL, SHACL, Reasoning
Information Layer  → PostgreSQL, Qdrant, Kafka, FastAPI, MCP Server, OpenMetadata
Data Layer         → MinIO, Apache Iceberg, Trino, Kafka
```

## Key Principles

- Knowledge-centric (not data-centric) — agents reason through ontology
- Evidence mandatory — no finding without evidence (0 tolerance)
- Human in the loop — all knowledge changes require human approval
- Open source, container-native, Kubernetes-ready
- Vendor independent

## Documentation

- [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) — all architectural decisions and rationale
- [`TASKS.md`](TASKS.md) — development backlog (8 sprints, 164 tasks)
- [`Assessment Domain Ontology v0.2.md`](Assessment%20Domain%20Ontology%20v0.2.md) — domain ontology

## Assessment Scope

8 workstreams, each with a dedicated AI agent:

| Agent | Workstream |
|---|---|
| Kubernetes Agent | Business Continuity & K8s Resilience |
| Cloud Strategy Agent | Cloud Transformation (GCP) |
| Ingestion Agent | Data Ingestion & ETL |
| Teradata DR Agent | Teradata EDW DR & Cloud Options |
| Lakehouse Agent | Lakehouse Architecture |
| Governance Agent | Data Governance |
| Data Product Agent | Data Product Approach |
| CDP Agent | CDP & Customer 360 |

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| API | FastAPI, MCP Server, WebSocket, Kafka |
| Agents | LangGraph (Supervisor pattern) |
| Knowledge | Apache Jena Fuseki, OWL, SPARQL, SHACL |
| Storage | PostgreSQL, MinIO, Qdrant, Redis |
| Data | Apache Iceberg, Trino |
| Catalog | OpenMetadata |
| Security | Keycloak, OPA, Presidio |
| Monitoring | LangFuse, Prometheus, Grafana, Loki, Tempo |
| Deployment | Kubernetes, Helm, Kong Gateway |
