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
from app.core.metrics import kg_writes_total  # S6-BA-001

logger = logging.getLogger(__name__)


async def _record_bg_touch(
    operation: str,
    layer: str,
    technology: str,
    action: str,
    *,
    assessment_id: uuid.UUID | None = None,
    interview_id: uuid.UUID | None = None,
    detail: dict | None = None,
) -> None:
    try:
        from app.services.layer_touch import record_touch
        async with AsyncSessionLocal() as session:
            await record_touch(
                session, layer, technology, action,
                operation=operation,
                assessment_id=assessment_id,
                interview_id=interview_id,
                detail=detail,
                broadcast=bool(interview_id),
            )
            await session.commit()
    except Exception as exc:
        logger.debug("Layer touch record failed: %s", exc)


async def _assessment_id_for_task(task_id: uuid.UUID) -> uuid.UUID | None:
    from app.models.assessment import Task
    async with AsyncSessionLocal() as session:
        task = await session.get(Task, task_id)
        return task.assessment_id if task else None


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
                            client_name: str, project_name: str,
                            is_simulated: bool = False) -> None:
    try:
        uri = await sparql_client.insert_assessment(
            assessment_id, client_name, project_name, is_simulated=is_simulated,
        )
        await _store_kg_uri("assessments", assessment_id, uri)
        kg_writes_total.labels(entity_type="assessment").inc()
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


async def write_question(question_id: uuid.UUID, interview_id: uuid.UUID, text: str, order: int = 0) -> None:
    try:
        uri = await sparql_client.insert_question(question_id, interview_id, text, order)
        # questions table does not currently include kg_uri field; emit instrumentation only.
        await _record_bg_touch(
            "write_question", "knowledge", "fuseki", "write",
            interview_id=interview_id,
            detail={"entity": "question", "question_id": str(question_id), "kg_uri": uri},
        )
    except Exception as exc:
        logger.warning("KG write failed for question %s: %s", question_id, exc)


async def write_answer(
    answer_id: uuid.UUID,
    question_id: uuid.UUID,
    text: str,
    interview_id: uuid.UUID | None = None,
    consultant_comment: str | None = None,
) -> None:
    try:
        uri = await sparql_client.insert_answer(
            answer_id, question_id, text, consultant_comment=consultant_comment,
        )
        await _record_bg_touch(
            "write_answer", "knowledge", "fuseki", "write",
            interview_id=interview_id,
            detail={"entity": "answer", "answer_id": str(answer_id), "kg_uri": uri},
        )
    except Exception as exc:
        logger.warning("KG write failed for answer %s: %s", answer_id, exc)


async def write_consultant_assignment(
    assessment_id: uuid.UUID,
    consultant_id: uuid.UUID,
    first_name: str,
    last_name: str,
    role: str | None = None,
    expertise: list[str] | str | None = None,
) -> None:
    if isinstance(expertise, list):
        expertise_str = ", ".join(expertise) if expertise else None
    else:
        expertise_str = expertise
    try:
        uri = await sparql_client.insert_consultant(
            consultant_id, assessment_id, first_name, last_name, role, expertise_str,
        )
        await _record_bg_touch(
            "write_consultant", "knowledge", "fuseki", "write",
            assessment_id=assessment_id,
            detail={"entity": "consultant", "consultant_id": str(consultant_id), "kg_uri": uri},
        )
    except Exception as exc:
        logger.warning("KG write failed for consultant %s: %s", consultant_id, exc)


async def write_consultant_on_answer(
    answer_id: uuid.UUID,
    question_id: uuid.UUID,
    consultant_id: uuid.UUID,
    first_name: str,
    last_name: str,
    consultant_comment: str | None,
    assessment_id: uuid.UUID,
) -> None:
    try:
        await sparql_client.link_consultant_to_answer(answer_id, consultant_id, consultant_comment)
        await _record_bg_touch(
            "write_consultant", "knowledge", "fuseki", "write",
            assessment_id=assessment_id,
            detail={"entity": "consultant_answer", "answer_id": str(answer_id), "consultant_id": str(consultant_id)},
        )
    except Exception as exc:
        logger.warning("KG consultant link failed for answer %s: %s", answer_id, exc)


