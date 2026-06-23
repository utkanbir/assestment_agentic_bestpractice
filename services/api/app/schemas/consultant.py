import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.services.expertise_catalog import validate_expertise_tags


class ConsultantCreate(BaseModel):
    first_name: str
    last_name: str
    role: str | None = None
    expertise: list[str] = Field(default_factory=list)

    @field_validator("expertise")
    @classmethod
    def check_expertise(cls, v: list[str]) -> list[str]:
        return validate_expertise_tags(v)


class ConsultantUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    expertise: list[str] | None = None

    @field_validator("expertise")
    @classmethod
    def check_expertise(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        return validate_expertise_tags(v)


class ConsultantOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    first_name: str
    last_name: str
    role: str | None
    expertise: list[str] = Field(default_factory=list)
    created_at: datetime

    @field_validator("expertise", mode="before")
    @classmethod
    def normalize_expertise(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return [v] if v else []


class AssignConsultantIn(BaseModel):
    consultant_id: uuid.UUID


class ConsultantSynthesisOut(BaseModel):
    assessment_id: str
    consultant_synthesis: str


class MaturityAiSuggestOut(BaseModel):
    workstream: str
    score: float
    maturity_level: str
    notes: str
    saved: bool = True
