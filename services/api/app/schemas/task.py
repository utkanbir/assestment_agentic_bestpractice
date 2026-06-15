import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.assessment import TaskStatus


class TaskCreate(BaseModel):
    assessment_id: uuid.UUID
    agent_type: str
    workstream: str
    scope: str | None = None


class TaskUpdate(BaseModel):
    workstream: str | None = None
    status: TaskStatus | None = None
    scope: str | None = None


class TaskOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    assessment_id: uuid.UUID
    agent_type: str
    workstream: str
    status: TaskStatus
    scope: str | None
    kg_uri: str | None
    created_at: datetime
    updated_at: datetime
