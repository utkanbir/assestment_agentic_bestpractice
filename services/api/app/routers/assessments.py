import asyncio
import uuid
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.assessment import Answer, AnswerConsultantComment, Assessment, Interview, MaturityScore, Question, Task
from app.models.consultant import Consultant, assessment_consultants
from app.models.finding import Finding
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentDuplicateIn,
    AssessmentOut,
    AssessmentUpdate,
    LatestInterviewOut,
)
from app.schemas.consultant import (
    AssignConsultantIn,
    ConsultantOut,
    ConsultantSynthesisOut,
    MaturityAiSuggestOut,
)
from app.services import kg_writer
from app.services import llm_client
router = APIRouter(prefix="/assessments", tags=["assessments"])


class MaturityScoreIn(BaseModel):
    score: float
    maturity_level: str = "initial"
    notes: str | None = None
    target_score: float | None = None


class MaturityScoreOut(BaseModel):
    id: str
    workstream: str
    score: float
    maturity_level: str
    notes: str | None = None
    target_score: float | None = None

    model_config = {"from_attributes": True}


class AgentStatusOut(BaseModel):
    task_id: str
    workstream: str
    agent_type: str
    status: str


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


@router.post("/{assessment_id}/duplicate", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
async def duplicate_assessment(
    assessment_id: uuid.UUID,
    body: AssessmentDuplicateIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """S22-BA-001: Copy assessment metadata; optionally tasks and Q&A (not findings)."""
    source = await db.get(Assessment, assessment_id)
    if not source:
        raise HTTPException(status_code=404, detail="Assessment not found")

    copy = Assessment(
        client_name=source.client_name,
        project_name=f"{source.project_name} (Copy)",
        description=source.description,
        status="draft",
        assessment_mode="live",
    )
    db.add(copy)
    await db.flush()

    if body.include_tasks:
        task_result = await db.execute(
            select(Task)
            .where(Task.assessment_id == assessment_id)
            .options(
                selectinload(Task.interviews)
                .selectinload(Interview.questions)
                .selectinload(Question.answers)
                .selectinload(Answer.consultant_comments)
            )
        )
        source_tasks = task_result.scalars().all()

        for src_task in source_tasks:
            new_task = Task(
                assessment_id=copy.id,
                agent_type=src_task.agent_type,
                workstream=src_task.workstream,
                status="pending",
                scope=src_task.scope,
            )
            db.add(new_task)
            await db.flush()

            if not body.include_qa:
                continue

            for src_iv in src_task.interviews:
                new_iv = Interview(
                    task_id=new_task.id,
                    interviewee_name=src_iv.interviewee_name,
                    interviewee_role=src_iv.interviewee_role,
                    status=src_iv.status,
                )
                db.add(new_iv)
                await db.flush()

                q_id_map: dict[uuid.UUID, uuid.UUID] = {}
                for src_q in sorted(src_iv.questions, key=lambda q: q.order):
                    new_q = Question(
                        interview_id=new_iv.id,
                        text=src_q.text,
                        order=src_q.order,
                        agent_suggested=src_q.agent_suggested,
                        approval_status=src_q.approval_status,
                    )
                    db.add(new_q)
                    await db.flush()
                    q_id_map[src_q.id] = new_q.id

                    for src_a in src_q.answers:
                        new_a = Answer(
                            question_id=new_q.id,
                            text=src_a.text,
                            raw_transcript=src_a.raw_transcript,
                            evaluation=src_a.evaluation,
                            consultant_id=src_a.consultant_id,
                            consultant_comment=src_a.consultant_comment,
                            consultant_review_feedback=src_a.consultant_review_feedback,
                        )
                        db.add(new_a)
                        await db.flush()
                        for src_cc in src_a.consultant_comments:
                            db.add(AnswerConsultantComment(
                                answer_id=new_a.id,
                                consultant_id=src_cc.consultant_id,
                                comment=src_cc.comment,
                                consultant_review_feedback=src_cc.consultant_review_feedback,
                            ))

    await db.commit()
    await db.refresh(copy)
    background_tasks.add_task(
        kg_writer.write_assessment,
        copy.id, copy.client_name, copy.project_name,
    )
    return copy


@router.get("/{assessment_id}/interviews/latest", response_model=LatestInterviewOut)
async def get_latest_interview(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """S22-BA-002: Most recent interview for an assessment (any workstream)."""
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    result = await db.execute(
        select(Interview, Task)
        .join(Task, Interview.task_id == Task.id)
        .where(Task.assessment_id == assessment_id)
        .order_by(Interview.created_at.desc())
        .limit(1)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="No interviews found for this assessment")

    interview, task = row
    return LatestInterviewOut(
        interview_id=str(interview.id),
        task_id=str(task.id),
        workstream=task.workstream,
        created_at=interview.created_at,
    )


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
            target_score=float(s.target_score) if s.target_score is not None else None,
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
        if body.target_score is not None:
            score.target_score = Decimal(str(body.target_score))
    else:
        score = MaturityScore(
            assessment_id=assessment_id,
            workstream=workstream,
            score=Decimal(str(body.score)),
            maturity_level=body.maturity_level,
            notes=body.notes,
            target_score=Decimal(str(body.target_score)) if body.target_score is not None else None,
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
        target_score=float(score.target_score) if score.target_score is not None else None,
    )


@router.get("/{assessment_id}/agent-status", response_model=list[AgentStatusOut])
async def get_agent_status(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """S10-BA-002: Return status of all 8 agent tasks for an assessment."""
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    result = await db.execute(
        select(Task)
        .where(Task.assessment_id == assessment_id)
        .order_by(Task.workstream)
    )
    tasks = result.scalars().all()
    return [
        AgentStatusOut(
            task_id=str(t.id),
            workstream=t.workstream,
            agent_type=t.agent_type,
            status=t.status,
        )
        for t in tasks
    ]


@router.get("/{assessment_id}/consultants", response_model=list[ConsultantOut])
async def list_assessment_consultants(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    result = await db.execute(
        select(Consultant)
        .join(assessment_consultants, Consultant.id == assessment_consultants.c.consultant_id)
        .where(assessment_consultants.c.assessment_id == assessment_id)
        .order_by(Consultant.last_name, Consultant.first_name)
    )
    return result.scalars().all()


@router.post("/{assessment_id}/consultants", response_model=ConsultantOut, status_code=status.HTTP_201_CREATED)
async def assign_consultant(
    assessment_id: uuid.UUID,
    body: AssignConsultantIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    consultant = await db.get(Consultant, body.consultant_id)
    if not consultant:
        raise HTTPException(status_code=404, detail="Consultant not found")

    existing = await db.execute(
        select(assessment_consultants)
        .where(assessment_consultants.c.assessment_id == assessment_id)
        .where(assessment_consultants.c.consultant_id == body.consultant_id)
    )
    if not existing.first():
        await db.execute(
            insert(assessment_consultants).values(
                assessment_id=assessment_id,
                consultant_id=body.consultant_id,
            )
        )
        await db.commit()
        background_tasks.add_task(
            kg_writer.write_consultant_assignment,
            assessment_id, consultant.id,
            consultant.first_name, consultant.last_name,
            consultant.role, consultant.expertise,
        )
    return consultant


@router.delete("/{assessment_id}/consultants/{consultant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_consultant(
    assessment_id: uuid.UUID,
    consultant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    consultant = await db.get(Consultant, consultant_id)
    if not consultant:
        raise HTTPException(status_code=404, detail="Consultant not found")
    await db.execute(
        delete(assessment_consultants)
        .where(assessment_consultants.c.assessment_id == assessment_id)
        .where(assessment_consultants.c.consultant_id == consultant_id)
    )
    await db.commit()


@router.post("/{assessment_id}/consultant-synthesis", response_model=ConsultantSynthesisOut)
async def generate_consultant_synthesis(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """S23-BA-002: LLM batch summary from Q&A evaluations + consultant comments."""
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    result = await db.execute(
        select(Answer, Question, Task)
        .join(Question, Answer.question_id == Question.id)
        .join(Interview, Question.interview_id == Interview.id)
        .join(Task, Interview.task_id == Task.id)
        .where(Task.assessment_id == assessment_id)
        .options(selectinload(Answer.consultant_comments))
        .order_by(Task.workstream, Question.order, Answer.created_at)
    )
    rows = result.all()
    if not rows:
        raise HTTPException(status_code=422, detail="No Q&A data found for synthesis")

    qa_items = []
    for answer, question, task in rows:
        comments = sorted(answer.consultant_comments, key=lambda c: c.created_at)
        if comments:
            for cc in comments:
                consultant = await db.get(Consultant, cc.consultant_id)
                qa_items.append({
                    "workstream": task.workstream,
                    "question": question.text,
                    "answer": answer.text,
                    "evaluation": answer.evaluation or "",
                    "consultant_name": f"{consultant.first_name} {consultant.last_name}" if consultant else "",
                    "consultant_comment": cc.comment or "",
                })
        else:
            legacy = await db.get(Consultant, answer.consultant_id) if answer.consultant_id else None
            qa_items.append({
                "workstream": task.workstream,
                "question": question.text,
                "answer": answer.text,
                "evaluation": answer.evaluation or "",
                "consultant_name": f"{legacy.first_name} {legacy.last_name}" if legacy else "",
                "consultant_comment": answer.consultant_comment or "",
            })

    synthesis = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: llm_client.generate_consultant_synthesis(qa_items),
    )
    assessment.consultant_synthesis = synthesis
    await db.commit()
    return ConsultantSynthesisOut(assessment_id=str(assessment_id), consultant_synthesis=synthesis)


@router.post("/{assessment_id}/maturity/{workstream}/ai-suggest", response_model=MaturityAiSuggestOut)
async def ai_suggest_maturity(
    assessment_id: uuid.UUID,
    workstream: str,
    db: AsyncSession = Depends(get_db),
):
    """S23-BA-003: AI maturity suggestion from interview evaluations + findings."""
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    task_result = await db.execute(
        select(Task).where(Task.assessment_id == assessment_id).where(Task.workstream == workstream)
    )
    task = task_result.scalar_one_or_none()

    eval_result = await db.execute(
        select(Answer, Question)
        .join(Question, Answer.question_id == Question.id)
        .join(Interview, Question.interview_id == Interview.id)
        .join(Task, Interview.task_id == Task.id)
        .where(Task.assessment_id == assessment_id)
        .where(Task.workstream == workstream)
        .where(Answer.evaluation.isnot(None))
        .order_by(Question.order)
    )
    evaluations = [
        {"question": q.text, "answer": a.text, "evaluation": a.evaluation or ""}
        for a, q in eval_result.all()
    ]

    findings: list[dict] = []
    if task:
        finding_result = await db.execute(
            select(Finding).where(Finding.task_id == task.id).order_by(Finding.created_at.desc())
        )
        findings = [
            {"description": f.description, "severity": f.severity, "confidence": float(f.confidence)}
            for f in finding_result.scalars().all()
        ]

    suggestion = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: llm_client.suggest_maturity_score(workstream, evaluations, findings),
    )

    score_row = await db.execute(
        select(MaturityScore)
        .where(MaturityScore.assessment_id == assessment_id)
        .where(MaturityScore.workstream == workstream)
    )
    maturity = score_row.scalar_one_or_none()
    if maturity:
        maturity.score = Decimal(str(suggestion["score"]))
        maturity.maturity_level = suggestion["maturity_level"]
        maturity.notes = suggestion["notes"]
    else:
        maturity = MaturityScore(
            assessment_id=assessment_id,
            workstream=workstream,
            score=Decimal(str(suggestion["score"])),
            maturity_level=suggestion["maturity_level"],
            notes=suggestion["notes"],
        )
        db.add(maturity)
    await db.commit()

    return MaturityAiSuggestOut(
        workstream=workstream,
        score=suggestion["score"],
        maturity_level=suggestion["maturity_level"],
        notes=suggestion["notes"],
    )


@router.get("/{assessment_id}/data-products/assessment-results")
async def get_assessment_results_product(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Gold composite data product: Assessment Results View."""
    from app.services.assessment_results_product import compose_assessment_results_view

    try:
        return await compose_assessment_results_view(assessment_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
