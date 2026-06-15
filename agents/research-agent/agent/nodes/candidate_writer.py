# S5-AA-006: Write synthesized triples to candidate graph in Fuseki
import httpx
import logging

from agent.config import settings
from agent.state import ResearchAgentState

log = logging.getLogger(__name__)


async def candidate_writer(state: ResearchAgentState) -> dict:
    sparql = state.get("sparql_insert", "")
    if not sparql:
        return {"status": "failed"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.fuseki_url}/aakp/update",
                data=sparql,
                headers={"Content-Type": "application/sparql-update"},
            )
            if resp.status_code in (200, 204):
                log.info("Candidate triples written for topic: %s", state["topic"])
                return {"status": "pending"}
            log.error("Fuseki write failed: %s", resp.status_code)
            return {"status": "failed"}
    except Exception as exc:
        log.error("Candidate write error: %s", exc)
        return {"status": "failed"}
