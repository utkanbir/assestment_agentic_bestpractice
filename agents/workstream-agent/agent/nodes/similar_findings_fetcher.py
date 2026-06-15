import httpx

from agent.config import settings
from agent.state import WorkstreamAgentState

_SEARCH_URL = "/api/v1/qdrant/search/findings"


async def similar_findings_fetcher(state: WorkstreamAgentState) -> dict:
    evidence_list = state.get("pending_evidence", [])
    last_evidence = evidence_list[-1] if evidence_list else None
    query_text = (last_evidence or {}).get("content", "") or state.get("last_answer", "")

    if not query_text:
        return {"similar_findings": []}

    try:
        async with httpx.AsyncClient(base_url=settings.api_base_url, timeout=10) as client:
            resp = await client.post(
                _SEARCH_URL,
                json={"query": query_text, "limit": 5, "score_threshold": 0.60},
            )
            if resp.status_code == 200:
                return {"similar_findings": resp.json().get("results", [])}
    except Exception:
        pass

    return {"similar_findings": []}
