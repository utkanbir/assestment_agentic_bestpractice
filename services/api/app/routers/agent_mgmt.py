"""Agent management — performance metrics + knowledge document upload (S11)."""
import asyncio
import io
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.agent_learning import AgentLearningEvent
from app.models.assessment import Answer, Interview, Question, Task
from app.models.knowledge import KnowledgeDocument
from app.services import layer_touch as layer_touch_svc

router = APIRouter(prefix="/agents", tags=["agent-management"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class AgentMetrics(BaseModel):
    workstream: str
    interviews_conducted: int
    questions_total: int
    questions_agent_suggested: int
    suggestions_approved: int
    suggestions_rejected: int
    suggestions_pending: int
    answers_total: int
    answers_evaluated: int
    documents_loaded: int


class KnowledgeDocumentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workstream: str
    filename: str
    file_type: str
    chunk_count: int
    description: str | None
    created_at: datetime


class LearningHistoryItem(BaseModel):
    answer_id: uuid.UUID
    question_text: str
    answer_text: str
    evaluation: str
    created_at: datetime


class AahaQuestionOut(BaseModel):
    question: str


class AahaAnswerIn(BaseModel):
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    consultant_id: uuid.UUID | None = None
    answer_author: str = Field(default="consultant")
    approved_by_consultant_id: uuid.UUID | None = None


class AahaAiAnswerIn(BaseModel):
    question: str = Field(min_length=1)


class AahaAiAnswerOut(BaseModel):
    answer: str


class TextTrainIn(BaseModel):
    content: str = Field(min_length=1)
    consultant_id: uuid.UUID | None = None


class LearningEventOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workstream: str
    mode: str
    question_text: str | None
    answer_text: str | None
    source_doc_id: uuid.UUID | None
    consultant_id: uuid.UUID | None = None
    answer_author: str = "consultant"
    approved_by_consultant_id: uuid.UUID | None = None
    created_at: datetime


class DocumentUploadOut(BaseModel):
    id: uuid.UUID
    workstream: str
    filename: str
    file_type: str
    chunk_count: int
    description: str | None
    created_at: datetime
    learning_summary: dict


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    mode: str | None = None
    answer_author: str | None = None
    created_at: datetime | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str


class AgentGraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class KnowledgeSummaryStats(BaseModel):
    total_events: int
    aaha_count: int
    aaha_ai_count: int
    aaha_consultant_count: int
    text_count: int
    document_count: int
    chunk_estimate: int
    knowledge_pieces: int


class KnowledgeSummaryEvent(BaseModel):
    id: uuid.UUID
    label: str
    mode: str
    author_display: str
    created_at: datetime


class AgentKnowledgeSummaryOut(BaseModel):
    workstream: str
    stats: KnowledgeSummaryStats
    recent_events: list[KnowledgeSummaryEvent]
    graph: AgentGraphOut
    ontology_classes: list[dict]


_VALID_WORKSTREAMS = {
    "kubernetes", "cloud_strategy", "ingestion", "teradata_dr",
    "lakehouse", "governance", "data_product", "cdp",
}


def _check_workstream(workstream: str) -> None:
    if workstream not in _VALID_WORKSTREAMS:
        raise HTTPException(status_code=404, detail="Unknown workstream")


def _resolve_aaha_author(body: AahaAnswerIn) -> tuple[str, uuid.UUID | None, uuid.UUID | None]:
    author = body.answer_author if body.answer_author in ("consultant", "ai") else "consultant"
    if author == "ai":
        return author, None, body.approved_by_consultant_id
    return author, body.consultant_id, None


async def _build_agent_graph(workstream: str, db: AsyncSession) -> AgentGraphOut:
    agent_id = f"agent:{workstream}"
    nodes: list[GraphNode] = [
        GraphNode(id=agent_id, label=workstream.replace("_", " ").title(), type="agent"),
        GraphNode(id="cls:TrainingInteraction", label="TrainingInteraction", type="ontology"),
        GraphNode(id="cls:AgentKnowledge", label="AgentKnowledge", type="ontology"),
    ]
    edges: list[GraphEdge] = []

    docs_res = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.workstream == workstream)
        .order_by(KnowledgeDocument.created_at.desc())
        .limit(20)
    )
    for doc in docs_res.scalars().all():
        nid = f"doc:{doc.id}"
        nodes.append(GraphNode(id=nid, label=doc.filename, type="document", created_at=doc.created_at))
        edges.append(GraphEdge(source=agent_id, target=nid, label="hasDocument"))

    events_res = await db.execute(
        select(AgentLearningEvent)
        .where(AgentLearningEvent.workstream == workstream)
        .order_by(AgentLearningEvent.created_at.desc())
        .limit(30)
    )
    for ev in events_res.scalars().all():
        nid = f"event:{ev.id}"
        label = (ev.question_text or ev.answer_text or ev.mode)[:40]
        node_type = "learning_event_ai" if ev.answer_author == "ai" else "learning_event"
        nodes.append(GraphNode(
            id=nid,
            label=label,
            type=node_type,
            mode=ev.mode,
            answer_author=ev.answer_author,
            created_at=ev.created_at,
        ))
        edges.append(GraphEdge(source=agent_id, target=nid, label="hasTrainingEvent"))
        cls = "cls:TrainingInteraction" if ev.mode == "aaha" else "cls:AgentKnowledge"
        edges.append(GraphEdge(source=nid, target=cls, label="rdf:type"))

    return AgentGraphOut(nodes=nodes, edges=edges)


