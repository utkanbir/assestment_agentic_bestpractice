import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.finding import Report
from app.schemas.report import ReportCreate, ReportOut

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def create_report(
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
):
    report = Report(**body.model_dump())
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("", response_model=list[ReportOut])
async def list_reports(
    assessment_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Report).order_by(Report.created_at.desc())
    if assessment_id:
        q = q.where(Report.assessment_id == assessment_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{report_id}", response_model=ReportOut)
async def update_report(
    report_id: uuid.UUID,
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    await db.commit()
    await db.refresh(report)
    return report
