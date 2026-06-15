import uuid
from datetime import datetime

from pydantic import BaseModel


class WorkstreamQuestionCreate(BaseModel):
    workstream: str
    area: str
    text: str
    follow_ups: list[str] | None = None  # serialized to JSON string in DB
    order: int = 0
    is_active: bool = True


class WorkstreamQuestionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workstream: str
    area: str
    text: str
    follow_ups: str | None   # raw JSON string
    order: int
    is_active: bool
    created_at: datetime


class BulkLoadRequest(BaseModel):
    workstream: str
    questions: list[WorkstreamQuestionCreate]
    replace: bool = False  # if True, delete existing questions for workstream first
