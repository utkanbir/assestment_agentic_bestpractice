import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
