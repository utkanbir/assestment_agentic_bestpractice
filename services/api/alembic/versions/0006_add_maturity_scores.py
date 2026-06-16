"""add maturity_scores table

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-16

S8-BA-001: MaturityScore per workstream per assessment.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maturity_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("assessment_id", UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workstream", sa.String(100), nullable=False),
        sa.Column("score", sa.Numeric(3, 1), nullable=False),
        sa.Column("maturity_level", sa.String(50), nullable=False, server_default="initial"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("assessment_id", "workstream", name="uq_maturity_assessment_workstream"),
    )
    op.create_index("ix_maturity_scores_assessment_id", "maturity_scores", ["assessment_id"])


def downgrade() -> None:
    op.drop_index("ix_maturity_scores_assessment_id")
    op.drop_table("maturity_scores")
