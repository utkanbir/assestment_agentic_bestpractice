import uuid
from datetime import datetime

from pydantic import BaseModel


class RecommendationCreate(BaseModel):
    finding_id: uuid.UUID
    description: str
    priority: int = 1       # 1=highest
    effort: str | None = None   # low | medium | high


class RecommendationOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    finding_id: uuid.UUID
    description: str
    priority: int
    effort: str | None
    created_at: datetime
