import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.question_bank import WorkstreamQuestion
from app.schemas.question_bank import BulkLoadRequest, WorkstreamQuestionCreate, WorkstreamQuestionOut

router = APIRouter(prefix="/question-bank", tags=["question-bank"])


@router.get("/workstreams", response_model=list[str])
async def list_workstreams(db: AsyncSession = Depends(get_db)):
    """Return all workstream names that have at least one active question."""
    result = await db.execute(
        select(WorkstreamQuestion.workstream)
        .where(WorkstreamQuestion.is_active == True)
        .distinct()
        .order_by(WorkstreamQuestion.workstream)
    )
    return [row[0] for row in result.all()]


@router.get("", response_model=list[WorkstreamQuestionOut])
async def list_questions(
    workstream: str | None = None,
    area: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List questions, optionally filtered by workstream and/or area."""
    q = (
        select(WorkstreamQuestion)
        .where(WorkstreamQuestion.is_active == True)
        .order_by(WorkstreamQuestion.workstream, WorkstreamQuestion.order)
    )
    if workstream:
        q = q.where(WorkstreamQuestion.workstream == workstream)
    if area:
        q = q.where(WorkstreamQuestion.area == area)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=WorkstreamQuestionOut, status_code=status.HTTP_201_CREATED)
async def create_question(
    body: WorkstreamQuestionCreate,
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump()
    if data.get("follow_ups") is not None:
        data["follow_ups"] = json.dumps(data["follow_ups"], ensure_ascii=False)
    q = WorkstreamQuestion(**data)
    db.add(q)
    await db.commit()
    await db.refresh(q)
    return q


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_load(body: BulkLoadRequest, db: AsyncSession = Depends(get_db)):
    """Bulk-load questions for a workstream. If replace=True, deletes existing first."""
    if body.replace:
        await db.execute(
            delete(WorkstreamQuestion).where(
                WorkstreamQuestion.workstream == body.workstream
            )
        )
        await db.flush()

    rows = []
    for i, q in enumerate(body.questions):
        data = q.model_dump()
        data["workstream"] = body.workstream
        if data.get("follow_ups") is not None:
            data["follow_ups"] = json.dumps(data["follow_ups"], ensure_ascii=False)
        if data["order"] == 0:
            data["order"] = i + 1
        rows.append(WorkstreamQuestion(**data))

    db.add_all(rows)
    await db.commit()
    return {"workstream": body.workstream, "loaded": len(rows), "replaced": body.replace}


@router.get("/{question_id}", response_model=WorkstreamQuestionOut)
async def get_question(question_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    q = await db.get(WorkstreamQuestion, question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    q = await db.get(WorkstreamQuestion, question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    await db.delete(q)
    await db.commit()
