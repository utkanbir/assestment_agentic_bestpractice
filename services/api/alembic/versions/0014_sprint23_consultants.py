"""sprint23 consultants, answer consultant fields, assessment synthesis

Revision ID: 0014
Revises: 0013
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "consultants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("expertise", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "assessment_consultants",
        sa.Column("assessment_id", UUID(as_uuid=True), sa.ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("consultant_id", UUID(as_uuid=True), sa.ForeignKey("consultants.id", ondelete="CASCADE"), primary_key=True),
    )
    op.add_column(
        "answers",
        sa.Column("consultant_id", UUID(as_uuid=True), sa.ForeignKey("consultants.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("answers", sa.Column("consultant_comment", sa.Text(), nullable=True))
    op.add_column("assessments", sa.Column("consultant_synthesis", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("assessments", "consultant_synthesis")
    op.drop_column("answers", "consultant_comment")
    op.drop_column("answers", "consultant_id")
    op.drop_table("assessment_consultants")
    op.drop_table("consultants")
