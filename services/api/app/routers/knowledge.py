import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from rdflib import RDF, RDFS, OWL, URIRef

from app.services.sparql_client import sparql_client

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class ApprovalBody(BaseModel):
    status: str  # "approved" | "rejected"


@router.get("/tasks/{task_id}/findings")
async def kg_task_findings(task_id: uuid.UUID):
    try:
        return await sparql_client.get_task_findings(task_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fuseki error: {e}")


@router.post("/findings/{finding_id}/approve")
async def kg_approve_finding(finding_id: uuid.UUID, body: ApprovalBody):
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'rejected'")
    try:
        await sparql_client.approve_finding(finding_id, body.status)
        return {"finding_id": str(finding_id), "status": body.status}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fuseki error: {e}")


@router.post("/inference/run")
async def run_inference():
    """Trigger all materialized inference rules (rule_*.sparql).
    Returns per-rule status: 'ok' or 'error: <msg>'.
    """
    try:
        results = await sparql_client.run_inference_rules()
        return {"results": results, "rules_run": len(results)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Inference error: {e}")


@router.get("/gaps/confidence")
async def gap_confidence():
    """Return all Gaps with their inferred confidence (after Rule 5 runs)."""
    try:
        return await sparql_client.get_gap_confidence()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fuseki error: {e}")


@router.get("/chain/capability-gap-risk")
async def capability_gap_risk_chain(capability_uri: str | None = None):
    """S2-KA-009: Traverse Capability -> Gap -> Risk -> Finding chain.
    Optional capability_uri filter; omit to get full chain.
    """
    try:
        return await sparql_client.get_capability_gap_risk_chain(capability_uri)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fuseki error: {e}")


@router.get("/graphs/assessments")
async def list_assessment_graphs():
    """S2-KA-010: List all per-assessment versioned named graphs."""
    try:
        return {"graphs": await sparql_client.list_assessment_graphs()}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fuseki error: {e}")


@router.post("/graphs/assessments/{assessment_id}/snapshot")
async def snapshot_assessment_graph(assessment_id: uuid.UUID):
    """S2-KA-010: Copy assessment triples into a versioned named graph
    (graph:assessment/<assessment_id>). Idempotent — safe to re-run.
    """
    try:
        dst = await sparql_client.copy_to_assessment_graph(assessment_id)
        return {"assessment_id": str(assessment_id), "graph": dst}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fuseki error: {e}")


@router.delete("/graphs/assessments/{assessment_id}/snapshot", status_code=204)
async def drop_assessment_graph(assessment_id: uuid.UUID):
    """S2-KA-010: Remove the versioned per-assessment named graph."""
    try:
        await sparql_client.drop_assessment_graph(assessment_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fuseki error: {e}")


@router.post("/validate/shacl")
async def validate_shacl(graph_uri: str | None = None):
    """S2-KA-002: Validate Fuseki KG against bundled SHACL shapes.

    Optional query param: graph_uri=<URI> to validate a specific named graph.
    Default: validates default graph (all data).
    """
    try:
        return await sparql_client.validate_shacl(graph_uri)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"SHACL validation error: {e}")


# ── Agent Registry (S3-AA-008) ────────────────────────────────────────────────

@router.get("/agents")
async def list_agents():
    """S3-AA-008: Return all registered assessment agents from graph:agents."""
    try:
        return await sparql_client.list_agents()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fuseki error: {e}")


@router.post("/agents/register")
async def register_agents():
    """S3-AA-008: (Re-)register all 8 assessment agents into graph:agents.
    Idempotent — safe to call multiple times.
    """
    try:
        return await sparql_client.register_all_agents()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fuseki error: {e}")


def _ontology_dir() -> Path:
    bundled = Path(__file__).resolve().parent.parent / "data" / "ontology"
    if bundled.is_dir():
        return bundled
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "knowledge" / "ontology"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("knowledge/ontology directory not found")


@router.get("/ontology/schema")
async def ontology_schema():
    try:
        from rdflib import Graph
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"rdflib not available: {exc}")

    graph = Graph()
    sources: list[str] = []
    for ttl in sorted(_ontology_dir().glob("*.ttl")):
        if ttl.name.endswith("_instances.ttl"):
            continue
        try:
            graph.parse(ttl.as_posix(), format="turtle")
            sources.append(ttl.name)
        except Exception:
            continue

    classes = []
    properties = []

    for cls in set(graph.subjects(RDF.type, OWL.Class)):
        classes.append(
            {
                "id": str(cls),
                "label": str(graph.value(cls, RDFS.label) or cls.split("#")[-1]),
                "comment": str(graph.value(cls, RDFS.comment) or ""),
                "parents": [str(parent) for parent in graph.objects(cls, RDFS.subClassOf)],
            }
        )

    for prop_type in (OWL.ObjectProperty, OWL.DatatypeProperty):
        for prop in set(graph.subjects(RDF.type, prop_type)):
            properties.append(
                {
                    "id": str(prop),
                    "label": str(graph.value(prop, RDFS.label) or str(prop).split("#")[-1]),
                    "comment": str(graph.value(prop, RDFS.comment) or ""),
                    "kind": "object" if prop_type == OWL.ObjectProperty else "datatype",
                    "domain": [str(v) for v in graph.objects(prop, RDFS.domain)],
                    "range": [str(v) for v in graph.objects(prop, RDFS.range)],
                }
            )

    classes.sort(key=lambda c: c["label"])
    properties.sort(key=lambda p: p["label"])
    return {"sources": sources, "classes": classes, "properties": properties}


@router.get("/ontology/export.ttl", response_class=PlainTextResponse)
async def export_ontology_ttl(include_instances: bool = False):
    """Merge bundled ontology TTL into one graph (imports inlined) for Protege."""
    try:
        import rdflib  # noqa: F401 — availability check
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"rdflib unavailable: {exc}") from exc

    from app.services.protege_export import load_ontology_graph

    graph = load_ontology_graph(include_instances=include_instances)
    if len(graph) == 0:
        raise HTTPException(status_code=404, detail="No ontology files found")

    body = graph.serialize(format="turtle")
    filename = "aakp-ontology-full.ttl" if include_instances else "aakp-ontology.ttl"
    return PlainTextResponse(
        content=body,
        media_type="text/turtle",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/graph/assessment/{assessment_id}")
async def assessment_graph(assessment_id: uuid.UUID):
    try:
        raw = await sparql_client.get_assessment_graph(assessment_id)
    except Exception:
        return {"nodes": [], "edges": []}

    bindings = raw.get("results", {}).get("bindings", [])
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    seen_edges: set[tuple[str, str, str]] = set()

    def _short(uri: str) -> str:
        if "#" in uri:
            return uri.split("#")[-1]
        return uri.rstrip("/").split("/")[-1]

    for row in bindings:
        s = row.get("s", {}).get("value")
        s_type = row.get("sType", {}).get("value", "")
        p = row.get("p", {}).get("value")
        o = row.get("o", {}).get("value")
        o_type = row.get("oType", {}).get("value", "")
        if not (s and p and o):
            continue

        if s not in nodes:
            nodes[s] = {"id": s, "type": _short(s_type) if s_type else "Resource", "label": _short(s)}

        if o.startswith("http://") or o.startswith("https://"):
            if o not in nodes:
                nodes[o] = {"id": o, "type": _short(o_type) if o_type else "Resource", "label": _short(o)}
            key = (s, o, p)
            if key not in seen_edges:
                seen_edges.add(key)
                edges.append({"from": s, "to": o, "predicate": _short(p)})

    return {"nodes": list(nodes.values()), "edges": edges}
