# S4-AA-005: Risk consolidation node — 8 workstream → unified risk list
from pathlib import Path
from SPARQLWrapper import SPARQLWrapper, JSON
from agent.config import settings
from agent.state import OrchestratorState

_HEATMAP_SPARQL = Path(__file__).parents[3] / "knowledge" / "sparql" / "orchestrator" / "02_risk_heatmap.sparql"

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _run_heatmap_query() -> list[dict]:
    sparql = SPARQLWrapper(
        f"{settings.fuseki_url}/{settings.fuseki_dataset}/sparql",
        agent="AAKP-Orchestrator/1.0",
    )
    sparql.setCredentials(settings.fuseki_user, settings.fuseki_password)
    sparql.setQuery(_HEATMAP_SPARQL.read_text(encoding="utf-8"))
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    rows = []
    for r in results["results"]["bindings"]:
        rows.append({
            "capability_area": r.get("capabilityArea", {}).get("value", ""),
            "severity": r.get("severityLevel", {}).get("value", ""),
            "risk_count": int(r.get("riskCount", {}).get("value", 0)),
            "workstreams": r.get("affectedWorkstreams", {}).get("value", "").split(","),
            "max_confidence": float(r.get("maxConfidence", {}).get("value", 0) or 0),
        })
    return rows


async def risk_consolidator(state: OrchestratorState) -> dict:
    try:
        heatmap = _run_heatmap_query()
    except Exception:
        heatmap = []

    # Build consolidated list: one entry per (capability_area, severity) sorted by severity
    consolidated = sorted(
        heatmap,
        key=lambda r: (_SEVERITY_ORDER.get(r["severity"], 99), r["capability_area"])
    )

    # Add propagated risks from state (Rule 6 output comes via dependency_checker)
    propagated = [
        {
            "capability_area": r.get("sharedCapabilityArea", ""),
            "severity": r.get("riskSeverityA", ""),
            "risk_count": 1,
            "workstreams": [r.get("workstreamA", ""), r.get("workstreamB", "")],
            "max_confidence": 0.0,
            "propagated": True,
        }
        for r in state.cross_task_dependencies
        if r.get("sharedCapabilityArea")
    ]

    return {
        "risk_heatmap": heatmap,
        "consolidated_risks": consolidated,
        "propagated_risks": propagated,
    }
