"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("project_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("assessment_id", UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("workstream", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("scope", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "interviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interviewee_name", sa.String(255), nullable=False),
        sa.Column("interviewee_role", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "questions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("interview_id", UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("agent_suggested", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "answers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("raw_transcript", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "evidences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("interview_id", UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("evidence_type", sa.String(50), nullable=False),
        sa.Column("kg_uri", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "findings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_id", UUID(as_uuid=True), sa.ForeignKey("evidences.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("approval_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("kg_uri", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "risks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finding_id", UUID(as_uuid=True), sa.ForeignKey("findings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("level", sa.String(50), nullable=False),
        sa.Column("impact", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finding_id", UUID(as_uuid=True), sa.ForeignKey("findings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="1"),
        sa.Column("effort", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("assessment_id", UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("executive_summary", sa.Text, nullable=True),
        sa.Column("content_json", sa.Text, nullable=True),
        sa.Column("kg_uri", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("recommendations")
    op.drop_table("risks")
    op.drop_table("findings")
    op.drop_table("evidences")
    op.drop_table("answers")
    op.drop_table("questions")
    op.drop_table("interviews")
    op.drop_table("tasks")
    op.drop_table("assessments")
