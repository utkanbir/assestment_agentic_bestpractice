"""add kg_uri to assessments, tasks, interviews

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assessments", sa.Column("kg_uri", sa.String(500), nullable=True))
    op.add_column("tasks", sa.Column("kg_uri", sa.String(500), nullable=True))
    op.add_column("interviews", sa.Column("kg_uri", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("interviews", "kg_uri")
    op.drop_column("tasks", "kg_uri")
    op.drop_column("assessments", "kg_uri")
