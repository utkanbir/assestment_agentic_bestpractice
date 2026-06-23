import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.architecture import LayerTouchOut


class ChatSessionCreate(BaseModel):
    assessment_id: uuid.UUID
    workstream: str
    title: str = "Yeni Sohbet"


class ChatSessionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    assessment_id: uuid.UUID
    workstream: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatSessionUpdate(BaseModel):
    title: str | None = None
    workstream: str | None = None


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1)


class ChatMessageOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ChatMessageExchangeOut(BaseModel):
    session_id: uuid.UUID
    user_message: ChatMessageOut
    assistant_message: ChatMessageOut
    layer_trace: list[LayerTouchOut] = []
    transaction_id: uuid.UUID | None = None
