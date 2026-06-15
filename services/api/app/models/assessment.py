import enum
import uuid

from sqlalchemy import ForeignKey, String, Text
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

    tasks: Mapped[list["Task"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")


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

    interview: Mapped["Interview"] = relationship(back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class Answer(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "answers"

    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    raw_transcript: Mapped[str | None] = mapped_column(Text)

    question: Mapped["Question"] = relationship(back_populates="answers")
