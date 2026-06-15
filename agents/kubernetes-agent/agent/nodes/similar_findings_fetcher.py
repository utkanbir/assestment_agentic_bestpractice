"""
S2-AA-005: Fetch semantically similar past findings from Qdrant before
finding_detector runs.

Calls POST /api/v1/qdrant/search/findings with the current evidence content
as the query. Results are stored in state["similar_findings"] and injected
into finding_detector's LLM prompt to help calibrate severity and confidence.

Non-fatal: if Qdrant is unreachable, returns empty list and lets
finding_detector proceed without context.
"""
import logging

import httpx

from agent.config import settings
from agent.state import KubernetesAgentState

logger = logging.getLogger(__name__)

_SEARCH_URL = f"{settings.api_base_url}/api/v1/qdrant/search/findings"


async def similar_findings_fetcher(state: KubernetesAgentState) -> dict:
    evidence_list = state.get("pending_evidence", [])
    last_evidence = evidence_list[-1] if evidence_list else None

    query_text = ""
    if last_evidence:
        query_text = last_evidence.get("content", "")
    if not query_text:
        query_text = state.get("last_answer", "")

    if not query_text:
        return {"similar_findings": []}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                _SEARCH_URL,
                json={"query": query_text, "limit": 5, "score_threshold": 0.60},
            )
            resp.raise_for_status()
            hits = resp.json().get("results", [])
            logger.info("Similar findings: %d hits for evidence snippet", len(hits))
            return {"similar_findings": hits}
    except Exception as exc:
        logger.warning("similar_findings_fetcher: Qdrant search failed (non-fatal): %s", exc)
        return {"similar_findings": []}
