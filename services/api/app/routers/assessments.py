import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate, AssessmentOut, AssessmentUpdate

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("", response_model=list[AssessmentOut])
async def list_assessments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).order_by(Assessment.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
async def create_assessment(body: AssessmentCreate, db: AsyncSession = Depends(get_db)):
    assessment = Assessment(**body.model_dump())
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    return assessment


@router.get("/{assessment_id}", response_model=AssessmentOut)
async def get_assessment(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@router.patch("/{assessment_id}", response_model=AssessmentOut)
async def update_assessment(assessment_id: uuid.UUID, body: AssessmentUpdate, db: AsyncSession = Depends(get_db)):
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(assessment, field, value)
    await db.commit()
    await db.refresh(assessment)
    return assessment


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    await db.delete(assessment)
    await db.commit()
