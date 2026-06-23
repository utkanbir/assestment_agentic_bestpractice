import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.assessment import Answer, AnswerConsultantComment, Interview, Question, Task
from app.schemas.interview import (
    AnswerConsultantCommentCreate, AnswerConsultantCommentOut, AnswerConsultantCommentUpdate,
    AnswerConsultantReviewIn, AnswerConsultantReviewOut, AnswerCreate, AnswerOut, AnswerUpdate, EvaluateOut,
    InterviewCreate, InterviewOut, InterviewUpdate,
    QuestionApprovalUpdate, QuestionCreate, QuestionOut,
    SuggestFollowupBody,
)
from app.services import kg_writer
from app.services import llm_client
from app.services import layer_touch as layer_touch_svc
from app.services.sparql_client import sparql_client

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _sync_answer_legacy_fields(answer: Answer) -> None:
    comments = sorted(answer.consultant_comments, key=lambda c: c.created_at)
    if comments:
        first = comments[0]
        answer.consultant_id = first.consultant_id
        answer.consultant_comment = first.comment
        answer.consultant_review_feedback = first.consultant_review_feedback
    else:
        answer.consultant_id = None
        answer.consultant_comment = None
        answer.consultant_review_feedback = None


def _answer_out(answer: Answer, **extra) -> AnswerOut:
    out = AnswerOut.model_validate(answer)
    out.consultant_comments = [
        AnswerConsultantCommentOut.model_validate(c) for c in sorted(answer.consultant_comments, key=lambda x: x.created_at)
    ]
    for key, value in extra.items():
        setattr(out, key, value)
    return out


async def _load_answer(db: AsyncSession, answer_id: uuid.UUID) -> Answer | None:
    result = await db.execute(
        select(Answer)
        .where(Answer.id == answer_id)
        .options(selectinload(Answer.consultant_comments))
    )
    return result.scalar_one_or_none()


async def _upsert_answer_consultant_comment(
    db: AsyncSession,
    answer: Answer,
    consultant_id: uuid.UUID,
    comment: str | None,
) -> AnswerConsultantComment:
    existing = next((c for c in answer.consultant_comments if c.consultant_id == consultant_id), None)
    if existing:
        existing.comment = comment
        row = existing
    else:
        row = AnswerConsultantComment(
            answer_id=answer.id,
            consultant_id=consultant_id,
            comment=comment,
        )
        db.add(row)
        answer.consultant_comments.append(row)
    _sync_answer_legacy_fields(answer)
    return row


