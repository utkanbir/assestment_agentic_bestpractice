import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.assessment import AssessmentStatus


class SimulationStartIn(BaseModel):
    client_name: str
    project_name: str
    description: str | None = None
    company_profile: dict[str, Any] | None = None
    max_workstreams: int | None = None
    max_questions_per_workstream: int | None = None


class SimulationProgressOut(BaseModel):
    workstreams_total: int = 8
    workstreams_completed: int = 0
    current_workstream: str | None = None
    current_interview_id: str | None = None
    questions_asked: int = 0
    questions_evaluated: int = 0
    total_questions_planned: int = 0
    steps: list[dict[str, Any]] = Field(default_factory=list)


class SimulationStatusOut(BaseModel):
    assessment_id: uuid.UUID
    assessment_mode: str
    simulation_status: str | None
    simulation_progress: SimulationProgressOut | None
    primary_interview_id: str | None = None


class SimulationStartOut(BaseModel):
    id: uuid.UUID
    client_name: str
    project_name: str
    status: AssessmentStatus
    assessment_mode: str
    simulation_status: str | None
    simulation_progress: dict[str, Any] | None
    primary_interview_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SimulationFinalizeOut(BaseModel):
    assessment_id: uuid.UUID
    report_id: uuid.UUID
    executive_summary: str
    simulation_status: str
    ai_sections_updated: int
