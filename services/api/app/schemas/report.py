import uuid
from datetime import datetime

from pydantic import BaseModel


class ReportCreate(BaseModel):
    assessment_id: uuid.UUID
    title: str
    executive_summary: str | None = None
    content_json: str | None = None    # JSON string; agent stores markdown-in-JSON or structured dict


class ReportOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    assessment_id: uuid.UUID
    title: str
    executive_summary: str | None
    content_json: str | None
    kg_uri: str | None
    created_at: datetime