async def _interview_context(db: AsyncSession, interview_id: uuid.UUID) -> tuple[Interview, Task]:
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    task = await db.get(Task, interview.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return interview, task


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
async def add_question(
    interview_id: uuid.UUID,
    body: QuestionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    body.interview_id = interview_id
    question = Question(**body.model_dump())
    db.add(question)
    await db.commit()
    await db.refresh(question)
    background_tasks.add_task(
        kg_writer.write_question,
        question.id,
        question.interview_id,
        question.text,
        question.order,
    )
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
async def add_answer(
    question_id: uuid.UUID,
    body: AnswerCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    question = await db.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    interview, task = await _interview_context(db, question.interview_id)

    layer_touch_svc.begin_operation(
        "save_answer",
        source="interview",
        interview_id=interview.id,
        assessment_id=task.assessment_id,
    )

    body.question_id = question_id
    payload = body.model_dump()
    consultant_id = payload.pop("consultant_id", None)
    consultant_comment = payload.pop("consultant_comment", None)
    answer = Answer(**payload)
    db.add(answer)
    await db.flush()
    if consultant_id:
        await _upsert_answer_consultant_comment(db, answer, consultant_id, consultant_comment)
    elif consultant_comment:
        answer.consultant_comment = consultant_comment
    await db.commit()
    answer = await _load_answer(db, answer.id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    await layer_touch_svc.record_touch(
        db, "information", "postgresql", "write",
        detail={"table": "answers", "answer_id": str(answer.id)},
    )
    background_tasks.add_task(
        kg_writer.write_answer,
        answer.id,
        question.id,
        answer.text,
        interview.id,
        answer.consultant_comment,
    )
    if answer.consultant_id:
        from app.models.consultant import Consultant
        consultant = await db.get(Consultant, answer.consultant_id)
        if consultant:
            background_tasks.add_task(
                kg_writer.write_consultant_on_answer,
                answer.id,
                question.id,
                consultant.id,
                consultant.first_name,
                consultant.last_name,
                answer.consultant_comment,
                task.assessment_id,
            )
    await db.commit()
    transaction_id = layer_touch_svc.get_transaction_id()
    trace = layer_touch_svc.finish_operation()
    return _answer_out(answer, layer_trace=trace, transaction_id=transaction_id)


@router.post("/answers/{answer_id}/evaluate", response_model=EvaluateOut)
async def evaluate_answer(
    answer_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Call Claude to evaluate an answer and persist the result."""
    answer = await db.get(Answer, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    question = await db.get(Question, answer.question_id)
    interview = await db.get(Interview, question.interview_id)
    task = await db.get(Task, interview.task_id)
    workstream = task.workstream if task else "unknown"

    layer_touch_svc.begin_operation(
        "evaluate_answer",
        source="interview",
        interview_id=interview.id,
        assessment_id=task.assessment_id if task else None,
    )
    await layer_touch_svc.record_touch(
        db, "information", "postgresql", "read",
        detail={"tables": ["answers", "questions", "interviews", "tasks"]},
    )

    doc_context = ""
    chunk_count = 0
    try:
        from app.services.qdrant_client import search_documents
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(
            None,
            lambda: search_documents(answer.text, workstream, limit=2),
        )
        chunk_count = len(chunks)
        doc_context = "\n".join(c["text"] for c in chunks)
        await layer_touch_svc.record_touch(
            db, "information", "qdrant", "search",
            detail={"chunks": chunk_count, "workstream": workstream},
        )
    except Exception:
        await layer_touch_svc.record_touch(
            db, "information", "qdrant", "search",
            detail={"chunks": 0, "workstream": workstream, "status": "unavailable"},
        )

    ontology_context = ""
    kg_hits = 0
    try:
        from app.services.agent_knowledge_context import build_kg_context
        ontology_context, kg_hits, _schema_hits = await build_kg_context(workstream)
        await layer_touch_svc.record_touch(
            db, "knowledge", "fuseki", "read",
            detail={"operation": "agent_training_context", "workstream": workstream, "hits": kg_hits},
        )
    except Exception:
        await layer_touch_svc.record_touch(
            db, "knowledge", "fuseki", "read",
            detail={"operation": "agent_training_context", "workstream": workstream, "status": "unavailable"},
        )

    evaluation = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: llm_client.evaluate_answer(
            workstream=workstream,
            question_text=question.text,
            answer_text=answer.text,
            doc_context="\n\n".join([s for s in [doc_context, ontology_context] if s.strip()]),
        ),
    )
    await layer_touch_svc.record_touch(
        db, "agent", "claude", "infer",
        detail={"operation": "evaluate_answer", "workstream": workstream},
    )

    answer.evaluation = evaluation
    await db.commit()

    await layer_touch_svc.record_touch(
        db, "information", "postgresql", "write",
        detail={"table": "answers", "field": "evaluation"},
    )
    await db.commit()

    background_tasks.add_task(
        kg_writer.write_evaluation,
        uuid.uuid4(),
        answer.id,
        evaluation,
        interview.id,
        task.assessment_id if task else None,
        True,
    )

    transaction_id = layer_touch_svc.get_transaction_id()
    trace = layer_touch_svc.finish_operation()
    return EvaluateOut(
        answer_id=answer_id,
        evaluation=evaluation,
        layer_trace=trace,
        transaction_id=transaction_id,
    )


@router.patch("/answers/{answer_id}", response_model=AnswerOut)
async def update_answer(
    answer_id: uuid.UUID,
    body: AnswerUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    answer = await _load_answer(db, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    question = await db.get(Question, answer.question_id)
    interview, task = await _interview_context(db, question.interview_id)

    data = body.model_dump(exclude_unset=True)
    consultant_id = data.pop("consultant_id", None) if "consultant_id" in data else None
    consultant_comment = data.pop("consultant_comment", None) if "consultant_comment" in data else None
    for field, value in data.items():
        setattr(answer, field, value)

    if consultant_id is not None or consultant_comment is not None:
        target_id = consultant_id or answer.consultant_id
        if target_id:
            await _upsert_answer_consultant_comment(
                db,
                answer,
                target_id,
                consultant_comment if consultant_comment is not None else answer.consultant_comment,
            )
        elif consultant_comment is not None:
            answer.consultant_comment = consultant_comment
    await db.commit()
    answer = await _load_answer(db, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    if answer.consultant_id is not None or body.consultant_comment is not None:
        from app.models.consultant import Consultant
        consultant = await db.get(Consultant, answer.consultant_id) if answer.consultant_id else None
        if consultant:
            background_tasks.add_task(
                kg_writer.write_consultant_on_answer,
                answer.id,
                question.id,
                consultant.id,
                consultant.first_name,
                consultant.last_name,
                answer.consultant_comment,
                task.assessment_id,
            )
    return _answer_out(answer)


@router.post("/answers/{answer_id}/consultant-review", response_model=AnswerConsultantReviewOut)
async def review_answer_consultant(
    answer_id: uuid.UUID,
    body: AnswerConsultantReviewIn,
    db: AsyncSession = Depends(get_db),
):
    answer = await _load_answer(db, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    question = await db.get(Question, answer.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    comment_row = sorted(answer.consultant_comments, key=lambda c: c.created_at)[0] if answer.consultant_comments else None
    comment = body.consultant_comment
    if comment is None:
        comment = comment_row.comment if comment_row else answer.consultant_comment
    check = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: llm_client.check_answer_consultant_consistency(
            question.text,
            answer.text,
            comment or "",
        ),
    )
    if comment_row:
        comment_row.consultant_review_feedback = check["feedback"]
        _sync_answer_legacy_fields(answer)
    else:
        answer.consultant_review_feedback = check["feedback"]
    await db.commit()
    return AnswerConsultantReviewOut(consistent=check["consistent"], feedback=check["feedback"])


@router.post(
    "/answers/{answer_id}/consultant-comments",
    response_model=AnswerConsultantCommentOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_answer_consultant_comment(
    answer_id: uuid.UUID,
    body: AnswerConsultantCommentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    answer = await _load_answer(db, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    from app.models.consultant import Consultant
    consultant = await db.get(Consultant, body.consultant_id)
    if not consultant:
        raise HTTPException(status_code=404, detail="Consultant not found")
    question = await db.get(Question, answer.question_id)
    interview, task = await _interview_context(db, question.interview_id)

    row = await _upsert_answer_consultant_comment(db, answer, body.consultant_id, body.comment)
    await db.commit()
    await db.refresh(row)

    background_tasks.add_task(
        kg_writer.write_consultant_on_answer,
        answer.id,
        question.id,
        consultant.id,
        consultant.first_name,
        consultant.last_name,
        row.comment,
        task.assessment_id,
    )
    return AnswerConsultantCommentOut.model_validate(row)


@router.patch(
    "/answers/{answer_id}/consultant-comments/{comment_id}",
    response_model=AnswerConsultantCommentOut,
)
async def update_answer_consultant_comment(
    answer_id: uuid.UUID,
    comment_id: uuid.UUID,
    body: AnswerConsultantCommentUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    answer = await _load_answer(db, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    row = next((c for c in answer.consultant_comments if c.id == comment_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Consultant comment not found")

    data = body.model_dump(exclude_unset=True)
    new_consultant_id = data.get("consultant_id")
    if new_consultant_id and new_consultant_id != row.consultant_id:
        from app.models.consultant import Consultant
        consultant = await db.get(Consultant, new_consultant_id)
        if not consultant:
            raise HTTPException(status_code=404, detail="Consultant not found")
        conflict = next((c for c in answer.consultant_comments if c.consultant_id == new_consultant_id and c.id != comment_id), None)
        if conflict:
            raise HTTPException(status_code=409, detail="Consultant already commented on this answer")
        row.consultant_id = new_consultant_id
    if "comment" in data:
        row.comment = data["comment"]
    _sync_answer_legacy_fields(answer)
    await db.commit()
    await db.refresh(row)

    question = await db.get(Question, answer.question_id)
    interview, task = await _interview_context(db, question.interview_id)
    from app.models.consultant import Consultant
    consultant = await db.get(Consultant, row.consultant_id)
    if consultant:
        background_tasks.add_task(
            kg_writer.write_consultant_on_answer,
            answer.id,
            question.id,
            consultant.id,
            consultant.first_name,
            consultant.last_name,
            row.comment,
            task.assessment_id,
        )
    return AnswerConsultantCommentOut.model_validate(row)


@router.post(
    "/answers/{answer_id}/consultant-comments/{comment_id}/consultant-review",
    response_model=AnswerConsultantReviewOut,
)
async def review_answer_consultant_comment(
    answer_id: uuid.UUID,
    comment_id: uuid.UUID,
    body: AnswerConsultantReviewIn,
    db: AsyncSession = Depends(get_db),
):
    answer = await _load_answer(db, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    question = await db.get(Question, answer.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    row = next((c for c in answer.consultant_comments if c.id == comment_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Consultant comment not found")

    comment = body.consultant_comment if body.consultant_comment is not None else row.comment
    check = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: llm_client.check_answer_consultant_consistency(
            question.text,
            answer.text,
            comment or "",
        ),
    )
    row.consultant_review_feedback = check["feedback"]
    _sync_answer_legacy_fields(answer)
    await db.commit()
    return AnswerConsultantReviewOut(consistent=check["consistent"], feedback=check["feedback"])


@router.get("/questions/{question_id}/answers", response_model=list[AnswerOut])
async def list_answers(question_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Answer)
        .where(Answer.question_id == question_id)
        .options(selectinload(Answer.consultant_comments))
        .order_by(Answer.created_at)
    )
    return [_answer_out(a) for a in result.scalars().all()]


# ── Agent follow-up suggestion ────────────────────────────────────────────────

@router.post("/{interview_id}/suggest-followup", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def suggest_followup(
    interview_id: uuid.UUID,
    body: SuggestFollowupBody = SuggestFollowupBody(),
    db: AsyncSession = Depends(get_db),
):
    interview, task = await _interview_context(db, interview_id)
    workstream = task.workstream

    layer_touch_svc.begin_operation(
        "suggest_followup",
        source="interview",
        interview_id=interview.id,
        assessment_id=task.assessment_id,
    )
    await layer_touch_svc.record_touch(
        db, "information", "postgresql", "read",
        detail={"tables": ["interviews", "questions", "answers", "tasks"]},
    )

    questions_result = await db.execute(
        select(Question)
        .where(Question.interview_id == interview_id)
        .order_by(Question.order)
        .options(selectinload(Question.answers))
    )
    questions = questions_result.scalars().all()

    qa_context = []
    for q in questions:
        qa_context.append({
            "question": q.text,
            "answer": questions[0].answers[0].text if q.answers else "",
        })
        if q.answers:
            qa_context[-1]["answer"] = q.answers[-1].text

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
        await layer_touch_svc.record_touch(
            db, "information", "qdrant", "search",
            detail={"chunks": len(chunks), "workstream": workstream},
        )
    except Exception:
        pass

    kg_context = ""
    try:
        from app.services.agent_knowledge_context import build_kg_context
        kg_context, _, _ = await build_kg_context(workstream)
        await layer_touch_svc.record_touch(
            db, "knowledge", "fuseki", "read",
            detail={"operation": "suggest_followup_kg", "workstream": workstream},
        )
    except Exception:
        pass
    doc_context = "\n\n".join(s for s in [doc_context, kg_context] if s.strip())

    last_order = max((q.order for q in questions), default=-1)
    next_order = last_order + 1

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
        await layer_touch_svc.record_touch(
            db, "agent", "claude", "infer",
            detail={"operation": "suggest_followup", "workstream": workstream},
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

    await layer_touch_svc.record_touch(
        db, "information", "postgresql", "write",
        detail={"table": "questions", "agent_suggested": True},
    )
    await db.commit()

    trace = layer_touch_svc.finish_operation()
    out = QuestionOut.model_validate(question)
    out.layer_trace = trace
    return out


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
