import asyncio
import logging
from contextlib import asynccontextmanager

from app.core.logging_config import configure_logging
configure_logging()  # S6-BA-007: JSON structured logging from process start

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.metrics import metrics_app  # S6-BA-001
from app.routers import assessments, health, interviews, knowledge, qdrant, question_bank, recommendations, reports, risks, tasks, ws
from app.routers.findings import evidence_router, finding_router
from app.routers import orchestrator, approvals, agent_mgmt
from app.middleware.guardrails import PIIGuardrailMiddleware
from app.middleware.tracing import setup_tracing  # S6-BA-006

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure Qdrant collections exist (idempotent)
    try:
        from app.services.qdrant_client import ensure_collections
        await asyncio.get_event_loop().run_in_executor(None, ensure_collections)
    except Exception as exc:
        logger.warning("Qdrant collection bootstrap failed (non-fatal): %s", exc)

    # Register assessment agents in Fuseki knowledge graph (S3-AA-008, idempotent)
    try:
        from app.services.sparql_client import sparql_client
        result = await sparql_client.register_all_agents()
        logger.info("Agent registry: %s", result.get("status"))
    except Exception as exc:
        logger.warning("Agent registry bootstrap failed (non-fatal): %s", exc)

    # Register AssessmentFinding custom entity type in OpenMetadata (S3-BA-002, idempotent)
    try:
        from app.services.openmetadata_client import ensure_custom_type
        await ensure_custom_type()
        logger.info("OpenMetadata custom type registration attempted")
    except Exception as exc:
        logger.warning("OpenMetadata bootstrap failed (non-fatal): %s", exc)

    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

setup_tracing(app)  # S6-BA-006: OpenTelemetry distributed tracing
app.mount("/metrics", metrics_app)  # S6-BA-001: Prometheus metrics endpoint

app.add_middleware(PIIGuardrailMiddleware)  # S5-BA-001: PII input guardrail
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(assessments.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(interviews.router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(finding_router, prefix="/api/v1")
app.include_router(risks.router, prefix="/api/v1")
app.include_router(question_bank.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(qdrant.router, prefix="/api/v1")
app.include_router(ws.router)
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(orchestrator.router, prefix="/api/v1")
app.include_router(approvals.router, prefix="/api/v1")
app.include_router(agent_mgmt.router, prefix="/api/v1")
