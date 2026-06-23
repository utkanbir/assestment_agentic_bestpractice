import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.assessment import AssessmentStatus


class AssessmentCreate(BaseModel):
    client_name: str
    project_name: str
    description: str | None = None


class AssessmentUpdate(BaseModel):
    client_name: str | None = None
    project_name: str | None = None
    description: str | None = None
    status: AssessmentStatus | None = None


class AssessmentDuplicateIn(BaseModel):
    include_qa: bool = False
    include_tasks: bool = True


class LatestInterviewOut(BaseModel):
    interview_id: str
    task_id: str
    workstream: str
    created_at: datetime


class AssessmentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    client_name: str
    project_name: str
    status: AssessmentStatus
    description: str | None
    kg_uri: str | None
    assessment_mode: str = "live"
    simulation_status: str | None = None
    simulation_progress: dict | None = None
    company_profile: dict | None = None
    consultant_synthesis: str | None = None
    created_at: datetime
    updated_at: datetime
