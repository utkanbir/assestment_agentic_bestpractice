from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, String, Table, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

assessment_consultants = Table(
    "assessment_consultants",
    Base.metadata,
    sa.Column("assessment_id", UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("consultant_id", UUID(as_uuid=True), ForeignKey("consultants.id", ondelete="CASCADE"), primary_key=True),
)


class Consultant(UUIDMixin, Base):
    __tablename__ = "consultants"

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expertise: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assessments: Mapped[list["Assessment"]] = relationship(  # noqa: F821
        secondary=assessment_consultants,
        back_populates="consultants",
    )
