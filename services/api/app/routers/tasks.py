import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assessment import Task
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services import kg_writer
from app.services.kafka_producer import publish

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(assessment_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Task).order_by(Task.created_at)
    if assessment_id:
        q = q.where(Task.assessment_id == assessment_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    task = Task(**body.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    background_tasks.add_task(
        kg_writer.write_task,
        task.id, task.assessment_id, task.agent_type, task.workstream, task.scope,
    )
    return task


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    old_status = task.status if hasattr(task, "status") else None
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    new_status = task.status if hasattr(task, "status") else None
    if old_status != new_status and new_status is not None:
        background_tasks.add_task(
            publish,
            "assessment.task.status.changed",
            {
                "task_id": str(task.id),
                "assessment_id": str(task.assessment_id),
                "workstream": getattr(task, "workstream", None),
                "agent_type": getattr(task, "agent_type", None),
                "old_status": old_status,
                "new_status": new_status,
            },
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
