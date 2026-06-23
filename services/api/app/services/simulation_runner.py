"""S21: Autonomous AI simulated assessment runner."""
import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.assessment import Answer, Assessment, Interview, Question, Task
from app.models.question_bank import WorkstreamQuestion
from app.routers.ws import WSEventType, WSMessage, manager
from app.seeds.question_bank_seed import QUESTION_BANKS
from app.services import kg_writer
from app.services.llm_client import (
    WORKSTREAM_LABELS,
    evaluate_answer,
    generate_simulated_answers_batch,
)

logger = logging.getLogger(__name__)

SIMULATION_WORKSTREAMS = list(WORKSTREAM_LABELS.keys())


class _BankQuestion:
    """Adapter for DB or seed question bank entries."""

    def __init__(self, text: str, order: int):
        self.text = text
        self.order = order


async def _load_bank_questions(db: AsyncSession, ws: str) -> list[_BankQuestion]:
    result = await db.execute(
        select(WorkstreamQuestion)
        .where(WorkstreamQuestion.workstream == ws)
        .where(WorkstreamQuestion.is_active.is_(True))
        .order_by(WorkstreamQuestion.order)
    )
    rows = list(result.scalars().all())
    if rows:
        return [_BankQuestion(q.text, q.order) for q in rows]
    seed = QUESTION_BANKS.get(ws, [])
    return [_BankQuestion(item["text"], idx) for idx, item in enumerate(seed)]


async def _broadcast(interview_id: str | None, event: WSEventType, payload: dict) -> None:
    if not interview_id:
        return
    try:
        await manager.broadcast(interview_id, WSMessage(event=event, payload=payload))
    except Exception as exc:
        logger.debug("WS broadcast skipped: %s", exc)


async def _get_simulation_status(db: AsyncSession, assessment_id: uuid.UUID) -> str | None:
    result = await db.execute(
        select(Assessment.simulation_status).where(Assessment.id == assessment_id)
    )
    return result.scalar_one_or_none()


async def _should_stop(db: AsyncSession, assessment_id: uuid.UUID) -> bool:
    status = await _get_simulation_status(db, assessment_id)
    return status is None or status == "stopped"


async def _update_assessment(
    db: AsyncSession,
    assessment_id: uuid.UUID,
    *,
    simulation_status: str | None = None,
    status: str | None = None,
    simulation_progress: dict | None = None,
) -> None:
    values: dict = {}
    if simulation_status is not None:
        values["simulation_status"] = simulation_status
    if status is not None:
        values["status"] = status
    if simulation_progress is not None:
        values["simulation_progress"] = dict(simulation_progress)
    if not values:
        return
    await db.execute(
        update(Assessment).where(Assessment.id == assessment_id).values(**values)
    )
    await db.commit()


def _broadcast_interview_id(progress: dict) -> str | None:
    return progress.get("primary_interview_id") or progress.get("current_interview_id")


async def _save_progress(db: AsyncSession, assessment_id: uuid.UUID, progress: dict) -> None:
    await _update_assessment(db, assessment_id, simulation_progress=progress)
    await _broadcast(
        _broadcast_interview_id(progress),
        WSEventType.SIMULATION_PROGRESS,
        {"assessment_id": str(assessment_id), **progress},
    )


async def build_simulation_exec_summary(assessment_id: uuid.UUID, db: AsyncSession) -> str:
    """Build executive summary text from simulated Q&A evaluations."""
    result = await db.execute(
        select(Answer, Question, Task)
        .join(Question, Answer.question_id == Question.id)
        .join(Interview, Question.interview_id == Interview.id)
        .join(Task, Interview.task_id == Task.id)
        .where(Task.assessment_id == assessment_id)
        .where(Answer.evaluation.isnot(None))
        .order_by(Task.workstream, Question.order)
    )
    rows = result.all()
    if not rows:
        return "Simülasyon tamamlandı; henüz değerlendirilmiş yanıt bulunmuyor."

    by_ws: dict[str, list[str]] = {}
    for answer, _question, task in rows:
        snippet = (answer.evaluation or "")[:200]
        by_ws.setdefault(task.workstream, []).append(snippet)

    lines = ["AI Simülasyon Değerlendirme Özeti", ""]
    for ws, evals in by_ws.items():
        label = WORKSTREAM_LABELS.get(ws, ws)
        lines.append(f"## {label}")
        for i, ev in enumerate(evals[:3], 1):
            lines.append(f"{i}. {ev}")
        lines.append("")
    return "\n".join(lines).strip()


