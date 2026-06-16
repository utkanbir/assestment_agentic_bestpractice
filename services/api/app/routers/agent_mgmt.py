"""Agent management — performance metrics + knowledge document upload (S11)."""
import asyncio
import io
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assessment import Answer, Interview, Question, Task
from app.models.knowledge import KnowledgeDocument

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


# ── Knowledge Documents (RAG) ─────────────────────────────────────────────────

@router.get("/{workstream}/documents", response_model=list[KnowledgeDocumentOut])
async def list_documents(workstream: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.workstream == workstream)
        .order_by(KnowledgeDocument.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{workstream}/documents", response_model=KnowledgeDocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workstream: str,
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
    await db.commit()
    await db.refresh(doc)
    return doc


@router.delete("/{workstream}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(workstream: str, doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc or doc.workstream != workstream:
        raise HTTPException(status_code=404, detail="Document not found")
    # Remove from Qdrant
    try:
        from app.services.qdrant_client import delete_document_chunks
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: delete_document_chunks(str(doc_id)))
    except Exception:
        pass
    await db.delete(doc)
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
