import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.architecture import LayerTouchOut

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
    layer_trace: list[LayerTouchOut] = []


class QuestionApprovalUpdate(BaseModel):
    action: str  # "approved" or "rejected"


class SuggestFollowupBody(BaseModel):
    text: str | None = None


class AnswerCreate(BaseModel):
    question_id: uuid.UUID
    text: str
    raw_transcript: str | None = None
    consultant_id: uuid.UUID | None = None
    consultant_comment: str | None = None


class AnswerUpdate(BaseModel):
    consultant_id: uuid.UUID | None = None
    consultant_comment: str | None = None


class AnswerConsultantReviewIn(BaseModel):
    consultant_comment: str | None = None


class AnswerConsultantReviewOut(BaseModel):
    consistent: bool
    feedback: str


class AnswerConsultantCommentCreate(BaseModel):
    consultant_id: uuid.UUID
    comment: str | None = None


class AnswerConsultantCommentUpdate(BaseModel):
    consultant_id: uuid.UUID | None = None
    comment: str | None = None


class AnswerConsultantCommentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    answer_id: uuid.UUID
    consultant_id: uuid.UUID
    comment: str | None = None
    consultant_review_feedback: str | None = None
    created_at: datetime


class AnswerOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    question_id: uuid.UUID
    text: str
    raw_transcript: str | None
    evaluation: str | None
    consultant_id: uuid.UUID | None = None
    consultant_comment: str | None = None
    consultant_review_feedback: str | None = None
    consultant_comments: list[AnswerConsultantCommentOut] = []
    created_at: datetime
    layer_trace: list[LayerTouchOut] = []
    transaction_id: uuid.UUID | None = None


class EvaluateOut(BaseModel):
    answer_id: uuid.UUID
    evaluation: str
    layer_trace: list[LayerTouchOut] = []
    transaction_id: uuid.UUID | None = None
