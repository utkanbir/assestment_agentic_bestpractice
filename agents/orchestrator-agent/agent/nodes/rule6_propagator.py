# S4-KA-001 / S4-AA-003: Rule 6 cross-task risk propagation via SPARQL INSERT
from pathlib import Path
import httpx
from agent.config import settings
from agent.state import OrchestratorState

_SPARQL_FILE = Path(__file__).parents[3] / "knowledge" / "sparql" / "orchestrator" / "00_rule6_cross_task_risk_propagation.sparql"


async def rule6_propagator(state: OrchestratorState) -> dict:
    query = _SPARQL_FILE.read_text(encoding="utf-8")
    url = f"{settings.fuseki_url}/{settings.fuseki_dataset}/update"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                content=query,
                headers={"Content-Type": "application/sparql-update"},
                auth=(settings.fuseki_user, settings.fuseki_password),
            )
        success = resp.status_code in (200, 204)
    except Exception:
        success = False

    return {"rule6_executed": success}
