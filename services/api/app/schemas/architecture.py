import uuid
from datetime import datetime

from pydantic import BaseModel


class TechnologyOut(BaseModel):
    id: str
    name: str
    role: str
    configured: bool
    active_in_api: bool
    console_url: str | None = None
    notes: str | None = None
    link_mode: str | None = None  # internal | app | external


class LayerOut(BaseModel):
    id: str
    name: str
    description: str
    namespace: str
    technologies: list[TechnologyOut]


class LayersRegistryOut(BaseModel):
    layers: list[LayerOut]


class LayerTouchOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    assessment_id: uuid.UUID | None
    interview_id: uuid.UUID | None
    transaction_id: uuid.UUID | None = None
    step_order: int | None = None
    operation: str
    layer: str
    technology: str
    action: str
    detail: dict | None
    duration_ms: int | None
    created_at: datetime


class LayerTouchSummaryOut(BaseModel):
    layer: str
    touch_count: int
    last_operation: str | None
    last_at: datetime | None


class LayerTransactionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    operation: str
    source: str
    assessment_id: uuid.UUID | None
    interview_id: uuid.UUID | None
    chat_session_id: uuid.UUID | None
    status: str
    summary: str | None
    started_at: datetime
    ended_at: datetime | None
    total_duration_ms: int | None


class LayerTransactionDetailOut(LayerTransactionOut):
    steps: list[LayerTouchOut]
    narrative: str = ""
