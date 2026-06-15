# S4-AA-003: Cross-task dependency checker (SPARQL + KG)
from pathlib import Path
import httpx
from SPARQLWrapper import SPARQLWrapper, JSON
from agent.config import settings
from agent.state import OrchestratorState

_SPARQL_FILE = Path(__file__).parents[3] / "knowledge" / "sparql" / "orchestrator" / "01_cross_task_dependencies.sparql"


def _run_dependency_query() -> list[dict]:
    sparql = SPARQLWrapper(
        f"{settings.fuseki_url}/{settings.fuseki_dataset}/sparql",
        agent="AAKP-Orchestrator/1.0",
    )
    sparql.setCredentials(settings.fuseki_user, settings.fuseki_password)
    sparql.setQuery(_SPARQL_FILE.read_text(encoding="utf-8"))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    rows = []
    for r in results["results"]["bindings"]:
        rows.append({k: v["value"] for k, v in r.items()})
    return rows


async def dependency_checker(state: OrchestratorState) -> dict:
    try:
        rows = _run_dependency_query()
    except Exception:
        rows = []

    dependencies = [r for r in rows if "conflictSignal" not in r or r.get("conflictSignal") == "SHARED_RISK_AREA"]
    shared_risks = [r for r in rows if r.get("conflictSignal", "").startswith("SEVERITY_CONFLICT")]

    return {
        "cross_task_dependencies": dependencies,
        "shared_risk_areas": shared_risks,
    }
