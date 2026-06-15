# S5-AA-005: Promote approved candidate triples to the knowledge graph
import httpx
import logging

from agent.config import settings
from agent.state import CopilotState

log = logging.getLogger(__name__)

_APPROVE_SPARQL_PATH = "knowledge/sparql/candidate/02_approve_candidate.sparql"


async def knowledge_publisher(state: CopilotState) -> dict:
    if state.get("status") != "approved":
        return {"status": state.get("status", "rejected")}

    try:
        with open(_APPROVE_SPARQL_PATH) as f:
            sparql = f.read()
    except FileNotFoundError:
        sparql = (
            "DELETE { GRAPH <urn:aakp:candidate> { ?s ?p ?o } } "
            "INSERT { GRAPH <urn:aakp:knowledge> { ?s ?p ?o } } "
            "WHERE { GRAPH <urn:aakp:candidate> { ?s ?p ?o } }"
        )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.fuseki_url}/aakp/update",
                data=sparql,
                headers={"Content-Type": "application/sparql-update"},
            )
            if resp.status_code in (200, 204):
                log.info("Candidate triples promoted to knowledge graph")
                return {"status": "published", "published_uri": f"{settings.fuseki_url}/aakp/knowledge"}
            else:
                log.error("Fuseki promote failed: %s", resp.status_code)
                return {"status": "failed"}
    except Exception as exc:
        log.error("Knowledge publish error: %s", exc)
        return {"status": "failed"}
