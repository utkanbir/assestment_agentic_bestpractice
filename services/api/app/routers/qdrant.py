import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import qdrant_client as qc

router = APIRouter(prefix="/qdrant", tags=["qdrant"])


class SimilarFindingsQuery(BaseModel):
    query: str
    limit: int = 5
    score_threshold: float = 0.6
    severity_filter: str | None = None


@router.get("/collections")
async def get_collections():
    """Collection stats: vector count, point count, status."""
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, qc.collection_stats)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Qdrant error: {exc}")


@router.post("/search/findings")
async def search_findings(body: SimilarFindingsQuery):
    """Semantic search over findings collection."""
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: qc.search_similar_findings(
                body.query, body.limit, body.score_threshold, body.severity_filter
            ),
        )
        return {"results": results, "count": len(results)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Qdrant error: {exc}")


@router.post("/search/evidence")
async def search_evidence(body: SimilarFindingsQuery):
    """Semantic search over evidence collection."""
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: qc.search_similar_evidence(
                body.query, body.limit, body.score_threshold
            ),
        )
        return {"results": results, "count": len(results)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Qdrant error: {exc}")
