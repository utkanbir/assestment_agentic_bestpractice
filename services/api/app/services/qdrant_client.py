"""
Qdrant vector store client — S2-BA-001/002/003.

Collections (384-dim cosine, paraphrase-multilingual-MiniLM-L12-v2 via fastembed):
  findings    — finding descriptions + severity/confidence metadata
  evidence    — evidence content + source metadata
  transcripts — full interview answer text + interview metadata

Uses fastembed (ONNX-based, no PyTorch) for lightweight server-side embedding.
"""
import logging
import uuid
from functools import lru_cache
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_COLLECTIONS = ("findings", "evidence", "transcripts")
_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_VECTOR_SIZE = 384


@lru_cache(maxsize=1)
def _get_encoder():
    from fastembed import TextEmbedding
    logger.info("Loading fastembed model %s", _EMBEDDING_MODEL)
    return TextEmbedding(model_name=_EMBEDDING_MODEL)


def _embed(text: str) -> list[float]:
    encoder = _get_encoder()
    return list(next(iter(encoder.embed([text]))))


def _client():
    from qdrant_client import QdrantClient
    return QdrantClient(url=settings.qdrant_url, timeout=30)


# ── Collection bootstrap ───────────────────────────────────────────────────────

def ensure_collections() -> None:
    """Create collections if they don't exist. Called at app startup."""
    from qdrant_client.models import Distance, VectorParams
    client = _client()
    existing = {c.name for c in client.get_collections().collections}
    for name in _COLLECTIONS:
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=_VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection: %s", name)


# ── Upsert helpers ─────────────────────────────────────────────────────────────

def upsert_finding(
    finding_id: uuid.UUID,
    description: str,
    severity: str,
    confidence: float,
    task_id: uuid.UUID,
    assessment_id: uuid.UUID | None = None,
) -> None:
    from qdrant_client.models import PointStruct
    client = _client()
    vector = _embed(description)
    client.upsert(
        collection_name="findings",
        points=[PointStruct(
            id=str(finding_id),
            vector=vector,
            payload={
                "finding_id": str(finding_id),
                "task_id": str(task_id),
                "assessment_id": str(assessment_id) if assessment_id else None,
                "severity": severity,
                "confidence": confidence,
                "description": description,
            },
        )],
    )


def upsert_evidence(
    evidence_id: uuid.UUID,
    content: str,
    source: str,
    interview_id: uuid.UUID | None = None,
) -> None:
    from qdrant_client.models import PointStruct
    client = _client()
    vector = _embed(content)
    client.upsert(
        collection_name="evidence",
        points=[PointStruct(
            id=str(evidence_id),
            vector=vector,
            payload={
                "evidence_id": str(evidence_id),
                "interview_id": str(interview_id) if interview_id else None,
                "source": source,
                "content": content,
            },
        )],
    )


def upsert_transcript(
    interview_id: uuid.UUID,
    text: str,
    task_id: uuid.UUID,
    interviewee_name: str = "",
) -> None:
    from qdrant_client.models import PointStruct
    client = _client()
    vector = _embed(text)
    client.upsert(
        collection_name="transcripts",
        points=[PointStruct(
            id=str(interview_id),
            vector=vector,
            payload={
                "interview_id": str(interview_id),
                "task_id": str(task_id),
                "interviewee_name": interviewee_name,
                "text": text[:1000],
            },
        )],
    )


# ── Search ─────────────────────────────────────────────────────────────────────

def search_similar_findings(
    query: str,
    limit: int = 5,
    score_threshold: float = 0.6,
    severity_filter: str | None = None,
) -> list[dict[str, Any]]:
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    client = _client()
    query_filter = None
    if severity_filter:
        query_filter = Filter(
            must=[FieldCondition(key="severity", match=MatchValue(value=severity_filter))]
        )
    hits = client.search(
        collection_name="findings",
        query_vector=_embed(query),
        limit=limit,
        score_threshold=score_threshold,
        query_filter=query_filter,
        with_payload=True,
    )
    return [{"score": h.score, **h.payload} for h in hits]


def search_similar_evidence(
    query: str,
    limit: int = 5,
    score_threshold: float = 0.6,
) -> list[dict[str, Any]]:
    client = _client()
    hits = client.search(
        collection_name="evidence",
        query_vector=_embed(query),
        limit=limit,
        score_threshold=score_threshold,
        with_payload=True,
    )
    return [{"score": h.score, **h.payload} for h in hits]


# ── Collection info ────────────────────────────────────────────────────────────

def collection_stats() -> dict[str, Any]:
    client = _client()
    result = {}
    for name in _COLLECTIONS:
        try:
            info = client.get_collection(name)
            result[name] = {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": str(info.status),
            }
        except Exception as exc:
            result[name] = {"error": str(exc)}
    return result