async def write_evaluation(
    evaluation_id: uuid.UUID,
    answer_id: uuid.UUID,
    text: str,
    interview_id: uuid.UUID | None = None,
    assessment_id: uuid.UUID | None = None,
    upsert: bool = False,
) -> None:
    try:
        if upsert:
            uri = await sparql_client.upsert_answer_evaluation(answer_id, text)
        else:
            uri = await sparql_client.insert_evaluation(evaluation_id, answer_id, text)
        await _record_bg_touch(
            "write_evaluation", "knowledge", "fuseki", "write",
            interview_id=interview_id,
            assessment_id=assessment_id,
            detail={"entity": "evaluation", "answer_id": str(answer_id), "kg_uri": uri},
        )
    except Exception as exc:
        logger.warning("KG write failed for evaluation answer %s: %s", answer_id, exc)


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
    assessment_id = await _assessment_id_for_task(task_id)
    try:
        uri = await sparql_client.insert_finding(
            finding_id, task_id, evidence_id, description, severity, confidence
        )
        await _store_kg_uri("findings", finding_id, uri)
        await _record_bg_touch(
            "write_finding", "knowledge", "fuseki", "write",
            assessment_id=assessment_id,
            detail={"entity": "finding", "finding_id": str(finding_id)},
        )
        await _record_bg_touch(
            "write_finding", "knowledge", "sparql", "write",
            assessment_id=assessment_id,
            detail={"graph": "assessment"},
        )
    except Exception as exc:
        logger.warning("KG write failed for finding %s: %s", finding_id, exc)
        return

    # S5-KA-002: SHACL validation after KG write (non-blocking, logs violations)
    try:
        report = await sparql_client.validate_shacl(
            graph_uri="https://aakp.ai/graph/assessment"
        )
        if not report.get("conforms"):
            logger.warning(
                "SHACL violation after finding write %s: %d violations",
                finding_id, report.get("violations_count", 0)
            )
            await _audit_kg_event("shacl_violation", str(finding_id), {
                "violations": report.get("violations", [])[:5],
                "graph": "assessment",
            })
            await _record_bg_touch(
                "write_finding", "knowledge", "shacl", "validate",
                assessment_id=assessment_id,
                detail={"conforms": False, "violations": report.get("violations_count", 0)},
            )
        else:
            await _record_bg_touch(
                "write_finding", "knowledge", "shacl", "validate",
                assessment_id=assessment_id,
                detail={"conforms": True},
            )
    except Exception as exc:
        logger.debug("SHACL validation skipped (Fuseki unavailable): %s", exc)

    await _record_bg_touch(
        "write_finding", "information", "postgresql", "write",
        assessment_id=assessment_id,
        detail={"table": "findings", "field": "kg_uri"},
    )

    # S2-BA-002: embed finding description into Qdrant (sync, run in executor)
    await asyncio.get_event_loop().run_in_executor(
        None, _qdrant_embed_finding, finding_id, description, severity, confidence, task_id
    )
    await _record_bg_touch(
        "write_finding", "information", "qdrant", "embed",
        assessment_id=assessment_id,
        detail={"entity": "finding", "finding_id": str(finding_id)},
    )


async def _audit_kg_event(event_type: str, entity_id: str, detail: dict) -> None:
    """S5-SA-010: Log every KG mutation to the audit log service (non-fatal)."""
    try:
        import httpx
        from app.core.config import settings
        await httpx.AsyncClient().post(
            f"{settings.audit_log_url}/events",
            json={"event_type": event_type, "entity_id": entity_id, "detail": detail},
            timeout=5,
        )
    except Exception:
        pass


async def write_risk(risk_id: uuid.UUID, finding_id: uuid.UUID,
                      title: str, description: str,
                      severity: str, impact: str) -> None:
    try:
        uri = await sparql_client.insert_risk(
            risk_id, finding_id, title, description, severity, impact
        )
        await _store_kg_uri("risks", risk_id, uri)
        # S5-SA-010: audit KG write
        await _audit_kg_event("kg_write", str(risk_id), {
            "graph": "maturity", "entity_type": "Risk",
            "finding_id": str(finding_id), "severity": severity,
        })
    except Exception as exc:
        logger.warning("KG write failed for risk %s: %s", risk_id, exc)


