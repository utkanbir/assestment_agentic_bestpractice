import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.assessment import Assessment
from app.schemas.simulation import (
    SimulationFinalizeOut,
    SimulationProgressOut,
    SimulationStartIn,
    SimulationStartOut,
    SimulationStatusOut,
)
from app.services import kg_writer
from app.services.simulation_runner import finalize_simulation, run_simulation

router = APIRouter(prefix="/assessments", tags=["simulation"])


def _progress_out(raw: dict | None) -> SimulationProgressOut | None:
    if not raw:
        return None
    return SimulationProgressOut(**raw)


def _status_out(assessment: Assessment) -> SimulationStatusOut:
    progress = assessment.simulation_progress or {}
    return SimulationStatusOut(
        assessment_id=assessment.id,
        assessment_mode=assessment.assessment_mode,
        simulation_status=assessment.simulation_status,
        simulation_progress=_progress_out(progress),
        primary_interview_id=progress.get("primary_interview_id") or progress.get("current_interview_id"),
    )


@router.post("/simulated", response_model=SimulationStartOut, status_code=status.HTTP_201_CREATED)
async def start_simulated_assessment(
    body: SimulationStartIn,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    assessment = Assessment(
        client_name=body.client_name,
        project_name=body.project_name,
        description=body.description,
        status="active",
        assessment_mode="simulated",
        simulation_status="pending",
        company_profile=body.company_profile,
        simulation_progress={
            "workstreams_total": 8,
            "workstreams_completed": 0,
            "questions_asked": 0,
            "questions_evaluated": 0,
            "total_questions_planned": 0,
            "steps": [],
        },
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    background_tasks.add_task(
        kg_writer.write_assessment,
        assessment.id, assessment.client_name, assessment.project_name, True,
    )
    background_tasks.add_task(
        run_simulation,
        assessment.id,
        body.max_workstreams,
        body.max_questions_per_workstream,
    )

    progress = assessment.simulation_progress or {}
    return SimulationStartOut(
        id=assessment.id,
        client_name=assessment.client_name,
        project_name=assessment.project_name,
        status=assessment.status,
        assessment_mode=assessment.assessment_mode,
        simulation_status=assessment.simulation_status,
        simulation_progress=progress,
        primary_interview_id=progress.get("primary_interview_id"),
        created_at=assessment.created_at,
    )


@router.post("/{assessment_id}/simulation/stop", response_model=SimulationStatusOut)
async def stop_simulation(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.assessment_mode != "simulated":
        raise HTTPException(status_code=400, detail="Not a simulated assessment")

    assessment.simulation_status = "stopped"
    await db.commit()
    await db.refresh(assessment)

    from app.routers.ws import WSEventType, WSMessage, manager

    progress = assessment.simulation_progress or {}
    interview_id = progress.get("current_interview_id") or progress.get("primary_interview_id")
    if interview_id:
        await manager.broadcast(
            interview_id,
            WSMessage(
                event=WSEventType.SIMULATION_STOPPED,
                payload={"assessment_id": str(assessment_id)},
            ),
        )
    return _status_out(assessment)


@router.get("/{assessment_id}/simulation/status", response_model=SimulationStatusOut)
async def get_simulation_status(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return _status_out(assessment)


@router.post("/{assessment_id}/simulation/finalize", response_model=SimulationFinalizeOut)
async def finalize_simulation_endpoint(assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    assessment = await db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.assessment_mode != "simulated":
        raise HTTPException(status_code=400, detail="Not a simulated assessment")

    try:
        result = await finalize_simulation(assessment_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SimulationFinalizeOut(**result)
