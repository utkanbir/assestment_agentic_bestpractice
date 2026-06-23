"""Agent learning events — AAHA, text, and document training (S24)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class AgentLearningEvent(UUIDMixin, Base):
    __tablename__ = "agent_learning_events"

    workstream: Mapped[str] = mapped_column(String(100), index=True)
    mode: Mapped[str] = mapped_column(String(20))  # aaha | text | document
    question_text: Mapped[str | None] = mapped_column(Text, default=None)
    answer_text: Mapped[str | None] = mapped_column(Text, default=None)
    source_doc_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id"), default=None
    )
    consultant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultants.id"), default=None
    )
    answer_author: Mapped[str] = mapped_column(String(20), default="consultant")
    approved_by_consultant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultants.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
