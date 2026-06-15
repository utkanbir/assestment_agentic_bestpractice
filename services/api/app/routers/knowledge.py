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
