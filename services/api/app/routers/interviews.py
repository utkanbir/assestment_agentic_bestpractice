import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assessment import Answer, Interview, Question
from app.schemas.interview import AnswerCreate, AnswerOut, InterviewCreate, InterviewOut, InterviewUpdate, QuestionCreate, QuestionOut
from app.services import kg_writer

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.get("", response_model=list[InterviewOut])
async def list_interviews(task_id: uuid.UUID | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Interview).order_by(Interview.created_at)
    if task_id:
        q = q.where(Interview.task_id == task_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=InterviewOut, status_code=status.HTTP_201_CREATED)
async def create_interview(
    body: InterviewCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    interview = Interview(**body.model_dump())
    db.add(interview)
    await db.commit()
    await db.refresh(interview)
    background_tasks.add_task(
        kg_writer.write_interview,
        interview.id, interview.task_id,
        interview.interviewee_name, interview.interviewee_role,
    )
    return interview


@router.get("/{interview_id}", response_model=InterviewOut)
async def get_interview(interview_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@router.patch("/{interview_id}", response_model=InterviewOut)
async def update_interview(interview_id: uuid.UUID, body: InterviewUpdate, db: AsyncSession = Depends(get_db)):
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(interview, field, value)
    await db.commit()
    await db.refresh(interview)
    return interview


@router.post("/{interview_id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def add_question(interview_id: uuid.UUID, body: QuestionCreate, db: AsyncSession = Depends(get_db)):
    body.interview_id = interview_id
    question = Question(**body.model_dump())
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


@router.get("/{interview_id}/questions", response_model=list[QuestionOut])
async def list_questions(interview_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question).where(Question.interview_id == interview_id).order_by(Question.order))
    return result.scalars().all()


@router.post("/questions/{question_id}/answers", response_model=AnswerOut, status_code=status.HTTP_201_CREATED)
async def add_answer(question_id: uuid.UUID, body: AnswerCreate, db: AsyncSession = Depends(get_db)):
    body.question_id = question_id
    answer = Answer(**body.model_dump())
    db.add(answer)
    await db.commit()
    await db.refresh(answer)
    return answer
