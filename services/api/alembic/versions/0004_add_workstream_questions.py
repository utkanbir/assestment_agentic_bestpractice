"""add workstream_questions table

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workstream_questions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workstream", sa.String(100), nullable=False),
        sa.Column("area", sa.String(100), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("follow_ups", sa.Text, nullable=True),
        sa.Column("order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        if_not_exists=True,
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_workstream_questions_workstream "
        "ON workstream_questions (workstream)"
    )


def downgrade() -> None:
    op.drop_index("ix_workstream_questions_workstream", table_name="workstream_questions")
    op.drop_table("workstream_questions")
