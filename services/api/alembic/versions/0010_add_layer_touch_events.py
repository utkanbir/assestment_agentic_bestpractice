"""add layer_touch_events table for architecture instrumentation

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "layer_touch_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("assessment_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("interview_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("operation", sa.String(100), nullable=False, index=True),
        sa.Column("layer", sa.String(50), nullable=False, index=True),
        sa.Column("technology", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("detail", JSONB, nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )


def downgrade():
    op.drop_table("layer_touch_events")
