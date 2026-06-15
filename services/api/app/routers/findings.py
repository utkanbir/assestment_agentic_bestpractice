import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.finding import Evidence, Finding
from app.schemas.finding import EvidenceCreate, EvidenceOut, FindingCreate, FindingOut, FindingUpdate

router = APIRouter(tags=["findings"])

evidence_router = APIRouter(prefix="/evidences")
finding_router = APIRouter(prefix="/findings")


@evidence_router.post("", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
async def create_evidence(body: EvidenceCreate, db: AsyncSession = Depends(get_db)):
    evidence = Evidence(**body.model_dump())
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return evidence


@evidence_router.get("/{evidence_id}", response_model=EvidenceOut)
async def get_evidence(evidence_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    evidence = await db.get(Evidence, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@finding_router.get("", response_model=list[FindingOut])
async def list_findings(task_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Finding).order_by(Finding.created_at.desc())
    if task_id:
        q = q.where(Finding.task_id == task_id)
    result = await db.execute(q)
    return result.scalars().all()


@finding_router.post("", response_model=FindingOut, status_code=status.HTTP_201_CREATED)
async def create_finding(body: FindingCreate, db: AsyncSession = Depends(get_db)):
    finding = Finding(**body.model_dump())
    db.add(finding)
    await db.commit()
    await db.refresh(finding)
    return finding


@finding_router.get("/{finding_id}", response_model=FindingOut)
async def get_finding(finding_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@finding_router.patch("/{finding_id}", response_model=FindingOut)
async def update_finding(finding_id: uuid.UUID, body: FindingUpdate, db: AsyncSession = Depends(get_db)):
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(finding, field, value)
    await db.commit()
    await db.refresh(finding)
    return finding
