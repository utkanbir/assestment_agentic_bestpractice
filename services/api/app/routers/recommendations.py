import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.finding import Recommendation
from app.schemas.recommendation import RecommendationCreate, RecommendationOut

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationOut, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    body: RecommendationCreate,
    db: AsyncSession = Depends(get_db),
):
    rec = Recommendation(**body.model_dump())
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


@router.get("", response_model=list[RecommendationOut])
async def list_recommendations(
    finding_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Recommendation).order_by(Recommendation.priority, Recommendation.created_at)
    if finding_id:
        q = q.where(Recommendation.finding_id == finding_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{rec_id}", response_model=RecommendationOut)
async def get_recommendation(rec_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rec = await db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec


@router.patch("/{rec_id}", response_model=RecommendationOut)
async def update_recommendation(
    rec_id: uuid.UUID,
    body: RecommendationCreate,
    db: AsyncSession = Depends(get_db),
):
    rec = await db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rec, field, value)
    await db.commit()
    await db.refresh(rec)
    return rec
