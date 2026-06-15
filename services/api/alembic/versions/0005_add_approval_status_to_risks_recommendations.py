"""add approval_status to risks and recommendations

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-15

S5-BA-005: Human approval workflow requires approval_status on Risk and Recommendation.
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("risks", sa.Column("approval_status", sa.String(50), nullable=False, server_default="pending"))
    op.add_column("recommendations", sa.Column("approval_status", sa.String(50), nullable=False, server_default="pending"))


def downgrade() -> None:
    op.drop_column("risks", "approval_status")
    op.drop_column("recommendations", "approval_status")