def _author_display_for_event(
    ev: AgentLearningEvent,
    consultants: dict[uuid.UUID, str],
) -> str:
    if ev.answer_author == "ai":
        return "AI"
    if ev.consultant_id and ev.consultant_id in consultants:
        return consultants[ev.consultant_id]
    return "—"


async def _compute_knowledge_summary(workstream: str, db: AsyncSession) -> AgentKnowledgeSummaryOut:
    from app.models.consultant import Consultant

    events_res = await db.execute(
        select(AgentLearningEvent)
        .where(AgentLearningEvent.workstream == workstream)
        .order_by(AgentLearningEvent.created_at.desc())
    )
    events = list(events_res.scalars().all())

    docs_res = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.workstream == workstream)
    )
    docs = list(docs_res.scalars().all())
    chunk_estimate = sum(d.chunk_count for d in docs)

    consultant_ids = {
        e.consultant_id for e in events if e.consultant_id
    } | {
        e.approved_by_consultant_id for e in events if e.approved_by_consultant_id
    }
    consultant_map: dict[uuid.UUID, str] = {}
    if consultant_ids:
        c_res = await db.execute(select(Consultant).where(Consultant.id.in_(consultant_ids)))
        for c in c_res.scalars().all():
            consultant_map[c.id] = f"{c.first_name} {c.last_name}".strip()

    aaha = [e for e in events if e.mode == "aaha"]
    stats = KnowledgeSummaryStats(
        total_events=len(events),
        aaha_count=len(aaha),
        aaha_ai_count=sum(1 for e in aaha if e.answer_author == "ai"),
        aaha_consultant_count=sum(1 for e in aaha if e.answer_author != "ai"),
        text_count=sum(1 for e in events if e.mode == "text"),
        document_count=len(docs),
        chunk_estimate=chunk_estimate,
        knowledge_pieces=len(events) + chunk_estimate,
    )

    recent_events = [
        KnowledgeSummaryEvent(
            id=ev.id,
            label=(ev.question_text or ev.answer_text or ev.mode or "")[:60],
            mode=ev.mode,
            author_display=_author_display_for_event(ev, consultant_map),
            created_at=ev.created_at,
        )
        for ev in events[:5]
    ]

    graph = await _build_agent_graph(workstream, db)

    ontology_classes = [
        {"id": "cls:TrainingInteraction", "label": "TrainingInteraction", "comment": "AAHA soru-yanıt eğitimi"},
        {"id": "cls:AgentKnowledge", "label": "AgentKnowledge", "comment": "Metin ve döküman bilgisi"},
    ]

    return AgentKnowledgeSummaryOut(
        workstream=workstream,
        stats=stats,
        recent_events=recent_events,
        graph=graph,
        ontology_classes=ontology_classes,
    )


# ── Metrics ───────────────────────────────────────────────────────────────────

@router.get("/metrics", response_model=list[AgentMetrics])
async def get_all_metrics(db: AsyncSession = Depends(get_db)):
    """Aggregate performance metrics per workstream."""
    workstreams = [
        "kubernetes", "cloud_strategy", "ingestion", "teradata_dr",
        "lakehouse", "governance", "data_product", "cdp",
    ]
    metrics = []
    for ws in workstreams:
        m = await _compute_metrics(ws, db)
        metrics.append(m)
    return metrics


@router.get("/metrics/{workstream}", response_model=AgentMetrics)
async def get_workstream_metrics(workstream: str, db: AsyncSession = Depends(get_db)):
    return await _compute_metrics(workstream, db)


