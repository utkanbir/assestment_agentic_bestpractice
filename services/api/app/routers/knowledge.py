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
