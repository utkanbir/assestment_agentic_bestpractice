import uuid
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assessment import Assessment, MaturityScore
from app.schemas.assessment import AssessmentCreate, AssessmentOut, AssessmentUpdate
from app.services import kg_writer

router = APIRouter(prefix="/assessments", tags=["assessments"])


class MaturityScoreIn(BaseModel):
    score: float
    maturity_level: str = "initial"
    notes: str | None = None


class MaturityScoreOut(BaseModel):
    id: str
    workstream: str
    score: float
    maturity_level: str
    notes: str | None = None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[AssessmentOut])
async def list_assessments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assessment).order_by(Assessment.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    body: AssessmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    assessment = Assessment(**body.model_dump())
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    background_tasks.add_task(
        kg_writer.write_assessment,
        assessment.id, assessment.client_name, assessment.project_name,
    )
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


@router.get("/{assessment_id}/maturity", response_model=list[MaturityScoreOut])
async def get_maturity_scores(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """S8-BA-001: Return all workstream maturity scores for an assessment."""
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    result = await db.execute(
        select(MaturityScore)
        .where(MaturityScore.assessment_id == assessment_id)
        .order_by(MaturityScore.workstream)
    )
    scores = result.scalars().all()
    return [
        MaturityScoreOut(
            id=str(s.id),
            workstream=s.workstream,
            score=float(s.score),
            maturity_level=s.maturity_level,
            notes=s.notes,
        )
        for s in scores
    ]


@router.put("/{assessment_id}/maturity/{workstream}", response_model=MaturityScoreOut, status_code=status.HTTP_200_OK)
async def upsert_maturity_score(
    assessment_id: uuid.UUID,
    workstream: str,
    body: MaturityScoreIn,
    db: AsyncSession = Depends(get_db),
):
    """S8-BA-001: Create or update maturity score for a workstream."""
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    result = await db.execute(
        select(MaturityScore)
        .where(MaturityScore.assessment_id == assessment_id)
        .where(MaturityScore.workstream == workstream)
    )
    score = result.scalar_one_or_none()
    if score:
        score.score = Decimal(str(body.score))
        score.maturity_level = body.maturity_level
        score.notes = body.notes
    else:
        score = MaturityScore(
            assessment_id=assessment_id,
            workstream=workstream,
            score=Decimal(str(body.score)),
            maturity_level=body.maturity_level,
            notes=body.notes,
        )
        db.add(score)
    await db.commit()
    await db.refresh(score)
    return MaturityScoreOut(
        id=str(score.id),
        workstream=score.workstream,
        score=float(score.score),
        maturity_level=score.maturity_level,
        notes=score.notes,
    )
