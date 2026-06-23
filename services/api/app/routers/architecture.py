import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.architecture import (
    LayerTouchOut,
    LayerTouchSummaryOut,
    LayerTransactionDetailOut,
    LayerTransactionOut,
    LayersRegistryOut,
)
from app.services.layer_registry import get_layers_registry
from app.services import layer_touch as layer_touch_svc

router = APIRouter(prefix="/architecture", tags=["architecture"])


@router.get("/layers", response_model=LayersRegistryOut)
async def get_architecture_layers():
    """Return the 4-layer registry with technologies."""
    return get_layers_registry()


@router.get("/touches", response_model=list[LayerTouchOut])
async def list_layer_touches(
    assessment_id: uuid.UUID | None = None,
    interview_id: uuid.UUID | None = None,
    layer: str | None = None,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await layer_touch_svc.list_touches(
        db,
        assessment_id=assessment_id,
        interview_id=interview_id,
        layer=layer,
        limit=limit,
    )


@router.get("/touches/summary", response_model=list[LayerTouchSummaryOut])
async def layer_touch_summary(
    assessment_id: uuid.UUID | None = None,
    interview_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await layer_touch_svc.touch_summary(
        db,
        assessment_id=assessment_id,
        interview_id=interview_id,
    )


@router.get("/transactions", response_model=list[LayerTransactionOut])
async def list_transactions(
    assessment_id: uuid.UUID | None = None,
    source: str | None = None,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await layer_touch_svc.list_transactions(
        db,
        assessment_id=assessment_id,
        source=source,
        limit=limit,
    )


@router.get("/transactions/{transaction_id}", response_model=LayerTransactionDetailOut)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    detail = await layer_touch_svc.get_transaction_detail(db, transaction_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Transaction not found")
    from app.services.explain_narrative import build_narrative

    narrative = build_narrative(detail.steps, operation=detail.operation)
    return detail.model_copy(update={"narrative": narrative})