async def _process_workstream_batch(
    db: AsyncSession,
    assessment_id: uuid.UUID,
    company_profile,
    interview: Interview,
    task: Task,
    bank_questions: list[_BankQuestion],
    progress: dict,
) -> bool:
    """Create questions, batch-generate answers, parallel-evaluate. Returns False if stopped."""
    if await _should_stop(db, assessment_id):
        return False

    loop = asyncio.get_event_loop()
    questions: list[Question] = []

    for order, bank_q in enumerate(bank_questions):
        question = Question(
            interview_id=interview.id,
            text=bank_q.text,
            order=order,
            agent_suggested=False,
            approval_status="approved",
        )
        db.add(question)
        await db.commit()
        await db.refresh(question)
        await kg_writer.write_question(question.id, interview.id, question.text, question.order)
        questions.append(question)

    progress["questions_asked"] = progress.get("questions_asked", 0) + len(questions)
    progress["current_interview_id"] = str(interview.id)
    progress["current_workstream"] = task.workstream
    await _save_progress(db, assessment_id, progress)

    if await _should_stop(db, assessment_id):
        return False

    question_texts = [q.text for q in questions]
    answer_texts = await loop.run_in_executor(
        None,
        lambda: generate_simulated_answers_batch(
            task.workstream, question_texts, company_profile,
        ),
    )
    if len(answer_texts) != len(questions):
        logger.warning(
            "Batch answer count mismatch ws=%s: expected %d got %d",
            task.workstream, len(questions), len(answer_texts),
        )
        while len(answer_texts) < len(questions):
            answer_texts.append(
                f"{WORKSTREAM_LABELS.get(task.workstream, task.workstream)} "
                "kapsamında standart süreçlerimiz uygulanıyor."
            )
        answer_texts = answer_texts[: len(questions)]

    if await _should_stop(db, assessment_id):
        return False

    answers: list[Answer] = []
    for question, answer_text in zip(questions, answer_texts):
        answer = Answer(question_id=question.id, text=answer_text)
        db.add(answer)
        await db.commit()
        await db.refresh(answer)
        await kg_writer.write_answer(answer.id, question.id, answer.text, interview.id)
        answers.append(answer)

    if await _should_stop(db, assessment_id):
        return False

    sem = asyncio.Semaphore(3)

    async def _eval_one(question: Question, answer: Answer) -> tuple[Answer, str]:
        async with sem:
            try:
                evaluation = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda q=question, a=answer: evaluate_answer(
                            task.workstream, q.text, a.text,
                        ),
                    ),
                    timeout=120.0,
                )
            except asyncio.TimeoutError:
                evaluation = "[Evaluation timed out after 120s]"
            return answer, evaluation

    eval_results = await asyncio.gather(
        *[_eval_one(q, a) for q, a in zip(questions, answers)]
    )

    for answer, evaluation in eval_results:
        answer.evaluation = evaluation
        await db.commit()

        eval_id = uuid.uuid4()
        await kg_writer.write_evaluation(
            eval_id, answer.id, evaluation,
            interview_id=interview.id, assessment_id=assessment_id,
        )

        progress["questions_evaluated"] = progress.get("questions_evaluated", 0) + 1
        step = {
            "workstream": task.workstream,
            "question_id": str(answer.question_id),
            "answer_id": str(answer.id),
            "evaluation_id": str(eval_id),
            "status": "evaluated",
            "at": datetime.now(timezone.utc).isoformat(),
        }
        progress.setdefault("steps", []).append(step)

    await _save_progress(db, assessment_id, progress)

    await _broadcast(
        _broadcast_interview_id(progress),
        WSEventType.KG_UPDATED,
        {
            "assessment_id": str(assessment_id),
            "entity": "evaluation",
            "workstream": task.workstream,
            "count": len(eval_results),
        },
    )
    return True


