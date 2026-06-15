import uuid

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class WorkstreamQuestion(UUIDMixin, TimestampMixin, Base):
    """Reusable question library scoped per workstream.

    Separate from the per-interview Question model — this is the template
    library agents and MCP clients pull from to drive interviews.
    """
    __tablename__ = "workstream_questions"

    workstream: Mapped[str] = mapped_column(String(100), index=True)
    area: Mapped[str] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    follow_ups: Mapped[str | None] = mapped_column(Text)  # JSON array
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
