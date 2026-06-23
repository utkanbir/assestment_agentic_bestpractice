import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    assessment_id: uuid.UUID
    title: str
    executive_summary: str | None = None
    content_json: str | None = None


class ReportUpdate(BaseModel):
    title: str | None = None
    executive_summary: str | None = None
    content_json: str | None = None


class ReportOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    assessment_id: uuid.UUID
    title: str
    executive_summary: str | None
    content_json: str | None
    kg_uri: str | None
    created_at: datetime


class ReportAiGenerateRequest(BaseModel):
    section_id: str | None = None
    instruction: str = Field(default="Bu bölüm için profesyonel rapor metni yaz", min_length=1)
    mode: Literal["generate", "rewrite", "expand", "shorten", "tone_executive"] = "generate"


class ReportAiGenerateResponse(BaseModel):
    report_id: uuid.UUID
    updated_sections: list[str]
    content_json: str
    total_sections: int = 0


class ReportAiEditRequest(BaseModel):
    section_id: str | None = None
    instruction: str = Field(min_length=1)
    mode: Literal["rewrite", "expand", "shorten", "tone_executive"] = "rewrite"


class ReportAiEditResponse(BaseModel):
    report_id: uuid.UUID
    updated_sections: list[str]
    content_json: str


class ConsultantReviewRequest(BaseModel):
    section_id: str
    consultant_comment: str = Field(default="", max_length=8000)


class ConsultantReviewResponse(BaseModel):
    report_id: uuid.UUID
    section_id: str
    consistent: bool
    feedback: str
    content_json: str
