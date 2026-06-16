# S5-BA-005: Human approval workflow for findings, risks, and recommendations
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.finding import ApprovalStatus, Finding, Risk, Recommendation

log = logging.getLogger("approvals")

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalRequest(BaseModel):
    decision: ApprovalStatus  # approved / rejected
    reviewer_note: str | None = None


@router.patch("/findings/{finding_id}", response_model=dict)
async def approve_finding(
    finding_id: uuid.UUID,
    body: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
):
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    if finding.approval_status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Finding already {finding.approval_status}")
    finding.approval_status = body.decision
    await db.commit()
    log.info("Finding %s → %s", finding_id, body.decision)
    return {"id": str(finding_id), "approval_status": body.decision, "reviewer_note": body.reviewer_note}


@router.patch("/risks/{risk_id}", response_model=dict)
async def approve_risk(
    risk_id: uuid.UUID,
    body: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
):
    risk = await db.get(Risk, risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    if risk.approval_status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Risk already {risk.approval_status}")
    risk.approval_status = body.decision
    await db.commit()
    log.info("Risk %s → %s", risk_id, body.decision)
    return {"id": str(risk_id), "approval_status": body.decision, "reviewer_note": body.reviewer_note}


@router.patch("/recommendations/{rec_id}", response_model=dict)
async def approve_recommendation(
    rec_id: uuid.UUID,
    body: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
):
    rec = await db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.approval_status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Recommendation already {rec.approval_status}")
    rec.approval_status = body.decision
    await db.commit()
    log.info("Recommendation %s → %s", rec_id, body.decision)
    return {"id": str(rec_id), "approval_status": body.decision, "reviewer_note": body.reviewer_note}


@router.get("/pending", response_model=dict)
async def list_pending_approvals(
    assessment_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """S8-BA-002: Return enriched pending approval items (full object details, not just IDs)."""
    from sqlalchemy import select
    from app.models.assessment import Task

    async def _fetch(model):
        q = select(model).where(model.approval_status == ApprovalStatus.PENDING)
        r = await db.execute(q)
        return r.scalars().all()

    findings = await _fetch(Finding)
    risks = await _fetch(Risk)
    recs = await _fetch(Recommendation)

    # If assessment_id filter given, restrict to findings/risks/recs under that assessment
    if assessment_id:
        task_result = await db.execute(select(Task).where(Task.assessment_id == assessment_id))
        task_ids = {t.id for t in task_result.scalars().all()}
        findings = [f for f in findings if f.task_id in task_ids]
        risk_finding_ids = {r.finding_id for r in risks}
        finding_task_map = {f.id: f.task_id for f in findings}
        risks = [r for r in risks if finding_task_map.get(r.finding_id) in task_ids]
        rec_finding_ids = {r.finding_id for r in recs}
        recs = [r for r in recs if finding_task_map.get(r.finding_id) in task_ids]

    return {
        "pending_findings": [
            {"id": str(f.id), "description": f.description, "severity": f.severity, "confidence": f.confidence}
            for f in findings
        ],
        "pending_risks": [
            {"id": str(r.id), "title": r.title, "description": r.description, "level": r.level}
            for r in risks
        ],
        "pending_recommendations": [
            {"id": str(r.id), "description": r.description, "priority": r.priority, "effort": r.effort}
            for r in recs
        ],
        "total": len(findings) + len(risks) + len(recs),
    }
