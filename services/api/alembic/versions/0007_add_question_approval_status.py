"""add approval_status to questions

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-16

S10-BA-001: Agent follow-up suggestion and approval workflow.
"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("approval_status", sa.String(50), server_default="approved", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("questions", "approval_status")
