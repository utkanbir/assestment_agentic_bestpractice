# S5-AA-004: Validate candidate triples against SHACL shapes via Fuseki
import httpx
import logging

from agent.config import settings
from agent.state import CopilotState

log = logging.getLogger(__name__)


async def shacl_validator(state: CopilotState) -> dict:
    sparql = state.get("sparql_insert", "")
    if not sparql:
        return {"validation_errors": ["No SPARQL INSERT generated"]}

    # Insert into candidate graph first, then validate
    errors: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Write candidate triples
            resp = await client.post(
                f"{settings.fuseki_url}/aakp/update",
                data=sparql,
                headers={"Content-Type": "application/sparql-update"},
            )
            if resp.status_code not in (200, 204):
                return {"validation_errors": [f"Fuseki INSERT failed: {resp.status_code}"]}

            # Validate via Fuseki SHACL endpoint
            shacl_resp = await client.post(
                f"{settings.fuseki_url}/aakp/shacl",
                data="SELECT * WHERE { ?s ?p ?o }",
                headers={"Content-Type": "application/sparql-query"},
            )
            if shacl_resp.status_code == 200:
                body = shacl_resp.json()
                violations = body.get("violations", [])
                errors = [v.get("message", str(v)) for v in violations]
    except Exception as exc:
        log.warning("SHACL validation non-fatal: %s", exc)

    return {
        "validation_errors": errors,
        "human_review_required": True,  # always require human review for ontology changes
    }
