import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.assessment import Answer, Interview, Question, Task
from app.schemas.interview import (
    AnswerCreate, AnswerOut, EvaluateOut,
    InterviewCreate, InterviewOut, InterviewUpdate,
    QuestionApprovalUpdate, QuestionCreate, QuestionOut,
    SuggestFollowupBody,
)
from app.services import kg_writer
from app.services import llm_client

router = APIRouter(prefix="/interviews", tags=["interviews"])


# ── Interview CRUD ────────────────────────────────────────────────────────────

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


# ── Questions ─────────────────────────────────────────────────────────────────

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
    result = await db.execute(
        select(Question)
        .where(Question.interview_id == interview_id)
        .order_by(Question.order)
    )
    return result.scalars().all()


# ── Answers ───────────────────────────────────────────────────────────────────

@router.post("/questions/{question_id}/answers", response_model=AnswerOut, status_code=status.HTTP_201_CREATED)
async def add_answer(question_id: uuid.UUID, body: AnswerCreate, db: AsyncSession = Depends(get_db)):
    body.question_id = question_id
    answer = Answer(**body.model_dump())
    db.add(answer)
    await db.commit()
    await db.refresh(answer)
    return answer


@router.post("/answers/{answer_id}/evaluate", response_model=EvaluateOut)
async def evaluate_answer(answer_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Call Claude to evaluate an answer and persist the result."""
    answer = await db.get(Answer, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Traverse: answer → question → interview → task (for workstream)
    question = await db.get(Question, answer.question_id)
    interview = await db.get(Interview, question.interview_id)
    task = await db.get(Task, interview.task_id)
    workstream = task.workstream if task else "unknown"

    # Fetch relevant doc context from Qdrant (best effort)
    doc_context = ""
    try:
        from app.services.qdrant_client import search_documents
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(
            None,
            lambda: search_documents(answer.text, workstream, limit=2),
        )
        doc_context = "\n".join(c["text"] for c in chunks)
    except Exception:
        pass

    evaluation = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: llm_client.evaluate_answer(
            workstream=workstream,
            question_text=question.text,
            answer_text=answer.text,
            doc_context=doc_context,
        ),
    )

    answer.evaluation = evaluation
    await db.commit()
    return EvaluateOut(answer_id=answer_id, evaluation=evaluation)


@router.get("/questions/{question_id}/answers", response_model=list[AnswerOut])
async def list_answers(question_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Answer)
        .where(Answer.question_id == question_id)
        .order_by(Answer.created_at)
    )
    return result.scalars().all()


# ── Agent follow-up suggestion ────────────────────────────────────────────────

@router.post("/{interview_id}/suggest-followup", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def suggest_followup(
    interview_id: uuid.UUID,
    body: SuggestFollowupBody = SuggestFollowupBody(),
    db: AsyncSession = Depends(get_db),
):
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    # Determine workstream from task
    task = await db.get(Task, interview.task_id)
    workstream = task.workstream if task else "unknown"

    # Load all questions with their answers for context
    questions_result = await db.execute(
        select(Question)
        .where(Question.interview_id == interview_id)
        .order_by(Question.order)
        .options(selectinload(Question.answers))
    )
    questions = questions_result.scalars().all()

    # Build Q&A context
    qa_context = []
    for q in questions:
        qa_context.append({
            "question": q.text,
            "answer": questions[0].answers[0].text if q.answers else "",
        })
        if q.answers:
            qa_context[-1]["answer"] = q.answers[-1].text

    # Fetch doc context from Qdrant (best effort)
    doc_context = ""
    try:
        from app.services.qdrant_client import search_documents
        loop = asyncio.get_event_loop()
        query = qa_context[-1]["answer"] if qa_context else workstream
        chunks = await loop.run_in_executor(
            None,
            lambda: search_documents(query, workstream, limit=2),
        )
        doc_context = "\n".join(c["text"] for c in chunks)
    except Exception:
        pass

    # Determine next order
    last_order = max((q.order for q in questions), default=-1)
    next_order = last_order + 1

    # Generate or use provided text
    if body.text:
        text = body.text
    else:
        text = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm_client.generate_followup_question(
                workstream=workstream,
                questions_and_answers=qa_context,
                doc_context=doc_context,
            ),
        )

    question = Question(
        interview_id=interview_id,
        text=text,
        order=next_order,
        agent_suggested=True,
        approval_status="pending",
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


# ── Question approval ─────────────────────────────────────────────────────────

@router.patch("/questions/{question_id}/approval", response_model=QuestionOut)
async def approve_question(question_id: uuid.UUID, body: QuestionApprovalUpdate, db: AsyncSession = Depends(get_db)):
    if body.action not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="action must be 'approved' or 'rejected'")
    question = await db.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    question.approval_status = body.action
    await db.commit()
    await db.refresh(question)
    return question
