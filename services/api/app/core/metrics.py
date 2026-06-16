# S6-BA-001..005: Custom Prometheus metrics for AAKP API
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

# S6-BA-002: Evidence coverage per assessment (ratio findings with evidence)
evidence_coverage_score = Gauge(
    "aakp_evidence_coverage_score",
    "Ratio of findings with at least one evidence (per assessment)",
    ["assessment_id"],
)

# S6-BA-003: Recommendations without evidence — 0 tolerance metric
recommendation_without_evidence_total = Counter(
    "aakp_recommendation_without_evidence_total",
    "Number of recommendations created without linked evidence (should always be 0)",
    ["assessment_id", "severity"],
)

# S6-BA-004: Guardrail violations by category
guardrail_violations_total = Counter(
    "aakp_guardrail_violations_total",
    "PII / policy guardrail violations detected",
    ["violation_type", "entity_type", "path"],
)

# S6-BA-005: Average agent confidence score per workstream
agent_confidence_avg = Gauge(
    "aakp_agent_confidence_avg",
    "Rolling average confidence score of findings per agent workstream",
    ["workstream"],
)

# General request duration (complementary to OpenTelemetry tracing)
api_request_duration_seconds = Histogram(
    "aakp_api_request_duration_seconds",
    "FastAPI endpoint latency",
    ["method", "path", "status_code"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# LLM call tracking
llm_calls_total = Counter(
    "aakp_llm_calls_total",
    "Total LLM invocations per agent and model",
    ["agent", "model"],
)

llm_tokens_total = Counter(
    "aakp_llm_tokens_total",
    "Total LLM tokens consumed",
    ["agent", "model", "direction"],  # direction: input | output
)

# KG write events
kg_writes_total = Counter(
    "aakp_kg_writes_total",
    "Successful knowledge graph write operations",
    ["entity_type"],
)

# Expose /metrics endpoint as ASGI app (mounted in main.py)
metrics_app = make_asgi_app()
