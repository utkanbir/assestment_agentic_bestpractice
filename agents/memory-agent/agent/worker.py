"""Assessment Memory Agent — S3-AA-014

Kafka consumer that auto-ingests assessment artifacts into Qdrant for semantic search.

Topics consumed:
  - assessment.finding.created   → upsert finding into Qdrant findings collection
  - interview.answer.submitted   → upsert evidence content into Qdrant evidence collection
  - assessment.interview.completed → upsert full transcript into Qdrant transcripts collection

This agent has NO LangGraph dependency — it's a pure async Kafka consumer.
"""
import asyncio
import json
import logging
import uuid
from functools import lru_cache

import httpx
from aiokafka import AIOKafkaConsumer

from agent.config import settings

log = logging.getLogger(__name__)

_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_VECTOR_SIZE = 384


@lru_cache(maxsize=1)
def _get_encoder():
    from fastembed import TextEmbedding
    log.info("Loading fastembed model %s", _EMBEDDING_MODEL)
    return TextEmbedding(model_name=_EMBEDDING_MODEL)


def _embed(text: str) -> list[float]:
    encoder = _get_encoder()
    return list(next(iter(encoder.embed([text]))))


def _qdrant():
    from qdrant_client import QdrantClient
    return QdrantClient(url=settings.qdrant_url, timeout=30)


def _ensure_collections() -> None:
    from qdrant_client.models import Distance, VectorParams
    client = _qdrant()
    existing = {c.name for c in client.get_collections().collections}
    for name in ("findings", "evidence", "transcripts"):
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=_VECTOR_SIZE, distance=Distance.COSINE),
            )
            log.info("Created Qdrant collection: %s", name)


def _upsert_finding(event: dict) -> None:
    from qdrant_client.models import PointStruct
    finding_id = event.get("finding_id")
    description = event.get("description", "")
    if not finding_id or not description:
        return
    client = _qdrant()
    client.upsert(
        collection_name="findings",
        points=[PointStruct(
            id=str(finding_id),
            vector=_embed(description),
            payload={
                "finding_id": str(finding_id),
                "task_id": str(event.get("task_id", "")),
                "assessment_id": str(event.get("assessment_id", "")),
                "severity": event.get("severity", ""),
                "confidence": event.get("confidence", 0.0),
                "description": description,
                "workstream": event.get("workstream", ""),
            },
        )],
    )
    log.info("Qdrant upsert finding %s", finding_id)


def _upsert_evidence(event: dict) -> None:
    from qdrant_client.models import PointStruct
    evidence_id = event.get("evidence_id")
    content = event.get("content", "")
    if not evidence_id or not content:
        return
    client = _qdrant()
    client.upsert(
        collection_name="evidence",
        points=[PointStruct(
            id=str(evidence_id),
            vector=_embed(content),
            payload={
                "evidence_id": str(evidence_id),
                "interview_id": str(event.get("interview_id", "")),
                "source": event.get("source", "interview"),
                "content": content[:1000],
            },
        )],
    )
    log.info("Qdrant upsert evidence %s", evidence_id)


def _upsert_transcript(event: dict) -> None:
    from qdrant_client.models import PointStruct
    interview_id = event.get("interview_id")
    content = event.get("content", "") or event.get("text", "")
    if not interview_id or not content:
        return
    client = _qdrant()
    client.upsert(
        collection_name="transcripts",
        points=[PointStruct(
            id=str(interview_id),
            vector=_embed(content),
            payload={
                "interview_id": str(interview_id),
                "task_id": str(event.get("task_id", "")),
                "interviewee_name": event.get("interviewee_name", ""),
                "text": content[:1000],
            },
        )],
    )
    log.info("Qdrant upsert transcript %s", interview_id)


async def _enrich_finding_from_api(event: dict) -> dict:
    """If the event lacks description/severity, fetch from API."""
    finding_id = event.get("finding_id")
    if not finding_id or event.get("description"):
        return event
    try:
        async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=10) as client:
            resp = await client.get(f"/api/v1/findings/{finding_id}")
            if resp.status_code == 200:
                data = resp.json()
                return {**event, **data}
    except Exception as exc:
        log.warning("Could not enrich finding %s from API: %s", finding_id, exc)
    return event


async def run() -> None:
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _ensure_collections)

    consumer = AIOKafkaConsumer(
        "assessment.finding.created",
        "interview.answer.submitted",
        "assessment.interview.completed",
        bootstrap_servers=settings.kafka_bootstrap,
        group_id=settings.kafka_group_id,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    await consumer.start()
    log.info("Memory agent worker started — listening for artifacts to index into Qdrant")
    try:
        async for msg in consumer:
            topic = msg.topic
            event = msg.value
            log.debug("Received %s: %s", topic, list(event.keys()))
            try:
                if topic == "assessment.finding.created":
                    enriched = await _enrich_finding_from_api(event)
                    await loop.run_in_executor(None, _upsert_finding, enriched)
                elif topic == "interview.answer.submitted":
                    await loop.run_in_executor(None, _upsert_evidence, event)
                elif topic == "assessment.interview.completed":
                    await loop.run_in_executor(None, _upsert_transcript, event)
            except Exception as exc:
                log.exception("Error indexing %s event: %s", topic, exc)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