async def run_simulation(
    assessment_id: uuid.UUID,
    max_workstreams: int | None = None,
    max_questions_per_workstream: int | None = None,
) -> None:
    """Background task: sequential 8-workstream autonomous Q&A."""
    workstreams = SIMULATION_WORKSTREAMS
    if max_workstreams is not None:
        workstreams = workstreams[: max(1, max_workstreams)]

    async with AsyncSessionLocal() as db:
        assessment = await db.get(Assessment, assessment_id)
        if not assessment:
            return

        company_profile = assessment.company_profile
        await _update_assessment(db, assessment_id, simulation_status="running", status="active")

        total_planned = 0
        bank_by_ws: dict[str, list[_BankQuestion]] = {}
        for ws in workstreams:
            qs = await _load_bank_questions(db, ws)
            if max_questions_per_workstream is not None:
                qs = qs[: max(1, max_questions_per_workstream)]
            bank_by_ws[ws] = qs
            total_planned += len(qs)

        progress: dict = {
            "workstreams_total": len(workstreams),
            "workstreams_completed": 0,
            "current_workstream": None,
            "current_interview_id": None,
            "primary_interview_id": None,
            "questions_asked": 0,
            "questions_evaluated": 0,
            "total_questions_planned": total_planned,
            "steps": [],
        }
        await _save_progress(db, assessment_id, progress)

        primary_interview_id: str | None = None

        try:
            for ws_idx, ws in enumerate(workstreams):
                if await _should_stop(db, assessment_id):
                    break

                bank_questions = bank_by_ws.get(ws, [])
                if not bank_questions:
                    continue

                task = Task(
                    assessment_id=assessment_id,
                    agent_type=ws if ws == "kubernetes" else "workstream",
                    workstream=ws,
                    status="in_progress",
                    scope="AI Simulated",
                )
                db.add(task)
                await db.commit()
                await db.refresh(task)
                await kg_writer.write_task(
                    task.id, assessment_id, task.agent_type, task.workstream, task.scope,
                )

                interview = Interview(
                    task_id=task.id,
                    interviewee_name="AI Simulated",
                    interviewee_role="Autonomous Agent",
                    status="in_progress",
                )
                db.add(interview)
                await db.commit()
                await db.refresh(interview)
                await kg_writer.write_interview(
                    interview.id, task.id, interview.interviewee_name, interview.interviewee_role,
                )

                if primary_interview_id is None:
                    primary_interview_id = str(interview.id)
                    progress["primary_interview_id"] = primary_interview_id
                    await _save_progress(db, assessment_id, progress)

                stopped_mid_ws = False
                if not await _process_workstream_batch(
                    db,
                    assessment_id,
                    company_profile,
                    interview,
                    task,
                    bank_questions,
                    progress,
                ):
                    stopped_mid_ws = True

                if await _should_stop(db, assessment_id):
                    break

                if not stopped_mid_ws:
                    task.status = "completed"
                    interview.status = "completed"
                    progress["workstreams_completed"] = ws_idx + 1
                    await db.commit()
                    await _save_progress(db, assessment_id, progress)

                if ws_idx < len(workstreams) - 1:
                    await asyncio.sleep(0.05)

            current_status = await _get_simulation_status(db, assessment_id)
            if current_status != "stopped":
                await _update_assessment(
                    db, assessment_id, simulation_status="completed", status="completed",
                )
                await _broadcast(
                    primary_interview_id,
                    WSEventType.SIMULATION_COMPLETED,
                    {"assessment_id": str(assessment_id)},
                )
        except Exception as exc:
            logger.exception("Simulation failed for %s: %s", assessment_id, exc)
            await _update_assessment(db, assessment_id, simulation_status="failed")
            await _broadcast(
                primary_interview_id,
                WSEventType.ERROR,
                {"detail": str(exc), "assessment_id": str(assessment_id)},
            )


async def finalize_simulation(assessment_id: uuid.UUID, db: AsyncSession) -> dict:
    """Compose report + AI generate from partial simulation data."""
    from app.models.finding import Report
    from app.services.report_ai import build_assessment_context, generate_sections
    from app.services.report_content import compose_assessment_report, dump_content_json, parse_content_json

    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise ValueError("Assessment not found")

    exec_summary = await build_simulation_exec_summary(assessment_id, db)
    composed = await compose_assessment_report(assessment_id, db)
    composed["executive_summary"] = exec_summary

    result = await db.execute(
        select(Report)
        .where(Report.assessment_id == assessment_id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    content_str = dump_content_json(composed["content"])

    if report:
        report.title = composed["title"]
        report.executive_summary = exec_summary
        report.content_json = content_str
    else:
        report = Report(
            assessment_id=assessment_id,
            title=composed["title"],
            executive_summary=exec_summary,
            content_json=content_str,
        )
        db.add(report)

    await db.commit()
    await db.refresh(report)

    sim_status = assessment.simulation_status
    if sim_status in (None, "running", "stopped"):
        sim_status = "finalized"
    await _update_assessment(
        db, assessment_id, simulation_status=sim_status, status="completed",
    )

    content = parse_content_json(report.content_json)
    assessment_context = await build_assessment_context(assessment_id, db)
    if exec_summary:
        assessment_context = f"{assessment_context}\n\nSimülasyon özeti:\n{exec_summary[:1500]}"

    updated = generate_sections(
        content.get("sections", []),
        assessment_context,
        section_ids=None,
        instruction="Simülasyon verilerine dayalı profesyonel rapor metni yaz",
        mode="generate",
    )
    report.content_json = dump_content_json(content)
    await db.commit()
    await db.refresh(report)

    return {
        "assessment_id": assessment_id,
        "report_id": report.id,
        "executive_summary": exec_summary,
        "simulation_status": sim_status,
        "ai_sections_updated": len(updated),
    }