class KgStatsTotals(BaseModel):
    individuals: int = 0
    triples_total: int = 0
    triples_assessment_graph: int = 0
    triples_agents_graph: int = 0
    assessments: int = 0
    tasks: int = 0
    interviews: int = 0
    questions: int = 0
    answers: int = 0
    evaluations: int = 0
    findings: int = 0
    consultants: int = 0
    evidence: int = 0
    assessment_agents: int = 0
    training_interactions: int = 0
    agent_knowledge: int = 0
    concept_links: int = 0
    learning_pieces: int = 0
    ontology_classes: int = 0


class KgStatsPostgres(BaseModel):
    learning_events: int = 0
    aaha_count: int = 0
    text_count: int = 0
    document_count: int = 0
    answers: int = 0
    questions: int = 0
    evaluations: int = 0


class KgStatsWorkstream(BaseModel):
    workstream: str
    answer_count: int = 0
    question_count: int = 0
    training_count: int = 0
    knowledge_count: int = 0
    total_pieces: int = 0


class AgentKgStatsOut(BaseModel):
    source: str
    collected_at: str
    totals: KgStatsTotals
    postgres: KgStatsPostgres
    by_workstream: list[KgStatsWorkstream]


@router.get("/kg-stats", response_model=AgentKgStatsOut)
async def get_agent_kg_stats(db: AsyncSession = Depends(get_db)):
    """Platform-wide Knowledge Graph counters (Fuseki + PostgreSQL)."""
    from app.services.agent_kg_stats import fetch_kg_stats

    raw = await fetch_kg_stats(db)
    return AgentKgStatsOut(**raw)


@router.get("/kg-protege-export.ttl", response_class=PlainTextResponse)
async def export_full_kg_protege_ttl():
    """Full TBox + all 8 agents + all KM instances for Protege."""
    from app.services.protege_export import build_full_kg_protege_bundle

    body, _ = await build_full_kg_protege_bundle()
    return PlainTextResponse(
        content=body,
        media_type="text/turtle",
        headers={"Content-Disposition": 'attachment; filename="aakp-agent-kg-full.ttl"'},
    )


async def _compute_metrics(workstream: str, db: AsyncSession) -> AgentMetrics:
    # Tasks → interviews → questions → answers chain
    tasks_q = select(Task.id).where(Task.workstream == workstream)
    tasks_res = await db.execute(tasks_q)
    task_ids = [r[0] for r in tasks_res.all()]

    if not task_ids:
        return AgentMetrics(
            workstream=workstream, interviews_conducted=0, questions_total=0,
            questions_agent_suggested=0, suggestions_approved=0, suggestions_rejected=0,
            suggestions_pending=0, answers_total=0, answers_evaluated=0, documents_loaded=0,
        )

    interviews_res = await db.execute(
        select(func.count(Interview.id)).where(Interview.task_id.in_(task_ids))
    )
    interviews_count = interviews_res.scalar() or 0

    interview_ids_res = await db.execute(
        select(Interview.id).where(Interview.task_id.in_(task_ids))
    )
    interview_ids = [r[0] for r in interview_ids_res.all()]

    if not interview_ids:
        docs_res = await db.execute(
            select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.workstream == workstream)
        )
        return AgentMetrics(
            workstream=workstream, interviews_conducted=interviews_count, questions_total=0,
            questions_agent_suggested=0, suggestions_approved=0, suggestions_rejected=0,
            suggestions_pending=0, answers_total=0, answers_evaluated=0,
            documents_loaded=docs_res.scalar() or 0,
        )

    q_total = (await db.execute(
        select(func.count(Question.id)).where(Question.interview_id.in_(interview_ids))
    )).scalar() or 0

    q_suggested = (await db.execute(
        select(func.count(Question.id))
        .where(Question.interview_id.in_(interview_ids))
        .where(Question.agent_suggested == True)
    )).scalar() or 0

    q_approved = (await db.execute(
        select(func.count(Question.id))
        .where(Question.interview_id.in_(interview_ids))
        .where(Question.agent_suggested == True)
        .where(Question.approval_status == "approved")
    )).scalar() or 0

    q_rejected = (await db.execute(
        select(func.count(Question.id))
        .where(Question.interview_id.in_(interview_ids))
        .where(Question.agent_suggested == True)
        .where(Question.approval_status == "rejected")
    )).scalar() or 0

    q_pending = (await db.execute(
        select(func.count(Question.id))
        .where(Question.interview_id.in_(interview_ids))
        .where(Question.agent_suggested == True)
        .where(Question.approval_status == "pending")
    )).scalar() or 0

    question_ids_res = await db.execute(
        select(Question.id).where(Question.interview_id.in_(interview_ids))
    )
    question_ids = [r[0] for r in question_ids_res.all()]

    answers_total = 0
    answers_evaluated = 0
    if question_ids:
        answers_total = (await db.execute(
            select(func.count(Answer.id)).where(Answer.question_id.in_(question_ids))
        )).scalar() or 0

        answers_evaluated = (await db.execute(
            select(func.count(Answer.id))
            .where(Answer.question_id.in_(question_ids))
            .where(Answer.evaluation.isnot(None))
        )).scalar() or 0

    docs_count = (await db.execute(
        select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.workstream == workstream)
    )).scalar() or 0

    return AgentMetrics(
        workstream=workstream,
        interviews_conducted=interviews_count,
        questions_total=q_total,
        questions_agent_suggested=q_suggested,
        suggestions_approved=q_approved,
        suggestions_rejected=q_rejected,
        suggestions_pending=q_pending,
        answers_total=answers_total,
        answers_evaluated=answers_evaluated,
        documents_loaded=docs_count,
    )


