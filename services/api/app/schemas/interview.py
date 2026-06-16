import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.assessment import InterviewStatus


class InterviewCreate(BaseModel):
    task_id: uuid.UUID
    interviewee_name: str
    interviewee_role: str | None = None


class InterviewUpdate(BaseModel):
    interviewee_name: str | None = None
    interviewee_role: str | None = None
    status: InterviewStatus | None = None


class InterviewOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    task_id: uuid.UUID
    interviewee_name: str
    interviewee_role: str | None
    status: InterviewStatus
    kg_uri: str | None
    created_at: datetime
    updated_at: datetime


class QuestionCreate(BaseModel):
    interview_id: uuid.UUID
    text: str
    order: int = 0
    agent_suggested: bool = False


class QuestionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    interview_id: uuid.UUID
    text: str
    order: int
    agent_suggested: bool
    approval_status: str
    created_at: datetime


class QuestionApprovalUpdate(BaseModel):
    action: str  # "approved" or "rejected"


class SuggestFollowupBody(BaseModel):
    text: str | None = None


class AnswerCreate(BaseModel):
    question_id: uuid.UUID
    text: str
    raw_transcript: str | None = None


class AnswerOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    question_id: uuid.UUID
    text: str
    raw_transcript: str | None
    evaluation: str | None
    created_at: datetime


class EvaluateOut(BaseModel):
    answer_id: uuid.UUID
    evaluation: str
