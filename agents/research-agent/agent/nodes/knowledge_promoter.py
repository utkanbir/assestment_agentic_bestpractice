# S5-AA-007: Promote approved research triples to knowledge graph
import httpx
import logging

from agent.config import settings
from agent.state import ResearchAgentState

log = logging.getLogger(__name__)

_PROMOTE_SPARQL = (
    "DELETE { GRAPH <urn:aakp:candidate> { ?s ?p ?o } } "
    "INSERT { GRAPH <urn:aakp:knowledge> { ?s ?p ?o } } "
    "WHERE { GRAPH <urn:aakp:candidate> { ?s ?p ?o } "
    "FILTER NOT EXISTS { GRAPH <urn:aakp:knowledge> { ?s ?p ?o } } }"
)


async def knowledge_promoter(state: ResearchAgentState) -> dict:
    if state.get("status") != "approved":
        return {"status": state.get("status", "rejected")}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.fuseki_url}/aakp/update",
                data=_PROMOTE_SPARQL,
                headers={"Content-Type": "application/sparql-update"},
            )
            if resp.status_code in (200, 204):
                log.info("Research triples promoted to knowledge graph")
                return {"status": "published", "published_uri": f"{settings.fuseki_url}/aakp/knowledge"}
            return {"status": "failed"}
    except Exception as exc:
        log.error("Promote error: %s", exc)
        return {"status": "failed"}
