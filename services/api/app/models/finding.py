import enum
import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class EvidenceType(str, enum.Enum):
    INTERVIEW = "interview"
    DOCUMENT = "document"
    OBSERVATION = "observation"
    METRIC = "metric"


class FindingSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RiskLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Evidence(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "evidences"

    interview_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True)
    source: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    evidence_type: Mapped[str] = mapped_column(String(50))
    kg_uri: Mapped[str | None] = mapped_column(String(500))

    findings: Mapped[list["Finding"]] = relationship(back_populates="evidence", cascade="all, delete-orphan")


class Finding(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "findings"

    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evidences.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    approval_status: Mapped[str] = mapped_column(String(50), default="pending")
    kg_uri: Mapped[str | None] = mapped_column(String(500))

    evidence: Mapped["Evidence"] = relationship(back_populates="findings")
    risks: Mapped[list["Risk"]] = relationship(back_populates="finding", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="finding", cascade="all, delete-orphan")


class Risk(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "risks"

    finding_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"))
    title: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(50))
    impact: Mapped[str | None] = mapped_column(Text)
    kg_uri: Mapped[str | None] = mapped_column(String(500))

    finding: Mapped["Finding"] = relationship(back_populates="risks")


class Recommendation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"

    finding_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(default=1)
    effort: Mapped[str | None] = mapped_column(String(50))

    finding: Mapped["Finding"] = relationship(back_populates="recommendations")


class Report(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "reports"

    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(500))
    executive_summary: Mapped[str | None] = mapped_column(Text)
    content_json: Mapped[str | None] = mapped_column(Text)
    kg_uri: Mapped[str | None] = mapped_column(String(500))
