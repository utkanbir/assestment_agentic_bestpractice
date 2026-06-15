import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.finding import ApprovalStatus, EvidenceType, FindingSeverity, RiskLevel


class EvidenceCreate(BaseModel):
    interview_id: uuid.UUID | None = None
    source: str
    content: str
    evidence_type: EvidenceType


class EvidenceOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    interview_id: uuid.UUID | None
    source: str
    content: str
    evidence_type: EvidenceType
    kg_uri: str | None
    created_at: datetime


class FindingCreate(BaseModel):
    task_id: uuid.UUID
    evidence_id: uuid.UUID
    description: str
    severity: FindingSeverity
    confidence: float = 0.0


class FindingUpdate(BaseModel):
    description: str | None = None
    severity: FindingSeverity | None = None
    confidence: float | None = None
    approval_status: ApprovalStatus | None = None


class FindingOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    task_id: uuid.UUID
    evidence_id: uuid.UUID
    description: str
    severity: FindingSeverity
    confidence: float
    approval_status: ApprovalStatus
    kg_uri: str | None
    created_at: datetime
    updated_at: datetime
