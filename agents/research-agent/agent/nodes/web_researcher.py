# S5-AA-006: Web search for domain knowledge
import logging

import httpx

from agent.config import settings
from agent.state import ResearchAgentState

log = logging.getLogger(__name__)


async def web_researcher(state: ResearchAgentState) -> dict:
    topic = state["topic"]
    results: list[dict] = []

    if not settings.tavily_api_key:
        log.info("No Tavily key — skipping web search for topic: %s", topic)
        return {"web_results": [], "status": "researching"}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": f"{topic} {state.get('domain', '')} best practices",
                    "search_depth": "advanced",
                    "max_results": 5,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                results = [
                    {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
                    for r in data.get("results", [])
                ]
    except Exception as exc:
        log.warning("Web search failed (non-fatal): %s", exc)

    return {"web_results": results, "status": "researching"}
