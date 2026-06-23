import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class AssessmentStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class InterviewStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Assessment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "assessments"

    client_name: Mapped[str] = mapped_column(String(255))
    project_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="draft")
    description: Mapped[str | None] = mapped_column(Text)
    kg_uri: Mapped[str | None] = mapped_column(String(500))
    assessment_mode: Mapped[str] = mapped_column(String(20), default="live")
    simulation_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    simulation_progress: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    company_profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    consultant_synthesis: Mapped[str | None] = mapped_column(Text, nullable=True)

    tasks: Mapped[list["Task"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")
    consultants: Mapped[list["Consultant"]] = relationship(  # noqa: F821
        secondary="assessment_consultants",
        back_populates="assessments",
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")


class Task(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tasks"

    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"))
    agent_type: Mapped[str] = mapped_column(String(100))
    workstream: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    scope: Mapped[str | None] = mapped_column(Text)
    kg_uri: Mapped[str | None] = mapped_column(String(500))

    assessment: Mapped["Assessment"] = relationship(back_populates="tasks")
    interviews: Mapped[list["Interview"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class Interview(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "interviews"

    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    interviewee_name: Mapped[str] = mapped_column(String(255))
    interviewee_role: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    kg_uri: Mapped[str | None] = mapped_column(String(500))

    task: Mapped["Task"] = relationship(back_populates="interviews")
    questions: Mapped[list["Question"]] = relationship(back_populates="interview", cascade="all, delete-orphan")


class Question(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "questions"

    interview_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    order: Mapped[int] = mapped_column(default=0)
    agent_suggested: Mapped[bool] = mapped_column(default=False)
    approval_status: Mapped[str] = mapped_column(String(50), default="approved")

    interview: Mapped["Interview"] = relationship(back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class Answer(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "answers"

    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    raw_transcript: Mapped[str | None] = mapped_column(Text)
    evaluation: Mapped[str | None] = mapped_column(Text, default=None)
    consultant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultants.id", ondelete="SET NULL"), nullable=True,
    )
    consultant_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    consultant_review_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    question: Mapped["Question"] = relationship(back_populates="answers")
    consultant_comments: Mapped[list["AnswerConsultantComment"]] = relationship(
        back_populates="answer", cascade="all, delete-orphan", order_by="AnswerConsultantComment.created_at",
    )


class AnswerConsultantComment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "answer_consultant_comments"
    __table_args__ = (
        UniqueConstraint("answer_id", "consultant_id", name="uq_answer_consultant_comment"),
    )

    answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    consultant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consultants.id", ondelete="CASCADE"), nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    consultant_review_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    answer: Mapped["Answer"] = relationship(back_populates="consultant_comments")


class MaturityScore(UUIDMixin, TimestampMixin, Base):
    """Per-workstream maturity score for an assessment (S8-BA-001)."""
    __tablename__ = "maturity_scores"

    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"))
    workstream: Mapped[str] = mapped_column(String(100), index=True)
    score: Mapped[float] = mapped_column(Numeric(3, 1))
    maturity_level: Mapped[str] = mapped_column(String(50), default="initial")
    notes: Mapped[str | None] = mapped_column(Text)
    target_score: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)

    __table_args__ = (
        UniqueConstraint("assessment_id", "workstream", name="uq_maturity_assessment_workstream"),
    )


class LayerTransaction(UUIDMixin, Base):
    __tablename__ = "layer_transactions"

    operation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    interview_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    chat_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ChatSession(UUIDMixin, Base):
    __tablename__ = "chat_sessions"

    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    workstream: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Yeni Sohbet")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    assessment: Mapped["Assessment"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ChatMessage(UUIDMixin, Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
