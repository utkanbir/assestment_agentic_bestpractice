import uuid
from datetime import datetime

from pydantic import BaseModel


class RiskCreate(BaseModel):
    finding_id: uuid.UUID
    description: str
    level: str        # high | medium | low
    title: str | None = None
    impact: str | None = None


class RiskUpdate(BaseModel):
    level: str | None = None
    title: str | None = None
    description: str | None = None
    impact: str | None = None


class RiskOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    finding_id: uuid.UUID
    description: str
    level: str
    title: str | None
    impact: str | None
    kg_uri: str | None
    created_at: datetime