# ── Learning History ──────────────────────────────────────────────────────────

@router.get("/{workstream}/learning-history", response_model=list[LearningHistoryItem])
async def get_learning_history(workstream: str, db: AsyncSession = Depends(get_db)):
    """Return past answer evaluations for the workstream (most recent first)."""
    result = await db.execute(
        select(
            Answer.id,
            Question.text,
            Answer.text,
            Answer.evaluation,
            Answer.created_at,
        )
        .join(Question, Answer.question_id == Question.id)
        .join(Interview, Question.interview_id == Interview.id)
        .join(Task, Interview.task_id == Task.id)
        .where(Task.workstream == workstream)
        .where(Answer.evaluation.isnot(None))
        .order_by(Answer.created_at.desc())
        .limit(50)
    )
    return [
        LearningHistoryItem(
            answer_id=row[0],
            question_text=row[1],
            answer_text=row[2],
            evaluation=row[3],
            created_at=row[4],
        )
        for row in result.all()
    ]


# ── Knowledge Documents (RAG) ─────────────────────────────────────────────────

@router.get("/{workstream}/documents", response_model=list[KnowledgeDocumentOut])
async def list_documents(workstream: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.workstream == workstream)
        .order_by(KnowledgeDocument.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{workstream}/training-events", response_model=list[LearningEventOut])
async def list_training_events(workstream: str, db: AsyncSession = Depends(get_db)):
    _check_workstream(workstream)
    result = await db.execute(
        select(AgentLearningEvent)
        .where(AgentLearningEvent.workstream == workstream)
        .order_by(AgentLearningEvent.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.post("/{workstream}/documents", response_model=DocumentUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workstream: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF or text document to the agent's knowledge base."""
    content_bytes = await file.read()
    filename = file.filename or "document"
    file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

    # Extract text
    text_content = _extract_text(content_bytes, file_type, filename)

    # Chunk and embed into Qdrant
    chunks = _chunk_text(text_content)
    doc_id = uuid.uuid4()
    try:
        from app.services.qdrant_client import upsert_document_chunks
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: upsert_document_chunks(str(doc_id), workstream, filename, chunks),
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Qdrant upsert failed (non-fatal): %s", exc)

    doc = KnowledgeDocument(
        id=doc_id,
        workstream=workstream,
        filename=filename,
        file_type=file_type,
        content=text_content[:50_000],  # store up to 50k chars
        chunk_count=len(chunks),
        description=description,
    )
    db.add(doc)
    await db.flush()

    learning_event = AgentLearningEvent(
        id=uuid.uuid4(),
        workstream=workstream,
        mode="document",
        answer_text=description or filename,
        source_doc_id=doc_id,
    )
    db.add(learning_event)
    await db.commit()
    await db.refresh(doc)

    from app.services.kg_writer import write_document_knowledge
    background_tasks.add_task(
        write_document_knowledge,
        learning_event.id, workstream, doc_id, filename, description or filename,
    )
    layer_touch_svc.begin_operation(f"upload_doc_{workstream}", source="api")
    await layer_touch_svc.record_touch(
        db, "knowledge", "fuseki", "write",
        operation=f"upload_doc_{workstream}",
        detail={"event_id": str(learning_event.id), "mode": "document"},
    )
    await layer_touch_svc.record_touch(
        db, "information", "qdrant", "embed",
        operation=f"upload_doc_{workstream}",
        detail={"doc_id": str(doc_id), "chunks": len(chunks)},
    )
    await db.commit()

    preview = " ".join(text_content[:200].split())
    learning_summary = {
        "event_id": str(learning_event.id),
        "mode": "document",
        "workstream": workstream,
        "chunks": len(chunks),
        "characters": len(text_content),
        "filename": filename,
        "preview": preview,
        "qdrant_embedded": len(chunks) > 0,
    }

    return DocumentUploadOut(
        id=doc.id,
        workstream=doc.workstream,
        filename=doc.filename,
        file_type=doc.file_type,
        chunk_count=doc.chunk_count,
        description=doc.description,
        created_at=doc.created_at,
        learning_summary=learning_summary,
    )


@router.delete("/{workstream}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    workstream: str,
    doc_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc or doc.workstream != workstream:
        raise HTTPException(status_code=404, detail="Document not found")
    events_result = await db.execute(
        select(AgentLearningEvent).where(AgentLearningEvent.source_doc_id == doc_id)
    )
    linked_events = list(events_result.scalars().all())
    try:
        from app.services.qdrant_client import delete_document_chunks
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: delete_document_chunks(str(doc_id)))
    except Exception:
        pass
    from app.services.kg_writer import delete_learning_event
    for ev in linked_events:
        background_tasks.add_task(delete_learning_event, ev.id)
        await db.delete(ev)
    await db.delete(doc)
    await db.commit()


@router.delete("/{workstream}/training-events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_training_event(
    workstream: str,
    event_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    _check_workstream(workstream)
    event = await db.get(AgentLearningEvent, event_id)
    if not event or event.workstream != workstream:
        raise HTTPException(status_code=404, detail="Training event not found")
    if event.source_doc_id:
        raise HTTPException(
            status_code=400,
            detail="Document-linked events must be deleted via document delete",
        )
    from app.services.kg_writer import delete_learning_event
    background_tasks.add_task(delete_learning_event, event.id)
    await db.delete(event)
    await db.commit()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_text(content_bytes: bytes, file_type: str, filename: str) -> str:
    if file_type == "pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            return f"[PDF parse error: {exc}]"
    # Plain text (txt, md, etc.)
    try:
        return content_bytes.decode("utf-8", errors="replace")
    except Exception:
        return content_bytes.decode("latin-1", errors="replace")


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return [c for c in chunks if c.strip()]


# ── AAHA Training (S24) ───────────────────────────────────────────────────────

@router.post("/{workstream}/train/aaha", response_model=AahaQuestionOut)
async def generate_aaha_question(workstream: str, db: AsyncSession = Depends(get_db)):
    """LLM generates a training question for consultant know-how capture."""
    _check_workstream(workstream)
    from app.services.llm_client import generate_aaha_training_question

    prior_res = await db.execute(
        select(AgentLearningEvent)
        .where(AgentLearningEvent.workstream == workstream)
        .where(AgentLearningEvent.mode == "aaha")
        .order_by(AgentLearningEvent.created_at.desc())
        .limit(5)
    )
    prior = [
        {"question_text": e.question_text, "answer_text": e.answer_text}
        for e in prior_res.scalars().all()
    ]
    loop = asyncio.get_event_loop()
    question = await loop.run_in_executor(
        None, lambda: generate_aaha_training_question(workstream, prior),
    )
    return AahaQuestionOut(question=question)


@router.post("/{workstream}/train/aaha/ai-answer", response_model=AahaAiAnswerOut)
async def generate_aaha_ai_answer(workstream: str, body: AahaAiAnswerIn):
    """LLM generates a draft AAHA answer for consultant review."""
    _check_workstream(workstream)
    from app.services.llm_client import generate_aaha_training_answer

    loop = asyncio.get_event_loop()
    answer = await loop.run_in_executor(
        None, lambda: generate_aaha_training_answer(workstream, body.question),
    )
    return AahaAiAnswerOut(answer=answer)


@router.post(
    "/{workstream}/train/aaha/answer",
    response_model=LearningEventOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_aaha_answer(
    workstream: str,
    body: AahaAnswerIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Save AAHA training Q&A, embed to Qdrant, write KG triple."""
    _check_workstream(workstream)
    author, consultant_id, approved_by = _resolve_aaha_author(body)
    event = AgentLearningEvent(
        id=uuid.uuid4(),
        workstream=workstream,
        mode="aaha",
        question_text=body.question,
        answer_text=body.answer,
        consultant_id=consultant_id,
        answer_author=author,
        approved_by_consultant_id=approved_by,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    qa_text = f"Soru: {body.question}\nYanıt: {body.answer}"
    chunks = _chunk_text(qa_text, chunk_size=200, overlap=20)
    try:
        from app.services.qdrant_client import upsert_training_chunks
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: upsert_training_chunks(str(event.id), workstream, chunks, mode="aaha"),
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Qdrant training embed failed: %s", exc)

    from app.services.kg_writer import write_training_interaction
    background_tasks.add_task(
        write_training_interaction,
        event.id, workstream, "aaha", body.question, body.answer, author,
    )

    layer_touch_svc.begin_operation(f"train_aaha_{workstream}", source="api")
    await layer_touch_svc.record_touch(
        db, "knowledge", "fuseki", "write",
        operation=f"train_aaha_{workstream}",
        detail={"event_id": str(event.id), "mode": "aaha"},
    )
    await layer_touch_svc.record_touch(
        db, "information", "qdrant", "embed",
        operation=f"train_aaha_{workstream}",
        detail={"event_id": str(event.id)},
    )
    await db.commit()

    return event


# ── Text Training (S24) ───────────────────────────────────────────────────────

@router.post(
    "/{workstream}/train/text",
    response_model=LearningEventOut,
    status_code=status.HTTP_201_CREATED,
)
async def train_text_knowledge(
    workstream: str,
    body: TextTrainIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Ingest consultant text know-how: chunk, embed, KG, learning event."""
    _check_workstream(workstream)
    event = AgentLearningEvent(
        id=uuid.uuid4(),
        workstream=workstream,
        mode="text",
        answer_text=body.content,
        consultant_id=body.consultant_id,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    chunks = _chunk_text(body.content)
    try:
        from app.services.qdrant_client import upsert_training_chunks
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: upsert_training_chunks(str(event.id), workstream, chunks, mode="text"),
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Qdrant text training embed failed: %s", exc)

    from app.services.kg_writer import write_agent_knowledge
    background_tasks.add_task(
        write_agent_knowledge, event.id, workstream, body.content,
    )

    layer_touch_svc.begin_operation(f"train_text_{workstream}", source="api")
    await layer_touch_svc.record_touch(
        db, "knowledge", "fuseki", "write",
        operation=f"train_text_{workstream}",
        detail={"event_id": str(event.id), "mode": "text"},
    )
    await layer_touch_svc.record_touch(
        db, "information", "qdrant", "embed",
        operation=f"train_text_{workstream}",
        detail={"event_id": str(event.id), "chunks": len(chunks)},
    )
    await db.commit()

    return event


# ── Agent Knowledge (S30) ─────────────────────────────────────────────────────

@router.get("/{workstream}/knowledge-summary", response_model=AgentKnowledgeSummaryOut)
async def get_agent_knowledge_summary(workstream: str, db: AsyncSession = Depends(get_db)):
    """Stats, recent learning events, mini-graph, and ontology class summary."""
    _check_workstream(workstream)
    return await _compute_knowledge_summary(workstream, db)


@router.get("/{workstream}/graph", response_model=AgentGraphOut)
async def get_agent_graph(workstream: str, db: AsyncSession = Depends(get_db)):
    """Agent KG subgraph from Fuseki (live). Falls back to PG-derived graph if Fuseki unavailable."""
    _check_workstream(workstream)
    try:
        from app.services.agent_kg import fetch_agent_kg_triples, triples_to_graph

        triples = await fetch_agent_kg_triples(workstream)
        if triples:
            g = triples_to_graph(triples)
            return AgentGraphOut(
                nodes=[GraphNode(id=n["id"], label=n["label"], type=n["type"]) for n in g["nodes"]],
                edges=[GraphEdge(**e) for e in g["edges"]],
            )
    except Exception:
        pass
    return await _build_agent_graph(workstream, db)


@router.get("/{workstream}/protege-export.ttl", response_class=PlainTextResponse)
async def export_agent_protege_ttl(workstream: str):
    """Ontology TBox + Fuseki agent instances as one Protege-ready Turtle file."""
    _check_workstream(workstream)
    from app.services.protege_export import build_agent_protege_bundle

    body, _triple_count = await build_agent_protege_bundle(workstream)
    filename = f"aakp-agent-{workstream}-protege.ttl"
    return PlainTextResponse(
        content=body,
        media_type="text/turtle",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
