"""Knowledge document model for RAG pipeline (S11-BA-005)."""
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class KnowledgeDocument(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    workstream: Mapped[str] = mapped_column(String(100), index=True)
    filename: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(50), default="txt")
    content: Mapped[str] = mapped_column(Text)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text, default=None)
