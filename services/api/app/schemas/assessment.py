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


class AssessmentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    client_name: str
    project_name: str
    status: AssessmentStatus
    description: str | None
    kg_uri: str | None
    created_at: datetime
    updated_at: datetime