async def write_training_interaction(
    event_id: uuid.UUID,
    workstream: str,
    mode: str,
    question_text: str,
    answer_text: str,
    answer_author: str = "consultant",
) -> None:
    try:
        uri = await sparql_client.insert_training_interaction(
            event_id, workstream, mode, question_text, answer_text, answer_author,
        )
        await _record_bg_touch(
            "write_training", "knowledge", "fuseki", "write",
            detail={"entity": "training", "event_id": str(event_id), "kg_uri": uri},
        )
    except Exception as exc:
        logger.warning("KG write failed for training %s: %s", event_id, exc)
        return
    await enrich_training_concepts(
        event_id, workstream, question_text, answer_text, knowledge_kind="training",
    )


async def enrich_training_concepts(
    event_id: uuid.UUID,
    workstream: str,
    question_text: str,
    answer_text: str,
    *,
    knowledge_kind: str = "training",
) -> None:
    """Link TrainingInteraction/AgentKnowledge to domain concepts (refersToConcept)."""
    try:
        from app.services.training_concepts import (
            list_concepts_for_workstream,
            resolve_concepts_for_training,
        )
        from app.services.llm_client import suggest_training_concept_ids

        candidates = list_concepts_for_workstream(workstream)
        loop = asyncio.get_event_loop()
        llm_ids = await loop.run_in_executor(
            None,
            lambda: suggest_training_concept_ids(
                workstream, question_text, answer_text, candidates,
            ),
        )
        concept_uris = resolve_concepts_for_training(
            workstream, question_text, answer_text, llm_ids,
        )
        if not concept_uris:
            return
        await sparql_client.insert_training_concept_links(
            event_id, concept_uris, knowledge_kind=knowledge_kind,
        )
        await _record_bg_touch(
            "enrich_training_concepts", "knowledge", "fuseki", "write",
            detail={
                "event_id": str(event_id),
                "concepts": concept_uris,
                "kind": knowledge_kind,
            },
        )
    except Exception as exc:
        logger.warning("Concept enrichment failed for %s: %s", event_id, exc)


async def write_agent_knowledge(
    event_id: uuid.UUID,
    workstream: str,
    content: str,
    *,
    knowledge_mode: str = "text",
    source_doc_id: uuid.UUID | None = None,
    source_filename: str | None = None,
) -> None:
    try:
        uri = await sparql_client.insert_agent_knowledge(
            event_id, workstream, content,
            knowledge_mode=knowledge_mode,
            source_doc_id=source_doc_id,
            source_filename=source_filename,
        )
        await _record_bg_touch(
            "write_agent_knowledge", "knowledge", "fuseki", "write",
            detail={"entity": "agent_knowledge", "event_id": str(event_id), "kg_uri": uri},
        )
    except Exception as exc:
        logger.warning("KG write failed for agent knowledge %s: %s", event_id, exc)
        return
    await enrich_training_concepts(
        event_id, workstream, "", content, knowledge_kind="knowledge",
    )


async def write_document_knowledge(
    event_id: uuid.UUID,
    workstream: str,
    doc_id: uuid.UUID,
    filename: str,
    description: str,
) -> None:
    await write_agent_knowledge(
        event_id, workstream, description or filename,
        knowledge_mode="document",
        source_doc_id=doc_id,
        source_filename=filename,
    )


async def delete_learning_event(event_id: uuid.UUID) -> None:
    try:
        await sparql_client.delete_learning_by_pg_id(event_id)
        await _record_bg_touch(
            "delete_learning", "knowledge", "fuseki", "delete",
            detail={"entity": "learning_event", "event_id": str(event_id)},
        )
    except Exception as exc:
        logger.warning("KG delete failed for learning event %s: %s", event_id, exc)
    try:
        from app.services.qdrant_client import delete_training_chunks
        await asyncio.get_event_loop().run_in_executor(
            None, delete_training_chunks, str(event_id),
        )
    except Exception as exc:
        logger.warning("Qdrant delete failed for training %s: %s", event_id, exc)
