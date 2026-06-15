import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.finding import Risk
from app.schemas.risk import RiskCreate, RiskOut
from app.services import kg_writer

router = APIRouter(prefix="/risks", tags=["risks"])


@router.post("", response_model=RiskOut, status_code=status.HTTP_201_CREATED)
async def create_risk(
    body: RiskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    risk = Risk(**body.model_dump())
    db.add(risk)
    await db.commit()
    await db.refresh(risk)
    background_tasks.add_task(
        kg_writer.write_risk,
        risk.id, risk.finding_id,
        risk.title or risk.description[:80],
        risk.description, risk.level, risk.impact or "",
    )
    return risk


@router.get("", response_model=list[RiskOut])
async def list_risks(finding_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Risk).order_by(Risk.created_at.desc())
    if finding_id:
        q = q.where(Risk.finding_id == finding_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{risk_id}", response_model=RiskOut)
async def get_risk(risk_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    risk = await db.get(Risk, risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return risk
