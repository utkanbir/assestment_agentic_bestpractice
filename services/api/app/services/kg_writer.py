"""
KG Writer — fires-and-forgets after every PG insert.

Each public function is designed to run as a FastAPI BackgroundTask:
  background_tasks.add_task(write_assessment, assessment.id, ...)

On Fuseki/Qdrant error: logs and returns; never raises (doesn't kill the response).
On success: updates kg_uri in PG using a fresh session (the request session
  is already closed by the time BackgroundTasks execute).
"""

import asyncio
import logging
import uuid

from app.core.database import AsyncSessionLocal
from app.services.sparql_client import sparql_client

logger = logging.getLogger(__name__)


def _qdrant_embed_finding(finding_id, description, severity, confidence, task_id):
    try:
        from app.services.qdrant_client import upsert_finding
        upsert_finding(finding_id, description, severity, confidence, task_id)
    except Exception as exc:
        logger.warning("Qdrant embed failed for finding %s: %s", finding_id, exc)


def _qdrant_embed_evidence(evidence_id, content, source, interview_id):
    try:
        from app.services.qdrant_client import upsert_evidence
        upsert_evidence(evidence_id, content, source, interview_id)
    except Exception as exc:
        logger.warning("Qdrant embed failed for evidence %s: %s", evidence_id, exc)


async def _store_kg_uri(table: str, row_id: uuid.UUID, uri: str) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            __import__("sqlalchemy", fromlist=["text"]).text(
                f"UPDATE {table} SET kg_uri = :uri WHERE id = :id"
            ),
            {"uri": uri, "id": str(row_id)},
        )
        await session.commit()


async def write_assessment(assessment_id: uuid.UUID,
                            client_name: str, project_name: str) -> None:
    try:
        uri = await sparql_client.insert_assessment(assessment_id, client_name, project_name)
        await _store_kg_uri("assessments", assessment_id, uri)
    except Exception as exc:
        logger.warning("KG write failed for assessment %s: %s", assessment_id, exc)


async def write_task(task_id: uuid.UUID, assessment_id: uuid.UUID,
                      agent_type: str, workstream: str,
                      scope: str | None = None) -> None:
    try:
        uri = await sparql_client.insert_task(task_id, assessment_id, agent_type, workstream, scope)
        await _store_kg_uri("tasks", task_id, uri)
    except Exception as exc:
        logger.warning("KG write failed for task %s: %s", task_id, exc)


async def write_interview(interview_id: uuid.UUID, task_id: uuid.UUID,
                           interviewee_name: str,
                           interviewee_role: str | None = None) -> None:
    try:
        uri = await sparql_client.insert_interview(
            interview_id, task_id, interviewee_name, interviewee_role
        )
        await _store_kg_uri("interviews", interview_id, uri)
    except Exception as exc:
        logger.warning("KG write failed for interview %s: %s", interview_id, exc)


async def write_evidence(evidence_id: uuid.UUID, interview_id: uuid.UUID | None,
                          source: str, content: str) -> None:
    try:
        uri = await sparql_client.insert_evidence(evidence_id, interview_id, source, content)
        await _store_kg_uri("evidences", evidence_id, uri)
    except Exception as exc:
        logger.warning("KG write failed for evidence %s: %s", evidence_id, exc)
    # S2-BA-003: embed evidence into Qdrant (sync, run in executor)
    await asyncio.get_event_loop().run_in_executor(
        None, _qdrant_embed_evidence, evidence_id, content, source, interview_id
    )


async def write_finding(finding_id: uuid.UUID, task_id: uuid.UUID,
                         evidence_id: uuid.UUID, description: str,
                         severity: str, confidence: float) -> None:
    try:
        uri = await sparql_client.insert_finding(
            finding_id, task_id, evidence_id, description, severity, confidence
        )
        await _store_kg_uri("findings", finding_id, uri)
    except Exception as exc:
        logger.warning("KG write failed for finding %s: %s", finding_id, exc)
    # S2-BA-002: embed finding description into Qdrant (sync, run in executor)
    await asyncio.get_event_loop().run_in_executor(
        None, _qdrant_embed_finding, finding_id, description, severity, confidence, task_id
    )


async def write_risk(risk_id: uuid.UUID, finding_id: uuid.UUID,
                      title: str, description: str,
                      severity: str, impact: str) -> None:
    try:
        uri = await sparql_client.insert_risk(
            risk_id, finding_id, title, description, severity, impact
        )
        await _store_kg_uri("risks", risk_id, uri)
    except Exception as exc:
        logger.warning("KG write failed for risk %s: %s", risk_id, exc)
