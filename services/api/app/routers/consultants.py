import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assessment import Assessment
from app.models.consultant import Consultant
from app.schemas.consultant import ConsultantCreate, ConsultantOut, ConsultantUpdate
from app.services.expertise_catalog import ExpertiseCatalogOut, get_expertise_catalog

router = APIRouter(prefix="/consultants", tags=["consultants"])


@router.get("/expertise-catalog", response_model=ExpertiseCatalogOut)
async def expertise_catalog():
    return get_expertise_catalog()


@router.get("", response_model=list[ConsultantOut])
async def list_consultants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Consultant).order_by(Consultant.last_name, Consultant.first_name))
    return result.scalars().all()


@router.post("", response_model=ConsultantOut, status_code=status.HTTP_201_CREATED)
async def create_consultant(body: ConsultantCreate, db: AsyncSession = Depends(get_db)):
    consultant = Consultant(**body.model_dump())
    db.add(consultant)
    await db.commit()
    await db.refresh(consultant)
    return consultant


@router.get("/{consultant_id}", response_model=ConsultantOut)
async def get_consultant(consultant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    consultant = await db.get(Consultant, consultant_id)
    if not consultant:
        raise HTTPException(status_code=404, detail="Consultant not found")
    return consultant


@router.patch("/{consultant_id}", response_model=ConsultantOut)
async def update_consultant(
    consultant_id: uuid.UUID,
    body: ConsultantUpdate,
    db: AsyncSession = Depends(get_db),
):
    consultant = await db.get(Consultant, consultant_id)
    if not consultant:
        raise HTTPException(status_code=404, detail="Consultant not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(consultant, field, value)
    await db.commit()
    await db.refresh(consultant)
    return consultant


@router.delete("/{consultant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_consultant(consultant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    consultant = await db.get(Consultant, consultant_id)
    if not consultant:
        raise HTTPException(status_code=404, detail="Consultant not found")
    await db.delete(consultant)
    await db.commit()
